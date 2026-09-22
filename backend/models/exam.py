"""Data access layer for Exam, ExamSchedule, ExamQuestion, and CandidateRegistration."""
from database import fetch_all, fetch_one, execute


def list_exams():
    return fetch_all(
        """SELECT e.*, s.subjectName, s.subjectCode,
                  es.startTime, es.endTime, es.autoSubmit
           FROM Exam e
           JOIN Subject s ON s.subjectId = e.subjectId
           LEFT JOIN ExamSchedule es ON es.examId = e.examId
           ORDER BY e.examId DESC"""
    )


def list_student_available_exams(user_id):
    return fetch_all(
        """SELECT e.examId, e.examCode, e.examTitle, e.examType, e.totalMarks,
                  e.passingMarks, e.durationMinutes, e.instructions, e.examStatus,
                  s.subjectId, s.subjectCode, s.subjectName,
                  es.scheduleId, es.startTime, es.endTime, es.registrationStart,
                  es.registrationEnd, es.lateEntryMinutes, es.autoSubmit,
                  cr.registrationId, cr.registrationStatus, cr.eligibilityVerified
           FROM Exam e
           JOIN Subject s ON s.subjectId = e.subjectId
           LEFT JOIN ExamSchedule es ON es.examId = e.examId
           LEFT JOIN CandidateRegistration cr ON cr.examId = e.examId AND cr.userId = %s
           WHERE e.isActive = TRUE AND e.examStatus IN ('ACTIVE', 'SCHEDULED')
           ORDER BY es.startTime ASC, e.examId DESC""",
        (user_id,),
    )


def create_exam(data, user_id):
    exam_id, _ = execute(
        """INSERT INTO Exam (subjectId, examCode, examTitle, examType, totalMarks,
                              passingMarks, durationMinutes, instructions, maximumAttempts,
                              shuffleQuestions, shuffleOptions, negativeMarking,
                              negativeMarksPerQuestion, createdBy)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (data["subjectId"], data["examCode"], data["examTitle"], data.get("examType", "OBJECTIVE"),
         data["totalMarks"], data["passingMarks"], data["durationMinutes"],
         data.get("instructions"), data.get("maximumAttempts", 1),
         data.get("shuffleQuestions", True), data.get("shuffleOptions", True),
         data.get("negativeMarking", False), data.get("negativeMarksPerQuestion", 0.00),
         user_id),
    )

    if data.get("startTime") and data.get("endTime"):
        execute(
            """INSERT INTO ExamSchedule (examId, startTime, endTime, registrationStart, registrationEnd, lateEntryMinutes, autoSubmit)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (exam_id, data["startTime"], data["endTime"], data.get("registrationStart"),
             data.get("registrationEnd"), data.get("lateEntryMinutes", 0), data.get("autoSubmit", True)),
        )
        execute("UPDATE Exam SET examStatus = 'SCHEDULED' WHERE examId = %s", (exam_id,))

    return exam_id


def get_exam_by_id(exam_id):
    exam = fetch_one(
        """SELECT e.*, s.subjectName, s.subjectCode FROM Exam e
           JOIN Subject s ON s.subjectId = e.subjectId
           WHERE e.examId = %s""",
        (exam_id,),
    )
    if not exam:
        return None
    exam["schedule"] = fetch_one("SELECT * FROM ExamSchedule WHERE examId = %s", (exam_id,))
    q_count = fetch_one("SELECT COUNT(*) AS totalQuestions, COALESCE(SUM(marks), 0) AS blueprintMarks FROM ExamQuestion WHERE examId = %s", (exam_id,))
    exam["totalQuestions"] = q_count["totalQuestions"] if q_count else 0
    exam["blueprintMarks"] = float(q_count["blueprintMarks"]) if q_count else 0.0
    return exam


def update_exam(exam_id, data, user_id):
    editable = ["examTitle", "examType", "totalMarks", "passingMarks", "durationMinutes",
                "instructions", "maximumAttempts", "shuffleQuestions", "shuffleOptions",
                "negativeMarking", "negativeMarksPerQuestion", "examStatus", "isActive"]
    fields, params = [], []
    for col in editable:
        if col in data:
            fields.append(f"{col} = %s")
            params.append(data[col])
    if not fields:
        return 0
    fields.append("updatedBy = %s")
    params.append(user_id)
    params.append(exam_id)
    _, rowcount = execute(f"UPDATE Exam SET {', '.join(fields)} WHERE examId = %s", params)
    return rowcount


def delete_exam(exam_id):
    _, rowcount = execute("UPDATE Exam SET isActive = FALSE, examStatus = 'CANCELLED' WHERE examId = %s", (exam_id,))
    return rowcount


