"""Data access layer for Evaluation, EvaluationDetail, and Result."""
from database import fetch_all, fetch_one, execute


def list_pending_evaluations():
    return fetch_all(
        """SELECT ea.attemptId, ea.attemptNumber, ea.status AS attemptStatus,
                  ea.submittedAt, ea.submissionMethod, ea.startTime, ea.endTime,
                  u.userId, u.firstName, u.lastName, u.email,
                  e.examId, e.examTitle, e.examCode, e.totalMarks, e.passingMarks,
                  ev.evaluationId, ev.evaluationStatus, ev.totalMarksObtained
           FROM ExamAttempt ea
           JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
           JOIN User u ON u.userId = cr.userId
           JOIN Exam e ON e.examId = cr.examId
           LEFT JOIN Evaluation ev ON ev.attemptId = ea.attemptId
           WHERE ea.status IN ('SUBMITTED', 'AUTO_SUBMITTED')
           ORDER BY ea.submittedAt DESC"""
    )


def get_evaluation_by_id(evaluation_id):
    evaluation = fetch_one(
        """SELECT ev.*, ea.attemptNumber, ea.submittedAt, ea.startTime, ea.endTime,
                  u.userId, u.firstName, u.lastName, u.email,
                  e.examId, e.examTitle, e.examCode, e.totalMarks AS examTotalMarks, e.passingMarks
           FROM Evaluation ev
           JOIN ExamAttempt ea ON ea.attemptId = ev.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
           JOIN User u ON u.userId = cr.userId
           JOIN Exam e ON e.examId = cr.examId
           WHERE ev.evaluationId = %s""",
        (evaluation_id,)
    )
    if not evaluation:
        return None
    evaluation["details"] = fetch_all(
        """SELECT ed.*, q.questionText, q.questionType, q.correctAnswer, q.explanation,
                  a.selectedOptionId, a.answerText AS candidateAnswerText,
                  qo.optionText AS selectedOptionText
           FROM EvaluationDetail ed
           JOIN Question q ON q.questionId = ed.questionId
           LEFT JOIN Answer a ON a.attemptId = %s AND a.questionId = ed.questionId
           LEFT JOIN QuestionOption qo ON qo.optionId = a.selectedOptionId
           WHERE ed.evaluationId = %s""",
        (evaluation["attemptId"], evaluation_id),
    )
    return evaluation


def save_manual_grade(evaluation_id, question_id, marks_awarded, max_marks, is_correct, remarks, evaluated_by):
    existing = fetch_one(
        "SELECT evaluationDetailId FROM EvaluationDetail WHERE evaluationId = %s AND questionId = %s",
        (evaluation_id, question_id),
    )
    if existing:
        execute(
            """UPDATE EvaluationDetail
               SET marksAwarded = %s, maxMarks = %s, isCorrect = %s, evaluatorRemarks = %s
               WHERE evaluationDetailId = %s""",
            (marks_awarded, max_marks, is_correct, remarks, existing["evaluationDetailId"]),
        )
    else:
        execute(
            """INSERT INTO EvaluationDetail (evaluationId, questionId, marksAwarded, maxMarks,
                                              isCorrect, evaluatorRemarks)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (evaluation_id, question_id, marks_awarded, max_marks, is_correct, remarks),
        )

    totals = fetch_one(
        """SELECT COALESCE(SUM(marksAwarded), 0) AS total,
                  SUM(CASE WHEN isCorrect THEN 1 ELSE 0 END) AS correct,
                  SUM(CASE WHEN NOT isCorrect THEN 1 ELSE 0 END) AS wrong
           FROM EvaluationDetail WHERE evaluationId = %s""",
        (evaluation_id,),
    )
    execute(
        """UPDATE Evaluation
           SET totalMarksObtained = %s, totalCorrect = %s, totalWrong = %s,
               evaluationStatus = 'MANUAL_EVALUATED', evaluatedBy = %s, evaluatedAt = NOW()
           WHERE evaluationId = %s""",
        (totals["total"], totals["correct"], totals["wrong"], evaluated_by, evaluation_id),
    )
    return totals


def list_all_results(exam_id=None):
    query = """SELECT r.*, e.examId, e.examTitle, e.examCode, e.totalMarks, e.passingMarks,
                      u.userId, u.firstName, u.lastName, u.email,
                      ev.totalMarksObtained, ev.totalCorrect, ev.totalWrong, ev.totalSkipped
               FROM Result r
               JOIN Evaluation ev ON ev.evaluationId = r.evaluationId
               JOIN ExamAttempt att ON att.attemptId = ev.attemptId
               JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
               JOIN Exam e ON e.examId = cr.examId
               JOIN User u ON u.userId = cr.userId"""
    params = []
    if exam_id:
        query += " WHERE e.examId = %s"
        params.append(exam_id)
    query += " ORDER BY r.resultId DESC"
    return fetch_all(query, params)


def get_result_detail(result_id):
    result = fetch_one(
        """SELECT r.*, e.examId, e.examTitle, e.examCode, e.totalMarks, e.passingMarks, e.durationMinutes,
                  s.subjectName, s.subjectCode,
                  cr.userId, u.firstName, u.lastName, u.email,
                  ev.totalMarksObtained, ev.totalCorrect, ev.totalWrong, ev.totalSkipped, ev.evaluationStatus,
                  att.attemptId, att.attemptNumber, att.startTime, att.endTime, att.submittedAt
           FROM Result r
           JOIN Evaluation ev ON ev.evaluationId = r.evaluationId
           JOIN ExamAttempt att ON att.attemptId = ev.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
           JOIN Exam e ON e.examId = cr.examId
           JOIN Subject s ON s.subjectId = e.subjectId
           JOIN User u ON u.userId = cr.userId
           WHERE r.resultId = %s""",
        (result_id,),
    )
    if not result:
        return None
    result["questionBreakdown"] = fetch_all(
        """SELECT ed.questionId, ed.marksAwarded, ed.maxMarks, ed.isCorrect, ed.evaluatorRemarks,
                  q.questionText, q.questionType, q.explanation,
                  a.selectedOptionId, a.answerText,
                  qo.optionText AS selectedOptionText
           FROM EvaluationDetail ed
           JOIN Question q ON q.questionId = ed.questionId
           LEFT JOIN Answer a ON a.attemptId = %s AND a.questionId = ed.questionId
           LEFT JOIN QuestionOption qo ON qo.optionId = a.selectedOptionId
           WHERE ed.evaluationId = %s""",
        (result["attemptId"], result["evaluationId"]),
    )
    return result


def get_student_results(user_id):
    return fetch_all(
        """SELECT r.resultId, r.percentage, r.grade, r.passStatus, r.isPublished, r.publishedAt,
                  e.examId, e.examTitle, e.examCode, e.totalMarks, e.passingMarks,
                  s.subjectName, ev.totalMarksObtained, ev.totalCorrect, ev.totalWrong,
                  att.attemptId, att.submittedAt
           FROM Result r
           JOIN Evaluation ev ON ev.evaluationId = r.evaluationId
           JOIN ExamAttempt att ON att.attemptId = ev.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
           JOIN Exam e ON e.examId = cr.examId
           JOIN Subject s ON s.subjectId = e.subjectId
           WHERE cr.userId = %s AND r.isPublished = TRUE
           ORDER BY r.publishedAt DESC""",
        (user_id,),
    )
