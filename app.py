from flask import Flask, request, jsonify, send_from_directory
import os
import json
import requests
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from digital_twin.engine import DigitalTwin

app = Flask(__name__, static_folder="html_files")

def load_dotenv_file(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value
load_dotenv_file()
load_dotenv_file(os.path.join("env_files", ".env"))

def prepare_model():
    data = pd.read_csv("datasets/vitamin_deficiency_disease_dataset_20260123.csv")
    data.columns = data.columns.str.strip()
    for col in data.select_dtypes(include=["object"]).columns:
        data[col] = data[col].str.strip()

    X = data.drop(columns=["disease_diagnosis"])

    # capture original dtypes before encoding so we can parse inputs correctly
    original_dtypes = X.dtypes.to_dict()

    encoders = {}
    categorical_cols = X.select_dtypes(include=["object"]).columns
    nullable_categorical_cols = [col for col in categorical_cols if X[col].isna().any()]

    for col in categorical_cols:
        encoders[col] = LabelEncoder()
        X[col] = encoders[col].fit_transform(X[col])

    le_y = LabelEncoder()
    y = le_y.fit_transform(data["disease_diagnosis"])

    model = RandomForestClassifier()
    model.fit(X, y)

    return model, encoders, le_y, X.columns.tolist(), original_dtypes, nullable_categorical_cols

model, encoders, label_encoder, feature_columns, feature_dtypes, nullable_categorical_cols = prepare_model()


def parse_feature(form, key, dtype):
    raw = form.get(key, "").strip()
    if raw == "":
        if np.issubdtype(dtype, np.number):
            raise ValueError(f"Missing required numeric field: {key}")
        if key in nullable_categorical_cols:
            return np.nan
        raise ValueError(f"Missing required categorical field: {key}")

    if np.issubdtype(dtype, np.integer):
        return int(raw)
    if np.issubdtype(dtype, np.floating):
        return float(raw)
    return raw


DEFAULT_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent"
)


def normalize_gemini_endpoint(endpoint: str) -> str:
    """Map legacy generateMessage/generateText URLs to generateContent."""
    endpoint = endpoint.strip()
    if not endpoint.startswith("https://"):
        return DEFAULT_GEMINI_ENDPOINT
    for suffix in (":generateMessage", ":generateText", ":generateContent"):
        if endpoint.endswith(suffix):
            return endpoint[: -len(suffix)] + ":generateContent"
    if "/models/" in endpoint:
        return endpoint.rstrip("/") + ":generateContent"
    return DEFAULT_GEMINI_ENDPOINT


def call_gemini(prompt_text: str) -> str:
    """Call Google Gemini generateContent API (GEMINI_API_KEY, optional GEMINI_API_ENDPOINT)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY must be set in the environment")

    endpoint = normalize_gemini_endpoint(
        os.getenv("GEMINI_API_ENDPOINT", DEFAULT_GEMINI_ENDPOINT)
    )
    url = f"{endpoint}?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt_text}],
            }
        ]
    }

    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            f"Gemini request failed ({resp.status_code}) at {endpoint}: {resp.text}"
        ) from exc

    data = resp.json()
    candidates = data.get("candidates") or []
    if candidates:
        parts = candidates[0].get("content", {}).get("parts") or []
        if parts and "text" in parts[0]:
            return parts[0]["text"]

    return json.dumps(data)

@app.route("/")
def home():
    return send_from_directory("html_files", "home.html")


@app.route("/twin")
def twin_page():
    return send_from_directory("html_files", "twin.html")


@app.route("/simulate", methods=["POST"])
def simulate():
    """Run rule-based digital twin simulation over N days."""
    try:
        if request.is_json:
            payload = request.get_json()
        else:
            payload = request.form.to_dict()
        if not isinstance(payload, dict):
            return jsonify({"error": "Invalid request body"}), 400

        twin, habits = DigitalTwin.from_payload(payload)
        result = twin.simulate(habits)
        return jsonify(result)
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict", methods=["POST"])
def predict():
    data = {}
    for col in feature_columns:
        data[col] = parse_feature(request.form, col, feature_dtypes[col])

    sample = pd.DataFrame([data])
    for col, encoder in encoders.items():
        sample[col] = encoder.transform(sample[col])

    prediction = model.predict(sample)
    result = label_encoder.inverse_transform(prediction)[0]

    return jsonify({"prediction": result})


@app.route("/explain", methods=["POST"])
def explain():
    """Return a natural-language explanation for a disease diagnosis.

    Accepts either:
    - JSON or form with `diagnosis`: a string to send to Gemini; or
    - the same feature form used by `/predict`, in which case the server will first predict.
    """
    try:
        # prefer explicit diagnosis if provided
        diagnosis = None
        if request.is_json:
            body = request.get_json()
            diagnosis = body.get("diagnosis") if isinstance(body, dict) else None
        else:
            diagnosis = request.form.get("diagnosis")

        if not diagnosis:
            # build features and predict
            data = {}
            for col in feature_columns:
                data[col] = parse_feature(request.form, col, feature_dtypes[col])

            sample = pd.DataFrame([data])
            for col, encoder in encoders.items():
                sample[col] = encoder.transform(sample[col])

            prediction = model.predict(sample)
            diagnosis = label_encoder.inverse_transform(prediction)[0]

        # craft a friendly prompt for Gemini
        prompt = (
            f"You are a helpful medical assistant. Produce a concise, patient-friendly paragraph explaining the diagnosis\n"
            f"Diagnosis: {diagnosis}\n\n"
            "Include a brief explanation of what it means, likely causes, and general dietary/lifestyle suggestions the patient can discuss with their clinician."
        )

        explanation = call_gemini(prompt)
        return jsonify({"diagnosis": diagnosis, "explanation": explanation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)