from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..database.database import (
    get_user_statistics, get_all_employees, get_all_predictions,
    get_all_sos_requests, get_user_by_id, get_predictions_by_employee,
    create_user, delete_user, update_password,
)
from ..utils.security_utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("")
@login_required
@admin_required
def dashboard():
    stats = get_user_statistics()
    employees = get_all_employees()
    predictions = get_all_predictions(limit=20)
    all_sos = get_all_sos_requests()
    pending = [s for s in all_sos if s.get("status") == "pending"]
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        employees=employees,
        predictions=predictions,
        user=current_user,
        pending_sos=pending[:5],
        pending_sos_count=len(pending),
    )


@admin_bp.route("/add-employee", methods=["POST"])
@login_required
@admin_required
def add_employee():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    full_name = request.form.get("full_name", "")
    if not all([username, email, password]):
        flash("All fields are required.", "danger")
        return redirect(url_for("admin.dashboard"))
    user, error = create_user(username, email, password, role="employee", full_name=full_name)
    flash(f"Employee {username} added." if user else f"Error: {error}", "success" if user else "danger")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/delete-employee/<user_id>", methods=["POST"])
@login_required
@admin_required
def delete_employee(user_id):
    ok = delete_user(user_id)
    flash("Employee deleted." if ok else "Failed to delete employee.", "success" if ok else "danger")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/employee-predictions/<user_id>")
@login_required
@admin_required
def employee_predictions(user_id):
    employee = get_user_by_id(user_id)
    predictions = get_predictions_by_employee(user_id)
    return render_template("employee_predictions.html", employee=employee, predictions=predictions, user=current_user)


@admin_bp.route("/sos")
@login_required
@admin_required
def sos_management():
    all_sos = get_all_sos_requests()
    return render_template("admin_sos.html", user=current_user, sos_requests=all_sos)
