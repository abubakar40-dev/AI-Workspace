/* =====================================================================================
   WORLD MONITOR — "god's-eye" globe: aircraft · ships · satellites · quakes · cams · alerts
   Live feeds are fetched straight from the browser when reachable (USGS, OpenSky, CelesTrak, GDELT);
   every layer falls back to a clearly-labelled SIM so the globe is never empty. The bridge can also push
   {type:'alert'|'headline'} events. (Swap point for the installed gods-eye-view: replace G.fetchers.*)
   ===================================================================================== */
(function () {
'use strict';
const H = window.H, G = H.globe, D2R = Math.PI / 180, R2D = 180 / Math.PI, RE = 6371;
const ll2v = (lat, lon, r = 1) => { const a = lat * D2R, o = lon * D2R, c = Math.cos(a); return [r * c * Math.cos(o), r * Math.sin(a), -r * c * Math.sin(o)]; };
const v2ll = (x, y, z) => { const r = Math.hypot(x, y, z) || 1; return { lat: Math.asin(y / r) * R2D, lon: Math.atan2(-z, x) * R2D }; };
const wrap = l => ((l + 540) % 360) - 180;
G.ll2v = ll2v; G.v2ll = v2ll;
function sunLL(date) {
  const d = date / 86400000 + 2440587.5 - 2451545.0, g = (357.529 + 0.98560028 * d) * D2R, q = 280.459 + 0.98564736 * d;
  const L = (q + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * D2R, e = (23.439 - 3.6e-7 * d) * D2R;
  const dec = Math.asin(Math.sin(e) * Math.sin(L)), ra = Math.atan2(Math.cos(e) * Math.sin(L), Math.cos(L)) * R2D;
  const gmst = ((18.697374558 + 24.06570982441908 * d) % 24 + 24) % 24 * 15; return { lat: dec * R2D, lon: wrap(ra - gmst) };
}
G.sunLL = sunLL;
function gcInterp(a, b, p) {
  const va = ll2v(a[0], a[1]), vb = ll2v(b[0], b[1]), dot = H.clamp(va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2], -1, 1), om = Math.acos(dot) || 1e-6, s = Math.sin(om);
  const k1 = Math.sin((1 - p) * om) / s, k2 = Math.sin(p * om) / s; return v2ll(k1 * va[0] + k2 * vb[0], k1 * va[1] + k2 * vb[1], k1 * va[2] + k2 * vb[2]);
}
const gcDist = (a, b) => { const va = ll2v(a[0], a[1]), vb = ll2v(b[0], b[1]); return Math.acos(H.clamp(va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2], -1, 1)) * RE * 1000; };
const bearing = (a, b) => { const y = Math.sin((b[1] - a[1]) * D2R) * Math.cos(b[0] * D2R), x = Math.cos(a[0] * D2R) * Math.sin(b[0] * D2R) - Math.sin(a[0] * D2R) * Math.cos(b[0] * D2R) * Math.cos((b[1] - a[1]) * D2R); return (Math.atan2(y, x) * R2D + 360) % 360; };
const dest = (lat, lon, brg, distM) => {
  const d = distM / (RE * 1000), t = brg * D2R, p1 = lat * D2R, l1 = lon * D2R, p2 = Math.asin(Math.sin(p1) * Math.cos(d) + Math.cos(p1) * Math.sin(d) * Math.cos(t));
  const l2 = l1 + Math.atan2(Math.sin(t) * Math.sin(d) * Math.cos(p1), Math.cos(d) - Math.sin(p1) * Math.sin(p2)); return [p2 * R2D, wrap(l2 * R2D)];
};

/* ---------------- layers ---------------- */
const LAYERS = {
  air:   { label: 'Aircraft',    col: '#46f0a0', shape: 1, size: 7,  items: [], src: 'OpenSky Network', mode: 'sim' },
  ship:  { label: 'Ships',       col: '#27c8ff', shape: 4, size: 8,  items: [], src: 'AIS (simulated lanes)', mode: 'sim' },
  sat:   { label: 'Satellites',  col: '#ffffff', shape: 2, size: 12, items: [], src: 'CelesTrak TLE · SGP4', mode: 'sim' },
  quake: { label: 'Earthquakes', col: '#ff8a2a', shape: 3, size: 20, items: [], src: 'USGS 2.5+ / 24h', mode: 'sim' },
  cam:   { label: 'Public cams', col: '#4aa3ff', shape: 0, size: 9,  items: [], src: 'curated list', mode: 'live' },
  alert: { label: 'Alerts',      col: '#ff3b4f', shape: 3, size: 26, items: [], src: 'watch-list + bridge', mode: 'live' }
};
G.LAYERS = LAYERS;
const DEFAULT_WATCH = ['Ukraine', 'Iran', 'Israel', 'Sudan', 'Yemen', 'Myanmar'];
H.config.watch = H.config.watch || DEFAULT_WATCH;
G.alertCountries = () => Array.from(new Set([...(H.config.watch || []), ...H.state.alerts.map(a => a.country).filter(Boolean)]));
const satPos = (it, date) => {   // -> {x,y,z (unit coords, compressed altitude), lat, lon, altKm, vKms}
  let ecf, alt, v = 7.6;
  if (it.rec && window.satellite) {
    const pv = satellite.propagate(it.rec, date); if (!pv.position) return null; const gm = satellite.gstime(date), e = satellite.eciToEcf(pv.position, gm);
    ecf = [e.x, e.y, e.z]; const r = Math.hypot(...ecf); alt = r - RE; const vv = pv.velocity; v = vv ? Math.hypot(vv.x, vv.y, vv.z) : 7.6; ecf = [ecf[0] / r, ecf[2] / r, -ecf[1] / r];
  } else {
    const t = date / 1000, a = RE + it.alt, w = Math.sqrt(398600.4418 / (a * a * a)), u = it.ph + w * t, ci = Math.cos(it.inc * D2R), si = Math.sin(it.inc * D2R);
    const xo = Math.cos(u), yo = Math.sin(u), cr = Math.cos(it.raan), sr = Math.sin(it.raan);
    let X = xo * cr - yo * ci * sr, Y = xo * sr + yo * ci * cr, Z = yo * si; const gm = (satellite && satellite.gstime ? satellite.gstime(new Date(date)) : 0);
    const cg = Math.cos(gm), sg = Math.sin(gm), ex = X * cg + Y * sg, ey = -X * sg + Y * cg; ecf = [ex, Z, -ey]; alt = it.alt; v = Math.sqrt(398600.4418 / a);
  }
  const ll = v2ll(ecf[0], ecf[1], ecf[2]), r = 1.012 + 0.34 * (1 - Math.exp(-alt / 8000));
  return { x: ecf[0] * r, y: ecf[1] * r, z: ecf[2] * r, lat: ll.lat, lon: ll.lon, altKm: alt, v };
};
function updateItems(key, date, dt) {
  const L = LAYERS[key], now = date / 1000;
  if (key === 'air') for (const it of L.items) {
    if (it.sim) {
      it.p += dt * it.spd / it.dist; if (it.p >= 1) { const nxt = H.pick(G.hubs); it.a = it.b; it.b = [nxt.lat, nxt.lon, nxt.name, nxt.country]; if (it.a[0] === it.b[0]) it.b = [G.hubs[0].lat, G.hubs[0].lon, G.hubs[0].name, G.hubs[0].country]; it.dist = gcDist(it.a, it.b); it.p = 0; }
      const ll = gcInterp(it.a, it.b, it.p); it.lat = ll.lat; it.lon = ll.lon; it.hdg = bearing([it.lat, it.lon], it.b);
    } else { const d = dest(it.lat0, it.lon0, it.hdg, it.vel * (now - it.t0)); it.lat = d[0]; it.lon = d[1]; }
  }
  else if (key === 'ship') for (const it of L.items) {
    it.p += dt * it.spd; const ln = it.lane, tot = ln.cum[ln.cum.length - 1]; if (it.p >= tot) it.p -= tot; let i = 1; while (i < ln.cum.length - 1 && ln.cum[i] < it.p) i++;
    const f = (it.p - ln.cum[i - 1]) / ((ln.cum[i] - ln.cum[i - 1]) || 1), A = ln.pts[i - 1], B = ln.pts[i]; it.lat = A[0] + (B[0] - A[0]) * f; it.lon = A[1] + (B[1] - A[1]) * f; it.hdg = bearing(A, B);
    if (it.rev) { it.hdg = (it.hdg + 180) % 360; }
  }
  else if (key === 'sat') for (const it of L.items) { const s = satPos(it, date); if (s) { it.x = s.x; it.y = s.y; it.z = s.z; it.lat = s.lat; it.lon = s.lon; it.altKm = s.altKm; it.v = s.v; } }
}
function itemV(key, it) {
  if (key === 'sat') return [it.x || 0, it.y || 0, it.z || 0];
  if (key === 'air') return ll2v(it.lat, it.lon, 1.004 + (it.alt || 10000) / RE * 6);
  if (key === 'ship') return ll2v(it.lat, it.lon, 1.0015);
  return ll2v(it.lat, it.lon, 1.002);
}

/* ---------------- sim generators ---------------- */
function simAir(n) {
  G.hubs = H.CITIES.filter(c => c.w >= 5); const out = [], codes = ['PIA', 'UAE', 'QTR', 'BAW', 'DLH', 'AFR', 'THY', 'SIA', 'CPA', 'ANA', 'AAL', 'DAL', 'UAL', 'RYR', 'ETD', 'SVA', 'QFA', 'KAL', 'CCA', 'AIC'];
  for (let i = 0; i < n; i++) {
    const a = H.pick(G.hubs); let b = H.pick(G.hubs); while (b === a) b = H.pick(G.hubs); const A = [a.lat, a.lon, a.name, a.country], B = [b.lat, b.lon, b.name, b.country], d = gcDist(A, B);
    out.push({ id: 'sim' + i, call: H.pick(codes) + (100 + Math.random() * 899 | 0), country: a.country, sim: true, a: A, b: B, dist: d, p: Math.random(), spd: H.rand(215, 255), alt: H.rand(9000, 12000), vr: 0, lat: 0, lon: 0, hdg: 0, from: a.name, to: b.name });
  } return out;
}
function simShips(n) {
  const lanes = H.LANES.map(pts => { const cum = [0]; for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], (pts[i][1] - pts[i - 1][1]) * Math.cos(pts[i][0] * D2R))); return { pts, cum }; });
  const kinds = ['Container ship', 'Bulk carrier', 'Oil tanker', 'LNG carrier', 'Car carrier', 'General cargo'], out = [];
  for (let i = 0; i < n; i++) { const ln = H.pick(lanes), tot = ln.cum[ln.cum.length - 1]; out.push({ id: 'sh' + i, name: 'SIM-' + H.pick(['ATLAS', 'ORION', 'DELTA', 'NOVA', 'AURORA', 'MERIDIAN', 'PACIFIC', 'GLOBAL']) + '-' + (100 + i), kind: H.pick(kinds), lane: ln, p: Math.random() * tot, spd: H.rand(.0012, .003) * 60, kn: (10 + Math.random() * 10).toFixed(1), rev: false, lat: 0, lon: 0, hdg: 0 }); }
  return out;
}
function simSats(n) {
  const out = [], names = ['ISS (SIM)', 'TIANGONG (SIM)', 'HUBBLE (SIM)'];
  for (let i = 0; i < n; i++) { const meo = i % 12 === 0, geo = i % 29 === 0, alt = geo ? 35786 : meo ? 20200 : H.rand(380, 820); out.push({ id: 's' + i, name: i < 3 ? names[i] : (geo ? 'SIM-GEO-' : meo ? 'SIM-MEO-' : 'SIM-LEO-') + (i + 10), alt, inc: geo ? 0.1 : i < 3 ? 51.6 : H.rand(0, 98), raan: Math.random() * 6.283, ph: Math.random() * 6.283, lat: 0, lon: 0 }); }
  return out;
}
function simQuakes() {
  const belts = [[35, 140, 12], [-5, 105, 10], [-20, -70, 8], [38, 22, 5], [34, 70, 5], [60, -150, 4], [-38, 176, 5], [15, -92, 5], [36, -118, 3]], out = [];
  belts.forEach(b => { for (let i = 0; i < b[2]; i++) out.push({ id: 'q' + out.length, mag: +(2.5 + Math.pow(Math.random(), 3) * 4).toFixed(1), place: 'SIM region', lat: b[0] + H.rand(-6, 6), lon: wrap(b[1] + H.rand(-8, 8)), depth: H.rand(5, 120), time: Date.now() - H.rand(0, 8.6e7), sim: true }); });
  return out;
}
function camItems() { return H.CAMS.map((c, i) => ({ id: 'c' + i, name: c.name, city: c.city, lat: c.lat, lon: c.lon })); }
function alertItems() {
  const out = []; (H.config.watch || []).forEach(n => { const c = G.byName[String(n).toLowerCase()]; if (c) out.push({ id: 'w-' + c.name, title: c.name, country: c.name, lat: c.lat, lon: c.lon, level: 'watch', desc: 'Watch-list region (demo list — edit in More → Watch-list, or push {type:"alert"} from the bridge).' }); });
  H.state.alerts.forEach(a => { if (a.lat != null) out.push({ id: a.id || H.uid('a'), title: a.title || 'Alert', country: a.country, lat: a.lat, lon: a.lon, level: a.level || 'warn', desc: a.desc || '' }); });
  return out;
}

