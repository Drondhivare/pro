import sys
import json
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, 'backend')
from database import fetch_all, fetch_one

def json_serial(obj):
    if isinstance(obj, (datetime, Decimal)):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

# 1. Find student
user = fetch_one("SELECT userId, firstName, lastName, email FROM User WHERE userId = 3")
print("Student User:", json.dumps(user, default=json_serial, indent=2))
user_id = user['userId'] if user else 3

# 2. Registrations
regs = fetch_all("""
    SELECT cr.*, e.examTitle, e.examCode, e.totalMarks as examTotalMarks, e.passingMarks, e.examStatus
    FROM CandidateRegistration cr
    JOIN Exam e ON e.examId = cr.examId
    WHERE cr.userId = %s
    ORDER BY cr.registrationId
""", (user_id,))
print(f"\n--- Candidate Registrations ({len(regs)}) ---")
print(json.dumps(regs, default=json_serial, indent=2))

# 3. Exam Attempts
attempts = fetch_all("""
    SELECT ea.*, cr.examId, e.examTitle, e.totalMarks as examTotalMarks
    FROM ExamAttempt ea
    JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
    JOIN Exam e ON e.examId = cr.examId
    WHERE cr.userId = %s
    ORDER BY ea.attemptId
""", (user_id,))
print(f"\n--- Exam Attempts ({len(attempts)}) ---")
print(json.dumps(attempts, default=json_serial, indent=2))

# 4. Evaluations & Details
evals = fetch_all("""
    SELECT ev.*, ea.attemptNumber, ea.status as attemptStatus, cr.examId, cr.userId, e.examTitle, e.totalMarks as examTotalMarks
    FROM Evaluation ev
    JOIN ExamAttempt ea ON ea.attemptId = ev.attemptId
    JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
    JOIN Exam e ON e.examId = cr.examId
    WHERE cr.userId = %s
    ORDER BY ev.evaluationId
""", (user_id,))
print(f"\n--- Evaluations ({len(evals)}) ---")
print(json.dumps(evals, default=json_serial, indent=2))

for ev in evals:
    details = fetch_all("SELECT * FROM EvaluationDetail WHERE evaluationId = %s", (ev['evaluationId'],))
    print(f"\n--- EvaluationDetail for Evaluation #{ev['evaluationId']} ({len(details)} details) ---")
    print(json.dumps(details, default=json_serial, indent=2))

# 5. Results
results = fetch_all("""
    SELECT res.*, ev.attemptId, cr.examId, cr.userId, e.examTitle, e.totalMarks as examTotalMarks
    FROM Result res
    JOIN Evaluation ev ON ev.evaluationId = res.evaluationId
    JOIN ExamAttempt ea ON ea.attemptId = ev.attemptId
    JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
    JOIN Exam e ON e.examId = cr.examId
    WHERE cr.userId = %s
    ORDER BY res.resultId
""", (user_id,))
print(f"\n--- Results ({len(results)}) ---")
print(json.dumps(results, default=json_serial, indent=2))

# 6. Check ALL Results in the database (to see if other students or exams have results)
all_results = fetch_all("""
    SELECT res.*, ev.attemptId, cr.examId, cr.userId, u.email, e.examTitle, e.totalMarks as examTotalMarks
    FROM Result res
    JOIN Evaluation ev ON ev.evaluationId = res.evaluationId
    JOIN ExamAttempt ea ON ea.attemptId = ev.attemptId
    JOIN CandidateRegistration cr ON cr.registrationId = ea.registrationId
    JOIN User u ON u.userId = cr.userId
    JOIN Exam e ON e.examId = cr.examId
    ORDER BY res.resultId
""")
print(f"\n--- ALL Results in DB ({len(all_results)}) ---")
print(json.dumps(all_results, default=json_serial, indent=2))
