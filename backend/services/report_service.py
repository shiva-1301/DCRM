"""
Report generation service.
"""
from datetime import datetime
from flask_login import current_user
from ..database.database import get_prediction_by_id


def generate_text_report(report_id: str) -> tuple:
    """
    Returns (content: str, filename: str) or raises LookupError / PermissionError.
    """
    prediction = get_prediction_by_id(report_id)
    if not prediction:
        raise LookupError("Report not found")
    if prediction["user_id"] != current_user.id:
        raise PermissionError("Access denied")

    sep = "=" * 60
    lines = [
        "DCRM TEST REPORT",
        sep,
        f"Report ID  : {report_id}",
        f"Generated  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"User       : {current_user.full_name or current_user.username}",
        sep,
        "FILE INFORMATION",
        sep,
        f"Filename   : {prediction['filename']}",
        f"Test Date  : {prediction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
        f"Vector Size: {prediction['vector_size']} features",
        sep,
        "PREDICTION RESULTS",
        sep,
        f"Classification: {prediction['prediction'].upper()}",
        "",
        "Confidence Levels:",
    ]
    for label, prob in sorted(prediction["probabilities"].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  {label.capitalize()}: {prob * 100:.2f}%")

    lines += [sep, "INTERPRETATION", sep]
    pred = prediction["prediction"]
    if pred == "healthy":
        lines += [
            "Status: HEALTHY",
            "Normal contact resistance — no faults detected.",
            "Recommendation: Continue regular monitoring.",
        ]
    elif pred == "main":
        lines += [
            "Status: MAIN CONTACT FAULT",
            "Issues with the primary contact mechanism detected.",
            "Recommendation: Immediate inspection — check contact surfaces.",
        ]
    else:
        lines += [
            "Status: ARC FAULT DETECTED",
            "Electrical arcing detected — IMMEDIATE ACTION REQUIRED.",
            "Recommendation: Contact supervisor and schedule emergency maintenance.",
        ]

    lines += [sep, "Model: Random Forest Classifier | Features: Channel-1 DCRM", sep, "END OF REPORT", sep]
    content = "\n".join(lines)
    filename = f"DCRM_Report_{report_id}.txt"
    return content, filename
