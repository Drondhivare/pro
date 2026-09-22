/* ==========================================================================
   LIVE EXAMINATION ENGINE & QUESTION NAVIGATION LOGIC
   Dynamic integration with Flask REST API
   ========================================================================== */

let attemptId = null;
let examId = null;
let attemptData = null;
let questionsList = [];
let answersMap = {};
let currentQuestionIndex = 1;
let isSubmitting = false;
let currentViolationCount = 0;
const MAX_VIOLATIONS = 3;
let lastSecurityEventTime = 0;
const SECURITY_EVENT_COOLDOWN_MS = 1500;
let isNavigatingToReview = false;
let isProcessingSecurityEvent = false;
let securityMonitorInitialized = false;

document.addEventListener('DOMContentLoaded', async () => {
  const user = Auth.requireAuth('Student');
  if (!user) return;

  const params = new URLSearchParams(window.location.search);
  attemptId = params.get('attemptId');
  examId = params.get('examId');

  if (!attemptId || !examId) {
    alert('Invalid exam session parameters. Returning to available exams.');
    window.location.href = '/student/exams/available.html';
    return;
  }

  const btnReview = document.getElementById('btnFinishReview');
  if (btnReview) {
    btnReview.href = `/exam_runtime/review.html?attemptId=${attemptId}&examId=${examId}`;
    btnReview.addEventListener('click', (e) => {
      if (!questionsList || questionsList.length === 0) {
        e.preventDefault();
        return;
      }
      isNavigatingToReview = true;
    });
  }

  await loadExamSession();
});

async function loadExamSession() {
  const wrapper = document.getElementById('questionsWrapper');

  try {
    // 1. Fetch & Validate Attempt Data
    attemptData = await apiFetch(`/attempts/${attemptId}`);
    if (!attemptData) {
      alert('Failed to load examination attempt.');
      window.location.href = '/student/dashboard.html';
      return;
    }

    // Prevent continuation if attempt is already submitted
    if (attemptData.status !== 'IN_PROGRESS') {
      alert('This exam attempt is already submitted or closed.');
      window.location.href = `/exam_runtime/submitted.html?attemptId=${attemptId}`;
      return;
    }

    // Update Header
    const titleEl = document.getElementById('examTitleHeader');
    if (titleEl) titleEl.innerText = attemptData.examTitle || 'Live Examination';
    const codeEl = document.getElementById('examSubjectCode');
    if (codeEl) codeEl.innerText = attemptData.examCode || 'EXAM';

    // 2. Initialize Timer (runs even for zero-question state)
    const durationMinutes = attemptData.durationMinutes || 60;
    let remainingSeconds = durationMinutes * 60;
    if (attemptData.startTime) {
      const cleanStartTime = typeof attemptData.startTime === 'string'
        ? attemptData.startTime.replace(/\s+GMT$/i, '')
        : attemptData.startTime;
      const startTimeMs = new Date(cleanStartTime).getTime();
      const elapsedSeconds = Math.floor((Date.now() - startTimeMs) / 1000);
      if (!isNaN(elapsedSeconds) && elapsedSeconds > 0) {
        remainingSeconds = Math.max(5, remainingSeconds - elapsedSeconds);
      }
    }
    startExamTimerSeconds(remainingSeconds, 'examTimer', autoSubmitExam);

    // 3. Authoritative Security Monitor Initialization (runs even for zero-question state)
    currentViolationCount = parseInt(attemptData.violationCount || 0);
    updateSecurityIndicator(currentViolationCount);
    initializeSecurityMonitor();

    // 4. Fetch Questions
    questionsList = await apiFetch(`/exams/${examId}/questions`);
    if (!Array.isArray(questionsList)) {
      if (wrapper) {
        wrapper.innerHTML = `<div class="alert alert-danger">Failed to load questions for this exam.</div>`;
      }
      return;
    }

    const btnReview = document.getElementById('btnFinishReview');

    if (questionsList.length === 0) {
      if (wrapper) {
        wrapper.innerHTML = `<div class="alert alert-warning">No questions assigned to this exam yet. Contact faculty.</div>`;
      }
      const paletteContainer = document.getElementById('paletteContainer');
      if (paletteContainer) {
        paletteContainer.innerHTML = `<span class="text-muted small">No questions assigned.</span>`;
      }
      if (btnReview) {
        btnReview.classList.add('disabled', 'd-none');
        btnReview.setAttribute('aria-disabled', 'true');
        btnReview.removeAttribute('href');
      }
      return;
    }

    // Ensure Finish & Review is enabled and visible when questions exist
    if (btnReview) {
      btnReview.classList.remove('d-none', 'disabled');
      btnReview.removeAttribute('aria-disabled');
      btnReview.href = `/exam_runtime/review.html?attemptId=${attemptId}&examId=${examId}`;
    }

    // 5. Fetch Existing Answers
    try {
      const answers = await apiFetch(`/attempts/${attemptId}/answers`);
      if (Array.isArray(answers)) {
        answers.forEach(a => {
          answersMap[a.questionId] = a;
        });
      }
    } catch (e) {
      console.warn('Could not fetch existing answers:', e);
    }

    // 6. Render Questions & Palette
    renderQuestions();
    renderPalette();
    navigateQuestion(1);

  } catch (err) {
    console.error('Error loading exam session:', err);
    if (wrapper) {
      wrapper.innerHTML = `<div class="alert alert-danger">An unexpected error occurred while loading the exam: ${err.message}</div>`;
    }
  }
}

function renderPalette() {
  const container = document.getElementById('paletteContainer');
  if (!container) return;

  container.innerHTML = questionsList.map((q, idx) => {
    const num = idx + 1;
    const ans = answersMap[q.questionId];
    const isAnswered = ans && ans.isAnswered;
    const isReview = ans && ans.isMarkedForReview;

    let classes = 'question-palette-btn';
    if (num === currentQuestionIndex) classes += ' current';
    if (isReview) classes += ' review';
    else if (isAnswered) classes += ' answered';

    return `<button class="${classes}" id="palette-btn-${num}" onclick="navigateQuestion(${num})">${num}</button>`;
  }).join('');
}

function renderQuestions() {
  const wrapper = document.getElementById('questionsWrapper');
  if (!wrapper) return;

  const total = questionsList.length;

  wrapper.innerHTML = questionsList.map((q, idx) => {
    const num = idx + 1;
    const ans = answersMap[q.questionId] || {};
    const isReview = !!ans.isMarkedForReview;

    let optionsHtml = '';
    const qType = (q.questionType || 'MCQ').toUpperCase();

    if (qType === 'MCQ' || qType === 'TRUE_FALSE') {
      optionsHtml = (q.options || []).map(opt => {
        const isChecked = ans.selectedOptionId === opt.optionId ? 'checked' : '';
        return `
          <label class="p-3 rounded border section-bg d-flex align-items-center gap-3 cursor-pointer">
            <input type="radio" name="q_${q.questionId}_option" value="${opt.optionId}" ${isChecked}
                   onchange="handleOptionSelect(${num}, ${q.questionId}, ${opt.optionId})">
            <span class="fw-medium">${escapeHtml(opt.optionText)}</span>
          </label>
        `;
      }).join('');
    } else if (qType === 'MSQ') {
      // Multiple Select: parse comma-separated option IDs if stored in answerText
      const selectedIds = (ans.answerText ? ans.answerText.split(',') : []).map(s => s.trim());
      optionsHtml = (q.options || []).map(opt => {
        const isChecked = selectedIds.includes(String(opt.optionId)) ? 'checked' : '';
        return `
          <label class="p-3 rounded border section-bg d-flex align-items-center gap-3 cursor-pointer">
            <input type="checkbox" name="q_${q.questionId}_msq" value="${opt.optionId}" ${isChecked}
                   onchange="handleMsqSelect(${num}, ${q.questionId})">
            <span class="fw-medium">${escapeHtml(opt.optionText)}</span>
          </label>
        `;
      }).join('');
    } else {
      // DESCRIPTIVE
      const textVal = ans.answerText || '';
      optionsHtml = `
        <div class="mb-3">
          <textarea class="form-control" rows="6" placeholder="Type your descriptive response here..."
                    id="desc_${q.questionId}"
                    onchange="handleDescriptiveChange(${num}, ${q.questionId})">${escapeHtml(textVal)}</textarea>
        </div>
      `;
    }

    const prevBtn = num > 1
      ? `<button class="btn btn-outline-secondary btn-sm" onclick="navigateQuestion(${num - 1})">&larr; Previous</button>`
      : `<div></div>`;

    const nextBtn = num < total
      ? `<button class="btn btn-primary btn-sm" onclick="navigateQuestion(${num + 1})">Next Question &rarr;</button>`
      : `<a href="/exam_runtime/review.html?attemptId=${attemptId}&examId=${examId}" class="btn btn-success btn-sm">Finish & Review &rarr;</a>`;

    const reviewBtnText = isReview ? 'Marked for Review' : 'Mark for Review';
    const reviewBtnClass = isReview ? 'btn-warning text-dark' : 'btn-outline-warning';

    return `
      <div class="glass-card p-4 question-card ${num === 1 ? '' : 'd-none'}" id="question-${num}">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <span class="badge bg-primary fs-6">Question ${num} of ${total}</span>
          <span class="text-muted small">${q.marks || 1} Marks &bull; ${qType} ${q.negativeMarks > 0 ? `(-${q.negativeMarks})` : ''}</span>
        </div>

        <h5 class="fw-bold mb-4 text-dark">${escapeHtml(q.questionText)}</h5>

        <div class="d-flex flex-column gap-3 mb-4">
          ${optionsHtml}
        </div>

        <div class="d-flex justify-content-between align-items-center border-top pt-3">
          ${prevBtn}
          <div class="d-flex gap-2">
            <button class="btn ${reviewBtnClass} btn-sm" id="review-btn-${num}" onclick="toggleReview(${num}, ${q.questionId})">
              <i class="bi bi-bookmark-star"></i> ${reviewBtnText}
            </button>
            ${nextBtn}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function navigateQuestion(index) {
  if (index < 1 || index > questionsList.length) return;

  // Hide all questions
  document.querySelectorAll('.question-card').forEach(card => card.classList.add('d-none'));

  // Show target question
  const targetCard = document.getElementById(`question-${index}`);
  if (targetCard) targetCard.classList.remove('d-none');

  // Update palette active button
  document.querySelectorAll('.question-palette-btn').forEach(btn => btn.classList.remove('current'));
  const activePaletteBtn = document.getElementById(`palette-btn-${index}`);
  if (activePaletteBtn) activePaletteBtn.classList.add('current');

  currentQuestionIndex = index;
}

async function handleOptionSelect(questionIndex, questionId, optionId) {
  const existing = answersMap[questionId] || {};
  const isReview = !!existing.isMarkedForReview;

  answersMap[questionId] = {
    ...existing,
    questionId: questionId,
    selectedOptionId: optionId,
    answerText: null,
    isAnswered: true,
    isMarkedForReview: isReview
  };

  updatePaletteButton(questionIndex, true, isReview);

  try {
    await apiFetch(`/attempts/${attemptId}/answers`, {
      method: 'POST',
      body: JSON.stringify({
        questionId: questionId,
        selectedOptionId: optionId,
        answerText: null,
        isAnswered: true,
        isMarkedForReview: isReview,
        timeSpentSeconds: 5
      })
    });
  } catch (err) {
    console.error('Error saving answer:', err);
  }
}

async function handleMsqSelect(questionIndex, questionId) {
  const checkboxes = document.querySelectorAll(`input[name="q_${questionId}_msq"]:checked`);
  const selectedOptionIds = Array.from(checkboxes).map(cb => cb.value);
  const isAnswered = selectedOptionIds.length > 0;
  const existing = answersMap[questionId] || {};
  const isReview = !!existing.isMarkedForReview;

  answersMap[questionId] = {
    ...existing,
    questionId: questionId,
    selectedOptionId: selectedOptionIds.length > 0 ? parseInt(selectedOptionIds[0]) : null,
    answerText: selectedOptionIds.join(','),
    isAnswered: isAnswered,
    isMarkedForReview: isReview
  };

  updatePaletteButton(questionIndex, isAnswered, isReview);

  try {
    await apiFetch(`/attempts/${attemptId}/answers`, {
      method: 'POST',
      body: JSON.stringify({
        questionId: questionId,
        selectedOptionId: selectedOptionIds.length > 0 ? parseInt(selectedOptionIds[0]) : null,
        answerText: selectedOptionIds.join(','),
        isAnswered: isAnswered,
        isMarkedForReview: isReview,
        timeSpentSeconds: 5
      })
    });
  } catch (err) {
    console.error('Error saving answer:', err);
  }
}

async function handleDescriptiveChange(questionIndex, questionId) {
  const textarea = document.getElementById(`desc_${questionId}`);
  if (!textarea) return;
  const textVal = textarea.value.trim();
  const isAnswered = textVal.length > 0;
  const existing = answersMap[questionId] || {};
  const isReview = !!existing.isMarkedForReview;

  answersMap[questionId] = {
    ...existing,
    questionId: questionId,
    selectedOptionId: null,
    answerText: textVal,
    isAnswered: isAnswered,
    isMarkedForReview: isReview
  };

  updatePaletteButton(questionIndex, isAnswered, isReview);

  try {
    await apiFetch(`/attempts/${attemptId}/answers`, {
      method: 'POST',
      body: JSON.stringify({
        questionId: questionId,
        selectedOptionId: null,
        answerText: textVal,
        isAnswered: isAnswered,
        isMarkedForReview: isReview,
        timeSpentSeconds: 10
      })
    });
  } catch (err) {
    console.error('Error saving descriptive answer:', err);
  }
}

async function toggleReview(questionIndex, questionId) {
  const existing = answersMap[questionId] || {};
  const newReviewState = !existing.isMarkedForReview;

  answersMap[questionId] = {
    ...existing,
    questionId: questionId,
    isMarkedForReview: newReviewState
  };

  const isAnswered = !!answersMap[questionId].isAnswered;
  updatePaletteButton(questionIndex, isAnswered, newReviewState);

  // Update button visual
  const btn = document.getElementById(`review-btn-${questionIndex}`);
  if (btn) {
    if (newReviewState) {
      btn.className = 'btn btn-warning text-dark btn-sm';
      btn.innerHTML = '<i class="bi bi-bookmark-star"></i> Marked for Review';
    } else {
      btn.className = 'btn btn-outline-warning btn-sm';
      btn.innerHTML = '<i class="bi bi-bookmark-star"></i> Mark for Review';
    }
  }

  try {
    await apiFetch(`/attempts/${attemptId}/answers`, {
      method: 'POST',
      body: JSON.stringify({
        questionId: questionId,
        selectedOptionId: answersMap[questionId].selectedOptionId || null,
        answerText: answersMap[questionId].answerText || null,
        isAnswered: isAnswered,
        isMarkedForReview: newReviewState
      })
    });
  } catch (err) {
    console.error('Error updating review flag:', err);
  }
}

function updatePaletteButton(questionIndex, isAnswered, isReview) {
  const paletteBtn = document.getElementById(`palette-btn-${questionIndex}`);
  if (!paletteBtn) return;

  paletteBtn.classList.remove('answered', 'review');
  if (isReview) {
    paletteBtn.classList.add('review');
  } else if (isAnswered) {
    paletteBtn.classList.add('answered');
  }
}

async function autoSubmitExam() {
  if (isSubmitting) return;
  if (!questionsList || questionsList.length === 0) {
    alert('Time has expired! This exam has no assigned questions.');
    window.location.href = '/student/dashboard.html';
    return;
  }
  isSubmitting = true;
  alert('Time has expired! Submitting your exam automatically...');
  try {
    await apiFetch(`/attempts/${attemptId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ autoSubmitted: true, submissionReason: 'AUTO_TIMEOUT' })
    });
  } catch (err) {
    console.error('Error auto-submitting attempt:', err);
  } finally {
    window.location.href = `/exam_runtime/submitted.html?attemptId=${attemptId}`;
  }
}

