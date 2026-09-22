"""Exam analytics and performance report routes."""
from flask import Blueprint, jsonify
from auth_utils import role_required
from services import result_service

reports_bp = Blueprint("reports_bp", __name__)


@reports_bp.get("/exams/<int:exam_id>/report")
@role_required("Admin", "Faculty")
def get_exam_report(exam_id):
    """Generate detailed performance analytics for an exam."""
    report, err_msg, status_code = result_service.generate_exam_report(exam_id)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(report), status_code
