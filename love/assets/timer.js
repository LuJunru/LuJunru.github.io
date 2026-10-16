'use strict';
// Actual elapsed seconds, not a tick counter: background tabs never accumulate drift.
// The ISO start value with explicit UTC+8 lives in index.html as a single source of truth.
function elapsedParts(now, start) {
  if (!Number.isFinite(now) || !Number.isFinite(start)) throw new TypeError('Invalid timer date');
  const elapsed = Math.max(0, Math.floor((now - start) / 1000));
  return {
    days: Math.floor(elapsed / 86400),
    hours: Math.floor(elapsed / 3600) % 24,
    minutes: Math.floor(elapsed / 60) % 60,
    seconds: elapsed % 60
  };
}
if (typeof module !== 'undefined' && module.exports) module.exports = { elapsedParts };
if (typeof document !== 'undefined') {
  const content = document.querySelector('.content[data-start]');
  const start = Date.parse(content.dataset.start);
  const nodes = ['d', 'h', 'm', 's'].map(id => document.getElementById(id));
  function updateTimer() {
    const parts = elapsedParts(Date.now(), start);
    [parts.days, parts.hours, parts.minutes, parts.seconds].forEach((value, index) => {
      nodes[index].textContent = index === 0 ? String(value) : String(value).padStart(2, '0');
    });
  }
  updateTimer();
  setInterval(updateTimer, 1000);
  document.addEventListener('visibilitychange', updateTimer);
  const back = document.getElementById('back-home');
  if (new URLSearchParams(location.search).get('lang') !== 'zh') {
    back.href = '/';
    back.innerHTML = '<span aria-hidden="true">←</span> Back to home';
    back.setAttribute('aria-label', 'Back to personal homepage');
    back.lang = 'en';
  } else {
    back.href = '/zh/';
  }
}
