"""Business logic for exams, schedules, and attempts eligibility."""
from database import log_audit
from models import exam as exam_model
from models import attempt as attempt_model


def start_exam_attempt(exam_id: int, user_id: int | str, ip_address: str):
    """
    Validates candidate registration and attempt limits, creates or resumes attempt.
    Returns (response_data, error_message, status_code).
    """
    registration = attempt_model.get_candidate_registration(exam_id, user_id)
    if not registration:
        return None, "You are not registered for this exam", 403

    exam = attempt_model.get_exam_for_attempt(exam_id)
    exam_status = (exam.get("examStatus") or exam.get("status")) if exam else None
    if not exam or not exam["isActive"] or exam_status not in ("PUBLISHED", "ONGOING", "SCHEDULED", "ACTIVE"):
        return None, "Exam is not currently open for attempts", 400

    registration_id = registration["registrationId"]

    active_attempt = attempt_model.get_active_attempt(registration_id)
    if active_attempt:
        return {
            "attemptId": active_attempt["attemptId"],
            "attemptNumber": active_attempt["attemptNumber"],
            "resumed": True,
            "message": "Resumed active attempt",
        }, None, 200

    previous_attempts = attempt_model.get_previous_attempts(registration_id)
    if len(previous_attempts) >= exam["maximumAttempts"]:
        return None, "Maximum attempts reached for this exam", 403

    attempt_number = len(previous_attempts) + 1
    attempt_id = attempt_model.create_attempt(registration_id, attempt_number, ip_address)

    log_audit(user_id, "ExamAttempt", attempt_id, "START", None, f"Attempt #{attempt_number} for {exam['examTitle']}")
    return {"attemptId": attempt_id, "attemptNumber": attempt_number}, None, 201
