/* ==========================================================================
   LIVE EXAMINATION TIMER LOGIC
   ========================================================================== */

let totalSeconds = 3600; // 60 minutes default
let timerInterval = null;

function startExamTimerSeconds(seconds, displayElementId, onExpireCallback) {
  totalSeconds = Math.max(0, Math.floor(seconds));
  const displayElement = document.getElementById(displayElementId);
  const timerBox = document.getElementById('timerBox');

  updateTimerDisplay(displayElement);

  if (timerInterval) clearInterval(timerInterval);

  timerInterval = setInterval(() => {
    totalSeconds--;

    updateTimerDisplay(displayElement);

    if (totalSeconds <= 300 && totalSeconds > 0) { // 5 minutes warning
      if (timerBox) {
        timerBox.classList.add('bg-danger');
      } else if (displayElement) {
        displayElement.classList.add('text-danger', 'fw-bold');
      }
    } else if (totalSeconds > 300) {
      if (timerBox) {
        timerBox.classList.remove('bg-danger');
      } else if (displayElement) {
        displayElement.classList.remove('text-danger', 'fw-bold');
      }
    }

    if (totalSeconds <= 0) {
      clearInterval(timerInterval);
      if (typeof onExpireCallback === 'function') {
        onExpireCallback();
      }
    }
  }, 1000);
}

function startExamTimer(durationMinutes, displayElementId, onExpireCallback) {
  startExamTimerSeconds(durationMinutes * 60, displayElementId, onExpireCallback);
}

function updateTimerDisplay(element) {
  if (!element) return;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  element.innerText = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}
