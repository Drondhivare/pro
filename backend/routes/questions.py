"""Question bank, category, and difficulty level routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

import pymysql

from auth_utils import role_required
from database import log_audit
from utils.validators import validate_required
from models import question as question_model

questions_bp = Blueprint("questions_bp", __name__)


@questions_bp.get("/question-categories")
@jwt_required()
def list_categories():
    return jsonify(question_model.list_categories())


@questions_bp.post("/question-categories")
@role_required("Admin", "Faculty")
def create_category():
    data = request.get_json(force=True)
    user_id = get_jwt_identity()
    category_name = (data.get("categoryName") or "").strip()
    if not category_name:
        return jsonify({"error": "categoryName is required"}), 400
    if len(category_name) < 3:
        return jsonify({"error": "Category name must be at least 3 characters"}), 400

    try:
        category_id = question_model.create_category(category_name, data.get("description"), user_id)
        log_audit(user_id, "QuestionCategory", category_id, "CREATE", None, category_name)
        return jsonify({"categoryId": category_id, "message": "Category created"}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"error": f"Category '{category_name}' already exists."}), 409


@questions_bp.get("/difficulty-levels")
@jwt_required()
def list_difficulty_levels():
    return jsonify(question_model.list_difficulty_levels())


@questions_bp.get("/questions")
@jwt_required()
def list_questions():
    category_id = request.args.get("categoryId")
    difficulty_id = request.args.get("difficultyLevelId")
    question_type = request.args.get("questionType")
    search = request.args.get("search")
    return jsonify(question_model.list_questions(category_id, difficulty_id, question_type, search))


@questions_bp.post("/questions")
@role_required("Admin", "Faculty")
def create_question():
    data = request.get_json(force=True)
    user_id = get_jwt_identity()

    is_valid, err = validate_required(data, ["categoryId", "difficultyLevelId", "questionType", "questionText"])
    if not is_valid:
        return jsonify({"error": f"Missing required fields: {err.replace('Missing fields: ', '')}"}), 400

    question_id = question_model.create_question(data, user_id)
    log_audit(user_id, "Question", question_id, "CREATE", None, data["questionText"][:100])
    return jsonify({"questionId": question_id, "message": "Question created"}), 201


@questions_bp.get("/questions/<int:question_id>")
@jwt_required()
def get_question(question_id):
    question = question_model.get_question_by_id(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404
    return jsonify(question)


@questions_bp.put("/questions/<int:question_id>")
@role_required("Admin", "Faculty")
def update_question(question_id):
    data = request.get_json(force=True)
    user_id = get_jwt_identity()

    target_type = data.get("questionType")
    if not target_type:
        curr = question_model.get_question_by_id(question_id)
        if not curr:
            return jsonify({"error": "Question not found"}), 404
        target_type = curr["questionType"]

    if "options" in data or target_type == "DESCRIPTIVE":
        options = data.get("options", [])
        if target_type == "MCQ" and "options" in data:
            if len(options) < 2:
                return jsonify({"error": "MCQ questions must have at least 2 options."}), 400
            for o in options:
                if not (o.get("optionText") or "").strip():
                    return jsonify({"error": "All MCQ options must have non-empty text."}), 400
            correct_count = sum(1 for o in options if bool(o.get("isCorrect")))
            if correct_count != 1:
                return jsonify({"error": "MCQ questions must have exactly 1 correct option selected."}), 400
        elif target_type == "MSQ" and "options" in data:
            if len(options) < 2:
                return jsonify({"error": "MSQ questions must have at least 2 options."}), 400
            for o in options:
                if not (o.get("optionText") or "").strip():
                    return jsonify({"error": "All MSQ options must have non-empty text."}), 400
            correct_count = sum(1 for o in options if bool(o.get("isCorrect")))
            if correct_count < 1:
                return jsonify({"error": "MSQ questions must have at least 1 correct option selected."}), 400
        elif target_type == "TRUE_FALSE" and "options" in data:
            if len(options) != 2:
                return jsonify({"error": "True/False questions must have exactly 2 options."}), 400
            for o in options:
                if not (o.get("optionText") or "").strip():
                    return jsonify({"error": "True/False options must have non-empty text."}), 400
            correct_count = sum(1 for o in options if bool(o.get("isCorrect")))
            if correct_count != 1:
                return jsonify({"error": "True/False questions must have exactly 1 correct option selected."}), 400
        elif target_type == "DESCRIPTIVE":
            if "options" in data and len(options) > 0:
                return jsonify({"error": "Descriptive questions cannot have options."}), 400
            if "modelAnswer" in data or "correctAnswer" in data or data.get("questionType") == "DESCRIPTIVE":
                model_ans = (data.get("modelAnswer") or data.get("correctAnswer") or "").strip()
                if not model_ans:
                    return jsonify({"error": "Model Answer is required for descriptive questions."}), 400

    existing = question_model.update_question(question_id, data, user_id)
    if not existing:
        return jsonify({"error": "Question not found"}), 404

    log_audit(user_id, "Question", question_id, "UPDATE", existing["questionText"][:100], data.get("questionText", existing["questionText"])[:100])
    return jsonify({"message": "Question updated"})


@questions_bp.delete("/questions/<int:question_id>")
@role_required("Admin", "Faculty")
def delete_question(question_id):
    user_id = get_jwt_identity()
    existing = question_model.delete_question(question_id)
    if not existing:
        return jsonify({"error": "Question not found"}), 404

    log_audit(user_id, "Question", question_id, "DELETE", existing["questionText"][:100], "Deactivated")
    return jsonify({"message": "Question deactivated"})


@questions_bp.get("/questions/<int:question_id>/options")
@jwt_required()
def get_question_options(question_id):
    return jsonify(question_model.get_question_options(question_id))
