/**
 * MMCOE Online Examination Platform - Shared Application Utilities & API Client
 */

// Central API Base URL pointing to the Flask REST API backend
const API_BASE = 'http://localhost:8000/api';

/**
 * Unified API Client for REST requests with automatic JWT authentication
 */
async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {})
  };

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const token = sessionStorage.getItem('accessToken');
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers
  };

  try {
    const response = await fetch(url, config);

    // Session expired or unauthenticated
    if (response.status === 401) {
      const isAuthPage = window.location.pathname.includes('/auth/');
      if (!isAuthPage) {
        sessionStorage.removeItem('accessToken');
        sessionStorage.removeItem('sessionId');
        sessionStorage.removeItem('user');
        window.location.href = '/auth/login.html';
        const dummy = { ok: false, status: 401, json: async () => null, error: 'Session expired' };
        return dummy;
      }
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg = (data && (data.error || data.message)) || `Request failed with status ${response.status}`;
      const err = new Error(errorMsg);
      err.status = response.status;
      err.data = data;
      throw err;
    }

    if (data && typeof data === 'object') {
      try {
        if (!('ok' in data)) {
          Object.defineProperty(data, 'ok', { value: true, writable: true, configurable: true });
        }
        if (!('status' in data)) {
          Object.defineProperty(data, 'status', { value: response.status, writable: true, configurable: true });
        }
        if (!('json' in data)) {
          Object.defineProperty(data, 'json', { value: async () => data, writable: true, configurable: true });
        }
      } catch (_) {}
    }

    return data;
  } catch (err) {
    if (err.status !== 401) {
      console.error(`API Error [${options.method || 'GET'} ${endpoint}]:`, err);
    }
    throw err;
  }
}

/**
 * Global Authentication & Session Helpers
 */
