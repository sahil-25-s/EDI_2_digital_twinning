from flask import Flask, request, jsonify, send_from_directory
import os
import json
import requests
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__, static_folder="html_files")

def prepare_model():
    data = pd.read_csv("datasets/vitamin_deficiency_disease_dataset_20260123.csv")

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


def call_gemini(prompt_text: str) -> str:
    """Call Google Gemini API using env vars GEMINI_API_KEY and GEMINI_API_ENDPOINT.
    
    Example env vars:
    - GEMINI_API_KEY=your-api-key
    - GEMINI_API_ENDPOINT=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
    """
    api_key = os.getenv("GEMINI_API_KEY")
    endpoint = os.getenv("GEMINI_API_ENDPOINT")
    if not api_key or not endpoint:
        raise RuntimeError("GEMINI_API_KEY and GEMINI_API_ENDPOINT must be set in the environment")

    # Google Gemini API format: add key as query param
    url = f"{endpoint}?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Google Gemini expects "contents" with "parts" containing "text"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    # Extract text from Google Gemini response
    if isinstance(data, dict):
        if "candidates" in data and isinstance(data["candidates"], list) and len(data["candidates"]) > 0:
            first_candidate = data["candidates"][0]
            if "content" in first_candidate and "parts" in first_candidate["content"]:
                parts = first_candidate["content"]["parts"]
                if isinstance(parts, list) and len(parts) > 0:
                    return parts[0].get("text", "")

    # fallback: return pretty-printed json
    return json.dumps(data)

@app.route("/")
def home():
    return send_from_directory("html_files", "home.html")

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