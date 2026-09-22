"""Validation utilities for request payloads."""

def validate_required(data: dict | None, required_fields: list[str]) -> tuple[bool, str | None]:
    """
    Checks if all required fields are present in data and not empty strings/None.
    Returns (True, None) if valid, or (False, error_message) if any missing.
    Matches exact message format from endpoint.py:
    'Missing fields: field1, field2'
    """
    if not data or not isinstance(data, dict):
        return False, f"Missing fields: {', '.join(required_fields)}"
    missing = [f for f in required_fields if data.get(f) is None or str(data.get(f)).strip() == ""]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    return True, None
