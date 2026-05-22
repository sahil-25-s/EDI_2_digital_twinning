"""Persistence helpers for users, profiles, and simulation runs."""

from __future__ import annotations

from typing import Any

from extensions import db
from models import SimulationRun, UserClinicalBaseline, UserDailyHabits, UserProfile


def _int_flag(value) -> int:
    return 1 if str(value) in ("1", "true", "True", "on") else 0


def save_user_profile(user_id: int, payload: dict[str, Any]) -> UserProfile:
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)

    profile.age = int(payload["age"])
    profile.gender = str(payload["gender"])
    profile.height_cm = float(payload["height_cm"])
    profile.bmi = float(payload["bmi"])
    profile.diet_type = str(payload["diet_type"])
    profile.exercise_level = str(payload["exercise_level"])
    profile.smoking_status = str(payload["smoking_status"])
    profile.alcohol_consumption = str(payload.get("alcohol_consumption") or "None")
    profile.sun_exposure = str(payload["sun_exposure"])
    profile.income_level = str(payload.get("income_level", "Middle"))
    profile.latitude_region = str(payload.get("latitude_region", "Mid"))
    db.session.commit()
    return profile


def save_user_clinical(user_id: int, payload: dict[str, Any]) -> UserClinicalBaseline:
    clinical = UserClinicalBaseline.query.filter_by(user_id=user_id).first()
    if not clinical:
        clinical = UserClinicalBaseline(user_id=user_id)
        db.session.add(clinical)

    clinical.vitamin_a_percent_rda = float(payload["vitamin_a_percent_rda"])
    clinical.vitamin_c_percent_rda = float(payload["vitamin_c_percent_rda"])
    clinical.vitamin_e_percent_rda = float(payload["vitamin_e_percent_rda"])
    clinical.folate_percent_rda = float(payload["folate_percent_rda"])
    clinical.calcium_percent_rda = float(payload["calcium_percent_rda"])
    clinical.hemoglobin_g_dl = float(payload["hemoglobin_g_dl"])
    clinical.serum_vitamin_d_ng_ml = float(payload["serum_vitamin_d_ng_ml"])
    clinical.serum_vitamin_b12_pg_ml = float(payload["serum_vitamin_b12_pg_ml"])
    clinical.serum_folate_ng_ml = float(payload["serum_folate_ng_ml"])
    clinical.symptoms_count = int(payload.get("symptoms_count", 0))
    clinical.symptoms_list = payload.get("symptoms_list") or None
    clinical.has_night_blindness = _int_flag(payload.get("has_night_blindness", 0))
    clinical.has_fatigue = _int_flag(payload.get("has_fatigue", 0))
    clinical.has_bleeding_gums = _int_flag(payload.get("has_bleeding_gums", 0))
    clinical.has_bone_pain = _int_flag(payload.get("has_bone_pain", 0))
    clinical.has_muscle_weakness = _int_flag(payload.get("has_muscle_weakness", 0))
    clinical.has_numbness_tingling = _int_flag(payload.get("has_numbness_tingling", 0))
    clinical.has_memory_problems = _int_flag(payload.get("has_memory_problems", 0))
    clinical.has_pale_skin = _int_flag(payload.get("has_pale_skin", 0))
    clinical.has_multiple_deficiencies = _int_flag(payload.get("has_multiple_deficiencies", 0))
    db.session.commit()
    return clinical


def save_user_habits(user_id: int, payload: dict[str, Any]) -> UserDailyHabits:
    habits = UserDailyHabits.query.filter_by(user_id=user_id).first()
    if not habits:
        habits = UserDailyHabits(user_id=user_id)
        db.session.add(habits)

    habits.calories_per_day = float(payload["calories_per_day"])
    habits.protein_per_day = float(payload["protein_per_day"])
    habits.carbohydrates_per_day = float(payload["carbohydrates_per_day"])
    habits.fats_per_day = float(payload["fats_per_day"])
    habits.water_intake_liters = float(payload["water_intake_liters"])
    habits.sleep_hours = float(payload["sleep_hours"])
    habits.screen_time_hours = float(payload["screen_time_hours"])
    habits.vitamin_d_percent_rda = float(payload["vitamin_d_percent_rda"])
    habits.vitamin_b12_percent_rda = float(payload["vitamin_b12_percent_rda"])
    habits.iron_percent_rda = float(payload["iron_percent_rda"])
    db.session.commit()
    return habits


