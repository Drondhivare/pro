# Frontend Architecture — Online Examination Platform

**Version:** 1.0  
**Layer:** Presentation Layer (of the Layered Modular Monolith defined in ADP-003)

---

## 1. Architecture Overview

The frontend follows the **Presentation Layer** responsibilities as defined in the project's ADP-003 (Layered Software Architecture):

- User Interface rendering
- HTTP Request Handling (via Flask route templates)
- Session Validation (display-level)
- Input Collection
- Response Rendering

> **Critical Constraint (ADP-003):** The Presentation Layer **must not** contain business rules, database logic, or complex validation. These belong in the Application/Domain/Persistence layers handled by the backend team.

---

## 2. Template Architecture

### 2.1 Template Hierarchy

```
base.html                          ← Master layout (sidebar + navbar + content area)
├── auth/login.html                ← Standalone (no sidebar)
├── auth/register.html             ← Standalone
├── admin/dashboard.html           ← Extends base.html
├── faculty/dashboard.html         ← Extends base.html
├── student/dashboard.html         ← Extends base.html
├── exam_runtime/exam.html         ← Fullscreen layout (no sidebar, custom nav)
└── ... (all other pages)          ← Extends base.html
```

### 2.2 Template Blocks

The `base.html` template defines these Jinja2 blocks for child templates:

```html
{% block title %}{% endblock %}        <!-- Page title -->
{% block breadcrumb %}{% endblock %}    <!-- Breadcrumb trail -->
{% block content %}{% endblock %}       <!-- Main content area -->
{% block modals %}{% endblock %}        <!-- Page-specific modals -->
{% block scripts %}{% endblock %}       <!-- Page-specific JS -->
```

### 2.3 Include Components

Reusable UI fragments included via `{% include %}`:

| Component | Path | Usage |
|---|---|---|
| Sidebar | `components/sidebar.html` | Role-aware navigation menu |
| Navbar | `components/navbar.html` | Top bar with search, notifications, user menu |
| Notification Dropdown | `components/notifications_dropdown.html` | Real-time notification bell |
| Pagination | `components/pagination.html` | Reusable table pagination |
| Confirm Modal | `components/confirm_modal.html` | Generic confirmation dialog |
| Toast Container | `components/toast_container.html` | Success/error/warning toast stack |

---

## 3. CSS Architecture

### 3.1 File Organization

```
static/css/
├── styles.css          ← All custom styles (design system + component + page overrides)
```

### 3.2 Design Tokens (CSS Custom Properties)

```css
:root {
  /* Colors */
  --color-bg-primary: #0f1117;
  --color-bg-secondary: #1a1d29;
  --color-bg-card: rgba(255, 255, 255, 0.05);
  --color-accent-blue: #3b82f6;
  --color-accent-green: #10b981;
  --color-accent-amber: #f59e0b;
  --color-accent-red: #ef4444;
  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;
  --color-border: rgba(255, 255, 255, 0.1);

  /* Typography */
  --font-body: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Borders */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;

  /* Shadows */
  --shadow-card: 0 4px 24px rgba(0, 0, 0, 0.3);
  --shadow-glow: 0 0 20px rgba(59, 130, 246, 0.15);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
  --transition-slow: 400ms ease;
}
```

### 3.3 Naming Convention

CSS classes follow BEM-inspired naming:
- `.exam-card` — Block
- `.exam-card__title` — Element
- `.exam-card--active` — Modifier
- Bootstrap utility classes are used for spacing, grid, and basic layout

---

## 4. JavaScript Architecture

### 4.1 File Organization

```
static/js/
├── app.js              ← Shared utilities (AJAX, toasts, modals, form validation)
├── exam_timer.js       ← Countdown timer logic for live exam
└── exam_engine.js      ← Exam navigation, answer state, auto-save
```

### 4.2 AJAX Communication

All dynamic operations use `fetch()` with JSON payloads:

```javascript
// Pattern for AJAX calls
async function apiCall(url, method = 'GET', data = null) {
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    }
  };
  if (data) options.body = JSON.stringify(data);
  
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(response.statusText);
  return response.json();
}
```

### 4.3 Live Exam State Machine

The exam engine manages states:

```
NOT_STARTED → IN_PROGRESS → SUBMITTED
                    ↓
              AUTO_SUBMITTED (on timer expiry)
```

---

## 5. Responsive Breakpoints

| Breakpoint | Width | Layout |
|---|---|---|
| Desktop | ≥ 1200px | Sidebar expanded + 3-column content |
| Laptop | ≥ 992px | Sidebar collapsed + 2-column content |
| Tablet | ≥ 768px | Sidebar hidden (hamburger) + 1-column |
| Mobile | < 768px | Full-width stacked layout |

---

## 6. Role-Based UI Rules

| UI Element | Admin | Faculty | Student |
|---|---|---|---|
| Sidebar: Users/Roles | ✅ | ❌ | ❌ |
| Sidebar: Question Bank | ✅ | ✅ | ❌ |
| Sidebar: Exam Management | ✅ | ✅ | ❌ |
| Sidebar: Take Exam | ❌ | ❌ | ✅ |
| Sidebar: My Results | ❌ | ❌ | ✅ |
| Sidebar: Evaluation | ❌ | ✅ | ❌ |
| Sidebar: Reports | ✅ | ✅ | ❌ |
| Sidebar: System Config | ✅ | ❌ | ❌ |
| Sidebar: Audit Logs | ✅ | ❌ | ❌ |
| Notification Bell | ✅ | ✅ | ✅ |

---

## 7. Integration Contract with Backend

The frontend team delivers **complete HTML templates** with:
- Jinja2 template blocks and variable placeholders (e.g., `{{ user.firstName }}`)
- Form `action` URLs as Flask route names (e.g., `{{ url_for('auth.login') }}`)
- CSRF token inclusion in all forms
- AJAX endpoints documented for dynamic interactions

The backend team is responsible for:
- Rendering templates via Flask routes
- Passing context variables to templates
- Implementing REST API endpoints for AJAX calls
- Session management and authentication middleware
