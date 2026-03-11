"""
File utilities: save uploads, remove uploads.
"""
import os
from flask import current_app
from .security_utils import secure_upload_filename, allowed_file


def save_upload(file_storage) -> str:
    """Validate, sanitize and save an upload. Returns absolute filepath."""
    filename = file_storage.filename
    if not filename or not allowed_file(filename):
        raise ValueError("Only CSV files are accepted.")
    safe_name = secure_upload_filename(filename)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, safe_name)
    file_storage.save(filepath)
    return filepath


def remove_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass
