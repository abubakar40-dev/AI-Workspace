/* =====================================================================================
   SIDE PANEL (voice transcript · agent tool stream · notes+audit), composer + slash commands,
   confirm/kill security layer, Visual Hub (kanban), Gesture tab, LMS ops, link downloader, media link
   ===================================================================================== */
(function () {
'use strict';
const H = window.H, $ = H.$;

/* ---------- chat / tool feeds ---------- */
const chatFeed = () => $('#chat-feed'), toolFeed = () => $('#tool-feed');
function atBottom(el) { return el.scrollHeight - el.scrollTop - el.clientHeight < 60; }
function addMsg(e) {
  const f = chatFeed(), stick = atBottom(f), ur = H.isUrdu(e.text), role = e.role === 'agent' ? 'helix' : e.role;
  const who = e.role === 'user' ? 'YOU' : e.role === 'sys' ? '' : (e.role === 'agent' ? (H.agent(e.agent) || {}).name + ' · ' + e.agent : 'HELIX');
  const m = H.el('div', { class: 'msg ' + role, dir: ur ? 'rtl' : 'ltr' }, who ? H.el('div', { class: 'who', style: e.role === 'agent' ? 'color:' + H.agentColor(e.agent) : '' }, who, H.el('small', null, H.hhmm(e.t))) : null, e.text);
  f.append(m); if (stick || e.role === 'user') f.scrollTop = f.scrollHeight;
  while (f.children.length > 200) f.firstChild.remove();
}
H.bus.on('chat', addMsg);
function pretty(o) { let s; try { s = typeof o === 'string' ? o : JSON.stringify(o, null, 1); } catch (e) { s = String(o); } return s.length > 1400 ? s.slice(0, 1400) + '\n… (truncated)' : s; }
function addTool(e) {
  const f = toolFeed(), stick = atBottom(f), bad = e.ok === false, a = H.agent(e.agent) || { name: e.agent };
  const c = H.el('div', { class: 'tcard' + (bad ? ' bad' : '') }, H.el('div', { class: 'tcard-h' }, H.el('i', { class: 'st' }), H.el('span', { class: 'ag', style: 'color:' + H.agentColor(e.agent) }, (a.name || '').toUpperCase() + ' · ' + e.agent), H.el('span', { class: 'tn', html: H.icon('tool', 12) + '<span>' + H.esc(e.tool) + '</span>' }), H.el('span', { class: 'ms' }, ((e.ms || 0) / 1000).toFixed(1) + 's')),
    H.el('div', { class: 'tcard-b' }, H.el('h6', null, 'INPUT'), H.el('pre', null, pretty(e.input)), H.el('h6', null, 'OUTPUT'), H.el('pre', { class: 'out' }, pretty(e.output))));
  f.append(c); if (stick) f.scrollTop = f.scrollHeight; else { $('#new-msgs').hidden = false; } while (f.children.length > 120) f.firstChild.remove();
}
H.bus.on('tool.call', addTool);
H.bus.on('verify', e => { const t = H.state.tasks[e.task] || {}, f = toolFeed(), stick = atBottom(f); f.append(H.el('div', { class: 'tcard' }, H.el('div', { class: 'tcard-h' }, H.el('i', { class: 'st' }), H.el('span', { class: 'ag' }, 'VERIFICATION'), H.el('span', { class: 'tn' }, t.title || e.task)), H.el('div', { class: 'tcard-b' }, H.el('div', { class: 'vchips' }, ...e.checks.map(c => H.el('span', { class: 'vchip' + (c.ok ? '' : ' bad') }, (c.ok ? '✓ ' : '✗ ') + c.name)))))); if (stick) f.scrollTop = f.scrollHeight; });

/* ---------- tabs ---------- */
function showPane(id) { H.$$('.spane').forEach(p => p.classList.toggle('on', p.id === 'pane-' + id)); H.$$('#side-tabs button').forEach(b => b.classList.toggle('on', b.dataset.p === id)); if (id === 'agent') { const f = toolFeed(); f.scrollTop = f.scrollHeight; $('#new-msgs').hidden = true; } }
H.showPane = showPane;

/* ---------- submit / slash ---------- */
const hist = []; let hi = 0;
const CMDS = [['/help', 'list commands'], ['/status', 'what is every agent doing?'], ['/agents', 'open the Visual Hub roster'], ['/tasks', 'open the kanban board'], ['/kill', 'halt UI — stop voice, freeze display'], ['/resume', 'resume after halt'], ['/lang', 'en|ur — recognition language'], ['/lms', 'open LMS operations'], ['/download', '<url> — universal link downloader'], ['/gesture', 'open gesture control'], ['/memory', 'open local notes'], ['/skills', 'open skills'], ['/soul', 'open SOUL.md editor'], ['/settings', 'open settings'], ['/clear', 'clear this chat']];
H.submit = function (text, source = 'text') {
  text = text.trim(); if (!text) return;
  if (text.startsWith('/')) { const [c, ...r] = text.split(/\s+/), a = r.join(' '); if (slash(c.toLowerCase(), a)) return; }
  hist.push(text); hi = hist.length; const lang = H.isUrdu(text) ? 'ur' : H.config.lang;
  H.ingest({ type: 'chat', role: 'user', text, lang, source });
  const url = text.match(/^(https?:\/\/\S+)$/i); if (url) { H.send({ type: 'download', url: url[1] }); return; }
  H.send({ type: 'command', text, source, lang });
};
H.ask = t => { H.submit(t, 'text'); showPane('voice'); };
function sys(t) { H.ingest({ type: 'chat', role: 'sys', text: t }); showPane('voice'); }
function slash(c, a) {
  switch (c) {
    case '/help': sys(CMDS.map(x => x[0] + '  ' + x[1]).join('\n')); return true;
    case '/status': H.submit('what is the status of all agents?', 'text'); return true;
    case '/agents': case '/tasks': H.hub.open('hub'); return true; case '/kill': H.kill(); return true; case '/resume': H.resume(); return true;
    case '/lang': H.config.lang = a === 'ur' ? 'ur' : 'en'; H.saveConfig(); sys('Recognition language: ' + H.config.lang); return true;
    case '/lms': H.lms.open(); return true; case '/download': if (a) H.send({ type: 'download', url: a }); else H.openDownloader(); return true; case '/gesture': H.hub.open('gesture'); return true;
    case '/memory': H.openDrawer('memory'); return true; case '/skills': H.openDrawer('skills'); return true; case '/soul': H.openDrawer('soul', a || 'helix'); return true; case '/settings': H.openDrawer('setting'); return true;
    case '/clear': chatFeed().innerHTML = ''; H.state.chat = []; return true;
  } return false;
}
/* ---------- security: halt / confirm ---------- */
H.kill = () => { if (!H.send({ type: 'kill' })) H.ingest({ type: 'kill' }); H.voice && H.voice.active && H.voice.stop(); };
H.resume = () => { if (!H.send({ type: 'resume' })) H.ingest({ type: 'resume' }); };
H.bus.on('kill', () => { $('#tb-kill').classList.add('armed'); $('#tb-kill').lastChild.textContent = 'HALTED · RESUME'; sys('■ UI HALT — voice stopped, agent display frozen. Running Hermes tasks are not cancelled.'); H.toast('UI halted — voice stopped; tasks keep running', 'err', 'HALT'); });
H.bus.on('resume', () => { $('#tb-kill').classList.remove('armed'); $('#tb-kill').lastChild.textContent = 'HALT'; sys('Agent display resumed.'); });
let confirmOpen = null;
H.bus.on('confirm.request', e => {
  const risk = e.risk || 'high'; H.audit('confirm.request', `${e.agent}: ${e.action}`);
  const scrim = H.el('div', { class: 'scrim' }), done = ok => { clearInterval(tm); scrim.remove(); confirmOpen = null; H.send({ type: 'confirm.response', id: e.id, approve: ok }); H.ingest({ type: 'chat', role: 'sys', text: (ok ? '✓ Approved: ' : '✗ Denied: ') + e.action }); };
  let left = 60; const cd = H.el('span', { style: 'color:var(--dim)' }, left + 's'), tm = setInterval(() => { cd.textContent = --left + 's'; if (left <= 0) done(false); }, 1000);
  const m = H.el('div', { class: 'panel modal sm risk' }, H.el('div', { class: 'modal-h' }, '⚠ CONFIRMATION REQUIRED', H.el('span', { class: 'spacer' }), cd),
    H.el('div', { class: 'modal-b' }, H.el('div', { style: 'margin-bottom:8px' }, H.el('span', { class: 'tag ' + (risk === 'high' ? 'err' : 'warn') }, risk.toUpperCase() + ' RISK'), H.el('span', { class: 'tag' }, (H.agent(e.agent) || {}).name + ' · ' + e.agent)), H.el('div', { style: 'font-size:13px;line-height:1.5;margin-bottom:8px' }, e.action), H.el('div', { style: 'color:var(--dim);line-height:1.5' }, e.detail || ''), H.el('div', { style: 'margin-top:10px;color:var(--dimmer);font-size:10px' }, 'Auto-denies when the timer ends · Esc = deny · logged to the audit trail')),
    H.el('div', { class: 'modal-f' }, H.el('button', { class: 'btn bad', onclick: () => done(false) }, 'Deny'), H.el('button', { class: 'btn ok', onclick: () => done(true) }, 'Approve once')));
  scrim.append(m); $('#modal-root').append(scrim); confirmOpen = () => done(false);
});
addEventListener('keydown', e => { if (e.key === 'Escape') { if (confirmOpen) confirmOpen(); else { const s = $('#modal-root .scrim'); if (s) s.remove(); const p = $('#sat-panel'); if (p.classList.contains('expanded')) p.classList.remove('expanded'); $('#col-right').classList.remove('focus'); } } });

/* ---------- Visual hub + Gesture ---------- */
const HUB = H.hub = { tab: 'agents' };
HUB.open = t => { H.$$('#town-tabs button').forEach(b => b.classList.toggle('on', b.dataset.t === t)); H.$$('.tview').forEach(v => v.classList.toggle('on', v.id === 'view-' + t)); HUB.tab = t; if (t === 'hub') renderHub(); if (t === 'gesture') renderGesture(); if (t !== 'gesture') stopGesture(); };
let hubT = 0; function renderHub() {
  const v = $('#view-hub'); if (!v.classList.contains('on')) return; v.innerHTML = '';
  const cols = [['BACKLOG', ['backlog', 'ready'], '#7a8a99'], ['RUNNING', ['running'], '#46f0a0'], ['BLOCKED', ['blocked'], '#ffb020'], ['DONE', ['done'], '#2ee6ff'], ['FAILED', ['failed'], '#ff4d5e']], tasks = Object.values(H.state.tasks);
  const kb = H.el('div', { class: 'kanban' }); cols.forEach(c => { const col = H.el('div', { class: 'kcol' }, H.el('h6', null, c[0], H.el('span', null, tasks.filter(t => c[1].includes(t.status)).length))); tasks.filter(t => c[1].includes(t.status)).slice(-8).forEach(t => col.append(H.el('div', { class: 'kcard', style: '--c:' + H.agentColor(t.assignee) }, t.title, H.el('small', null, t.assignee + (t.summary ? ' · ' + t.summary : '')), t.status === 'running' ? H.el('div', { class: 'bar' }, H.el('i', { style: `width:${Math.round((t.progress || 0) * 100)}%` })) : null))); kb.append(col); });
  const rt = H.el('table', { class: 't' }, H.el('tr', null, ...['AGENT', 'STATUS', 'TASK', 'PROFILE'].map(h => H.el('th', null, h)))); H.AGENTS.forEach(a => { const s = H.state.agents[a.id], t = s.task && H.state.tasks[s.task]; rt.append(H.el('tr', null, H.el('td', { style: 'color:' + H.agentColor(a.id) }, a.name), H.el('td', null, H.el('span', { class: 'tag ' + (s.status === 'working' ? 'ok' : s.status === 'error' ? 'err' : s.status === 'idle' ? '' : 'warn') }, H.state.killed ? 'halted' : s.status)), H.el('td', null, t ? t.title : '—'), H.el('td', { style: 'color:var(--dim)' }, a.id))); });
  const dl = H.el('div', null, ...Object.values(H.state.downloads).slice(-6).map(d => H.el('div', { class: 'row2' }, H.el('div', { class: 'grow' }, d.file || d.url, H.el('small', null, d.status + (d.pct != null ? ' · ' + Math.round(d.pct) + '%' : ''))), H.el('span', { class: 'tag ' + (d.status === 'done' ? 'ok' : d.status === 'error' ? 'err' : 'warn') }, d.status)))); if (!Object.keys(H.state.downloads).length) dl.append(H.el('div', { style: 'color:var(--dim)' }, 'No downloads yet. Paste a link in the chat box, or use the button.'));
  v.append(kb, H.el('div', { class: 'hub-grid' }, H.el('div', { class: 'hub-box' }, H.el('h5', null, 'AGENT ROSTER'), rt), H.el('div', { class: 'hub-box' }, H.el('h5', null, 'LINK DOWNLOADER'), dl, H.el('div', { style: 'margin-top:8px' }, H.el('button', { class: 'btn sm', onclick: () => H.openDownloader() }, 'Add link')))));
}
['task.upsert', 'agent.status', 'download', 'kill', 'resume'].forEach(t => H.bus.on(t, () => { clearTimeout(hubT); hubT = setTimeout(renderHub, 120); }));
H.openDownloader = () => {
  const scrim = H.el('div', { class: 'scrim', onclick: e => { if (e.target === scrim) scrim.remove(); } }), inp = H.el('input', { type: 'text', placeholder: 'https://… (video, audio, image, document)', style: 'width:100%' });
  const go = () => { if (/^https?:\/\//i.test(inp.value)) { H.send({ type: 'download', url: inp.value.trim() }); scrim.remove(); HUB.open('hub'); } else H.toast('Enter a full http(s) link', 'warn'); }; inp.onkeydown = e => { if (e.key === 'Enter') go(); };
  scrim.append(H.el('div', { class: 'panel modal sm' }, H.el('div', { class: 'modal-h' }, 'UNIVERSAL LINK DOWNLOADER'), H.el('div', { class: 'modal-b' }, H.el('div', { style: 'color:var(--dim);margin-bottom:8px;line-height:1.5' }, 'Queues a real task for the pc agent: yt-dlp for video/audio, direct fetch for plain files. It reports the saved path when done.'), inp), H.el('div', { class: 'modal-f' }, H.el('button', { class: 'btn', onclick: () => scrim.remove() }, 'Cancel'), H.el('button', { class: 'btn ok', onclick: go }, 'Queue download')))); $('#modal-root').append(scrim); setTimeout(() => inp.focus(), 50);
};
/* gesture */
let gs = { on: false, stream: null, rec: null, raf: 0, last: 0, lastFire: 0 };
const GESTURES = [['Closed_Fist', 'closed fist', 'screenshot', 'pc'], ['Pointing_Up', 'point', 'cursor control (fingertip)', ''], ['Victory', 'two fingers', 'grab / drag', ''], ['Open_Palm', 'open palm', 'STOP — interrupt voice', 'voice.interrupt'], ['Thumb_Down', 'thumb down', 'deny pending confirmation', 'deny']];
function fireGesture(name) {
  const g = GESTURES.find(x => x[0] === name); if (!g) return; H.$$('.gest-list .g').forEach(el => el.classList.toggle('hit', el.dataset.g === name)); setTimeout(() => H.$$('.gest-list .g').forEach(el => el.classList.remove('hit')), 900);
  H.send({ type: 'gesture', name }); H.audit('gesture', name);
  if (name === 'Open_Palm') H.voice.interrupt(); if (name === 'Thumb_Down' && confirmOpen) confirmOpen(); if (name === 'Closed_Fist') H.submit('take a screenshot of my screen', 'text');
}
function renderGesture() {
  const v = $('#view-gesture'); v.innerHTML = ''; const vid = H.el('video', { autoplay: true, muted: true, playsinline: true }), cvs = H.el('canvas'), st = H.el('div', { style: 'color:var(--dim);margin:6px 0' }, gs.on ? 'Tracking…' : 'Camera off. Gesture control is lightweight: ~10 fps, only while this tab is open.');
  const list = H.el('div', { class: 'gest-list' }, ...GESTURES.map(g => H.el('div', { class: 'g', 'data-g': g[0] }, H.el('b', null, g[1]), g[2], H.el('button', { class: 'btn sm', style: 'margin-left:auto', onclick: () => fireGesture(g[0]) }, 'simulate'))));
  const b = H.el('button', { class: 'btn' + (gs.on ? ' bad' : ' ok'), onclick: async () => { if (gs.on) { stopGesture(); renderGesture(); } else startGesture(vid, cvs, st, b); } }, gs.on ? 'Stop camera' : 'Start camera');
  v.append(H.el('div', { class: 'gest-wrap' }, H.el('div', null, H.el('div', { class: 'gest-cam' }, vid, cvs), st, b), H.el('div', null, H.el('h5', { style: 'color:var(--accent);letter-spacing:.18em;font-size:10px;margin-bottom:6px' }, 'GESTURE MAP'), list, H.el('div', { style: 'color:var(--dimmer);margin-top:8px;font-size:10px;line-height:1.5' }, 'Recognition uses MediaPipe Gesture Recognizer (lazy-loaded from jsDelivr when you press Start). Offline? Use “simulate” — the events are identical.'))));
  if (gs.on && gs.stream) vid.srcObject = gs.stream;
}
async function startGesture(vid, cvs, st, btn) {
  try { gs.stream = await navigator.mediaDevices.getUserMedia({ video: { width: 480, height: 360 } }); vid.srcObject = gs.stream; gs.on = true; btn.textContent = 'Stop camera'; btn.className = 'btn bad'; st.textContent = 'Loading hand model…'; } catch (e) { st.textContent = 'Camera unavailable: ' + (e.name || e); return; }
  try {
    const mp = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs'), fs = await mp.FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
    gs.rec = await mp.GestureRecognizer.createFromOptions(fs, { baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task' }, runningMode: 'VIDEO', numHands: 1 }); st.textContent = 'Tracking — show a gesture';
    const ctx = cvs.getContext('2d'); const loop = () => { if (!gs.on) return; gs.raf = setTimeout(loop, 100); if (vid.readyState < 2) return; try { const r = gs.rec.recognizeForVideo(vid, performance.now()); cvs.width = vid.videoWidth; cvs.height = vid.videoHeight; ctx.clearRect(0, 0, cvs.width, cvs.height); const lm = r.landmarks && r.landmarks[0]; if (lm) { ctx.fillStyle = '#2ee6ff'; lm.forEach(p => { ctx.beginPath(); ctx.arc(p.x * cvs.width, p.y * cvs.height, 3, 0, 6.28); ctx.fill(); }); } const g = r.gestures && r.gestures[0] && r.gestures[0][0]; if (g && g.score > .7 && performance.now() - gs.lastFire > 1400) { gs.lastFire = performance.now(); fireGesture(g.categoryName); st.textContent = 'Detected: ' + g.categoryName; } } catch (e) { /* frame skipped */ } }; loop();
  } catch (e) { st.textContent = 'Hand model could not load (offline?). Camera preview works; use “simulate” buttons.'; }
}
function stopGesture() { gs.on = false; clearTimeout(gs.raf); try { gs.rec && gs.rec.close(); } catch (e) { /* noop */ } gs.rec = null; if (gs.stream) { gs.stream.getTracks().forEach(t => t.stop()); gs.stream = null; } }

/* ---------- LMS ---------- */
const LMS = H.lms = {};
const STEPS = [['pending', 'Found'], ['downloading', 'Lecture'], ['reading', 'Read'], ['drafting', 'Draft'], ['awaiting_confirm', 'Your OK'], ['uploading', 'Upload'], ['submitted', 'Done']];
const dueTxt = ms => { const d = ms - Date.now(); if (d < 0) return 'overdue'; const h = d / 3.6e6; return h < 48 ? Math.floor(h) + 'h ' + Math.floor((h % 1) * 60) + 'm' : Math.floor(h / 24) + 'd ' + Math.floor(h % 24) + 'h'; };
LMS.badge = () => { const L = H.state.lms; const n = L ? L.items.filter(i => i.status !== 'submitted' && i.due && i.due - Date.now() < 48 * 3.6e6).length : 0; const b = $('#tb-lms-badge'); b.hidden = !n; b.textContent = n; };
LMS.open = function () {
  let scrim = $('#modal-root .scrim.lms'); if (scrim) scrim.remove(); scrim = H.el('div', { class: 'scrim lms', onclick: e => { if (e.target === scrim) scrim.remove(); } }); const box = H.el('div', { class: 'panel modal' }); scrim.append(box); $('#modal-root').append(scrim); LMS.draw();
};
LMS.draw = function () {
  const box = $('#modal-root .scrim.lms .modal'); if (!box) return; const L = H.state.lms; box.innerHTML = '';
  box.append(H.el('div', { class: 'modal-h' }, 'LMS OPERATIONS', H.el('span', { class: 'tag' }, 'agent: lms'), H.el('span', { class: 'tag' }, 'read-only snapshot'), H.el('span', { class: 'spacer' }), H.el('span', { style: 'color:var(--dim);font:11px var(--mono);letter-spacing:0' }, L ? (L.live ? 'synced ' + H.hhmm(L.synced) : 'unreachable') : 'contacting LMS…'), H.el('button', { class: 'icon-btn', onclick: () => $('#modal-root .scrim.lms').remove() }, '✕')));
  const body = H.el('div', { class: 'modal-b' }); box.append(body); if (!L) { body.append('Contacting LMS…'); return; }
  const left = H.el('div'), right = H.el('div');
  left.append(H.el('h5', { style: 'color:var(--dim);font-size:10px;letter-spacing:.18em;margin-bottom:8px' }, 'DEADLINES · ASSIGNMENTS · LABS'));
  L.items.slice().sort((a, b) => a.due - b.due).forEach(it => {
    const idx = Math.max(0, STEPS.findIndex(s => s[0] === it.status)), urgent = !!it.due && it.due - Date.now() < 36e5 * 24 && it.status !== 'submitted';
    const card = H.el('div', { class: 'lms-card' }, H.el('h4', null, H.el('span', { class: 'tag' }, it.kind), it.title, H.el('span', { class: 'due' + (urgent ? ' urgent' : '') }, it.status === 'submitted' ? 'submitted' : !it.due ? 'no due date' : it.due < Date.now() ? 'overdue' : 'due in ' + dueTxt(it.due))), H.el('div', { style: 'color:var(--dim);margin-top:2px' }, it.course + ' · lecture: ' + (it.lecture || '—')),
      H.el('div', { class: 'pipe' }, ...STEPS.map((s, i) => H.el('div', { class: 'stp' + (i < idx || it.status === 'submitted' ? ' done' : i === idx ? ' cur' : '') }, s[1]))));
    if (it.draft && (it.status === 'awaiting_confirm' || it.status === 'submitted')) card.append(H.el('div', { class: 'draft', dir: 'auto' }, it.draft.text), H.el('div', { style: 'color:var(--dim)' }, it.draft.words + ' words · file: ' + it.draft.file));
    const acts = H.el('div', { style: 'display:flex;gap:6px;margin-top:6px;align-items:center' });
    if (it.status === 'pending') acts.append(H.el('button', { class: 'btn sm', disabled: true, title: 'Not wired: the lms agent workflow is not implemented.' }, 'Lecture → draft (not wired)'));
    else if (it.status === 'awaiting_confirm') acts.append(H.el('span', { class: 'tag warn' }, 'not wired'), H.el('span', { style: 'color:var(--warn);font-size:10px' }, 'Drafting and upload are not implemented; nothing will be uploaded.'));
    else if (it.status !== 'submitted') acts.append(H.el('span', { class: 'tag warn' }, it.status + '…'));
    card.append(acts); left.append(card);
  });
  right.append(H.el('h5', { style: 'color:var(--dim);font-size:10px;letter-spacing:.18em;margin-bottom:8px' }, 'ATTENDANCE'));
  L.courses.forEach(c => { const total = +c.total || 0, present = +c.present || 0, has = total > 0, pct = has ? present / total * 100 : 0, safe = has ? Math.floor(present / .75 - total) : 0, col = !has ? 'var(--dim)' : pct < 75 ? 'var(--err)' : pct < 82 ? 'var(--warn)' : 'var(--ok)'; right.append(H.el('div', { class: 'lms-card' }, H.el('div', { style: 'display:flex;justify-content:space-between' }, H.el('span', null, c.name), H.el('b', { style: 'color:' + col }, has ? pct.toFixed(0) + '%' : '—')), H.el('div', { class: 'att-bar' }, H.el('i', { style: `width:${pct}%;background:${col}` })), H.el('div', { style: 'color:var(--dim);font-size:10px' }, has ? `${present}/${total} classes · ` + (pct < 75 ? 'BELOW 75% — attend every class' : `can still miss ${Math.max(0, safe)}`) : 'no attendance data'))); });
  right.append(H.el('div', { style: 'color:var(--dimmer);font-size:10px;line-height:1.5;margin-top:8px' }, L.live ? 'Read-only snapshot from the LMS portal.' : 'LMS unreachable — no data.'));
  body.append(H.el('div', { class: 'lms-grid' }, left, right));
};
['lms.data', 'lms.update'].forEach(t => H.bus.on(t, () => { LMS.draw(); LMS.badge(); })); setInterval(() => { if ($('#modal-root .scrim.lms')) LMS.draw(); LMS.badge(); }, 30000);

/* ---------- media link (camera / screen local preview) ---------- */
function mediaInit() {
  const vid = $('#media-video'), off = $('#media-off'), tag = $('#media-tag'); let stream = null;
  const stop = () => { if (stream) stream.getTracks().forEach(t => t.stop()); stream = null; vid.hidden = true; vid.srcObject = null; off.hidden = false; tag.hidden = true; };
  const start = async kind => { stop(); try { stream = kind === 'screen' ? await navigator.mediaDevices.getDisplayMedia({ video: true }) : await navigator.mediaDevices.getUserMedia({ video: true }); vid.srcObject = stream; vid.hidden = false; off.hidden = true; tag.hidden = false; tag.textContent = (kind === 'screen' ? 'SCREEN' : 'CAMERA') + ' · LOCAL PREVIEW'; stream.getVideoTracks()[0].onended = stop; } catch (e) { H.toast((kind === 'screen' ? 'Screen share' : 'Camera') + ' unavailable: ' + (e.name || 'denied'), 'warn', 'MEDIA LINK'); } };
  $('#btn-cam').onclick = () => stream ? stop() : start('cam'); $('#btn-screen').onclick = () => stream ? stop() : start('screen'); $('#btn-media-more').onclick = () => H.toast('Local preview only — frames never leave this window. The vision-agent frame link is not wired yet.', '', 'MEDIA LINK');
  const fx = $('#media-fx'), x = fx.getContext('2d'); H.loop.add((dt, t) => { const w = fx.clientWidth, h = fx.clientHeight; if (fx.width !== w) { fx.width = w; fx.height = h; } x.clearRect(0, 0, w, h); x.strokeStyle = 'rgba(46,230,255,.6)'; x.lineWidth = 1; [[6, 6, 1, 1], [w - 6, 6, -1, 1], [6, h - 6, 1, -1], [w - 6, h - 6, -1, -1]].forEach(c => { x.beginPath(); x.moveTo(c[0], c[1] + c[3] * 10); x.lineTo(c[0], c[1]); x.lineTo(c[0] + c[2] * 10, c[1]); x.stroke(); }); const y = (t * 40) % h; const g = x.createLinearGradient(0, y - 12, 0, y + 2); g.addColorStop(0, 'rgba(46,230,255,0)'); g.addColorStop(1, 'rgba(46,230,255,.25)'); x.fillStyle = g; x.fillRect(0, y - 12, w, 14); }, { fps: 20, vis: () => true });
}

/* ---------- notes / audit / terminal / history ---------- */
function notesInit() {
  const p = $('#pane-notes'), ta = H.el('textarea', { placeholder: 'Scratch notes — saved locally in this browser.', spellcheck: 'false' }); ta.value = H.store.get('notes', ''); ta.oninput = () => H.store.set('notes', ta.value); const au = H.el('div', { class: 'audit' });
  const drawA = () => { au.innerHTML = ''; H.store.get('audit', []).slice(-60).reverse().forEach(a => au.append(H.el('div', null, H.hhmm(a.t) + ' ', H.el('b', null, a.k), ' ' + a.x))); };
  p.append(H.el('h5', { style: 'color:var(--accent);font:600 10px var(--head);letter-spacing:.2em' }, 'NOTES'), ta, H.el('h5', { style: 'color:var(--accent);font:600 10px var(--head);letter-spacing:.2em;margin-top:4px' }, 'AUDIT TRAIL'), au); drawA(); H.bus.on('audit', drawA);
  const tl = $('#term-log'); H.bus.on('event', e => { if (e.type === 'voice.level') return; const s = JSON.stringify(e); tl.textContent += H.hhmm() + ' ' + (s.length > 260 ? s.slice(0, 260) + '…' : s) + '\n'; if (tl.textContent.length > 40000) tl.textContent = tl.textContent.slice(-30000); if (atBottom(tl)) tl.scrollTop = tl.scrollHeight; });
}
function sessions() { return H.store.get('sessions', []); }
function newSession() { const msgs = H.state.chat.filter(m => m.role !== 'sys'); if (msgs.length) { const s = sessions(); s.unshift({ t: Date.now(), title: (msgs.find(m => m.role === 'user') || msgs[0]).text.slice(0, 50), chat: H.state.chat.slice(-80) }); H.store.set('sessions', s.slice(0, 20)); } H.state.chat = []; H.state.tools = []; chatFeed().innerHTML = ''; toolFeed().innerHTML = ''; showPane('voice'); H.toast('New session', ''); }
function histDraw() { const p = $('#pane-hist'); p.innerHTML = ''; p.append(H.el('h5', { style: 'color:var(--accent);font:600 10px var(--head);letter-spacing:.2em;margin-bottom:8px' }, 'SESSION HISTORY')); const s = sessions(); if (!s.length) p.append(H.el('div', { style: 'color:var(--dim)' }, 'Nothing saved yet — press + to start a new session and keep this one.')); s.forEach(x => p.append(H.el('div', { class: 'res', onclick: () => { chatFeed().innerHTML = ''; x.chat.forEach(addMsg); showPane('voice'); } }, H.el('span', { class: 'ico' }, '›'), x.title || '(untitled)', H.el('small', null, new Date(x.t).toLocaleString())))); }

/* ---------- init ---------- */
H.initSide = function () {
  H.$$('#side-tabs button').forEach(b => b.onclick = () => showPane(b.dataset.p)); H.$$('#town-tabs button').forEach(b => b.onclick = () => HUB.open(b.dataset.t));
  const inp = $('#cmd-input'), menu = $('#slash-menu'); let mi = 0;
  const drawMenu = () => { const q = inp.value; if (!q.startsWith('/') || q.includes(' ')) { menu.hidden = true; return; } const items = CMDS.filter(c => c[0].startsWith(q.toLowerCase())); menu.hidden = !items.length; menu.innerHTML = ''; mi = Math.min(mi, items.length - 1); items.forEach((c, i) => menu.append(H.el('div', { class: i === mi ? 'on' : '', onmousedown: e => { e.preventDefault(); inp.value = c[0] + ' '; menu.hidden = true; inp.focus(); } }, H.el('b', null, c[0]), H.el('span', null, c[1])))); menu._items = items; };
  inp.oninput = () => { mi = 0; drawMenu(); };
  inp.onkeydown = e => {
    if (!menu.hidden) { if (e.key === 'ArrowDown') { mi = (mi + 1) % menu._items.length; drawMenu(); e.preventDefault(); return; } if (e.key === 'ArrowUp') { mi = (mi + menu._items.length - 1) % menu._items.length; drawMenu(); e.preventDefault(); return; } if (e.key === 'Tab' || (e.key === 'Enter' && menu._items[mi] && inp.value !== menu._items[mi][0])) { inp.value = menu._items[mi][0] + ' '; menu.hidden = true; e.preventDefault(); return; } }
    if (e.key === 'Enter') { H.submit(inp.value); inp.value = ''; menu.hidden = true; } else if (e.key === 'ArrowUp' && hist.length) { hi = Math.max(0, hi - 1); inp.value = hist[hi] || ''; e.preventDefault(); } else if (e.key === 'ArrowDown' && hist.length) { hi = Math.min(hist.length, hi + 1); inp.value = hist[hi] || ''; e.preventDefault(); }
  };
  $('#btn-send').onclick = () => { H.submit(inp.value); inp.value = ''; menu.hidden = true; }; $('#btn-mic').onclick = e => H.voice.dictate(e.currentTarget);
  $('#btn-attach').onclick = () => H.toast('File upload is not wired yet — use the document agent or paste a link.', 'warn', 'ATTACH');
  const sp = $('#side-panel'); sp.addEventListener('dragover', e => { e.preventDefault(); }); sp.addEventListener('drop', e => { e.preventDefault(); if (e.dataTransfer.files.length) H.toast('File upload is not wired yet — drop a link instead.', 'warn', 'ATTACH'); else { const u = e.dataTransfer.getData('text'); if (/^https?:/.test(u)) H.send({ type: 'download', url: u }); } });
  $('#new-msgs').onclick = () => { const f = toolFeed(); f.scrollTop = f.scrollHeight; $('#new-msgs').hidden = true; }; toolFeed().onscroll = () => { if (atBottom(toolFeed())) $('#new-msgs').hidden = true; };
  $('#sd-new').onclick = newSession; $('#sd-history').onclick = () => { histDraw(); H.$$('.spane').forEach(p => p.classList.toggle('on', p.id === 'pane-hist')); }; $('#sd-term').onclick = () => { H.$$('.spane').forEach(p => p.classList.toggle('on', p.id === 'pane-term')); }; $('#sd-full').onclick = () => $('#col-right').classList.toggle('focus');
  // top bar
  $('#tb-demo').onclick = () => H.openDrawer('setting'); $('#tb-lms').onclick = () => LMS.open(); $('#tb-kill').onclick = () => H.state.killed ? H.resume() : H.kill();
  $('#tb-full').onclick = () => { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => { }); };
  const clk = () => { $('#tb-clock').textContent = new Date().toLocaleString([], { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }); }; clk(); setInterval(clk, 15000);
  const mode = () => { const b = $('#tb-demo'); b.classList.toggle('live', H.state.mode === 'live'); $('#tb-bridge').textContent = H.state.mode === 'live' ? 'BRIDGE LIVE' : 'BRIDGE OFFLINE'; $('#st-online span').textContent = H.state.killed ? 'Halted' : H.state.mode === 'live' ? 'Online' : 'Offline'; }; H.bus.on('mode', mode); mode();
  notesInit(); mediaInit(); LMS.badge(); H.bus.on('voice.state', e => { if (e.state === 'thinking') showPane('voice'); });
};
})();
