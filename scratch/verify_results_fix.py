import sys
sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.database import fetch_all, fetch_one
from backend.app import create_app
from flask_jwt_extended import create_access_token
from backend.endpoint import calculate_grade_and_pass
import json

def test_all():
    print("=== 1. TEST GRADING LOGIC HELPER ===")
    test_cases = [
        (50.0, 100.0, 40.0, 50.0, "D", True),
        (100.0, 100.0, 40.0, 100.0, "A+", True),
        (85.0, 100.0, 40.0, 85.0, "A", True),
        (75.0, 100.0, 40.0, 75.0, "B", True),
        (65.0, 100.0, 40.0, 65.0, "C", True),
        (39.0, 100.0, 40.0, 39.0, "F", False),
        (0.0, 50.0, 20.0, 0.0, "F", False),
        (50.0, 50.0, 20.0, 100.0, "A+", True),
    ]
    for obtained, total, pass_m, exp_pct, exp_grd, exp_pass in test_cases:
        pct, grd, p_stat = calculate_grade_and_pass(obtained, total, pass_m)
        assert pct == exp_pct, f"Expected pct {exp_pct}, got {pct}"
        assert grd == exp_grd, f"Expected grade {exp_grd}, got {grd}"
        assert p_stat == exp_pass, f"Expected pass {exp_pass}, got {p_stat}"
    print("[OK] Grading logic helper passed all test cases.")

    print("\n=== 2. DATABASE INTEGRITY CHECK ===")
    res_rows = fetch_all("SELECT * FROM Result")
    print(f"Total Result rows in DB: {len(res_rows)}")
    assert len(res_rows) == 1, f"Expected exactly 1 Result row, found {len(res_rows)}"
    r1 = res_rows[0]
    print(f"Result #1: id={r1['resultId']}, pct={r1['percentage']}, grade={r1['grade']}, passStatus={r1['passStatus']}, isPublished={r1['isPublished']}")
    assert float(r1['percentage']) == 50.00, f"Expected percentage 50.00, got {r1['percentage']}"
    assert r1['grade'] == 'D', f"Expected grade D, got {r1['grade']}"
    assert r1['passStatus'] == 1, f"Expected passStatus 1, got {r1['passStatus']}"
    print("[OK] Result #1 in database is 50.00%, Grade D, passStatus 1.")

    print("\n=== 3. UNRELATED EXAMS INTEGRITY CHECK ===")
    regs = fetch_all("SELECT cr.registrationId, cr.examId, e.examTitle FROM CandidateRegistration cr JOIN Exam e ON e.examId = cr.examId WHERE cr.userId = 3 ORDER BY cr.registrationId")
    for reg in regs:
        att = fetch_one("SELECT attemptId, status FROM ExamAttempt WHERE registrationId = %s", (reg['registrationId'],))
        ev = fetch_one("SELECT evaluationId, totalMarksObtained, evaluationStatus FROM Evaluation WHERE attemptId = %s", (att['attemptId'],)) if att else None
        res = fetch_one("SELECT resultId FROM Result WHERE evaluationId = %s", (ev['evaluationId'],)) if ev else None
        print(f"Exam {reg['examId']} ('{reg['examTitle']}'): Attempt #{att['attemptId'] if att else None}, Eval #{ev['evaluationId'] if ev else None}, Result: {'EXISTS (' + str(res['resultId']) + ')' if res else 'None (Awaiting faculty review)'}")
        if reg['examId'] != 1:
            assert res is None, f"Exam {reg['examId']} should not have a Result row!"
    print("[OK] Unrelated exams remain completely untouched without fabricated Result rows.")

    print("\n=== 4. TEST API RESPONSES VIA FLASK TEST CLIENT ===")
    app = create_app()
    client = app.test_client()

    # Generate student token for student 3
    with app.app_context():
        token = create_access_token(identity="3", additional_claims={"role": "Student", "email": "rutuja.student@college.edu"})
    headers = {"Authorization": f"Bearer {token}"}

    # Test GET /api/students/3/results
    res = client.get("/api/students/3/results", headers=headers)
    assert res.status_code == 200, f"Failed GET /api/students/3/results: {res.status_code}"
    data = res.get_json()
    print(f"GET /api/students/3/results returned {len(data)} published results:")
    for item in data:
        print(f"  RES-{item['resultId']}: Exam='{item['examTitle']}', Marks={item['totalMarksObtained']}/{item['totalMarks']}, Pct={item['percentage']}%, Grade={item['grade']}, Pass={item['passStatus']}")
    assert len(data) == 1, f"Expected exactly 1 result in My Results, got {len(data)}"
    item = data[0]
    assert float(item['percentage']) == 50.00, f"Expected 50.00%, got {item['percentage']}"
    assert float(item['totalMarksObtained']) == 50.00, f"Expected obtained 50.00, got {item['totalMarksObtained']}"
    assert float(item['totalMarks']) == 100.00, f"Expected total 100.00, got {item['totalMarks']}"
    assert item['grade'] == 'D', f"Expected grade D, got {item['grade']}"
    assert item['passStatus'] == 1, f"Expected passStatus 1, got {item['passStatus']}"
    print("[OK] Student My Results API correctly returns 50.00% (50.00/100.00), Grade D.")

    # Test GET /api/results/1
    res = client.get("/api/results/1", headers=headers)
    assert res.status_code == 200, f"Failed GET /api/results/1: {res.status_code}"
    scorecard = res.get_json()
    print(f"\nGET /api/results/1 Scorecard:")
    print(f"  Exam: {scorecard['examTitle']} ({scorecard['examCode']})")
    print(f"  Marks: {scorecard['totalMarksObtained']} / {scorecard['totalMarks']}")
    print(f"  Percentage: {scorecard['percentage']}%")
    print(f"  Grade: {scorecard['grade']}")
    print(f"  PassStatus: {scorecard['passStatus']}")
    assert float(scorecard['percentage']) == 50.00
    assert scorecard['grade'] == 'D'
    assert float(scorecard['totalMarksObtained']) == 50.00
    assert float(scorecard['totalMarks']) == 100.00
    print("[OK] Scorecard detail API correctly returns 50.00% (50.00/100.00), Grade D.")

    # Test GET /api/student/dashboard
    res = client.get("/api/student/dashboard", headers=headers)
    assert res.status_code == 200, f"Failed GET /api/student/dashboard: {res.status_code}"
    dash = res.get_json()
    if dash.get("recentResults"):
        recent = dash["recentResults"][0]
        print(f"\nDashboard Recent Results:")
        print(f"  Exam: {recent['examTitle']}, Pct: {recent['percentage']}%, Grade: {recent['grade']}")
        assert float(recent['percentage']) == 50.00
        assert recent['grade'] == 'D'
    print("[OK] Student Dashboard recent results verified.")

    print("\n=== ALL REGRESSION CHECKS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_all()
