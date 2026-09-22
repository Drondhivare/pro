import requests
import json
import time
import os
import shutil
import websocket
import subprocess

class ChromeSession:
    def __init__(self, headless=True):
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = r"C:\Users\DRON\.gemini\antigravity-ide\brain\1c51a158-d30c-4160-88c9-ccc0af0a57c9\scratch\chrome_zero_q_data"
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
            "--remote-debugging-port=9223",
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

        tabs = requests.get("http://127.0.0.1:9223/json").json()
        pages = [t for t in tabs if t.get("type") == "page"]
        ws_url = pages[0]["webSocketDebuggerUrl"] if pages else tabs[0]["webSocketDebuggerUrl"]

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
        for _ in range(50):
            time.sleep(0.1)
            ready = self.evaluate("document.readyState")
            if ready == "complete":
                break
        time.sleep(0.5)

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        if self.proc:
            self.proc.terminate()
            self.proc.wait()

def test_zero_question_exam():
    # 1. Update Exam 27 Schedule as Faculty so attempt can be started now
    import datetime
    fac_s = requests.Session()
    fac_login = fac_s.post("http://127.0.0.1:8000/api/auth/login", json={"email": "rajesh.sharma@college.edu", "password": "password123"})
    fac_token = fac_login.json()["accessToken"]
    fac_headers = {"Authorization": f"Bearer {fac_token}"}

    now = datetime.datetime.now()
    t_start = (now - datetime.timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
    t_end = (now + datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    fac_s.put("http://127.0.0.1:8000/api/exams/27", headers=fac_headers, json={"isActive": True})
    fac_s.post("http://127.0.0.1:8000/api/exams/27/schedule", headers=fac_headers, json={
        "startTime": t_start,
        "endTime": t_end,
        "lateEntryMinutes": 60,
        "autoSubmit": True
    })

    # 2. Student flow
    s = requests.Session()
    login_res = s.post("http://127.0.0.1:8000/api/auth/login", json={"email": "rutuja.student@college.edu", "password": "password123"})
    token_data = login_res.json()
    token = token_data["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    # Register for Exam 27 (0 questions)
    reg_res = s.post("http://127.0.0.1:8000/api/exams/27/register", headers=headers)
    print("Register for Exam 27:", reg_res.status_code)

    # Start Attempt for Exam 27
    start_res = s.post("http://127.0.0.1:8000/api/exams/27/attempts/start", headers=headers)
    print("Start attempt Exam 27:", start_res.status_code, start_res.json())
    attempt_id = start_res.json()["attemptId"]

    browser = ChromeSession(headless=True)
    browser.start()
    try:
        browser.navigate("http://127.0.0.1:5000/auth/login.html")
        browser.evaluate(f"""
            localStorage.setItem('accessToken', '{token}');
            localStorage.setItem('user', JSON.stringify({json.dumps(token_data['user'])}));
        """)

        # Open runtime for Exam 27
        url = f"http://127.0.0.1:5000/exam_runtime/exam.html?attemptId={attempt_id}&examId=27"
        print("Navigating to:", url)
        browser.navigate(url)
        time.sleep(1.5)

        # 1. Verify No questions warning appears
        alert_text = browser.evaluate("document.getElementById('questionsWrapper').innerText")
        print("Wrapper text:", alert_text)
        assert "No questions assigned to this exam yet" in alert_text, f"Missing zero-question alert: {alert_text}"

        # 2. Verify Timer initialized and counting down
        timer_text = browser.evaluate("document.getElementById('examTimer').innerText")
        print("Timer in zero-question exam:", timer_text)
        assert timer_text != "--:--", f"Timer failed to initialize! Got: {timer_text}"

        # 3. Verify Security initialized
        sec_text = browser.evaluate("document.getElementById('securityStatusText').innerText")
        warn_badge = browser.evaluate("document.getElementById('securityWarningBadge').innerText")
        print(f"Security in zero-question exam -> Status: {sec_text}, Badge: {warn_badge}")
        assert "Active" in sec_text
        assert "Warnings: 0/3" in warn_badge

        # 4. Verify Finish & Review is disabled and hidden
        btn_hidden = browser.evaluate("""
            const btn = document.getElementById('btnFinishReview');
            btn.classList.contains('d-none') && btn.classList.contains('disabled')
        """)
        print("Finish & Review button disabled/hidden:", btn_hidden)
        assert btn_hidden is True, "Finish & Review button is not hidden/disabled!"

        # 5. Verify tab switch security still triggers
        print("Testing tab switch on zero-question exam...")
        browser.evaluate("""
            Object.defineProperty(document, 'visibilityState', { value: 'hidden', writable: true });
            document.dispatchEvent(new Event('visibilitychange'));
        """)
        time.sleep(1.5)

        warn_badge_after = browser.evaluate("document.getElementById('securityWarningBadge').innerText")
        print("Badge after tab switch on zero-question exam:", warn_badge_after)
        assert "Warnings: 1/3" in warn_badge_after, f"Expected Warnings: 1/3, got: {warn_badge_after}"

        print("=== ZERO-QUESTION EXAM TEST PASSED PERFECTLY! ===")
    finally:
        browser.close()

if __name__ == "__main__":
    test_zero_question_exam()