/* ---------------- feeds (browser-side, each with timeout + sim fallback) ---------------- */
G.src = {}; const setSrc = (k, mode, note) => { G.src[k] = { mode, note: note || '', t: Date.now() }; LAYERS[k] && (LAYERS[k].mode = mode); G.renderLayers && G.renderLayers(); G.renderSat && G.renderSat(); };
async function jget(url, ms = 9000, text) {
  const ac = new AbortController(), t = setTimeout(() => ac.abort(), ms);
  try { const r = await fetch(url, { signal: ac.signal, cache: 'no-store' }); if (!r.ok) throw new Error(r.status); return text ? await r.text() : await r.json(); } finally { clearTimeout(t); }
}
G.fetchers = {
  async quake() {
    try {
      const j = await jget('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson');
      const items = j.features.map(f => ({ id: f.id, mag: f.properties.mag, place: f.properties.place, lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0], depth: f.geometry.coordinates[2], time: f.properties.time, url: f.properties.url }));
      G.layer('quake').setItems(items); setSrc('quake', 'live', items.length + ' events'); G.quakeHeadlines(items);
    } catch (e) { if (!LAYERS.quake.items.length) G.layer('quake').setItems(simQuakes()); setSrc('quake', 'sim', 'USGS unreachable'); }
  },
  async air() {
    try {
      const j = await jget('https://opensky-network.org/api/states/all', 15000); const t0 = (j.time || Date.now() / 1000), items = [];
      (j.states || []).forEach(s => { if (s[8] || s[5] == null || s[6] == null || s[9] == null) return; items.push({ id: s[0], call: (s[1] || '').trim() || s[0], country: s[2], lat: s[6], lon: s[5], lat0: s[6], lon0: s[5], t0: t0, alt: s[7] || s[13] || 10000, vel: s[9], hdg: s[10] || 0, vr: s[11] || 0 }); });
      if (items.length > 4500) { for (let i = items.length - 1; i > 0; i--) { const k = Math.random() * (i + 1) | 0;[items[i], items[k]] = [items[k], items[i]]; } items.length = 4500; }
      if (!items.length) throw new Error('empty'); G.layer('air').setItems(items); setSrc('air', 'live', items.length + ' tracked');
    } catch (e) { if (!LAYERS.air.items.length || LAYERS.air.mode !== 'live') G.layer('air').setItems(simAir(H.quality.level === 'low' ? 380 : 900)); setSrc('air', 'sim', 'OpenSky unreachable / rate-limited'); }
  },
  async sat() {
    try {
      if (!window.satellite) throw new Error('no satellite.js');
      const groups = ['stations', 'visual', 'gps-ops', 'weather'], items = [];
      const txts = await Promise.all(groups.map(g => jget('https://celestrak.org/NORAD/elements/gp.php?GROUP=' + g + '&FORMAT=tle', 12000, true).catch(() => '')));
      txts.forEach(tx => { const ln = tx.split(/\r?\n/).map(s => s.trimEnd()).filter(Boolean); for (let i = 0; i + 2 < ln.length; i += 3) { try { const rec = satellite.twoline2satrec(ln[i + 1], ln[i + 2]); items.push({ id: ln[i + 1].slice(2, 7), name: ln[i].trim(), rec, lat: 0, lon: 0 }); } catch (e) { /* skip bad TLE */ } } });
      if (!items.length) throw new Error('no TLE'); const seen = new Set(), uniq = items.filter(s => !seen.has(s.id) && seen.add(s.id)).slice(0, 420);
      G.layer('sat').setItems(uniq); setSrc('sat', 'live', uniq.length + ' objects');
    } catch (e) { if (!LAYERS.sat.items.length || LAYERS.sat.mode !== 'live') G.layer('sat').setItems(simSats(H.quality.level === 'low' ? 40 : 90)); setSrc('sat', 'sim', 'CelesTrak unreachable'); }
  },
  async news() {
    const src = H.$('#news-src');
    try {
      const j = await jget('https://api.gdeltproject.org/api/v2/doc/doc?query=sourcelang:english&mode=artlist&maxrecords=18&format=json&sort=datedesc&timespan=3h', 10000);
      const arts = (j.articles || []).filter(a => a.title).slice(0, 14); if (!arts.length) throw new Error('empty');
      G.newsItems = arts.map(a => ({ title: a.title, source: a.domain, url: a.url, ts: a.seendate, live: true })); src && (src.textContent = 'GDELT · LIVE');
    } catch (e) {
      G.newsItems = G.newsItems && G.newsItems.some(n => n.live) ? G.newsItems : [];
      src && (src.textContent = G.quakeNews && G.quakeNews.length ? 'USGS · LIVE' : 'DEMO FEED');
    }
    G.renderNews();
  }
};
G.quakeHeadlines = items => {
  G.quakeNews = items.filter(q => q.mag >= 4.8).sort((a, b) => b.time - a.time).slice(0, 6).map(q => ({ title: `M${q.mag.toFixed(1)} earthquake — ${q.place}`, source: 'USGS', url: q.url, lat: q.lat, lon: q.lon, ts: q.time, live: true, quake: true }));
  items.filter(q => q.mag >= 6 && Date.now() - q.time < 6 * 3.6e6).forEach(q => { if (!H.state.alerts.find(a => a.id === 'eq-' + q.id)) H.ingest({ type: 'alert', id: 'eq-' + q.id, title: `M${q.mag.toFixed(1)} ${q.place}`, lat: q.lat, lon: q.lon, level: 'crit', desc: 'USGS significant earthquake' }); });
  G.renderNews && G.renderNews();
};
const DEMO_NEWS = ['[DEMO] Headline feed not connected — pushing {type:"headline"} from the bridge or enabling GDELT replaces these.', '[DEMO] news-api-skills (currentslab) slot: wire it here via the HELIX bridge.', '[DEMO] Click any headline with a location to fly the globe there.', '[DEMO] Quake headlines below are real once USGS is reachable.'];
G.renderNews = function () {
  const ol = H.$('#headlines'); if (!ol) return; const bridge = H.state.headlines.map(h => Object.assign({ live: true }, h));
  let list = [...bridge, ...(G.quakeNews || []), ...(G.newsItems || [])]; if (!list.length) list = DEMO_NEWS.map(t => ({ title: t, source: 'demo', demo: true }));
  ol.innerHTML = ''; list.slice(0, 16).forEach(n => {
    const li = H.el('li', { class: n.demo ? 'demo' : '' }, H.el('div', null, n.title, H.el('small', null, (n.source || '') + (n.ts && typeof n.ts === 'number' ? ' · ' + H.hhmm(n.ts) : ''))));
    li.onclick = () => { if (n.lat != null) { G.focus(n.lat, n.lon, 1.7); G.select({ layer: 'quake', item: LAYERS.quake.items.find(q => Math.abs(q.lat - n.lat) < 1e-6 && Math.abs(q.lon - n.lon) < 1e-6) }); } else if (n.url) window.open(n.url, '_blank', 'noopener'); else H.ask && H.ask('Brief me on: ' + n.title); };
    ol.append(li);
  });
};
H.bus.on('headline', () => G.renderNews()); H.bus.on('alert', () => { G.refreshAlerts && G.refreshAlerts(); });

