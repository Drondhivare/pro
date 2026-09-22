import sys
sys.path.insert(0, ".")
sys.path.insert(0, "backend")
from backend.database import fetch_all, fetch_one
import json

student_id = 3
regs = fetch_all('''
    SELECT cr.registrationId, cr.examId, cr.registrationStatus,
           e.examTitle, e.examCode, e.totalMarks, e.passingMarks, e.examStatus
    FROM CandidateRegistration cr
    JOIN Exam e ON e.examId = cr.examId
    WHERE cr.userId = %s
    ORDER BY cr.registrationId
''', (student_id,))

print(f"Total exams registered for student {student_id}: {len(regs)}\n")

for reg in regs:
    att = fetch_one('SELECT * FROM ExamAttempt WHERE registrationId = %s ORDER BY attemptId DESC LIMIT 1', (reg['registrationId'],))
    ev = fetch_one('SELECT * FROM Evaluation WHERE attemptId = %s', (att['attemptId'],)) if att else None
    res = fetch_one('SELECT * FROM Result WHERE evaluationId = %s', (ev['evaluationId'],)) if ev else None
    
    print(f"Exam ID: {reg['examId']}")
    print(f"  Exam Title: {reg['examTitle']} ({reg['examCode']})")
    print(f"  Registration Status: {reg['registrationStatus']} (Reg ID: {reg['registrationId']})")
    print(f"  Attempt Status: {att['status'] if att else 'No Attempt'} (Attempt ID: {att['attemptId'] if att else None})")
    print(f"  Total Marks: {reg['totalMarks']}")
    print(f"  Obtained Marks: {ev['totalMarksObtained'] if ev else 'Not Evaluated'}")
    print(f"  Evaluation Status: {ev['evaluationStatus'] if ev else 'None'} (Eval ID: {ev['evaluationId'] if ev else None})")
    print(f"  Result Existence: {'YES (Result ID: ' + str(res['resultId']) + ')' if res else 'NO (No record in Result table)'}")
    print(f"  Result Publication Status: {('PUBLISHED (isPublished = ' + str(res['isPublished']) + ')') if res else 'NOT_APPLICABLE'}")
    if res and res.get('isPublished'):
        print(f"  Reason in My Results: VISIBLE - A Result record exists and isPublished is TRUE.")
    elif res and not res.get('isPublished'):
        print(f"  Reason in My Results: NOT VISIBLE - Result record exists but isPublished is FALSE.")
    else:
        print(f"  Reason in My Results: NOT VISIBLE - No record in Result table. The evaluation has not been finalized (POST /api/evaluations/<id>/finalize) and published.")
    print("-" * 50)
