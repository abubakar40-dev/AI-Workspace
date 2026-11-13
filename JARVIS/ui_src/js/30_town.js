/* =====================================================================================
   AGENT TOWN — procedural pixel-art office. Every sub-agent is an autonomous actor:
   • reacts to bridge events (agent.status / interact / task.upsert / confirm.request / kill)
   • walks via BFS path-finding, sits at its desk, types, visits colleagues to brief / hand-off / review
   • idles like a person (coffee, water cooler, chat, window, sofa) when its profile has no task
   • you control a visitor avatar (WASD/arrows, E to interact, click an agent for its card)
   ===================================================================================== */
(function () {
'use strict';
const H = window.H, T = 16, MW = 44, MH = 28, PW = MW * T, PH = MH * T;
const Town = H.town = { actors: {}, objs: [], sel: null };
const mkc = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
const spr = (w, h, fn) => { const c = mkc(w, h), x = c.getContext('2d'); fn(x, w, h); return c; };
const R = (x, c, a, b, w, h) => { x.fillStyle = c; x.fillRect(a, b, w, h); };
const hash = (a, b) => { let h = Math.imul(a * 7919 + b * 104729, 2654435761); return ((h ^ (h >>> 15)) >>> 0) / 4294967296; };

/* ---------- map ---------- */
const solid = Array.from({ length: MH }, () => new Uint8Array(MW)), floor = Array.from({ length: MH }, () => new Uint8Array(MW));
const block = (x, y, w = 1, h = 1) => { for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) if (solid[j] && i >= 0 && i < MW) solid[j][i] = 1; };
for (let x = 0; x < MW; x++) { solid[0][x] = solid[1][x] = solid[MH - 1][x] = 1; solid[13][x] = 1; }
for (let y = 0; y < MH; y++) { solid[y][0] = solid[y][MW - 1] = 1; solid[y][14] = solid[y][29] = 1; }
[[6, 8], [20, 22], [35, 37]].forEach(g => { for (let x = g[0]; x <= g[1]; x++) solid[13][x] = 0; });
[8, 9, 19, 20].forEach(y => { solid[y][14] = solid[y][29] = 0; });
const ROOMS = [[1, 2, 13, 12, 1], [15, 2, 28, 12, 2], [30, 2, 42, 12, 3], [1, 14, 13, 26, 4], [15, 14, 28, 26, 5], [30, 14, 42, 26, 6]];
ROOMS.forEach(r => { for (let y = r[1]; y <= r[3]; y++) for (let x = r[0]; x <= r[2]; x++) floor[y][x] = r[4]; });
for (const y of [8, 9, 19, 20]) { floor[y][14] = floor[y][29] = y < 13 ? 2 : 5; } for (let x = 6; x <= 8; x++) floor[13][x] = 1; for (let x = 20; x <= 22; x++) floor[13][x] = 2; for (let x = 35; x <= 37; x++) floor[13][x] = 3;

/* ---------- furniture (sprites + optional dynamic overlays) ---------- */
const objs = Town.objs;
function add(kind, x, y, w, h, o = {}) { const ob = Object.assign({ kind, x, y, w, h, sortY: (y + h) * T - 1 }, o); objs.push(ob); if (o.solid !== false) block(...(o.fp || [x, y, w, h])); return ob; }
const DESKS = {}; // agent id -> {x,y,seat,visit}
const deskX = { research: 2, files: 6, career: 10, dev: 16, vision: 20, lms: 24, pc: 31, sysmon: 35, comms: 39 };
Object.keys(deskX).forEach(id => { const dx = deskX[id]; DESKS[id] = { x: dx, y: 5, seat: { x: dx + 1, y: 7, dir: 'up' }, visit: { x: dx + 3 > 42 ? dx - 1 : dx + 3, y: 7, dir: dx + 3 > 42 ? 'right' : 'left' }, id }; });
DESKS.helix = { x: 5, y: 18, seat: { x: 6, y: 20, dir: 'up' }, visit: { x: 6, y: 17, dir: 'down' }, id: 'helix' };

function drawDesk(x, w, h, oy, wood) {
  const W = w * T, Hh = h * T; R(x, 'rgba(0,0,0,.28)', 1, oy + Hh - 2, W - 2, 4);
  R(x, wood[1], 0, oy + 15, W, Hh - 15); R(x, wood[2], 0, oy + Hh - 3, W, 3); for (let i = 1; i < w; i++) R(x, wood[2], i * T - 1, oy + 17, 1, Hh - 21);
  R(x, wood[0], 0, oy + 2, W, 14); R(x, wood[3], 0, oy + 2, W, 1); R(x, 'rgba(0,0,0,.18)', 0, oy + 15, W, 1);
}
const WOODS = { a: ['#7b5a3c', '#5a402b', '#3f2c1d', '#936d49'], b: ['#5b6678', '#3f4958', '#2b3340', '#74829a'], c: ['#2d3f52', '#1f2d3b', '#16212c', '#42586e'] };
const S = {};
S.desk = (w, wood) => spr(w * T, 2 * T + 16, (x) => { drawDesk(x, w, 2, 16, WOODS[wood]); R(x, '#b9c6cf', w * T / 2 - 6, 16 + 9, 12, 3); R(x, '#8794a0', w * T / 2 - 6, 16 + 11, 12, 1); R(x, '#e9eef2', w * T - 9, 16 + 5, 3, 4); R(x, '#d8d0b0', 4, 16 + 6, 6, 4); R(x, '#c4b88f', 4, 16 + 5, 6, 1); });
S.chair = spr(T, T, x => { R(x, 'rgba(0,0,0,.25)', 3, 12, 10, 3); R(x, '#2b394b', 3, 3, 10, 9); R(x, '#3a4d66', 3, 3, 10, 2); R(x, '#1c2735', 4, 12, 8, 2); R(x, '#46607f', 5, 6, 6, 4); });
S.plant = spr(T, 26, x => { R(x, 'rgba(0,0,0,.25)', 3, 22, 10, 3); R(x, '#7a4a2a', 4, 17, 8, 7); R(x, '#5a3720', 4, 21, 8, 3); [[8, 8, 6], [4, 11, 4], [12, 11, 4], [8, 4, 4], [6, 14, 4], [11, 14, 4]].forEach(l => { x.fillStyle = '#2f8f4e'; x.beginPath(); x.arc(l[0], l[1], l[2], 0, 6.28); x.fill(); x.fillStyle = '#46b86a'; x.beginPath(); x.arc(l[0] - 1, l[1] - 1, l[2] * .55, 0, 6.28); x.fill(); }); });
S.shelf = w => spr(w * T, 2 * T, (x, W) => { R(x, '#3b2a1c', 0, 0, W, 32); R(x, '#241910', 0, 0, W, 2); for (let r = 0; r < 3; r++) { const y = 3 + r * 9; R(x, '#2a1d13', 1, y + 7, W - 2, 2); for (let i = 2; i < W - 3;) { const bw = 2 + (hash(i, r + w) * 3 | 0), bh = 5 + (hash(r, i + w) * 3 | 0); x.fillStyle = ['#c0392b', '#2e86c1', '#27ae60', '#d4ac0d', '#8e44ad', '#16a085', '#d35400', '#ecf0f1'][(hash(i * 3, r) * 8) | 0]; x.fillRect(i, y + 7 - bh, bw, bh); i += bw + 1; } } });
S.rack = spr(2 * T, 2 * T, x => { R(x, 'rgba(0,0,0,.3)', 1, 29, 30, 3); R(x, '#12181f', 2, 1, 28, 30); R(x, '#222c37', 2, 1, 28, 2); for (let i = 0; i < 6; i++) { R(x, '#1b2530', 4, 5 + i * 4.5, 24, 3.4); R(x, '#2e3b49', 4, 5 + i * 4.5, 24, 1); } });
S.printer = spr(2 * T, T + 6, x => { R(x, 'rgba(0,0,0,.25)', 2, 19, 28, 3); R(x, '#9aa7b3', 2, 8, 28, 12); R(x, '#c5cfd8', 2, 8, 28, 3); R(x, '#2b3540', 6, 12, 20, 3); R(x, '#f4f4ee', 8, 3, 16, 6); R(x, '#3fe08a', 25, 16, 2, 2); });
S.coffee = spr(2 * T, 28, x => { R(x, '#2b2f38', 2, 2, 28, 24); R(x, '#444b58', 2, 2, 28, 3); R(x, '#14171d', 6, 8, 12, 12); R(x, '#8a5a34', 10, 17, 4, 3); R(x, '#e74c3c', 22, 8, 4, 4); R(x, '#3fe08a', 22, 15, 4, 2); R(x, '#fff', 11, 16, 3, 4); });
S.cooler = spr(T, 30, x => { R(x, 'rgba(0,0,0,.25)', 2, 26, 12, 3); R(x, '#8fb4d8', 3, 1, 10, 11); R(x, '#cfe6fa', 4, 2, 3, 8); R(x, '#d6dde4', 2, 12, 12, 15); R(x, '#aab6c0', 2, 12, 12, 2); R(x, '#2a7fd4', 6, 16, 4, 2); });
S.vend = spr(2 * T, 2 * T, x => { R(x, '#6c2330', 1, 1, 30, 31); R(x, '#8e2f40', 1, 1, 30, 3); R(x, '#10161d', 4, 6, 20, 20); for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) R(x, ['#ffcc00', '#2ecc71', '#e67e22', '#3498db'][(r + c) % 4], 5 + c * 5, 7 + r * 5, 3, 3); R(x, '#23303c', 25, 8, 4, 10); R(x, '#111', 5, 27, 18, 3); });
S.couch = spr(6 * T, 2 * T, x => { R(x, 'rgba(0,0,0,.25)', 2, 28, 92, 4); R(x, '#5a2f4a', 0, 8, 96, 22); R(x, '#76405f', 2, 12, 92, 10); R(x, '#8a4e72', 2, 12, 92, 2); R(x, '#43223a', 0, 4, 96, 6); R(x, '#4b2740', 0, 6, 6, 24); R(x, '#4b2740', 90, 6, 6, 24); for (let i = 1; i < 3; i++) R(x, '#5a2f4a', 6 + i * 28, 13, 1, 9); });
S.round = spr(2 * T, 2 * T, x => { R(x, 'rgba(0,0,0,.25)', 3, 24, 26, 6); x.fillStyle = '#6d5036'; x.beginPath(); x.ellipse(16, 16, 14, 11, 0, 0, 6.28); x.fill(); x.fillStyle = '#8b6948'; x.beginPath(); x.ellipse(16, 14, 14, 10, 0, 0, 6.28); x.fill(); R(x, '#e9eef2', 12, 11, 3, 4); R(x, '#d9534f', 18, 13, 4, 3); });
S.cab = spr(T, 2 * T, x => { R(x, '#5f6b78', 1, 4, 14, 27); R(x, '#7d8a98', 1, 4, 14, 3); for (let i = 0; i < 3; i++) { R(x, '#46515d', 3, 9 + i * 7, 10, 5); R(x, '#cdd6de', 7, 11 + i * 7, 2, 1); } });
S.table = spr(6 * T, 2 * T, x => { R(x, 'rgba(0,0,0,.25)', 2, 28, 92, 4); R(x, '#4a5568', 0, 14, 96, 16); R(x, '#5f6d82', 0, 4, 96, 14); R(x, '#76869e', 0, 4, 96, 1); [[8, 8, 14, 7], [30, 7, 14, 8], [58, 8, 14, 7], [78, 7, 12, 8]].forEach(m => { R(x, '#10171f', m[0], m[1] + 2, m[2], m[3] - 2); R(x, '#243241', m[0] + 1, m[1] + 3, m[2] - 2, m[3] - 4); }); R(x, '#d9dee4', 44, 8, 10, 4); });

