import urllib.request
import json
import sys
import time

def run_test2():
    print("==================================================")
    print("TEST 2 — Comprehensive Regression Testing")
    print("==================================================")
    base_api = "http://127.0.0.1:8000/api"

    # 1. Authenticate users
    # Admin (userId: 1)
    admin_login = json.dumps({"email": "admin@platform.com", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/auth/login", data=admin_login, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        admin_data = json.loads(res.read().decode("utf-8"))
        admin_token = admin_data["accessToken"]
        print("  [OK] Admin logged in successfully.")

    # Faculty (userId: 2)
    fac_login = json.dumps({"email": "rajesh.sharma@college.edu", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/auth/login", data=fac_login, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        fac_data = json.loads(res.read().decode("utf-8"))
        fac_token = fac_data["accessToken"]
        print("  [OK] Faculty logged in successfully.")

    # Student (userId: 3)
    stud_login = json.dumps({"email": "rutuja.student@college.edu", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/auth/login", data=stud_login, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        stud_data = json.loads(res.read().decode("utf-8"))
        stud_token = stud_data["accessToken"]
        stud_user = stud_data["user"]
        print("  [OK] Student logged in successfully.")

    admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    fac_headers = {"Authorization": f"Bearer {fac_token}", "Content-Type": "application/json"}
    stud_headers = {"Authorization": f"Bearer {stud_token}", "Content-Type": "application/json"}

    # 2. Check Student Dashboard
    print("\n--- 2.1 Student Dashboard ---")
    req = urllib.request.Request(f"{base_api}/student/dashboard", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        dash = json.loads(res.read().decode("utf-8"))
        print(f"  Total registered: {dash.get('totalRegistered')}, Completed: {dash.get('completedExams')}, Pending: {dash.get('pendingExams')}")
        print(f"  Recent results count: {len(dash.get('recentResults', []))}")
        print("  [OK] Student dashboard works.")

    # 3. Check Available Exams
    print("\n--- 2.2 Available Exams ---")
    req = urllib.request.Request(f"{base_api}/students/available-exams", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        avail = json.loads(res.read().decode("utf-8"))
        print(f"  Available exams count: {len(avail)}")
        assert len(avail) > 0
        print("  [OK] Available exams works.")

    # 4. Check Registered Exams
    print("\n--- 2.3 Registered Exams ---")
    req = urllib.request.Request(f"{base_api}/students/3/registrations", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        regs = json.loads(res.read().decode("utf-8"))
        print(f"  Registered exams count: {len(regs)}")
        assert len(regs) > 0
        print("  [OK] Registered exams works.")

    # 5. Check Faculty Dashboard
    print("\n--- 2.4 Faculty Dashboard ---")
    req = urllib.request.Request(f"{base_api}/faculty/dashboard", headers=fac_headers)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        fac_dash = json.loads(res.read().decode("utf-8"))
        print(f"  Stats: Total Exams={fac_dash.get('totalExams')}, Active Exams={fac_dash.get('activeExams')}, Pending Evaluations={fac_dash.get('pendingEvaluations')}")
        print("  [OK] Faculty dashboard works.")

    # 6. Check Admin Dashboard
    print("\n--- 2.5 Admin Dashboard ---")
    req = urllib.request.Request(f"{base_api}/admin/dashboard", headers=admin_headers)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        adm_dash = json.loads(res.read().decode("utf-8"))
        print(f"  Stats: Total Users={adm_dash.get('totalUsers')}, Total Exams={adm_dash.get('totalExams')}, Total Attempts={adm_dash.get('totalAttempts')}")
        print("  [OK] Admin dashboard works.")

    # 7. Check Exam Runtime, Timer, Autosave, Security Warnings & 3-Violation Auto-Submit
    print("\n--- 2.6 Exam Runtime: Create Dedicated Verification Exam ---")
    # Faculty creates a test exam specifically for runtime testing
    create_exam_payload = json.dumps({
        "subjectId": 1,
        "examCode": f"REG-TEST-{int(time.time())}",
        "examTitle": "Regression Verification Exam",
        "examType": "OBJECTIVE",
        "durationMinutes": 30,
        "totalMarks": 50.0,
        "passingMarks": 20.0,
        "instructions": "E2E Runtime Test Exam"
    }).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/exams", data=create_exam_payload, headers=fac_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        created_exam = json.loads(res.read().decode("utf-8"))
        runtime_exam_id = created_exam["examId"]
        print(f"  Created test exam #{runtime_exam_id} ({created_exam.get('examCode')})")

    # Add schedule for test exam
    sched_payload = json.dumps({
        "startTime": "2026-01-01 00:00:00",
        "endTime": "2027-12-31 23:59:59",
        "registrationStart": "2026-01-01 00:00:00",
        "registrationEnd": "2027-12-31 23:59:59",
        "lateEntryMinutes": 15,
        "autoSubmit": True
    }).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/exams/{runtime_exam_id}/schedule", data=sched_payload, headers=fac_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        print("  Scheduled test exam.")

    # Add Question 1 to exam
    add_q_payload = json.dumps({"questionId": 1, "questionOrder": 1, "marks": 50.0, "negativeMarks": 0.0}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/exams/{runtime_exam_id}/questions", data=add_q_payload, headers=fac_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        print("  Added Question #1 to exam.")

    # Student registers for exam
    req = urllib.request.Request(f"{base_api}/exams/{runtime_exam_id}/register", data=b"{}", headers=stud_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        reg_res = json.loads(res.read().decode("utf-8"))
        print(f"  Student registered (regId={reg_res['registrationId']}).")

    # Student starts attempt
    start_payload = json.dumps({"deviceInfo": "Test Browser", "browserInfo": "Python E2E Client"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/exams/{runtime_exam_id}/attempts/start", data=start_payload, headers=stud_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        att_data = json.loads(res.read().decode("utf-8"))
        test_attempt_id = att_data["attemptId"]
        print(f"  Attempt started: attemptId={test_attempt_id}, attemptNumber={att_data.get('attemptNumber')}")
        assert test_attempt_id > 0

    # Verify attempt state & timer
    print("\n--- 2.7 Timer & Attempt State ---")
    req = urllib.request.Request(f"{base_api}/attempts/{test_attempt_id}", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        att_info = json.loads(res.read().decode("utf-8"))
        print(f"  Attempt status: {att_info.get('status')}, startTime: {att_info.get('startTime')}, durationMinutes: {att_info.get('durationMinutes')}")
        assert att_info.get("status") == "IN_PROGRESS"
        print("  [OK] Timer & attempt state verified.")

    # Autosave answer
    print("\n--- 2.8 Answer Autosave ---")
    save_payload = json.dumps({
        "questionId": 1,
        "selectedOptionId": 1,
        "answerText": None,
        "isMarkedForReview": False,
        "timeSpentSeconds": 15
    }).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/attempts/{test_attempt_id}/answers", data=save_payload, headers=stud_headers, method="POST")
    with urllib.request.urlopen(req) as res:
        save_res = json.loads(res.read().decode("utf-8"))
        print(f"  Autosave response (HTTP {res.status}): {save_res.get('message')}")
        assert res.status in (200, 201)

    # Verify answer saved
    req = urllib.request.Request(f"{base_api}/attempts/{test_attempt_id}/answers", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        answers = json.loads(res.read().decode("utf-8"))
        assert len(answers) == 1
        assert answers[0]["selectedOptionId"] == 1
        print(f"  Verified saved answer in DB: questionId={answers[0]['questionId']}, selectedOptionId={answers[0]['selectedOptionId']}")
        print("  [OK] Answer autosave works.")

    # Security monitoring: normal actions should NOT create violations
    print("\n--- 2.9 Normal Actions Check (No Violations) ---")
    req = urllib.request.Request(f"{base_api}/attempts/{test_attempt_id}", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        info = json.loads(res.read().decode("utf-8"))
        assert info.get("violationCount", 0) == 0
        print(f"  Current violationCount: {info.get('violationCount', 0)}")
        print("  [OK] Normal navigation, answer saving, and polling create 0 violations.")

    # Security monitoring: Tab switch violations
    print("\n--- 2.10 Tab-Switch Security Warnings & Auto-Submit on 3 Violations ---")
    for v_num in range(1, 4):
        time.sleep(2)  # Respect the 1.5s debounce threshold
        event_payload = json.dumps({
            "eventType": "TAB_SWITCH",
            "eventDetails": f"Tab switch #{v_num} simulation"
        }).encode("utf-8")
        req = urllib.request.Request(f"{base_api}/attempts/{test_attempt_id}/security-event", data=event_payload, headers=stud_headers, method="POST")
        with urllib.request.urlopen(req) as res:
            ev_res = json.loads(res.read().decode("utf-8"))
            print(f"  Tab switch event #{v_num} response: violationCount={ev_res.get('violationCount')}, autoSubmitTriggered={ev_res.get('autoSubmitTriggered')}, message='{ev_res.get('message')}'")

            if v_num < 3:
                assert ev_res.get("violationCount") == v_num
                assert ev_res.get("autoSubmitTriggered") is False
                assert "Warning" in ev_res.get("message", "")
                print(f"    [OK] Violation #{v_num} issued warning without auto-submit.")
            else:
                assert ev_res.get("violationCount") >= 3
                assert ev_res.get("autoSubmitTriggered") is True
                print("    [OK] Violation #3 successfully triggered auto-submit!")

    # Verify attempt status is now AUTO_SUBMITTED
    req = urllib.request.Request(f"{base_api}/attempts/{test_attempt_id}", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        final_att = json.loads(res.read().decode("utf-8"))
        print(f"\n  Final Attempt Status: {final_att.get('status')}, submissionReason: {final_att.get('submissionReason')}, violationCount: {final_att.get('violationCount')}")
        assert final_att.get("status") == "AUTO_SUBMITTED"
        assert final_att.get("submissionReason") == "AUTO_SUBMITTED_TAB_SWITCH_LIMIT"
        print("  [OK] 3-violation auto-submit fully verified.")

    # 8. Check Multi-Tab Session Isolation
    print("\n--- 2.11 Multi-Tab Authentication Isolation ---")
    # Verify that admin token authenticates as Admin, faculty token as Faculty, and student as Student
    req = urllib.request.Request(f"{base_api}/auth/me", headers=admin_headers)
    with urllib.request.urlopen(req) as res:
        adm_me = json.loads(res.read().decode("utf-8"))
        assert adm_me["roleName"] == "Admin"
        print(f"  Tab 1 (Admin Session): user='{adm_me['email']}', role='{adm_me['roleName']}'")

    req = urllib.request.Request(f"{base_api}/auth/me", headers=fac_headers)
    with urllib.request.urlopen(req) as res:
        fac_me = json.loads(res.read().decode("utf-8"))
        assert fac_me["roleName"] == "Faculty"
        print(f"  Tab 2 (Faculty Session): user='{fac_me['email']}', role='{fac_me['roleName']}'")

    req = urllib.request.Request(f"{base_api}/auth/me", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        stud_me = json.loads(res.read().decode("utf-8"))
        assert stud_me["roleName"] == "Student"
        print(f"  Tab 3 (Student Session): user='{stud_me['email']}', role='{stud_me['roleName']}'")

    print("  [OK] Admin, Faculty, and Student sessions are completely isolated and independent.")

    print("\n>>> TEST 2: ALL REGRESSION CHECKS PASSED <<<")
    return True

if __name__ == "__main__":
    success = run_test2()
    sys.exit(0 if success else 1)
