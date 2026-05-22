from datetime import datetime

from extensions import db


class UserProfile(db.Model):
    """Static lifestyle profile (age, BMI, diet, etc.)."""

    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(32), nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    diet_type = db.Column(db.String(64), nullable=False)
    exercise_level = db.Column(db.String(64), nullable=False)
    smoking_status = db.Column(db.String(64), nullable=False)
    alcohol_consumption = db.Column(db.String(64), nullable=False, default="None")
    sun_exposure = db.Column(db.String(64), nullable=False)
    income_level = db.Column(db.String(64), nullable=False, default="Middle")
    latitude_region = db.Column(db.String(64), nullable=False, default="Mid")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")


class UserClinicalBaseline(db.Model):
    """Labs, symptoms, and flags used for ML + twin baseline."""

    __tablename__ = "user_clinical_baselines"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    vitamin_a_percent_rda = db.Column(db.Float, nullable=True)
    vitamin_c_percent_rda = db.Column(db.Float, nullable=True)
    vitamin_e_percent_rda = db.Column(db.Float, nullable=True)
    folate_percent_rda = db.Column(db.Float, nullable=True)
    calcium_percent_rda = db.Column(db.Float, nullable=True)
    hemoglobin_g_dl = db.Column(db.Float, nullable=True)
    serum_vitamin_d_ng_ml = db.Column(db.Float, nullable=True)
    serum_vitamin_b12_pg_ml = db.Column(db.Float, nullable=True)
    serum_folate_ng_ml = db.Column(db.Float, nullable=True)
    symptoms_count = db.Column(db.Integer, default=0)
    symptoms_list = db.Column(db.String(512), nullable=True)
    has_night_blindness = db.Column(db.Integer, default=0)
    has_fatigue = db.Column(db.Integer, default=0)
    has_bleeding_gums = db.Column(db.Integer, default=0)
    has_bone_pain = db.Column(db.Integer, default=0)
    has_muscle_weakness = db.Column(db.Integer, default=0)
    has_numbness_tingling = db.Column(db.Integer, default=0)
    has_memory_problems = db.Column(db.Integer, default=0)
    has_pale_skin = db.Column(db.Integer, default=0)
    has_multiple_deficiencies = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="clinical")


class UserDailyHabits(db.Model):
    """Default daily habits the user plans to follow."""

    __tablename__ = "user_daily_habits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    calories_per_day = db.Column(db.Float, nullable=False)
    protein_per_day = db.Column(db.Float, nullable=False)
    carbohydrates_per_day = db.Column(db.Float, nullable=False)
    fats_per_day = db.Column(db.Float, nullable=False)
    water_intake_liters = db.Column(db.Float, nullable=False)
    sleep_hours = db.Column(db.Float, nullable=False)
    screen_time_hours = db.Column(db.Float, nullable=False)
    vitamin_d_percent_rda = db.Column(db.Float, nullable=False)
    vitamin_b12_percent_rda = db.Column(db.Float, nullable=False)
    iron_percent_rda = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="daily_habits")