/* ---------- furniture placement ---------- */
Object.keys(DESKS).forEach(id => {
  const d = DESKS[id], wide = id === 'helix', w = wide ? 4 : 3, wood = id === 'helix' ? 'c' : (d.x < 14 ? 'a' : d.x < 29 ? 'b' : 'c');
  add('desk', d.x, d.y, w, 2, { agent: id, wood, mons: wide ? 3 : 1, spr: S.desk(w, wood), oy: 16, sortY: (d.y + 2) * T - 2 });
  add('chair', d.seat.x, d.seat.y, 1, 1, { solid: false, spr: S.chair, sortY: d.seat.y * T + 6 });
});
// room A (research / files / career)
add('shelf', 2, 2, 4, 2, { spr: S.shelf(4), wall: true, label: 'Memory vault', act: 'memory', front: [3, 4], sortY: 3 * T }); add('shelf', 7, 2, 4, 2, { spr: S.shelf(4), wall: true, sortY: 3 * T });
add('plant', 12, 2, 1, 1, { spr: S.plant, sortY: 3 * T }); add('plant', 1, 11, 1, 1, { spr: S.plant, fp: [1, 11, 1, 1] });
add('shelf', 2, 10, 4, 2, { spr: S.shelf(4), label: 'Library', front: [3, 12], fp: [2, 11, 4, 1], sortY: 12 * T - 4 }); add('shelf', 7, 10, 3, 2, { spr: S.shelf(3), fp: [7, 11, 3, 1], sortY: 12 * T - 4 });
add('printer', 11, 11, 2, 1, { spr: S.printer, label: 'Printer', front: [11, 12], sortY: 12 * T - 2 }); add('cab', 13, 10, 1, 2, { spr: S.cab, fp: [13, 11, 1, 1], sortY: 12 * T - 2 });
// room B (dev / vision / lms)
add('shelf', 16, 2, 4, 2, { spr: S.shelf(4), wall: true, sortY: 3 * T }); add('shelf', 22, 2, 4, 2, { spr: S.shelf(4), wall: true, sortY: 3 * T }); add('plant', 27, 2, 1, 1, { spr: S.plant, sortY: 3 * T });
add('table', 17, 10, 6, 2, { label: 'Lab bench', spr: S.table, front: [19, 12], fp: [17, 11, 6, 1], sortY: 12 * T - 3 }); add('plant', 27, 11, 1, 1, { spr: S.plant, fp: [27, 11, 1, 1] }); add('cab', 15, 10, 1, 2, { spr: S.cab, fp: [15, 11, 1, 1], sortY: 12 * T - 2 });
// room C (pc / sysmon / comms) + racks
add('rack', 39, 10, 2, 2, { label: 'Server racks', front: [40, 12], spr: S.rack, fp: [39, 11, 2, 1], dyn: 'rack', sortY: 12 * T - 2 }); add('rack', 41, 10, 2, 2, { spr: S.rack, fp: [41, 11, 2, 1], dyn: 'rack', front: [41, 12], sortY: 12 * T - 2 }); add('plant', 30, 2, 1, 1, { spr: S.plant, sortY: 3 * T });
add('shelf', 31, 2, 4, 2, { spr: S.shelf(4), wall: true, sortY: 3 * T }); add('shelf', 36, 2, 4, 2, { spr: S.shelf(4), wall: true, sortY: 3 * T }); add('plant', 31, 11, 1, 1, { spr: S.plant, fp: [31, 11, 1, 1] });
// CEO office
add('core', 11, 15, 2, 2, { label: 'HELIX core (toggle voice)', act: 'core', front: [11, 17], dyn: 'core', spr: S.round, sortY: 17 * T, fp: [11, 16, 2, 1] }); add('shelf', 2, 14, 4, 2, { spr: S.shelf(4), wall: true, fp: [2, 14, 4, 2], sortY: 16 * T }); add('plant', 1, 25, 1, 1, { spr: S.plant, fp: [1, 25, 1, 1] }); add('plant', 13, 25, 1, 1, { spr: S.plant, fp: [13, 25, 1, 1] }); add('cab', 2, 23, 1, 2, { spr: S.cab, fp: [2, 24, 1, 1], sortY: 25 * T - 2 });
// meeting room
add('board', 17, 13, 8, 2, { label: 'Kanban board', act: 'board', front: [20, 15], dyn: 'board', fp: [17, 14, 8, 1], sortY: 15 * T }); add('table', 20, 18, 6, 4, { dyn: 'holo', spr: null, fp: [20, 18, 6, 4], sortY: 21 * T });
MEET = [[20, 17, 'down'], [22, 17, 'down'], [24, 17, 'down'], [21, 22, 'up'], [23, 22, 'up'], [25, 22, 'up'], [19, 19, 'right'], [19, 20, 'right'], [26, 19, 'left'], [26, 20, 'left']];
var MEET; MEET.forEach(m => add('chair', m[0], m[1], 1, 1, { solid: false, spr: S.chair, sortY: m[1] * T + 6 })); add('plant', 15, 25, 1, 1, { spr: S.plant, fp: [15, 25, 1, 1] }); add('plant', 28, 25, 1, 1, { spr: S.plant, fp: [28, 25, 1, 1] });
// lounge
add('coffee', 31, 14, 2, 1, { label: 'Coffee machine', act: 'coffee', front: [31, 15], spr: S.coffee, sortY: 15 * T - 2 }); add('cooler', 34, 14, 1, 1, { label: 'Water cooler', act: 'water', front: [34, 15], spr: S.cooler, sortY: 15 * T - 2 }); add('vend', 36, 14, 2, 2, { label: 'Vending', front: [36, 16], spr: S.vend, fp: [36, 14, 2, 2], sortY: 16 * T });
add('couch', 33, 23, 6, 2, { label: 'Sofa', act: 'sit', front: [35, 22], spr: S.couch, fp: [33, 23, 6, 2], sortY: 24 * T + 2 }); add('round', 39, 18, 2, 2, { spr: S.round, fp: [39, 18, 2, 2], sortY: 20 * T }); add('chair', 38, 19, 1, 1, { solid: false, spr: S.chair, sortY: 19 * T + 6 }); add('chair', 41, 19, 1, 1, { solid: false, spr: S.chair, sortY: 19 * T + 6 }); add('plant', 30, 25, 1, 1, { spr: S.plant, fp: [30, 25, 1, 1] }); add('plant', 42, 25, 1, 1, { spr: S.plant, fp: [42, 25, 1, 1] }); add('plant', 42, 15, 1, 1, { spr: S.plant, fp: [42, 15, 1, 1] });

const SPOTS = {
  coffee: [[31, 15], [32, 15]], water: [[34, 15]], vend: [[36, 16], [37, 16]], rack: [[39, 12], [40, 12], [41, 12], [42, 12]], shelf: [[3, 12], [4, 12], [8, 12], [9, 12]], printer: [[11, 12], [12, 12]], lab: [[18, 12], [20, 12], [22, 12]], board: [[18, 15], [19, 15], [20, 15], [21, 15], [22, 15], [23, 15]], sofa: [[34, 23, 'up'], [36, 23, 'up'], [38, 23, 'up']], window: [[4, 4], [20, 4], [35, 4], [8, 16], [36, 16]], break: [[38, 19, 'right'], [41, 19, 'left']], plant: [[12, 12], [28, 12], [43 - 2, 12]]
};

