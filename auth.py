from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from models import db
from models.user import User

bp = Blueprint("auth", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_page"))
    return render_template("index.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_page"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        identifier = (data.get("email") or data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        if not identifier or not password:
            if request.is_json:
                return jsonify({"success": False, "message": "Email and password are required."}), 400
            flash("Email and password are required.", "error")
            return render_template("login.html")

        user = User.query.filter((User.email == identifier) | (User.email == identifier.lower())).first()
        if not user or not user.verify_password(password):
            if request.is_json:
                return jsonify({"success": False, "message": "Invalid email or password."}), 401
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        login_user(user, remember=bool(data.get("remember_me")))
        if request.is_json:
            return jsonify({"success": True, "message": "Login successful.", "redirect": url_for("dashboard.dashboard_page")})
        flash("Login successful.", "success")
        return redirect(url_for("dashboard.dashboard_page"))

    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_page"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "")
        confirm_password = (data.get("confirm_password") or "")
        user_type = (data.get("user_type") or "Other").strip()

        if not name or not email or not password:
            if request.is_json:
                return jsonify({"success": False, "message": "All fields are required."}), 400
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 8:
            if request.is_json:
                return jsonify({"success": False, "message": "Password must be at least 8 characters long."}), 400
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html")

        if password != confirm_password:
            if request.is_json:
                return jsonify({"success": False, "message": "Passwords do not match."}), 400
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if "@" not in email or "." not in email:
            if request.is_json:
                return jsonify({"success": False, "message": "Please provide a valid email address."}), 400
            flash("Please provide a valid email address.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({"success": False, "message": "An account with this email already exists."}), 409
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        user = User(name=name, email=email, user_type=user_type)
        user.password = password
        db.session.add(user)
        db.session.commit()

        login_user(user)
        if request.is_json:
            return jsonify({"success": True, "message": "Account created successfully.", "redirect": url_for("dashboard.dashboard_page")})
        flash("Account created successfully.", "success")
        return redirect(url_for("dashboard.dashboard_page"))

    return render_template("register.html")


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/api/auth/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user": current_user.to_public_dict()})
