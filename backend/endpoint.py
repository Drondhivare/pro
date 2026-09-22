"""
endpoint.py (Backward Compatibility Facade)
===========================================
This file previously contained all 79 routes and helper functions in a single 2,179-line monolith.
The architecture has been modularized into:
  - backend/routes/      (HTTP controllers & blueprints)
  - backend/services/    (Domain & business logic)
  - backend/models/      (Database data access queries)
  - backend/utils/       (Validators and common helpers)

This facade re-exports the master `api` blueprint and core evaluation helpers to maintain
100% backward compatibility for existing scripts, tests, and tools.
"""
from routes import api
from services.evaluation_service import calculate_grade_and_pass, auto_grade_internal

__all__ = ["api", "calculate_grade_and_pass", "auto_grade_internal"]
