import subprocess
import time
import requests
import json
import websocket
import os
import shutil

class ChromeMultiTab:
    def __init__(self):
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = r"C:\Users\DRON\Downloads\Online ExaminationPlatfrom\scratch\chrome_tab_test_data"
        self.proc = None
        self.msg_id = 0

    def start(self):
        if os.path.exists(self.user_data_dir):
            try:
                shutil.rmtree(self.user_data_dir)
            except Exception as e:
                print("Could not clean dir:", e)

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
        # Enable domains
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

def run():
    chrome = ChromeMultiTab()
    try:
        chrome.start()
        pages = chrome.get_pages()
        print(f"Initial pages: {len(pages)}")

        # Tab 1: Admin Tab
        ws1 = chrome.connect_tab(pages[0])
        print("\n--- TAB 1: Navigating to login.html ---")
        chrome.navigate(ws1, "http://127.0.0.1:5000/auth/login.html")
        
        # Perform Admin login
        print("Logging in as Admin (admin@platform.com)...")
        login_script = """
        (async () => {
            const res = await Auth.login('admin@platform.com', 'password123');
            return res;
        })()
        """
        login_res = chrome.evaluate(ws1, login_script)
        print("Tab 1 Login response user:", login_res.get('user'))
        
        # Navigate to permissions.html
        chrome.navigate(ws1, "http://127.0.0.1:5000/admin/roles/permissions.html")
        time.sleep(1)
        
        tab1_user = chrome.evaluate(ws1, "localStorage.getItem('user')")
        tab1_token = chrome.evaluate(ws1, "localStorage.getItem('accessToken')")
        tab1_header_name = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent")
        tab1_header_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent")
        tab1_sidebar_title = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent")
        tab1_url = chrome.evaluate(ws1, "window.location.href")
        
        print(f"\n[Tab 1 State (Admin)]")
        print(f"  URL: {tab1_url}")
        print(f"  Header Name: {tab1_header_name}")
        print(f"  Header Role: {tab1_header_role}")
        print(f"  Sidebar Title: {tab1_sidebar_title}")
        print(f"  localStorage user: {tab1_user}")

        # Now create Tab 2: Faculty Tab
        print("\n--- TAB 2: Opening new tab for Faculty ---")
        tab2_obj = chrome.create_tab("http://127.0.0.1:5000/auth/login.html")
        ws2 = chrome.connect_tab(tab2_obj)
        time.sleep(1)
        
        # Perform Faculty login in Tab 2
        print("Logging in as Faculty (rajesh.sharma@college.edu) in Tab 2...")
        fac_login_script = """
        (async () => {
            const res = await Auth.login('rajesh.sharma@college.edu', 'password123');
            return res;
        })()
        """
        fac_login_res = chrome.evaluate(ws2, fac_login_script)
        print("Tab 2 Login response user:", fac_login_res.get('user'))
        
        # Navigate Tab 2 to faculty dashboard
        chrome.navigate(ws2, "http://127.0.0.1:5000/faculty/dashboard.html")
        time.sleep(1)
        
        tab2_user = chrome.evaluate(ws2, "localStorage.getItem('user')")
        tab2_header_name = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-name')?.textContent")
        tab2_header_role = chrome.evaluate(ws2, "document.querySelector('.user-dropdown .user-role')?.textContent")
        print(f"\n[Tab 2 State (Faculty)]")
        print(f"  Header Name: {tab2_header_name}")
        print(f"  Header Role: {tab2_header_role}")
        print(f"  localStorage user: {tab2_user}")

        # NOW INSPECT TAB 1 AGAIN!
        print("\n--- INSPECTING TAB 1 AFTER FACULTY LOGIN IN TAB 2 ---")
        tab1_after_user = chrome.evaluate(ws1, "localStorage.getItem('user')")
        tab1_after_token = chrome.evaluate(ws1, "localStorage.getItem('accessToken')")
        print(f"  Tab 1 localStorage user is now: {tab1_after_user}")
        print(f"  Did Tab 1 token change? {tab1_token != tab1_after_token}")
        
        # Check what Tab 1 header looks like BEFORE any action in Tab 1
        h_name = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent")
        h_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent")
        print(f"  Tab 1 Header Name before refresh: {h_name}")
        print(f"  Tab 1 Header Role before refresh: {h_role}")

        # Now test 1: What happens if Tab 1 makes an API request? (e.g. clicking Save or calling apiFetch)
        print("\n[Test 1] What happens if Tab 1 makes an Admin API call with the new token?")
        api_test = """
        (async () => {
            try {
                const res = await apiFetch('/permissions');
                return { success: true, data: res };
            } catch (err) {
                return { success: false, status: err.status, message: err.message };
            }
        })()
        """
        api_res = chrome.evaluate(ws1, api_test)
        print("  Tab 1 API call to /permissions result:", api_res)

        # Now test 2: What happens if Tab 1 calls updateNavbarUser()? (e.g. if page re-runs or updates)
        print("\n[Test 2] If updateNavbarUser() runs in Tab 1:")
        chrome.evaluate(ws1, "updateNavbarUser()")
        h_name_after = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent")
        h_role_after = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent")
        print(f"  Tab 1 Header Name after updateNavbarUser(): {h_name_after}")
        print(f"  Tab 1 Header Role after updateNavbarUser(): {h_role_after}")

        # Now test 3: What happens if Tab 1 reloads (or user refreshes Tab 1)?
        print("\n[Test 3] What happens when user refreshes Tab 1 (admin/roles/permissions.html)?")
        chrome.navigate(ws1, "http://127.0.0.1:5000/admin/roles/permissions.html")
        time.sleep(2)
        tab1_reloaded_url = chrome.evaluate(ws1, "window.location.href")
        tab1_reloaded_h_name = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent")
        tab1_reloaded_h_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent")
        tab1_reloaded_sidebar = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent")
        print(f"  Tab 1 URL after refresh: {tab1_reloaded_url}")
        print(f"  Tab 1 Header Name: {tab1_reloaded_h_name}")
        print(f"  Tab 1 Header Role: {tab1_reloaded_h_role}")
        print(f"  Tab 1 Sidebar Title: {tab1_reloaded_sidebar}")

        # Now test 4: What happens if Tab 1 user navigates to an admin page or subjects page?
        print("\n[Test 4] What happens if Tab 1 navigates to /subjects/list.html?")
        chrome.navigate(ws1, "http://127.0.0.1:5000/subjects/list.html")
        time.sleep(1)
        sub_url = chrome.evaluate(ws1, "window.location.href")
        sub_h_name = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-name')?.textContent")
        sub_h_role = chrome.evaluate(ws1, "document.querySelector('.user-dropdown .user-role')?.textContent")
        sub_sidebar = chrome.evaluate(ws1, "document.querySelector('.nav-section-title')?.textContent")
        print(f"  URL: {sub_url}")
        print(f"  Header Name: {sub_h_name}")
        print(f"  Header Role: {sub_h_role}")
        print(f"  Sidebar Title: {sub_sidebar}")

        # Now test 5: What happens when 401 Session Expired triggers?
        print("\n[Test 5] What happens if 401 occurs in one tab?")
        clear_test = """
        (async () => {
            // Simulate 401 handling
            localStorage.removeItem('accessToken');
            localStorage.removeItem('sessionId');
            localStorage.removeItem('user');
        })()
        """
        chrome.evaluate(ws2, clear_test)
        print("  Tab 2 cleared localStorage on logout/401")
        print("  Tab 1 localStorage user now:", chrome.evaluate(ws1, "localStorage.getItem('user')"))
        print("  Tab 1 localStorage token now:", chrome.evaluate(ws1, "localStorage.getItem('accessToken')"))

    finally:
        chrome.stop()

if __name__ == "__main__":
    run()
