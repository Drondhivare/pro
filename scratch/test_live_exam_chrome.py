import subprocess
import time
import requests
import json
import websocket
import os
import shutil

class ChromeSession:
    def __init__(self, headless=True):
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = r"C:\Users\DRON\.gemini\antigravity-ide\brain\1c51a158-d30c-4160-88c9-ccc0af0a57c9\scratch\chrome_session_data"
        self.headless = headless
        self.proc = None
        self.ws = None
        self.msg_id = 0

    def start(self):
        if os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir)
            except Exception:
                pass

        args = [
            self.chrome_path,
            "--remote-debugging-port=9222",
            "--remote-allow-origins=*",
            f"--user-data-dir={self.user_data_dir}",
            "--disable-gpu",
            "--no-sandbox",
        ]
        if self.headless:
            args.append("--headless=new")
        args.append("about:blank")
        self.proc = subprocess.Popen(args)
        time.sleep(2)

        tabs = requests.get("http://127.0.0.1:9222/json").json()
        pages = [t for t in tabs if t.get("type") == "page"]
        if not pages:
            # Create a new page target
            new_tab = requests.get("http://127.0.0.1:9222/json/new?about:blank").json()
            ws_url = new_tab["webSocketDebuggerUrl"]
        else:
            ws_url = pages[0]["webSocketDebuggerUrl"]

        self.ws = websocket.create_connection(ws_url)
        self.send("Page.enable")
        self.send("Runtime.enable")

    def send(self, method, params=None):
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method, "params": params or {}}
        self.ws.send(json.dumps(payload))
        while True:
            resp = json.loads(self.ws.recv())
            if resp.get("id") == self.msg_id:
                return resp.get("result", {})

    def evaluate(self, expression):
        res = self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS Error in '{expression}': {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def navigate(self, url):
        self.send("Page.navigate", {"url": url})
        # Wait until document ready
        for _ in range(50):
            time.sleep(0.1)
            ready = self.evaluate("document.readyState")
            if ready == "complete":
                break
        time.sleep(0.5)

    def wait_for_text(self, selector, expected_substr=None, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            val = self.evaluate(f"document.querySelector('{selector}') ? document.querySelector('{selector}').innerText : null")
            if val is not None:
                if expected_substr is None or expected_substr in val:
                    return val
            time.sleep(0.2)
        return self.evaluate(f"document.querySelector('{selector}') ? document.querySelector('{selector}').innerText : null")

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        if self.proc:
            self.proc.terminate()
            self.proc.wait()

def run_test():
    # 1. Obtain Student JWT Token via API
    s = requests.Session()
    login_res = s.post("http://127.0.0.1:8000/api/auth/login", json={"email": "rutuja.student@college.edu", "password": "password123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    token = token_data["accessToken"]
    user_json = json.dumps(token_data["user"])

    # Check Attempt 25 state before in DB
    import sys
    sys.path.insert(0, "backend")
    from database import fetch_one
    att = fetch_one("SELECT * FROM ExamAttempt WHERE attemptId = 25")
    print(f"[DB] Initial Attempt 25: status={att['status']}, violationCount={att['violationCount']}")

    # 2. Launch Chrome
    browser = ChromeSession(headless=True)
    browser.start()

    try:
        # First navigate to login page to set localStorage without triggering requireAuth redirect
        browser.navigate("http://127.0.0.1:5000/auth/login.html")
        browser.evaluate(f"""
            localStorage.setItem('accessToken', '{token}');
            localStorage.setItem('user', JSON.stringify({user_json}));
        """)
        print("[Browser] Auth tokens set in localStorage.")

        # 3. Open Exam 28: http://127.0.0.1:5000/exam_runtime/exam.html?attemptId=25&examId=28
        print("[Browser] Navigating to Exam 28 runtime...")
        browser.navigate("http://127.0.0.1:5000/exam_runtime/exam.html?attemptId=25&examId=28")
        time.sleep(1.5)

        curr_url = browser.evaluate("window.location.href")
        print(f"[Browser] Current URL: {curr_url}")

        # 4. Verify Header & Questions
        browser.wait_for_text("#examTitleHeader", expected_substr=None, timeout=10)
        title = browser.evaluate("document.getElementById('examTitleHeader') ? document.getElementById('examTitleHeader').innerText : ''")
        print(f"[Browser] Exam Title: {title}")
        assert "UT" in title, f"Expected UT, got {title}"

        # Wait for questions to load
        q1_text = browser.wait_for_text("#question-1 h5")
        print(f"[Browser] Question 1 text: {q1_text}")
        assert "Which SQL clause" in q1_text, f"Question 1 not rendered: {q1_text}"

        palette_count = browser.evaluate("document.querySelectorAll('#paletteContainer .question-palette-btn').length")
        print(f"[Browser] Navigation palette buttons count: {palette_count}")
        assert palette_count == 2, f"Expected 2 palette buttons, got {palette_count}"

        # 5. Verify Timer
        timer_text_1 = browser.wait_for_text("#examTimer")
        print(f"[Browser] Timer reading 1: {timer_text_1}")
        assert timer_text_1 != "--:--", f"Timer is stuck at --:--!"
        time.sleep(2)
        timer_text_2 = browser.wait_for_text("#examTimer")
        print(f"[Browser] Timer reading 2: {timer_text_2}")
        assert timer_text_1 != timer_text_2, f"Timer is not ticking! 1: {timer_text_1}, 2: {timer_text_2}"

        # 6. Verify Initial Security Widget
        sec_text = browser.evaluate("document.getElementById('securityStatusText').innerText")
        sec_warn = browser.evaluate("document.getElementById('securityWarningBadge').innerText")
        print(f"[Browser] Initial Security Status: {sec_text}, Badge: {sec_warn}")
        assert "Active" in sec_text
        assert "Warnings: 0/3" in sec_warn

        # 7. Select Answer for Q1 (Radio option 1 = WHERE)
        print("[Browser] Selecting Option for Question 1...")
        browser.evaluate("document.querySelector('input[name=\"q_1_option\"]').click()")
        time.sleep(1)
        is_checked = browser.evaluate("document.querySelector('input[name=\"q_1_option\"]').checked")
        print(f"[Browser] Option 1 checked: {is_checked}")
        assert is_checked is True

        # Check answers in backend
        ans_res = s.get("http://127.0.0.1:8000/api/attempts/25/answers", headers={"Authorization": f"Bearer {token}"})
        print(f"[API] Answers saved in attempt 25: {ans_res.json()}")
        assert len(ans_res.json()) >= 1, "Answer was not autosaved to backend!"

        # 8. Trigger Tab Switch 1 (Lost Focus)
        print("[Browser] Simulating 1st Tab Switch (visibilityState=hidden / blur)...")
        browser.evaluate("""
            Object.defineProperty(document, 'visibilityState', { value: 'hidden', writable: true });
            document.dispatchEvent(new Event('visibilitychange'));
        """)
        time.sleep(1.5)

        warn_badge_1 = browser.evaluate("document.getElementById('securityWarningBadge').innerText")
        alert_title_1 = browser.evaluate("document.getElementById('securityAlertTitle').innerText")
        print(f"[Browser] After 1st Tab Switch -> Badge: {warn_badge_1}, Alert: {alert_title_1}")
        assert "Warnings: 1/3" in warn_badge_1, f"Expected Warnings: 1/3, got {warn_badge_1}"

        # Check DB
        att_db_1 = fetch_one("SELECT violationCount FROM ExamAttempt WHERE attemptId = 25")
        print(f"[DB] Violation count in MySQL: {att_db_1['violationCount']}")
        assert att_db_1['violationCount'] == 1

        # Return to tab
        browser.evaluate("""
            Object.defineProperty(document, 'visibilityState', { value: 'visible', writable: true });
            document.dispatchEvent(new Event('visibilitychange'));
        """)
        time.sleep(1)

        # Normal interaction test: click question 2 in palette
        print("[Browser] Normal interaction: navigating to Question 2...")
        browser.evaluate("document.getElementById('palette-btn-2').click()")
        time.sleep(0.5)
        q2_visible = browser.evaluate("!document.getElementById('question-2').classList.contains('d-none')")
        print(f"[Browser] Question 2 visible: {q2_visible}")
        assert q2_visible is True

        # Verify normal interaction did NOT increase violations
        att_db_normal = fetch_one("SELECT violationCount FROM ExamAttempt WHERE attemptId = 25")
        assert att_db_normal['violationCount'] == 1, "Normal interaction increased violation count!"

        # 9. Trigger Tab Switch 2 (Second Violation)
        print("[Browser] Simulating 2nd Tab Switch (visibilityState=hidden / blur)...")
        time.sleep(1) # respect 1.5s cooldown
        browser.evaluate("""
            Object.defineProperty(document, 'visibilityState', { value: 'hidden', writable: true });
            document.dispatchEvent(new Event('visibilitychange'));
        """)
        time.sleep(1.5)

        warn_badge_2 = browser.evaluate("document.getElementById('securityWarningBadge').innerText")
        alert_title_2 = browser.evaluate("document.getElementById('securityAlertTitle').innerText")
        print(f"[Browser] After 2nd Tab Switch -> Badge: {warn_badge_2}, Alert: {alert_title_2}")
        assert "Warnings: 2/3" in warn_badge_2, f"Expected Warnings: 2/3, got {warn_badge_2}"

        att_db_2 = fetch_one("SELECT violationCount FROM ExamAttempt WHERE attemptId = 25")
        print(f"[DB] Violation count in MySQL after 2nd switch: {att_db_2['violationCount']}")
        assert att_db_2['violationCount'] == 2

        # 10. Refresh & Resume Test
        print("[Browser] Refreshing page to verify resume capability...")
        browser.navigate("http://127.0.0.1:5000/exam_runtime/exam.html?attemptId=25&examId=28")
        time.sleep(1.5)

        resumed_badge = browser.evaluate("document.getElementById('securityWarningBadge').innerText")
        resumed_timer = browser.evaluate("document.getElementById('examTimer').innerText")
        print(f"[Browser] Resumed state -> Badge: {resumed_badge}, Timer: {resumed_timer}")
        assert "Warnings: 2/3" in resumed_badge, f"Badge did not resume: {resumed_badge}"
        assert resumed_timer != "--:--", f"Timer stuck at --:-- on resume"

        print("=== ALL LIVE EXAM CHROME TESTS PASSED SUCCESSFULLY! ===")

    finally:
        browser.close()

if __name__ == "__main__":
    run_test()
