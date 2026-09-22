import requests
import json
import time

BASE_API = "http://127.0.0.1:8000/api"
BASE_WEB = "http://127.0.0.1:5000"

results = []

def check(name, condition, msg=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, msg))
    print(f"[{status}] {name}: {msg}")
    return condition

def run_e2e():
    print("\n=== MMCOE EXAMINATION PLATFORM - COMPREHENSIVE E2E VERIFICATION ===")

    # 1. Health checks
    r = requests.get("http://127.0.0.1:8000/health")
    check("1. Backend Health", r.status_code == 200 and r.json().get("status") == "ok")

    r = requests.get(f"{BASE_WEB}/")
    check("2. Frontend Login Page", r.status_code == 200 and "MMCOE" in r.text)

    # 3. Student Login
    s = requests.Session()
    r = s.post(f"{BASE_API}/auth/login", json={"email": "rutuja.student@college.edu", "password": "password123"})
    check("3. Student Auth", r.status_code == 200)
    student_token = r.json()["accessToken"]
    st_headers = {"Authorization": f"Bearer {student_token}"}

    # 4. Faculty Login
    f = requests.Session()
    r = f.post(f"{BASE_API}/auth/login", json={"email": "rajesh.sharma@college.edu", "password": "password123"})
    check("4. Faculty Auth", r.status_code == 200)
    fac_token = r.json()["accessToken"]
    fac_headers = {"Authorization": f"Bearer {fac_token}"}

    # 5. Admin Login
    a = requests.Session()
    r = a.post(f"{BASE_API}/auth/login", json={"email": "admin@platform.com", "password": "password123"})
    check("5. Admin Auth", r.status_code == 200)

    # 6. Check Exam 28 Configuration
    r = s.get(f"{BASE_API}/exams/28", headers=st_headers)
    check("6. Exam 28 Exists & Active", r.status_code == 200 and r.json().get("examTitle") == "UT")

    # 7. Check Exam 28 Assigned Questions
    r = s.get(f"{BASE_API}/exams/28/questions", headers=st_headers)
    q_list = r.json()
    check("7. Exam 28 Questions Assigned", r.status_code == 200 and len(q_list) == 2, f"Count={len(q_list)}")

    # 8. Check Attempt 25
    r = s.get(f"{BASE_API}/attempts/25", headers=st_headers)
    att = r.json()
    check("8. Attempt 25 Active", r.status_code == 200 and att.get("status") == "IN_PROGRESS", f"Status={att.get('status')}")

    # 9. Check Attempt 25 Answer Autosave
    r = s.get(f"{BASE_API}/attempts/25/answers", headers=st_headers)
    answers = r.json()
    check("9. Answers Autosaved in Attempt 25", r.status_code == 200 and len(answers) >= 1, f"Count={len(answers)}")

    # 10. Check Attempt 25 Security Violations (authoritative in DB)
    check("10. Violation Count Authoritative in DB", att.get("violationCount") == 2, f"violationCount={att.get('violationCount')}")

    # 11. Test Security Event Backend Authorization & Rate Limiting
    # Send another security event to verify backend debounce or handling
    r = s.post(f"{BASE_API}/attempts/25/security-event", headers=st_headers, json={"eventType": "TAB_SWITCH", "details": "Test verify"})
    # It might be debounced if < 1.5s or trigger auto-submit if count reaches 3
    # We already verified count=2 in the live test
    check("11. Security Event Endpoint Responsive", r.status_code in (200, 429), f"Status={r.status_code}")

    # 12. Check exam_engine.js file integrity
    with open("frontend/static/js/exam_engine.js", "r", encoding="utf-8") as file:
        content = file.read()
    check("12. Timer unconditionally initialized before question check",
          content.find("startExamTimerSeconds") < content.find("questionsList = await apiFetch") or
          content.find("startExamTimerSeconds") < content.find("questionsList.length === 0"))
    check("13. Security monitor unconditionally initialized before question check",
          content.find("initializeSecurityMonitor()") < content.find("questionsList = await apiFetch") or
          content.find("initializeSecurityMonitor()") < content.find("questionsList.length === 0"))
    check("14. Finish & Review disabled/hidden for 0 questions", "btnReview.classList.add('disabled', 'd-none')" in content)
    check("15. Clean GMT stripping present in startExamTimerSeconds", "replace(/\\s+GMT$/i, '')" in content)

    # 13. Summary
    passed_count = sum(1 for _, st, _ in results if st == "PASS")
    total_count = len(results)
    print(f"\n=======================================================")
    print(f"VERIFICATION SUMMARY: {passed_count}/{total_count} CHECKS PASSED")
    print(f"=======================================================\n")
    assert passed_count == total_count

if __name__ == "__main__":
    run_e2e()
