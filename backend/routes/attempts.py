"""Exam runtime attempt, answer autosave, security monitoring, and submission routes."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from auth_utils import role_required
from database import transaction, log_audit
from utils.helpers import get_client_ip, get_user_agent
from models import attempt as attempt_model
from services import exam_service
from services.evaluation_service import auto_grade_internal

attempts_bp = Blueprint("attempts_bp", __name__)


@attempts_bp.post("/exams/<int:exam_id>/attempts/start")
@role_required("Student")
def start_attempt(exam_id):
    user_id = get_jwt_identity()
    resp, err_msg, status_code = exam_service.start_exam_attempt(
        exam_id, user_id, get_client_ip()
    )
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(resp), status_code


@attempts_bp.get("/attempts/<int:attempt_id>")
@jwt_required()
def get_attempt(attempt_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")

    attempt = attempt_model.get_attempt_detail(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found"}), 404

    if role == "Student" and str(attempt["userId"]) != str(user_id):
        return jsonify({"error": "Unauthorized access to attempt"}), 403

    return jsonify(attempt)


@attempts_bp.post("/attempts/<int:attempt_id>/answers")
@role_required("Student")
def submit_answer(attempt_id):
    user_id = get_jwt_identity()
    attempt = attempt_model.get_attempt_owner(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found"}), 404
    if str(attempt["userId"]) != str(user_id):
        return jsonify({"error": "Unauthorized"}), 403
    if attempt["status"] != "IN_PROGRESS":
        return jsonify({"error": "Cannot modify answers for a submitted attempt"}), 400

    data = request.get_json(force=True)
    if not data.get("questionId"):
        return jsonify({"error": "questionId is required"}), 400

    answer_id, created = attempt_model.save_or_update_answer(attempt_id, data)
    msg = "Answer recorded" if created else "Answer updated"
    status_code = 201 if created else 200
    return jsonify({"answerId": answer_id, "message": msg}), status_code


@attempts_bp.get("/attempts/<int:attempt_id>/answers")
@jwt_required()
def list_answers(attempt_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")

    attempt = attempt_model.get_attempt_owner(attempt_id)
    if not attempt:
        return jsonify({"error": "Attempt not found"}), 404
    if role == "Student" and str(attempt["userId"]) != str(user_id):
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify(attempt_model.list_attempt_answers(attempt_id))


@attempts_bp.post("/attempts/<int:attempt_id>/security-event")
@role_required("Student")
def record_security_event(attempt_id):
    """
    Backend-authoritative exam security event monitor.
    Enforces a strict 3-warning limit on tab switching / window blurring.
    Automatically locks and submits the attempt on the 3rd violation.
    Uses row-level locking (FOR UPDATE) within an atomic transaction
    to eliminate race conditions and double-increments under concurrent requests.
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    event_type = data.get("eventType", "TAB_SWITCH")
    details = data.get("details", "Tab switch or window blur detected")
    ip_address = get_client_ip()

    trigger_auto_grade = False
    response_payload = None

    with transaction() as cur:
        cur.execute(
            """SELECT ea.*, cr.userId, cr.examId, e.examTitle, e.examCode 
               FROM ExamAttempt ea
               JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
               JOIN Exam e ON e.examId = cr.examId
               WHERE ea.attemptId = %s FOR UPDATE""",
            (attempt_id,)
        )
        attempt = cur.fetchone()
        if not attempt:
            return jsonify({"error": "Attempt not found"}), 404
        if str(attempt["userId"]) != str(user_id):
            return jsonify({"error": "Unauthorized"}), 403

        current_violations = int(attempt.get("violationCount") or 0)
        current_status = attempt["status"]

        # If attempt is already submitted/closed, return authoritative locked state
        if current_status != "IN_PROGRESS":
            return jsonify({
                "violationCount": current_violations,
                "maxViolations": 3,
                "autoSubmitTriggered": True,
                "attemptStatus": current_status,
                "submissionReason": attempt.get("submissionReason"),
                "message": "Attempt already submitted or closed."
            }), 200

        # Debounce / duplicate protection within the transaction
        cur.execute(
            """SELECT createdAt FROM ExamSecurityEvent 
               WHERE attemptId = %s 
               ORDER BY createdAt DESC LIMIT 1""",
            (attempt_id,)
        )
        recent_event = cur.fetchone()
        if recent_event and recent_event.get("createdAt"):
            delta = datetime.now() - recent_event["createdAt"]
            if delta.total_seconds() < 1.5:
                return jsonify({
                    "violationCount": current_violations,
                    "maxViolations": 3,
                    "autoSubmitTriggered": (current_violations >= 3),
                    "isDuplicate": True,
                    "message": f"Warnings: {current_violations}/3"
                }), 200

        # Increment authoritative violation count atomically under row lock
        new_count = current_violations + 1
        cur.execute(
            "UPDATE ExamAttempt SET violationCount = %s WHERE attemptId = %s",
            (new_count, attempt_id)
        )

        # Record immutable security event
        cur.execute(
            """INSERT INTO ExamSecurityEvent (attemptId, userId, eventType, warningNumber, details, ipAddress)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (attempt_id, user_id, event_type, new_count, details[:255], ip_address),
        )

        if new_count >= 3:
            # THIRD VIOLATION: Lock and auto-submit attempt immediately
            cur.execute(
                """UPDATE ExamAttempt
                   SET status = 'AUTO_SUBMITTED', endTime = NOW(), submittedAt = NOW(),
                       submissionMethod = 'SYSTEM', autoSubmitted = TRUE,
                       submissionReason = 'AUTO_SUBMITTED_TAB_SWITCH_LIMIT'
                   WHERE attemptId = %s""",
                (attempt_id,)
            )
            trigger_auto_grade = True
            response_payload = {
                "violationCount": new_count,
                "maxViolations": 3,
                "autoSubmitTriggered": True,
                "submissionReason": "AUTO_SUBMITTED_TAB_SWITCH_LIMIT",
                "message": "Maximum security violations reached. Your exam is being submitted automatically."
            }
        elif new_count == 2:
            response_payload = {
                "violationCount": new_count,
                "maxViolations": 3,
                "autoSubmitTriggered": False,
                "message": "Warning 2/3: This is your final warning. One more violation will automatically submit your exam."
            }
        else:
            response_payload = {
                "violationCount": new_count,
                "maxViolations": 3,
                "autoSubmitTriggered": False,
                "message": "Warning 1/3: Leaving the exam window is not allowed. Further violations may automatically submit your exam."
            }

    log_audit(
        user_id, "ExamSecurityEvent", attempt_id, "SECURITY_VIOLATION",
        f"Warning {current_violations}/3", f"Warning {new_count}/3: {event_type}",
        ip_address, get_user_agent()
    )

    if trigger_auto_grade:
        log_audit(user_id, "ExamAttempt", attempt_id, "AUTO_SUBMIT", "IN_PROGRESS", "AUTO_SUBMITTED_TAB_SWITCH_LIMIT")
        try:
            auto_grade_internal(attempt_id)
        except Exception as e:
            print(f"[Auto-Evaluate Error on Security Submit]: {e}")

    return jsonify(response_payload), 200


@attempts_bp.post("/attempts/<int:attempt_id>/submit")
@role_required("Student")
def submit_attempt(attempt_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    auto = bool(data.get("autoSubmitted", False))
    reason = data.get("submissionReason") or ("AUTO_TIMEOUT" if auto else "MANUAL_SUBMISSION")
    status = "AUTO_SUBMITTED" if auto else "SUBMITTED"

    if reason == "AUTO_SUBMITTED_TAB_SWITCH_LIMIT":
        method = "SYSTEM"
    else:
        method = "AUTO_TIMEOUT" if auto else "MANUAL"

    trigger_auto_grade = False

    with transaction() as cur:
        cur.execute(
            """SELECT ea.*, cr.userId, cr.examId, e.examTitle FROM ExamAttempt ea
               JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
               JOIN Exam e ON e.examId = cr.examId
               WHERE ea.attemptId = %s FOR UPDATE""",
            (attempt_id,)
        )
        attempt = cur.fetchone()
        if not attempt:
            return jsonify({"error": "Attempt not found"}), 404
        if str(attempt["userId"]) != str(user_id):
            return jsonify({"error": "Unauthorized"}), 403
        if attempt["status"] != "IN_PROGRESS":
            if attempt.get("submissionReason") == "AUTO_SUBMITTED_TAB_SWITCH_LIMIT" or attempt["status"] in ("AUTO_SUBMITTED", "SUBMITTED"):
                return jsonify({
                    "message": "Attempt already submitted",
                    "attemptId": attempt_id,
                    "status": attempt["status"],
                    "submissionReason": attempt.get("submissionReason"),
                    "alreadySubmitted": True
                }), 200
            return jsonify({"error": "Attempt already submitted"}), 400

        cur.execute(
            """UPDATE ExamAttempt
               SET status = %s, endTime = NOW(), submittedAt = NOW(),
                   submissionMethod = %s, autoSubmitted = %s, submissionReason = %s
               WHERE attemptId = %s""",
            (status, method, auto, reason, attempt_id),
        )
        trigger_auto_grade = True

    log_audit(user_id, "ExamAttempt", attempt_id, "SUBMIT", "IN_PROGRESS", f"{status}:{reason}")

    if trigger_auto_grade:
        try:
            auto_grade_internal(attempt_id)
        except Exception as e:
            print(f"[Auto-Evaluate Error]: {e}")

    return jsonify({
        "message": "Exam submitted successfully",
        "attemptId": attempt_id,
        "status": status,
        "submissionReason": reason
    })
