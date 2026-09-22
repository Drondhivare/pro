# UI Component Guide — Online Examination Platform

**Version:** 1.0

---

## 1. Card Components

### 1.1 KPI Card (Dashboard)
Used for at-a-glance metrics on dashboards.

```html
<div class="kpi-card">
  <div class="kpi-card__icon" style="--icon-color: var(--color-accent-blue)">
    <i class="bi bi-people"></i>
  </div>
  <div class="kpi-card__content">
    <span class="kpi-card__value">1,247</span>
    <span class="kpi-card__label">Total Students</span>
  </div>
  <span class="kpi-card__trend kpi-card__trend--up">+12%</span>
</div>
```

### 1.2 Exam Card
Used in exam listings (student available exams, faculty exam list).

```html
<div class="exam-card">
  <div class="exam-card__header">
    <span class="badge badge--status-draft">DRAFT</span>
    <span class="exam-card__code">EXAM-DBMS-MID</span>
  </div>
  <h3 class="exam-card__title">DBMS Mid-Term Assessment</h3>
  <div class="exam-card__meta">
    <span><i class="bi bi-clock"></i> 60 min</span>
    <span><i class="bi bi-trophy"></i> 100 marks</span>
    <span><i class="bi bi-question-circle"></i> 25 questions</span>
  </div>
  <div class="exam-card__actions">
    <button class="btn btn-primary btn-sm">View Details</button>
  </div>
</div>
```

---

## 2. Table Components

### 2.1 Data Table
Standard paginated, sortable table for lists (users, questions, results).

```html
<div class="data-table-wrapper">
  <div class="data-table__toolbar">
    <input type="search" class="form-control" placeholder="Search...">
    <select class="form-select">
      <option>All Roles</option>
      <option>Admin</option>
      <option>Faculty</option>
      <option>Student</option>
    </select>
  </div>
  <table class="data-table">
    <thead>
      <tr>
        <th class="sortable">Name <i class="bi bi-arrow-down-up"></i></th>
        <th>Email</th>
        <th>Role</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <!-- Rows -->
    </tbody>
  </table>
  <div class="data-table__footer">
    <!-- Pagination component -->
  </div>
</div>
```

---

## 3. Form Components

### 3.1 Standard Form
All forms follow this pattern with validation states.

```html
<form class="form-panel" method="POST" action="{{ url_for('...') }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  
  <div class="form-group">
    <label class="form-label" for="examTitle">Exam Title *</label>
    <input type="text" class="form-control" id="examTitle" name="examTitle" 
           required minlength="3" maxlength="150">
    <div class="invalid-feedback">Exam title must be 3-150 characters.</div>
  </div>
  
  <div class="form-actions">
    <button type="submit" class="btn btn-primary">Save</button>
    <a href="{{ url_for('...') }}" class="btn btn-outline-secondary">Cancel</a>
  </div>
</form>
```

### 3.2 Dynamic Option Editor (Question Creation)
For MCQ/MSQ question types — allows adding/removing options.

```html
<div class="option-editor" id="optionEditor">
  <div class="option-editor__item">
    <span class="option-editor__label">A</span>
    <input type="text" class="form-control" name="options[]" placeholder="Option text">
    <div class="form-check">
      <input class="form-check-input" type="checkbox" name="correct[]" value="0">
      <label class="form-check-label">Correct</label>
    </div>
    <button type="button" class="btn btn-icon btn-danger-ghost" onclick="removeOption(this)">
      <i class="bi bi-trash"></i>
    </button>
  </div>
  <!-- More options... -->
  <button type="button" class="btn btn-outline-primary btn-sm" onclick="addOption()">
    <i class="bi bi-plus"></i> Add Option
  </button>
</div>
```

---

## 4. Navigation Components

### 4.1 Sidebar

```html
<aside class="sidebar" id="sidebar">
  <div class="sidebar__brand">
    <img src="/static/img/logo.svg" alt="Logo">
    <span>ExamPlatform</span>
  </div>
  <nav class="sidebar__nav">
    <a href="/dashboard" class="sidebar__link sidebar__link--active">
      <i class="bi bi-grid"></i>
      <span>Dashboard</span>
    </a>
    <!-- Role-specific menu items -->
  </nav>
  <div class="sidebar__footer">
    <span class="sidebar__version">v1.0</span>
  </div>
</aside>
```

### 4.2 Question Navigation Palette (Live Exam)

```html
<div class="question-palette">
  <h4 class="question-palette__title">Questions</h4>
  <div class="question-palette__grid">
    <button class="q-btn q-btn--answered" data-q="1">1</button>
    <button class="q-btn q-btn--unanswered" data-q="2">2</button>
    <button class="q-btn q-btn--review" data-q="3">3</button>
    <button class="q-btn q-btn--current" data-q="4">4</button>
    <!-- ... -->
  </div>
  <div class="question-palette__legend">
    <span class="legend-item"><span class="dot dot--answered"></span> Answered</span>
    <span class="legend-item"><span class="dot dot--unanswered"></span> Not Answered</span>
    <span class="legend-item"><span class="dot dot--review"></span> Marked for Review</span>
    <span class="legend-item"><span class="dot dot--current"></span> Current</span>
  </div>
</div>
```

---

## 5. Status Badge System

| Status | CSS Class | Color |
|---|---|---|
| DRAFT | `badge--status-draft` | Gray |
| SCHEDULED | `badge--status-scheduled` | Blue |
| ACTIVE / ONGOING | `badge--status-active` | Green |
| COMPLETED | `badge--status-completed` | Purple |
| CANCELLED | `badge--status-cancelled` | Red |
| PENDING | `badge--status-pending` | Amber |
| PASSED | `badge--status-passed` | Green |
| FAILED | `badge--status-failed` | Red |

---

## 6. Notification Types

| Type | Icon | Color |
|---|---|---|
| EXAM | `bi-journal-text` | Blue |
| RESULT | `bi-award` | Green |
| SYSTEM | `bi-gear` | Gray |
| REMINDER | `bi-bell` | Amber |
| SECURITY | `bi-shield-exclamation` | Red |

---

## 7. Toast Notifications

```javascript
// Usage
showToast('success', 'Exam created successfully!');
showToast('error', 'Failed to save question.');
showToast('warning', 'Session expiring in 5 minutes.');
showToast('info', 'New notification received.');
```

---

## 8. Loading States

Every AJAX operation should show a loading state:

```html
<!-- Button loading -->
<button class="btn btn-primary" disabled>
  <span class="spinner-border spinner-border-sm" role="status"></span>
  Saving...
</button>

<!-- Table skeleton loading -->
<div class="skeleton-table">
  <div class="skeleton-row"></div>
  <div class="skeleton-row"></div>
  <div class="skeleton-row"></div>
</div>
```
