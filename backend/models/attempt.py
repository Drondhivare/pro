"""Data access layer for ExamAttempt, Answer, and ExamSecurityEvent."""
from database import fetch_all, fetch_one, execute


def get_candidate_registration(exam_id, user_id):
    return fetch_one(
        "SELECT registrationId FROM CandidateRegistration WHERE examId = %s AND userId = %s",
        (exam_id, user_id),
    )


def get_exam_for_attempt(exam_id):
    return fetch_one("SELECT * FROM Exam WHERE examId = %s", (exam_id,))


def get_active_attempt(registration_id):
    return fetch_one(
        "SELECT attemptId, attemptNumber FROM ExamAttempt WHERE registrationId = %s AND status = 'IN_PROGRESS'",
        (registration_id,)
    )


def get_previous_attempts(registration_id):
    return fetch_all(
        "SELECT attemptNumber FROM ExamAttempt WHERE registrationId = %s", (registration_id,)
    )


def create_attempt(registration_id, attempt_number, ip_address):
    attempt_id, _ = execute(
        """INSERT INTO ExamAttempt (registrationId, attemptNumber, status, ipAddress)
           VALUES (%s, %s, 'IN_PROGRESS', %s)""",
        (registration_id, attempt_number, ip_address),
    )
    return attempt_id


def get_attempt_detail(attempt_id):
    attempt = fetch_one(
        """SELECT ea.*, cr.userId, cr.examId, e.examTitle, e.examCode, e.durationMinutes,
                  e.totalMarks, e.passingMarks, es.startTime AS scheduledStartTime, es.endTime AS scheduledEndTime
           FROM ExamAttempt ea
           JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
           JOIN Exam e ON e.examId = cr.examId
           LEFT JOIN ExamSchedule es ON es.examId = e.examId
           WHERE ea.attemptId = %s""",
        (attempt_id,)
    )
    if not attempt:
        return None
    attempt["answers"] = fetch_all("SELECT * FROM Answer WHERE attemptId = %s", (attempt_id,))
    return attempt


def save_or_update_answer(attempt_id, data):
    question_id = data["questionId"]
    existing = fetch_one(
        "SELECT answerId FROM Answer WHERE attemptId = %s AND questionId = %s",
        (attempt_id, question_id),
    )
    if existing:
        execute(
            """UPDATE Answer SET selectedOptionId = %s, answerText = %s,
                                  isMarkedForReview = %s, isAnswered = %s,
                                  timeSpentSeconds = %s, submittedAt = NOW()
               WHERE answerId = %s""",
            (data.get("selectedOptionId"), data.get("answerText"),
             bool(data.get("isMarkedForReview", False)), bool(data.get("isAnswered", True)),
             data.get("timeSpentSeconds", 0), existing["answerId"]),
        )
        return existing["answerId"], False

    answer_id, _ = execute(
        """INSERT INTO Answer (attemptId, questionId, selectedOptionId, answerText,
                                isMarkedForReview, isAnswered, timeSpentSeconds)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (attempt_id, question_id, data.get("selectedOptionId"), data.get("answerText"),
         bool(data.get("isMarkedForReview", False)), bool(data.get("isAnswered", True)),
         data.get("timeSpentSeconds", 0)),
    )
    return answer_id, True


def list_attempt_answers(attempt_id):
    return fetch_all("SELECT * FROM Answer WHERE attemptId = %s", (attempt_id,))


def get_attempt_owner(attempt_id):
    return fetch_one(
        """SELECT ea.*, cr.userId FROM ExamAttempt ea
           JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
           WHERE ea.attemptId = %s""",
        (attempt_id,)
    )
