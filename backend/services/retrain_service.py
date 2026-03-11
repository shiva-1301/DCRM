"""
Retrain service — adds a correction to in-memory data and retrains the model.
"""
import os
import numpy as np
from datetime import datetime
from flask_login import current_user

from .ml_service import (
    X_data, y_data, training_history,
    load_signature, align_vector,
    train_model, save_dataset, save_training_history,
)
from .csv_parser_service import load_signature
from ..database.database import save_training_log

VALID_LABELS = {"healthy", "main", "arc"}


def add_correction_and_retrain(filepath: str, correct_label: str) -> dict:
    """
    Append (filepath, correct_label) to the dataset, retrain, persist.
    Returns summary dict or raises RuntimeError.
    """
    global X_data, y_data, training_history
    # Import module-level lists directly so mutations are shared
    import backend.services.ml_service as ml_svc

    if correct_label not in VALID_LABELS:
        raise ValueError(f"Invalid label '{correct_label}'. Must be one of {VALID_LABELS}")

    vector, err = load_signature(filepath)
    if err or vector is None:
        raise RuntimeError(f"CSV parse error: {err}")

    # Align to existing feature length
    if ml_svc.X_data:
        vector = align_vector(vector, len(ml_svc.X_data[0]))

    ml_svc.X_data.append(vector)
    ml_svc.y_data.append(correct_label)
    save_dataset(ml_svc.X_data, ml_svc.y_data)

    X_arr = np.array([np.array(x) for x in ml_svc.X_data])
    model, scaler, train_err = train_model(X_arr, ml_svc.y_data)
    if train_err:
        raise RuntimeError(f"Training error: {train_err}")

    entry = {
        "timestamp": datetime.now().isoformat(),
        "filename": os.path.basename(filepath),
        "label": correct_label,
        "total_samples": len(ml_svc.X_data),
        "user_id": current_user.id,
    }
    ml_svc.training_history.append(entry)
    save_training_history()

    save_training_log(
        user_id=current_user.id,
        filename=os.path.basename(filepath),
        correct_label=correct_label,
        total_samples=len(ml_svc.X_data),
    )

    return {"total_samples": len(ml_svc.X_data), "training_entry": entry}