const Auth = {
  async login(email, password) {
    const data = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });

    if (data && data.accessToken) {
      sessionStorage.setItem('accessToken', data.accessToken);
      sessionStorage.setItem('sessionId', data.sessionId || '');
      sessionStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
  },

  async logout() {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch (e) {
      console.warn('Logout API notification failed:', e);
    } finally {
      sessionStorage.removeItem('accessToken');
      sessionStorage.removeItem('sessionId');
      sessionStorage.removeItem('user');
      window.location.href = '/auth/login.html';
    }
  },

  getUser() {
    try {
      const userStr = sessionStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  getToken() {
    return sessionStorage.getItem('accessToken');
  },

  requireAuth(...allowedRoles) {
    const roles = allowedRoles.flat(Infinity).filter(Boolean);
    const token = this.getToken();
    const user = this.getUser();

    if (!token || !user) {
      window.location.href = '/auth/login.html';
      return null;
    }

    if (roles.length > 0 && !roles.includes(user.role)) {
      showToast(`Access restricted to ${roles.join('/')}`, 'warning');
      if (user.role === 'Student') window.location.href = '/student/dashboard.html';
      else if (user.role === 'Faculty') window.location.href = '/faculty/dashboard.html';
      else if (user.role === 'Admin') window.location.href = '/admin/dashboard.html';
      return null;
    }

    return user;
  }
};

/**
 * Toast notification trigger
 */
function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toast-container') || createToastContainer();
  
  const bgClass = type === 'success' ? 'bg-success' : 
                  type === 'danger' ? 'bg-danger' : 
                  type === 'warning' ? 'bg-warning text-dark' : 'bg-primary';

  const toastId = 'toast-' + Date.now();
  const html = `
    <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0 show shadow-sm" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">
          <i class="bi bi-info-circle-fill me-2"></i> ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;
  
  toastContainer.insertAdjacentHTML('beforeend', html);
  setTimeout(() => {
    const el = document.getElementById(toastId);
    if (el) el.remove();
  }, 4000);
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toast-container';
  div.className = 'toast-container position-fixed bottom-0 end-0 p-3';
  div.style.zIndex = '9999';
  document.body.appendChild(div);
  return div;
}

/**
 * Password visibility toggle helper
 */
function togglePasswordVisibility(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon = document.getElementById(iconId);
  if (!input) return;
  
  if (input.type === 'password') {
    input.type = 'text';
    if (icon) {
      icon.classList.remove('bi-eye');
      icon.classList.add('bi-eye-slash');
    }
  } else {
    input.type = 'password';
    if (icon) {
      icon.classList.remove('bi-eye-slash');
      icon.classList.add('bi-eye');
    }
  }
}

/**
 * Mobile sidebar toggle
 */
function toggleMobileSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) {
    sidebar.classList.toggle('show');
  }
}

/**
 * Dynamic Option Row Adder for Question Creation & Editing
 */
function addQuestionOption(text = '', isCorrect = false, isLocked = false, optionId = null) {
  const container = document.getElementById('optionsContainer');
  if (!container) return;

  const qType = document.getElementById('qTypeSelect')?.value;
  if (qType === 'TRUE_FALSE' && container.children.length >= 2) {
    return;
  }
  
  const currentCount = container.children.length;
  const optionLetter = String.fromCharCode(65 + Math.min(currentCount, 25)); // A, B, C...
  
  const div = document.createElement('div');
  div.className = 'input-group mb-2 option-row';
  div.id = `option-row-${currentCount + 1}`;
  if (optionId != null) {
    div.dataset.optionId = optionId;
  }
  div.innerHTML = `
    <span class="input-group-text bg-light text-dark font-monospace">${optionLetter}</span>
    <input type="text" class="form-control form-control-custom option-text option-text-input" placeholder="Option ${optionLetter} text" value="${escapeHtml(text)}" ${isLocked ? 'readonly' : ''} required>
    <div class="input-group-text bg-light text-dark">
      <input class="form-check-input mt-0 option-correct option-correct-check" type="checkbox" title="Mark as correct answer" ${isCorrect ? 'checked' : ''}>
      <span class="ms-1 small">Correct</span>
    </div>
    ${isLocked ? '' : `
    <button class="btn btn-outline-danger btn-remove-option" type="button" onclick="removeQuestionOption(this)">
      <i class="bi bi-trash"></i>
    </button>
    `}
  `;
  container.appendChild(div);
  reindexOptions();
}

function removeQuestionOption(btn) {
  const qType = document.getElementById('qTypeSelect')?.value;
  if (qType === 'TRUE_FALSE') return;

  const row = btn.closest('.option-row');
  if (!row) return;
  const container = document.getElementById('optionsContainer');
  if (!container) return;
  if (container.children.length <= 2) {
    showToast('A question must have at least 2 options!', 'warning');
    return;
  }
  row.remove();
  reindexOptions();
}

function reindexOptions() {
  const container = document.getElementById('optionsContainer');
  if (!container) return;
  
  Array.from(container.children).forEach((row, idx) => {
    const letter = String.fromCharCode(65 + Math.min(idx, 25));
    const span = row.querySelector('.font-monospace');
    if (span) span.textContent = letter;
    const input = row.querySelector('.option-text, .option-text-input');
    if (input && !input.readOnly) {
      input.placeholder = `Option ${letter} text`;
    }
  });
}

function isTrueFalseContainer() {
  const rows = document.querySelectorAll('#optionsContainer .option-row');
  if (rows.length === 2) {
    const text0 = (rows[0].querySelector('.option-text, .option-text-input')?.value || '').trim().toLowerCase();
    const text1 = (rows[1].querySelector('.option-text, .option-text-input')?.value || '').trim().toLowerCase();
    if ((text0 === 'true' && text1 === 'false') || (text0 === 'false' && text1 === 'true')) {
      return true;
    }
  }
  return false;
}

function buildDefaultOptions() {
  const container = document.getElementById('optionsContainer');
  if (!container) return;
  container.innerHTML = '';
  addQuestionOption('Option A', true);
  addQuestionOption('Option B', false);
  addQuestionOption('Option C', false);
  addQuestionOption('Option D', false);
}

function buildTrueFalseOptions() {
  const container = document.getElementById('optionsContainer');
  if (!container) return;
  container.innerHTML = '';
  addQuestionOption('True', true, true);
  addQuestionOption('False', false, true);
}

function setupSingleChoiceHandler() {
  const container = document.getElementById('optionsContainer');
  if (!container || container.dataset.singleChoiceBound === 'true') return;
  container.dataset.singleChoiceBound = 'true';
  container.addEventListener('change', (e) => {
    if (e.target.matches('.option-correct, .option-correct-check')) {
      const qType = document.getElementById('qTypeSelect')?.value;
      if (qType === 'MCQ') {
        if (e.target.checked) {
          const allChecks = container.querySelectorAll('.option-correct, .option-correct-check');
          allChecks.forEach(cb => {
            if (cb !== e.target) cb.checked = false;
          });
        }
      } else if (qType === 'TRUE_FALSE') {
        if (e.target.checked) {
          const allChecks = container.querySelectorAll('.option-correct, .option-correct-check');
          allChecks.forEach(cb => {
            if (cb !== e.target) cb.checked = false;
          });
        } else {
          // Ensure one option remains checked for True/False
          const allChecks = Array.from(container.querySelectorAll('.option-correct, .option-correct-check'));
          const other = allChecks.find(cb => cb !== e.target);
          if (other) {
            other.checked = true;
          } else {
            e.target.checked = true;
          }
        }
      }
    }
  });
}

window.addQuestionOption = addQuestionOption;
window.removeQuestionOption = removeQuestionOption;
window.reindexOptions = reindexOptions;
window.isTrueFalseContainer = isTrueFalseContainer;
window.buildDefaultOptions = buildDefaultOptions;
window.buildTrueFalseOptions = buildTrueFalseOptions;
window.setupSingleChoiceHandler = setupSingleChoiceHandler;

function toggleOptionSection() {
  const qTypeSelect = document.getElementById('qTypeSelect');
  if (!qTypeSelect) return;
  const nextType = qTypeSelect.value;
  const prevType = qTypeSelect.dataset.prevType || window.currentQuestionType || 'MCQ';

  const wrapper = document.getElementById('optionsWrapper');
  const btnAddOption = document.getElementById('btnAddOption');
  const container = document.getElementById('optionsContainer');
  const modelAnswerWrapper = document.getElementById('modelAnswerWrapper');
  const explanationWrapper = document.getElementById('explanationWrapper');

  if (nextType === 'DESCRIPTIVE') {
    if (wrapper) wrapper.classList.add('d-none');
    if (btnAddOption) {
      btnAddOption.classList.add('d-none');
      btnAddOption.disabled = true;
    }
    if (modelAnswerWrapper) modelAnswerWrapper.classList.remove('d-none');
    if (explanationWrapper) explanationWrapper.classList.add('d-none');
  } else if (nextType === 'TRUE_FALSE') {
    if (wrapper) wrapper.classList.remove('d-none');
    if (btnAddOption) {
      btnAddOption.classList.add('d-none');
      btnAddOption.disabled = true;
    }
    if (modelAnswerWrapper) modelAnswerWrapper.classList.add('d-none');
    if (explanationWrapper) explanationWrapper.classList.remove('d-none');
    buildTrueFalseOptions();
  } else if (nextType === 'MCQ') {
    if (wrapper) wrapper.classList.remove('d-none');
    if (btnAddOption) {
      btnAddOption.classList.remove('d-none');
      btnAddOption.disabled = false;
    }
    if (modelAnswerWrapper) modelAnswerWrapper.classList.add('d-none');
    if (explanationWrapper) explanationWrapper.classList.remove('d-none');

    // Rebuild if transitioning from TRUE_FALSE, empty, or if options are True/False
    if (container && (container.children.length === 0 || isTrueFalseContainer() || prevType === 'TRUE_FALSE')) {
      buildDefaultOptions();
    } else if (container) {
      // Keep existing options, but ensure exactly ONE is checked
      const checks = Array.from(container.querySelectorAll('.option-correct, .option-correct-check'));
      let foundChecked = false;
      checks.forEach(cb => {
        if (cb.checked) {
          if (!foundChecked) {
            foundChecked = true;
          } else {
            cb.checked = false;
          }
        }
      });
      if (!foundChecked && checks.length > 0) {
        checks[0].checked = true;
      }
    }
  } else if (nextType === 'MSQ') {
    if (wrapper) wrapper.classList.remove('d-none');
    if (btnAddOption) {
      btnAddOption.classList.remove('d-none');
      btnAddOption.disabled = false;
    }
    if (modelAnswerWrapper) modelAnswerWrapper.classList.add('d-none');
    if (explanationWrapper) explanationWrapper.classList.remove('d-none');

    // Rebuild if transitioning from TRUE_FALSE, empty, or if options are True/False
    if (container && (container.children.length === 0 || isTrueFalseContainer() || prevType === 'TRUE_FALSE')) {
      buildDefaultOptions();
    }
  }

  qTypeSelect.dataset.prevType = nextType;
  window.currentQuestionType = nextType;
}
window.toggleOptionSection = toggleOptionSection;

/**
 * Render dynamic profile in Navbar & hook logout
 */
function updateNavbarUser() {
  const user = Auth.getUser();
  if (!user) return;

  const avatarEl = document.querySelector('.user-dropdown .avatar');
  const nameEl = document.querySelector('.user-dropdown .user-name');
  const roleEl = document.querySelector('.user-dropdown .user-role');

  if (avatarEl && user.firstName) {
    avatarEl.textContent = user.firstName.charAt(0).toUpperCase();
    if (user.role === 'Admin') {
      avatarEl.style.background = 'var(--rose, #e11d48)';
    } else if (user.role === 'Faculty') {
      avatarEl.style.background = 'var(--mmcoe-navy, #1b365d)';
    } else if (user.role === 'Student') {
      avatarEl.style.background = 'var(--mmcoe-maroon, #8b152b)';
    }
  }
  if (nameEl && user.firstName) {
    nameEl.textContent = `${user.firstName} ${user.lastName || ''}`.trim();
  }
  if (roleEl && user.role) {
    roleEl.textContent = `${user.role} (ID: ${user.userId})`;
  }

  // Hook all logout links
  document.querySelectorAll('a[href*="logout"], a[href*="login.html"]').forEach(link => {
    if (link.textContent.toLowerCase().includes('logout')) {
      link.removeAttribute('href');
      link.style.cursor = 'pointer';
      link.onclick = (e) => {
        e.preventDefault();
        Auth.logout();
      };
    }
  });
}

/**
 * Dynamic Role-aware Sidebar for shared/multi-role views (Subjects, Notifications, Reports)
 */
function updateRoleSidebar() {
  const user = Auth.getUser();
  if (!user || !user.role) return;

  const sidebarNav = document.querySelector('.sidebar .sidebar-nav');
  if (!sidebarNav) return;

  const currentPath = window.location.pathname;

  // We now dynamically build the sidebar for ALL routes to ensure consistency
  // and fix missing items across different pages.

  // Update brand link to point to the user's dashboard
  const brandLink = document.querySelector('.sidebar-header a.sidebar-brand');
  if (brandLink) {
    if (user.role === 'Admin') brandLink.setAttribute('href', '/admin/dashboard.html');
    else if (user.role === 'Faculty') brandLink.setAttribute('href', '/faculty/dashboard.html');
    else if (user.role === 'Student') brandLink.setAttribute('href', '/student/dashboard.html');
  }

  if (user.role === 'Admin') {
    sidebarNav.innerHTML = `
      <div class="nav-section-title">Administrator Portal</div>
      <div class="nav-item">
        <a href="/admin/dashboard.html" class="nav-link ${currentPath === '/admin/dashboard.html' ? 'active' : ''}">
          <i class="bi bi-grid-1x2-fill"></i>
          <span>Dashboard</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/admin/users/list.html" class="nav-link ${currentPath.includes('/users/') ? 'active' : ''}">
          <i class="bi bi-people-fill"></i>
          <span>User Management</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/admin/roles/permissions.html" class="nav-link ${currentPath.includes('/roles/') ? 'active' : ''}">
          <i class="bi bi-shield-lock-fill"></i>
          <span>RBAC Matrix</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/subjects/list.html" class="nav-link ${currentPath.includes('/subjects/') ? 'active' : ''}">
          <i class="bi bi-book-fill"></i>
          <span>Subjects</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/admin/system/metrics.html" class="nav-link ${currentPath.includes('/metrics') ? 'active' : ''}">
          <i class="bi bi-cpu-fill"></i>
          <span>System Health & Flags</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/admin/system/backup.html" class="nav-link ${currentPath.includes('/backup') ? 'active' : ''}">
          <i class="bi bi-database-fill-gear"></i>
          <span>Backup & Restore</span>
        </a>
      </div>
    `;

    // Update breadcrumbs referencing Faculty or Home
    document.querySelectorAll('.breadcrumb-item a').forEach(link => {
      const text = link.textContent.trim().toLowerCase();
      if ((link.getAttribute('href') === '/faculty/dashboard.html' && text === 'faculty') ||
          (link.getAttribute('href') === '/' && text === 'home')) {
        link.setAttribute('href', '/admin/dashboard.html');
        link.textContent = 'Admin';
      }
    });

  } else if (user.role === 'Faculty') {
    sidebarNav.innerHTML = `
      <div class="nav-section-title">Faculty Portal</div>
      <div class="nav-item">
        <a href="/faculty/dashboard.html" class="nav-link ${currentPath === '/faculty/dashboard.html' ? 'active' : ''}">
          <i class="bi bi-grid-1x2-fill"></i>
          <span>Dashboard</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/questions/list.html" class="nav-link ${currentPath.includes('/questions/') ? 'active' : ''}">
          <i class="bi bi-question-square-fill"></i>
          <span>Question Bank</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/exams/list.html" class="nav-link ${currentPath.includes('/exams/') ? 'active' : ''}">
          <i class="bi bi-card-checklist"></i>
          <span>Exam Management</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/evaluation/pending.html" class="nav-link ${currentPath.includes('/evaluation/') ? 'active' : ''}">
          <i class="bi bi-pencil-square"></i>
          <span>Evaluations</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/subjects/list.html" class="nav-link ${currentPath.includes('/subjects/') ? 'active' : ''}">
          <i class="bi bi-book-fill"></i>
          <span>Subjects</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/reports/exam_report.html" class="nav-link ${currentPath.includes('/reports/') ? 'active' : ''}">
          <i class="bi bi-bar-chart-fill"></i>
          <span>Analytics</span>
        </a>
      </div>
    `;

    document.querySelectorAll('.breadcrumb-item a').forEach(link => {
      const text = link.textContent.trim().toLowerCase();
      if ((link.getAttribute('href') === '/admin/dashboard.html' && text === 'admin') ||
          (link.getAttribute('href') === '/' && text === 'home')) {
        link.setAttribute('href', '/faculty/dashboard.html');
        link.textContent = 'Faculty';
      }
    });

  } else if (user.role === 'Student') {
    sidebarNav.innerHTML = `
      <div class="nav-section-title">Student Portal</div>
      <div class="nav-item">
        <a href="/student/dashboard.html" class="nav-link ${currentPath === '/student/dashboard.html' ? 'active' : ''}">
          <i class="bi bi-grid-1x2-fill"></i>
          <span>Dashboard</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/student/exams/available.html" class="nav-link ${currentPath.includes('/exams/') ? 'active' : ''}">
          <i class="bi bi-journal-check"></i>
          <span>Available Exams</span>
        </a>
      </div>
      <div class="nav-item">
        <a href="/student/results/list.html" class="nav-link ${currentPath.includes('/results/') ? 'active' : ''}">
          <i class="bi bi-trophy-fill"></i>
          <span>My Results</span>
        </a>
      </div>
    `;

    document.querySelectorAll('.breadcrumb-item a').forEach(link => {
      const text = link.textContent.trim().toLowerCase();
      if (link.getAttribute('href') === '/' && text === 'home') {
        link.setAttribute('href', '/student/dashboard.html');
        link.textContent = 'Student';
      }
    });
  }
}
window.updateRoleSidebar = updateRoleSidebar;

/**
 * Dynamic Notifications in Top Navbar
 */
async function loadNavbarNotifications() {
  const notifDropdown = document.getElementById('notifDropdown');
  if (!notifDropdown || !Auth.getToken()) return;

  try {
    const notifs = await apiFetch('/notifications');
    if (!Array.isArray(notifs)) return;

    const unread = notifs.filter(n => !n.isRead);
    const dot = notifDropdown.querySelector('.badge-dot');
    if (dot) {
      dot.style.display = unread.length > 0 ? 'block' : 'none';
    }

    const container = notifDropdown.parentElement.querySelector('.list-group');
    const badge = notifDropdown.parentElement.querySelector('.badge');
    if (badge) badge.textContent = `${unread.length} New`;

    if (container) {
      if (notifs.length === 0) {
        container.innerHTML = '<div class="p-3 text-center text-muted small">No notifications</div>';
      } else {
        container.innerHTML = notifs.slice(0, 5).map(n => `
          <a href="/notifications/center.html" class="list-group-item list-group-item-action p-3 ${n.isRead ? 'opacity-75' : 'bg-light'}">
            <div class="d-flex w-100 justify-content-between mb-1">
              <strong class="${n.priority === 'HIGH' ? 'text-danger' : 'text-info'}">
                <i class="bi bi-${n.notificationType === 'EXAM_RESULT' ? 'award' : 'bell'} me-1"></i> ${n.title}
              </strong>
              <small class="text-muted">${n.sentAt ? new Date(n.sentAt).toLocaleDateString() : 'Recent'}</small>
            </div>
            <p class="mb-1 text-muted small">${n.message}</p>
          </a>
        `).join('');
      }
    }
  } catch (e) {
    // Silently ignore navbar notification poll error
  }
}

// Global initialization on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  // Mobile sidebar toggle button
  const navbar = document.querySelector('.top-navbar');
  if (navbar && !navbar.querySelector('.mobile-toggle-btn')) {
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-outline-secondary d-lg-none me-2 mobile-toggle-btn';
    btn.innerHTML = '<i class="bi bi-list fs-5"></i>';
    btn.onclick = toggleMobileSidebar;
    navbar.insertBefore(btn, navbar.firstChild);
  }

  // Update navbar user profile, role-aware sidebar & notifications
  updateNavbarUser();
  updateRoleSidebar();
  loadNavbarNotifications();
});

/**
 * Global HTML Escaping Helper to sanitize dynamic string interpolation
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;

function formatDate(dateStr) {
  if (!dateStr) return '--';
  try {
    return new Date(dateStr).toLocaleString([], {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch (_) {
    return String(dateStr);
  }
}
window.formatDate = formatDate;

