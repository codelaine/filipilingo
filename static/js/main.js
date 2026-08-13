/* ============================================================
   main.js – Global utilities shared across all pages
   ============================================================ */

// ── Toast Notification ─────────────────────────────────────────
function showToast(msg, duration = 2500) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add('hidden'), duration);
}

// ── Celebration Overlay ─────────────────────────────────────────
function showCelebration({ emoji, title, msg, stars, onClose }) {
  const overlay = document.getElementById('celebration-overlay');
  const eEl     = document.getElementById('celebration-emoji');
  const tEl     = document.getElementById('celebration-title');
  const mEl     = document.getElementById('celebration-msg');
  const sEl     = document.getElementById('stars-display');
  const btn     = document.getElementById('celebration-btn');

  eEl.textContent = emoji || '🎉';
  tEl.textContent = title || 'Napakagaling!';
  mEl.textContent = msg   || '';

  // Render stars (out of 3)
  sEl.innerHTML = '';
  const earned = Math.min(3, Math.max(0, stars || 0));
  for (let i = 0; i < 3; i++) {
    const s = document.createElement('span');
    if (i < earned) {
      s.textContent = '⭐';
      s.className = 'star-earned';
      s.style.animationDelay = `${i * 0.15}s`;
    } else {
      s.textContent = '⭐';
      s.className = 'star-empty';
    }
    sEl.appendChild(s);
  }

  overlay.classList.remove('hidden');

  btn.onclick = () => {
    overlay.classList.add('hidden');
    if (typeof onClose === 'function') onClose();
  };
}

// ── Confetti burst (pure CSS / JS, no library) ────────────────
function burstConfetti(count = 36) {
  const colors = ['#FF6B6B','#FFD93D','#6BCB77','#4ECDC4','#845EC2','#FF9A3C','#FF6FA8'];
  const container = document.createElement('div');
  container.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:999;overflow:hidden;';
  document.body.appendChild(container);

  for (let i = 0; i < count; i++) {
    const dot = document.createElement('div');
    const size = 8 + Math.random() * 10;
    dot.style.cssText = `
      position:absolute;
      width:${size}px;height:${size}px;
      border-radius:${Math.random() > .5 ? '50%' : '2px'};
      background:${colors[Math.floor(Math.random() * colors.length)]};
      left:${Math.random() * 100}%;
      top:-${size}px;
      opacity:1;
      transition: none;
    `;
    container.appendChild(dot);

    const duration = 1000 + Math.random() * 800;
    const targetY  = window.innerHeight + 20;
    const targetX  = (Math.random() - .5) * 200;
    const rot      = Math.random() * 720 - 360;

    dot.animate([
      { transform: `translate(0,0) rotate(0deg)`, opacity: 1 },
      { transform: `translate(${targetX}px,${targetY}px) rotate(${rot}deg)`, opacity: 0 }
    ], { duration, easing: 'ease-in', fill: 'forwards' }).onfinish = () => dot.remove();
  }
  setTimeout(() => container.remove(), 2500);
}

// ── Sync nav counters from server session ─────────────────────
async function refreshNavStats() {
  try {
    const res  = await fetch('/api/session_data');
    const data = await res.json();
    const sc = document.getElementById('streak-count');
    const st = document.getElementById('stars-count');
    if (sc) sc.textContent = data.streak;
    if (st) st.textContent = data.total_stars;
    const lt = document.getElementById('lessons-today');
    if (lt) lt.textContent = data.lessons_today;
  } catch (_) { /* network silent fail */ }
}