/* ==========================================================================
   EXAM SECURITY MONITORING & TAB-SWITCH DETECTION
   ========================================================================== */

function updateSecurityIndicator(count) {
  currentViolationCount = Math.max(0, parseInt(count) || 0);
  const badge = document.getElementById('securityWarningBadge');
  const icon = document.getElementById('securityIcon');
  const statusText = document.getElementById('securityStatusText');

  if (badge) {
    badge.innerText = `Warnings: ${currentViolationCount}/${MAX_VIOLATIONS}`;
    if (currentViolationCount === 0) {
      badge.className = 'badge bg-light text-dark border ms-1 fw-bold';
      if (icon) icon.className = 'bi bi-shield-check text-success';
      if (statusText) statusText.className = 'text-success';
    } else if (currentViolationCount === 1) {
      badge.className = 'badge bg-warning text-dark border ms-1 fw-bold';
      if (icon) icon.className = 'bi bi-shield-exclamation text-warning';
      if (statusText) statusText.className = 'text-warning';
    } else if (currentViolationCount === 2) {
      badge.className = 'badge bg-danger text-white border ms-1 fw-bold';
      if (icon) icon.className = 'bi bi-shield-exclamation text-danger';
      if (statusText) statusText.className = 'text-danger';
    } else {
      badge.className = 'badge bg-danger text-white border ms-1 fw-bold';
      if (icon) icon.className = 'bi bi-shield-slash-fill text-danger';
      if (statusText) statusText.className = 'text-danger';
    }
  }
}

