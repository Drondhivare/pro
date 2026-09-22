"""Security and administrative audit trail routes."""
from flask import Blueprint, request, jsonify
from auth_utils import role_required
from models import audit as audit_model

audit_bp = Blueprint("audit_bp", __name__)


@audit_bp.get("/audit-logs")
@role_required("Admin")
def list_audit_logs():
    user_filter = request.args.get("userId")
    entity_filter = request.args.get("entityName")
    action_filter = request.args.get("action")
    limit = min(int(request.args.get("limit", 200)), 1000)

    rows = audit_model.list_audit_logs(user_filter, entity_filter, action_filter, limit)
    return jsonify(rows)
