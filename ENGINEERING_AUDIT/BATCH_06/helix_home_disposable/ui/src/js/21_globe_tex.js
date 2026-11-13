/* ---------- procedural Earth: day / night / cloud / overlay textures from embedded Natural Earth topology ---------- */
(function () {
'use strict';
const H = window.H;
const G = H.globe = H.globe || {};
const D2R = Math.PI / 180;
const mk = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };

function hash(x, y, s) { let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(s | 0, 1013904223); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
function vnoise(x, y, s, w) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), W = w || 1e9;
  const X0 = ((xi % W) + W) % W, X1 = (((xi + 1) % W) + W) % W;
  const a = hash(X0, yi, s), b = hash(X1, yi, s), c = hash(X0, yi + 1, s), d = hash(X1, yi + 1, s);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
function fbm(x, y, oct, s, w) { let a = .5, f = 1, sum = 0, n = 0; for (let i = 0; i < oct; i++) { sum += a * vnoise(x * f, y * f, s + i * 17, w ? w * f : 0); n += a; a *= .5; f *= 2; } return sum / n; }
G.fbm = fbm;

const X = (l, W) => (l + 180) / 360 * W, Y = (l, Hh) => (90 - l) / 180 * Hh;
function geoEach(g, fn) {
  if (!g) return; if (g.type === 'FeatureCollection') g.features.forEach(f => geoEach(f.geometry, fn)); else if (g.type === 'Feature') geoEach(g.geometry, fn);
  else if (g.type === 'GeometryCollection') g.geometries.forEach(x => geoEach(x, fn)); else fn(g);
}
function polyPath(ctx, geom, W, Hh) {
  geoEach(geom, g => {
    const ring = r => { for (let i = 0; i < r.length; i++) { const p = r[i]; i ? ctx.lineTo(X(p[0], W), Y(p[1], Hh)) : ctx.moveTo(X(p[0], W), Y(p[1], Hh)); } ctx.closePath(); };
    if (g.type === 'Polygon') g.coordinates.forEach(ring); else if (g.type === 'MultiPolygon') g.coordinates.forEach(p => p.forEach(ring));
  });
}
// stroke rings/lines while skipping seam/pole-edge segments (avoids horizontal streaks across the map)
function strokeGeo(ctx, geom, W, Hh) {
  const edge = (a, b) => (Math.abs(a[0]) > 179.99 && Math.abs(b[0]) > 179.99 && Math.sign(a[0]) === Math.sign(b[0])) || (a[1] < -89.9 && b[1] < -89.9) || Math.abs(a[0] - b[0]) > 180;
  const line = (r, closed) => {
    for (let i = 0; i < r.length; i++) {
      const p = r[i]; if (i === 0 || edge(r[i - 1], p)) ctx.moveTo(X(p[0], W), Y(p[1], Hh)); else ctx.lineTo(X(p[0], W), Y(p[1], Hh));
    }
  };
  geoEach(geom, g => {
    if (g.type === 'Polygon') g.coordinates.forEach(r => line(r)); else if (g.type === 'MultiPolygon') g.coordinates.forEach(p => p.forEach(r => line(r)));
    else if (g.type === 'LineString') line(g.coordinates); else if (g.type === 'MultiLineString') g.coordinates.forEach(r => line(r));
  });
}
G._polyPath = polyPath; G._strokeGeo = strokeGeo;

function noiseCanvas(w, h, scale, oct, seed, pal) {
  const c = mk(w, h), x = c.getContext('2d'), id = x.createImageData(w, h), d = id.data;
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const v = fbm(i / w * scale, j / h * scale * .5, oct, seed, scale), k = (j * w + i) * 4;
    if (pal) { const c2 = pal(v, j / h); d[k] = c2[0]; d[k + 1] = c2[1]; d[k + 2] = c2[2]; d[k + 3] = c2[3] === undefined ? 255 : c2[3]; } else { const g = v * 255; d[k] = d[k + 1] = d[k + 2] = g; d[k + 3] = 255; }
  }
  x.putImageData(id, 0, 0); return c;
}

