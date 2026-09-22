import urllib.request
import json
import sys

def run_test3():
    print("==================================================")
    print("TEST 3 — Result Consistency Across Endpoints")
    print("==================================================")
    base_api = "http://127.0.0.1:8000/api"

    # 1. Login as Student (student_id = 3)
    stud_login = json.dumps({"email": "rutuja.student@college.edu", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/auth/login", data=stud_login, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        stud_data = json.loads(res.read().decode("utf-8"))
        stud_token = stud_data["accessToken"]
    stud_headers = {"Authorization": f"Bearer {stud_token}", "Content-Type": "application/json"}

    # 2. Login as Faculty
    fac_login = json.dumps({"email": "rajesh.sharma@college.edu", "password": "password123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_api}/auth/login", data=fac_login, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as res:
        fac_data = json.loads(res.read().decode("utf-8"))
        fac_token = fac_data["accessToken"]
    fac_headers = {"Authorization": f"Bearer {fac_token}", "Content-Type": "application/json"}

    # 3. GET /api/students/3/results
    print("\n--- 3.1 Fetching Student Results: GET /api/students/3/results ---")
    req = urllib.request.Request(f"{base_api}/students/3/results", headers=stud_headers)
    with urllib.request.urlopen(req) as res:
        student_results = json.loads(res.read().decode("utf-8"))
        print(f"  Returned {len(student_results)} results for student 3.")

    # 4. GET /api/results (Faculty view)
    print("\n--- 3.2 Fetching Faculty Results: GET /api/results ---")
    req = urllib.request.Request(f"{base_api}/results", headers=fac_headers)
    with urllib.request.urlopen(req) as res:
        all_results = json.loads(res.read().decode("utf-8"))
        print(f"  Returned {len(all_results)} total results in platform.")

    fac_results_by_id = {r["resultId"]: r for r in all_results}

    # 5. For each student result, verify consistency across all 3 endpoints
    print("\n--- 3.3 Verifying Field-by-Field Consistency ---")
    for sr in student_results:
        rid = sr["resultId"]
        print(f"\nChecking Result #{rid} ('{sr['examTitle']}'):")

        # Must exist in faculty results list
        assert rid in fac_results_by_id, f"Result #{rid} missing from GET /api/results!"
        fr = fac_results_by_id[rid]

        # Fetch detail: GET /api/results/<result_id>
        req = urllib.request.Request(f"{base_api}/results/{rid}", headers=stud_headers)
        with urllib.request.urlopen(req) as res:
            dr = json.loads(res.read().decode("utf-8"))

        print(f"  [Student List]   Marks: {sr['totalMarksObtained']}/{sr['totalMarks']} | Pct: {sr['percentage']}% | Grade: {sr['grade']} | Pass: {sr['passStatus']}")
        print(f"  [Faculty List]   Marks: {fr['totalMarksObtained']}/{fr['totalMarks']} | Pct: {fr['percentage']}% | Grade: {fr['grade']} | Pass: {fr['passStatus']}")
        print(f"  [Scorecard Detail] Marks: {dr['totalMarksObtained']}/{dr['totalMarks']} | Pct: {dr['percentage']}% | Grade: {dr['grade']} | Pass: {dr['passStatus']}")

        # Consistency checks: Percentage
        assert float(sr["percentage"]) == float(fr["percentage"]), f"Percentage mismatch for #{rid}: student={sr['percentage']}, faculty={fr['percentage']}"
        assert float(sr["percentage"]) == float(dr["percentage"]), f"Percentage mismatch for #{rid}: student={sr['percentage']}, detail={dr['percentage']}"

        # Consistency checks: Grade
        assert sr["grade"] == fr["grade"], f"Grade mismatch for #{rid}: student={sr['grade']}, faculty={fr['grade']}"
        assert sr["grade"] == dr["grade"], f"Grade mismatch for #{rid}: student={sr['grade']}, detail={dr['grade']}"

        # Consistency checks: Marks Obtained
        assert float(sr["totalMarksObtained"]) == float(fr["totalMarksObtained"]), f"Obtained marks mismatch for #{rid}: student={sr['totalMarksObtained']}, faculty={fr['totalMarksObtained']}"
        assert float(sr["totalMarksObtained"]) == float(dr["totalMarksObtained"]), f"Obtained marks mismatch for #{rid}: student={sr['totalMarksObtained']}, detail={dr['totalMarksObtained']}"

        # Consistency checks: Total Marks
        assert float(sr["totalMarks"]) == float(fr["totalMarks"]), f"Total marks mismatch for #{rid}: student={sr['totalMarks']}, faculty={fr['totalMarks']}"
        assert float(sr["totalMarks"]) == float(dr["totalMarks"]), f"Total marks mismatch for #{rid}: student={sr['totalMarks']}, detail={dr['totalMarks']}"

        # Consistency checks: Pass Status
        assert int(sr["passStatus"]) == int(fr["passStatus"]), f"Pass status mismatch for #{rid}: student={sr['passStatus']}, faculty={fr['passStatus']}"
        assert int(sr["passStatus"]) == int(dr["passStatus"]), f"Pass status mismatch for #{rid}: student={sr['passStatus']}, detail={dr['passStatus']}"

        # Mathematical verification: percentage = (obtained / total) * 100
        expected_pct = round((float(sr["totalMarksObtained"]) / float(sr["totalMarks"])) * 100, 2)
        assert float(sr["percentage"]) == expected_pct, f"Mathematical error for #{rid}: expected {expected_pct}%, got {sr['percentage']}%"

        print(f"  [OK] Result #{rid} is 100% consistent across all 3 endpoints.")

    print("\n>>> TEST 3: ALL CONSISTENCY CHECKS PASSED <<<")
    return True

if __name__ == "__main__":
    success = run_test3()
    sys.exit(0 if success else 1)
