"""Authentication and user session service."""
import uuid
from flask_jwt_extended import create_access_token
from auth_utils import hash_password, verify_password
from database import log_audit
from models import user as user_model


def authenticate_user(email: str, password: str, ip_address: str, user_agent: str) -> tuple[dict | None, str | None, int]:
    """
    Validates user credentials, updates login history, creates session and JWT token.
    Returns (response_data, error_message, status_code).
    """
    user = user_model.get_user_by_email(email)

    if not user or not verify_password(password, user["passwordHash"]):
        if user:
            new_failed = (user.get("failedLoginAttempts") or 0) + 1
            account_locked = new_failed >= 5
            user_model.record_login_failure(user["userId"], new_failed, account_locked, ip_address, user_agent)
        return None, "Invalid email or password", 401

    if not user["isActive"] or user["accountLocked"]:
        return None, "Account is inactive or locked", 403

    access_token = create_access_token(
        identity=str(user["userId"]),
        additional_claims={"role": user["roleName"], "email": user["email"]},
    )

    session_id = str(uuid.uuid4())
    user_model.record_login_success(user["userId"], session_id, ip_address, user_agent)

    data = {
        "accessToken": access_token,
        "sessionId": session_id,
        "user": {
            "userId": user["userId"],
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "phone": user.get("phone"),
            "role": user["roleName"],
        },
    }
    return data, None, 200


def register_user(data: dict, ip_address: str, user_agent: str) -> tuple[dict | None, str | None, int]:
    """
    Registers a new user (defaults to roleId=3: Student).
    Returns (response_data, error_message, status_code).
    """
    role_id = data.get("roleId", 3)

    if user_model.get_user_by_email(data["email"]):
        return None, "Email already registered", 409

    password_hash = hash_password(data["password"])
    user_id = user_model.create_user(
        first_name=data["firstName"],
        last_name=data["lastName"],
        email=data["email"],
        phone=data.get("phone"),
        password_hash=password_hash,
        role_id=role_id,
        is_active=True
    )

    log_audit(
        user_id, "User", user_id, "CREATE", None,
        {"email": data["email"], "roleId": role_id},
        ip_address, user_agent
    )
    return {"userId": user_id, "message": "Registered successfully"}, None, 201


def request_password_reset(email: str, ip_address: str, user_agent: str) -> dict:
    """Simulates password reset email dispatch and logs audit event."""
    user = user_model.get_user_by_email(email)
    if user:
        log_audit(
            user["userId"], "User", user["userId"], "UPDATE", None,
            {"action": "PASSWORD_RESET_REQUEST"}, ip_address, user_agent
        )
    return {"message": "If this email is registered, instructions to reset your password have been sent."}


def perform_password_reset(email: str, new_password: str, ip_address: str, user_agent: str) -> tuple[dict | None, str | None, int]:
    """Resets user password with new plaintext password."""
    if len(new_password) < 6:
        return None, "Password must be at least 6 characters", 400

    user = user_model.get_user_by_email(email)
    if not user:
        return None, "User with this email not found", 404

    pw_hash = hash_password(new_password)
    user_model.reset_password(user["userId"], pw_hash)
    log_audit(
        user["userId"], "User", user["userId"], "UPDATE", None,
        {"action": "PASSWORD_RESET_SUCCESS"}, ip_address, user_agent
    )
    return {"message": "Password reset successful. Please sign in with your new password."}, None, 200
