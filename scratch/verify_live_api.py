import urllib.request
import json

def test_live():
    # Login as student 3
    login_payload = json.dumps({'email': 'rutuja.student@college.edu', 'password': 'password123'}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=login_payload, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as res:
        login_data = json.loads(res.read().decode('utf-8'))
        token = login_data['accessToken']
        user = login_data['user']
        print(f"Logged in as {user['firstName']} {user['lastName']} (userId={user['userId']})")

    # GET /api/students/3/results
    req = urllib.request.Request('http://127.0.0.1:8000/api/students/3/results', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as res:
        results = json.loads(res.read().decode('utf-8'))
        print(f"Results from live server count: {len(results)}")
        for r in results:
            print(f"  RES-{r['resultId']}: {r['examTitle']} | Marks: {r['totalMarksObtained']}/{r['totalMarks']} | Pct: {r['percentage']}% | Grade: {r['grade']}")
            assert float(r['percentage']) == 50.00
            assert r['grade'] == 'D'

    # GET /api/results/1
    req = urllib.request.Request('http://127.0.0.1:8000/api/results/1', headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as res:
        scorecard = json.loads(res.read().decode('utf-8'))
        print(f"Scorecard from live server: percentage={scorecard['percentage']}%, grade={scorecard['grade']}, marks={scorecard['totalMarksObtained']}/{scorecard['totalMarks']}")
        assert float(scorecard['percentage']) == 50.00
        assert scorecard['grade'] == 'D'

    print("LIVE API VERIFICATION SUCCESSFUL!")

if __name__ == "__main__":
    test_live()