/* ---------- static background ---------- */
let BG = null;
function buildBG() {
  BG = mkc(PW, PH); const x = BG.getContext('2d');
  R(x, '#070d14', 0, 0, PW, PH);
  const pal = { 1: ['#14283d', '#183049'], 2: ['#5b4630', '#665037'], 3: ['#26323f', '#2c3a49'], 4: ['#1c1f3a', '#212548'], 5: ['#6a5238', '#745a3f'], 6: ['#3b2a35', '#43303e'] };
  for (let ty = 0; ty < MH; ty++) for (let tx = 0; tx < MW; tx++) {
    const f = floor[ty][tx]; if (!f) continue; const p = pal[f], c = p[(tx + ty) & 1]; R(x, c, tx * T, ty * T, T, T);
    if (f === 2 || f === 5) { R(x, 'rgba(0,0,0,.18)', tx * T, ty * T + 7 + ((tx & 1) * 3), T, 1); R(x, 'rgba(255,255,255,.04)', tx * T + (tx * 5 % 9), ty * T, 1, T); }
    else if (f === 3) { R(x, 'rgba(255,255,255,.05)', tx * T, ty * T, T, 1); R(x, 'rgba(255,255,255,.05)', tx * T, ty * T, 1, T); R(x, 'rgba(46,230,255,.05)', tx * T + 6, ty * T + 6, 3, 3); }
    else { R(x, 'rgba(255,255,255,.025)', tx * T, ty * T, T, 1); const h = hash(tx, ty); if (h > .86) R(x, 'rgba(255,255,255,.05)', tx * T + 4, ty * T + 4, 2, 2); }
  }
  // rugs
  const rug = (rx, ry, rw, rh, c1, c2) => { R(x, c1, rx * T, ry * T, rw * T, rh * T); R(x, c2, rx * T + 3, ry * T + 3, rw * T - 6, rh * T - 6); x.strokeStyle = 'rgba(255,255,255,.10)'; x.strokeRect(rx * T + 6.5, ry * T + 6.5, rw * T - 13, rh * T - 13); };
  rug(3, 16, 8, 6, '#17324d', '#1d4568'); rug(18, 16, 9, 7, '#6e3f3a', '#7f4c45'); rug(32, 19, 7, 3, '#24435a', '#2b536d'); rug(15, 3, 3, 3, '#12354a', '#164460');
  // walls
  const wallTile = (tx, ty) => { const px = tx * T, py = ty * T; R(x, '#1b2735', px, py, T, T); R(x, '#2b3e55', px, py, T, 3); R(x, '#0f1822', px, py + T - 4, T, 4); R(x, 'rgba(255,255,255,.04)', px, py + 3, T, 1); };
  for (let ty = 0; ty < MH; ty++) for (let tx = 0; tx < MW; tx++) if (solid[ty][tx] && !floor[ty][tx] && !(ty >= 14 && ty <= 25 && tx > 0 && tx < 43 && false)) wallTile(tx, ty);
  // outer top wall with windows (rows 0-1)
  R(x, '#16222f', 0, 0, PW, 2 * T); R(x, '#26384d', 0, 2 * T - 4, PW, 4); R(x, '#0d141c', 0, 2 * T - 1, PW, 1);
  [[3, 4], [8, 4], [17, 4], [21, 4], [32, 4], [36, 4], [3, 15], [8, 15]].forEach(w => { if (w[1] === 15) return; const px = w[0] * T, py = 3; R(x, '#0b141d', px - 1, py - 1, 4 * T - 6, 2 * T - 9); const g = x.createLinearGradient(0, py, 0, py + 20); g.addColorStop(0, '#173a63'); g.addColorStop(1, '#2d6aa0'); x.fillStyle = g; x.fillRect(px + 1, py + 1, 4 * T - 10, 2 * T - 13); R(x, 'rgba(255,255,255,.12)', px + 1, py + 1, 4 * T - 10, 3); R(x, '#0b141d', px + 2 * T - 5, py, 2, 2 * T - 10); });
  // wall posters / lights on room dividers (row 13)
  for (let tx = 1; tx < 43; tx++) if (solid[13][tx]) { if (hash(tx, 3) > .7) { R(x, '#0b141d', tx * T + 3, 13 * T + 3, 10, 7); R(x, ['#2e86c1', '#27ae60', '#c0392b', '#8e44ad'][tx % 4], tx * T + 4, 13 * T + 4, 8, 5); } }
  // lighting pools
  [[7, 8, 120], [22, 8, 130], [36, 8, 120], [7, 20, 120], [22, 20, 140], [36, 20, 120]].forEach(p => { const g = x.createRadialGradient(p[0] * T, p[1] * T, 0, p[0] * T, p[1] * T, p[2]); g.addColorStop(0, 'rgba(255,240,200,.07)'); g.addColorStop(1, 'rgba(255,240,200,0)'); x.fillStyle = g; x.fillRect(p[0] * T - p[2], p[1] * T - p[2], p[2] * 2, p[2] * 2); });
  // room labels (floor stencils)
  x.font = '600 7px monospace'; x.fillStyle = 'rgba(160,220,255,.22)'; [['RESEARCH WING', 2, 12.5], ['ENGINEERING', 16, 12.5], ['OPERATIONS', 31, 12.5], ['HELIX OFFICE', 2, 26.6], ['WAR ROOM', 16, 26.6], ['LOUNGE', 31, 26.6]].forEach(l => x.fillText(l[0], l[1] * T, l[2] * T));
}

/* ---------- actors ---------- */
const DIRV = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };
class Actor {
  constructor(a, i) {
    this.id = a.id; this.def = a; this.name = a.name; const d = DESKS[a.id] || { seat: { x: 21, y: 24 } }; this.tx = d.seat.x; this.ty = d.seat.y; this.x = this.tx * T + 8; this.y = this.ty * T + 11; this.dir = 'up'; this.pose = 'sit'; this.q = []; this.cur = null; this.path = []; this.frame = 0; this.ft = 0;
    this.sit = true; this.status = 'idle'; this.where = 'desk'; this.bubble = null; this.sbub = null; this.carry = null; this.idleT = H.rand(2, 8); this.at = 'desk'; this.progress = 0; this.speed = 50 + Math.random() * 8; this.flash = 0; this.typing = false; this.waitT = 0; this.spark = 0;
  }
  get tile() { return [Math.round((this.x - 8) / T), Math.round((this.y - 11) / T)]; }
  say(icon, ms = 2200, text) { this.bubble = { icon, text, until: performance.now() + ms }; }
  go(x, y, dir, opt) { this.q.push(Object.assign({ t: 'go', x, y, dir }, opt)); return this; }
  wait(ms) { this.q.push({ t: 'wait', ms }); return this; }
  act(fn) { this.q.push({ t: 'fn', fn }); return this; }
  clear() { this.q.length = 0; this.cur = null; this.path = []; this.carry = null; }
  busy() { return !!(this.cur || this.q.length); }
}
function bfs(sx, sy, gx, gy) {
  if (sx === gx && sy === gy) return [];
  const prev = new Int16Array(MW * MH).fill(-1), qx = [sx + sy * MW]; prev[sx + sy * MW] = sx + sy * MW; let h = 0;
  while (h < qx.length) { const c = qx[h++], cx = c % MW, cy = (c / MW) | 0; if (cx === gx && cy === gy) break;
    for (const d of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = cx + d[0], ny = cy + d[1]; if (nx < 0 || ny < 0 || nx >= MW || ny >= MH) continue; const k = nx + ny * MW; if (prev[k] >= 0) continue; if (solid[ny][nx] && !(nx === gx && ny === gy)) continue; prev[k] = c; qx.push(k); } }
  const gk = gx + gy * MW; if (prev[gk] < 0) return null; const out = []; let k = gk; while (k !== sx + sy * MW) { out.push([k % MW, (k / MW) | 0]); k = prev[k]; } return out.reverse();
}
function stepActor(a, dt, now) {
  if (a.bubble && now > a.bubble.until) a.bubble = null;
  a.ft += dt; if (a.ft > .16) { a.ft = 0; a.frame = (a.frame + 1) & 3; }
  if (a.flash > 0) a.flash -= dt;
  // current action
  if (!a.cur) { a.cur = a.q.shift() || null; if (a.cur) { if (a.cur.t === 'go') { const [tx, ty] = a.tile; a.path = bfs(tx, ty, a.cur.x, a.cur.y); if (a.path === null) { a.cur = null; a.path = []; } else { a.pose = 'walk'; } } else if (a.cur.t === 'wait') a.waitT = a.cur.ms / 1000; else if (a.cur.t === 'fn') { try { a.cur.fn(a); } catch (e) { console.error(e); } a.cur = null; } } }
  const c = a.cur;
  if (c && c.t === 'go') {
    if (a.path.length) {
      const [px, py] = a.path[0], tx = px * T + 8, ty = py * T + 11, dx = tx - a.x, dy = ty - a.y, d = Math.hypot(dx, dy), step = (a.id === 'player' ? 0 : 1) * a.speed * dt;
      if (Math.abs(dx) > Math.abs(dy)) a.dir = dx > 0 ? 'right' : 'left'; else if (Math.abs(dy) > .01) a.dir = dy > 0 ? 'down' : 'up';
      if (d <= step) { a.x = tx; a.y = ty; a.path.shift(); } else { a.x += dx / d * step; a.y += dy / d * step; }
      a.pose = 'walk'; a.sit = false;
    } else { a.x = c.x * T + 8; a.y = c.y * T + 11; if (c.dir) a.dir = c.dir; a.pose = c.sit ? 'sit' : 'stand'; a.sit = !!c.sit; a.at = c.at || a.at; a.cur = null; }
  } else if (c && c.t === 'wait') { a.waitT -= dt; a.pose = a.sit ? 'sit' : 'stand'; if (a.waitT <= 0) a.cur = null; }
  else if (!c) { a.pose = a.sit ? 'sit' : 'stand'; behave(a, dt, now); }
}

