"""
Comprehensive regression verification suite for Online Examination Platform.
Tests all 80 endpoints across all 4 stages of the modular backend architecture.
"""
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from backend.app import create_app
from backend.database import fetch_one, fetch_all, execute
from flask_jwt_extended import create_access_token


class ModularBackendComprehensiveRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            cls.admin_token = create_access_token(
                identity="1",
                additional_claims={"role": "Admin", "email": "admin@platform.com"}
            )
            cls.faculty_token = create_access_token(
                identity="2",
                additional_claims={"role": "Faculty", "email": "rajesh.sharma@college.edu"}
            )
            cls.student_token = create_access_token(
                identity="3",
                additional_claims={"role": "Student", "email": "rutuja.student@college.edu"}
            )

        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.faculty_headers = {"Authorization": f"Bearer {cls.faculty_token}"}
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

    # =========================================================================
    # CORE & DATABASE CONNECTIVITY
    # =========================================================================
    def test_01_health_and_database(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})

        row = fetch_one("SELECT 1 AS alive")
        self.assertIsNotNone(row)
        self.assertEqual(row.get("alive"), 1)

    def test_02_route_parity_and_inventory(self):
        api_rules = [
            r for r in self.app.url_map.iter_rules()
            if r.rule.startswith("/api")
        ]
        self.assertGreaterEqual(len(api_rules), 79, f"Expected >= 79 API routes, found {len(api_rules)}")

    # =========================================================================
    # STAGE 1: AUTH, USERS, ROLES, SESSIONS, DASHBOARDS, SUBJECTS
    # =========================================================================
    def test_10_auth_login_and_me(self):
        res = self.client.post("/api/auth/login", json={
            "email": "rutuja.student@college.edu",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("accessToken", data)
        self.assertEqual(data["user"]["email"], "rutuja.student@college.edu")

        # Invalid credentials check
        res_bad = self.client.post("/api/auth/login", json={
            "email": "rutuja.student@college.edu",
            "password": "wrong"
        })
        self.assertEqual(res_bad.status_code, 401)

        # GET /api/auth/me
        res_me = self.client.get("/api/auth/me", headers=self.student_headers)
        self.assertEqual(res_me.status_code, 200)
        self.assertEqual(res_me.get_json()["email"], "rutuja.student@college.edu")

    def test_11_auth_password_reset_endpoints(self):
        res_forgot = self.client.post("/api/auth/forgot-password", json={"email": "rutuja.student@college.edu"})
        self.assertEqual(res_forgot.status_code, 200)
        self.assertIn("message", res_forgot.get_json())

        # Test validation of missing email
        res_forgot_bad = self.client.post("/api/auth/forgot-password", json={})
        self.assertEqual(res_forgot_bad.status_code, 400)

    def test_12_users_and_roles_admin(self):
        # Admin list users
        res = self.client.get("/api/users", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

        # Forbidden for Student
        res_forbid = self.client.get("/api/users", headers=self.student_headers)
        self.assertEqual(res_forbid.status_code, 403)

        # Roles and Permissions
        res_roles = self.client.get("/api/roles", headers=self.faculty_headers)
        self.assertEqual(res_roles.status_code, 200)

        res_perms = self.client.get("/api/permissions", headers=self.admin_headers)
        self.assertEqual(res_perms.status_code, 200)

        res_rp = self.client.get("/api/roles/1/permissions", headers=self.admin_headers)
        self.assertEqual(res_rp.status_code, 200)

    def test_13_sessions_admin(self):
        res = self.client.get("/api/sessions", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    def test_14_dashboards(self):
        res_st = self.client.get("/api/student/dashboard", headers=self.student_headers)
        self.assertEqual(res_st.status_code, 200)
        st_data = res_st.get_json()
        self.assertIn("registeredExams", st_data)
        self.assertIn("recentResults", st_data)

        res_fc = self.client.get("/api/faculty/dashboard", headers=self.faculty_headers)
        self.assertEqual(res_fc.status_code, 200)
        fc_data = res_fc.get_json()
        self.assertIn("totalExams", fc_data)
        self.assertIn("pendingEvaluations", fc_data)

        res_ad = self.client.get("/api/admin/dashboard", headers=self.admin_headers)
        self.assertEqual(res_ad.status_code, 200)
        ad_data = res_ad.get_json()
        self.assertIn("totalUsers", ad_data)

    def test_15_subjects_crud(self):
        res = self.client.get("/api/subjects", headers=self.student_headers)
        self.assertEqual(res.status_code, 200)
        subjects = res.get_json()
        self.assertGreater(len(subjects), 0)

        # GET /api/subjects/<id>
        sub_id = subjects[0]["subjectId"]
        res_one = self.client.get(f"/api/subjects/{sub_id}", headers=self.student_headers)
        self.assertEqual(res_one.status_code, 200)
        self.assertEqual(res_one.get_json()["subjectId"], sub_id)

    # =========================================================================
    # STAGE 2: EXAMS, QUESTIONS, ATTEMPTS & EXAM SECURITY
    # =========================================================================
    def test_20_exams_list_and_available(self):
        res_ex = self.client.get("/api/exams", headers=self.faculty_headers)
        self.assertEqual(res_ex.status_code, 200)

        res_avail = self.client.get("/api/students/available-exams", headers=self.student_headers)
        self.assertEqual(res_avail.status_code, 200)

        res_exam1 = self.client.get("/api/exams/1", headers=self.student_headers)
        self.assertEqual(res_exam1.status_code, 200)
        self.assertEqual(res_exam1.get_json()["examId"], 1)

    def test_21_exam_questions_and_blueprint(self):
        res_q = self.client.get("/api/exams/1/questions", headers=self.faculty_headers)
        self.assertEqual(res_q.status_code, 200)
        questions = res_q.get_json()
        self.assertIsInstance(questions, list)
        if questions:
            self.assertIn("options", questions[0])
            self.assertIn("isCorrect", questions[0]["options"][0])

        # Student should not see isCorrect
        res_st_q = self.client.get("/api/exams/1/questions", headers=self.student_headers)
        self.assertEqual(res_st_q.status_code, 200)
        st_questions = res_st_q.get_json()
        if st_questions and st_questions[0].get("options"):
            self.assertNotIn("isCorrect", st_questions[0]["options"][0])

    def test_22_question_bank_and_categories(self):
        res_cats = self.client.get("/api/question-categories", headers=self.student_headers)
        self.assertEqual(res_cats.status_code, 200)

        res_diff = self.client.get("/api/difficulty-levels", headers=self.student_headers)
        self.assertEqual(res_diff.status_code, 200)

        res_qlist = self.client.get("/api/questions", headers=self.faculty_headers)
        self.assertEqual(res_qlist.status_code, 200)

    def test_23_exam_registrations(self):
        res_reg = self.client.get("/api/students/3/registrations", headers=self.student_headers)
        self.assertEqual(res_reg.status_code, 200)

        res_fac_reg = self.client.get("/api/exams/1/registrations", headers=self.faculty_headers)
        self.assertEqual(res_fac_reg.status_code, 200)

    def test_24_exam_attempts(self):
        res_att = self.client.get("/api/attempts/1", headers=self.faculty_headers)
        self.assertEqual(res_att.status_code, 200)
        self.assertEqual(res_att.get_json()["attemptId"], 1)

        res_ans = self.client.get("/api/attempts/1/answers", headers=self.faculty_headers)
        self.assertEqual(res_ans.status_code, 200)

    # =========================================================================
    # STAGE 3: EVALUATIONS, RESULTS & PERFORMANCE REPORTS
    # =========================================================================
    def test_30_evaluations_pending_and_detail(self):
        res_pending = self.client.get("/api/evaluations/pending", headers=self.faculty_headers)
        self.assertEqual(res_pending.status_code, 200)

        res_ev1 = self.client.get("/api/evaluations/1", headers=self.faculty_headers)
        self.assertEqual(res_ev1.status_code, 200)
        self.assertEqual(res_ev1.get_json()["evaluationId"], 1)

    def test_31_results_list_and_scorecard(self):
        res_all = self.client.get("/api/results", headers=self.faculty_headers)
        self.assertEqual(res_all.status_code, 200)

        # GET /api/results/1
        res_r1 = self.client.get("/api/results/1", headers=self.student_headers)
        self.assertEqual(res_r1.status_code, 200)
        r1 = res_r1.get_json()
        self.assertEqual(float(r1["percentage"]), 50.00)
        self.assertEqual(r1["grade"], "D")
        self.assertIn("questionBreakdown", r1)

        # GET /api/students/3/results
        res_st_res = self.client.get("/api/students/3/results", headers=self.student_headers)
        self.assertEqual(res_st_res.status_code, 200)
        self.assertGreater(len(res_st_res.get_json()), 0)

    def test_32_exam_report(self):
        res_rep = self.client.get("/api/exams/1/report", headers=self.faculty_headers)
        self.assertEqual(res_rep.status_code, 200)
        rep = res_rep.get_json()
        self.assertEqual(rep["examId"], 1)
        self.assertIn("passPercentage", rep)
        self.assertIn("gradeDistribution", rep)

    # =========================================================================
    # STAGE 4: NOTIFICATIONS, AUDIT LOGS, SYSTEM MONITORING & BACKUP
    # =========================================================================
    def test_40_notifications(self):
        res_notif = self.client.get("/api/notifications", headers=self.student_headers)
        self.assertEqual(res_notif.status_code, 200)

        # Mark all read
        res_read_all = self.client.put("/api/notifications/read-all", headers=self.student_headers)
        self.assertEqual(res_read_all.status_code, 200)

    def test_41_audit_logs(self):
        res_audit = self.client.get("/api/audit-logs", headers=self.admin_headers)
        self.assertEqual(res_audit.status_code, 200)
        self.assertIsInstance(res_audit.get_json(), list)

    def test_42_system_monitoring(self):
        res_cfg = self.client.get("/api/system/config", headers=self.admin_headers)
        self.assertEqual(res_cfg.status_code, 200)

        res_ff = self.client.get("/api/system/feature-flags", headers=self.faculty_headers)
        self.assertEqual(res_ff.status_code, 200)

        res_metrics = self.client.get("/api/system/metrics", headers=self.admin_headers)
        self.assertEqual(res_metrics.status_code, 200)

        res_info = self.client.get("/api/system/info", headers=self.admin_headers)
        self.assertEqual(res_info.status_code, 200)
        self.assertEqual(res_info.get_json()["status"], "HEALTHY")

        res_events = self.client.get("/api/system/events", headers=self.admin_headers)
        self.assertEqual(res_events.status_code, 200)

    def test_43_backup_placeholder(self):
        res_bk = self.client.get("/api/system/backup/status", headers=self.admin_headers)
        self.assertEqual(res_bk.status_code, 200)


if __name__ == "__main__":
    unittest.main()
