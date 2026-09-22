"""Subject management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from auth_utils import role_required
from database import fetch_all, fetch_one, execute, log_audit
from utils.validators import validate_required
from utils.helpers import get_client_ip, get_user_agent

subjects_bp = Blueprint("subjects_bp", __name__)


@subjects_bp.get("/subjects")
@jwt_required()
def list_subjects():
    return jsonify(fetch_all("SELECT * FROM Subject WHERE isActive = TRUE ORDER BY subjectId"))


@subjects_bp.post("/subjects")
@role_required("Admin", "Faculty")
def create_subject():
    data = request.get_json(force=True)
    is_valid, err = validate_required(data, ["subjectCode", "subjectName"])
    if not is_valid:
        return jsonify({"error": f"Missing required fields: {err.replace('Missing fields: ', '')}"}), 400

    user_id = get_jwt_identity()
    subject_id, _ = execute(
        """INSERT INTO Subject (subjectCode, subjectName, description, credits, createdBy)
           VALUES (%s, %s, %s, %s, %s)""",
        (data["subjectCode"], data["subjectName"], data.get("description"),
         data.get("credits", 4), user_id),
    )
    log_audit(user_id, "Subject", subject_id, "CREATE", None, data, get_client_ip(), get_user_agent())
    return jsonify({"subjectId": subject_id, "message": "Subject created successfully"}), 201


@subjects_bp.get("/subjects/<int:subject_id>")
@jwt_required()
def get_subject(subject_id):
    subject = fetch_one("SELECT * FROM Subject WHERE subjectId = %s", (subject_id,))
    if not subject:
        return jsonify({"error": "Subject not found"}), 404
    return jsonify(subject)


@subjects_bp.put("/subjects/<int:subject_id>")
@role_required("Admin", "Faculty")
def update_subject(subject_id):
    data = request.get_json(force=True)
    user_id = get_jwt_identity()
    fields, params = [], []
    for col in ["subjectCode", "subjectName", "description", "credits", "isActive"]:
        if col in data:
            fields.append(f"{col} = %s")
            params.append(data[col])
    if not fields:
        return jsonify({"error": "No fields to update"}), 400
    fields.append("updatedBy = %s")
    params.append(user_id)
    params.append(subject_id)
    _, rowcount = execute(f"UPDATE Subject SET {', '.join(fields)} WHERE subjectId = %s", params)
    if rowcount == 0:
        return jsonify({"error": "Subject not found"}), 404
    log_audit(user_id, "Subject", subject_id, "UPDATE", None, data, get_client_ip(), get_user_agent())
    return jsonify({"message": "Subject updated"})


@subjects_bp.delete("/subjects/<int:subject_id>")
@role_required("Admin")
def delete_subject(subject_id):
    user_id = get_jwt_identity()
    _, rowcount = execute("UPDATE Subject SET isActive = FALSE WHERE subjectId = %s", (subject_id,))
    if rowcount == 0:
        return jsonify({"error": "Subject not found"}), 404
    log_audit(user_id, "Subject", subject_id, "DELETE", None, {"isActive": False}, get_client_ip(), get_user_agent())
    return jsonify({"message": "Subject deactivated"})
