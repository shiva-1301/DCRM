from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

chatbot_bp = Blueprint("chatbot", __name__)

RESPONSES = {
    ("hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"):
        "Hello! I'm your Field Advisor chatbot. How can I assist you with the DCRM system today?",
    ("healthy", "normal reading"):
        "A healthy DCRM reading indicates normal contact resistance with no faults detected. Your equipment is functioning properly.",
    ("main contact", "main fault"):
        "Main contact fault indicates issues with the primary contact mechanism. Immediate inspection is recommended.",
    ("arc", "arcing"):
        "Arc fault detected — electrical arcing in the contact system. This requires IMMEDIATE attention.",
    ("dcrm",):
        "DCRM (Dynamic Contact Resistance Measurement) analyses contacts and classifies them as healthy, main fault, or arc fault using machine learning.",
    ("upload", "csv", "file"):
        "To upload: 1) Click 'Browse Files', 2) Select your CSV, 3) Click 'Predict' to analyse. Make sure your CSV contains Channel-1 data.",
    ("prediction", "result", "classify"):
        "Predictions show the probability of each fault type. Always validate by clicking 'Correct' or 'Incorrect' to improve the model.",
    ("retrain", "training", "improve", "model"):
        "If a prediction is incorrect, click 'Incorrect' and pick the right label. The system retrains automatically.",
    ("sos", "problem", "stuck", "error"):
        "You can send an SOS to your admin, chat with colleagues on the Interactions page, or ask me more questions.",
    ("history", "past", "previous", "track"):
        "View all your past predictions on the 'My History' page — filename, fault type, confidence and timestamp are all recorded.",
    ("thank", "thanks", "appreciate"):
        "You're welcome! Feel free to ask any time.",
    ("bye", "goodbye", "see you", "farewell"):
        "Goodbye! Come back anytime you need help.",
    ("who are you", "what are you", "your name"):
        "I'm the Field Advisor chatbot — your 24/7 assistant for the DCRM system.",
}


def _match(question_lower: str) -> str:
    for keywords, response in RESPONSES.items():
        if any(kw in question_lower for kw in keywords):
            return response
    return (
        "I can help with DCRM questions, file uploads, predictions, troubleshooting and more. "
        "Could you be more specific?"
    )


@chatbot_bp.route("/field-advisor")
@login_required
def field_advisor():
    return render_template("field_advisor.html", user=current_user)


@chatbot_bp.route("/api/chatbot/ask", methods=["POST"])
@login_required
def chatbot_ask():
    data = request.json or {}
    question = (data.get("question") or "").strip()[:500]
    if not question:
        return jsonify({"error": "Question is required"}), 400
    response = _match(question.lower())
    return jsonify({"response": response})
