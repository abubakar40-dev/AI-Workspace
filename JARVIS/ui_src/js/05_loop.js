/* ---------- shared render loop with per-task fps caps, visibility gating and a frame-time governor ---------- */
(function () {
'use strict';
const H = window.H;
const tasks = [];
let last = performance.now(), slow = 0, fast = 0, acc = 0, frames = 0, fpsShown = 60;
H.loop = {
  add(fn, o = {}) { const t = { fn, fps: o.fps || 60, vis: o.vis || (() => true), last: 0, ms: 0 }; tasks.push(t); return t; },
  fps: () => fpsShown
};
function frame(now) {
  requestAnimationFrame(frame);
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (document.hidden) return;
  const cap = H.quality.fps || 60;
  const t0 = performance.now();
  for (const t of tasks) {
    const minDt = 1000 / Math.min(t.fps, cap);
    if (now - t.last < minDt - 1) continue;
    if (!t.vis()) continue;
    const d = Math.min(0.1, (now - (t.last || now - 16)) / 1000); t.last = now;
    try { t.fn(d, now / 1000); } catch (e) { if (!t.err) { t.err = 1; console.error('[loop]', e); } }
  }
  /* governor: if work per frame is consistently heavy, step quality down (auto mode only) */
  const work = performance.now() - t0; frames++; acc += dt;
  if (acc >= 1) { fpsShown = Math.round(frames / acc); frames = 0; acc = 0; H.bus.emit('fps', fpsShown); }
  if (H.config.quality === 'auto') {
    if (work > 30) { slow++; fast = 0; } else if (work < 8) { fast++; slow = Math.max(0, slow - 1); }
    if (slow > 90 && H.quality.level !== 'low') { slow = 0; H.setQuality(H.quality.level === 'high' ? 'med' : 'low'); H.toast('Auto-quality lowered to ' + H.quality.level.toUpperCase() + ' to keep the UI smooth', 'warn', 'GRAPHICS'); }
  }
}
requestAnimationFrame(frame);
})();