function showSecurityAlert(title, message, isCritical = false) {
  const container = document.getElementById('securityAlertContainer');
  const titleEl = document.getElementById('securityAlertTitle');
  const msgEl = document.getElementById('securityAlertMessage');
  const box = document.getElementById('securityAlertBox');
  const icon = document.getElementById('securityAlertIcon');

  if (container && titleEl && msgEl) {
    titleEl.innerText = title;
    msgEl.innerText = message;
    if (isCritical) {
      if (box) box.className = 'alert alert-danger border-danger d-flex align-items-center justify-content-between p-3 shadow-sm mb-0 rounded';
      if (icon) icon.className = 'bi bi-shield-slash-fill fs-3 text-danger';
    } else {
      if (box) box.className = 'alert alert-warning border-warning d-flex align-items-center justify-content-between p-3 shadow-sm mb-0 rounded';
      if (icon) icon.className = 'bi bi-exclamation-triangle-fill fs-3 text-warning';
    }
    container.classList.remove('d-none');
  }
}

function dismissSecurityAlert() {
  const container = document.getElementById('securityAlertContainer');
  if (container) container.classList.add('d-none');
}

function initializeSecurityMonitor() {
  if (securityMonitorInitialized) return;
  securityMonitorInitialized = true;

  // Listen to visibility change (tab switch, window minimization)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      handleSecurityViolation('TAB_SWITCH', 'Switched browser tab or minimized window');
    }
  });

  // Listen to window blur (switching to another application/window)
  window.addEventListener('blur', () => {
    handleSecurityViolation('WINDOW_BLUR', 'Left examination window');
  });
}

