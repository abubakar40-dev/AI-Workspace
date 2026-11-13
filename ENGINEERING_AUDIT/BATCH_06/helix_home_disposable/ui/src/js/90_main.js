/* ---------- boot ---------- */
(function () {
'use strict';
const H = window.H, $ = H.$;
const lines = $('#boot-lines'), bar = $('#boot-bar'); const log = (t, p) => { lines.append(H.el('div', null, t)); lines.scrollTop = 999; if (p != null) bar.style.width = (p * 100) + '%'; };
const step = async (name, p, fn) => { try { log(name, p); await fn(); } catch (e) { console.error('[boot] ' + name, e); log('! ' + name + ' failed: ' + (e.message || e)); } await new Promise(r => setTimeout(r, 30)); };

async function main() {
  H.setAccent(H.config.accent || 'cyan'); H.setQuality(H.detectQuality()); log('graphics profile: ' + H.quality.level.toUpperCase(), .05);
  await step('voice core · particle orb', .12, () => H.voice.init());
  await step('side panels · composer · security layer', .2, () => H.initSide());
  await step('agent town · pixel office', .3, () => H.town.init());
  await step('world monitor · procedural Earth', .4, () => H.globe.init((p, m) => { bar.style.width = (40 + p * 50) + '%'; log('  earth: ' + m); }));
  await step('bridge · connect', .95, () => {
    const params = new URLSearchParams(location.search);
    const q = params.get('bridge');
    if (q) { H.config.bridgeUrl = q; H.saveConfig(); }
    // No demo backend: show BRIDGE OFFLINE until a real socket opens.
    H.state.mode = 'offline'; H.bus.emit('mode', 'offline');
    H.bridge.connect(q || H.config.bridgeUrl, true);
  });
  bar.style.width = '100%'; setTimeout(() => $('#boot').classList.add('done'), 350); setTimeout(() => $('#boot').remove(), 1200);
}
if (typeof THREE === 'undefined') { document.body.innerHTML = '<pre style="color:#f66;padding:20px">three.js failed to load</pre>'; } else main();
/* Collect page errors so the desktop app can report them in its log. Without
   this, a JS failure in the webview is invisible — the window just looks
   empty and there is nothing to diagnose. */
window.__helixErrors = [];
window.addEventListener('error', e => { window.__helixErrors.push(String(e.message) + ' @ ' + (e.filename || '') + ':' + (e.lineno || '')); });
window.addEventListener('unhandledrejection', e => { window.__helixErrors.push('unhandled rejection: ' + String(e.reason)); });

/* Report the page's own state back to the bridge. A webview that failed
   silently looks exactly like one that works, and there is no console to
   read — so the page says what it thinks its state is. */
function __helixReport(tag) {
  try {
    const S = H.state;
    H.bridge.send({ type: 'diag', tag: tag, state: {
      mode: S.mode,
      connected: H.bridge.connected, url: H.bridge.url,
      agents: Object.keys(S.agents).length, tasks: Object.keys(S.tasks).length,
      chat: S.chat.length, headlines: S.headlines.length, lms: !!S.lms,
      lmsCourses: S.lms ? (S.lms.courses || []).length : 0,
      lmsItems: S.lms ? (S.lms.items || []).length : 0,
      memory: S.memory.length, skills: S.skills.length, souls: Object.keys(S.souls).length,
      model: S.model, ctx: S.ctx.used, voice: S.voice,
      orbAlive: !!(H.orb && !H.orb.dead),
      errors: (window.__helixErrors || []).slice(0, 8),
    }});
  } catch (e) { /* nothing to report with */ }
}
setTimeout(() => __helixReport('t+5s'), 5000);
setTimeout(() => __helixReport('t+20s'), 20000);
setTimeout(() => __helixReport('t+40s'), 40000);
})();
