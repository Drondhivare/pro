"""Common helpers for request context, IP extraction, and data formatting."""
from datetime import date, datetime
from decimal import Decimal
from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity


def get_client_ip() -> str:
    """Extract client remote IP address safely."""
    try:
        return request.remote_addr or "0.0.0.0"
    except Exception:
        return "0.0.0.0"


def get_user_agent() -> str:
    """Extract User-Agent header safely."""
    try:
        return request.headers.get("User-Agent", "")
    except Exception:
        return ""


def get_auth_user() -> tuple[int | None, str | None]:
    """Return (user_id, role) from current JWT token context."""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get("role")
        return user_id, role
    except Exception:
        return None, None


def serialize_db_row(row: dict | None) -> dict | None:
    """Convert Decimals, dates, datetimes to JSON serializable forms if needed."""
    if not row:
        return row
    result = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            result[k] = float(v)
        elif isinstance(v, (datetime, date)):
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result
