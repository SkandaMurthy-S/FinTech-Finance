from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html", user=current_user, current_year=datetime.utcnow().year)


@bp.route("/profile")
@login_required
def profile_page():
    return redirect(url_for("dashboard.dashboard_page"))