/* ---------------- 3D layer wrapper ---------------- */
const MV = 'attribute float aSize;attribute float aPh;uniform float uPR,uScale;varying float vPh;void main(){vec4 mv=modelViewMatrix*vec4(position,1.0);gl_Position=projectionMatrix*mv;gl_PointSize=aSize*uPR*uScale;vPh=aPh;}';
const MF = `uniform vec3 uColor;uniform float uShape,uTime,uOp;varying float vPh;
void main(){vec2 p=gl_PointCoord*2.0-1.0;p.y=-p.y;float a=0.0;
 if(uShape<0.5){a=smoothstep(1.0,0.45,length(p));}
 else if(uShape<1.5){float d=abs(p.x)+abs(p.y);a=smoothstep(1.0,0.72,d);}
 else if(uShape<2.5){float d=min(min(abs(p.x),abs(p.y)),min(abs(p.x+p.y),abs(p.x-p.y))*0.7071);a=smoothstep(0.24,0.06,d)*smoothstep(1.0,0.8,length(p));a=max(a,smoothstep(0.3,0.1,length(p)));}
 else if(uShape<3.5){float r=fract(uTime*0.45+vPh);float d=abs(length(p)-r);a=smoothstep(0.2,0.0,d)*(1.0-r)+smoothstep(0.26,0.1,length(p))*0.75;}
 else if(uShape<4.5){float d=max(abs(p.x)*0.9+p.y*0.5,-p.y)-0.5;a=smoothstep(0.12,-0.1,d);}
 else {float d=abs(length(p)-0.82);a=smoothstep(0.2,0.04,d);}
 if(a<0.02)discard;gl_FragColor=vec4(uColor*(0.8+0.5*a),a*uOp);}`;
class Layer {
  constructor(key, scene) {
    this.key = key; this.def = LAYERS[key]; this.cap = 0; this.on = H.config.layers[key] !== false;
    this.u = { uColor: { value: new THREE.Color(this.def.col) }, uShape: { value: this.def.shape }, uTime: { value: 0 }, uOp: { value: 1 }, uPR: { value: 1 }, uScale: { value: 1 } };
    this.mat = new THREE.ShaderMaterial({ uniforms: this.u, vertexShader: MV, fragmentShader: MF, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
    this.scene = scene; this.build(64);
  }
  build(cap) {
    if (this.pts) { this.scene.remove(this.pts); this.pts.geometry.dispose(); }
    this.cap = cap; const g = new THREE.BufferGeometry(); this.pos = new Float32Array(cap * 3); this.size = new Float32Array(cap); this.ph = new Float32Array(cap);
    g.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage)); g.setAttribute('aSize', new THREE.BufferAttribute(this.size, 1)); g.setAttribute('aPh', new THREE.BufferAttribute(this.ph, 1)); g.setDrawRange(0, 0);
    this.pts = new THREE.Points(g, this.mat); this.pts.frustumCulled = false; this.pts.renderOrder = 3; this.scene.add(this.pts); this.pts.visible = this.on;
  }
  setItems(items) {
    const L = this.def; L.items = items; if (items.length > this.cap) this.build(Math.ceil(items.length * 1.2));
    items.forEach((it, i) => { this.ph[i] = Math.random(); this.size[i] = this.key === 'quake' ? L.size * (.55 + Math.max(0, it.mag - 2) / 3.2) : this.key === 'alert' ? L.size : L.size * (.85 + (i % 5) * .06); });
    this.pts.geometry.attributes.aSize.needsUpdate = true; this.pts.geometry.attributes.aPh.needsUpdate = true; this.refresh(true);
  }
  refresh() {
    const L = this.def.items, n = L.length; for (let i = 0; i < n; i++) { const v = itemV(this.key, L[i]); this.pos[i * 3] = v[0]; this.pos[i * 3 + 1] = v[1]; this.pos[i * 3 + 2] = v[2]; L[i]._v = v; }
    this.pts.geometry.attributes.position.needsUpdate = true; this.pts.geometry.setDrawRange(0, n);
  }
  setOn(v) { this.on = v; this.pts.visible = v; }
}
G._layers = {}; G.layer = k => G._layers[k];
G.activeKeys = () => Object.keys(LAYERS).filter(k => G._layers[k] && G._layers[k].on);

