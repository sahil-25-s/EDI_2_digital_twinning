"""Rule-based digital twin: simulates health/well-being state over N days."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import uuid


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass
class StaticProfile:
    age: int
    gender: str
    height_cm: float
    bmi: float
    diet_type: str
    exercise_level: str
    smoking_status: str
    alcohol_consumption: str
    sun_exposure: str

    @property
    def weight_kg(self) -> float:
        height_m = self.height_cm / 100.0
        return self.bmi * (height_m ** 2)

    @property
    def is_underweight(self) -> bool:
        return self.bmi < 18.5

    @property
    def is_overweight(self) -> bool:
        return self.bmi >= 25.0


@dataclass
class DailyHabits:
    simulation_days: int
    calories_per_day: float
    protein_per_day: float
    carbohydrates_per_day: float
    fats_per_day: float
    water_intake_liters: float
    sleep_hours: float
    screen_time_hours: float
    vitamin_d_percent_rda: float
    vitamin_b12_percent_rda: float
    iron_percent_rda: float


@dataclass
class TwinState:
    energy_level: float = 70.0
    focus_level: float = 70.0
    fatigue_level: float = 30.0
    stress_level: float = 30.0
    hydration_score: float = 70.0
    nutrition_score: float = 70.0
    deficiency_risk: float = 25.0
    skin_health: float = 70.0
    hair_health: float = 70.0
    immune_resilience: float = 70.0
    sleep_quality: float = 70.0
    metabolic_balance: float = 70.0
    mood_stability: float = 70.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass
class PersonalizedTargets:
    calories: float
    protein_g: float
    water_liters: float
    sleep_hours: float
    vitamin_d_rda: float
    vitamin_b12_rda: float
    iron_rda: float
    screen_time_max_hours: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


class DigitalTwin:
    """In-memory digital twin with rule-based daily state evolution."""

    _registry: dict[str, "DigitalTwin"] = {}

    def __init__(self, profile: StaticProfile, twin_id: str | None = None):
        self.twin_id = twin_id or str(uuid.uuid4())
        self.profile = profile
        self.state = self._initial_state()
        self.targets = self._compute_targets()
        self.day_history: list[dict[str, Any]] = []
        DigitalTwin._registry[self.twin_id] = self

    @classmethod
    def get(cls, twin_id: str) -> "DigitalTwin | None":
        return cls._registry.get(twin_id)

    @classmethod
    def list_ids(cls) -> list[str]:
        return list(cls._registry.keys())

    def _initial_state(self) -> TwinState:
        p = self.profile
        s = TwinState()
        if p.is_underweight:
            s.energy_level -= 8
            s.nutrition_score -= 10
            s.deficiency_risk += 12
        if p.is_overweight:
            s.metabolic_balance -= 10
            s.energy_level -= 5
        if p.smoking_status == "Current":
            s.immune_resilience -= 15
            s.skin_health -= 10
            s.hair_health -= 8
            s.deficiency_risk += 8
            s.fatigue_level += 10
        if p.alcohol_consumption in ("Heavy", "Moderate"):
            s.metabolic_balance -= 12 if p.alcohol_consumption == "Heavy" else 6
            s.sleep_quality -= 8
            s.fatigue_level += 8 if p.alcohol_consumption == "Heavy" else 4
        if p.exercise_level == "Sedentary":
            s.energy_level -= 5
            s.metabolic_balance -= 8
        elif p.exercise_level == "Active":
            s.energy_level += 5
            s.immune_resilience += 5
        if p.sun_exposure == "Low":
            s.deficiency_risk += 10
            s.skin_health -= 5
        elif p.sun_exposure == "High":
            s.skin_health += 3
        if p.diet_type in ("Vegan", "Vegetarian"):
            s.deficiency_risk += 6
        if p.age >= 60:
            s.immune_resilience -= 5
            s.skin_health -= 5
        return s

    def _activity_multiplier(self) -> float:
        return {
            "Sedentary": 1.2,
            "Light": 1.375,
            "Moderate": 1.55,
            "Active": 1.725,
        }.get(self.profile.exercise_level, 1.375)

    def _compute_targets(self) -> PersonalizedTargets:
        p = self.profile
        weight = p.weight_kg
        height_m = p.height_cm / 100.0

        if p.gender.lower() in ("male", "m"):
            bmr = 10 * weight + 6.25 * p.height_cm - 5 * p.age + 5
        else:
            bmr = 10 * weight + 6.25 * p.height_cm - 5 * p.age - 161

        calories = bmr * self._activity_multiplier()
        if p.is_underweight:
            calories *= 1.1
        if p.is_overweight:
            calories *= 0.92

        protein_mult = {"Sedentary": 0.8, "Light": 0.9, "Moderate": 1.0, "Active": 1.2}.get(
            p.exercise_level, 0.9
        )
        protein_g = weight * protein_mult
        if p.is_underweight:
            protein_g *= 1.15

        water_liters = (weight * 0.035) + (
            0.5 if p.exercise_level in ("Moderate", "Active") else 0.0
        )
        if p.height_cm >= 180:
            water_liters += 0.3

        vitamin_d_rda = 100.0
        vitamin_b12_rda = 100.0
        iron_rda = 100.0
        if p.sun_exposure == "Low":
            vitamin_d_rda = 120.0
        if p.diet_type in ("Vegan", "Vegetarian"):
            vitamin_b12_rda = 115.0
            iron_rda = 115.0
        if p.gender.lower() in ("female", "f") and p.age < 50:
            iron_rda = 110.0

        return PersonalizedTargets(
            calories=round(calories),
            protein_g=round(protein_g, 1),
            water_liters=round(water_liters, 2),
            sleep_hours=8.0 if p.age < 65 else 7.5,
            vitamin_d_rda=vitamin_d_rda,
            vitamin_b12_rda=vitamin_b12_rda,
            iron_rda=iron_rda,
            screen_time_max_hours=6.0 if p.age >= 18 else 4.0,
        )

    def _score_ratio(self, actual: float, target: float) -> float:
        if target <= 0:
            return 50.0
        ratio = actual / target
        if 0.9 <= ratio <= 1.1:
            return 95.0
        if 0.75 <= ratio < 0.9 or 1.1 < ratio <= 1.25:
            return 75.0
        if 0.6 <= ratio < 0.75 or 1.25 < ratio <= 1.4:
            return 55.0
        return 35.0

    def _apply_daily_rules(self, habits: DailyHabits) -> dict[str, float]:
        t = self.targets
        day_scores = {
            "calorie_match": self._score_ratio(habits.calories_per_day, t.calories),
            "protein_match": self._score_ratio(habits.protein_per_day, t.protein_g),
            "hydration": self._score_ratio(habits.water_intake_liters, t.water_liters),
            "vitamin_d": self._score_ratio(habits.vitamin_d_percent_rda, t.vitamin_d_rda),
            "vitamin_b12": self._score_ratio(habits.vitamin_b12_percent_rda, t.vitamin_b12_rda),
            "iron": self._score_ratio(habits.iron_percent_rda, t.iron_rda),
        }

        sleep = habits.sleep_hours
        sleep_target = t.sleep_hours
        if abs(sleep - sleep_target) <= 0.5:
            day_scores["sleep"] = 95.0
        elif abs(sleep - sleep_target) <= 1.5:
            day_scores["sleep"] = 70.0
        else:
            day_scores["sleep"] = 40.0

        screen = habits.screen_time_hours
        if screen <= t.screen_time_max_hours:
            day_scores["screen"] = 90.0
        elif screen <= t.screen_time_max_hours + 2:
            day_scores["screen"] = 65.0
        else:
            day_scores["screen"] = 35.0

        macro_total = habits.carbohydrates_per_day + habits.fats_per_day + habits.protein_per_day * 4
        if macro_total > 0:
            protein_share = (habits.protein_per_day * 4) / macro_total
            day_scores["macro_balance"] = 85.0 if 0.15 <= protein_share <= 0.35 else 55.0
        else:
            day_scores["macro_balance"] = 50.0

        return day_scores

    def _update_state(self, day_scores: dict[str, float], habits: DailyHabits) -> None:
        s = self.state
        nutrition_avg = (
            day_scores["calorie_match"]
            + day_scores["protein_match"]
            + day_scores["macro_balance"]
        ) / 3
        micronutrient_avg = (
            day_scores["vitamin_d"]
            + day_scores["vitamin_b12"]
            + day_scores["iron"]
        ) / 3

        s.nutrition_score = _clamp(s.nutrition_score * 0.85 + nutrition_avg * 0.15)
        s.hydration_score = _clamp(s.hydration_score * 0.85 + day_scores["hydration"] * 0.15)
        s.sleep_quality = _clamp(s.sleep_quality * 0.85 + day_scores["sleep"] * 0.15)

        s.energy_level = _clamp(
            s.energy_level * 0.9
            + (nutrition_avg * 0.4 + day_scores["sleep"] * 0.4 + day_scores["hydration"] * 0.2) * 0.1
        )
        s.focus_level = _clamp(
            s.focus_level * 0.9
            + (day_scores["sleep"] * 0.5 + day_scores["screen"] * 0.5) * 0.1
        )
        daily_fatigue_pressure = (
            (100 - day_scores["sleep"]) * 0.35
            + (100 - nutrition_avg) * 0.25
            + (100 - day_scores["hydration"]) * 0.2
            + (100 - day_scores["screen"]) * 0.2
        )
        s.fatigue_level = _clamp(s.fatigue_level + (daily_fatigue_pressure - 52) * 0.22)
        s.stress_level = _clamp(
            s.stress_level * 0.92
            + (100 - day_scores["screen"]) * 0.04
            + (100 - day_scores["sleep"]) * 0.04
        )
        s.deficiency_risk = _clamp(
            s.deficiency_risk * 0.88 + (100 - micronutrient_avg) * 0.12
        )
        s.skin_health = _clamp(
            s.skin_health * 0.92
            + (day_scores["hydration"] * 0.3 + day_scores["vitamin_d"] * 0.4 + day_scores["sleep"] * 0.3) * 0.08
        )
        s.hair_health = _clamp(
            s.hair_health * 0.92
            + (day_scores["protein_match"] * 0.4 + day_scores["iron"] * 0.35 + day_scores["vitamin_b12"] * 0.25) * 0.08
        )
        s.immune_resilience = _clamp(
            s.immune_resilience * 0.93
            + (micronutrient_avg * 0.4 + day_scores["sleep"] * 0.35 + nutrition_avg * 0.25) * 0.07
        )
        s.metabolic_balance = _clamp(
            s.metabolic_balance * 0.9
            + (day_scores["calorie_match"] * 0.5 + day_scores["macro_balance"] * 0.5) * 0.1
        )
        s.mood_stability = _clamp(
            s.mood_stability * 0.9
            + (day_scores["sleep"] * 0.4 + (100 - s.stress_level) * 0.3 + nutrition_avg * 0.3) * 0.1
        )

        p = self.profile
        if p.smoking_status == "Current":
            s.immune_resilience = _clamp(s.immune_resilience - 0.5)
            s.skin_health = _clamp(s.skin_health - 0.4)
        if p.alcohol_consumption == "Heavy":
            s.sleep_quality = _clamp(s.sleep_quality - 0.8)
            s.metabolic_balance = _clamp(s.metabolic_balance - 0.5)

    def _generate_recommendations(self) -> list[str]:
        s = self.state
        t = self.targets
        recs: list[str] = []

        if s.fatigue_level > 70:
            recs.append("Increase protein intake and sleep duration.")
        if s.hydration_score < 55:
            recs.append(
                f"Increase daily water intake toward {t.water_liters} L based on your height and weight."
            )
        if s.nutrition_score < 55:
            recs.append(
                f"Adjust calories toward ~{t.calories} kcal and protein toward ~{t.protein_g} g per day."
            )
        if s.deficiency_risk > 65:
            recs.append(
                "Raise vitamin D, B12, and iron intake toward your personalized RDA targets."
            )
        if s.sleep_quality < 55:
            recs.append(f"Aim for about {t.sleep_hours} hours of sleep per night.")
        if s.stress_level > 65:
            recs.append("Reduce screen time and add short recovery breaks during the day.")
        if s.skin_health < 55 or s.hair_health < 55:
            recs.append("Improve hydration, protein, and micronutrient consistency for skin and hair health.")
        if s.metabolic_balance < 55 and self.profile.is_overweight:
            recs.append("Balance calories and activity to support gradual metabolic improvement.")
        if self.profile.is_underweight and s.energy_level < 55:
            recs.append("Consider slightly higher calories and protein to support healthy weight gain.")
        if self.profile.sun_exposure == "Low" and s.deficiency_risk > 50:
            recs.append("Prioritize vitamin D sources or safe sun exposure given low sun exposure.")
        if not recs:
            recs.append("Maintain current habits; overall trajectory looks stable.")

        return recs

    def simulate(self, habits: DailyHabits) -> dict[str, Any]:
        days = max(1, min(habits.simulation_days, 365))
        for day in range(1, days + 1):
            scores = self._apply_daily_rules(habits)
            self._update_state(scores, habits)
            self.day_history.append({"day": day, "scores": scores, "state": self.state.to_dict()})

        return {
            "twin_id": self.twin_id,
            "simulation_days": days,
            "profile": asdict(self.profile),
            "personalized_targets": self.targets.to_dict(),
            "final_state": self.state.to_dict(),
            "recommendations": self._generate_recommendations(),
            "history": self.day_history[-min(7, len(self.day_history)) :],
        }

    @staticmethod
    def from_payload(data: dict[str, Any]) -> tuple["DigitalTwin", DailyHabits]:
        static = StaticProfile(
            age=int(data["age"]),
            gender=str(data["gender"]),
            height_cm=float(data["height_cm"]),
            bmi=float(data["bmi"]),
            diet_type=str(data["diet_type"]),
            exercise_level=str(data["exercise_level"]),
            smoking_status=str(data["smoking_status"]),
            alcohol_consumption=str(data.get("alcohol_consumption") or "None"),
            sun_exposure=str(data["sun_exposure"]),
        )
        habits = DailyHabits(
            simulation_days=int(data.get("simulation_days", 7)),
            calories_per_day=float(data["calories_per_day"]),
            protein_per_day=float(data["protein_per_day"]),
            carbohydrates_per_day=float(data["carbohydrates_per_day"]),
            fats_per_day=float(data["fats_per_day"]),
            water_intake_liters=float(data["water_intake_liters"]),
            sleep_hours=float(data["sleep_hours"]),
            screen_time_hours=float(data["screen_time_hours"]),
            vitamin_d_percent_rda=float(data["vitamin_d_percent_rda"]),
            vitamin_b12_percent_rda=float(data["vitamin_b12_percent_rda"]),
            iron_percent_rda=float(data["iron_percent_rda"]),
        )
        twin_id = data.get("twin_id")
        if twin_id and DigitalTwin.get(twin_id):
            twin = DigitalTwin.get(twin_id)
            assert twin is not None
            return twin, habits
        return DigitalTwin(static, twin_id=twin_id), habits
