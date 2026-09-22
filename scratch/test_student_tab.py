import subprocess
import time
import requests
import json
import websocket
import os
import shutil

class ChromeStudentTest:
    def __init__(self):
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = r"C:\Users\DRON\Downloads\Online ExaminationPlatfrom\scratch\chrome_student_data"
        self.proc = None
        self.msg_id = 0

    def start(self):
        if os.path.exists(self.user_data_dir):
            try: shutil.rmtree(self.user_data_dir)
            except: pass
        args = [
            self.chrome_path,
            "--remote-debugging-port=9222",
            "--remote-allow-origins=*",
            f"--user-data-dir={self.user_data_dir}",
            "--disable-gpu",
            "--no-sandbox",
            "--headless=new",
            "about:blank"
        ]
        self.proc = subprocess.Popen(args)
        time.sleep(2)

    def _send(self, ws, method, params=None):
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method, "params": params or {}}
        ws.send(json.dumps(payload))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == self.msg_id:
                return resp.get("result", {})

    def evaluate(self, ws, expr):
        res = self._send(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        return res.get("result", {}).get("value")

    def navigate(self, ws, url):
        self._send(ws, "Page.navigate", {"url": url})
        time.sleep(1.5)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait()

def run():
    c = ChromeStudentTest()
    try:
        c.start()
        tabs = requests.get("http://127.0.0.1:9222/json").json()
        pages = [t for t in tabs if t.get("type") == "page"]
        ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"])
        c._send(ws, "Page.enable")
        c._send(ws, "Runtime.enable")

        c.navigate(ws, "http://127.0.0.1:5000/auth/login.html")
        c.evaluate(ws, """
        (async () => {
            return await Auth.login('rutuja.student@college.edu', 'password123');
        })()
        """)
        c.navigate(ws, "http://127.0.0.1:5000/student/dashboard.html")
        time.sleep(1)

        name = c.evaluate(ws, "document.querySelector('.user-dropdown .user-name')?.textContent?.trim()")
        role = c.evaluate(ws, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        sidebar = c.evaluate(ws, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        print(f"Student Name: {name}")
        print(f"Student Role: {role}")
        print(f"Student Sidebar: {sidebar}")

        assert "Rutuja" in name
        assert "Student" in role
        assert sidebar == "Student Portal"
        print("[PASS] Student Login & Dashboard verified successfully!")
    finally:
        c.stop()

if __name__ == "__main__":
    run()