/* ---------------- 3D view ---------------- */
class View3D {
  constructor(canvas) {
    this.canvas = canvas; this.r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'low-power' }); this.r.setClearColor(0x010409, 1);
    this.scene = new THREE.Scene(); this.cam = new THREE.PerspectiveCamera(32, 1, 0.05, 200);
    this.view = { lat: 27, lon: 62, zoom: 1 }; this.tgt = { lat: 27, lon: 62, zoom: 1 }; this.vel = { lat: 0, lon: 0 }; this.idle = 0; this.drag = null; this.follow = null; this.hover = null; this.mouse = null; this.pickT = 0;
    this.build(); this.resize(); new ResizeObserver(() => this.resize()).observe(canvas.parentElement); this.bind();
  }
  build() {
    const tex = (c, rep) => { const t = new THREE.CanvasTexture(c); t.anisotropy = Math.min(8, this.r.capabilities.getMaxAnisotropy()); if (rep) t.wrapS = THREE.RepeatWrapping; t.needsUpdate = true; return t; };
    G.earthTex = { day: tex(G.dayCanvas), night: tex(G.nightCanvas), cloud: tex(G.cloudCanvas, true), ov: tex(G.ovCanvas) };
    const sun = sunLL(Date.now()), sv = ll2v(sun.lat, sun.lon);
    this.eu = { tDay: { value: G.earthTex.day }, tNight: { value: G.earthTex.night }, tCloud: { value: G.earthTex.cloud }, tOv: { value: G.earthTex.ov }, uSun: { value: new THREE.Vector3(...sv) }, uTime: { value: 0 }, uCloud: { value: H.quality.clouds ? 1 : 0 }, uCam: { value: new THREE.Vector3() }, uAcc: { value: new THREE.Color('#2ee6ff') } };
    const mat = new THREE.ShaderMaterial({
      uniforms: this.eu, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
      vertexShader: 'varying vec2 vUv;varying vec3 vN;varying vec3 vP;void main(){vUv=uv;vN=normalize(position);vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
      fragmentShader: `uniform sampler2D tDay,tNight,tCloud,tOv;uniform vec3 uSun,uCam,uAcc;uniform float uTime,uCloud;varying vec2 vUv;varying vec3 vN;varying vec3 vP;
void main(){
  vec3 n=normalize(vN);float ndl=dot(n,normalize(uSun));
  float dm=smoothstep(-0.14,0.2,ndl);
  vec3 day=texture2D(tDay,vUv).rgb;vec3 night=texture2D(tNight,vUv).rgb;
  vec3 dl=day*(0.30+0.95*max(ndl,0.0));
  vec3 col=mix(night*1.25,dl,dm);
  float cl=texture2D(tCloud,vUv+vec2(uTime*0.0006,0.0)).a*uCloud;
  col=mix(col,vec3(0.78,0.88,0.98)*(0.10+0.75*dm),cl*0.34);
  float tw=smoothstep(0.0,0.12,ndl+0.1)*smoothstep(0.38,0.0,ndl);col+=vec3(0.95,0.42,0.12)*tw*0.07;
  vec4 ov=texture2D(tOv,vUv);float pl=0.72+0.28*sin(uTime*2.6);col=mix(col,ov.rgb,min(1.0,ov.a*pl*1.15));
  vec3 vd=normalize(uCam-vP);float fr=pow(1.0-max(dot(n,vd),0.0),2.6);col+=uAcc*fr*0.55;
  gl_FragColor=vec4(col,1.0);}`
    });
    this.earth = new THREE.Mesh(new THREE.SphereGeometry(1, 128, 96), mat); this.scene.add(this.earth);
    const atm = new THREE.Mesh(new THREE.SphereGeometry(1.07, 64, 48), new THREE.ShaderMaterial({
      uniforms: { uAcc: this.eu.uAcc, uCam: this.eu.uCam }, transparent: true, side: THREE.BackSide, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: 'varying vec3 vN;varying vec3 vP;void main(){vN=normalize(position);vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
      fragmentShader: 'uniform vec3 uAcc,uCam;varying vec3 vN;varying vec3 vP;void main(){vec3 vd=normalize(uCam-vP);float i=pow(max(0.0,0.62-dot(-vN,vd)*0.0-abs(dot(vN,vd))*0.62),2.4)*2.2;gl_FragColor=vec4(uAcc*i,i);}'
    })); this.scene.add(atm);
    const sp = []; for (let i = 0; i < 1400; i++) { const u = Math.random() * 2 - 1, t = Math.random() * 6.283, s = Math.sqrt(1 - u * u), r = 60 + Math.random() * 20; sp.push(Math.cos(t) * s * r, u * r, Math.sin(t) * s * r); }
    const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.Float32BufferAttribute(sp, 3)); this.stars = new THREE.Points(sg, new THREE.PointsMaterial({ color: 0x9fd8ff, size: 0.18, sizeAttenuation: true, transparent: true, opacity: .55, depthWrite: false })); this.scene.add(this.stars);
    Object.keys(LAYERS).forEach(k => { G._layers[k] = new Layer(k, this.scene); });
    // selection ring + trail
    this.selU = { uColor: { value: new THREE.Color('#ffffff') }, uShape: { value: 5 }, uTime: { value: 0 }, uOp: { value: 1 }, uPR: { value: 1 }, uScale: { value: 1 } };
    const sg2 = new THREE.BufferGeometry(); sg2.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3)); sg2.setAttribute('aSize', new THREE.Float32BufferAttribute([30], 1)); sg2.setAttribute('aPh', new THREE.Float32BufferAttribute([0], 1));
    this.selPts = new THREE.Points(sg2, new THREE.ShaderMaterial({ uniforms: this.selU, vertexShader: MV, fragmentShader: MF, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })); this.selPts.visible = false; this.selPts.frustumCulled = false; this.selPts.renderOrder = 5; this.scene.add(this.selPts);
    this.trail = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: .8 })); this.trail.frustumCulled = false; this.scene.add(this.trail); this.trail.visible = false;
    H.bus.on('accent', a => this.eu.uAcc.value.set(a.hex).multiplyScalar(.35));
    this.eu.uAcc.value.set('#2ee6ff').multiplyScalar(.35);
  }
  fitDist() { const asp = this.w / this.h, fv = this.cam.fov * D2R / 2, ef = Math.min(fv, Math.atan(Math.tan(fv) * asp)); return 1 / Math.sin(ef * 0.9); }
  resize() {
    const p = this.canvas.parentElement, w = p.clientWidth, h = p.clientHeight; if (!w || !h) return; this.w = w; this.h = h;
    this.r.setPixelRatio(H.quality.dpr); this.r.setSize(w, h, false); this.cam.aspect = w / h; this.cam.updateProjectionMatrix();
    const sc = Math.max(.9, h / 300); Object.values(G._layers).forEach(l => { l.u.uPR.value = H.quality.dpr; l.u.uScale.value = sc; }); this.selU.uPR.value = H.quality.dpr; this.selU.uScale.value = sc;
  }
  setView(lat, lon, zoom) { this.tgt.lat = H.clamp(lat, -84, 84); this.tgt.lon = wrap(lon); if (zoom) this.tgt.zoom = H.clamp(zoom, .75, 7); }
  camPos() { const d = Math.max(1.12, 1 + (this.fitDist() - 1) / this.view.zoom), v = ll2v(this.view.lat, this.view.lon, d); return { d, v }; }
  bind() {
    const c = this.canvas; let moved = 0;
    const rect = e => { const r = c.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    c.addEventListener('pointerdown', e => { c.setPointerCapture(e.pointerId); this.drag = { x: e.clientX, y: e.clientY }; moved = 0; this.follow = null; this.vel.lat = this.vel.lon = 0; });
    c.addEventListener('pointermove', e => {
      this.mouse = rect(e); this.mouseEv = e;
      if (this.drag) {
        const dx = e.clientX - this.drag.x, dy = e.clientY - this.drag.y; moved += Math.abs(dx) + Math.abs(dy); this.drag = { x: e.clientX, y: e.clientY };
        const { d } = this.camPos(), k = 2 * Math.tan(this.cam.fov * D2R / 2) * (d - 1) / this.h * R2D; const dlon = -dx * k / Math.max(.25, Math.cos(this.view.lat * D2R)), dlat = dy * k;
        this.view.lon = wrap(this.view.lon + dlon); this.view.lat = H.clamp(this.view.lat + dlat, -84, 84); this.tgt.lat = this.view.lat; this.tgt.lon = this.view.lon; this.vel.lon = dlon; this.vel.lat = dlat; this.idle = 0;
        G.hideTip();
      }
    });
    c.addEventListener('pointerup', e => { this.drag = null; if (moved < 5) this.click(rect(e)); });
    c.addEventListener('pointerleave', () => { this.mouse = null; G.hideTip(); });
    c.addEventListener('wheel', e => { e.preventDefault(); this.tgt.zoom = H.clamp(this.tgt.zoom * Math.exp(-e.deltaY * 0.0014), .75, 7); this.idle = 0; }, { passive: false });
    c.addEventListener('dblclick', e => { const h = this.groundPick(rect(e)); if (h) { this.setView(h.lat, h.lon, Math.min(7, this.tgt.zoom * 1.8)); } });
  }
  groundPick(m) {
    const ray = new THREE.Raycaster(); ray.setFromCamera(new THREE.Vector2(m[0] / this.w * 2 - 1, -(m[1] / this.h * 2 - 1)), this.cam);
    const h = ray.intersectObject(this.earth)[0]; return h ? v2ll(h.point.x, h.point.y, h.point.z) : null;
  }
  project(v) { const p = new THREE.Vector3(v[0], v[1], v[2]).project(this.cam); return [(p.x * .5 + .5) * this.w, (-p.y * .5 + .5) * this.h, p.z]; }
  occluded(v, cp) { const dx = v[0] - cp[0], dy = v[1] - cp[1], dz = v[2] - cp[2], a = dx * dx + dy * dy + dz * dz, b = cp[0] * dx + cp[1] * dy + cp[2] * dz, cc = cp[0] ** 2 + cp[1] ** 2 + cp[2] ** 2 - 1, disc = b * b - a * cc; if (disc <= 0) return false; const t = (-b - Math.sqrt(disc)) / a; return t > 0 && t < 0.999; }
  pick(m) {
    const cp = this.camPos().v; let best = null, bd = 12 * 12;
    for (const k of G.activeKeys()) {
      const L = LAYERS[k].items; for (let i = 0; i < L.length; i++) {
        const v = L[i]._v; if (!v) continue; if (v[0] * cp[0] + v[1] * cp[1] + v[2] * cp[2] < 0.55 && this.occluded(v, cp)) continue;
        const s = this.project(v), dx = s[0] - m[0], dy = s[1] - m[1], d = dx * dx + dy * dy; if (d < bd) { bd = d; best = { layer: k, item: L[i], sx: s[0], sy: s[1] }; }
      }
    } return best;
  }
  click(m) {
    const p = this.pick(m); if (p) { G.select(p); return; }
    const g = this.groundPick(m); if (g) { const c = G.countryAt(g.lat, g.lon); G.selectedCountry = c ? c.name : null; G.redrawOverlay(); G.select(c ? { layer: 'country', item: { name: c.name, lat: g.lat, lon: g.lon, c } } : null); } else G.select(null);
  }
  frame(dt, t) {
    const v = this.view, tg = this.tgt;
    if (this.follow && this.follow.item && this.follow.item.lat != null) { tg.lat = this.follow.item.lat; tg.lon = this.follow.item.lon; }
    if (!this.drag) {
      if (Math.abs(this.vel.lon) + Math.abs(this.vel.lat) > .01 && !this.follow) { tg.lon = wrap(tg.lon + this.vel.lon); tg.lat = H.clamp(tg.lat + this.vel.lat, -84, 84); this.vel.lon *= .93; this.vel.lat *= .93; }
      this.idle += dt; if (H.config.autoRotate && this.idle > 4 && !this.follow && !G.sel) tg.lon = wrap(tg.lon + dt * 3.2);
      const k = 1 - Math.exp(-dt * 5); let dl = wrap(tg.lon - v.lon); v.lon = wrap(v.lon + dl * k); v.lat += (tg.lat - v.lat) * k;
    }
    v.zoom += (tg.zoom - v.zoom) * (1 - Math.exp(-dt * 6));
    const cp = this.camPos(); this.cam.position.set(cp.v[0], cp.v[1], cp.v[2]); this.cam.up.set(0, 1, 0); this.cam.lookAt(0, 0, 0); this.cam.near = Math.max(.02, cp.d - 1.5); this.cam.far = 200; this.cam.updateProjectionMatrix();
    this.eu.uCam.value.copy(this.cam.position); this.eu.uTime.value = t; this.eu.uCloud.value = H.quality.clouds ? 1 : 0;
    this.stars.rotation.y = t * 0.004;
    if (!this._sunT || t - this._sunT > 20) { this._sunT = t; const s = sunLL(Date.now()); this.eu.uSun.value.set(...ll2v(s.lat, s.lon)); }
    Object.values(G._layers).forEach(l => { l.u.uTime.value = t; }); this.selU.uTime.value = t;
    // selection ring + hover
    if (G.sel && G.sel.item && G.sel.layer !== 'country' && G.sel.item._v) { this.selPts.visible = true; const a = this.selPts.geometry.attributes.position; a.array.set(G.sel.item._v); a.needsUpdate = true; } else this.selPts.visible = false;
    if (this.mouse && !this.drag && t - this.pickT > .06) { this.pickT = t; const p = this.pick(this.mouse); if (p) G.showTip(p, this.mouse[0], this.mouse[1], this.canvas); else { const g = this.groundPick(this.mouse); const c = g && G.countryAt(g.lat, g.lon); if (c) G.showTip({ layer: 'country', item: { name: c.name } }, this.mouse[0], this.mouse[1], this.canvas); else G.hideTip(); } this.canvas.style.cursor = p ? 'pointer' : ''; }
    this.r.render(this.scene, this.cam);
  }
}

