"""Initial user and simulation tables

Revision ID: 001_initial
Revises:
Create Date: 2026-05-20

"""
from alembic import op
import sqlalchemy as sa


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=32), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("bmi", sa.Float(), nullable=False),
        sa.Column("diet_type", sa.String(length=64), nullable=False),
        sa.Column("exercise_level", sa.String(length=64), nullable=False),
        sa.Column("smoking_status", sa.String(length=64), nullable=False),
        sa.Column("alcohol_consumption", sa.String(length=64), nullable=False),
        sa.Column("sun_exposure", sa.String(length=64), nullable=False),
        sa.Column("income_level", sa.String(length=64), nullable=False),
        sa.Column("latitude_region", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "user_clinical_baselines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vitamin_a_percent_rda", sa.Float(), nullable=True),
        sa.Column("vitamin_c_percent_rda", sa.Float(), nullable=True),
        sa.Column("vitamin_e_percent_rda", sa.Float(), nullable=True),
        sa.Column("folate_percent_rda", sa.Float(), nullable=True),
        sa.Column("calcium_percent_rda", sa.Float(), nullable=True),
        sa.Column("hemoglobin_g_dl", sa.Float(), nullable=True),
        sa.Column("serum_vitamin_d_ng_ml", sa.Float(), nullable=True),
        sa.Column("serum_vitamin_b12_pg_ml", sa.Float(), nullable=True),
        sa.Column("serum_folate_ng_ml", sa.Float(), nullable=True),
        sa.Column("symptoms_count", sa.Integer(), nullable=True),
        sa.Column("symptoms_list", sa.String(length=512), nullable=True),
        sa.Column("has_night_blindness", sa.Integer(), nullable=True),
        sa.Column("has_fatigue", sa.Integer(), nullable=True),
        sa.Column("has_bleeding_gums", sa.Integer(), nullable=True),
        sa.Column("has_bone_pain", sa.Integer(), nullable=True),
        sa.Column("has_muscle_weakness", sa.Integer(), nullable=True),
        sa.Column("has_numbness_tingling", sa.Integer(), nullable=True),
        sa.Column("has_memory_problems", sa.Integer(), nullable=True),
        sa.Column("has_pale_skin", sa.Integer(), nullable=True),
        sa.Column("has_multiple_deficiencies", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "user_daily_habits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("calories_per_day", sa.Float(), nullable=False),
        sa.Column("protein_per_day", sa.Float(), nullable=False),
        sa.Column("carbohydrates_per_day", sa.Float(), nullable=False),
        sa.Column("fats_per_day", sa.Float(), nullable=False),
        sa.Column("water_intake_liters", sa.Float(), nullable=False),
        sa.Column("sleep_hours", sa.Float(), nullable=False),
        sa.Column("screen_time_hours", sa.Float(), nullable=False),
        sa.Column("vitamin_d_percent_rda", sa.Float(), nullable=False),
        sa.Column("vitamin_b12_percent_rda", sa.Float(), nullable=False),
        sa.Column("iron_percent_rda", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("twin_id", sa.String(length=64), nullable=True),
        sa.Column("simulation_days", sa.Integer(), nullable=False),
        sa.Column("disease_diagnosis", sa.String(length=128), nullable=True),
        sa.Column("symptoms_list", sa.String(length=512), nullable=True),
        sa.Column("personalized_targets", sa.JSON(), nullable=True),
        sa.Column("final_state", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("clinical_assessment", sa.JSON(), nullable=True),
        sa.Column("input_payload", sa.JSON(), nullable=True),
        sa.Column("gemini_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_simulation_runs_user_id"), "simulation_runs", ["user_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_simulation_runs_user_id"), table_name="simulation_runs")
    op.drop_table("simulation_runs")
    op.drop_table("user_daily_habits")
    op.drop_table("user_clinical_baselines")
    op.drop_table("user_profiles")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