G.prepGeo = function () {
  const W = window.__WORLD; G.world = W;
  G.land = topojson.feature(W, W.objects.land);
  G.borders = topojson.mesh(W, W.objects.countries, (a, b) => a !== b);
  G.countries = topojson.feature(W, W.objects.countries).features.map(f => {
    const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
    const bb = polys.map(p => { let a = 1e9, b = 1e9, c = -1e9, d = -1e9; p[0].forEach(q => { a = Math.min(a, q[0]); b = Math.min(b, q[1]); c = Math.max(c, q[0]); d = Math.max(d, q[1]); }); return [a, b, c, d]; });
    let bi = 0, ba = -1; bb.forEach((b, i) => { const ar = (b[2] - b[0]) * (b[3] - b[1]); if (ar > ba) { ba = ar; bi = i; } });
    const b = bb[bi]; return { name: f.properties.name, f, polys, bb, lat: (b[1] + b[3]) / 2, lon: (b[0] + b[2]) / 2 };
  });
  G.byName = {}; G.countries.forEach(c => G.byName[c.name.toLowerCase()] = c);
};
function inRing(r, x, y) { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const a = r[i], b = r[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
G.countryAt = (lat, lon) => {
  for (const c of G.countries) for (let i = 0; i < c.polys.length; i++) {
    const b = c.bb[i]; if (lon < b[0] || lon > b[2] || lat < b[1] || lat > b[3]) continue;
    const p = c.polys[i]; if (inRing(p[0], lon, lat)) { let hole = false; for (let k = 1; k < p.length; k++) if (inRing(p[k], lon, lat)) { hole = true; break; } if (!hole) return c; }
  } return null;
};

G.buildTextures = async function (progress) {
  const Wd = H.quality.tex || 4096, Hh = Wd / 2, tick = async (p, m) => { progress && progress(p, m); await new Promise(r => setTimeout(r, 0)); };
  // land mask (for lights placement)
  const MW = 2048, MH = 1024, mc = mk(MW, MH), mx = mc.getContext('2d'); mx.fillStyle = '#000'; mx.fillRect(0, 0, MW, MH); mx.fillStyle = '#fff'; mx.beginPath(); polyPath(mx, G.land, MW, MH); mx.fill('evenodd');
  const mdata = mx.getImageData(0, 0, MW, MH).data;
  G.isLand = (lat, lon) => { const i = Math.floor((90 - lat) / 180 * (MH - 1)), j = Math.floor((lon + 180) / 360 * (MW - 1)); return i >= 0 && i < MH && mdata[(i * MW + ((j + MW) % MW)) * 4] > 128; };
  await tick(.1, 'land mask');

  /* ---- DAY ---- */
  const day = mk(Wd, Hh), x = day.getContext('2d');
  const og = x.createLinearGradient(0, 0, 0, Hh); og.addColorStop(0, '#0a2744'); og.addColorStop(.5, '#0e4673'); og.addColorStop(1, '#0a2744'); x.fillStyle = og; x.fillRect(0, 0, Wd, Hh);
  const seaN = noiseCanvas(512, 256, 10, 5, 3, (v, y) => [10 + v * 40 | 0, 50 + v * 60 | 0, 90 + v * 70 | 0, 255]);
  x.globalAlpha = .38; x.globalCompositeOperation = 'soft-light'; x.drawImage(seaN, 0, 0, Wd, Hh); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
  await tick(.25, 'oceans');
  const lc = mk(Wd, Hh), lx = lc.getContext('2d'); lx.fillStyle = '#3b7064'; lx.beginPath(); polyPath(lx, G.land, Wd, Hh); lx.fill('evenodd');
  lx.globalCompositeOperation = 'source-atop';
  const landN = noiseCanvas(1024, 512, 14, 6, 11, (v, y) => { const hi = Math.pow(v, 1.6); const lat = Math.abs(y - .5) * 2; const desert = Math.max(0, 1 - Math.abs(lat - .27) * 7) * 0.8; return [38 + hi * 150 + desert * 60 | 0, 78 + hi * 120 + desert * 28 | 0, 66 + hi * 70 - desert * 14 | 0, 255]; });
  lx.globalAlpha = .88; lx.drawImage(landN, 0, 0, Wd, Hh); lx.globalAlpha = 1;
  const ice = lx.createLinearGradient(0, 0, 0, Hh); ice.addColorStop(0, 'rgba(225,240,250,.95)'); ice.addColorStop(.1, 'rgba(225,240,250,0)'); ice.addColorStop(.9, 'rgba(225,240,250,0)'); ice.addColorStop(1, 'rgba(225,240,250,.95)'); lx.fillStyle = ice; lx.fillRect(0, 0, Wd, Hh);
  lx.globalCompositeOperation = 'source-over'; x.drawImage(lc, 0, 0);
  await tick(.45, 'terrain');
  x.lineJoin = 'round'; x.lineCap = 'round';
  x.strokeStyle = 'rgba(90,220,255,.16)'; x.lineWidth = Wd / 1024 * 6; x.beginPath(); strokeGeo(x, G.land, Wd, Hh); x.stroke();
  x.strokeStyle = 'rgba(170,245,255,.8)'; x.lineWidth = Wd / 2048 * 1.15; x.beginPath(); strokeGeo(x, G.land, Wd, Hh); x.stroke();
  x.strokeStyle = 'rgba(190,240,255,.30)'; x.lineWidth = Wd / 4096 * .9; x.beginPath(); strokeGeo(x, G.borders, Wd, Hh); x.stroke();
  x.strokeStyle = 'rgba(80,200,255,.07)'; x.lineWidth = Wd / 4096; x.beginPath();
  for (let la = -75; la <= 75; la += 15) { x.moveTo(0, Y(la, Hh)); x.lineTo(Wd, Y(la, Hh)); } for (let lo = -180; lo <= 180; lo += 15) { x.moveTo(X(lo, Wd), 0); x.lineTo(X(lo, Wd), Hh); } x.stroke();
  G.dayCanvas = day; await tick(.6, 'day map');

  /* ---- NIGHT (dark map + city lights) ---- */
  const night = mk(Wd, Hh), n = night.getContext('2d'); n.fillStyle = '#020912'; n.fillRect(0, 0, Wd, Hh);
  n.fillStyle = '#05151f'; n.beginPath(); polyPath(n, G.land, Wd, Hh); n.fill('evenodd');
  n.globalAlpha = .55; n.globalCompositeOperation = 'lighter'; n.drawImage(noiseCanvas(512, 256, 12, 5, 7, (v) => [4 + v * 14 | 0, 14 + v * 30 | 0, 22 + v * 34 | 0, 255]), 0, 0, Wd, Hh); n.globalAlpha = 1;
  n.globalCompositeOperation = 'source-over'; n.lineJoin = 'round'; n.strokeStyle = 'rgba(46,230,255,.34)'; n.lineWidth = Wd / 2048 * 1.0; n.beginPath(); strokeGeo(n, G.land, Wd, Hh); n.stroke();
  n.strokeStyle = 'rgba(46,230,255,.10)'; n.lineWidth = Wd / 4096 * .8; n.beginPath(); strokeGeo(n, G.borders, Wd, Hh); n.stroke();
  n.globalCompositeOperation = 'lighter';
  const px = Wd / 4096, rnd = Math.random;
  const gauss = () => (rnd() + rnd() + rnd() + rnd() - 2) * 1.2;
  for (const c of H.CITIES) {
    const gx = X(c.lon, Wd), gy = Y(c.lat, Hh), gr = (c.w * 1.6 + 5) * px * 1.6;
    const g = n.createRadialGradient(gx, gy, 0, gx, gy, gr); g.addColorStop(0, `rgba(255,190,110,${.05 + c.w * .022})`); g.addColorStop(1, 'rgba(255,170,90,0)'); n.fillStyle = g; n.fillRect(gx - gr, gy - gr, gr * 2, gr * 2);
    const cnt = Math.round(c.w * c.w * 2.2 + 8), sg = .18 + c.w * .075;
    for (let i = 0; i < cnt; i++) {
      const la = c.lat + gauss() * sg, lo = c.lon + gauss() * sg / Math.max(.3, Math.cos(c.lat * D2R)); if (!G.isLand(la, lo)) continue;
      const a = .25 + rnd() * .65, rr = (.5 + rnd() * 1.1) * px * 1.5, warm = rnd(); n.fillStyle = `rgba(255,${190 + warm * 55 | 0},${110 + warm * 110 | 0},${a})`; n.beginPath(); n.arc(X(lo, Wd), Y(la, Hh), rr, 0, 6.283); n.fill();
    }
  }
  for (const r of H.LIGHT_REGIONS) for (let i = 0; i < r[4]; i++) {
    const la = r[0] + rnd() * (r[1] - r[0]), lo = r[2] + rnd() * (r[3] - r[2]); if (!G.isLand(la, lo)) continue;
    n.fillStyle = `rgba(255,${200 + rnd() * 40 | 0},${120 + rnd() * 90 | 0},${.12 + rnd() * .45})`; n.fillRect(X(lo, Wd), Y(la, Hh), px * (1 + rnd() * .9), px * (1 + rnd() * .9));
  }
  G.nightCanvas = night; await tick(.8, 'city lights');

  /* ---- CLOUDS ---- */
  G.cloudCanvas = noiseCanvas(1024, 512, 7, 6, 21, (v, y) => { const a = Math.max(0, Math.min(1, (v - .5) * 3.2)); return [255, 255, 255, a * 255 | 0]; });
  /* ---- OVERLAY (alerts / selection) ---- */
  G.ovCanvas = mk(2048, 1024); G.redrawOverlay(); await tick(1, 'done');
};

// overlay: red alert countries + cyan selected country (equirect 2048x1024)
G.redrawOverlay = function () {
  const c = G.ovCanvas; if (!c) return; const x = c.getContext('2d'), W = c.width, Hh = c.height; x.clearRect(0, 0, W, Hh);
  const draw = (names, fill, stroke, lw) => {
    names.forEach(nm => {
      const co = G.byName[String(nm).toLowerCase()] || G.byName[({ 'usa': 'united states of america', 'uk': 'united kingdom', 'uae': 'united arab emirates', 'russia': 'russia', 'czechia': 'czechia' })[String(nm).toLowerCase()]]; if (!co) return;
      x.beginPath(); polyPath(x, co.f, W, Hh); x.fillStyle = fill; x.fill('evenodd'); x.lineJoin = 'round'; x.strokeStyle = stroke; x.lineWidth = lw; x.beginPath(); strokeGeo(x, co.f, W, Hh); x.stroke();
    });
  };
  draw(G.alertCountries ? G.alertCountries() : [], 'rgba(255,40,60,.40)', 'rgba(255,110,120,.95)', 2.2);
  if (G.selectedCountry) draw([G.selectedCountry], 'rgba(46,230,255,.16)', 'rgba(46,230,255,.95)', 2.4);
  if (G.earthTex) G.earthTex.ov.needsUpdate = true; G.map2d && (G.map2d.dirty = true);
};
})();
