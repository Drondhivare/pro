# Online Examination Platform — Backend

A Flask REST API for the Online Examination Platform. It talks directly to
the MySQL schema defined in `schema.sql` (27 tables, 5 domains) — there's
no separate ORM model layer, so `schema.sql` is the single source of truth.

## Structure

```
backend/
├── schema.sql       # Full DB schema + seed data (provided) — source of truth
├── config.py         # Reads DB/JWT settings from .env
├── database.py        # PyMySQL connection + query helpers + schema.sql loader
├── auth_utils.py       # Password hashing + JWT role-check decorator
├── endpoint.py          # ALL API routes, organized by schema domain (A–E)
├── init_db.py            # One-time script: runs schema.sql to create DB/tables
├── app.py                 # Flask app entry point (registers endpoint.py)
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # fill in your MySQL credentials
python init_db.py         # creates online_exam_db + all 27 tables + seed data
python app.py              # starts API at http://localhost:8000
```

## Auth

- `POST /api/auth/register` — create a user (Admin/Faculty/Student via `roleId`)
- `POST /api/auth/login` — returns a JWT `accessToken`
- Send `Authorization: Bearer <token>` on all other routes.
- Role-gated routes use the `role` claim embedded in the token (Admin / Faculty / Student).

## Endpoint map (see `endpoint.py` for full detail)

| Domain | Base path | Examples |
|---|---|---|
| Identity & Access | `/api/auth`, `/api/users`, `/api/roles`, `/api/permissions` | login, register, list users |
| Academic & Exams | `/api/subjects`, `/api/exams`, `/api/exams/<id>/schedule`, `/api/exams/<id>/register` | create exam, schedule it, student registers |
| Question Bank | `/api/questions`, `/api/question-categories`, `/api/difficulty-levels` | create question with options |
| Execution & Results | `/api/exams/<id>/attempts/start`, `/api/attempts/<id>/answers`, `/api/attempts/<id>/submit`, `/api/evaluations`, `/api/results` | take exam, auto-grade, finalize, publish |
| Notifications & Admin | `/api/notifications`, `/api/audit-logs`, `/api/system/config`, `/api/system/feature-flags` | notify student, view audit trail |

## Typical exam flow

1. Faculty creates a `Subject`, then an `Exam` under it, then an `ExamSchedule`.
2. Faculty adds `Question`s (with `options` for MCQ) to the question bank, then assigns them to the exam via `/api/exams/<id>/questions`.
3. Student calls `/api/exams/<id>/register`, then `/api/exams/<id>/attempts/start`.
4. Student submits answers via `/api/attempts/<id>/answers`, then `/api/attempts/<id>/submit`.
5. Faculty runs `/api/attempts/<id>/evaluate/auto` (grades MCQ/TRUE_FALSE automatically), then manually grades any descriptive questions via `/api/evaluations/<id>/details`.
6. Faculty calls `/api/evaluations/<id>/finalize` (computes percentage/grade/pass) then `/api/results/<id>/publish`.
7. Student sees it at `/api/students/<id>/results`.

## Notes

- This is separate from the existing `frontend/` (Flask template server). Point the frontend's fetch calls at this API's base URL (e.g. `http://localhost:8000/api`), and enable CORS is already on.
- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2). The schema's sample seed rows use placeholder Argon2 hashes — re-register those demo users through `/api/auth/register` to get working logins.
