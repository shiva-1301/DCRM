from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from ..database.database import verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard" if current_user.is_admin() else "dashboard.index"))
    if request.method == "POST":
        user = verify_password(request.form.get("username"), request.form.get("password"))
        if user:
            login_user(user)
            flash(f"Welcome back, {user.full_name or user.username}!", "success")
            return redirect(url_for("admin.dashboard" if user.is_admin() else "dashboard.index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))