def save_exam_schedule(exam_id, data):
    existing = fetch_one("SELECT scheduleId FROM ExamSchedule WHERE examId = %s", (exam_id,))
    if existing:
        execute(
            """UPDATE ExamSchedule
               SET startTime = %s, endTime = %s, registrationStart = %s,
                   registrationEnd = %s, lateEntryMinutes = %s, autoSubmit = %s
               WHERE examId = %s""",
            (data["startTime"], data["endTime"], data.get("registrationStart"),
             data.get("registrationEnd"), data.get("lateEntryMinutes", 0),
             data.get("autoSubmit", True), exam_id),
        )
        schedule_id = existing["scheduleId"]
    else:
        schedule_id, _ = execute(
            """INSERT INTO ExamSchedule (examId, startTime, endTime, registrationStart,
                                          registrationEnd, lateEntryMinutes, autoSubmit)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (exam_id, data["startTime"], data["endTime"], data.get("registrationStart"),
             data.get("registrationEnd"), data.get("lateEntryMinutes", 0),
             data.get("autoSubmit", True)),
        )

    execute("UPDATE Exam SET examStatus = 'SCHEDULED' WHERE examId = %s", (exam_id,))
    return schedule_id


def get_exam_schedule(exam_id):
    return fetch_one("SELECT * FROM ExamSchedule WHERE examId = %s", (exam_id,))


def assign_question_to_exam(exam_id, data):
    q_order = data.get("questionOrder")
    if not q_order:
        last_order = fetch_one("SELECT MAX(questionOrder) AS maxOrder FROM ExamQuestion WHERE examId = %s", (exam_id,))
        q_order = (last_order["maxOrder"] or 0) + 1 if last_order else 1

    exam_question_id, _ = execute(
        """INSERT INTO ExamQuestion (examId, questionId, questionOrder, marks,
                                      negativeMarks, isMandatory)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (exam_id, data["questionId"], q_order, data["marks"],
         data.get("negativeMarks", 0.00), data.get("isMandatory", True)),
    )
    return exam_question_id


def remove_question_from_exam(exam_id, question_id):
    _, rowcount = execute(
        "DELETE FROM ExamQuestion WHERE examId = %s AND questionId = %s",
        (exam_id, question_id),
    )
    return rowcount


def list_exam_questions(exam_id, is_staff):
    rows = fetch_all(
        """SELECT eq.examQuestionId, eq.questionOrder, eq.marks, eq.negativeMarks,
                  eq.isMandatory, q.questionId, q.questionType, q.questionText
           FROM ExamQuestion eq
           JOIN Question q ON q.questionId = eq.questionId
           WHERE eq.examId = %s
           ORDER BY eq.questionOrder""",
        (exam_id,),
    )
    for row in rows:
        if is_staff:
            row["options"] = fetch_all(
                "SELECT optionId, optionText, optionOrder, isCorrect FROM QuestionOption "
                "WHERE questionId = %s ORDER BY optionOrder",
                (row["questionId"],),
            )
        else:
            row.pop("correctAnswer", None)
            row.pop("modelAnswer", None)
            row.pop("explanation", None)
            options = fetch_all(
                "SELECT optionId, optionText, optionOrder FROM QuestionOption "
                "WHERE questionId = %s ORDER BY optionOrder",
                (row["questionId"],),
            )
            for opt in options:
                opt.pop("isCorrect", None)
            row["options"] = options
    return rows


def register_student_for_exam(exam_id, user_id):
    existing = fetch_one(
        "SELECT registrationId FROM CandidateRegistration WHERE examId = %s AND userId = %s",
        (exam_id, user_id),
    )
    if existing:
        return None, "Already registered for this exam"

    registration_id, _ = execute(
        """INSERT INTO CandidateRegistration (examId, userId, eligibilityVerified)
           VALUES (%s, %s, TRUE)""",
        (exam_id, user_id),
    )
    return registration_id, None


def list_exam_registrations(exam_id):
    return fetch_all(
        """SELECT cr.*, cr.registrationTime AS registeredAt, u.firstName, u.lastName, u.email, u.phone
           FROM CandidateRegistration cr
           JOIN User u ON u.userId = cr.userId
           WHERE cr.examId = %s
           ORDER BY cr.registrationTime DESC""",
        (exam_id,),
    )


def list_student_registrations(user_id):
    return fetch_all(
        """SELECT cr.*, cr.registrationTime AS registeredAt, e.examTitle, e.examCode, e.durationMinutes, e.totalMarks,
                  es.startTime, es.endTime
           FROM CandidateRegistration cr
           JOIN Exam e ON e.examId = cr.examId
           LEFT JOIN ExamSchedule es ON es.examId = e.examId
           WHERE cr.userId = %s
           ORDER BY cr.registrationTime DESC""",
        (user_id,),
    )
