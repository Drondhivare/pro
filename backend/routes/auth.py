"""Authentication API routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.validators import validate_required
from utils.helpers import get_client_ip, get_user_agent
from services import auth_service
from models import user as user_model

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.post("/auth/register")
def register():
    data = request.get_json(force=True)
    is_valid, err = validate_required(data, ["firstName", "lastName", "email", "password"])
    if not is_valid:
        return jsonify({"error": err}), 400

    resp, err_msg, status_code = auth_service.register_user(
        data, get_client_ip(), get_user_agent()
    )
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(resp), status_code


@auth_bp.post("/auth/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email") if data else None
    password = data.get("password") if data else None
    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    resp, err_msg, status_code = auth_service.authenticate_user(
        email, password, get_client_ip(), get_user_agent()
    )
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(resp), status_code


@auth_bp.get("/auth/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = user_model.get_user_profile(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@auth_bp.post("/auth/logout")
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    user_model.logout_user_sessions(user_id)
    return jsonify({"message": "Logged out"})


@auth_bp.post("/auth/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400
    res = auth_service.request_password_reset(email, get_client_ip(), get_user_agent())
    return jsonify(res)


@auth_bp.post("/auth/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    new_password = data.get("newPassword") or data.get("password")
    if not email or not new_password:
        return jsonify({"error": "Email and new password are required"}), 400

    res, err_msg, status_code = auth_service.perform_password_reset(
        email, new_password, get_client_ip(), get_user_agent()
    )
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(res), status_code
