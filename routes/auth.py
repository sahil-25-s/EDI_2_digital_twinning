from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from db_service import get_user_data_payload, save_all_user_data
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


def _require_db() -> bool:
    return bool(current_app.config.get("SQLALCHEMY_DATABASE_URI"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_page"))

    if request.method == "GET":
        return render_template("login.html")

    if not _require_db():
        return jsonify({"error": "Database not configured"}), 503

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("Invalid email or password.")
        return redirect(url_for("auth.login"))

    login_user(user)
    next_page = request.args.get("next") or url_for("dashboard_page")
    return redirect(next_page)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_page"))

    if request.method == "GET":
        return render_template("register.html")

    if not _require_db():
        return jsonify({"error": "Database not configured"}), 503

    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm_password") or ""

    if not name or not email or not password:
        flash("Name, email, and password are required.")
        return redirect(url_for("auth.register"))
    if password != confirm:
        flash("Passwords do not match.")
        return redirect(url_for("auth.register"))
    if len(password) < 6:
        flash("Password must be at least 6 characters.")
        return redirect(url_for("auth.register"))
    if User.query.filter_by(email=email).first():
        flash("An account with this email already exists.")
        return redirect(url_for("auth.register"))

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    payload = request.form.to_dict()
    save_all_user_data(user.id, payload)

    login_user(user)
    flash("Account created. Your profile has been saved.")
    return redirect(url_for("dashboard_page"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/api/profile")
@login_required
def api_profile():
    data = get_user_data_payload(current_user.id)
    if not data:
        return jsonify({"error": "No profile saved yet"}), 404
    return jsonify(
        {
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
            },
            "profile": data,
        }
    )


@auth_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    payload = request.get_json() if request.is_json else request.form.to_dict()
    save_all_user_data(current_user.id, payload)
    return jsonify({"message": "Profile updated"})
