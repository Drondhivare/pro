import urllib.request
import json
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "backend")
from backend.database import fetch_one, fetch_all

def run_test1():
    print("==================================================")
    print("TEST 1 — Faculty Evaluation -> Student Results")
    print("==================================================")

    # 1. Verify servers
    base_api = "http://127.0.0.1:8000/api"

    # 2. Login as Faculty
    print("\nStep 1: Logging in as Faculty (rajesh.sharma@college.edu)...")
    payload = json.dumps({"email": "rajesh.sharma@college.edu", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/auth/login", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode("utf-8"))
        faculty_token = data["accessToken"]
        faculty_user = data["user"]
        print(f"  Logged in successfully as {faculty_user['firstName']} {faculty_user['lastName']} (role={faculty_user.get('role')})")

    faculty_headers = {
        "Authorization": f"Bearer {faculty_token}",
        "Content-Type": "application/json"
    }

    # 3. Open Faculty -> Pending Evaluation
    print("\nStep 2: Fetching Faculty Pending Evaluations (/api/evaluations/pending)...")
    req = urllib.request.Request(f"{base_api}/evaluations/pending", headers=faculty_headers)
    with urllib.request.urlopen(req) as res:
        pending = json.loads(res.read().decode("utf-8"))
        print(f"  Found {len(pending)} pending evaluations in queue.")

    # 4. Identify an existing AUTO_EVALUATED exam that currently has no Result row and is NOT examId=1
    target_eval = None
    for item in pending:
        if item.get("examId") != 1 and item.get("evaluationStatus") == "AUTO_EVALUATED":
            # Check if result row already exists
            existing_res = fetch_one("SELECT resultId FROM Result WHERE evaluationId = %s", (item["evaluationId"],))
            if not existing_res:
                target_eval = item
                break

    if not target_eval:
        print("FAIL: No suitable pending evaluation found!")
        return False

    # 5. Open that evaluation and record details
    exam_id = target_eval["examId"]
    attempt_id = target_eval["attemptId"]
    evaluation_id = target_eval["evaluationId"]
    marks_obtained = float(target_eval["totalMarksObtained"] or 0)
    total_marks = float(target_eval["totalMarks"] or 0)
    passing_marks = float(target_eval["passingMarks"] or 0)

    print(f"\nStep 3: Recorded Target Evaluation:")
    print(f"  Exam Title:     {target_eval.get('examTitle')} ({target_eval.get('examCode')})")
    print(f"  Exam ID:        {exam_id}")
    print(f"  Attempt ID:     {attempt_id}")
    print(f"  Evaluation ID:  {evaluation_id}")
    print(f"  Marks Obtained: {marks_obtained}")
    print(f"  Total Marks:    {total_marks}")
    print(f"  Passing Marks:  {passing_marks}")
    print(f"  Before Result:  None (verified no row in Result table)")

    # 6. Finalize evaluation through normal faculty flow
    print(f"\nStep 4: Finalizing Evaluation #{evaluation_id} (POST /api/evaluations/{evaluation_id}/finalize)...")
    req = urllib.request.Request(f"{base_api}/evaluations/{evaluation_id}/finalize", data=b"{}", headers=faculty_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        fin_data = json.loads(res.read().decode("utf-8"))
        print(f"  Finalize response: {fin_data}")
        result_id = fin_data["resultId"]

    # 7. Verify backend/database immediately after finalize
    print(f"\nStep 5: Verifying Database immediately after Finalize (before publish)...")
    db_res = fetch_one("SELECT * FROM Result WHERE resultId = %s", (result_id,))
    print(f"  DB Result record: {db_res}")
    expected_pct = round((marks_obtained / total_marks) * 100, 2)
    expected_pass = marks_obtained >= passing_marks
    expected_grade = "A+" if expected_pct >= 90 else "A" if expected_pct >= 80 else "B" if expected_pct >= 70 else "C" if expected_pct >= 60 else "D" if expected_pct >= 50 else "F"

    assert float(db_res["percentage"]) == expected_pct, f"Expected percentage {expected_pct}, got {db_res['percentage']}"
    assert db_res["grade"] == expected_grade, f"Expected grade {expected_grade}, got {db_res['grade']}"
    assert db_res["passStatus"] == (1 if expected_pass else 0), f"Expected passStatus {expected_pass}, got {db_res['passStatus']}"
    assert db_res["isPublished"] == 0, f"Expected isPublished=0 before publish, got {db_res['isPublished']}"
    print(f"  [OK] Percentage ({db_res['percentage']}%), Grade ({db_res['grade']}), PassStatus ({db_res['passStatus']}), isPublished ({db_res['isPublished']}) match expected finalize behavior.")

    # Publish result (matching evaluate.html finalizeAndPublish button)
    print(f"\nStep 6: Publishing Result #{result_id} (POST /api/results/{result_id}/publish)...")
    req = urllib.request.Request(f"{base_api}/results/{result_id}/publish", data=b"{}", headers=faculty_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        pub_data = json.loads(res.read().decode("utf-8"))
        print(f"  Publish response: {pub_data}")

    db_res_pub = fetch_one("SELECT * FROM Result WHERE resultId = %s", (result_id,))
    assert db_res_pub["isPublished"] == 1, f"Expected isPublished=1 after publish, got {db_res_pub['isPublished']}"
    print(f"  [OK] Result is now published: isPublished = {db_res_pub['isPublished']}, publishedAt = {db_res_pub['publishedAt']}")

    # 8. Login as Student
    print("\nStep 7: Logging in as Student (rutuja.student@college.edu)...")
    payload = json.dumps({"email": "rutuja.student@college.edu", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/auth/login", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode("utf-8"))
        student_token = data["accessToken"]
        student_user = data["user"]
        print(f"  Logged in successfully as {student_user['firstName']} {student_user['lastName']} (role={student_user.get('role')})")

    student_headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }

    # 9. Open My Results
    print("\nStep 8: Fetching Student Results (/api/students/3/results)...")
    req = urllib.request.Request(f"{base_api}/students/3/results", headers=student_headers)
    with urllib.request.urlopen(req) as res:
        student_results = json.loads(res.read().decode("utf-8"))
        print(f"  Found {len(student_results)} published results for student 3:")
        for r in student_results:
            print(f"    RES-{r['resultId']} | Exam {r['examId']}: '{r['examTitle']}' | Marks: {r['totalMarksObtained']}/{r['totalMarks']} | Pct: {r['percentage']}% | Grade: {r['grade']} | Pass: {r['passStatus']}")

    # 10. Verify finalized exam appears with exact values
    finalized_item = next((r for r in student_results if r["examId"] == exam_id), None)
    assert finalized_item is not None, f"Finalized exam {exam_id} not found in student results!"
    print(f"\nStep 9: Verifying newly finalized exam #{exam_id} in Student My Results:")
    print(f"  Obtained Marks: {finalized_item['totalMarksObtained']} (Expected {marks_obtained})")
    print(f"  Total Marks:    {finalized_item['totalMarks']} (Expected {total_marks})")
    print(f"  Percentage:     {finalized_item['percentage']}% (Expected {expected_pct}%)")
    print(f"  Grade:          {finalized_item['grade']} (Expected {expected_grade})")
    print(f"  Pass/Fail:      {finalized_item['passStatus']} (Expected {1 if expected_pass else 0})")
    assert float(finalized_item["totalMarksObtained"]) == marks_obtained
    assert float(finalized_item["totalMarks"]) == total_marks
    assert float(finalized_item["percentage"]) == expected_pct
    assert finalized_item["grade"] == expected_grade
    assert finalized_item["passStatus"] == (1 if expected_pass else 0)
    print("  [OK] Finalized exam verified successfully in My Results!")

    # 11. Verify examId=1 still displays 50/100, 50.00%, Grade D, PASSED
    exam1_item = next((r for r in student_results if r["examId"] == 1), None)
    assert exam1_item is not None, "Exam 1 not found in student results!"
    print(f"\nStep 10: Verifying Exam #1 still displays correctly:")
    print(f"  Obtained Marks: {exam1_item['totalMarksObtained']} (Expected 50.00)")
    print(f"  Total Marks:    {exam1_item['totalMarks']} (Expected 100.00)")
    print(f"  Percentage:     {exam1_item['percentage']}% (Expected 50.00%)")
    print(f"  Grade:          {exam1_item['grade']} (Expected D)")
    print(f"  PassStatus:     {exam1_item['passStatus']} (Expected 1)")
    assert float(exam1_item["totalMarksObtained"]) == 50.00
    assert float(exam1_item["totalMarks"]) == 100.00
    assert float(exam1_item["percentage"]) == 50.00
    assert exam1_item["grade"] == "D"
    assert exam1_item["passStatus"] == 1
    print("  [OK] Exam #1 values verified: 50/100, 50.00%, Grade D, PASSED.")

    # 12. Verify unfinalized exams do NOT appear in My Results
    published_exam_ids = {r["examId"] for r in student_results}
    print(f"\nStep 11: Checking for unfinalized exams in Student My Results:")
    print(f"  Currently published exam IDs: {published_exam_ids}")
    # Student 3 has registered exams: 1, 22, 23, 24, 27, 28, 30
    all_regs = fetch_all("SELECT examId FROM CandidateRegistration WHERE userId = 3")
    unfinalized_count = 0
    for reg in all_regs:
        eid = reg["examId"]
        if eid not in (1, exam_id):
            assert eid not in published_exam_ids, f"Unfinalized exam {eid} unexpectedly appears in My Results!"
            unfinalized_count += 1
            print(f"  [OK] Exam {eid} is unfinalized/unpublished and NOT in My Results.")

    print(f"  [OK] All {unfinalized_count} unfinalized/unpublished exams correctly excluded from My Results.")
    print("\n>>> TEST 1: ALL CHECKS PASSED <<<")
    return True

if __name__ == "__main__":
    success = run_test1()
    sys.exit(0 if success else 1)
