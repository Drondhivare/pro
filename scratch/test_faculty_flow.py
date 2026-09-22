import sys
sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.database import fetch_all, fetch_one, execute
from backend.app import create_app
from flask_jwt_extended import create_access_token
import json

def test_faculty():
    app = create_app()
    client = app.test_client()

    with app.app_context():
        # Faculty token for user 2 (Dr. Rajesh Sharma)
        token = create_access_token(identity="2", additional_claims={"role": "Faculty", "email": "rajesh.sharma@college.edu"})
    headers = {"Authorization": f"Bearer {token}"}

    # Verify pending evaluations list
    res = client.get("/api/evaluations/pending", headers=headers)
    assert res.status_code == 200
    pending = res.get_json()
    print(f"Pending evaluations in faculty queue: {len(pending)}")
    for p in pending:
        print(f"  Attempt {p['attemptId']} (Student {p['userId']} - {p['firstName']} {p['lastName']}): Exam {p['examId']} - {p['examTitle']}, Status: {p['evaluationStatus']}, Score: {p['totalMarksObtained']}")

    # Verify results list for faculty
    res = client.get("/api/results", headers=headers)
    assert res.status_code == 200
    results = res.get_json()
    print(f"\nFaculty Results view count: {len(results)}")
    for r in results:
        print(f"  RES-{r['resultId']}: Exam {r['examId']} ({r['examTitle']}) - Student {r['firstName']} {r['lastName']}: {r['totalMarksObtained']}/{r['totalMarks']} ({r['percentage']}%, Grade: {r['grade']}, Pass: {r['passStatus']})")
        assert float(r['percentage']) == 50.00
        assert r['grade'] == 'D'
    print("\nFaculty evaluation and results flow verified successfully!")

if __name__ == "__main__":
    test_faculty()