/* ---------------- 2D map ---------------- */
class Map2D {
  constructor(canvas) { this.c = canvas; this.x = canvas.getContext('2d'); this.v = { lon: 62, lat: 28, zoom: 1.0 }; this.dirty = true; this.drag = null; this.mouse = null; this.resize(); new ResizeObserver(() => this.resize()).observe(canvas.parentElement); this.bind(); }
  resize() { const p = this.c.parentElement, w = p.clientWidth, h = p.clientHeight, dpr = Math.min(2, H.quality.dpr || 1); if (!w || !h) return; this.c.width = w * dpr; this.c.height = h * dpr; this.w = w; this.h = h; this.dpr = dpr; this.dirty = true; }
  s() { return this.w / 360 * this.v.zoom * 1.0; }
  proj(lat, lon) { const s = this.s(); let dx = lon - this.v.lon; dx = ((dx + 540) % 360) - 180; return [this.w / 2 + dx * s, this.h / 2 + (this.v.lat - lat) * s]; }
  unproj(px, py) { const s = this.s(); return { lat: H.clamp(this.v.lat - (py - this.h / 2) / s, -90, 90), lon: wrap(this.v.lon + (px - this.w / 2) / s) }; }
  bind() {
    const c = this.c; let moved = 0; const rect = e => { const r = c.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    c.addEventListener('pointerdown', e => { c.setPointerCapture(e.pointerId); this.drag = [e.clientX, e.clientY]; moved = 0; });
    c.addEventListener('pointermove', e => { this.mouse = rect(e); if (this.drag) { const s = this.s(); moved += Math.abs(e.clientX - this.drag[0]) + Math.abs(e.clientY - this.drag[1]); this.v.lon = wrap(this.v.lon - (e.clientX - this.drag[0]) / s); this.v.lat = H.clamp(this.v.lat + (e.clientY - this.drag[1]) / s, -80, 80); this.drag = [e.clientX, e.clientY]; this.dirty = true; G.hideTip(); } else this.hoverT = 1; });
    c.addEventListener('pointerup', e => { this.drag = null; if (moved < 5) { const m = rect(e), p = this.pick(m); if (p) G.select(p); else { const g = this.unproj(m[0], m[1]), co = G.countryAt(g.lat, g.lon); G.selectedCountry = co ? co.name : null; G.redrawOverlay(); G.select(co ? { layer: 'country', item: { name: co.name, lat: g.lat, lon: g.lon, c: co } } : null); } } });
    c.addEventListener('pointerleave', () => { this.mouse = null; G.hideTip(); });
    c.addEventListener('wheel', e => { e.preventDefault(); const m = rect(e), b = this.unproj(m[0], m[1]); this.v.zoom = H.clamp(this.v.zoom * Math.exp(-e.deltaY * 0.0015), .9, 40); const a = this.unproj(m[0], m[1]); this.v.lon = wrap(this.v.lon + (b.lon - a.lon)); this.v.lat = H.clamp(this.v.lat + (b.lat - a.lat), -80, 80); this.dirty = true; }, { passive: false });
  }
  pick(m) {
    let best = null, bd = 10 * 10; for (const k of G.activeKeys()) for (const it of LAYERS[k].items) { if (it.lat == null) continue; const p = this.proj(it.lat, it.lon), dx = p[0] - m[0], dy = p[1] - m[1], d = dx * dx + dy * dy; if (d < bd) { bd = d; best = { layer: k, item: it, sx: p[0], sy: p[1] }; } } return best;
  }
  draw(t) {
    const x = this.x, W = this.w, Hh = this.h, s = this.s(); x.setTransform(this.dpr, 0, 0, this.dpr, 0, 0); x.fillStyle = '#020a14'; x.fillRect(0, 0, W, Hh);
    const day = G.dayCanvas; if (!day) return; x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
    const tw = 360 * s, th = 180 * s, y0 = Hh / 2 - (90 - this.v.lat) * s; let x0 = W / 2 - (this.v.lon + 180) * s; while (x0 > 0) x0 -= tw; for (let xx = x0; xx < W; xx += tw) x.drawImage(day, xx, y0, tw, th);
    // night side shading (terminator)
    const sun = sunLL(Date.now()); x.fillStyle = 'rgba(0,4,16,.52)'; x.beginPath(); const pts = []; for (let lo = -180; lo <= 180; lo += 3) { const H_ = (lo - sun.lon) * D2R, la = Math.atan(-Math.cos(H_) / Math.tan(sun.lat * D2R || 1e-6)) * R2D; pts.push([lo, la]); }
    for (let rep = -1; rep <= 1; rep++) { x.beginPath(); pts.forEach((p, i) => { const q = this.proj(p[1], p[0]); const X0 = q[0] + rep * tw; i ? x.lineTo(X0, q[1]) : x.moveTo(X0, q[1]); }); const edgeLat = sun.lat > 0 ? -90 : 90, a = this.proj(edgeLat, 180), b = this.proj(edgeLat, -180); x.lineTo(a[0] + rep * tw, a[1]); x.lineTo(b[0] + rep * tw - 0, b[1]); x.closePath(); x.fill(); }
    // overlay
    if (G.ovCanvas) { for (let xx = x0; xx < W; xx += tw) x.drawImage(G.ovCanvas, xx, y0, tw, th); }
    // graticule labels
    x.fillStyle = 'rgba(150,220,240,.35)'; x.font = '9px monospace'; for (let la = -60; la <= 60; la += 30) { const p = this.proj(la, this.v.lon - 180 + (W / 2) / s * 0); x.fillText(la + '°', 4, this.proj(la, 0)[1] - 2); }
    // markers
    for (const k of G.activeKeys()) {
      const L = LAYERS[k], items = L.items; x.fillStyle = L.col; x.strokeStyle = L.col; const z = Math.max(1, this.w / 300);
      for (let i = 0; i < items.length; i++) {
        const it = items[i]; if (it.lat == null) continue; const p = this.proj(it.lat, it.lon); if (p[0] < -10 || p[0] > W + 10 || p[1] < -10 || p[1] > Hh + 10) continue;
        if (k === 'air') { x.fillRect(p[0] - 1.5 * z, p[1] - 1.5 * z, 3 * z, 3 * z); }
        else if (k === 'ship') { x.beginPath(); x.moveTo(p[0], p[1] - 3 * z); x.lineTo(p[0] + 2.5 * z, p[1] + 2.5 * z); x.lineTo(p[0] - 2.5 * z, p[1] + 2.5 * z); x.fill(); }
        else if (k === 'sat') { x.beginPath(); x.moveTo(p[0] - 3 * z, p[1]); x.lineTo(p[0] + 3 * z, p[1]); x.moveTo(p[0], p[1] - 3 * z); x.lineTo(p[0], p[1] + 3 * z); x.stroke(); }
        else if (k === 'cam') { x.beginPath(); x.arc(p[0], p[1], 2.6 * z, 0, 6.283); x.fill(); }
        else { const r = ((t * .45 + (i * .37)) % 1); x.globalAlpha = 1 - r; x.beginPath(); x.arc(p[0], p[1], (k === 'quake' ? 3 + (it.mag || 3) * 2 : 12) * z * (.3 + r) * .6, 0, 6.283); x.stroke(); x.globalAlpha = 1; x.beginPath(); x.arc(p[0], p[1], 2.2 * z, 0, 6.283); x.fill(); }
      }
    }
    if (G.sel && G.sel.item && G.sel.item.lat != null && G.sel.layer !== 'country') { const p = this.proj(G.sel.item.lat, G.sel.item.lon); x.strokeStyle = '#fff'; x.lineWidth = 1.5; x.beginPath(); x.arc(p[0], p[1], 9 + Math.sin(t * 5) * 1.5, 0, 6.283); x.stroke(); x.lineWidth = 1; }
    // hover tooltip
    if (this.mouse && !this.drag) { const p = this.pick(this.mouse); if (p) G.showTip(p, this.mouse[0], this.mouse[1], this.c); else { const g = this.unproj(this.mouse[0], this.mouse[1]), co = G.countryAt(g.lat, g.lon); co ? G.showTip({ layer: 'country', item: { name: co.name } }, this.mouse[0], this.mouse[1], this.c) : G.hideTip(); } }
    this.dirty = false;
  }
}

/* ---------------- tooltip / info card / UI ---------------- */
const fmtLL = it => `${Math.abs(it.lat).toFixed(2)}°${it.lat >= 0 ? 'N' : 'S'} ${Math.abs(it.lon).toFixed(2)}°${it.lon >= 0 ? 'E' : 'W'}`;
const tipHTML = p => {
  const it = p.item, L = LAYERS[p.layer], sim = L && L.mode === 'sim' ? ' <b>(SIM)</b>' : '';
  switch (p.layer) {
    case 'air': return `<b>${H.esc(it.call)}</b>${sim}<br>${H.esc(it.country || '')} · ${Math.round((it.alt || 0) * 3.281 / 100) * 100} ft`;
    case 'ship': return `<b>${H.esc(it.name)}</b>${sim}<br>${it.kind} · ${it.kn} kn`;
    case 'sat': return `<b>${H.esc(it.name)}</b>${sim}<br>alt ${Math.round(it.altKm || 0)} km`;
    case 'quake': return `<b>M${(+it.mag).toFixed(1)}</b>${sim} ${H.esc(it.place || '')}<br>depth ${Math.round(it.depth || 0)} km`;
    case 'cam': return `<b>${H.esc(it.name)}</b><br>${H.esc(it.city)} · public cam`;
    case 'alert': return `<b>${H.esc(it.title)}</b><br>${H.esc(it.level)}`;
    case 'country': return `<b>${H.esc(it.name)}</b>`;
  } return '';
};
G.showTip = (p, x, y, cv) => { const t = H.$('#globe-tip'); t.innerHTML = tipHTML(p); t.hidden = false; const w = cv.parentElement.clientWidth; t.style.left = Math.min(w - 170, x + 12) + 'px'; t.style.top = Math.max(30, y - 8) + 'px'; };
G.hideTip = () => { H.$('#globe-tip').hidden = true; };
G.focus = (lat, lon, zoom) => { G.v3 && G.v3.setView(lat, lon, zoom || 2); if (G.m2) { G.m2.v.lat = lat; G.m2.v.lon = lon; if (zoom) G.m2.v.zoom = Math.max(G.m2.v.zoom, zoom * 1.5); G.m2.dirty = true; } };
G.select = p => {
  G.sel = p && p.item ? p : null; const box = H.$('#globe-info'); G.v3 && (G.v3.follow = null, G.v3.trail.visible = false); G.trailPts = [];
  if (!G.sel) { box.hidden = true; if (G.selectedCountry) { G.selectedCountry = null; G.redrawOverlay(); } return; }
  const it = G.sel.item, k = G.sel.layer, L = LAYERS[k], sim = L && L.mode === 'sim'; let rows = [], title = '', acts = [];
  const ask = txt => { H.ask && H.ask(txt); G.select(null); };
  if (k === 'air') { title = it.call; rows = [['Origin', it.country || '—'], ['Altitude', `${Math.round(it.alt)} m · ${Math.round(it.alt * 3.281)} ft`], ['Speed', `${Math.round((it.vel || it.spd) * 3.6)} km/h`], ['Heading', Math.round(it.hdg || 0) + '°'], ['Position', fmtLL(it)]]; if (it.from) rows.splice(1, 0, ['Route', `${it.from} → ${it.to}`]); acts = [['Track', () => { G.v3.follow = G.sel; G.v3.tgt.zoom = Math.max(G.v3.tgt.zoom, 2.2); }], ['Ask HELIX', () => ask(`Brief me on flight ${it.call} (${it.country}) near ${fmtLL(it)}`)]]; }
  else if (k === 'ship') { title = it.name; rows = [['Type', it.kind], ['Speed', it.kn + ' kn'], ['Heading', Math.round(it.hdg) + '°'], ['Position', fmtLL(it)]]; acts = [['Track', () => { G.v3.follow = G.sel; G.v3.tgt.zoom = Math.max(G.v3.tgt.zoom, 2.2); }]]; }
  else if (k === 'sat') { title = it.name; rows = [['Altitude', Math.round(it.altKm || 0) + ' km'], ['Velocity', (it.v || 0).toFixed(2) + ' km/s'], ['Sub-point', fmtLL(it)], ['Period', (2 * Math.PI * Math.sqrt(Math.pow(RE + (it.altKm || it.alt || 500), 3) / 398600.4418) / 60).toFixed(0) + ' min']]; acts = [['Track', () => { G.v3.follow = G.sel; }], ['Orbit', () => G.showOrbit(it)], ['Ask HELIX', () => ask(`When is the next visible pass of ${it.name} over my location?`)]]; }
  else if (k === 'quake') { title = 'M' + (+it.mag).toFixed(1) + ' earthquake'; rows = [['Place', it.place || '—'], ['Depth', Math.round(it.depth || 0) + ' km'], ['Time', new Date(it.time).toLocaleString()], ['Position', fmtLL(it)]]; acts = [['USGS', () => it.url && window.open(it.url, '_blank', 'noopener')], ['Ask HELIX', () => ask(`Research the M${(+it.mag).toFixed(1)} earthquake near ${it.place || fmtLL(it)} and summarise impact`)]]; }
  else if (k === 'cam') { title = it.name; rows = [['City', it.city], ['Position', fmtLL(it)], ['Source', 'web search (no hot-link)']]; acts = [['Find live view', () => window.open('https://www.youtube.com/results?search_query=' + encodeURIComponent(it.name + ' ' + it.city + ' live cam'), '_blank', 'noopener')]]; }
  else if (k === 'alert') { title = it.title; rows = [['Level', it.level], ['Region', it.country || '—'], ['Note', it.desc || '—']]; acts = [['Research', () => ask(`Research the current situation in ${it.country || it.title} and report with sources`)]]; }
  else if (k === 'country') { title = it.name; rows = [['Region', 'country']]; const near = H.CITIES.filter(c => c.country.toLowerCase() === it.name.toLowerCase()).map(c => c.name).slice(0, 5).join(', '); if (near) rows.push(['Cities', near]); acts = [['Fly to', () => G.focus(it.c.lat, it.c.lon, 2.4)], ['Watch', () => { const w = H.config.watch; if (!w.includes(it.name)) w.push(it.name); H.saveConfig(); G.refreshAlerts(); H.toast(it.name + ' added to watch-list'); }], ['Ask HELIX', () => ask(`Give me a briefing on ${it.name}: current headlines, risks, economy`)]]; }
  box.innerHTML = ''; box.append(H.el('h4', null, H.el('span', { style: 'color:' + (L ? L.col : '#2ee6ff') }, '◆'), title, sim ? H.el('span', { class: 'tag warn' }, 'SIM') : null, H.el('span', { class: 'x', onclick: () => G.select(null) }, '✕')),
    ...rows.map(r => H.el('div', { class: 'row' }, H.el('span', null, r[0]), H.el('b', null, r[1]))), H.el('div', { class: 'acts' }, ...acts.map(a => H.el('button', { class: 'btn sm', onclick: a[1] }, a[0])))); box.hidden = false;
  if (it.lat != null && k !== 'country') G.focus(it.lat, it.lon, Math.max(G.v3 ? G.v3.tgt.zoom : 1, k === 'sat' ? 1.1 : 1.8));
  G.m2 && (G.m2.dirty = true);
};
G.showOrbit = it => {
  const pts = [], now = Date.now(), per = 2 * Math.PI * Math.sqrt(Math.pow(RE + (it.altKm || it.alt || 500), 3) / 398600.4418) * 1000;
  for (let i = 0; i <= 120; i++) { const s = satPos(it, now + (i / 120 - .1) * per); if (s) pts.push(s.x, s.y, s.z); }
  const g = G.v3.trail.geometry; g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)); G.v3.trail.visible = true;
};
G.refreshAlerts = () => { const a = G.layer('alert'); a && a.setItems(alertItems()); G.redrawOverlay(); G.renderAlertsView && G.renderAlertsView(); const b = H.$('#alerts-badge'), n = alertItems().length; b.hidden = !n; b.textContent = n; };
G.renderLayers = () => {
  const box = H.$('#globe-layers'); if (!box) return; box.innerHTML = '';
  Object.keys(LAYERS).forEach(k => { const L = LAYERS[k], on = H.config.layers[k] !== false; const n = L.items.length;
    box.append(H.el('div', { class: 'lay' + (on ? ' on' : ''), title: `${L.label} — ${L.src} (${L.mode.toUpperCase()}) · ${n}`, onclick: () => { H.config.layers[k] = !on; H.saveConfig(); G._layers[k] && G._layers[k].setOn(!on); G.renderLayers(); G.m2 && (G.m2.dirty = true); } },
      H.el('i', { style: `background:${L.col};color:${L.col}` }), H.el('span', { class: 't' }, L.label + ' '), H.el('em', { class: L.mode === 'live' ? 'live' : '' }, n + ' · ' + L.mode.toUpperCase()))); });
};
G.renderSat = () => {
  const live = Object.values(LAYERS).filter(l => l.mode === 'live').length, el = H.$('#sat-status'); if (el) el.textContent = `${live}/${Object.keys(LAYERS).length} LIVE`;
  const b = H.$('#globe-badge'); if (b) { b.textContent = live >= 3 ? 'LIVE' : live ? 'PARTIAL' : 'SIM'; b.style.background = live >= 3 ? 'var(--accent)' : live ? 'var(--warn)' : '#8aa'; }
};
G.renderAlertsView = () => {
  const box = H.$('#sat-alert-list'); if (!box) return; box.innerHTML = ''; const list = alertItems(); const q = LAYERS.quake.items.filter(x => x.mag >= 5).sort((a, b) => b.mag - a.mag).slice(0, 8);
  box.append(H.el('h5', { style: 'color:var(--dim);font-size:10px;letter-spacing:.18em;margin-bottom:6px' }, 'ACTIVE ALERTS / WATCH-LIST'));
  list.forEach(a => box.append(H.el('div', { class: 'res', onclick: () => { G.focus(a.lat, a.lon, 2.2); G.select({ layer: 'alert', item: Object.assign({}, a) }); H.$('[data-v=today]').click(); } }, H.el('span', { class: 'ico', style: 'color:var(--err)' }, '▲'), a.title, H.el('small', null, a.level))));
  if (q.length) { box.append(H.el('h5', { style: 'color:var(--dim);font-size:10px;letter-spacing:.18em;margin:12px 0 6px' }, 'SIGNIFICANT QUAKES (M5+)')); q.forEach(a => box.append(H.el('div', { class: 'res', onclick: () => { G.focus(a.lat, a.lon, 2.2); G.select({ layer: 'quake', item: a }); H.$('[data-v=today]').click(); } }, H.el('span', { class: 'ico', style: 'color:var(--warn)' }, '◉'), 'M' + (+a.mag).toFixed(1) + ' ' + (a.place || ''), H.el('small', null, H.hhmm(a.time))))); }
};
G.search = q => {
  q = q.trim().toLowerCase(); if (!q) return []; const out = [];
  H.CITIES.forEach(c => { if (c.name.toLowerCase().includes(q)) out.push({ ico: '●', label: c.name, sub: c.country, lat: c.lat, lon: c.lon, z: 3 }); });
  G.countries.forEach(c => { if (c.name.toLowerCase().includes(q)) out.push({ ico: '▭', label: c.name, sub: 'country', lat: c.lat, lon: c.lon, z: 2, sel: { layer: 'country', item: { name: c.name, lat: c.lat, lon: c.lon, c } } }); });
  LAYERS.air.items.forEach(a => { if (out.length < 40 && a.call && a.call.toLowerCase().startsWith(q)) out.push({ ico: '◆', label: a.call, sub: 'aircraft', lat: a.lat, lon: a.lon, z: 2.4, sel: { layer: 'air', item: a } }); });
  LAYERS.sat.items.forEach(a => { if (out.length < 40 && a.name.toLowerCase().includes(q)) out.push({ ico: '✱', label: a.name, sub: 'satellite', lat: a.lat, lon: a.lon, z: 1.2, sel: { layer: 'sat', item: a } }); });
  LAYERS.quake.items.forEach(a => { if (out.length < 40 && (a.place || '').toLowerCase().includes(q)) out.push({ ico: '◉', label: 'M' + (+a.mag).toFixed(1) + ' ' + a.place, sub: 'quake', lat: a.lat, lon: a.lon, z: 2.4, sel: { layer: 'quake', item: a } }); });
  LAYERS.cam.items.forEach(a => { if ((a.name + a.city).toLowerCase().includes(q)) out.push({ ico: '◌', label: a.name, sub: a.city, lat: a.lat, lon: a.lon, z: 3, sel: { layer: 'cam', item: a } }); });
  return out.slice(0, 40);
};

