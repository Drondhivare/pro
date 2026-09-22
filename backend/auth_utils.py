"""Password hashing and role-based access helpers used by endpoint.py."""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain_password: str) -> str:
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not plain_password or not password_hash:
        return False
    try:
        return check_password_hash(password_hash, plain_password)
    except (ValueError, TypeError):
        return False


def role_required(*allowed_roles):
    """
    Decorator for routes: requires a valid JWT AND that the token's
    'role' claim is one of allowed_roles, e.g. @role_required('Admin', 'Faculty')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
