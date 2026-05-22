from datetime import datetime

from flask_login import UserMixin

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship("UserProfile", back_populates="user", uselist=False)
    clinical = db.relationship("UserClinicalBaseline", back_populates="user", uselist=False)
    daily_habits = db.relationship("UserDailyHabits", back_populates="user", uselist=False)
    simulation_runs = db.relationship("SimulationRun", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
