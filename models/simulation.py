from datetime import datetime

from extensions import db


class SimulationRun(db.Model):
    """One digital twin simulation execution and its outputs."""

    __tablename__ = "simulation_runs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    twin_id = db.Column(db.String(64), nullable=True)

    simulation_days = db.Column(db.Integer, nullable=False)
    disease_diagnosis = db.Column(db.String(128), nullable=True)
    symptoms_list = db.Column(db.String(512), nullable=True)

    personalized_targets = db.Column(db.JSON, nullable=True)
    final_state = db.Column(db.JSON, nullable=True)
    recommendations = db.Column(db.JSON, nullable=True)
    clinical_assessment = db.Column(db.JSON, nullable=True)
    input_payload = db.Column(db.JSON, nullable=True)
    gemini_feedback = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="simulation_runs")
