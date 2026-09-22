from flask import Flask, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('auth/login.html')

# Auth Routes
@app.route('/auth/login.html')
def login():
    return render_template('auth/login.html')

@app.route('/auth/register.html')
def register():
    return render_template('auth/register.html')

@app.route('/auth/forgot_password.html')
def forgot_password():
    return render_template('auth/forgot_password.html')

@app.route('/auth/reset_password.html')
def reset_password():
    return render_template('auth/reset_password.html')

# Student Portal Routes
@app.route('/student/dashboard.html')
def student_dashboard():
    return render_template('student/dashboard.html')

@app.route('/student/exams/available.html')
def student_exams_available():
    return render_template('student/exams/available.html')

@app.route('/student/exams/registered.html')
def student_exams_registered():
    return render_template('student/exams/registered.html')

@app.route('/student/results/list.html')
def student_results():
    return render_template('student/results/list.html')

@app.route('/student/results/detail.html')
def student_result_detail():
    return render_template('student/results/detail.html')

# Faculty Portal Routes
@app.route('/faculty/dashboard.html')
def faculty_dashboard():
    return render_template('faculty/dashboard.html')

@app.route('/questions/list.html')
def questions_list():
    return render_template('questions/list.html')

@app.route('/questions/create.html')
def questions_create():
    return render_template('questions/create.html')

@app.route('/questions/edit.html')
def questions_edit():
    from flask import make_response
    resp = make_response(render_template('questions/edit.html'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    return resp

@app.route('/exams/list.html')
def exams_list():
    return render_template('exams/list.html')

@app.route('/exams/create.html')
def exams_create():
    return render_template('exams/create.html')

@app.route('/exams/edit.html')
def exams_edit():
    return render_template('exams/edit.html')

@app.route('/exams/detail.html')
def exams_detail():
    return render_template('exams/detail.html')

@app.route('/exams/schedule.html')
def exams_schedule():
    return render_template('exams/schedule.html')

@app.route('/exams/questions/assign.html')
def exams_assign():
    return render_template('exams/questions/assign.html')

# Evaluation Routes
@app.route('/evaluation/pending.html')
def evaluation_pending():
    return render_template('evaluation/pending.html')

@app.route('/evaluation/evaluate.html')
def evaluation_evaluate():
    return render_template('evaluation/evaluate.html')

@app.route('/evaluation/results/list.html')
def evaluation_results_list():
    return render_template('evaluation/results/list.html')

@app.route('/evaluation/results/publish.html')
def evaluation_results_publish():
    return render_template('evaluation/results/publish.html')

# Admin Portal Routes
@app.route('/admin/dashboard.html')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/users/list.html')
def admin_users():
    return render_template('admin/users/list.html')

@app.route('/admin/users/create.html')
def admin_users_create():
    return render_template('admin/users/create.html')

@app.route('/admin/users/edit.html')
def admin_users_edit():
    return render_template('admin/users/edit.html')

@app.route('/admin/users/login_history.html')
def admin_users_login_history():
    return render_template('admin/users/login_history.html')

@app.route('/admin/sessions/list.html')
def admin_sessions():
    return render_template('admin/sessions/list.html')

@app.route('/admin/audit/list.html')
def admin_audit():
    return render_template('admin/audit/list.html')

@app.route('/admin/roles/permissions.html')
def admin_permissions():
    return render_template('admin/roles/permissions.html')

@app.route('/admin/system/metrics.html')
def admin_metrics():
    return render_template('admin/system/metrics.html')

@app.route('/admin/system/backup.html')
def admin_backup():
    return render_template('admin/system/backup.html')

# Subjects Routes
@app.route('/subjects/list.html')
def subjects_list():
    return render_template('subjects/list.html')

@app.route('/subjects/create.html')
def subjects_create():
    return render_template('subjects/create.html')

@app.route('/subjects/edit.html')
def subjects_edit():
    return render_template('subjects/edit.html')

# Reports & Notifications
@app.route('/reports/exam_report.html')
def reports_exam():
    return render_template('reports/exam_report.html')

@app.route('/notifications/center.html')
def notifications_center():
    return render_template('notifications/center.html')

# Exam Runtime Routes
@app.route('/exam_runtime/lobby.html')
def exam_lobby():
    return render_template('exam_runtime/lobby.html')

@app.route('/exam_runtime/exam.html')
def live_exam():
    return render_template('exam_runtime/exam.html')

@app.route('/exam_runtime/review.html')
def exam_review():
    return render_template('exam_runtime/review.html')

@app.route('/exam_runtime/submitted.html')
def exam_submitted():
    return render_template('exam_runtime/submitted.html')

if __name__ == '__main__':
    print("\n============================================================")
    print("Online Examination Platform - Frontend Development Server")
    print("============================================================")
    print("Running locally at: http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
