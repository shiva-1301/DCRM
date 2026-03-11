from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..database.database import get_user_predictions

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard_new.html", user=current_user)


@dashboard_bp.route("/my-history")
@login_required
def my_history():
    predictions = get_user_predictions(current_user.id, limit=50)
    return render_template("my_history.html", predictions=predictions, user=current_user)


@dashboard_bp.route("/reports")
@login_required
def reports_page():
    reports = get_user_predictions(current_user.id, limit=100)
    return render_template("reports.html", reports=reports, user=current_user)


@dashboard_bp.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html", user=current_user)


@dashboard_bp.route("/user-guide")
@login_required
def user_guide():
    return render_template("user_guide.html", user=current_user)


@dashboard_bp.route("/graph-plotter")
@login_required
def graph_plotter():
    return render_template("graph_plotter.html", user=current_user)