/* ---------- behaviour: map desired status → what the actor does when its queue is empty ---------- */
const seatOf = id => DESKS[id].seat;
function goSeat(a) { const s = seatOf(a.id); a.go(s.x, s.y, s.dir, { sit: true, at: 'desk' }); }
function behave(a, dt, now) {
  a.typing = false; a.sbub = null;
  if (a.id === 'player') return;
  const st = a.status;
  if (H.state.killed || st === 'offline') { if (a.at !== 'desk') return goSeat(a); a.sbub = 'zzz'; return; }
  if (st === 'working') {
    const where = a.where || 'desk';
    const spotKey = { rack: 'rack', shelf: 'shelf', printer: 'printer', board: 'board', lab: 'lab' }[where];
    if (spotKey) { if (a.at !== where) { const p = H.pick(SPOTS[spotKey]); return void a.go(p[0], p[1], 'up', { at: where }); } a.typing = false; a.sbub = where === 'printer' ? 'doc' : where === 'shelf' ? 'book' : where === 'board' ? 'doc' : 'gear'; return; }
    if (where === 'meeting') { if (a.at !== 'meeting') { const m = MEET[(H.AGENTS.findIndex(q => q.id === a.id)) % MEET.length]; return void a.go(m[0], m[1], m[2], { at: 'meeting', sit: true }); } return; }
    if (a.at !== 'desk') return goSeat(a); a.typing = true; a.sbub = 'code'; return;
  }
  if (st === 'blocked' || st === 'waiting' || st === 'error') { if (a.at !== 'desk') return goSeat(a); a.sbub = st === 'error' ? 'bang' : st === 'blocked' ? 'q' : 'dots'; return; }
  // idle life
  a.idleT -= dt; if (a.idleT > 0) return;
  a.idleT = H.rand(7, 20); if (a.at !== 'desk' && a.at !== 'idle') { goSeat(a); a.idleT = H.rand(4, 9); return; }
  const r = Math.random();
  const back = () => goSeat(a);
  if (a.id === 'helix') { if (r < .3) { const m = H.pick(SPOTS.window); a.go(m[0], m[1], 'up', { at: 'idle' }).wait(3500); back(); } else if (r < .55) { const p = H.pick(SPOTS.coffee); a.go(p[0], p[1], 'up', { at: 'idle' }).act(x => x.say('cup', 2200)).wait(2600); back(); } else if (r < .75) { a.go(DESKS.helix.visit.x + 2, 16, 'down', { at: 'idle' }).wait(2500); back(); } return; }
  if (r < .22) { const p = H.pick(SPOTS.coffee); a.go(p[0], p[1], 'up', { at: 'idle' }).act(x => x.say('cup', 2400)).wait(2800); back(); }
  else if (r < .33) { const p = SPOTS.water[0]; a.go(p[0], p[1], 'up', { at: 'idle' }).act(x => x.say('dots', 1600)).wait(2200); back(); }
  else if (r < .55) { const o = H.AGENTS.map(q => Town.actors[q.id]).filter(q => q && q !== a && q.id !== 'player' && q.status === 'idle' && !q.busy()); if (o.length) { const b = H.pick(o); Town.chat(a, b); } }
  else if (r < .68) { const m = H.pick(SPOTS.window); a.go(m[0], m[1], 'up', { at: 'idle' }).act(x => x.say('dots', 1800)).wait(3200); back(); }
  else if (r < .8) { const p = H.pick(SPOTS.sofa); a.go(p[0], p[1], p[2], { at: 'idle', sit: true }).wait(7000); back(); }
  else if (r < .9) { const p = H.pick(SPOTS.plant); a.go(p[0], p[1], 'up', { at: 'idle' }).wait(2200); back(); }
}
const SMALLTALK = ['dots', 'bolt', 'cup', 'check', 'mag', 'book'];
Town.chat = (a, b) => {
  const bt = DESKS[b.id].visit; if (!bt) return; b.clear(); a.clear();
  a.go(bt.x, bt.y, bt.dir === 'left' ? 'left' : 'right', { at: 'idle' }); a.act(x => { b.dir = bt.dir === 'left' ? 'right' : 'left'; x.say(H.pick(SMALLTALK), 1800); }).wait(1600).act(() => b.say(H.pick(SMALLTALK), 1800)).wait(1900).act(x => x.say(H.pick(SMALLTALK), 1500)).wait(1500); goSeat(a);
};
function visit(from, to, o = {}) {   // `from` walks next to `to`'s desk
  const A = Town.actors[from], B = Town.actors[to]; if (!A || !B || A === B) return; const vs = DESKS[to].visit;
  A.clear(); A.go(vs.x, vs.y, vs.dir, { at: 'visit' }).act(() => { B.dir = vs.dir === 'left' ? 'right' : 'left'; if (o.icon) A.say(o.icon, 2000, o.text); if (o.carry) A.carry = null; B.say(o.reply || 'check', 2000); if (B.at === 'desk' && B.status !== 'working') B.flash = .6; }).wait(o.ms || 2200);
  if (o.carry) { A.carry = o.carry; }
}

/* ---------- player ---------- */
const keys = {}; let player = null;
function movePlayer(a, dt) {
  const dx = (keys.d || keys.arrowright ? 1 : 0) - (keys.a || keys.arrowleft ? 1 : 0), dy = (keys.s || keys.arrowdown ? 1 : 0) - (keys.w || keys.arrowup ? 1 : 0);
  if (!dx && !dy) { a.pose = 'stand'; return; } const sp = 68 * dt, n = Math.hypot(dx, dy), vx = dx / n * sp, vy = dy / n * sp;
  const free = (px, py) => { for (const o of [[-4, -1], [4, -1], [-4, -6], [4, -6]]) { const tx = Math.floor((px + o[0]) / T), ty = Math.floor((py + o[1]) / T); if (tx < 0 || ty < 0 || tx >= MW || ty >= MH || solid[ty][tx]) return false; } return true; };
  if (free(a.x + vx, a.y)) a.x += vx; if (free(a.x, a.y + vy)) a.y += vy; a.pose = 'walk'; a.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up'); a.sit = false;
}

