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

student_id = 3

# Fetch all exams registered or attempted by student 3
query = """
    SELECT 
        e.examId,
        e.examTitle,
        e.examCode,
        e.totalMarks AS examTotalMarks,
        e.passingMarks,
        cr.registrationId,
        cr.registrationStatus,
        ea.attemptId,
        ea.attemptNumber,
        ea.status AS attemptStatus,
        ea.submittedAt,
        ev.evaluationId,
        ev.totalMarksObtained,
        ev.evaluationStatus,
        r.resultId,
        r.percentage,
        r.grade,
        r.passStatus,
        r.isPublished,
        r.publishedAt
    FROM CandidateRegistration cr
    JOIN Exam e ON e.examId = cr.examId
    LEFT JOIN ExamAttempt ea ON ea.registrationId = cr.registrationId
    LEFT JOIN Evaluation ev ON ev.attemptId = ea.attemptId
    LEFT JOIN Result r ON r.evaluationId = ev.evaluationId
    WHERE cr.userId = %s
    ORDER BY e.examId, ea.attemptId
"""

rows = fetch_all(query, (student_id,))
print(f"Total Registration/Attempt Rows for Student {student_id}: {len(rows)}\n")
for idx, row in enumerate(rows, 1):
    print(f"--- Record #{idx} ---")
    for k, v in row.items():
        print(f"  {k}: {v}")
    
    # Reason for visibility / invisibility in My Results
    # My Results queries:
    # SELECT ... FROM Result r ... WHERE cr.userId = %s AND r.isPublished = TRUE
    if not row['attemptId']:
        reason = "NOT VISIBLE: Exam was registered, but never attempted (no attempt record)."
    elif row['attemptStatus'] == 'IN_PROGRESS':
        reason = "NOT VISIBLE: Exam attempt is still IN_PROGRESS (not submitted)."
    elif not row['evaluationId']:
        reason = "NOT VISIBLE: Attempt was submitted, but has not been evaluated (no evaluation record)."
    elif not row['resultId']:
        reason = f"NOT VISIBLE: Attempt was evaluated (Evaluation #{row['evaluationId']}, status={row['evaluationStatus']}), but Result was never finalized (no Result record in Result table)."
    elif not row['isPublished']:
        reason = f"NOT VISIBLE: Result #{row['resultId']} exists (score={row['totalMarksObtained']}/{row['examTotalMarks']}, {row['percentage']}%), but is NOT PUBLISHED (isPublished=0/False)."
    else:
        reason = f"VISIBLE in My Results (Result #{row['resultId']}, isPublished=True, publishedAt={row['publishedAt']})."
    
    print(f"  >> Visibility in My Results: {reason}\n")

