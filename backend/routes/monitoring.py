"""System configuration, feature flags, health monitoring, and metrics routes."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from auth_utils import role_required
from database import fetch_one, log_audit
from models import audit as audit_model

monitoring_bp = Blueprint("monitoring_bp", __name__)


@monitoring_bp.get("/system/config")
@role_required("Admin")
def list_system_config():
    return jsonify(audit_model.list_system_config())


@monitoring_bp.put("/system/config/<string:config_key>")
@role_required("Admin")
def update_system_config(config_key):
    data = request.get_json(force=True)
    user_id = get_jwt_identity()
    new_val = str(data.get("configurationValue", ""))

    old_row = audit_model.update_system_config(config_key, new_val, user_id)
    if not old_row:
        return jsonify({"error": "Config key not found"}), 404

    log_audit(user_id, "SystemConfiguration", None, "UPDATE", old_row["configurationValue"], new_val)
    return jsonify({"message": "Configuration updated"})


@monitoring_bp.get("/system/feature-flags")
@jwt_required()
def list_feature_flags():
    return jsonify(audit_model.list_feature_flags())


@monitoring_bp.put("/system/feature-flags/<int:flag_id>")
@role_required("Admin")
def update_feature_flag(flag_id):
    data = request.get_json(force=True)
    user_id = get_jwt_identity()

    old_flag = fetch_one("SELECT * FROM FeatureFlag WHERE flagId = %s", (flag_id,))
    if not old_flag:
        return jsonify({"error": "Feature flag not found"}), 404

    is_enabled = bool(data.get("isEnabled", old_flag["isEnabled"]))
    desc = data.get("description", old_flag["description"])

    audit_model.update_feature_flag(flag_id, is_enabled, desc)
    log_audit(user_id, "FeatureFlag", flag_id, "UPDATE", str(old_flag["isEnabled"]), str(is_enabled))
    return jsonify({"message": "Feature flag updated"})


@monitoring_bp.get("/system/metrics")
@role_required("Admin")
def list_metrics():
    return jsonify(audit_model.list_metrics())


@monitoring_bp.get("/system/info")
@role_required("Admin")
def get_system_info():
    """System health check and platform overview."""
    total_users = fetch_one("SELECT COUNT(*) AS c FROM User WHERE isActive = TRUE")["c"]
    total_exams = fetch_one("SELECT COUNT(*) AS c FROM Exam WHERE isActive = TRUE")["c"]
    total_questions = fetch_one("SELECT COUNT(*) AS c FROM Question WHERE isActive = TRUE")["c"]
    total_results = fetch_one("SELECT COUNT(*) AS c FROM Result")["c"]
    active_sessions = fetch_one("SELECT COUNT(*) AS c FROM UserSession WHERE sessionStatus = 'ACTIVE' AND expiresAt > NOW()")["c"]

    return jsonify({
        "status": "HEALTHY",
        "database": "CONNECTED",
        "timestamp": datetime.utcnow().isoformat(),
        "totalUsers": total_users,
        "totalExams": total_exams,
        "totalQuestions": total_questions,
        "totalResults": total_results,
        "activeSessions": active_sessions,
        "version": "1.0.0",
    })


@monitoring_bp.get("/system/events")
@role_required("Admin")
def list_system_events():
    """Recent security and audit events for the admin events stream."""
    return jsonify(audit_model.list_system_events())