def save_all_user_data(user_id: int, payload: dict[str, Any]) -> None:
    save_user_profile(user_id, payload)
    save_user_clinical(user_id, payload)
    save_user_habits(user_id, payload)


def get_user_data_payload(user_id: int) -> dict[str, Any] | None:
    """Merge profile, clinical, and habits into one dict for forms/API."""
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None

    data: dict[str, Any] = {
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "bmi": profile.bmi,
        "diet_type": profile.diet_type,
        "exercise_level": profile.exercise_level,
        "smoking_status": profile.smoking_status,
        "alcohol_consumption": ""
        if str(profile.alcohol_consumption or "").strip().lower() in ("none", "nan", "")
        else profile.alcohol_consumption,
        "sun_exposure": profile.sun_exposure,
        "income_level": profile.income_level,
        "latitude_region": profile.latitude_region,
    }

    clinical = UserClinicalBaseline.query.filter_by(user_id=user_id).first()
    if clinical:
        data.update(
            {
                "vitamin_a_percent_rda": clinical.vitamin_a_percent_rda,
                "vitamin_c_percent_rda": clinical.vitamin_c_percent_rda,
                "vitamin_e_percent_rda": clinical.vitamin_e_percent_rda,
                "folate_percent_rda": clinical.folate_percent_rda,
                "calcium_percent_rda": clinical.calcium_percent_rda,
                "hemoglobin_g_dl": clinical.hemoglobin_g_dl,
                "serum_vitamin_d_ng_ml": clinical.serum_vitamin_d_ng_ml,
                "serum_vitamin_b12_pg_ml": clinical.serum_vitamin_b12_pg_ml,
                "serum_folate_ng_ml": clinical.serum_folate_ng_ml,
                "symptoms_count": clinical.symptoms_count,
                "symptoms_list": clinical.symptoms_list or "",
                "has_night_blindness": clinical.has_night_blindness,
                "has_fatigue": clinical.has_fatigue,
                "has_bleeding_gums": clinical.has_bleeding_gums,
                "has_bone_pain": clinical.has_bone_pain,
                "has_muscle_weakness": clinical.has_muscle_weakness,
                "has_numbness_tingling": clinical.has_numbness_tingling,
                "has_memory_problems": clinical.has_memory_problems,
                "has_pale_skin": clinical.has_pale_skin,
                "has_multiple_deficiencies": clinical.has_multiple_deficiencies,
            }
        )

    habits = UserDailyHabits.query.filter_by(user_id=user_id).first()
    if habits:
        data.update(
            {
                "calories_per_day": habits.calories_per_day,
                "protein_per_day": habits.protein_per_day,
                "carbohydrates_per_day": habits.carbohydrates_per_day,
                "fats_per_day": habits.fats_per_day,
                "water_intake_liters": habits.water_intake_liters,
                "sleep_hours": habits.sleep_hours,
                "screen_time_hours": habits.screen_time_hours,
                "vitamin_d_percent_rda": habits.vitamin_d_percent_rda,
                "vitamin_b12_percent_rda": habits.vitamin_b12_percent_rda,
                "iron_percent_rda": habits.iron_percent_rda,
            }
        )

    return data


def save_simulation_run(
    payload: dict[str, Any],
    result: dict[str, Any],
    user_id: int | None = None,
) -> int:
    run = SimulationRun(
        user_id=user_id,
        twin_id=result.get("twin_id"),
        simulation_days=result.get("simulation_days", 0),
        disease_diagnosis=result.get("disease_diagnosis"),
        symptoms_list=result.get("symptoms_list"),
        personalized_targets=result.get("personalized_targets"),
        final_state=result.get("final_state"),
        recommendations=result.get("recommendations"),
        clinical_assessment=result.get("clinical_assessment"),
        input_payload=payload,
        gemini_feedback=result.get("gemini_feedback"),
    )
    db.session.add(run)
    db.session.commit()
    return run.id