async function handleSecurityViolation(eventType, details) {
  // If exam is already submitting or student intentionally clicked Finish & Review, ignore
  if (isSubmitting || isNavigatingToReview) return;

  const now = Date.now();
  // Debounce throttle duplicate/rapid visibility & blur events
  if (now - lastSecurityEventTime < SECURITY_EVENT_COOLDOWN_MS) {
    return;
  }
  lastSecurityEventTime = now;

  if (isProcessingSecurityEvent) return;
  isProcessingSecurityEvent = true;

  try {
    const res = await apiFetch(`/attempts/${attemptId}/security-event`, {
      method: 'POST',
      body: JSON.stringify({ eventType, details })
    });

    if (!res) return;

    const count = parseInt(res.violationCount != null ? res.violationCount : (currentViolationCount + 1));
    updateSecurityIndicator(count);

    if (res.autoSubmitTriggered || count >= MAX_VIOLATIONS) {
      await handleSecurityAutoSubmit();
    } else {
      const title = `Security Warning ${count}/${MAX_VIOLATIONS}`;
      const msg = res.message || (count === 1
        ? 'Warning 1/3: Leaving the exam window is not allowed. Further violations may automatically submit your exam.'
        : 'Warning 2/3: This is your final warning. One more violation will automatically submit your exam.');
      showSecurityAlert(title, msg, count === 2);
    }
  } catch (err) {
    console.warn('Security event registration error:', err);
  } finally {
    isProcessingSecurityEvent = false;
  }
}

