import subprocess
import time
import requests
import json
import websocket
import os
import shutil

class ChromeMultiTabTest:
    def __init__(self):
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = r"C:\Users\DRON\Downloads\Online ExaminationPlatfrom\scratch\chrome_verify_data"
        self.proc = None
        self.msg_id = 0

    def start(self):
        if os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir)
            except Exception as e:
                pass

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

    def get_pages(self):
        tabs = requests.get("http://127.0.0.1:9222/json").json()
        return [t for t in tabs if t.get("type") == "page"]

    def create_tab(self, url="about:blank"):
        new_tab = requests.put(f"http://127.0.0.1:9222/json/new?{url}").json()
        return new_tab

    def connect_tab(self, page_obj):
        ws_url = page_obj["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url)
        self._send(ws, "Page.enable")
        self._send(ws, "Runtime.enable")
        return ws

    def _send(self, ws, method, params=None):
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method, "params": params or {}}
        ws.send(json.dumps(payload))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == self.msg_id:
                return resp.get("result", {})

    def evaluate(self, ws, expr):
        res = self._send(ws, "Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        })
        if "exceptionDetails" in res:
            raise RuntimeError(res["exceptionDetails"])
        return res.get("result", {}).get("value")

    def navigate(self, ws, url):
        self._send(ws, "Page.navigate", {"url": url})
        time.sleep(1.5)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait()

def run_tests():
    chrome = ChromeMultiTabTest()
    report = []

    def check(step, condition, details=""):
        status = "PASS" if condition else "FAIL"
        report.append((step, status, details))
        print(f"[{status}] {step}: {details}")
        assert condition, f"FAILED: {step} - {details}"

    try:
        chrome.start()
        pages = chrome.get_pages()

        # ============================================================
        # A. Tab 1 -> Admin Login -> /admin/roles/permissions.html
        # ============================================================
        print("\n--- Step A: Tab 1 Admin Login ---")
        ws1 = chrome.connect_tab(pages[0])
        chrome.navigate(ws1, "http://127.0.0.1:5000/auth/login.html")
        
        login_res1 = chrome.evaluate(ws1, """
        (async () => {
            return await Auth.login('admin@platform.com', 'password123');
        })()
        """)
        check("A1: Admin Login Success", login_res1.get("user", {}).get("role") == "Admin", f"role={login_res1.get('user', {}).get('role')}")
        
        chrome.navigate(ws1, "http://127.0.0.1:5000/admin/roles/permissions.html")
        time.sleep(1)

        t1_url = chrome.evaluate(ws1, "window.location.pathname")
        t1_name = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent?.trim()")
        t1_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        t1_side = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        check("A2: Tab 1 URL", t1_url == "/admin/roles/permissions.html", f"url={t1_url}")
        check("A3: Tab 1 Header Name", "System Admin" in t1_name, f"name={t1_name}")
        check("A4: Tab 1 Header Role", "Admin" in t1_role, f"role={t1_role}")
        check("A5: Tab 1 Sidebar Title", t1_side == "Administrator Portal", f"sidebar={t1_side}")

        # ============================================================
        # B. Tab 2 -> Faculty Login -> /faculty/dashboard.html
        # ============================================================
        print("\n--- Step B: Tab 2 Faculty Login ---")
        tab2_obj = chrome.create_tab("http://127.0.0.1:5000/auth/login.html")
        ws2 = chrome.connect_tab(tab2_obj)
        time.sleep(1)

        login_res2 = chrome.evaluate(ws2, """
        (async () => {
            return await Auth.login('rajesh.sharma@college.edu', 'password123');
        })()
        """)
        check("B1: Faculty Login Success", login_res2.get("user", {}).get("role") == "Faculty", f"role={login_res2.get('user', {}).get('role')}")

        chrome.navigate(ws2, "http://127.0.0.1:5000/faculty/dashboard.html")
        time.sleep(1)

        t2_url = chrome.evaluate(ws2, "window.location.pathname")
        t2_name = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-name')?.textContent?.trim()")
        t2_role = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        t2_side = chrome.evaluate(ws2, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        check("B2: Tab 2 URL", t2_url == "/faculty/dashboard.html", f"url={t2_url}")
        check("B3: Tab 2 Header Name", "Rajesh Sharma" in t2_name, f"name={t2_name}")
        check("B4: Tab 2 Header Role", "Faculty" in t2_role, f"role={t2_role}")
        check("B5: Tab 2 Sidebar Title", t2_side == "Faculty Portal", f"sidebar={t2_side}")

        # ============================================================
        # C & D: Return to Tab 1 without logging in again
        # ============================================================
        print("\n--- Step C & D: Tab 1 State After Faculty Logged In in Tab 2 ---")
        t1_ret_url = chrome.evaluate(ws1, "window.location.pathname")
        t1_ret_name = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent?.trim()")
        t1_ret_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        t1_ret_side = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        check("D1: Tab 1 Remains on Admin URL", t1_ret_url == "/admin/roles/permissions.html", f"url={t1_ret_url}")
        check("D2: Tab 1 Header Name is still System Admin", "System Admin" in t1_ret_name, f"name={t1_ret_name}")
        check("D3: Tab 1 Header Role is still Admin (ID: 1)", "Admin" in t1_ret_role, f"role={t1_ret_role}")
        check("D4: Tab 1 Sidebar is still Administrator Portal", t1_ret_side == "Administrator Portal", f"sidebar={t1_ret_side}")

        # ============================================================
        # E. Tab 1 can successfully call an Admin endpoint
        # ============================================================
        print("\n--- Step E: Tab 1 Admin API Request ---")
        api_res1 = chrome.evaluate(ws1, """
        (async () => {
            try {
                const res = await apiFetch('/permissions');
                return { success: true, count: res ? res.length : 0 };
            } catch (err) {
                return { success: false, status: err.status, message: err.message };
            }
        })()
        """)
        check("E: Tab 1 Admin API Call", api_res1.get("success") == True, f"result={api_res1}")

        # ============================================================
        # F. Tab 2 still shows Dr. Rajesh Sharma, Faculty, Faculty Portal
        # ============================================================
        print("\n--- Step F: Tab 2 State Check ---")
        t2_f_name = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-name')?.textContent?.trim()")
        t2_f_role = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        t2_f_side = chrome.evaluate(ws2, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        check("F1: Tab 2 Name", "Rajesh Sharma" in t2_f_name, f"name={t2_f_name}")
        check("F2: Tab 2 Role", "Faculty" in t2_f_role, f"role={t2_f_role}")
        check("F3: Tab 2 Sidebar", t2_f_side == "Faculty Portal", f"sidebar={t2_f_side}")

        # Also verify Tab 2 can call a Faculty endpoint
        api_res2 = chrome.evaluate(ws2, """
        (async () => {
            try {
                const res = await apiFetch('/questions');
                return { success: true, count: res ? res.length : 0 };
            } catch (err) {
                return { success: false, status: err.status, message: err.message };
            }
        })()
        """)
        check("F4: Tab 2 Faculty API Call", api_res2.get("success") == True, f"result={api_res2}")

        # ============================================================
        # G. Refresh both tabs and verify roles remain independent
        # ============================================================
        print("\n--- Step G: Refresh Both Tabs ---")
        chrome.navigate(ws1, "http://127.0.0.1:5000/admin/roles/permissions.html")
        time.sleep(1)
        chrome.navigate(ws2, "http://127.0.0.1:5000/faculty/dashboard.html")
        time.sleep(1)

        t1_ref_url = chrome.evaluate(ws1, "window.location.pathname")
        t1_ref_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        t1_ref_side = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        t2_ref_url = chrome.evaluate(ws2, "window.location.pathname")
        t2_ref_role = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        t2_ref_side = chrome.evaluate(ws2, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        check("G1: Tab 1 URL after refresh", t1_ref_url == "/admin/roles/permissions.html", f"url={t1_ref_url}")
        check("G2: Tab 1 Role after refresh", "Admin" in t1_ref_role, f"role={t1_ref_role}")
        check("G3: Tab 1 Sidebar after refresh", t1_ref_side == "Administrator Portal", f"sidebar={t1_ref_side}")

        check("G4: Tab 2 URL after refresh", t2_ref_url == "/faculty/dashboard.html", f"url={t2_ref_url}")
        check("G5: Tab 2 Role after refresh", "Faculty" in t2_ref_role, f"role={t2_ref_role}")
        check("G6: Tab 2 Sidebar after refresh", t2_ref_side == "Faculty Portal", f"sidebar={t2_ref_side}")

        # ============================================================
        # H. Logout Faculty in Tab 2 and verify Tab 1 Admin remains logged in
        # ============================================================
        print("\n--- Step H: Logout Tab 2 (Faculty) ---")
        chrome.evaluate(ws2, """
        (async () => {
            await Auth.logout();
        })()
        """)
        time.sleep(1)

        t2_out_url = chrome.evaluate(ws2, "window.location.pathname")
        check("H1: Tab 2 Logged Out to login page", "login" in t2_out_url, f"url={t2_out_url}")

        # Check Tab 1: Must STILL be logged in as Admin!
        t1_stay_token = chrome.evaluate(ws1, "Auth.getToken()")
        t1_stay_user = chrome.evaluate(ws1, "Auth.getUser()")
        check("H2: Tab 1 Admin Token preserved", t1_stay_token is not None, f"token exists={t1_stay_token is not None}")
        check("H3: Tab 1 Admin User role preserved", t1_stay_user.get("role") == "Admin", f"role={t1_stay_user.get('role')}")

        # Tab 1 can still perform Admin API requests
        api_res1_after = chrome.evaluate(ws1, """
        (async () => {
            try {
                const res = await apiFetch('/permissions');
                return { success: true };
            } catch (err) {
                return { success: false, status: err.status };
            }
        })()
        """)
        check("H4: Tab 1 API Call Still Succeeds", api_res1_after.get("success") == True, f"result={api_res1_after}")

        # ============================================================
        # I. Test shared Subjects page as Admin and Faculty
        # ============================================================
        print("\n--- Step I: Shared Subjects Page for Both Roles ---")
        # 1. Test Tab 1 (Admin) on /subjects/list.html
        chrome.navigate(ws1, "http://127.0.0.1:5000/subjects/list.html")
        time.sleep(1)

        sub_admin_side = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent?.trim()")
        sub_admin_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        sub_admin_name = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent?.trim()")
        sub_admin_bread = chrome.evaluate(ws1, "document.querySelector('.breadcrumb-item a')?.textContent?.trim()")

        check("I1: Admin on Subjects sees Administrator Portal sidebar", sub_admin_side == "Administrator Portal", f"sidebar={sub_admin_side}")
        check("I2: Admin on Subjects sees Admin header role", "Admin" in sub_admin_role, f"role={sub_admin_role}")
        check("I3: Admin on Subjects sees System Admin name", "System Admin" in sub_admin_name, f"name={sub_admin_name}")
        check("I4: Admin on Subjects breadcrumb updated to Admin", sub_admin_bread == "Admin", f"breadcrumb={sub_admin_bread}")

        # 2. Login Faculty again in Tab 2 and test on /subjects/list.html
        chrome.navigate(ws2, "http://127.0.0.1:5000/auth/login.html")
        chrome.evaluate(ws2, """
        (async () => {
            return await Auth.login('rajesh.sharma@college.edu', 'password123');
        })()
        """)
        chrome.navigate(ws2, "http://127.0.0.1:5000/subjects/list.html")
        time.sleep(1)

        sub_fac_side = chrome.evaluate(ws2, "document.querySelector('.nav-section-title')?.textContent?.trim()")
        sub_fac_role = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-role')?.textContent?.trim()")
        sub_fac_name = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-name')?.textContent?.trim()")
        sub_fac_bread = chrome.evaluate(ws2, "document.querySelector('.breadcrumb-item a')?.textContent?.trim()")

        check("I5: Faculty on Subjects sees Faculty Portal sidebar", sub_fac_side == "Faculty Portal", f"sidebar={sub_fac_side}")
        check("I6: Faculty on Subjects sees Faculty header role", "Faculty" in sub_fac_role, f"role={sub_fac_role}")
        check("I7: Faculty on Subjects sees Dr. Rajesh Sharma name", "Rajesh Sharma" in sub_fac_name, f"name={sub_fac_name}")
        check("I8: Faculty on Subjects breadcrumb shows Faculty", sub_fac_bread == "Faculty", f"breadcrumb={sub_fac_bread}")

        # 3. Test Notifications page for both roles
        chrome.navigate(ws1, "http://127.0.0.1:5000/notifications/center.html")
        chrome.navigate(ws2, "http://127.0.0.1:5000/notifications/center.html")
        time.sleep(1)

        notif_admin_side = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent?.trim()")
        notif_fac_side = chrome.evaluate(ws2, "document.querySelector('.nav-section-title')?.textContent?.trim()")

        check("I9: Admin on Notifications sees Administrator Portal", notif_admin_side == "Administrator Portal", f"sidebar={notif_admin_side}")
        check("I10: Faculty on Notifications sees Faculty Portal", notif_fac_side == "Faculty Portal", f"sidebar={notif_fac_side}")

        print("\n============================================================")
        print("ALL MULTI-TAB CHROME TESTS PASSED PERFECTLY!")
        print("============================================================")

    finally:
        chrome.stop()

if __name__ == "__main__":
    run_tests()
