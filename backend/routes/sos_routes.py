from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from flask_login import login_required, current_user
from ..database.database import (
    create_sos_request, get_user_sos_requests,
    get_all_sos_requests, resolve_sos_request,
)
from ..utils.security_utils import admin_required

sos_bp = Blueprint("sos", __name__)


@sos_bp.route("/sos")
@login_required
def sos_page():
    return render_template("sos.html", 
                         user=current_user, 
                         sos_requests=get_user_sos_requests(current_user.id),
                         now=datetime.now())


@sos_bp.route("/api/sos/create", methods=["POST"])
@login_required
def create_sos():
    data = request.json or {}
    problem_type = data.get("problem_type")
    if not problem_type:
        return jsonify({"error": "problem_type is required"}), 400
    
    description = data.get("description", "")[:2000]
    severity = data.get("severity", "standard")
    category = data.get("category", "other")
    
    sos = create_sos_request(
        current_user.id, 
        problem_type, 
        description, 
        severity=severity, 
        category=category
    )
    
    return jsonify({
        "message": "SOS request created",
        "sos": {
            "id": str(sos["_id"]),
            "problem_type": sos.get("problem_type"),
            "description": sos.get("description"),
            "status": sos.get("status"),
            "severity": sos.get("severity"),
            "category": sos.get("category"),
            "created_at": str(sos.get("created_at")),
        }
    }), 201


@sos_bp.route("/api/sos/resolve/<sos_id>", methods=["POST"])
@login_required
@admin_required
def resolve_sos(sos_id):
    if resolve_sos_request(sos_id, current_user.id):
        return jsonify({"message": "SOS request resolved"})
    return jsonify({"error": "Failed to resolve SOS request"}), 400
