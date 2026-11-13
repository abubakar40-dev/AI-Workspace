/* =====================================================================================
   VOICE CORE ORB — Three.js GPU particle orb (state machine + audio reactive)
   API (swap-friendly, so the old Jarvis orb can be dropped in behind the same calls):
     H.orb.setState('idle|listening|thinking|speaking|error|offline')
     H.orb.setLevel(0..1)            external amplitude (mic / TTS)  |  H.orb.setBands(low,mid,high)
     H.orb.attachAnalyser(AnalyserNode|null)   live mic spectrum
     H.orb.pulse(hexColor)           shock-wave burst (task done, model failover, ...)
   ===================================================================================== */
(function () {
'use strict';
const H = window.H;

const NOISE = `
vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
float snoise(vec3 v){
  const vec2 C=vec2(1.0/6.0,1.0/3.0);const vec4 D=vec4(0.0,0.5,1.0,2.0);
  vec3 i=floor(v+dot(v,C.yyy));vec3 x0=v-i+dot(i,C.xxx);
  vec3 g=step(x0.yzx,x0.xyz);vec3 l=1.0-g;vec3 i1=min(g.xyz,l.zxy);vec3 i2=max(g.xyz,l.zxy);
  vec3 x1=x0-i1+C.xxx;vec3 x2=x0-i2+C.yyy;vec3 x3=x0-D.yyy;
  i=mod289(i);
  vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
  float n_=0.142857142857;vec3 ns=n_*D.wyz-D.xzx;
  vec4 j=p-49.0*floor(p*ns.z*ns.z);vec4 x_=floor(j*ns.z);vec4 y_=floor(j-7.0*x_);
  vec4 x=x_*ns.x+ns.yyyy;vec4 y=y_*ns.x+ns.yyyy;vec4 h=1.0-abs(x)-abs(y);
  vec4 b0=vec4(x.xy,y.xy);vec4 b1=vec4(x.zw,y.zw);
  vec4 s0=floor(b0)*2.0+1.0;vec4 s1=floor(b1)*2.0+1.0;vec4 sh=-step(h,vec4(0.0));
  vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
  vec3 p0=vec3(a0.xy,h.x);vec3 p1=vec3(a0.zw,h.y);vec3 p2=vec3(a1.xy,h.z);vec3 p3=vec3(a1.zw,h.w);
  vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
  p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
  vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0);m=m*m;
  return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
}`;

const VERT = NOISE + `
uniform float uTime,uAmp,uSpeed,uTwist,uSize,uLevel,uPulse,uPulseT,uThink,uPR,uSwirl,uMouseOn,uJit;
uniform vec3 uBands,uMouse;
attribute float aSeed;attribute float aSize;
varying float vA;varying float vH;
void main(){
  vec3 d=normalize(position);
  float t=uTime*uSpeed;
  float ang=uTwist*d.y+t*0.35*uSwirl;
  float c=cos(ang),s=sin(ang);
  vec3 dd=vec3(d.x*c-d.z*s,d.y,d.x*s+d.z*c);
  float n=snoise(dd*1.5+vec3(0.0,t*0.5,0.0));
  float n2=snoise(dd*4.2-vec3(t*0.8,0.0,t*0.3));
  float shell=0.90+aSeed*0.17;
  float r=(1.0+n*uAmp+n2*uAmp*0.38)*shell;
  float ay=abs(d.y);
  float bw=uBands.x*(1.0-ay)+uBands.y*(1.0-abs(ay-0.5)*2.0)+uBands.z*ay;
  r+=bw*0.42*(0.55+0.45*n)+uLevel*0.10;
  r*=1.0+uThink*0.10*sin(t*3.2+aSeed*6.2831);
  r+=uJit*(fract(sin(aSeed*91.7+uTime*30.0)*437.5)-0.5)*0.4;
  float w=uPulseT*2.8-1.4;
  r+=uPulse*0.30*smoothstep(0.42,0.0,abs(d.y-w));
  vec3 p=dd*r*1.18;
  vec4 wp=modelMatrix*vec4(p,1.0);
  float md=distance(wp.xyz,uMouse);
  p+=normalize(p)*uMouseOn*0.42*smoothstep(0.75,0.0,md);
  vec4 mv=modelViewMatrix*vec4(p,1.0);
  gl_Position=projectionMatrix*mv;
  gl_PointSize=aSize*uSize*uPR*(5.2/-mv.z);
  vH=n*0.5+0.5;
  vA=(0.42+0.58*smoothstep(-0.9,1.1,(modelMatrix*vec4(p,1.0)).z))*(0.75+0.25*aSeed);
}`;
const FRAG = `
uniform vec3 uColor,uColor2;uniform float uOpacity;
varying float vA;varying float vH;
void main(){
  float d=length(gl_PointCoord-0.5);if(d>0.5)discard;
  float a=smoothstep(0.5,0.05,d);
  vec3 col=mix(uColor,uColor2,vH)*(0.65+vH*0.9);
  gl_FragColor=vec4(col,a*vA*uOpacity);
}`;
const RING_VERT = `
uniform float uTime,uPR,uSpeed;attribute float aSeed;varying float vA;
void main(){
  float a=position.x+uTime*uSpeed*(0.35+aSeed*0.5);float r=position.y;
  vec3 p=vec3(cos(a)*r,sin(a*1.0)*r*0.0+ (aSeed-0.5)*0.05,sin(a)*r);
  float tilt=0.42;p=vec3(p.x,p.y*cos(tilt)-p.z*sin(tilt),p.y*sin(tilt)+p.z*cos(tilt));
  vec4 mv=modelViewMatrix*vec4(p,1.0);gl_Position=projectionMatrix*mv;
  gl_PointSize=(1.4+aSeed*1.8)*uPR*(5.0/-mv.z);vA=0.4+0.6*aSeed;
}`;
const RING_FRAG = `uniform vec3 uColor;uniform float uOpacity;varying float vA;
void main(){float d=length(gl_PointCoord-0.5);if(d>0.5)discard;gl_FragColor=vec4(uColor,smoothstep(0.5,0.0,d)*vA*uOpacity);}`;
const GLOW_FRAG = `uniform vec3 uColor;uniform float uI;varying vec2 vUv;
void main(){float d=length(vUv-0.5)*2.0;float a=pow(max(0.0,1.0-d),2.2)*uI;gl_FragColor=vec4(uColor*a,a);}`;

const STATES = {
  idle:      { c1: '#2ee6ff', c2: '#7fa8ff', amp: .10, speed: .35, twist: .55, swirl: .35, size: 1.0, ring: 0,   think: 0, op: .95, jit: 0,   glow: .16, label: 'IDLE' },
  listening: { c1: '#46f0a0', c2: '#2ee6ff', amp: .14, speed: .65, twist: 1.0, swirl: .55, size: 1.05, ring: .25, think: 0, op: 1, jit: 0,   glow: .26, label: 'LISTENING' },
  thinking:  { c1: '#9b7bff', c2: '#2ee6ff', amp: .20, speed: 1.7, twist: 3.2, swirl: 1.5, size: 1.1, ring: .85, think: 1, op: 1, jit: 0,   glow: .30, label: 'THINKING' },
  speaking:  { c1: '#2ee6ff', c2: '#ffffff', amp: .13, speed: .8,  twist: 1.2, swirl: .7,  size: 1.1, ring: .45, think: 0, op: 1, jit: 0,   glow: .34, label: 'SPEAKING' },
  error:     { c1: '#ff4d5e', c2: '#ffb020', amp: .30, speed: 2.4, twist: 2.0, swirl: 1.2, size: 1.1, ring: .2,  think: 0, op: 1, jit: .5,  glow: .32, label: 'ERROR' },
  offline:   { c1: '#4c5f6a', c2: '#6c7f8a', amp: .03, speed: .08, twist: .2,  swirl: .1,  size: .8,  ring: 0,   think: 0, op: .55, jit: 0,  glow: .04, label: 'OFFLINE' }
};

class Orb {
  constructor(canvas) {
    this.canvas = canvas; this.state = 'idle'; this.ext = 0; this.lvl = 0; this.bands = [0, 0, 0]; this.analyser = null; this.fft = null;
    this.pulseV = 0; this.pulseT = 1; this.rot = { x: 0, y: 0, vx: 0, vy: 0.0015 }; this.drag = null; this.mouse = new THREE.Vector3(9, 9, 9); this.mouseOn = 0; this.mouseT = 0;
    this.cur = Object.assign({}, STATES.idle, { c1: new THREE.Color(STATES.idle.c1), c2: new THREE.Color(STATES.idle.c2) });
    let gl = null;
    try {
      this.r = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true, powerPreference: 'low-power' });
    } catch (e) { console.warn('orb: WebGL unavailable', e); this.dead = true; return; }
    this.r.setClearColor(0x000000, 0);
    this.scene = new THREE.Scene(); this.cam = new THREE.PerspectiveCamera(38, 1, 0.1, 50); this.cam.position.set(0, 0, 5.2);
    this.group = new THREE.Group(); this.scene.add(this.group);
    this.build();
    this.resize();
    new ResizeObserver(() => this.resize()).observe(canvas.parentElement);
    H.bus.on('quality', () => { this.build(); this.resize(); });
    this.bindPointer();
  }
  build() {
    if (this.pts) { this.group.remove(this.pts); this.pts.geometry.dispose(); this.group.remove(this.ring); this.ring.geometry.dispose(); }
    if (this.glow) { this.scene.remove(this.glow); }
    const N = Math.round(9000 * H.quality.particles), pos = new Float32Array(N * 3), seed = new Float32Array(N), size = new Float32Array(N);
    const ga = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2, rr = Math.sqrt(1 - y * y), th = ga * i;
      pos[i * 3] = Math.cos(th) * rr; pos[i * 3 + 1] = y; pos[i * 3 + 2] = Math.sin(th) * rr;
      seed[i] = Math.random(); size[i] = 0.7 + Math.random() * 1.5;
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aSeed', new THREE.BufferAttribute(seed, 1)); g.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
    this.u = {
      uTime: { value: 0 }, uAmp: { value: .1 }, uSpeed: { value: .35 }, uTwist: { value: .5 }, uSize: { value: 1 }, uLevel: { value: 0 }, uPulse: { value: 0 }, uPulseT: { value: 1 }, uThink: { value: 0 },
      uPR: { value: H.quality.dpr }, uSwirl: { value: .3 }, uMouseOn: { value: 0 }, uJit: { value: 0 }, uBands: { value: new THREE.Vector3() }, uMouse: { value: this.mouse },
      uColor: { value: new THREE.Color('#2ee6ff') }, uColor2: { value: new THREE.Color('#7fa8ff') }, uOpacity: { value: 1 }
    };
    const m = new THREE.ShaderMaterial({ uniforms: this.u, vertexShader: VERT, fragmentShader: FRAG, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
    this.pts = new THREE.Points(g, m); this.group.add(this.pts);
    // accretion ring
    const RN = Math.round(1800 * H.quality.particles), rp = new Float32Array(RN * 3), rs = new Float32Array(RN);
    for (let i = 0; i < RN; i++) { rp[i * 3] = Math.random() * 6.283; rp[i * 3 + 1] = 1.55 + Math.pow(Math.random(), 2) * 0.55; rp[i * 3 + 2] = 0; rs[i] = Math.random(); }
    const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.BufferAttribute(rp, 3)); rg.setAttribute('aSeed', new THREE.BufferAttribute(rs, 1));
    this.ru = { uTime: this.u.uTime, uPR: this.u.uPR, uSpeed: { value: 1 }, uColor: { value: new THREE.Color('#9b7bff') }, uOpacity: { value: 0 } };
    this.ring = new THREE.Points(rg, new THREE.ShaderMaterial({ uniforms: this.ru, vertexShader: RING_VERT, fragmentShader: RING_FRAG, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    this.group.add(this.ring);
    // soft core glow
    this.gu = { uColor: { value: new THREE.Color('#2ee6ff') }, uI: { value: .15 } };
    this.glow = new THREE.Mesh(new THREE.PlaneGeometry(6.2, 6.2), new THREE.ShaderMaterial({ uniforms: this.gu, vertexShader: 'varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}', fragmentShader: GLOW_FRAG, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
    this.glow.position.z = -1.2; this.scene.add(this.glow);
  }
  resize() {
    if (this.dead) return; const p = this.canvas.parentElement, w = p.clientWidth, h = p.clientHeight; if (!w || !h) return;
    this.r.setPixelRatio(H.quality.dpr); this.r.setSize(w, h, false); this.cam.aspect = w / h; this.u.uPR.value = H.quality.dpr;
    // keep the orb ~ 62% of canvas height regardless of aspect
    this.cam.fov = 38; this.cam.position.z = 5.2 * (h > w * 0.62 ? (h / (w * 0.62)) : 1); this.cam.updateProjectionMatrix(); this.group.position.y = 0.18; this.glow.position.y = 0.18;
    this.w = w; this.h = h;
  }
  bindPointer() {
    const c = this.canvas; let moved = 0;
    const toWorld = e => {
      const r = c.getBoundingClientRect(), nx = (e.clientX - r.left) / r.width * 2 - 1, ny = -((e.clientY - r.top) / r.height * 2 - 1);
      const v = new THREE.Vector3(nx, ny, 0.5).unproject(this.cam), dir = v.sub(this.cam.position).normalize();
      const t = -this.cam.position.z / dir.z; return this.cam.position.clone().add(dir.multiplyScalar(t));
    };
    c.addEventListener('pointermove', e => {
      const w = toWorld(e); this.mouse.set(w.x, w.y - 0.18 * 0, 0.9); this.mouseOn = 1; this.mouseT = performance.now();
      if (this.drag) { const dx = e.clientX - this.drag.x, dy = e.clientY - this.drag.y; moved += Math.abs(dx) + Math.abs(dy); this.rot.vy = dx * 0.006; this.rot.vx = dy * 0.004; this.rot.y += dx * 0.006; this.rot.x = H.clamp(this.rot.x + dy * 0.004, -1, 1); this.drag = { x: e.clientX, y: e.clientY }; }
    });
    c.addEventListener('pointerdown', e => { this.drag = { x: e.clientX, y: e.clientY }; moved = 0; c.setPointerCapture(e.pointerId); });
    c.addEventListener('pointerup', e => { this.drag = null; if (moved < 6) H.bus.emit('orb.click'); });
    c.addEventListener('pointerleave', () => { this.mouseOn = 0; });
  }
  setState(s) { if (!STATES[s]) return; if (s !== this.state) { this.state = s; if (s === 'error' || s === 'speaking') this.pulse(STATES[s].c1); } H.bus.emit('orb.state', s); }
  setLevel(v) { this.ext = H.clamp(v, 0, 1); }
  setBands(l, m, h) { this.bands = [l, m, h]; }
  attachAnalyser(a) { this.analyser = a; this.fft = a ? new Uint8Array(a.frequencyBinCount) : null; }
  pulse(hex) { this.pulseV = 1; this.pulseT = 0; this.pulseCol = new THREE.Color(hex || '#2ee6ff'); }
  frame(dt, t) {
    if (this.dead) return;
    const S = STATES[this.state], c = this.cur, k = 1 - Math.exp(-dt * 4);
    ['amp', 'speed', 'twist', 'swirl', 'size', 'ring', 'think', 'op', 'jit', 'glow'].forEach(p => c[p] = H.lerp(c[p], S[p], k));
    c.c1.lerp(new THREE.Color(S.c1), k); c.c2.lerp(new THREE.Color(S.c2), k);
    // audio level
    let lvl = this.ext, b = this.bands;
    if (this.analyser && this.state === 'listening') {
      this.analyser.getByteFrequencyData(this.fft); const n = this.fft.length, avg = (a, z) => { let s = 0; for (let i = a; i < z; i++) s += this.fft[i]; return s / Math.max(1, z - a) / 255; };
      b = [avg(1, n * .08 | 0), avg(n * .08 | 0, n * .3 | 0), avg(n * .3 | 0, n * .7 | 0)].map(v => Math.min(1, v * 1.8)); lvl = Math.max(lvl, (b[0] + b[1] + b[2]) / 2.2);
    } else if (this.state === 'speaking') {
      const e = 0.5 + 0.5 * Math.sin(t * 9) * Math.sin(t * 2.3 + 1), n = Math.random() * 0.25; lvl = Math.max(lvl, 0.18 + 0.5 * e + n);
      b = [lvl * .9, lvl * (0.6 + 0.4 * Math.sin(t * 5)), lvl * .5 * Math.abs(Math.sin(t * 11))];
    } else if (this.state === 'thinking') { lvl = 0.12 + 0.08 * Math.sin(t * 3); b = [0.1, 0.15 + 0.1 * Math.sin(t * 4), 0.1]; }
    this.lvl = H.lerp(this.lvl, lvl, 1 - Math.exp(-dt * 14)); this.bands = this.bands.map((v, i) => H.lerp(v, b[i] || 0, 1 - Math.exp(-dt * 12)));
    this.pulseT = Math.min(1, this.pulseT + dt * 0.9); this.pulseV = Math.max(0, 1 - this.pulseT * 1.1);
    if (performance.now() - this.mouseT > 600) this.mouseOn = Math.max(0, this.mouseOn - dt * 2);
    const u = this.u; u.uTime.value = t; u.uAmp.value = c.amp; u.uSpeed.value = c.speed; u.uTwist.value = c.twist; u.uSwirl.value = c.swirl; u.uSize.value = c.size * (1 + this.lvl * .25) * (1 / Math.sqrt(H.quality.particles)) * 1.15;
    u.uLevel.value = this.lvl; u.uThink.value = c.think; u.uJit.value = c.jit; u.uPulse.value = this.pulseV; u.uPulseT.value = this.pulseT; u.uMouseOn.value = this.mouseOn * 0.8;
    u.uBands.value.set(this.bands[0], this.bands[1], this.bands[2]); u.uColor.value.copy(c.c1); u.uColor2.value.copy(c.c2); u.uOpacity.value = c.op;
    if (this.pulseV > 0.02 && this.pulseCol) u.uColor2.value.lerp(this.pulseCol, this.pulseV * .7);
    this.ru.uColor.value.copy(c.c1).lerp(c.c2, .4); this.ru.uOpacity.value = c.ring * (0.55 + this.lvl * .6); this.ru.uSpeed.value = 0.6 + c.speed;
    this.gu.uColor.value.copy(c.c1); this.gu.uI.value = c.glow + this.lvl * .25 + this.pulseV * .22;
    // rotation with inertia
    if (!this.drag) { this.rot.vy = H.lerp(this.rot.vy, 0.0016 + c.speed * 0.0016, 0.03); this.rot.vx *= 0.94; this.rot.y += this.rot.vy; this.rot.x = H.lerp(this.rot.x, Math.sin(t * 0.3) * 0.12, 0.01) + this.rot.vx * 0.2; }
    this.pts.rotation.set(this.rot.x, this.rot.y, 0); this.ring.rotation.y = -this.rot.y * 0.4;
    this.r.render(this.scene, this.cam);
  }
}
H.Orb = Orb; H.ORB_STATES = STATES;
})();
