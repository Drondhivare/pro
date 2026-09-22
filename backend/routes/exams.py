"""Exam, schedule, question-blueprint, and registration routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from auth_utils import role_required
from database import log_audit
from utils.validators import validate_required
from utils.helpers import get_client_ip, get_user_agent
from models import exam as exam_model

exams_bp = Blueprint("exams_bp", __name__)


# ---------- Exams ----------

@exams_bp.get("/exams")
@jwt_required()
def list_exams():
    return jsonify(exam_model.list_exams())


@exams_bp.get("/students/available-exams")
@jwt_required()
def student_available_exams():
    user_id = get_jwt_identity()
    return jsonify(exam_model.list_student_available_exams(user_id))


@exams_bp.post("/exams")
@role_required("Admin", "Faculty")
def create_exam():
    data = request.get_json(force=True)
    required = ["subjectId", "examCode", "examTitle", "totalMarks", "passingMarks", "durationMinutes"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    user_id = get_jwt_identity()
    exam_id = exam_model.create_exam(data, user_id)
    log_audit(user_id, "Exam", exam_id, "CREATE", None, data, get_client_ip(), get_user_agent())
    return jsonify({"examId": exam_id, "message": "Exam created successfully"}), 201


@exams_bp.get("/exams/<int:exam_id>")
@jwt_required()
def get_exam(exam_id):
    exam = exam_model.get_exam_by_id(exam_id)
    if not exam:
        return jsonify({"error": "Exam not found"}), 404
    return jsonify(exam)


@exams_bp.put("/exams/<int:exam_id>")
@role_required("Admin", "Faculty")
def update_exam(exam_id):
    data = request.get_json(force=True)
    user_id = get_jwt_identity()
    rowcount = exam_model.update_exam(exam_id, data, user_id)
    if rowcount == 0:
        return jsonify({"error": "Exam not found"}), 404
    log_audit(user_id, "Exam", exam_id, "UPDATE", None, data, get_client_ip(), get_user_agent())
    return jsonify({"message": "Exam updated"})


@exams_bp.delete("/exams/<int:exam_id>")
@role_required("Admin", "Faculty")
def delete_exam(exam_id):
    user_id = get_jwt_identity()
    rowcount = exam_model.delete_exam(exam_id)
    if rowcount == 0:
        return jsonify({"error": "Exam not found"}), 404
    log_audit(user_id, "Exam", exam_id, "DELETE", None, {"examStatus": "CANCELLED"}, get_client_ip(), get_user_agent())
    return jsonify({"message": "Exam cancelled"})


# ---------- Exam Schedule ----------

@exams_bp.post("/exams/<int:exam_id>/schedule")
@role_required("Admin", "Faculty")
def create_schedule(exam_id):
    data = request.get_json(force=True)
    is_valid, err = validate_required(data, ["startTime", "endTime"])
    if not is_valid:
        return jsonify({"error": f"Missing required fields: {err.replace('Missing fields: ', '')}"}), 400

    user_id = get_jwt_identity()
    schedule_id = exam_model.save_exam_schedule(exam_id, data)
    log_audit(user_id, "ExamSchedule", schedule_id, "CREATE", None, data, get_client_ip(), get_user_agent())
    return jsonify({"scheduleId": schedule_id, "message": "Exam schedule saved"}), 201


@exams_bp.get("/exams/<int:exam_id>/schedule")
@jwt_required()
def get_schedule(exam_id):
    schedule = exam_model.get_exam_schedule(exam_id)
    if not schedule:
        return jsonify({"error": "No schedule found for this exam"}), 404
    return jsonify(schedule)


# ---------- Exam <-> Question assignment ----------

@exams_bp.post("/exams/<int:exam_id>/questions")
@role_required("Admin", "Faculty")
def assign_question_to_exam(exam_id):
    data = request.get_json(force=True)
    required = ["questionId", "marks"]
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    user_id = get_jwt_identity()
    exam_question_id = exam_model.assign_question_to_exam(exam_id, data)
    log_audit(user_id, "ExamQuestion", exam_question_id, "CREATE", None, data, get_client_ip(), get_user_agent())
    return jsonify({"examQuestionId": exam_question_id, "message": "Question assigned to exam"}), 201


@exams_bp.delete("/exams/<int:exam_id>/questions/<int:question_id>")
@role_required("Admin", "Faculty")
def remove_question_from_exam(exam_id, question_id):
    user_id = get_jwt_identity()
    rowcount = exam_model.remove_question_from_exam(exam_id, question_id)
    if rowcount == 0:
        return jsonify({"error": "Question assignment not found"}), 404
    log_audit(user_id, "ExamQuestion", exam_id, "DELETE", {"questionId": question_id}, None, get_client_ip(), get_user_agent())
    return jsonify({"message": "Question removed from exam blueprint"})


@exams_bp.get("/exams/<int:exam_id>/questions")
@jwt_required()
def list_exam_questions(exam_id):
    claims = get_jwt()
    is_staff = claims.get("role") in ("Admin", "Faculty")
    return jsonify(exam_model.list_exam_questions(exam_id, is_staff))


# ---------- Candidate Registration ----------

@exams_bp.post("/exams/<int:exam_id>/register")
@role_required("Student")
def register_for_exam(exam_id):
    user_id = get_jwt_identity()
    registration_id, err_msg = exam_model.register_student_for_exam(exam_id, user_id)
    if err_msg:
        return jsonify({"error": err_msg}), 409
    log_audit(user_id, "CandidateRegistration", registration_id, "CREATE", None, {"examId": exam_id, "userId": user_id}, get_client_ip(), get_user_agent())
    return jsonify({"registrationId": registration_id, "message": "Successfully registered for exam"}), 201


@exams_bp.get("/exams/<int:exam_id>/registrations")
@role_required("Admin", "Faculty")
def list_exam_registrations(exam_id):
    return jsonify(exam_model.list_exam_registrations(exam_id))


@exams_bp.get("/students/<int:user_id>/registrations")
@jwt_required()
def student_registrations(user_id):
    return jsonify(exam_model.list_student_registrations(user_id))
