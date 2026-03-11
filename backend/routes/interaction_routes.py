from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..database.database import (
    save_message, get_conversation, get_user_conversations,
    mark_messages_as_read, get_user_by_id, get_all_employees,
)

interaction_bp = Blueprint("interaction", __name__)


@interaction_bp.route("/interactions")
@login_required
def interactions():
    conversations = get_user_conversations(current_user.id)
    all_emp = get_all_employees()
    employees = [e for e in all_emp if e.id != current_user.id and not e.is_admin()]
    return render_template("interactions.html", user=current_user, conversations=conversations, employees=employees)


@interaction_bp.route("/api/interactions/send", methods=["POST"])
@login_required
def send_message():
    data = request.json or {}
    receiver_id = data.get("receiver_id")
    message = (data.get("message") or "").strip()[:2000]
    if not receiver_id or not message:
        return jsonify({"error": "receiver_id and message are required"}), 400
    receiver = get_user_by_id(receiver_id)
    if not receiver or receiver.is_admin():
        return jsonify({"error": "Invalid receiver"}), 400
    msg = save_message(current_user.id, receiver_id, message)
    return jsonify({"message": "Sent", "msg": {
        "id": str(msg["_id"]),
        "sender_id": msg["sender_id"],
        "receiver_id": msg["receiver_id"],
        "message": msg["message"],
        "created_at": msg["created_at"].isoformat(),
    }})


@interaction_bp.route("/api/interactions/conversation/<user_id>", methods=["GET"])
@login_required
def get_convo(user_id):
    msgs = get_conversation(current_user.id, user_id)
    mark_messages_as_read(user_id, current_user.id)
    return jsonify({"messages": [{
        "id": str(m["_id"]),
        "sender_id": m["sender_id"],
        "receiver_id": m["receiver_id"],
        "message": m["message"],
        "created_at": m["created_at"].isoformat(),
        "is_sender": m["sender_id"] == current_user.id,
    } for m in msgs]})
