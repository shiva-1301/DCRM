from flask import Blueprint, request, jsonify, make_response
from flask_login import login_required, current_user
from ..services.prediction_service import run_prediction, run_analysis
from ..services.retrain_service import add_correction_and_retrain
from ..services.report_service import generate_text_report
from ..services.ml_service import X_data, y_data, training_history, load_model_and_scaler
from ..database.database import get_user_predictions
from ..utils.file_utils import save_upload
from collections import Counter
from datetime import datetime, timedelta
import os

prediction_bp = Blueprint("prediction", __name__)


@prediction_bp.route("/api/predict", methods=["POST"])
@login_required
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        filepath = save_upload(request.files["file"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        result = run_prediction(filepath)
        result["filename"] = os.path.basename(filepath)
        return jsonify(result)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/api/analyze-csv", methods=["POST"])
@login_required
def analyze_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        filepath = save_upload(request.files["file"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    try:
        result = run_analysis(filepath)
        result["filename"] = os.path.basename(filepath)
        return jsonify(result)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/api/retrain", methods=["POST"])
@login_required
def retrain():
    data = request.json or {}
    filepath = data.get("filepath")
    label = data.get("correct_label")
    if not filepath or not label:
        return jsonify({"error": "filepath and correct_label are required"}), 400
    # Validate that the path is inside the uploads folder (prevent path traversal)
    from flask import current_app
    upload_dir = os.path.realpath(current_app.config["UPLOAD_FOLDER"])
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(upload_dir):
        return jsonify({"error": "Invalid filepath"}), 400
    try:
        result = add_correction_and_retrain(real_path, label)
        return jsonify({"message": "Model retrained successfully", **result})
    except (ValueError, RuntimeError) as e:
        return jsonify({"error": str(e)}), 400


@prediction_bp.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    import backend.services.ml_service as ml_svc
    model, _, err = load_model_and_scaler()
    if err:
        return jsonify({"error": err}), 500
    label_counts = Counter(ml_svc.y_data)
    history = ml_svc.training_history[-10:]
    return jsonify({
        "total_samples": len(ml_svc.X_data),
        "label_distribution": dict(label_counts),
        "training_history": history,
        "model_info": {
            "n_estimators": model.n_estimators,
            "n_features": getattr(model, "n_features_in_", "Unknown"),
        },
    })


@prediction_bp.route("/api/history", methods=["GET"])
@login_required
def get_history():
    import backend.services.ml_service as ml_svc
    return jsonify({"history": ml_svc.training_history})


@prediction_bp.route("/api/dashboard/analytics", methods=["GET"])
@login_required
def dashboard_analytics():
    all_preds = get_user_predictions(current_user.id, limit=1000)
    total = len(all_preds)
    healthy_count = sum(1 for p in all_preds if p["prediction"] == "healthy")
    avg_health = round((healthy_count / total * 100) if total else 0, 1)
    dist = Counter(p["prediction"] for p in all_preds)
    now = datetime.utcnow()
    thirty_ago = now - timedelta(days=30)
    daily_health: dict = {}
    daily_faults: dict = {}
    for p in all_preds:
        ts = p["timestamp"]
        d = ts.date() if hasattr(ts, "date") else datetime.fromisoformat(str(ts)).date()
        if d >= thirty_ago.date():
            k = d.isoformat()
            daily_health.setdefault(k, 0)
            daily_faults.setdefault(k, 0)
            if p["prediction"] == "healthy":
                daily_health[k] += 1
            else:
                daily_faults[k] += 1
    recent = []
    for p in all_preds[:10]:
        recent.append({
            "id": str(p["_id"]),
            "filename": p["filename"],
            "prediction": p["prediction"],
            "confidence": max(p["probabilities"].values()) * 100,
            "timestamp": p["timestamp"].isoformat() if hasattr(p["timestamp"], "isoformat") else str(p["timestamp"]),
        })
    return jsonify({
        "total_tests": total,
        "avg_health": avg_health,
        "fault_distribution": {"healthy": dist.get("healthy", 0), "main": dist.get("main", 0), "arc": dist.get("arc", 0)},
        "health_trend": [{"date": d, "count": c} for d, c in sorted(daily_health.items())],
        "spikes_trend": [{"date": d, "count": c} for d, c in sorted(daily_faults.items())],
        "recent_tests": recent,
    })


@prediction_bp.route("/api/user/reports", methods=["GET"])
@login_required
def user_reports():
    preds = get_user_predictions(current_user.id, limit=100)
    return jsonify({"reports": [{
        "_id": str(p["_id"]),
        "filename": p["filename"],
        "prediction": p["prediction"],
        "probabilities": p["probabilities"],
        "vector_size": p["vector_size"],
        "timestamp": p["timestamp"].isoformat() if hasattr(p["timestamp"], "isoformat") else str(p["timestamp"]),
    } for p in preds]})


@prediction_bp.route("/api/report/download/<report_id>", methods=["GET"])
@login_required
def download_report(report_id):
    try:
        content, filename = generate_text_report(report_id)
        response = make_response(content)
        response.headers["Content-Type"] = "text/plain"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except LookupError:
        return jsonify({"error": "Report not found"}), 404
    except PermissionError:
        return jsonify({"error": "Unauthorised"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/analysis")
@login_required
def analysis_page():
    from flask import render_template
    return render_template("analysis_new.html", user=current_user)