/* ---------------- init ---------------- */
G.init = async function (progress) {
  G.prepGeo(); await G.buildTextures(progress);
  G.v3 = new View3D(H.$('#globe-canvas')); G.m2 = new Map2D(H.$('#map2d')); G.map2d = G.m2;
  G.layer('cam').setItems(camItems()); G.layer('air').setItems(simAir(H.quality.level === 'low' ? 380 : 900)); G.layer('ship').setItems(simShips(H.quality.level === 'low' ? 90 : 220)); G.layer('sat').setItems(simSats(H.quality.level === 'low' ? 40 : 90)); G.layer('quake').setItems(simQuakes());
  G.refreshAlerts(); G.renderLayers(); G.renderSat(); G.renderNews(); G.renderAlertsView();
  // per-second simulation tick (positions)
  let acc = 1, last = Date.now(); H.loop.add((dt) => {
    acc += dt; if (acc < 1) return; const now = Date.now(), d = (now - last) / 1000; last = now; acc = 0;
    ['air', 'ship', 'sat'].forEach(k => { updateItems(k, now, d * (k === 'ship' && LAYERS.ship.mode !== 'live' ? 1 : 1)); G.layer(k).refresh(); });
    if (G.sel && G.sel.item && G.sel.item._v && G.v3.trail.visible === false && (G.sel.layer === 'air' || G.sel.layer === 'ship') && G.v3.follow) { G.trailPts.push(...G.sel.item._v); if (G.trailPts.length > 360) G.trailPts.splice(0, 3); G.v3.trail.geometry.setAttribute('position', new THREE.Float32BufferAttribute(G.trailPts.slice(), 3)); }
    const ck = H.$('#globe-clock'); if (ck) { const s = sunLL(now); ck.textContent = new Date(now).toISOString().slice(11, 19) + ' UTC · ☀ ' + s.lat.toFixed(0) + '°, ' + s.lon.toFixed(0) + '°'; }
  }, { fps: 10 });
  updateItems('air', Date.now(), 0); updateItems('ship', Date.now(), 0); updateItems('sat', Date.now(), 0); ['air', 'ship', 'sat'].forEach(k => G.layer(k).refresh());
  const vis3 = () => G.mode3d !== false && !G.hidden && (document.hasFocus() || true);
  H.loop.add((dt, t) => { if (G.v3) G.v3.frame(dt, t); }, { fps: 60, vis: () => G.mode === '3d' && !G.hidden });
  H.loop.add((dt, t) => { if (G.m2 && (G.m2.dirty || true)) G.m2.draw(t); }, { fps: 24, vis: () => G.mode === '2d' && !G.hidden });
  G.mode = '3d'; G.hidden = false; G.bindUI();
  // feeds (non-blocking)
  G.fetchers.quake(); G.fetchers.air(); G.fetchers.sat(); G.fetchers.news();
  setInterval(() => G.fetchers.quake(), 5 * 60e3); setInterval(() => G.fetchers.air(), 15 * 60e3); setInterval(() => G.fetchers.news(), 10 * 60e3); setInterval(() => G.fetchers.sat(), 6 * 3600e3);
  G.ready = true;
};

