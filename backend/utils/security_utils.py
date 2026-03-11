"""
Security utilities: secure filename, file validation, admin decorator.
"""
import os
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from werkzeug.utils import secure_filename as _secure_filename

ALLOWED_EXTENSIONS = {"csv"}
MAX_FILENAME_LENGTH = 120


def secure_upload_filename(filename: str) -> str:
    """Return a safe filename, stripping path components."""
    name = _secure_filename(filename)
    if not name:
        raise ValueError("Invalid filename")
    return name[:MAX_FILENAME_LENGTH]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Admin privileges required.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated
