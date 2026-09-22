"""
Master API Blueprint aggregating all modular route blueprints.
"""
from flask import Blueprint

from routes.auth import auth_bp
from routes.users import users_bp
from routes.subjects import subjects_bp
from routes.exams import exams_bp
from routes.questions import questions_bp
from routes.attempts import attempts_bp
from routes.evaluations import evaluations_bp
from routes.results import results_bp
from routes.reports import reports_bp
from routes.notifications import notifications_bp
from routes.audit import audit_bp
from routes.monitoring import monitoring_bp
from routes.backup import backup_bp

api = Blueprint("api", __name__)

ALL_BLUEPRINTS = [
    auth_bp,
    users_bp,
    subjects_bp,
    exams_bp,
    questions_bp,
    attempts_bp,
    evaluations_bp,
    results_bp,
    reports_bp,
    notifications_bp,
    audit_bp,
    monitoring_bp,
    backup_bp,
]

for bp in ALL_BLUEPRINTS:
    api.register_blueprint(bp)
