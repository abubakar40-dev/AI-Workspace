/* =====================================================================================
   HELIX COMMAND DECK — single-file UI
   =====================================================================================
   BRIDGE PROTOCOL (for the OpenCode integration — JSON text frames over WebSocket)
   -------------------------------------------------------------------------------------
   Default URL: ws://127.0.0.1:8765   (override: ?bridge=ws://127.0.0.1:PORT  or Settings → Bridge)
   The UI only accepts loopback URLs (127.0.0.1 / localhost / [::1]) — spec §16.4: never 0.0.0.0.
   While no bridge is reachable the UI shows BRIDGE OFFLINE. There is no built-in demo backend:
   every number on screen is either read from the bridge or explicitly labelled local/demo.

   SERVER → UI events (all optional, unknown fields ignored):
     {type:'hello', model:'openrouter/free', agents:[ids...]}
     {type:'agent.status', agent:'research', status:'idle|working|blocked|waiting|error|offline',
        task:'t12', note:'text', progress:0..1, where:'desk|rack|shelf|printer|board|meeting'}
     {type:'task.upsert', task:{id,title,assignee,status:'backlog|ready|running|blocked|done|failed',
        progress:0..1, deps:[ids], parent, summary}}
     {type:'interact', kind:'brief|handoff|review|help|chat', from:'helix', to:'research', text:'', task:'t12', artifact:'file.md'}
     {type:'tool.call', agent:'research', tool:'tavily_search', input:{...}, output:{...}, ms:1840, ok:true}
     {type:'verify', task:'t12', checks:[{name:'file exists',ok:true},...]}
     {type:'chat', role:'user|helix|agent', agent:'research', text:'...', lang:'en|ur'}
     {type:'voice.state', state:'idle|listening|thinking|speaking|error'}   {type:'voice.level', level:0..1}
     {type:'think', text:'reasoning line'}                                  (feeds the orb "THINKING" stream)
     {type:'model', name:'nvidia/nemotron-3-ultra:free', reason:'429 on previous', chain:[...]}
     {type:'ctx', used:123456, max:1000000}
     {type:'confirm.request', id:'c1', agent:'pc', action:'Delete 12 files in ~/Desktop/old', risk:'high|medium', detail:'...'}
     {type:'alert', id, title, lat, lon, country, level:'warn|crit'}      {type:'headline', title, source, url, lat, lon, ts}
     {type:'lms.data', lms:{synced, courses:[...], items:[...]}}          {type:'lms.update', item:{...}}
     {type:'download', id, url, status:'queued|running|done|error', pct, file}
     {type:'kill'} / {type:'resume'}      {type:'skills.list', items:[...]}
     {type:'souls', souls:{agent:text}}   {type:'soul.saved', agent, ok, error, path}
   UI → SERVER:
     {type:'command', text, source:'text|voice', lang:'en|ur'}
     {type:'confirm.response', id, approve:true|false}      {type:'kill'} {type:'resume'}
     {type:'voice.start'} {type:'voice.stop'} {type:'voice.interrupt'}
     {type:'download', url}    {type:'soul.update', agent, text}    {type:'gesture', name}
   ===================================================================================== */
