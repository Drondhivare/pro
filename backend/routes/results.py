"""Result management, scorecard retrieval, and publication routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from auth_utils import role_required
from models import result as result_model
from services import result_service
from services.evaluation_service import calculate_grade_and_pass

results_bp = Blueprint("results_bp", __name__)


@results_bp.get("/results")
@role_required("Admin", "Faculty")
def list_all_results():
    """List published and unpublished results across all exams or for a specific exam."""
    exam_id = request.args.get("examId")
    results = result_model.list_all_results(exam_id)
    for r in results:
        calc_pct, calc_grade, calc_pass = calculate_grade_and_pass(
            r.get("totalMarksObtained"), r.get("totalMarks"), r.get("passingMarks")
        )
        r["percentage"] = calc_pct
        if not r.get("grade") or r.get("grade") != calc_grade:
            r["grade"] = calc_grade
        r["passStatus"] = 1 if calc_pass else 0
    return jsonify(results)


@results_bp.post("/results/<int:result_id>/publish")
@role_required("Admin", "Faculty")
def publish_result(result_id):
    published_by = get_jwt_identity()
    resp, err_msg, status_code = result_service.publish_single_result(result_id, published_by)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(resp), status_code


@results_bp.post("/exams/<int:exam_id>/results/publish-all")
@role_required("Admin", "Faculty")
def publish_all_results_for_exam(exam_id):
    """Publish all finalized results for an exam in bulk and notify students."""
    published_by = get_jwt_identity()
    resp, err_msg, status_code = result_service.publish_all_exam_results(exam_id, published_by)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(resp), status_code


@results_bp.get("/results/<int:result_id>")
@jwt_required()
def get_result(result_id):
    user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")

    result = result_model.get_result_detail(result_id)
    if not result:
        return jsonify({"error": "Result not found"}), 404

    # Students may only view their own published results
    if role == "Student":
        if str(result["userId"]) != str(user_id):
            return jsonify({"error": "Unauthorized"}), 403
        if not result["isPublished"]:
            return jsonify({"error": "Result has not yet been published by the faculty"}), 403

    calc_pct, calc_grade, calc_pass = calculate_grade_and_pass(
        result.get("totalMarksObtained"), result.get("totalMarks"), result.get("passingMarks")
    )
    result["percentage"] = calc_pct
    result["grade"] = calc_grade
    result["passStatus"] = 1 if calc_pass else 0

    return jsonify(result)


@results_bp.get("/students/<int:user_id>/results")
@jwt_required()
def student_results(user_id):
    current_user = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role")

    if role == "Student" and str(current_user) != str(user_id):
        return jsonify({"error": "Unauthorized"}), 403

    rows = result_model.get_student_results(user_id)
    for r in rows:
        calc_pct, calc_grade, calc_pass = calculate_grade_and_pass(
            r.get("totalMarksObtained"), r.get("totalMarks"), r.get("passingMarks")
        )
        r["percentage"] = calc_pct
        if not r.get("grade") or r.get("grade") != calc_grade:
            r["grade"] = calc_grade
        r["passStatus"] = 1 if calc_pass else 0
    return jsonify(rows)
