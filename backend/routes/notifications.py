"""In-app and system notification routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from auth_utils import role_required
from utils.validators import validate_required
from models import audit as audit_model

notifications_bp = Blueprint("notifications_bp", __name__)


@notifications_bp.get("/notifications")
@jwt_required()
def list_notifications():
    user_id = get_jwt_identity()
    return jsonify(audit_model.list_notifications(user_id))


@notifications_bp.post("/notifications")
@role_required("Admin", "Faculty")
def create_notification():
    data = request.get_json(force=True)
    is_valid, err = validate_required(data, ["userId", "title", "message"])
    if not is_valid:
        return jsonify({"error": f"Missing required fields: {err.replace('Missing fields: ', '')}"}), 400

    notification_id = audit_model.create_notification(
        user_id=data["userId"],
        template_id=data.get("templateId"),
        title=data["title"],
        message=data["message"],
        notif_type=data.get("notificationType", "SYSTEM"),
        channel=data.get("deliveryChannel", "IN_APP"),
        priority=data.get("priority", "NORMAL")
    )
    return jsonify({"notificationId": notification_id, "message": "Notification dispatched"}), 201


@notifications_bp.put("/notifications/<int:notification_id>/read")
@jwt_required()
def mark_notification_read(notification_id):
    user_id = get_jwt_identity()
    rowcount = audit_model.mark_notification_read(notification_id, user_id)
    if rowcount == 0:
        return jsonify({"error": "Notification not found or unauthorized"}), 404
    return jsonify({"message": "Marked as read"})


@notifications_bp.put("/notifications/read-all")
@jwt_required()
def mark_all_notifications_read():
    user_id = get_jwt_identity()
    audit_model.mark_all_notifications_read(user_id)
    return jsonify({"message": "All notifications marked as read"})