/* ---------- sprite drawing ---------- */
function drawActor(x, a, t) {
  const fx = Math.round(a.x), fy = Math.round(a.y) + 3, d = a.def, sit = a.pose === 'sit', walk = a.pose === 'walk', f = a.frame, dir = a.dir;
  const off = sit ? -4 : 0, bob = walk && (f & 1) ? -1 : 0, dim = a.status === 'offline' || H.state.killed;
  const skin = d.skin, hair = d.hair, out = d.outfit, pants = '#222a3a';
  x.save(); if (dim) x.globalAlpha = .55;
  R(x, 'rgba(0,0,0,.32)', fx - 5, fy - 2, 10, 3);
  if (a.status !== 'idle' && a.status && a.id !== 'player') { const sc = { working: '#46f0a0', blocked: '#ffb020', waiting: '#ffb020', error: '#ff4d5e' }[a.status]; if (sc) { x.globalAlpha = .55; R(x, sc, fx - 6, fy - 1, 12, 1); x.globalAlpha = dim ? .55 : 1; } }
  if (!sit) { const l = walk ? ((f === 1) ? -1 : (f === 3 ? 1 : 0)) : 0; R(x, pants, fx - 3, fy - 7 + (l < 0 ? -1 : 0), 3, 6 + (l < 0 ? 1 : 0)); R(x, pants, fx, fy - 7 + (l > 0 ? -1 : 0), 3, 6 + (l > 0 ? 1 : 0)); R(x, '#10141c', fx - 3, fy - 1, 3, 1); R(x, '#10141c', fx, fy - 1, 3, 1); }
  const by = fy - 14 + off + bob;
  const side = dir === 'left' || dir === 'right';
  // body
  R(x, out, fx - (side ? 3 : 4), by, side ? 6 : 8, 8); R(x, 'rgba(255,255,255,.12)', fx - (side ? 3 : 4), by, side ? 6 : 8, 1); R(x, 'rgba(0,0,0,.18)', fx - (side ? 3 : 4), by + 7, side ? 6 : 8, 1);
  // arms
  const sw = walk ? ((f === 1) ? 1 : (f === 3 ? -1 : 0)) : 0;
  if (a.typing) { const ty = (Math.floor(t * 9) & 1); R(x, out, fx - 6, by + 2, 2, 5 + ty); R(x, skin, fx - 6, by + 6 + ty, 2, 2); R(x, out, fx + 4, by + 2, 2, 6 - ty); R(x, skin, fx + 4, by + 6 + (1 - ty), 2, 2); }
  else if (!side) { R(x, out, fx - 6, by + 1 + sw, 2, 6); R(x, skin, fx - 6, by + 7 + sw, 2, 2); R(x, out, fx + 4, by + 1 - sw, 2, 6); R(x, skin, fx + 4, by + 7 - sw, 2, 2); }
  else { R(x, out, fx - 1, by + 1 + sw, 2, 6); R(x, skin, fx - 1, by + 7 + sw, 2, 2); }
  // head
  const hy = by - 8;
  R(x, skin, fx - 4, hy, 8, 8);
  if (dir === 'down') { R(x, hair, fx - 5, hy - 2, 10, 4); R(x, hair, fx - 5, hy, 2, 5); R(x, hair, fx + 3, hy, 2, 5); R(x, '#16202c', fx - 2, hy + 4, 1, 2); R(x, '#16202c', fx + 1, hy + 4, 1, 2); }
  else if (dir === 'up') { R(x, hair, fx - 5, hy - 2, 10, 10); R(x, 'rgba(0,0,0,.2)', fx - 5, hy + 7, 10, 1); }
  else { const s = dir === 'left' ? -1 : 1; R(x, hair, fx - 5, hy - 2, 10, 4); R(x, hair, s > 0 ? fx - 5 : fx + 1, hy, 4, 6); R(x, '#16202c', s > 0 ? fx + 1 : fx - 3, hy + 4, 1, 2); }
  // accessories
  switch (d.acc) {
    case 'glasses': if (dir === 'down') { R(x, '#10202c', fx - 4, hy + 3, 8, 1); R(x, 'rgba(160,220,255,.7)', fx - 3, hy + 4, 2, 2); R(x, 'rgba(160,220,255,.7)', fx + 1, hy + 4, 2, 2); } break;
    case 'cap': R(x, '#c0392b', fx - 5, hy - 3, 10, 3); if (dir === 'down') R(x, '#a93226', fx - 5, hy, 10, 1); break;
    case 'headset': R(x, '#111', fx - 5, hy - 3, 10, 1); R(x, '#222', fx - 5, hy + 1, 2, 4); R(x, '#222', fx + 3, hy + 1, 2, 4); if (dir === 'down') R(x, '#111', fx - 4, hy + 5, 4, 1); break;
    case 'goggles': if (dir === 'down') { R(x, '#ff9f1a', fx - 4, hy + 3, 8, 3); R(x, '#222', fx - 3, hy + 4, 2, 1); R(x, '#222', fx + 1, hy + 4, 2, 1); } else R(x, '#ff9f1a', fx - 5, hy + 1, 10, 1); break;
    case 'phones': R(x, '#e84393', fx - 5, hy - 3, 10, 1); R(x, '#e84393', fx - 6, hy + 1, 2, 4); R(x, '#e84393', fx + 4, hy + 1, 2, 4); break;
    case 'tie': if (dir === 'down') { R(x, '#c0392b', fx - 1, by + 1, 2, 5); R(x, '#fff', fx - 2, by, 4, 1); } break;
    case 'bun': R(x, hair, fx - 2, hy - 5, 4, 3); break;
    case 'hardhat': R(x, '#f1c40f', fx - 5, hy - 4, 10, 3); R(x, '#d4ac0d', fx - 6, hy - 1, 12, 1); break;
    case 'scarf': R(x, '#c0392b', fx - 4, by - 1, 8, 2); break;
    case 'visor': if (dir === 'down') { R(x, '#2ee6ff', fx - 4, hy + 3, 8, 2); R(x, 'rgba(46,230,255,.35)', fx - 5, hy + 2, 10, 4); } else if (side) R(x, '#2ee6ff', dir === 'left' ? fx - 4 : fx + 1, hy + 3, 3, 2); R(x, '#2ee6ff', fx - 5, by, 2, 1); R(x, '#2ee6ff', fx + 3, by, 2, 1); break;
    case 'player': R(x, '#fff', fx - 4, by - 1, 8, 2); R(x, '#fff', fx - 2, by + 6, 4, 2); break;
  }
  if (a.carry) { const cy = by - 2 + Math.sin(t * 8) * .6; R(x, '#f4f4ee', fx + 5, cy, 6, 8); R(x, '#8aa', fx + 6, cy + 2, 4, 1); R(x, '#8aa', fx + 6, cy + 4, 4, 1); R(x, '#2ee6ff', fx + 6, cy + 6, 2, 1); }
  x.restore();
}

/* ---------- dynamic furniture overlays ---------- */
function drawScreens(x, o, t) {
  const A = Town.actors[o.agent], st = A ? (A.status) : 'idle', mons = o.mons || 1, W = o.w * T, ox = o.x * T, oy = o.y * T - 16 + 16;
  for (let m = 0; m < mons; m++) {
    const mw = mons > 1 ? 18 : 20, mx = ox + W / 2 - (mons * mw + (mons - 1) * 2) / 2 + m * (mw + 2), my = oy - 10 + 2 + (mons > 1 && m !== 1 ? 1 : 0);
    R(x, '#0b1118', mx, my, mw, 13); R(x, '#1a2430', mx + 1, my + 1, mw - 2, 10); R(x, '#26323f', mx + mw / 2 - 2, my + 13, 4, 2);
    const kill = H.state.killed || st === 'offline'; let col = st === 'working' ? '#2fe0a0' : st === 'error' ? '#ff4d5e' : (st === 'blocked' || st === 'waiting') ? '#ffb020' : '#2e6aa6';
    if (kill) { R(x, '#06090d', mx + 1, my + 1, mw - 2, 10); continue; }
    R(x, st === 'working' ? '#071a17' : st === 'error' ? '#240a0e' : '#0a1b30', mx + 1, my + 1, mw - 2, 10);
    const rows = 4, sc = st === 'working' ? Math.floor(t * 7) : 0;
    for (let r = 0; r < rows; r++) { const w = 3 + Math.floor(hash(sc + r * 3 + m, o.x) * (mw - 8)); x.globalAlpha = st === 'working' ? .95 : .5; R(x, col, mx + 3 + (r % 2) * 2, my + 2 + r * 2.3 | 0, w, 1); }
    x.globalAlpha = 1;
    if (st === 'working') { x.globalCompositeOperation = 'lighter'; const g = x.createRadialGradient(mx + mw / 2, my + 14, 1, mx + mw / 2, my + 14, 24); g.addColorStop(0, 'rgba(47,224,160,.18)'); g.addColorStop(1, 'rgba(47,224,160,0)'); x.fillStyle = g; x.fillRect(mx - 14, my - 8, mw + 28, 44); x.globalCompositeOperation = 'source-over'; }
  }
}
function drawDyn(x, o, t) {
  if (o.dyn === 'rack') { for (let i = 0; i < 6; i++) for (let j = 0; j < 3; j++) { const on = hash(i + j * 7 + (Math.floor(t * 2.2 + o.x) | 0), o.x + j) > .45; R(x, on ? (j === 2 ? '#ffb020' : '#46f0a0') : '#1a2a22', o.x * T + 6 + j * 4, o.y * T + 6 + i * 4.5, 2, 1.5); } const sys = Town.actors.sysmon; if (sys && sys.status === 'working') { x.globalCompositeOperation = 'lighter'; const g = x.createRadialGradient(o.x * T + 16, o.y * T + 18, 1, o.x * T + 16, o.y * T + 18, 30); g.addColorStop(0, 'rgba(70,240,160,.16)'); g.addColorStop(1, 'rgba(70,240,160,0)'); x.fillStyle = g; x.fillRect(o.x * T - 14, o.y * T - 12, 60, 60); x.globalCompositeOperation = 'source-over'; } }
  else if (o.dyn === 'core') {
    const cx = o.x * T + 16, cy = o.y * T + 12; R(x, 'rgba(0,0,0,.3)', cx - 11, cy + 8, 22, 4); R(x, '#2a3647', cx - 9, cy + 6, 18, 6); R(x, '#3e5068', cx - 9, cy + 6, 18, 2);
    const st = H.state.voice, col = { idle: '#2ee6ff', listening: '#46f0a0', thinking: '#9b7bff', speaking: '#ffd27a', error: '#ff4d5e' }[st] || '#2ee6ff', r = 7 + Math.sin(t * (st === 'thinking' ? 8 : 3)) * (st === 'idle' ? .8 : 1.8);
    x.globalCompositeOperation = 'lighter'; const g = x.createRadialGradient(cx, cy, 0, cx, cy, 26); g.addColorStop(0, col + 'aa'); g.addColorStop(1, col + '00'); x.fillStyle = g; x.fillRect(cx - 30, cy - 30, 60, 60); x.globalCompositeOperation = 'source-over';
    x.fillStyle = col; x.beginPath(); x.arc(cx, cy, r, 0, 6.28); x.fill(); x.fillStyle = 'rgba(255,255,255,.7)'; x.beginPath(); x.arc(cx - 2, cy - 2, r * .4, 0, 6.28); x.fill();
    x.strokeStyle = col; x.lineWidth = 1; x.beginPath(); x.ellipse(cx, cy, r + 5, 3 + Math.sin(t * 2) * 1, t, 0, 6.28); x.stroke();
  }
  else if (o.dyn === 'holo') {
    const cx = (o.x + 3) * T, cy = (o.y + 2) * T; R(x, 'rgba(0,0,0,.28)', o.x * T + 2, o.y * T + 16 * 4 - 8, 6 * T - 4, 6);
    x.fillStyle = '#4b3a2b'; x.beginPath(); x.ellipse(cx, cy + 4, 46, 28, 0, 0, 6.28); x.fill(); x.fillStyle = '#6d5238'; x.beginPath(); x.ellipse(cx, cy, 46, 27, 0, 0, 6.28); x.fill(); x.fillStyle = '#7b5d40'; x.beginPath(); x.ellipse(cx, cy - 1, 40, 22, 0, 0, 6.28); x.fill();
    const active = Object.values(H.state.tasks).some(k => k.status === 'running'); x.strokeStyle = active ? 'rgba(46,230,255,.9)' : 'rgba(46,230,255,.35)'; x.lineWidth = 1; for (let i = 0; i < 3; i++) { x.beginPath(); x.ellipse(cx, cy - 2, 12 + i * 7 + (active ? Math.sin(t * 3 + i) * 2 : 0), 6 + i * 3.5, 0, 0, 6.28); x.stroke(); }
    if (active) { x.globalCompositeOperation = 'lighter'; const g = x.createRadialGradient(cx, cy - 2, 0, cx, cy - 2, 40); g.addColorStop(0, 'rgba(46,230,255,.25)'); g.addColorStop(1, 'rgba(46,230,255,0)'); x.fillStyle = g; x.fillRect(cx - 44, cy - 40, 88, 80); x.globalCompositeOperation = 'source-over'; }
  }
  else if (o.dyn === 'board') {
    const bx = o.x * T, by = 13 * T + 2, bw = 8 * T, bh = 2 * T + 6; R(x, '#0a1119', bx, by, bw, bh); R(x, '#26384d', bx, by, bw, 2); R(x, '#26384d', bx, by + bh - 2, bw, 2);
    const cols = [['BACKLOG', '#7a8a99', ['backlog', 'ready']], ['RUNNING', '#46f0a0', ['running']], ['BLOCKED', '#ffb020', ['blocked']], ['DONE', '#2ee6ff', ['done']]], cw = bw / 4;
    cols.forEach((c, i) => { const cx = bx + i * cw; if (i) R(x, 'rgba(255,255,255,.07)', cx, by + 2, 1, bh - 4); x.fillStyle = c[1]; x.font = '5px monospace'; x.fillText(c[0], cx + 3, by + 8); const tk = Object.values(H.state.tasks).filter(k => c[2].includes(k.status)).slice(-4); tk.forEach((k, j) => { R(x, H.agentColor(k.assignee), cx + 3, by + 11 + j * 5.2, cw - 6, 4); R(x, 'rgba(0,0,0,.35)', cx + 4, by + 12 + j * 5.2, cw - 8, 2); if (c[0] === 'RUNNING') R(x, '#fff', cx + 4, by + 12 + j * 5.2, Math.max(1, (cw - 8) * (k.progress || 0)), 2); }); });
  }
}