(function () {
'use strict';
const H = window.H = { v: '0.1' };

/* ---------- tiny helpers ---------- */
H.$ = (s, r = document) => r.querySelector(s);
H.$$ = (s, r = document) => Array.from(r.querySelectorAll(s));
H.el = (tag, attrs, ...kids) => {
  const e = document.createElement(tag);
  if (attrs) for (const k in attrs) {
    const v = attrs[k];
    if (k === 'class') e.className = v; else if (k === 'html') e.innerHTML = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else if (v !== false && v != null) e.setAttribute(k, v === true ? '' : v);
  }
  kids.flat().forEach(c => c != null && e.append(c.nodeType ? c : document.createTextNode(c)));
  return e;
};
H.esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
H.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
H.lerp = (a, b, t) => a + (b - a) * t;
H.rand = (a, b) => a + Math.random() * (b - a);
H.pick = a => a[Math.floor(Math.random() * a.length)];
H.sleep = ms => new Promise(r => setTimeout(r, ms));
H.uid = (p = 'id') => p + Math.random().toString(36).slice(2, 8);
H.now = () => Date.now();
H.hhmm = (t = Date.now()) => new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
H.isUrdu = s => /[؀-ۿ]/.test(s || '');
H.store = {
  get(k, d) { try { const v = localStorage.getItem('helix.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('helix.' + k, JSON.stringify(v)); } catch (e) { /* storage unavailable */ } }
};

/* ---------- event bus ---------- */
H.bus = {
  m: {},
  on(t, f) { (this.m[t] = this.m[t] || []).push(f); return () => { this.m[t] = this.m[t].filter(x => x !== f); }; },
  emit(t, p) {
    (this.m[t] || []).slice().forEach(f => { try { f(p); } catch (e) { console.error('[bus]', t, e); } });
    (this.m['*'] || []).slice().forEach(f => { try { f(t, p); } catch (e) { console.error(e); } });
  }
};

/* ---------- configuration (persisted) ---------- */
H.config = Object.assign({
  accent: 'cyan', quality: 'auto', lang: 'en', speak: true, wake: false, bargeIn: true,
  bridgeUrl: 'ws://127.0.0.1:8765', autoConnect: true, voiceName: '', rate: 1.0, reasoning: false,
  autoRotate: true, layers: { air: true, ship: true, sat: true, quake: true, cam: true, alert: true }
}, H.store.get('config', {}));
H.saveConfig = () => H.store.set('config', H.config);

const ACCENTS = { cyan: ['46,230,255', '#2ee6ff', '#18b7d6'], green: ['70,240,160', '#46f0a0', '#22c07a'], amber: ['255,176,32', '#ffb020', '#d98c00'], violet: ['155,123,255', '#9b7bff', '#7656e0'] };
H.setAccent = name => {
  const a = ACCENTS[name] || ACCENTS.cyan, r = document.documentElement.style;
  r.setProperty('--accent-rgb', a[0]); r.setProperty('--accent', a[1]); r.setProperty('--accent2', a[2]);
  H.config.accent = name; H.saveConfig(); H.bus.emit('accent', { name, hex: a[1] });
};
H.ACCENTS = ACCENTS;

/* ---------- agents (display names are a UI concern; ids = Hermes profile ids) ---------- */
H.AGENTS = [
  { id: 'helix',    name: 'HELIX',  role: 'CEO / Orchestrator',  skin: '#f1c9a5', hair: '#dfe9ff', outfit: '#1d4e7a', acc: 'visor' },
  { id: 'research', name: 'Alice',  role: 'Research',            skin: '#f3cfb0', hair: '#8a3b2a', outfit: '#2b7a6b', acc: 'glasses' },
  { id: 'files',    name: 'Bob',    role: 'File / Documents',    skin: '#d9a67a', hair: '#2b2118', outfit: '#a1632b', acc: 'cap' },
  { id: 'pc',       name: 'Carol',  role: 'PC Control',          skin: '#f0c4a0', hair: '#161616', outfit: '#5b3a8a', acc: 'headset' },
  { id: 'vision',   name: 'Dave',   role: 'Vision',              skin: '#c68b62', hair: '#3a2a1a', outfit: '#8a2b2b', acc: 'goggles' },
  { id: 'dev',      name: 'Eve',    role: 'Development',         skin: '#f3d3bd', hair: '#d2a03a', outfit: '#2a4a8a', acc: 'phones' },
  { id: 'career',   name: 'Frank',  role: 'Career',              skin: '#e4b894', hair: '#6a6a6a', outfit: '#3c3c4c', acc: 'tie' },
  { id: 'comms',    name: 'Grace',  role: 'Communication',       skin: '#b97a55', hair: '#1a0f0a', outfit: '#b0456b', acc: 'bun' },
  { id: 'sysmon',   name: 'Heidi',  role: 'System Monitor',      skin: '#f2c9a8', hair: '#c0392b', outfit: '#2a7a3a', acc: 'hardhat' },
  { id: 'lms',      name: 'Ivan',   role: 'LMS / Study',         skin: '#e8bf9a', hair: '#4a2d14', outfit: '#8a7a1e', acc: 'scarf' }
];
H.agent = id => H.AGENTS.find(a => a.id === id);
H.agentColor = id => ({ helix: '#2ee6ff', research: '#34d6b4', files: '#ff9a4a', pc: '#a98bff', vision: '#ff6b6b', dev: '#5b9bff', career: '#c8c8d8', comms: '#ff6fa5', sysmon: '#6fe86f', lms: '#e8d34a' }[id] || '#2ee6ff');

/* ---------- state ---------- */
H.state = {
  mode: 'offline', killed: false,
  agents: {}, tasks: {}, chat: [], tools: [], events: [],
  voice: 'idle', level: 0, think: [],
  model: '', chain: [], ctx: { used: 0, max: 1000000 },
  alerts: [], headlines: [], lms: null, downloads: {}, memory: [], skills: [], souls: {}
};
H.AGENTS.forEach(a => { H.state.agents[a.id] = { id: a.id, status: 'idle', task: null, progress: 0, note: '', where: 'desk', model: '' }; });

/* ---------- toast / audit ---------- */
H.toast = (msg, kind = '', title = '') => {
  const t = H.el('div', { class: 'toast ' + kind }, title ? H.el('b', null, title) : null, msg);
  H.$('#toasts').append(t); setTimeout(() => { t.style.transition = '.4s'; t.style.opacity = 0; setTimeout(() => t.remove(), 400); }, 4200);
};
H.audit = (kind, text) => {
  const log = H.store.get('audit', []); log.push({ t: Date.now(), k: kind, x: String(text).slice(0, 240) });
  if (log.length > 400) log.splice(0, log.length - 400); H.store.set('audit', log); H.bus.emit('audit', log[log.length - 1]);
};

/* ---------- icons used by JS-built UI ---------- */
H.icon = (n, s = 14) => ({
  tool: `<svg viewBox="0 0 24 24" width="${s}" height="${s}"><path d="M14.7 6.3a4 4 0 00-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 005.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z" fill="none" stroke="currentColor" stroke-width="1.7"/></svg>`,
  check: `<svg viewBox="0 0 24 24" width="${s}" height="${s}"><path d="M5 12l5 5 9-10" fill="none" stroke="currentColor" stroke-width="2.4"/></svg>`,
  x: `<svg viewBox="0 0 24 24" width="${s}" height="${s}"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2"/></svg>`,
  doc: `<svg viewBox="0 0 24 24" width="${s}" height="${s}"><path d="M6 3h8l4 4v14H6zM14 3v4h4M9 12h6M9 16h6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>`
}[n] || '');

/* ---------- quality governor (laptop is CPU-only, ~7GB RAM) ---------- */
H.quality = { level: 'high', dpr: 1, particles: 1, tex: 4096 };
H.setQuality = lv => {
  const q = {
    low:  { level: 'low',  dpr: 1,                                   particles: .5, tex: 2048, clouds: false, fps: 30 },
    med:  { level: 'med',  dpr: Math.min(1.25, devicePixelRatio || 1), particles: .62, tex: 2048, clouds: true,  fps: 45 },
    high: { level: 'high', dpr: Math.min(2, devicePixelRatio || 1),    particles: 1,   tex: 4096, clouds: true,  fps: 60 }
  }[lv] || null;
  if (!q) return; H.quality = q; H.bus.emit('quality', q);
};
H.detectQuality = () => {
  if (H.config.quality !== 'auto') return H.config.quality;
  let soft = false;
  try {
    const c = document.createElement('canvas'), gl = c.getContext('webgl'); const ext = gl && gl.getExtension('WEBGL_debug_renderer_info');
    const r = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : '';
    soft = /swiftshader|llvmpipe|software|softpipe|basic render/i.test(r);
  } catch (e) { soft = true; }
  const mem = navigator.deviceMemory || 8, cores = navigator.hardwareConcurrency || 4;
  if (soft || mem <= 4 || cores <= 2) return 'low';
  if (mem <= 8 || cores <= 4) return 'med';
  return 'high';
};

/* ---------- ingest: every server event goes through here ---------- */
H.ingest = evt => {
  if (!evt || !evt.type) return;
  const S = H.state;
  S.events.push(evt); if (S.events.length > 300) S.events.shift();
  switch (evt.type) {
    case 'hello': if (evt.model) S.model = evt.model; break;
    case 'agent.status': {
      const a = S.agents[evt.agent]; if (!a) break;
      Object.assign(a, { status: evt.status || a.status, task: evt.task !== undefined ? evt.task : a.task, note: evt.note ?? a.note, progress: evt.progress ?? a.progress, where: evt.where || 'desk' });
      if (evt.status === 'idle') { a.progress = 0; a.task = null; a.note = evt.note || ''; }
      break;
    }
    case 'task.upsert': {
      const t = evt.task; S.tasks[t.id] = Object.assign(S.tasks[t.id] || { created: Date.now() }, t, { updated: Date.now() });
      const d = S.downloads[t.id];
      if (d) { d.status = t.status === 'done' ? 'done' : (t.status === 'failed' || t.status === 'error') ? 'error' : t.status === 'running' ? 'running' : 'queued'; d.pct = Math.round((t.progress || 0) * 100); }
      break;
    }
    case 'task.remove': delete S.tasks[evt.id]; break;
    case 'tool.call': evt.t = evt.t || Date.now(); S.tools.push(evt); if (S.tools.length > 200) S.tools.shift(); break;
    case 'chat': evt.t = evt.t || Date.now(); S.chat.push(evt); if (S.chat.length > 300) S.chat.shift(); break;
    case 'voice.state': S.voice = evt.state; break;
    case 'voice.level': S.level = evt.level; break;
    case 'think': S.think.push(evt.text); if (S.think.length > 12) S.think.shift(); break;
    case 'model': S.model = evt.name; if (evt.chain) S.chain = evt.chain; break;
    case 'ctx': S.ctx = { used: evt.used, max: evt.max || S.ctx.max }; break;
    case 'alert': { const i = S.alerts.findIndex(x => x.id === evt.id); if (i >= 0) S.alerts[i] = evt; else S.alerts.unshift(evt); break; }
    case 'headline': S.headlines.unshift(evt); S.headlines = S.headlines.slice(0, 30); break;
    case 'lms.data': S.lms = evt.lms; break;
    case 'lms.update': if (S.lms) { const i = S.lms.items.findIndex(x => x.id === evt.item.id); if (i >= 0) Object.assign(S.lms.items[i], evt.item); else S.lms.items.push(evt.item); } break;
    case 'download': S.downloads[evt.id] = Object.assign(S.downloads[evt.id] || {}, evt); break;
    case 'kill': S.killed = true; break;
    case 'resume': S.killed = false; break;
    case 'souls': S.souls = Object.assign(S.souls || {}, evt.souls || {}); break;
    case 'skills.list': S.skills = evt.items || []; break;
  }
  H.bus.emit(evt.type, evt);
  H.bus.emit('event', evt);
};

/* ---------- bridge: WebSocket (loopback only), reconnect, no demo fallback ---------- */
H.bridge = {
  ws: null, url: '', timer: null, connected: false,
  okUrl(u) { return /^wss?:\/\/(127\.0\.0\.1|localhost|\[::1\])(:\d{2,5})?(\/[^\s]*)?$/i.test(u); },
  connect(u, quiet) {
    u = u || H.config.bridgeUrl;
    if (!this.okUrl(u)) { H.toast('Bridge URL must be loopback (127.0.0.1 / localhost). Refused: ' + u, 'err', 'SECURITY'); return false; }
    try { if (this.ws) { this.ws.onclose = null; this.ws.close(); } } catch (e) { /* ignore */ }
    let ws; try { ws = new WebSocket(u); } catch (e) { return false; }
    this.ws = ws; this.url = u;
    ws.onopen = () => {
      this.connected = true; H.state.mode = 'live'; H.resetLive();
      ws.send(JSON.stringify({ type: 'hello', client: 'helix-ui', v: H.v }));
      ws.send(JSON.stringify({ type: 'ui.ready', v: H.v, note: 'send full snapshot: hello, agent.status x all, task.upsert x all, lms.data, souls, skills.list, model, ctx' }));
      H.bus.emit('mode', 'live'); if (!quiet) H.toast('Bridge connected: ' + u, 'ok', 'ONLINE');
    };
    ws.onmessage = ev => { try { H.ingest(JSON.parse(ev.data)); } catch (e) { console.warn('bad frame', e); } };
    ws.onclose = () => {
      const was = this.connected; this.connected = false;
      if (was) { H.toast('Bridge lost — reconnecting…', 'warn', 'OFFLINE'); }
      H.state.mode = 'offline'; H.bus.emit('mode', 'offline');
      clearTimeout(this.timer); if (H.config.autoConnect) this.timer = setTimeout(() => this.connect(null, true), 12000);
    };
    ws.onerror = () => { /* onclose handles it */ };
    return true;
  },
  send(m) { if (this.connected && this.ws.readyState === 1) { this.ws.send(JSON.stringify(m)); return true; } return false; },
  /* HTTP base for fetch()/XHR. The bridge speaks WebSocket, but the browser
     refuses fetch('ws://...') — only http/https work. ws->http is the same
     origin, same port, so the plain swap is correct. */
  httpUrl() { return (this.url || '').replace(/^ws:/, 'http:').replace(/^wss:/, 'https:'); }
};
H.send = msg => {
  if (msg.type === 'command' || msg.type === 'confirm.response' || msg.type === 'kill' || msg.type === 'resume') H.audit(msg.type, msg.text || msg.id || '');
  if (H.bridge && H.bridge.connected && H.bridge.send(msg)) return true;
  if (!H._offToast || Date.now() - H._offToast > 4000) { H._offToast = Date.now(); H.toast('Bridge not connected — command not sent', 'err', 'OFFLINE'); }
  return false;
};
/* Fresh live snapshot: drop only state the bridge will resend. Chat, local notes
   and event history are real and survive a reconnect; skills/souls are replaced
   when the snapshot arrives. */
H.resetLive = () => {
  const S = H.state;
  S.tasks = {}; S.lms = null; S.downloads = {}; S.model = ''; S.chain = []; S.ctx = { used: 0, max: S.ctx.max };
};

})();
