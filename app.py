from flask import Flask, render_template, request, jsonify, redirect, send_from_directory, url_for
import os
import json
import requests
import numpy as np
import pandas as pd
from flask_login import current_user, login_required
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from digital_twin.engine import DigitalTwin
from extensions import db, login_manager, migrate
import models  # noqa: F401 — register models with SQLAlchemy
from models import SimulationRun, User
from db_service import get_user_data_payload, save_all_user_data, save_simulation_run
from routes.auth import auth_bp


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

app = Flask(
    __name__,
    template_folder="html_files",
    static_folder="html_files/static",
    static_url_path="/static",
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-me-in-production")
database_url = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if database_url:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def _unauthorized():
        """Return JSON for API/fetch routes instead of an HTML login redirect."""
        if request.path.startswith("/api/") or request.path in ("/predict", "/explain"):
            return jsonify({"error": "Login required. Please sign in and try again."}), 401
        return redirect(url_for("auth.login", next=request.path))

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


def _is_missing_category(raw) -> bool:
    if raw is None:
        return True
    if isinstance(raw, float) and np.isnan(raw):
        return True
    if isinstance(raw, str):
        return raw.strip().lower() in ("", "none", "nan", "null")
    return False


def _parse_raw_value(key: str, raw, dtype):
    if _is_missing_category(raw):
        if np.issubdtype(dtype, np.number):
            raise ValueError(f"Missing required numeric field: {key}")
        if key in nullable_categorical_cols:
            return np.nan
        raise ValueError(f"Missing required categorical field: {key}")

    if np.issubdtype(dtype, np.integer):
        return int(raw)
    if np.issubdtype(dtype, np.floating):
        return float(raw)
    return str(raw).strip()


def parse_feature(form, key, dtype):
    raw = form.get(key, "")
    if isinstance(raw, str):
        raw = raw.strip()
    return _parse_raw_value(key, raw, dtype)


def parse_payload_value(key: str, raw, dtype):
    if isinstance(raw, str):
        raw = raw.strip()
    return _parse_raw_value(key, raw, dtype)


ML_SCREENING_DEFAULTS = {
    "age": 30,
    "gender": "Male",
    "bmi": 22.0,
    "smoking_status": "Never",
    "alcohol_consumption": "",
    "exercise_level": "Moderate",
    "diet_type": "Omnivore",
    "sun_exposure": "Moderate",
    "income_level": "Middle",
    "latitude_region": "Mid",
    "vitamin_a_percent_rda": 90.0,
    "vitamin_c_percent_rda": 90.0,
    "vitamin_d_percent_rda": 80.0,
    "vitamin_e_percent_rda": 90.0,
    "vitamin_b12_percent_rda": 90.0,
    "folate_percent_rda": 90.0,
    "calcium_percent_rda": 90.0,
    "iron_percent_rda": 85.0,
    "hemoglobin_g_dl": 13.5,
    "serum_vitamin_d_ng_ml": 30.0,
    "serum_vitamin_b12_pg_ml": 350.0,
    "serum_folate_ng_ml": 12.0,
    "symptoms_count": 0,
    "symptoms_list": "",
    "has_night_blindness": 0,
    "has_fatigue": 0,
    "has_bleeding_gums": 0,
    "has_bone_pain": 0,
    "has_muscle_weakness": 0,
    "has_numbness_tingling": 0,
    "has_memory_problems": 0,
    "has_pale_skin": 0,
    "has_multiple_deficiencies": 0,
}


def _merge_saved_profile(payload: dict) -> dict:
    """Fill missing ML fields from the logged-in user's saved profile."""
    if not getattr(current_user, "is_authenticated", False):
        return payload
    saved = get_user_data_payload(current_user.id)
    if not saved:
        return payload
    merged = dict(saved)
    for key, value in payload.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        merged[key] = value
    return merged


def _form_payload() -> dict:
    if request.is_json and isinstance(request.get_json(), dict):
        return request.get_json()
    return request.form.to_dict()


def build_ml_features(payload: dict) -> dict:
    payload = _merge_saved_profile(payload)
    for col, default in ML_SCREENING_DEFAULTS.items():
        if col not in payload or payload[col] is None:
            payload[col] = default
        elif isinstance(payload[col], str) and payload[col].strip() == "" and col not in nullable_categorical_cols:
            payload[col] = default
    features = {}
    for col in feature_columns:
        if col not in payload:
            raise ValueError(f"Missing required field for screening: {col}")
        features[col] = parse_payload_value(col, payload[col], feature_dtypes[col])
    return features


def predict_disease(payload: dict) -> str:
    features = build_ml_features(payload)
    sample = pd.DataFrame([features])
    for col, encoder in encoders.items():
        sample[col] = encoder.transform(sample[col])
    prediction = model.predict(sample)
    return label_encoder.inverse_transform(prediction)[0]


def attach_clinical_context(payload: dict) -> dict:
    if not payload.get("disease_diagnosis"):
        payload["disease_diagnosis"] = predict_disease(payload)
    return payload


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


def build_twin_gemini_prompt(simulation: dict) -> str:
    """Build a prompt from digital twin output for Gemini lifestyle feedback."""
    profile = simulation.get("profile", {})
    clinical = simulation.get("clinical_assessment", {})
    targets = simulation.get("personalized_targets", {})
    state = simulation.get("final_state", {})
    recs = simulation.get("recommendations", [])
    days = simulation.get("simulation_days", "?")

    state_lines = "\n".join(
        f"- {key.replace('_', ' ')}: {round(float(val), 1)}"
        for key, val in state.items()
    )
    rec_lines = "\n".join(f"- {r}" for r in recs) if recs else "- None"

    return (
        "You are a supportive wellness coach (not a doctor). Based on this digital twin "
        f"simulation over {days} days, give practical, encouraging feedback.\n\n"
        "Static profile:\n"
        f"- age: {profile.get('age')}, gender: {profile.get('gender')}, "
        f"height_cm: {profile.get('height_cm')}, bmi: {profile.get('bmi')}\n"
        f"- diet: {profile.get('diet_type')}, exercise: {profile.get('exercise_level')}\n"
        f"- smoking: {profile.get('smoking_status')}, alcohol: {profile.get('alcohol_consumption')}\n"
        f"- sun exposure: {profile.get('sun_exposure')}\n\n"
        f"Patient name (context): {simulation.get('user_name', 'Student')}\n\n"
        "Clinical context:\n"
        f"- disease_diagnosis: {simulation.get('disease_diagnosis', clinical.get('disease_diagnosis'))}\n"
        f"- symptoms_list: {simulation.get('symptoms_list', clinical.get('symptoms_list'))}\n"
        f"- symptoms_count: {clinical.get('symptoms_count')}\n"
        f"- hemoglobin_g_dl: {clinical.get('hemoglobin_g_dl')}\n"
        f"- serum_vitamin_d_ng_ml: {clinical.get('serum_vitamin_d_ng_ml')}\n\n"
        "Personalized daily targets used by the twin:\n"
        f"{json.dumps(targets, indent=2)}\n\n"
        "Final simulated state scores (0-100, higher is better except fatigue/stress/deficiency_risk):\n"
        f"{state_lines}\n\n"
        "Rule-based recommendations already generated:\n"
        f"{rec_lines}\n\n"
        "Write 2 short paragraphs:\n"
        "1) What the simulation suggests about current health trajectory.\n"
        "2) Top 3 prioritized habit changes for the next week.\n"
        "Keep language simple and actionable. Do not diagnose disease. Plain text only, no markdown"
    )


def _truthy(value) -> bool:
    return str(value).lower() in ("1", "true", "yes", "on")


@app.route("/db-health")
def db_health():
    """Check PostgreSQL connectivity (SELECT 1)."""
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        return jsonify({"database": "not_configured", "hint": "Set DATABASE_URL in env_files/.env"}), 503
    db.session.execute(db.text("SELECT 1"))
    return jsonify({"database": "ok"})


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/lifestyle")
@login_required
def lifestyle_page():
    return render_template("lifestyle.html")


@app.route("/results")
@login_required
def results_page():
    return render_template("results.html")


@app.route("/predict-page")
@login_required
def predict_page():
    return render_template("predict-page.html")


@app.route("/twin")
@login_required
def twin_page():
    return redirect(url_for("lifestyle_page"))


@app.route("/api/dashboard")
@login_required
def api_dashboard():
    summary = {}
    last_run = None
    if app.config.get("SQLALCHEMY_DATABASE_URI"):
        run = (
            SimulationRun.query.filter_by(user_id=current_user.id)
            .order_by(SimulationRun.created_at.desc())
            .first()
        )
        if run and run.final_state:
            summary = run.final_state
            last_run = {
                "disease_diagnosis": run.disease_diagnosis,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
    return jsonify(
        {
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
            },
            "summary": summary,
            "last_run": last_run,
        }
    )


@app.route("/api/latest-simulation")
@login_required
def api_latest_simulation():
    run = (
        SimulationRun.query.filter_by(user_id=current_user.id)
        .order_by(SimulationRun.created_at.desc())
        .first()
    )
    if not run:
        return jsonify({"error": "No simulations yet"}), 404
    return jsonify(
        {
            "simulation_days": run.simulation_days,
            "disease_diagnosis": run.disease_diagnosis,
            "symptoms_list": run.symptoms_list,
            "personalized_targets": run.personalized_targets,
            "final_state": run.final_state,
            "recommendations": run.recommendations,
            "clinical_assessment": run.clinical_assessment,
            "gemini_feedback": run.gemini_feedback,
            "history": [],
        }
    )


@app.route("/simulate", methods=["POST"])
@login_required
def simulate():
    """Run rule-based digital twin simulation over N days."""
    try:
        if request.is_json:
            payload = request.get_json()
        else:
            payload = request.form.to_dict()
        if not isinstance(payload, dict):
            return jsonify({"error": "Invalid request body"}), 400

        payload = attach_clinical_context(payload)
        twin, habits = DigitalTwin.from_payload(payload)
        result = twin.simulate(habits)

        if _truthy(payload.get("include_gemini", False)):
            try:
                result["gemini_feedback"] = call_gemini(build_twin_gemini_prompt(result))
            except Exception as exc:
                result["gemini_error"] = str(exc)

        if current_user.is_authenticated:
            result["user_name"] = current_user.name

        if app.config.get("SQLALCHEMY_DATABASE_URI"):
            try:
                save_all_user_data(current_user.id, payload)
                result["simulation_run_id"] = save_simulation_run(
                    payload, result, user_id=current_user.id
                )
            except Exception as exc:
                result["db_warning"] = f"Simulation ran but could not save to database: {exc}"

        return jsonify(result)
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/simulate/feedback", methods=["POST"])
def simulate_feedback():
    """Send an existing simulation result (or re-run from payload) to Gemini."""
    try:
        if request.is_json:
            payload = request.get_json() or {}
        else:
            payload = request.form.to_dict()

        simulation = payload.get("simulation_result")
        if not simulation:
            twin, habits = DigitalTwin.from_payload(payload)
            simulation = twin.simulate(habits)

        feedback = call_gemini(build_twin_gemini_prompt(simulation))
        return jsonify({"simulation": simulation, "gemini_feedback": feedback})
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict", methods=["POST"])
@login_required
def predict():
    try:
        payload = _form_payload()
        features = build_ml_features(payload)
        sample = pd.DataFrame([features])
        for col, encoder in encoders.items():
            sample[col] = encoder.transform(sample[col])
        prediction = model.predict(sample)
        result = label_encoder.inverse_transform(prediction)[0]
        return jsonify({"prediction": result})
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/explain", methods=["POST"])
@login_required
def explain():
    """Return a natural-language explanation for a disease diagnosis."""
    try:
        payload = _form_payload()
        diagnosis = payload.get("diagnosis")
        if diagnosis:
            diagnosis = str(diagnosis).strip()

        if not diagnosis:
            features = build_ml_features(payload)
            sample = pd.DataFrame([features])
            for col, encoder in encoders.items():
                sample[col] = encoder.transform(sample[col])
            prediction = model.predict(sample)
            diagnosis = label_encoder.inverse_transform(prediction)[0]

        prompt = (
            "You are a helpful medical assistant. Produce a concise, patient-friendly paragraph explaining the diagnosis\n"
            f"Diagnosis: {diagnosis}\n\n"
            "Include a brief explanation of what it means, likely causes, and general dietary/lifestyle suggestions the patient can discuss with their clinician. Plain text only, no markdown"
        )
        try:
            explanation = call_gemini(prompt)
        except Exception as gemini_exc:
            return jsonify(
                {
                    "diagnosis": diagnosis,
                    "prediction": diagnosis,
                    "gemini_error": str(gemini_exc),
                }
            )
        return jsonify(
            {"diagnosis": diagnosis, "prediction": diagnosis, "explanation": explanation}
        )
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)