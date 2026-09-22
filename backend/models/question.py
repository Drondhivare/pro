"""Data access layer for Question, QuestionOption, QuestionCategory, and DifficultyLevel."""
from database import fetch_all, fetch_one, execute


def list_categories():
    return fetch_all("SELECT * FROM QuestionCategory WHERE isActive = TRUE ORDER BY categoryName")


def create_category(category_name, description, user_id):
    category_id, _ = execute(
        "INSERT INTO QuestionCategory (categoryName, description, createdBy) VALUES (%s, %s, %s)",
        (category_name, description, user_id),
    )
    return category_id


def list_difficulty_levels():
    return fetch_all("SELECT * FROM DifficultyLevel ORDER BY difficultyScore")


def list_questions(category_id=None, difficulty_id=None, question_type=None, search=None):
    query = """SELECT q.*, c.categoryName, d.levelName,
                      (SELECT COUNT(*) FROM QuestionOption qo WHERE qo.questionId = q.questionId) AS optionCount
               FROM Question q
               JOIN QuestionCategory c ON c.categoryId = q.categoryId
               JOIN DifficultyLevel d ON d.difficultyLevelId = q.difficultyLevelId
               WHERE q.isActive = TRUE"""
    params = []
    if category_id:
        query += " AND q.categoryId = %s"
        params.append(category_id)
    if difficulty_id:
        query += " AND q.difficultyLevelId = %s"
        params.append(difficulty_id)
    if question_type:
        query += " AND q.questionType = %s"
        params.append(question_type)
    if search:
        query += " AND q.questionText LIKE %s"
        params.append(f"%{search}%")

    query += " ORDER BY q.questionId DESC"
    rows = fetch_all(query, params)
    for r in rows:
        r["modelAnswer"] = r.get("correctAnswer")
    return rows


def create_question(data, user_id):
    correct_ans = data.get("modelAnswer") if data.get("modelAnswer") is not None else data.get("correctAnswer")
    question_id, _ = execute(
        """INSERT INTO Question (categoryId, difficultyLevelId, questionType, questionText,
                                  correctAnswer, explanation, defaultMarks, negativeMarks,
                                  estimatedTimeSeconds, createdBy)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (data["categoryId"], data["difficultyLevelId"], data["questionType"],
         data["questionText"], correct_ans, data.get("explanation"),
         data.get("defaultMarks", 1.00), data.get("negativeMarks", 0.00),
         data.get("estimatedTimeSeconds"), user_id),
    )

    for i, opt in enumerate(data.get("options", []), start=1):
        execute(
            """INSERT INTO QuestionOption (questionId, optionText, optionOrder, isCorrect)
               VALUES (%s, %s, %s, %s)""",
            (question_id, opt["optionText"], opt.get("optionOrder", i), bool(opt.get("isCorrect", False))),
        )
    return question_id


def get_question_by_id(question_id):
    question = fetch_one(
        """SELECT q.*, c.categoryName, d.levelName
           FROM Question q
           JOIN QuestionCategory c ON c.categoryId = q.categoryId
           JOIN DifficultyLevel d ON d.difficultyLevelId = q.difficultyLevelId
           WHERE q.questionId = %s""",
        (question_id,)
    )
    if not question:
        return None
    question["modelAnswer"] = question.get("correctAnswer")
    question["options"] = fetch_all(
        "SELECT * FROM QuestionOption WHERE questionId = %s ORDER BY optionOrder", (question_id,)
    )
    return question


def update_question(question_id, data, user_id):
    existing = fetch_one("SELECT * FROM Question WHERE questionId = %s", (question_id,))
    if not existing:
        return None

    target_q_type = data.get("questionType", existing.get("questionType"))

    if target_q_type == "DESCRIPTIVE":
        if "modelAnswer" in data and "correctAnswer" not in data:
            data["correctAnswer"] = data["modelAnswer"]
    else:
        # Non-descriptive question: clear correctAnswer if transitioning from DESCRIPTIVE and not explicitly set
        if existing.get("questionType") == "DESCRIPTIVE" and "correctAnswer" not in data:
            data["correctAnswer"] = None

    if "modelAnswer" in data and "correctAnswer" not in data:
        data["correctAnswer"] = data["modelAnswer"]

    editable = ["categoryId", "difficultyLevelId", "questionType", "questionText",
                "correctAnswer", "explanation", "defaultMarks", "negativeMarks",
                "estimatedTimeSeconds", "isActive"]
    fields, params = [], []
    for col in editable:
        if col in data:
            fields.append(f"{col} = %s")
            params.append(data[col])

    if fields:
        fields.append("updatedBy = %s")
        params.append(user_id)
        params.append(question_id)
        execute(f"UPDATE Question SET {', '.join(fields)} WHERE questionId = %s", params)

    # Synchronize question options
    if target_q_type == "DESCRIPTIVE":
        # Descriptive questions must have zero QuestionOption records
        execute("DELETE FROM QuestionOption WHERE questionId = %s", (question_id,))
    elif "options" in data:
        submitted_options = data.get("options", [])
        existing_options = fetch_all("SELECT optionId FROM QuestionOption WHERE questionId = %s", (question_id,))
        existing_ids = {int(row["optionId"]) for row in existing_options}
        retained_ids = set()

        for i, opt in enumerate(submitted_options, start=1):
            opt_id = opt.get("optionId")
            if opt_id is not None:
                try:
                    opt_id = int(opt_id)
                except (ValueError, TypeError):
                    opt_id = None

            order = opt.get("optionOrder", i)
            is_correct = bool(opt.get("isCorrect", False))
            opt_text = opt.get("optionText", "")

            if opt_id and opt_id in existing_ids:
                retained_ids.add(opt_id)
                execute(
                    """UPDATE QuestionOption 
                       SET optionText = %s, optionOrder = %s, isCorrect = %s 
                       WHERE optionId = %s AND questionId = %s""",
                    (opt_text, order, is_correct, opt_id, question_id),
                )
            else:
                execute(
                    """INSERT INTO QuestionOption (questionId, optionText, optionOrder, isCorrect)
                       VALUES (%s, %s, %s, %s)""",
                    (question_id, opt_text, order, is_correct),
                )

        to_delete = existing_ids - retained_ids
        for del_id in to_delete:
            execute("DELETE FROM QuestionOption WHERE optionId = %s AND questionId = %s", (del_id, question_id))

    return existing


def delete_question(question_id):
    existing = fetch_one("SELECT questionText FROM Question WHERE questionId = %s", (question_id,))
    if not existing:
        return None
    execute("UPDATE Question SET isActive = FALSE WHERE questionId = %s", (question_id,))
    return existing


def get_question_options(question_id):
    return fetch_all("SELECT * FROM QuestionOption WHERE questionId = %s ORDER BY optionOrder", (question_id,))
