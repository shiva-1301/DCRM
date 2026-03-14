"""
Prediction service — run a single CSV through the model and persist the result.
"""
import numpy as np
from flask_login import current_user

from .ml_service import load_model_and_scaler
from .csv_parser_service import extract_features_from_file, convert_407b_to_arc_format, extract_timeseries
from ..database.database import save_prediction


def run_prediction(filepath: str) -> dict:
    """
    Full pipeline: normalise → extract features → predict → persist.
    Returns a result dict or raises RuntimeError.
    """
    # Normalise 407_B layout if needed
    _, norm_err = convert_407b_to_arc_format(filepath)
    if norm_err:
        raise RuntimeError(f"Normalisation error: {norm_err}")

    # Extract 24 statistical features (NOT raw flattened data)
    features, parse_err = extract_features_from_file(filepath)
    if parse_err or features is None:
        raise RuntimeError(f"Feature extraction error: {parse_err}")

    model, scaler, load_err = load_model_and_scaler()
    if load_err:
        raise RuntimeError(f"Model load error: {load_err}")

    # Features should already be 24 values — matching the scaler
    scaled = scaler.transform([features])
    prediction = model.predict(scaled)[0]
    proba = model.predict_proba(scaled)[0]
    prob_dict = {cls: float(p) for cls, p in zip(model.classes_, proba)}

    save_prediction(
        user_id=current_user.id,
        filename=filepath.rsplit("/", 1)[-1].rsplit("\\", 1)[-1],
        prediction=prediction,
        probabilities=prob_dict,
        vector_size=int(len(features)),
    )

    return {
        "prediction": prediction,
        "probabilities": prob_dict,
        "vector_size": int(len(features)),
        "filepath": filepath,
    }


def run_analysis(filepath: str) -> dict:
    """Like run_prediction but also returns graph time-series data."""
    result = run_prediction(filepath)
    result["graph_data"] = extract_timeseries(filepath)
    return result
