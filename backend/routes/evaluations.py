"""Evaluation and grading routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from auth_utils import role_required
from database import fetch_one, execute, log_audit
from models import result as result_model
from services.evaluation_service import auto_grade_internal, calculate_grade_and_pass

evaluations_bp = Blueprint("evaluations_bp", __name__)


@evaluations_bp.get("/evaluations/pending")
@role_required("Admin", "Faculty")
def list_pending_evaluations():
    """List submitted candidate attempts awaiting manual evaluation or finalization."""
    return jsonify(result_model.list_pending_evaluations())


@evaluations_bp.post("/attempts/<int:attempt_id>/evaluate/auto")
@role_required("Admin", "Faculty")
def auto_evaluate(attempt_id):
    """Auto-grade objective (MCQ/MSQ/TRUE_FALSE) answers."""
    user_id = get_jwt_identity()
    eval_id, total_marks, correct, wrong, skipped = auto_grade_internal(attempt_id)
    execute("UPDATE Evaluation SET evaluatedBy = %s WHERE evaluationId = %s", (user_id, eval_id))
    log_audit(user_id, "Evaluation", eval_id, "AUTO_EVALUATE", None, f"Score: {total_marks}")
    return jsonify({
        "evaluationId": eval_id,
        "totalMarksObtained": total_marks,
        "totalCorrect": correct,
        "totalWrong": wrong,
        "totalSkipped": skipped,
    })


@evaluations_bp.post("/evaluations/<int:evaluation_id>/details")
@role_required("Admin", "Faculty")
def manual_grade_question(evaluation_id):
    """Manually grade a single descriptive/coding question inside an evaluation."""
    data = request.get_json(force=True)
    required = ["questionId", "marksAwarded", "maxMarks"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    question_id = data["questionId"]
    marks_awarded = float(data["marksAwarded"])
    max_marks = float(data["maxMarks"])
    is_correct = data.get("isCorrect", marks_awarded >= max_marks)
    remarks = data.get("evaluatorRemarks")
    evaluated_by = get_jwt_identity()

    totals = result_model.save_manual_grade(
        evaluation_id, question_id, marks_awarded, max_marks, is_correct, remarks, evaluated_by
    )

    # If a Result row already exists for this evaluation, synchronize it to avoid stale scores
    existing_result = fetch_one("SELECT resultId FROM Result WHERE evaluationId = %s", (evaluation_id,))
    if existing_result:
        eval_exam = fetch_one(
            """SELECT e.totalMarks, e.passingMarks FROM Evaluation ev
               JOIN ExamAttempt att ON att.attemptId = ev.attemptId
               JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
               JOIN Exam e ON e.examId = cr.examId
               WHERE ev.evaluationId = %s""",
            (evaluation_id,)
        )
        if eval_exam:
            pct, grd, p_stat = calculate_grade_and_pass(
                totals["total"], eval_exam.get("totalMarks"), eval_exam.get("passingMarks")
            )
            execute(
                "UPDATE Result SET percentage = %s, grade = %s, passStatus = %s WHERE resultId = %s",
                (pct, grd, p_stat, existing_result["resultId"])
            )

    return jsonify({"message": "Question graded", "runningTotal": totals["total"]})


@evaluations_bp.get("/evaluations/<int:evaluation_id>")
@jwt_required()
def get_evaluation(evaluation_id):
    evaluation = result_model.get_evaluation_by_id(evaluation_id)
    if not evaluation:
        return jsonify({"error": "Evaluation not found"}), 404
    return jsonify(evaluation)


@evaluations_bp.post("/evaluations/<int:evaluation_id>/finalize")
@role_required("Admin", "Faculty")
def finalize_evaluation(evaluation_id):
    """Finalize evaluation and create/refresh its Result row (percentage, grade, pass/fail)."""
    user_id = get_jwt_identity()
    evaluation = fetch_one("SELECT * FROM Evaluation WHERE evaluationId = %s", (evaluation_id,))
    if not evaluation:
        return jsonify({"error": "Evaluation not found"}), 404

    attempt = fetch_one("SELECT * FROM ExamAttempt WHERE attemptId = %s", (evaluation["attemptId"],))
    registration = fetch_one(
        "SELECT * FROM CandidateRegistration WHERE registrationId = %s", (attempt["registrationId"],)
    )
    exam = fetch_one("SELECT totalMarks, passingMarks, examTitle FROM Exam WHERE examId = %s",
                      (registration["examId"],))

    percentage, grade, pass_status = calculate_grade_and_pass(
        evaluation["totalMarksObtained"], exam.get("totalMarks"), exam.get("passingMarks")
    )

    execute("UPDATE Evaluation SET evaluationStatus = 'FINALIZED', evaluatedBy = %s WHERE evaluationId = %s",
            (user_id, evaluation_id))
    execute("UPDATE ExamAttempt SET status = 'EVALUATED' WHERE attemptId = %s",
            (evaluation["attemptId"],))

    existing_result = fetch_one("SELECT resultId FROM Result WHERE evaluationId = %s", (evaluation_id,))
    if existing_result:
        execute(
            "UPDATE Result SET percentage = %s, grade = %s, passStatus = %s WHERE resultId = %s",
            (percentage, grade, pass_status, existing_result["resultId"]),
        )
        result_id = existing_result["resultId"]
    else:
        result_id, _ = execute(
            """INSERT INTO Result (evaluationId, percentage, grade, passStatus)
               VALUES (%s, %s, %s, %s)""",
            (evaluation_id, percentage, grade, pass_status),
        )

    log_audit(user_id, "Evaluation", evaluation_id, "FINALIZE", None, f"Result #{result_id}, {percentage}%, Grade {grade}")
    return jsonify({"resultId": result_id, "percentage": percentage, "grade": grade, "passStatus": pass_status})
