"""
ML service — model/scaler loading, training, vector alignment, dataset persistence.
"""
import os
import glob
import json
import numpy as np
import joblib
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from typing import Tuple, Optional, List

from .csv_parser_service import load_signature


# ── In-memory state (populated on startup) ─────────────────────────────────────
X_data: List[np.ndarray] = []
y_data: List[str] = []
training_history: List[dict] = []


def _cfg():
    """Lazy import to avoid circular deps at module load time."""
    from flask import current_app
    return current_app.config


# ── Dataset persistence ─────────────────────────────────────────────────────────
def save_dataset(X: list, y: list) -> bool:
    path = _cfg()["DATASET_PATH"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        np.savez(path, X=np.array(X, dtype=object), y=np.array(y, dtype=object))
        return True
    except Exception as exc:
        print(f"❌ Error saving dataset: {exc}")
        return False


def load_dataset() -> Tuple[list, list]:
    global X_data, y_data
    path = _cfg()["DATASET_PATH"]
    if os.path.exists(path):
        try:
            data = np.load(path, allow_pickle=True)
            X_data = list(data["X"])
            y_data = list(data["y"])
            print(f"📁 Loaded dataset: {len(X_data)} samples")
            return X_data, y_data
        except Exception as exc:
            print(f"⚠ Error loading dataset: {exc}")
    X_data, y_data = [], []
    return X_data, y_data


def load_initial_training_data(data_folder: str) -> Tuple[list, list]:
    X, y = [], []
    for fpath in glob.glob(os.path.join(data_folder, "*.csv")):
        fn = os.path.basename(fpath).lower()
        if "healthy" in fn:
            label = "healthy"
        elif "main" in fn:
            label = "main"
        elif "arc" in fn:
            label = "arc"
        else:
            continue
        vector, error = load_signature(fpath)
        if error or vector is None or vector.size == 0:
            continue
        X.append(vector)
        y.append(label)
    return X, y


# ── Training ─────────────────────────────────────────────────────────────────────
def align_vector(vector: np.ndarray, target_len: int) -> np.ndarray:
    if len(vector) == target_len:
        return vector
    if len(vector) > target_len:
        return vector[:target_len]
    return np.concatenate([vector, np.zeros(target_len - len(vector))])


def train_model(X: list, y: list) -> Tuple[Optional[object], Optional[object], Optional[str]]:
    cfg = _cfg()
    try:
        if not X or not y:
            return None, None, "No training data"
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = RandomForestClassifier(n_estimators=300, random_state=42)
        model.fit(X_scaled, y)
        os.makedirs(os.path.dirname(cfg["MODEL_PATH"]), exist_ok=True)
        joblib.dump(model, cfg["MODEL_PATH"])
        joblib.dump(scaler, cfg["SCALER_PATH"])
        return model, scaler, None
    except Exception as exc:
        return None, None, str(exc)


def load_model_and_scaler() -> Tuple[Optional[object], Optional[object], Optional[str]]:
    cfg = _cfg()
    try:
        model = joblib.load(cfg["MODEL_PATH"])
        scaler = joblib.load(cfg["SCALER_PATH"])
        return model, scaler, None
    except Exception as exc:
        return None, None, str(exc)


# ── Training-history persistence ───────────────────────────────────────────────
def load_training_history() -> list:
    global training_history
    path = _cfg()["TRAINING_HISTORY_PATH"]
    if os.path.exists(path):
        try:
            with open(path) as f:
                training_history = json.load(f)
        except Exception:
            training_history = []
    return training_history


def save_training_history() -> None:
    path = _cfg()["TRAINING_HISTORY_PATH"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(training_history, f, indent=2)
