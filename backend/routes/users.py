"""User, role, permission, session, and dashboard routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from auth_utils import role_required, hash_password
from database import fetch_all, fetch_one, execute, log_audit
from utils.validators import validate_required
from utils.helpers import get_client_ip, get_user_agent
from models import user as user_model
from services.evaluation_service import calculate_grade_and_pass

users_bp = Blueprint("users_bp", __name__)


# ---------- Users (Admin) ----------

@users_bp.get("/users")
@role_required("Admin")
def list_users():
    return jsonify(user_model.list_users())


@users_bp.post("/users")
@role_required("Admin")
def admin_create_user():
    data = request.get_json(force=True)
    is_valid, err = validate_required(data, ["firstName", "lastName", "email", "password", "roleId"])
    if not is_valid:
        return jsonify({"error": err}), 400

    if user_model.get_user_by_email(data["email"]):
        return jsonify({"error": "Email already registered"}), 409

    password_hash = hash_password(data["password"])
    user_id = user_model.create_user(
        first_name=data["firstName"],
        last_name=data["lastName"],
        email=data["email"],
        phone=data.get("phone"),
        password_hash=password_hash,
        role_id=data["roleId"],
        is_active=data.get("isActive", True)
    )
    admin_id = get_jwt_identity()
    log_audit(admin_id, "User", user_id, "CREATE", None, {"email": data["email"], "roleId": data["roleId"]}, get_client_ip(), get_user_agent())
    return jsonify({"userId": user_id, "message": "User created successfully"}), 201


@users_bp.get("/users/<int:user_id>")
@jwt_required()
def get_user(user_id):
    user = user_model.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@users_bp.put("/users/<int:user_id>")
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    if str(current_user_id) != str(user_id) and claims.get("role") != "Admin":
        return jsonify({"error": "Forbidden: unauthorized to update this user"}), 403

    data = request.get_json(force=True)
    allowed_fields = ["firstName", "lastName", "phone"]
    if claims.get("role") == "Admin":
        allowed_fields.extend(["isActive", "accountLocked"])

    fields_to_update = {col: data[col] for col in allowed_fields if col in data}
    if not fields_to_update:
        return jsonify({"error": "No valid fields to update"}), 400

    rowcount = user_model.update_user_fields(user_id, fields_to_update)
    if rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    log_audit(current_user_id, "User", user_id, "UPDATE", None, data, get_client_ip(), get_user_agent())
    return jsonify({"message": "User updated"})


@users_bp.delete("/users/<int:user_id>")
@role_required("Admin")
def delete_user(user_id):
    admin_id = get_jwt_identity()
    rowcount = user_model.deactivate_user(user_id)
    if rowcount == 0:
        return jsonify({"error": "User not found"}), 404
    log_audit(admin_id, "User", user_id, "DELETE", None, {"isActive": False}, get_client_ip(), get_user_agent())
    return jsonify({"message": "User deactivated"})


@users_bp.get("/users/<int:user_id>/login-history")
@jwt_required()
def user_login_history(user_id):
    return jsonify(user_model.get_user_login_history(user_id))


# ---------- Roles & Permissions ----------

@users_bp.get("/roles")
@jwt_required()
def list_roles():
    return jsonify(user_model.list_roles())


@users_bp.get("/permissions")
@role_required("Admin")
def list_permissions():
    return jsonify(user_model.list_permissions())


@users_bp.get("/roles/<int:role_id>/permissions")
@role_required("Admin")
def role_permissions(role_id):
    return jsonify(user_model.get_role_permissions(role_id))


@users_bp.post("/roles/<int:role_id>/permissions")
@role_required("Admin")
def update_role_permissions(role_id):
    data = request.get_json(force=True)
    permission_ids = data.get("permissionIds", [])
    admin_id = get_jwt_identity()
    user_model.update_role_permissions(role_id, permission_ids)
    log_audit(admin_id, "RolePermission", role_id, "UPDATE", None, {"permissionIds": permission_ids}, get_client_ip(), get_user_agent())
    return jsonify({"message": "Role permissions updated successfully"})


# ---------- Active Sessions (Admin) ----------

@users_bp.get("/sessions")
@role_required("Admin")
def list_sessions():
    return jsonify(user_model.list_sessions())


@users_bp.delete("/sessions/<string:session_id>")
@role_required("Admin")
def delete_session(session_id):
    admin_id = get_jwt_identity()
    rowcount = user_model.revoke_session(session_id)
    if rowcount == 0:
        return jsonify({"error": "Session not found"}), 404
    log_audit(admin_id, "UserSession", 0, "DELETE", {"sessionId": session_id}, {"sessionStatus": "INVALIDATED"}, get_client_ip(), get_user_agent())
    return jsonify({"message": "Session revoked successfully"})


@users_bp.post("/sessions/<string:session_id>/invalidate")
@role_required("Admin")
def invalidate_session_post(session_id):
    return delete_session(session_id)


# ---------- Dashboards ----------

@users_bp.get("/student/dashboard")
@role_required("Student")
def get_student_dashboard():
    user_id = get_jwt_identity()

    registered_exams = fetch_all(
        """SELECT e.examId, e.examTitle, e.examCode, e.durationMinutes, e.totalMarks, e.examStatus AS status,
                  s.subjectName, s.subjectCode, es.startTime, es.endTime,
                  cr.registrationTime AS registeredAt,
                  (SELECT COUNT(*) FROM ExamAttempt ea WHERE ea.registrationId = cr.registrationId) AS attemptCount,
                  (SELECT ea.status FROM ExamAttempt ea WHERE ea.registrationId = cr.registrationId ORDER BY ea.attemptId DESC LIMIT 1) AS lastAttemptStatus
           FROM CandidateRegistration cr
           JOIN Exam e ON e.examId = cr.examId
           JOIN Subject s ON s.subjectId = e.subjectId
           LEFT JOIN ExamSchedule es ON es.examId = e.examId
           WHERE cr.userId = %s AND e.isActive = TRUE
           ORDER BY cr.registrationTime DESC""",
        (user_id,)
    )

    recent_results = fetch_all(
        """SELECT r.resultId, r.percentage, r.grade, r.passStatus, r.publishedAt,
                  e.examTitle, e.examCode, s.subjectName, ev.totalMarksObtained, e.totalMarks
           FROM Result r
           JOIN Evaluation ev ON ev.evaluationId = r.evaluationId
           JOIN ExamAttempt att ON att.attemptId = ev.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
           JOIN Exam e ON e.examId = cr.examId
           JOIN Subject s ON s.subjectId = e.subjectId
           WHERE cr.userId = %s AND r.isPublished = TRUE
           ORDER BY r.publishedAt DESC LIMIT 5""",
        (user_id,)
    )
    for r in recent_results:
        calc_pct, calc_grade, calc_pass = calculate_grade_and_pass(
            r.get("totalMarksObtained"), r.get("totalMarks"), None
        )
        r["percentage"] = calc_pct
        if not r.get("grade") or r.get("grade") != calc_grade:
            r["grade"] = calc_grade

    unread_notifications = fetch_one(
        "SELECT COUNT(*) AS c FROM Notification WHERE userId = %s AND isRead = FALSE",
        (user_id,)
    )["c"]

    total_registered = len(registered_exams)
    completed_exams = sum(1 for e in registered_exams if e.get("lastAttemptStatus") in ("SUBMITTED", "AUTO_SUBMITTED", "EVALUATED"))

    return jsonify({
        "totalRegistered": total_registered,
        "completedExams": completed_exams,
        "pendingExams": max(0, total_registered - completed_exams),
        "unreadNotifications": unread_notifications,
        "registeredExams": registered_exams,
        "recentResults": recent_results,
    })


@users_bp.get("/faculty/dashboard")
@role_required("Admin", "Faculty")
def get_faculty_dashboard():
    total_subjects = fetch_one("SELECT COUNT(*) AS c FROM Subject WHERE isActive = TRUE")["c"]
    total_exams = fetch_one("SELECT COUNT(*) AS c FROM Exam WHERE isActive = TRUE")["c"]
    total_questions = fetch_one("SELECT COUNT(*) AS c FROM Question WHERE isActive = TRUE")["c"]
    pending_evaluations = fetch_one(
        "SELECT COUNT(*) AS c FROM ExamAttempt WHERE status IN ('SUBMITTED', 'AUTO_SUBMITTED')"
    )["c"]

    recent_exams = fetch_all(
        """SELECT e.*, s.subjectName, s.subjectCode,
                  (SELECT COUNT(*) FROM CandidateRegistration cr WHERE cr.examId = e.examId) AS registeredCount
           FROM Exam e
           JOIN Subject s ON s.subjectId = e.subjectId
           WHERE e.isActive = TRUE
           ORDER BY e.createdAt DESC LIMIT 5"""
    )

    recent_submissions = fetch_all(
        """SELECT ea.attemptId, ea.attemptNumber, ea.status, ea.submittedAt,
                  u.firstName, u.lastName, u.email, e.examTitle, e.examCode
           FROM ExamAttempt ea
           JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
           JOIN User u ON u.userId = cr.userId
           JOIN Exam e ON e.examId = cr.examId
           WHERE ea.status IN ('SUBMITTED', 'AUTO_SUBMITTED')
           ORDER BY ea.submittedAt DESC LIMIT 5"""
    )

    return jsonify({
        "totalSubjects": total_subjects,
        "totalExams": total_exams,
        "totalQuestions": total_questions,
        "pendingEvaluations": pending_evaluations,
        "recentExams": recent_exams,
        "recentSubmissions": recent_submissions,
    })


@users_bp.get("/admin/dashboard")
@role_required("Admin")
def get_admin_dashboard():
    user_stats = fetch_all(
        """SELECT r.roleName, COUNT(u.userId) AS count
           FROM Role r
           LEFT JOIN User u ON u.roleId = r.roleId AND u.isActive = TRUE
           GROUP BY r.roleName"""
    )

    total_users = fetch_one("SELECT COUNT(*) AS c FROM User WHERE isActive = TRUE")["c"]
    total_exams = fetch_one("SELECT COUNT(*) AS c FROM Exam WHERE isActive = TRUE")["c"]
    active_exams = fetch_one("SELECT COUNT(*) AS c FROM Exam WHERE isActive = TRUE AND examStatus IN ('ACTIVE', 'SCHEDULED')")["c"]
    total_subjects = fetch_one("SELECT COUNT(*) AS c FROM Subject WHERE isActive = TRUE")["c"]
    total_questions = fetch_one("SELECT COUNT(*) AS c FROM Question WHERE isActive = TRUE")["c"]
    active_sessions = fetch_one("SELECT COUNT(*) AS c FROM UserSession WHERE sessionStatus = 'ACTIVE' AND expiresAt > NOW()")["c"]

    recent_logs = fetch_all(
        """SELECT al.auditLogId AS logId, al.action, al.entityName, al.entityId, al.timestamp, al.ipAddress,
                  u.email, u.firstName, u.lastName
           FROM AuditLog al
           LEFT JOIN User u ON u.userId = al.userId
           ORDER BY al.timestamp DESC LIMIT 10"""
    )

    return jsonify({
        "totalUsers": total_users,
        "userStats": user_stats,
        "totalExams": total_exams,
        "activeExams": active_exams,
        "totalSubjects": total_subjects,
        "totalQuestions": total_questions,
        "activeSessions": active_sessions,
        "recentAuditLogs": recent_logs,
    })