G.setMode = m => {
  G.mode = m; H.$('#globe-canvas').style.display = m === '3d' ? '' : 'none'; H.$('#map2d').classList.toggle('on', m === '2d'); H.$('#btn-2d').classList.toggle('on', m === '2d'); H.$('#btn-3d').classList.toggle('on', m === '3d');
  H.$('#gz-spin').style.display = m === '3d' ? '' : 'none'; if (m === '2d') { G.m2.resize(); G.m2.dirty = true; } else G.v3.resize();
};
G.bindUI = () => {
  const $ = H.$;
  $('#btn-3d').onclick = () => G.setMode('3d'); $('#btn-2d').onclick = () => G.setMode('2d');
  $('#gz-in').onclick = () => { if (G.mode === '3d') G.v3.tgt.zoom = H.clamp(G.v3.tgt.zoom * 1.4, .75, 7); else { G.m2.v.zoom = Math.min(40, G.m2.v.zoom * 1.5); G.m2.dirty = true; } };
  $('#gz-out').onclick = () => { if (G.mode === '3d') G.v3.tgt.zoom = H.clamp(G.v3.tgt.zoom / 1.4, .75, 7); else { G.m2.v.zoom = Math.max(.9, G.m2.v.zoom / 1.5); G.m2.dirty = true; } };
  $('#gz-home').onclick = () => { G.v3.setView(27, 62, 1); G.m2.v = { lon: 62, lat: 28, zoom: 1 }; G.select(null); G.v3.follow = null; };
  $('#gz-spin').onclick = e => { H.config.autoRotate = !H.config.autoRotate; H.saveConfig(); e.currentTarget.classList.toggle('on', H.config.autoRotate); }; $('#gz-spin').classList.toggle('on', H.config.autoRotate);
  $('#btn-hide-map').onclick = e => { const w = $('#globe-wrap'); w.classList.toggle('hidden'); G.hidden = w.classList.contains('hidden'); e.currentTarget.textContent = G.hidden ? '▸ Show Map' : '▾ Hide Map'; $('#globe-top').style.position = G.hidden ? 'static' : ''; if (G.hidden) { $('#sat-body').prepend($('#globe-top')); } else { w.prepend($('#globe-top')); G.v3.resize(); } };
  const expand = () => { const p = $('#sat-panel'); p.classList.toggle('expanded'); setTimeout(() => { G.v3.resize(); G.m2.resize(); }, 60); G.renderLayers(); };
  $('#btn-sat-expand').onclick = expand; $('#btn-sat-full').onclick = expand;
  $('#sat-panel').classList.add('compact-layers');
  // nav
  const views = { search: '#sv-search', alerts: '#sv-alerts', more: '#sv-more' };
  H.$$('#sat-nav button').forEach(b => b.onclick = () => {
    H.$$('#sat-nav button').forEach(x => x.classList.toggle('on', x === b)); const v = b.dataset.v; Object.values(views).forEach(s => $(s).hidden = true);
    if (views[v]) { $(views[v]).hidden = false; if (v === 'search') { $('#sat-q').focus(); G.doSearch(); } if (v === 'alerts') G.renderAlertsView(); if (v === 'more') G.renderMore(); }
    if (v === 'today') G.setMode('3d'); if (v === 'map') G.setMode('2d');
  });
  $('#sat-q').oninput = G.doSearch; $('#btn-news-refresh').onclick = () => { G.fetchers.news(); G.fetchers.quake(); H.toast('Refreshing feeds…'); };
  H.bus.on('alert', () => G.renderAlertsView());
};
G.doSearch = () => {
  const q = H.$('#sat-q').value, box = H.$('#sat-results'); box.innerHTML = ''; const res = G.search(q);
  if (!q.trim()) { box.append(H.el('div', { class: 'res', style: 'color:var(--dim)' }, 'Try: Karachi · Iran · PIA · ISS · M5 · Venice')); return; }
  if (!res.length) box.append(H.el('div', { class: 'res', style: 'color:var(--dim)' }, 'No match'));
  res.forEach(r => box.append(H.el('div', { class: 'res', onclick: () => { H.$('[data-v=today]').click(); G.focus(r.lat, r.lon, r.z); if (r.sel) G.select(r.sel); else G.select({ layer: 'country', item: { name: r.label, lat: r.lat, lon: r.lon, c: { lat: r.lat, lon: r.lon } } }); } }, H.el('span', { class: 'ico' }, r.ico), r.label, H.el('small', null, r.sub))));
};
G.renderMore = () => {
  const box = H.$('#sat-more-list'); box.innerHTML = '';
  const sec = t => box.append(H.el('h5', { style: 'color:var(--dim);font-size:10px;letter-spacing:.18em;margin:10px 0 6px' }, t)); sec('DATA SOURCES');
  Object.keys(LAYERS).forEach(k => { const L = LAYERS[k], s = G.src[k]; box.append(H.el('div', { class: 'row2' }, H.el('div', { class: 'grow' }, L.label, H.el('small', null, L.src + (s && s.note ? ' — ' + s.note : ''))), H.el('span', { class: 'tag ' + (L.mode === 'live' ? 'ok' : 'warn') }, L.mode.toUpperCase()))); });
  box.append(H.el('div', { style: 'margin:6px 0' }, H.el('button', { class: 'btn sm', onclick: () => { ['quake', 'air', 'sat', 'news'].forEach(k => G.fetchers[k]()); H.toast('Re-fetching all feeds'); } }, 'Retry live feeds')));
  sec('WATCH-LIST (countries shaded red)'); const inp = H.el('input', { type: 'text', value: (H.config.watch || []).join(', '), style: 'width:100%' });
  box.append(inp, H.el('div', { style: 'margin-top:6px;display:flex;gap:6px' }, H.el('button', { class: 'btn sm', onclick: () => { H.config.watch = inp.value.split(',').map(s => s.trim()).filter(Boolean); H.saveConfig(); G.refreshAlerts(); H.toast('Watch-list updated', 'ok'); } }, 'Apply'), H.el('button', { class: 'btn sm', onclick: () => { H.config.watch = DEFAULT_WATCH.slice(); H.saveConfig(); inp.value = DEFAULT_WATCH.join(', '); G.refreshAlerts(); } }, 'Reset')));
  sec('TOOLS');
  [['Open LMS operations', () => H.lms && H.lms.open()], ['Paste a link to download (yt-dlp)', () => H.openDownloader && H.openDownloader()], ['Expand world monitor', () => H.$('#btn-sat-expand').click()]].forEach(a => box.append(H.el('div', { class: 'res', onclick: a[1] }, H.el('span', { class: 'ico' }, '›'), a[0])));
};
})();