/* ---------- view ---------- */
let cv, cx, buf, bx, view = { s: 1, ox: 0, oy: 0, zoom: 1, px: 0, py: 0 }, dpr = 1, hoverActor = null, lastNear = null;
function layout() { const p = cv.parentElement, w = p.clientWidth, h = p.clientHeight; dpr = Math.min(2, H.quality.dpr || 1); cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); view.W = w; view.H = h; view.fit = Math.min(w / PW, h / PH) * 1; }
function sc() { return view.fit * view.zoom; }
function w2s(x, y) { const s = sc(); return [(view.W - PW * s) / 2 + view.px + x * s, (view.H - PH * s) / 2 + view.py + y * s]; }
function s2w(x, y) { const s = sc(); return [(x - (view.W - PW * s) / 2 - view.px) / s, (y - (view.H - PH * s) / 2 - view.py) / s]; }
function bubble(ctx, a, s, now) {
  const [sx, sy] = w2s(a.x, a.y - 29 - (a.pose === 'sit' ? -4 : 0)), z = Math.max(1, s * 1.25); const b = a.bubble, icon = b ? b.icon : a.sbub; if (!icon || (a.pose === 'walk' && !b)) return;
  const w = (b && b.text ? Math.min(90, 8 + b.text.length * 5.2) : 22) * z * .85, h = 15 * z * .85, x0 = sx - w / 2, y0 = sy - h - 5 * z * .5 - (a.status === 'working' && a.progress > 0 ? 5 : 0);
  ctx.save(); ctx.globalAlpha = b ? 1 : .88; ctx.fillStyle = 'rgba(8,18,28,.94)'; ctx.strokeStyle = 'rgba(46,230,255,.6)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x0, y0, w, h, 4 * z * .6) : ctx.rect(x0, y0, w, h); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(sx - 3, y0 + h); ctx.lineTo(sx, y0 + h + 4 * z * .6); ctx.lineTo(sx + 3, y0 + h); ctx.fill();
  if (b && b.text) { ctx.fillStyle = '#dff'; ctx.font = `${8 * z * .9}px monospace`; ctx.textAlign = 'center'; ctx.fillText(b.text, sx, y0 + h * .68); } else icon2(ctx, icon, sx, y0 + h / 2, 5.2 * z * .85, now);
  ctx.restore();
}
function icon2(c, n, x, y, r, now) {
  c.save(); c.translate(x, y); c.lineWidth = Math.max(1, r * .22); c.lineCap = 'round'; c.strokeStyle = '#7fe8ff'; c.fillStyle = '#7fe8ff';
  const t = now / 1000;
  switch (n) {
    case 'dots': for (let i = -1; i <= 1; i++) { c.globalAlpha = .45 + .55 * Math.max(0, Math.sin(t * 5 - i * 1.2)); c.beginPath(); c.arc(i * r * .55, 0, r * .16, 0, 6.28); c.fill(); } break;
    case 'bang': c.strokeStyle = c.fillStyle = '#ff6b78'; c.beginPath(); c.moveTo(0, -r * .7); c.lineTo(0, r * .15); c.stroke(); c.beginPath(); c.arc(0, r * .55, r * .13, 0, 6.28); c.fill(); break;
    case 'q': c.strokeStyle = c.fillStyle = '#ffc04a'; c.beginPath(); c.arc(0, -r * .25, r * .35, Math.PI, Math.PI * 2.4); c.lineTo(0, r * .25); c.stroke(); c.beginPath(); c.arc(0, r * .6, r * .12, 0, 6.28); c.fill(); break;
    case 'check': c.strokeStyle = '#46f0a0'; c.beginPath(); c.moveTo(-r * .5, 0); c.lineTo(-r * .1, r * .4); c.lineTo(r * .55, -r * .45); c.stroke(); break;
    case 'doc': c.strokeRect(-r * .38, -r * .55, r * .76, r * 1.1); c.beginPath(); c.moveTo(-r * .2, -r * .15); c.lineTo(r * .2, -r * .15); c.moveTo(-r * .2, r * .15); c.lineTo(r * .2, r * .15); c.stroke(); break;
    case 'cup': c.strokeStyle = '#ffd27a'; c.strokeRect(-r * .4, -r * .25, r * .6, r * .6); c.beginPath(); c.arc(r * .3, r * .05, r * .2, -1.5, 1.5); c.stroke(); c.globalAlpha = .6; c.beginPath(); c.moveTo(-r * .2, -r * .5); c.quadraticCurveTo(-r * .05, -r * .8, -r * .2, -r * 1); c.stroke(); break;
    case 'mag': c.beginPath(); c.arc(-r * .1, -r * .1, r * .4, 0, 6.28); c.stroke(); c.beginPath(); c.moveTo(r * .2, r * .2); c.lineTo(r * .6, r * .6); c.stroke(); break;
    case 'gear': c.beginPath(); c.arc(0, 0, r * .3, 0, 6.28); c.stroke(); for (let i = 0; i < 6; i++) { const a = i / 6 * 6.28 + t * 2; c.beginPath(); c.moveTo(Math.cos(a) * r * .42, Math.sin(a) * r * .42); c.lineTo(Math.cos(a) * r * .62, Math.sin(a) * r * .62); c.stroke(); } break;
    case 'code': c.beginPath(); c.moveTo(-r * .2, -r * .4); c.lineTo(-r * .6, 0); c.lineTo(-r * .2, r * .4); c.moveTo(r * .2, -r * .4); c.lineTo(r * .6, 0); c.lineTo(r * .2, r * .4); c.stroke(); break;
    case 'bolt': c.fillStyle = '#ffd27a'; c.beginPath(); c.moveTo(r * .15, -r * .6); c.lineTo(-r * .4, r * .1); c.lineTo(0, r * .1); c.lineTo(-r * .15, r * .6); c.lineTo(r * .4, -r * .15); c.lineTo(0, -r * .15); c.fill(); break;
    case 'book': c.strokeRect(-r * .55, -r * .4, r * 1.1, r * .8); c.beginPath(); c.moveTo(0, -r * .4); c.lineTo(0, r * .4); c.stroke(); break;
    case 'mail': c.strokeRect(-r * .55, -r * .35, r * 1.1, r * .7); c.beginPath(); c.moveTo(-r * .55, -r * .35); c.lineTo(0, r * .1); c.lineTo(r * .55, -r * .35); c.stroke(); break;
    case 'zzz': c.fillStyle = '#7a8a99'; c.font = `bold ${r * 1.2}px monospace`; c.textAlign = 'center'; c.fillText('z' + 'z'.repeat(Math.floor(t * 1.5) % 3), 0, r * .4); break;
    case 'spark': c.strokeStyle = '#ffe28a'; for (let i = 0; i < 4; i++) { const a = i * 1.57 + t * 3; c.beginPath(); c.moveTo(Math.cos(a) * r * .15, Math.sin(a) * r * .15); c.lineTo(Math.cos(a) * r * .6, Math.sin(a) * r * .6); c.stroke(); } break;
    case 'hi': c.fillStyle = '#7fe8ff'; c.font = `bold ${r * 1.1}px monospace`; c.textAlign = 'center'; c.fillText('hi', 0, r * .35); break;
  }
  c.restore();
}
function render(dt, t) {
  const now = performance.now(), ctx = cx; if (!cv.width) layout();
  const rect = [...objs].map(o => o);
  bx.drawImage(BG, 0, 0);
  // drawables sorted by depth
  const list = []; objs.forEach(o => list.push({ y: o.sortY, o })); Object.values(Town.actors).forEach(a => list.push({ y: a.y + 3 + (a.sit ? 8 : 0), a })); list.sort((p, q) => p.y - q.y);
  for (const e of list) {
    if (e.o) { const o = e.o; if (o.spr) bx.drawImage(o.spr, o.x * T, o.y * T - (o.oy || (o.spr.height - o.h * T))); if (o.kind === 'desk') drawScreens(bx, o, t); if (o.dyn) drawDyn(bx, o, t); }
    else drawActor(bx, e.a, t);
  }
  // meeting table highlight and global grade
  bx.globalCompositeOperation = 'multiply'; const vg = bx.createRadialGradient(PW / 2, PH / 2, PH * .25, PW / 2, PH / 2, PH * .85); vg.addColorStop(0, 'rgba(255,255,255,1)'); vg.addColorStop(1, 'rgba(120,140,170,1)'); bx.fillStyle = vg; bx.fillRect(0, 0, PW, PH); bx.globalCompositeOperation = 'source-over';
  const s = sc(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#04090e'; ctx.fillRect(0, 0, cv.width, cv.height); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.imageSmoothingEnabled = Math.abs(s * dpr - Math.round(s * dpr)) > .02; ctx.imageSmoothingQuality = 'high'; const [ox, oy] = w2s(0, 0); ctx.drawImage(buf, ox, oy, PW * s, PH * s);
  // overlays in screen space (crisp)
  Object.values(Town.actors).forEach(a => {
    const [sx, sy] = w2s(a.x, a.y + 3); const sel = Town.sel === a.id, z = Math.max(.9, s);
    if (a.status === 'working' && a.progress > 0 && a.pose !== 'walk') { const w = 22 * z, [px, py] = w2s(a.x, a.y - 27 - (a.sit ? -4 : 0)); ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.fillRect(px - w / 2, py - 3, w, 3 * z * .8); ctx.fillStyle = H.agentColor(a.id); ctx.fillRect(px - w / 2, py - 3, w * a.progress, 3 * z * .8); }
    if (sel) { ctx.strokeStyle = '#2ee6ff'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.ellipse(sx, sy - 2 * z, 10 * z, 4 * z, 0, 0, 6.28); ctx.stroke(); }
    bubble(ctx, a, s, now);
    ctx.font = `${Math.max(8, 8.5 * z)}px "Share Tech Mono",monospace`; ctx.textAlign = 'center'; const nm = a.id === 'player' ? 'YOU' : a.name; const tw = ctx.measureText(nm).width + 6;
    ctx.fillStyle = sel || hoverActor === a ? 'rgba(46,230,255,.88)' : 'rgba(5,12,19,.78)'; ctx.fillRect(sx - tw / 2, sy + 2 * z, tw, 10 * z); ctx.fillStyle = sel || hoverActor === a ? '#021018' : (a.id === 'helix' ? '#2ee6ff' : '#bfe6f0'); ctx.fillText(nm, sx, sy + 2 * z + 7.4 * z);
    if (a.spark > 0) { a.spark -= dt; icon2(ctx, 'spark', sx, sy - 34 * z, 7 * z, now); }
  });
  // interaction prompt
  const pr = H.$('#town-prompt'); const nearby = nearest(); if (nearby && Town.focused) { const [px, py] = w2s(player.x, player.y - 30); pr.hidden = false; pr.style.left = px + 'px'; pr.style.top = py - 8 + 'px'; pr.textContent = 'Press E · ' + nearby.label; } else pr.hidden = true; lastNear = nearby;
}
function nearest() {
  if (!player) return null; let best = null, bd = 28 * 28; Object.values(Town.actors).forEach(a => { if (a === player) return; const d = (a.x - player.x) ** 2 + (a.y - player.y) ** 2; if (d < bd) { bd = d; best = { label: 'Talk to ' + a.name, run: () => Town.select(a.id) }; } });
  objs.forEach(o => { if (!o.act || !o.front) return; const fx = o.front[0] * T + 8, fy = o.front[1] * T + 11, d = (fx - player.x) ** 2 + (fy - player.y) ** 2; if (d < 26 * 26 && d < bd) { bd = d; best = { label: o.label, run: () => interact(o) }; } });
  return best;
}
function interact(o) {
  const P = player; switch (o.act) {
    case 'coffee': P.say('cup', 2500); H.toast('Fresh coffee. Productivity +1.'); break; case 'water': P.say('dots', 1500); break;
    case 'board': H.hub && H.hub.open('hub'); break; case 'core': H.voice && H.voice.toggle(); break; case 'memory': H.openDrawer && H.openDrawer('memory'); break;
    case 'sit': P.say('zzz', 2000); break;
  }
}

/* ---------- events ---------- */
function bindEvents() {
  H.bus.on('agent.status', e => {
    const a = Town.actors[e.agent]; if (!a) return; const prev = a.status; a.status = e.status || a.status; a.where = e.where || 'desk'; a.progress = e.progress || 0;
    if (prev !== a.status) { a.idleT = H.rand(2, 6); if (a.status === 'working' || a.status === 'blocked' || a.status === 'error') { if (!a.busy() || a.at === 'idle') { /* leave current idle activity */ } } if (prev === 'working' && a.status === 'idle') { a.spark = 1.4; a.say('check', 2200); } if (a.status === 'error') a.say('bang', 3000); }
    if (a.status === 'working' && !a.cur && a.q.length === 0 && a.at !== (a.where === 'desk' ? 'desk' : a.where)) { /* behave() handles routing */ }
    if (a.status === 'working' && a.at === 'idle') { a.q.length = 0; }
    refreshHud();
  });
  H.bus.on('interact', e => {
    const k = e.kind || 'brief', ico = { brief: 'doc', handoff: 'doc', review: 'check', help: 'q', chat: 'dots' }[k] || 'dots';
    if (k === 'brief') visit(e.from || 'helix', e.to, { icon: 'doc', text: e.text ? e.text.slice(0, 18) : '', reply: 'bang', ms: 2400 });
    else if (k === 'handoff') visit(e.from, e.to, { icon: 'doc', carry: true, reply: 'check', ms: 2400 });
    else if (k === 'review') visit(e.from, e.to || 'helix', { icon: 'check', carry: true, reply: 'spark', ms: 2200 });
    else if (k === 'help') visit(e.from, e.to, { icon: 'q', reply: 'bolt', ms: 2200 });
    else if (k === 'meeting') (e.agents || []).forEach((id, i) => { const a = Town.actors[id]; if (!a) return; a.clear(); const m = MEET[(i + (id === 'helix' ? 0 : 1)) % MEET.length]; a.go(m[0], m[1], m[2], { at: 'meeting', sit: true }).act(x => x.say(i % 2 ? 'dots' : 'doc', 1800)).wait(e.ms || 4500); goSeat(a); });
    else visit(e.from, e.to, { icon: ico });
  });
  H.bus.on('confirm.request', e => { const a = Town.actors[e.agent]; if (a) { a.say('q', 6000); } });
  H.bus.on('tool.call', e => { const a = Town.actors[e.agent]; if (a && a.status === 'working') { a.flash = .4; if (!e.ok) a.say('bang', 2000); } });
  H.bus.on('verify', e => { const a = Town.actors[(H.state.tasks[e.task] || {}).assignee]; if (a) a.say(e.checks.every(c => c.ok) ? 'check' : 'bang', 2400); });
  H.bus.on('kill', () => { Object.values(Town.actors).forEach(a => { if (a.id === 'player') return; a.clear(); a.status = 'offline'; a.say('bang', 2000); }); refreshHud(); });
  H.bus.on('resume', () => { Object.values(Town.actors).forEach(a => { if (a.id !== 'player') { a.status = 'idle'; a.idleT = H.rand(1, 3); } }); refreshHud(); });
  ['task.upsert', 'voice.state', 'model', 'ctx', 'mode'].forEach(t => H.bus.on(t, refreshHud));
}

/* ---------- HUD (roster / status bar / card) ---------- */
function faceCanvas(def) { const c = mkc(20, 20), x = c.getContext('2d'); x.imageSmoothingEnabled = false; R(x, def.outfit, 4, 14, 12, 6); R(x, def.skin, 5, 5, 10, 9); R(x, def.hair, 4, 3, 12, 4); R(x, def.hair, 4, 5, 2, 6); R(x, def.hair, 14, 5, 2, 6); R(x, '#16202c', 7, 10, 2, 2); R(x, '#16202c', 11, 10, 2, 2); if (def.acc === 'glasses') R(x, 'rgba(160,220,255,.8)', 6, 9, 8, 1); if (def.acc === 'visor') R(x, '#2ee6ff', 5, 9, 10, 2); if (def.acc === 'hardhat') R(x, '#f1c40f', 3, 2, 14, 3); if (def.acc === 'cap') R(x, '#c0392b', 3, 2, 14, 3); return c; }
function refreshHud() {
  const ros = H.$('#town-roster'); if (!ros) return;
  if (!ros._built) { ros._built = 1; H.AGENTS.forEach(a => { const d = H.el('div', { class: 'rost', 'data-id': a.id, title: a.role, onclick: () => Town.select(Town.sel === a.id ? null : a.id) }, faceCanvas(a), H.el('span', null, a.name), H.el('i')); ros.append(d); }); }
  H.$$('.rost', ros).forEach(d => { const st = H.state.agents[d.dataset.id]; d.querySelector('i').className = 's-' + (H.state.killed ? 'offline' : st.status); d.classList.toggle('sel', Town.sel === d.dataset.id); });
  const subs = H.AGENTS.filter(a => a.id !== 'helix'), busy = subs.filter(a => H.state.agents[a.id].status === 'working').length, seated = Object.values(Town.actors).filter(a => a.id !== 'player' && a.pose === 'sit').length;
  H.$('#seat-txt').textContent = `${seated}/${H.AGENTS.length} seat`; H.$('#busy-txt').textContent = `${busy}/${subs.length} busy`;
  const on = H.state.mode === 'live', so = H.$('#st-online'); so.classList.toggle('on', !H.state.killed); so.querySelector('span').textContent = H.state.killed ? 'Halted' : on ? 'Online' : 'Offline';
  H.$('#st-model span').textContent = H.state.model || 'No model yet'; const c = H.state.ctx; H.$('#ctx-fill').style.width = Math.min(100, c.used / c.max * 100) + '%'; H.$('#ctx-txt').textContent = c.used ? (c.used > 1e4 ? Math.round(c.used / 1000) + 'k' : c.used) + ' / ' + (c.max >= 1e6 ? c.max / 1e6 + 'M' : Math.round(c.max / 1000) + 'k') : '—';
  const pill = H.$('#town-ready'), anyRun = busy > 0; pill.textContent = H.state.killed ? 'HALTED' : anyRun ? 'WORKING' : 'READY'; pill.className = 'state-pill' + (H.state.killed ? ' err' : anyRun ? ' busy' : '');
  if (Town.sel) cardUpdate();
}
function cardUpdate() {
  const box = H.$('#town-card'), id = Town.sel; if (!id || id === 'player') { box.hidden = true; return; } const d = H.agent(id), st = H.state.agents[id], t = st.task && H.state.tasks[st.task];
  box.hidden = false; box.innerHTML = ''; box.append(H.el('h4', null, H.el('span', { style: 'color:' + H.agentColor(id) }, '●'), d.name, H.el('span', { class: 'tag ' + (st.status === 'working' ? 'ok' : st.status === 'error' ? 'err' : st.status === 'idle' ? '' : 'warn'), style: 'margin-left:auto' }, H.state.killed ? 'OFFLINE' : st.status.toUpperCase())),
    H.el('div', { class: 'row' }, H.el('span', null, 'Profile'), H.el('b', null, id)), H.el('div', { class: 'row' }, H.el('span', null, 'Role'), H.el('b', null, d.role)), H.el('div', { class: 'row' }, H.el('span', null, 'Task'), H.el('b', null, t ? t.title : '—')), H.el('div', { class: 'row' }, H.el('span', null, 'Note'), H.el('b', null, st.note || '—')),
    H.el('div', { class: 'bar' }, H.el('i', { style: `width:${Math.round((st.progress || 0) * 100)}%` })),
    H.el('div', { class: 'acts' }, H.el('button', { class: 'btn sm', onclick: () => { const i = H.$('#cmd-input'); i.value = '@' + id + ' '; i.focus(); } }, 'Message'), H.el('button', { class: 'btn sm', onclick: () => { H.openDrawer && H.openDrawer('soul', id); } }, 'SOUL.md'), H.el('button', { class: 'btn sm', onclick: () => Town.follow = Town.follow === id ? null : id }, 'Follow'), H.el('button', { class: 'btn sm', onclick: () => Town.select(null) }, 'Close')));
}
Town.select = id => { Town.sel = id; refreshHud(); if (!id) H.$('#town-card').hidden = true; };
Town.agentTile = id => { const a = Town.actors[id]; return a ? a.tile : null; };

/* ---------- init ---------- */
Town.init = function () {
  cv = H.$('#town-canvas'); cx = cv.getContext('2d'); buf = mkc(PW, PH); bx = buf.getContext('2d'); bx.imageSmoothingEnabled = false; buildBG();
  H.AGENTS.forEach((d, i) => { Town.actors[d.id] = new Actor(d, i); });
  const pdef = { id: 'player', name: 'YOU', role: 'Visitor', skin: '#e8c4a0', hair: '#26180f', outfit: '#d8dde4', acc: 'player' }; player = new Actor(pdef, 99); player.x = 21 * T + 8; player.y = 24 * T + 11; player.dir = 'up'; player.pose = 'stand'; player.sit = false; player.speed = 60; Town.actors.player = player; Town.player = player;
  layout(); new ResizeObserver(layout).observe(cv.parentElement); bindEvents(); refreshHud();
  // input
  const typing = () => /INPUT|TEXTAREA|SELECT/.test(document.activeElement && document.activeElement.tagName);
  cv.tabIndex = 0; cv.addEventListener('focus', () => Town.focused = true); cv.addEventListener('blur', () => Town.focused = false); cv.addEventListener('pointerenter', () => { Town.focused = true; });
  addEventListener('keydown', e => { if (typing()) return; const k = e.key.toLowerCase(); if ('wasd'.includes(k) || k.startsWith('arrow')) { if (Town.focused) { keys[k] = 1; e.preventDefault(); } } if (k === 'e' && Town.focused && lastNear) lastNear.run(); });
  addEventListener('keyup', e => { delete keys[e.key.toLowerCase()]; }); addEventListener('blur', () => Object.keys(keys).forEach(k => delete keys[k]));
  cv.addEventListener('pointermove', e => { const r = cv.getBoundingClientRect(), [wx, wy] = s2w(e.clientX - r.left, e.clientY - r.top); hoverActor = null; Object.values(Town.actors).forEach(a => { if (Math.abs(a.x - wx) < 8 && wy > a.y - 26 && wy < a.y + 6) hoverActor = a; }); cv.style.cursor = hoverActor ? 'pointer' : 'crosshair'; if (drag) { view.px += e.clientX - drag.x; view.py += e.clientY - drag.y; drag = { x: e.clientX, y: e.clientY, m: 1 }; } });
  let drag = null; cv.addEventListener('pointerdown', e => { cv.focus(); drag = { x: e.clientX, y: e.clientY, m: 0 }; cv.setPointerCapture(e.pointerId); }); cv.addEventListener('pointerup', e => { if (drag && !drag.m) Town.select(hoverActor && hoverActor.id !== 'player' ? hoverActor.id : null); drag = null; });
  cv.addEventListener('wheel', e => { e.preventDefault(); const r = cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top, [wx, wy] = s2w(mx, my); view.zoom = H.clamp(view.zoom * Math.exp(-e.deltaY * .0015), 1, 4); const s = sc(); view.px = mx - (view.W - PW * s) / 2 - wx * s; view.py = my - (view.H - PH * s) / 2 - wy * s; if (view.zoom <= 1.001) { view.px = view.py = 0; } }, { passive: false });
  H.$('#btn-town-fit').onclick = () => { view.zoom = 1; view.px = view.py = 0; Town.follow = null; }; H.$('#tt-me').onclick = () => { Town.follow = Town.follow === 'player' ? null : 'player'; if (Town.follow) view.zoom = Math.max(view.zoom, 2.2); H.toast(Town.follow ? 'Camera follows you (WASD · E)' : 'Camera free', ''); };
  H.$('#tt-board').onclick = () => H.hub && H.hub.open('hub'); H.$('#tt-share').onclick = () => H.$('#sd-term').click(); H.$('#btn-chat-fab').onclick = () => { H.$('#cmd-input').focus(); };
  H.loop.add((dt, t) => {
    const now = performance.now(); Object.values(Town.actors).forEach(a => { if (a === player) { if (!a.cur && a.q.length === 0) movePlayer(a, dt); a.ft += dt; if (a.ft > .15) { a.ft = 0; a.frame = (a.frame + 1) & 3; } if (a.bubble && now > a.bubble.until) a.bubble = null; } else stepActor(a, dt, now); });
    if (Town.follow && Town.actors[Town.follow]) { const f = Town.actors[Town.follow], s = sc(); view.px += ((view.W / 2 - ((view.W - PW * s) / 2 + f.x * s)) - view.px) * .08; view.py += ((view.H / 2 - ((view.H - PH * s) / 2 + f.y * s)) - view.py) * .08; }
    render(dt, t);
    if (!Town._hud || now - Town._hud > 700) { Town._hud = now; refreshHud(); }
  }, { fps: 60, vis: () => H.$('#view-agents').classList.contains('on') });
};
})();