async function handleSecurityAutoSubmit() {
  if (isSubmitting) return;
  isSubmitting = true;

  // 1. Lock UI
  lockExamUI();

  // 2. Display required message
  showSecurityAlert(
    'Maximum Security Violations Reached',
    'Maximum security violations reached. Your exam is being submitted automatically.',
    true
  );

  // 3. Flush any pending active answer
  try {
    const currentQ = questionsList[currentQuestionIndex - 1];
    if (currentQ && currentQ.questionType === 'DESCRIPTIVE') {
      const textarea = document.getElementById(`desc_${currentQ.questionId}`);
      if (textarea && textarea.value.trim()) {
        await apiFetch(`/attempts/${attemptId}/answers`, {
          method: 'POST',
          body: JSON.stringify({
            questionId: currentQ.questionId,
            selectedOptionId: null,
            answerText: textarea.value.trim(),
            isAnswered: true,
            isMarkedForReview: false,
            timeSpentSeconds: 10
          })
        }).catch(() => null);
      }
    }
  } catch (_) {}

  // 4. Submit with reason AUTO_SUBMITTED_TAB_SWITCH_LIMIT using existing API
  try {
    await apiFetch(`/attempts/${attemptId}/submit`, {
      method: 'POST',
      body: JSON.stringify({
        autoSubmitted: true,
        submissionReason: 'AUTO_SUBMITTED_TAB_SWITCH_LIMIT'
      })
    });
  } catch (err) {
    console.error('Error in security auto-submit:', err);
  } finally {
    // 5. Redirect to submitted page
    setTimeout(() => {
      window.location.href = `/exam_runtime/submitted.html?attemptId=${attemptId}`;
    }, 1200);
  }
}

function lockExamUI() {
  // Disable all interactive elements
  document.querySelectorAll('input, textarea, button, a').forEach(el => {
    el.disabled = true;
    el.style.pointerEvents = 'none';
  });

  const wrapper = document.getElementById('questionsWrapper');
  if (wrapper) {
    const lockNotice = document.createElement('div');
    lockNotice.className = 'alert alert-danger p-4 text-center my-3 shadow';
    lockNotice.innerHTML = `
      <i class="bi bi-shield-slash-fill fs-1 d-block mb-2 text-danger"></i>
      <h5 class="fw-bold">Exam Session Terminated</h5>
      <p class="mb-2">Maximum security violations reached. Your exam is being submitted automatically.</p>
      <div class="spinner-border spinner-border-sm text-danger" role="status"></div>
      <span class="small ms-2 text-muted">Submitting attempt...</span>
    `;
    wrapper.prepend(lockNotice);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
