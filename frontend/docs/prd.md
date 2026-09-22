# PRD — Online Examination Platform (Frontend)

**Version:** 1.0  
**Status:** Draft  
**Scope:** Frontend / Presentation Layer Only

---

## 1. Product Overview

The Online Examination Platform is a web-based application that enables educational institutions to conduct, manage, and evaluate online examinations. The frontend provides the **Presentation Layer** — all user-facing interfaces for three distinct user roles.

This PRD covers the frontend deliverables **only**. Backend (Flask/Python) and Database (MySQL 8) are handled by separate teams.

---

## 2. Target Users

| Role | Description | Key Activities |
|---|---|---|
| **Admin** | Full platform administrator | User management, RBAC, system config, monitoring, audit logs |
| **Faculty** | Creates exams, evaluates students | Question bank CRUD, exam design & scheduling, manual evaluation, result publishing |
| **Student** | Takes online exams | Exam registration, live exam taking, result viewing, notifications |

---

## 3. Tech Stack

- **HTML5** — Semantic markup
- **CSS3 + Bootstrap 5** — Responsive styling and components
- **Vanilla JavaScript** — Interactivity, AJAX calls to Flask REST endpoints
- **Google Fonts** — Inter (body), JetBrains Mono (code)
- **Chart.js** (optional) — Analytics and reporting charts

---

## 4. Functional Requirements

### 4.1 Authentication (All Roles)
- FR-01: Login page with email/password
- FR-02: Student self-registration
- FR-03: Password reset flow
- FR-04: Session timeout warning (configurable)
- FR-05: Account locked notification after failed attempts

### 4.2 Admin — User Management
- FR-10: List all users with search, filter by role/status, pagination
- FR-11: Create/Edit/Deactivate users
- FR-12: View user login history
- FR-13: Manage roles and permissions (RBAC matrix)
- FR-14: View and invalidate active sessions

### 4.3 Admin — System Administration
- FR-20: View and edit system configuration (key-value pairs)
- FR-21: Manage feature flags (toggle enable/disable, rollout %)
- FR-22: View audit logs with filtering
- FR-23: View system events with severity indicators
- FR-24: View performance metrics
- FR-25: Manage notification templates

### 4.4 Faculty — Question Bank
- FR-30: List questions with filters (category, difficulty, type, status)
- FR-31: Create questions — dynamic form based on type (MCQ, MSQ, TRUE_FALSE, SHORT_ANSWER, DESCRIPTIVE, CODING)
- FR-32: For MCQ/MSQ: dynamic option editor with add/remove, correct answer toggle
- FR-33: Edit and deactivate questions
- FR-34: Manage question categories
- FR-35: View difficulty levels

### 4.5 Faculty — Exam Administration
- FR-40: List exams with status filters
- FR-41: Create exam — multi-step wizard (basic info → config → question selection → schedule)
- FR-42: Assign questions to exam from bank — with search, drag-and-drop ordering
- FR-43: Schedule exam with time windows and registration period
- FR-44: View registered candidates
- FR-45: Manage exam status transitions (DRAFT → SCHEDULED → ACTIVE → COMPLETED)

### 4.6 Faculty — Evaluation
- FR-50: View pending evaluations
- FR-51: Evaluate student attempts — auto-evaluated results for MCQ/MSQ/TRUE_FALSE; manual marking for DESCRIPTIVE/CODING
- FR-52: Finalize and publish results (individual or bulk)

### 4.7 Student — Exam Lifecycle
- FR-60: View available exams for registration
- FR-61: Register for exam
- FR-62: View registered exams with schedule
- FR-63: Pre-exam lobby with instructions and system check
- FR-64: **Live exam interface** — timer, question navigation palette, answer submission, mark for review, auto-save
- FR-65: Pre-submission review screen
- FR-66: Auto-submit on timer expiry
- FR-67: Post-submission confirmation

### 4.8 Student — Results
- FR-70: View all published results (percentage, grade, pass/fail)
- FR-71: Detailed result — question-wise breakdown with marks and remarks

### 4.9 Notifications (All Roles)
- FR-80: Notification dropdown in navbar (unread count badge)
- FR-81: Full notification center with type/priority filters
- FR-82: Mark as read

### 4.10 Reporting (Faculty/Admin)
- FR-90: Exam-level analytics (pass/fail distribution, average score, question accuracy)
- FR-91: Student performance reports

---

## 5. Non-Functional Requirements

| Requirement | Target |
|---|---|
| **Responsiveness** | Desktop (1920px), Laptop (1366px), Tablet (768px), Mobile (375px) |
| **Browser Support** | Chrome 90+, Firefox 90+, Edge 90+ |
| **Page Load** | < 2 seconds on 4G connection |
| **Accessibility** | WCAG 2.1 Level AA — keyboard navigation, ARIA labels, color contrast |
| **Dark Mode** | Primary theme; optional light mode toggle |
| **Form Validation** | Client-side validation for all inputs before AJAX submission |
| **Live Exam Stability** | Timer must be accurate; auto-save every 30s; graceful handling of network interruptions |

---

## 6. Design Principles

1. **Premium aesthetic** — Not a basic Bootstrap template. Custom design tokens, glassmorphism, gradients.
2. **Consistency** — Reusable components (cards, tables, forms, modals) across all pages.
3. **Clarity** — Clear information hierarchy, proper typography scale.
4. **Feedback** — Loading states, success/error toasts, form validation messages.
5. **Security-aware** — CSRF tokens in forms, no sensitive data in client-side code.

---

## 7. Success Metrics

- All 3 user roles can complete their primary workflows end-to-end
- Live exam interface handles timer, navigation, and auto-submit correctly
- Responsive on all target screen sizes
- Consistent visual design across all pages
- Backend team can integrate templates with Flask/Jinja2 without major restructuring

---

## 8. Out of Scope

- Backend API development (Flask routes, business logic)
- Database operations (SQLAlchemy queries)
- Authentication/Authorization logic (session management, RBAC enforcement)
- Deployment (Docker, Gunicorn, Nginx)
- Email/SMS notification delivery
- Backup & restore functionality
- AI proctoring
- Mobile native app
