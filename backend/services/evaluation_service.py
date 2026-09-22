"""Evaluation and grading services."""
from database import fetch_all, fetch_one, execute, transaction, log_audit


def calculate_grade_and_pass(obtained_marks, total_marks, passing_marks):
    """Safely calculate percentage, letter grade, and pass status using system grading rules."""
    try:
        obtained = float(obtained_marks) if obtained_marks is not None else 0.0
        exam_total = float(total_marks) if total_marks is not None else 0.0
        pass_min = float(passing_marks) if passing_marks is not None else (exam_total * 0.40)
        percentage = round((obtained / exam_total) * 100, 2) if exam_total > 0 else 0.0
        grade = (
            "A+" if percentage >= 90 else
            "A"  if percentage >= 80 else
            "B"  if percentage >= 70 else
            "C"  if percentage >= 60 else
            "D"  if percentage >= 50 else
            "F"
        )
        pass_status = (percentage >= (pass_min / exam_total * 100)) if exam_total > 0 else False
        return percentage, grade, pass_status
    except Exception:
        return 0.0, "F", False


def auto_grade_internal(attempt_id):
    """Internal helper to grade objective questions without needing an HTTP request."""
    answers = fetch_all(
        """SELECT a.answerId, a.questionId, a.selectedOptionId, a.answerText, q.questionType,
                  eq.marks, eq.negativeMarks
           FROM Answer a
           JOIN Question q ON q.questionId = a.questionId
           JOIN ExamAttempt att ON att.attemptId = a.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
           JOIN ExamQuestion eq ON eq.examId = cr.examId AND eq.questionId = a.questionId
           WHERE a.attemptId = %s""",
        (attempt_id,),
    )

    evaluation = fetch_one("SELECT evaluationId FROM Evaluation WHERE attemptId = %s", (attempt_id,))
    if evaluation:
        evaluation_id = evaluation["evaluationId"]
    else:
        try:
            evaluation_id, _ = execute(
                "INSERT INTO Evaluation (attemptId, evaluationStatus) VALUES (%s, 'PENDING')",
                (attempt_id,),
            )
        except Exception:
            evaluation = fetch_one("SELECT evaluationId FROM Evaluation WHERE attemptId = %s", (attempt_id,))
            evaluation_id = evaluation["evaluationId"]

    total_marks, correct, wrong, skipped = 0.0, 0, 0, 0

    for ans in answers:
        qtype = ans["questionType"]
        marks_awarded, is_correct = 0.00, False

        if qtype in ("MCQ", "TRUE_FALSE"):
            if ans["selectedOptionId"] is None:
                skipped += 1
            else:
                correct_option = fetch_one(
                    "SELECT isCorrect FROM QuestionOption WHERE optionId = %s",
                    (ans["selectedOptionId"],),
                )
                is_correct = bool(correct_option and correct_option["isCorrect"])
                if is_correct:
                    marks_awarded = float(ans["marks"])
                    correct += 1
                else:
                    marks_awarded = -float(ans["negativeMarks"])
                    wrong += 1
            total_marks += marks_awarded

        elif qtype == "MSQ":
            correct_opts = {
                opt["optionId"]
                for opt in fetch_all("SELECT optionId FROM QuestionOption WHERE questionId = %s AND isCorrect = TRUE", (ans["questionId"],))
            }
            chosen_opts = set()
            if ans["selectedOptionId"]:
                chosen_opts.add(ans["selectedOptionId"])
            if ans.get("answerText"):
                try:
                    for part in ans["answerText"].split(","):
                        cleaned = part.strip()
                        if cleaned.isdigit():
                            chosen_opts.add(int(cleaned))
                except Exception:
                    pass

            if not chosen_opts:
                skipped += 1
            elif chosen_opts == correct_opts:
                marks_awarded = float(ans["marks"])
                is_correct = True
                correct += 1
            else:
                marks_awarded = -float(ans["negativeMarks"])
                wrong += 1
            total_marks += marks_awarded
        else:
            continue  # Descriptive / Coding left for manual grading

        existing_detail = fetch_one(
            "SELECT evaluationDetailId FROM EvaluationDetail WHERE evaluationId = %s AND questionId = %s",
            (evaluation_id, ans["questionId"]),
        )
        if existing_detail:
            execute(
                """UPDATE EvaluationDetail SET marksAwarded = %s, maxMarks = %s, isCorrect = %s
                   WHERE evaluationDetailId = %s""",
                (marks_awarded, ans["marks"], is_correct, existing_detail["evaluationDetailId"]),
            )
        else:
            execute(
                """INSERT INTO EvaluationDetail (evaluationId, questionId, marksAwarded, maxMarks, isCorrect)
                   VALUES (%s, %s, %s, %s, %s)""",
                (evaluation_id, ans["questionId"], marks_awarded, ans["marks"], is_correct),
            )

    execute(
        """UPDATE Evaluation
           SET totalMarksObtained = %s, totalCorrect = %s, totalWrong = %s, totalSkipped = %s,
               evaluationStatus = 'AUTO_EVALUATED', evaluatedAt = NOW()
           WHERE evaluationId = %s""",
        (total_marks, correct, wrong, skipped, evaluation_id),
    )

    # If a Result row already exists for this evaluation, synchronize it to avoid stale scores
    existing_result = fetch_one("SELECT resultId FROM Result WHERE evaluationId = %s", (evaluation_id,))
    if existing_result:
        reg_exam = fetch_one(
            """SELECT e.totalMarks, e.passingMarks FROM ExamAttempt att
               JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
               JOIN Exam e ON e.examId = cr.examId
               WHERE att.attemptId = %s""",
            (attempt_id,)
        )
        if reg_exam:
            pct, grd, p_stat = calculate_grade_and_pass(
                total_marks, reg_exam.get("totalMarks"), reg_exam.get("passingMarks")
            )
            execute(
                "UPDATE Result SET percentage = %s, grade = %s, passStatus = %s WHERE resultId = %s",
                (pct, grd, p_stat, existing_result["resultId"])
            )

    return evaluation_id, total_marks, correct, wrong, skipped
