"""Business logic for publishing results and compiling exam analytics reports."""
from database import fetch_all, fetch_one, execute, log_audit


def publish_single_result(result_id: int, published_by: int | str):
    """Publish a single exam result and notify candidate."""
    result = fetch_one(
        """SELECT r.*, e.examTitle, cr.userId, ev.totalMarksObtained, e.totalMarks
           FROM Result r
           JOIN Evaluation ev ON ev.evaluationId = r.evaluationId
           JOIN ExamAttempt att ON att.attemptId = ev.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
           JOIN Exam e ON e.examId = cr.examId
           WHERE r.resultId = %s""",
        (result_id,)
    )
    if not result:
        return None, "Result not found", 404

    execute(
        """UPDATE Result SET isPublished = TRUE, publishedAt = NOW(), publishedBy = %s
           WHERE resultId = %s""",
        (published_by, result_id),
    )

    execute(
        """INSERT INTO Notification (userId, title, message, notificationType, priority)
           VALUES (%s, %s, %s, 'RESULT', 'HIGH')""",
        (result["userId"],
         f"Exam Result Published: {result['examTitle']}",
         f"Your result for '{result['examTitle']}' has been released. Score: {result['totalMarksObtained']}/{result['totalMarks']} ({result['percentage']}%, Grade: {result['grade']}).")
    )

    log_audit(published_by, "Result", result_id, "PUBLISH", "Unpublished", "Published")
    return {"message": "Result published and student notified"}, None, 200


def publish_all_exam_results(exam_id: int, published_by: int | str):
    """Bulk publish all finalized results for an exam and notify students."""
    unpublished = fetch_all(
        """SELECT r.resultId, r.percentage, r.grade, e.examTitle, cr.userId, ev.totalMarksObtained, e.totalMarks
           FROM Result r
           JOIN Evaluation ev ON ev.evaluationId = r.evaluationId
           JOIN ExamAttempt att ON att.attemptId = ev.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
           JOIN Exam e ON e.examId = cr.examId
           WHERE e.examId = %s AND r.isPublished = FALSE""",
        (exam_id,)
    )

    for item in unpublished:
        execute(
            "UPDATE Result SET isPublished = TRUE, publishedAt = NOW(), publishedBy = %s WHERE resultId = %s",
            (published_by, item["resultId"]),
        )
        execute(
            """INSERT INTO Notification (userId, title, message, notificationType, priority)
               VALUES (%s, %s, %s, 'RESULT', 'HIGH')""",
            (item["userId"],
             f"Exam Result Published: {item['examTitle']}",
             f"Your result for '{item['examTitle']}' is ready. Score: {item['totalMarksObtained']}/{item['totalMarks']} ({item['percentage']}%, Grade: {item['grade']}).")
        )

    log_audit(published_by, "Exam", exam_id, "PUBLISH_RESULTS", None, f"Published {len(unpublished)} results")
    return {"message": f"Published {len(unpublished)} results successfully", "count": len(unpublished)}, None, 200


def generate_exam_report(exam_id: int):
    """Compile performance metrics and grade distributions for an exam."""
    exam = fetch_one("SELECT * FROM Exam WHERE examId = %s", (exam_id,))
    if not exam:
        return None, "Exam not found", 404

    registered_count = fetch_one("SELECT COUNT(*) AS c FROM CandidateRegistration WHERE examId = %s", (exam_id,))["c"]
    attempts_count = fetch_one(
        "SELECT COUNT(*) AS c FROM ExamAttempt ea JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId WHERE cr.examId = %s",
        (exam_id,)
    )["c"]

    results = fetch_all(
        """SELECT r.percentage, r.grade, r.passStatus, ev.totalMarksObtained
           FROM Result r
           JOIN Evaluation ev ON ev.evaluationId = r.evaluationId
           JOIN ExamAttempt att ON att.attemptId = ev.attemptId
           JOIN CandidateRegistration cr ON cr.registrationId = att.registrationId
           WHERE cr.examId = %s""",
        (exam_id,)
    )

    evaluated_count = len(results)
    passed_count = sum(1 for r in results if r["passStatus"])
    failed_count = evaluated_count - passed_count
    pass_percentage = round((passed_count / evaluated_count) * 100, 2) if evaluated_count > 0 else 0.0

    scores = [float(r["totalMarksObtained"]) for r in results if r["totalMarksObtained"] is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    highest_score = max(scores) if scores else 0.0
    lowest_score = min(scores) if scores else 0.0

    grade_distribution = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for r in results:
        g = r.get("grade")
        if g in grade_distribution:
            grade_distribution[g] += 1

    report = {
        "examId": exam_id,
        "examTitle": exam["examTitle"],
        "examCode": exam["examCode"],
        "totalMarks": float(exam["totalMarks"]),
        "passingMarks": float(exam["passingMarks"]),
        "registeredCandidates": registered_count,
        "totalAttempts": attempts_count,
        "evaluatedCount": evaluated_count,
        "passedCount": passed_count,
        "failedCount": failed_count,
        "passPercentage": pass_percentage,
        "averageScore": avg_score,
        "highestScore": highest_score,
        "lowestScore": lowest_score,
        "gradeDistribution": grade_distribution,
    }
    return report, None, 200
