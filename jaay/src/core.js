'use strict';
/* JAAY — "1 000 F POUR COMMENCER GRAND."
   Core motion/design system.
   Design tokens follow the LottieFiles Motion Design Skill:
   - Personality: PREMIUM (signature easing, 0% overshoot, long decelerations)
   - Signature easing: EXPO_OUT  (cubic-bezier(0.16, 1, 0.3, 1))
   - Duration palette: quick 350ms / standard 500ms / slow 800ms / cinematic 1200ms
   - Three motion layers on every scene: primary / secondary / ambient
*/
const { createCanvas, GlobalFonts, Image } = require('@napi-rs/canvas');
const path = require('path');

const W = 1080, H = 1920, FPS = 60, DUR = 45;

/* ---------------------------------------------------------------- fonts */
const F = path.join(__dirname, '..', 'fonts');
const reg = (f, name) => GlobalFonts.registerFromPath(path.join(F, f), name);
reg('Inter-300.ttf', 'InterLight');
reg('Inter-400.ttf', 'InterReg');
reg('Inter-500.ttf', 'InterMed');
reg('Inter-600.ttf', 'InterSemi');
reg('Inter-700.ttf', 'InterBold');
reg('Inter-800.ttf', 'InterBlack');
reg('Inter-900.ttf', 'InterHeavy');
reg('SG-400.ttf', 'SGReg');
reg('SG-500.ttf', 'SGMed');
reg('SG-700.ttf', 'SGBold');
reg('InstrumentSerif-Regular.ttf', 'Serif');
reg('InstrumentSerif-Italic.ttf', 'SerifIt');

/* -------------------------------------------------------------- palette */
const C = {
  void:      '#030605',
  ink:       '#050b08',
  deep:      '#07120c',
  forest:    '#0a2018',
  emerald:   '#0f9f63',
  emeraldHi: '#19c47c',
  jade:      '#4fe0a3',
  lime:      '#c8f45f',
  limeHi:    '#e2ff9e',
  gold:      '#e6c384',
  goldHi:    '#f6e2b8',
  white:     '#f3f7f2',
  smoke:     '#c3d0c6',
  muted:     '#8398 8b'.replace(' ', ''),
  slate:     '#5c6d63',
  wa:        '#25D366',
  waDark:    '#075E54',
};

/* -------------------------------------------------------------- easing */
const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, t) => clamp((t - a) / (b - a));
const smoothstep = (t) => t * t * (3 - 2 * t);
const expoOut = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));
const expoIn = (t) => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10));
const cubicOut = (t) => 1 - Math.pow(1 - t, 3);
const cubicIn = (t) => t * t * t;
const quintOut = (t) => 1 - Math.pow(1 - t, 5);
const inOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const inOutQuint = (t) => (t < 0.5 ? 16 * t * t * t * t * t : 1 - Math.pow(-2 * t + 2, 5) / 2);
const sineInOut = (t) => -(Math.cos(Math.PI * t) - 1) / 2;
const backOut = (t, s = 1.2) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2);
// damped spring, 0 -> 1
const spring = (t, freq = 10, damp = 7) =>
  t <= 0 ? 0 : t >= 1 ? 1 : 1 - Math.exp(-damp * t) * Math.cos(freq * t);
/* ease applied over a normalised window with a curve fn */
const ez = (t, a, b, fn = expoOut) => fn(inv(a, b, t));

/* --------------------------------------------------------------- colour */
const rgba = (hex, a = 1) => {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};
function mix(hexA, hexB, t) {
  const p = (h) => {
    const n = parseInt(h.replace('#', ''), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  };
  const A = p(hexA), B = p(hexB);
  return `rgb(${Math.round(lerp(A[0], B[0], t))},${Math.round(lerp(A[1], B[1], t))},${Math.round(lerp(A[2], B[2], t))})`;
}

/* ---------------------------------------------------------------- noise */
const rnd = (n) => {
  // deterministic hash-based random
  let x = Math.sin(n * 127.1 + 311.7) * 43758.5453123;
  return x - Math.floor(x);
};

/* --------------------------------------------------------------- assets */
const assets = {};
function img(name) {
  if (!assets[name]) {
    const im = new Image();
    im.src = require('fs').readFileSync(path.join(__dirname, '..', 'assets', name));
    assets[name] = im;
  }
  return assets[name];
}

/* decode every asset up-front: napi-rs needs an explicit decode before drawImage */
async function preload() {
  const fs = require('fs');
  const dir = path.join(__dirname, '..', 'assets');
  const files = fs.readdirSync(dir).filter((f) => /\.(jpe?g|png)$/i.test(f));
  await Promise.all(files.map(async (f) => {
    const im = new Image();
    im.src = fs.readFileSync(path.join(dir, f));
    await im.decode();
    assets[f] = im;
  }));
  return Object.keys(assets).length;
}

/* --------------------------------------------------------- draw helpers */
function roundRect(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.lineTo(x + w - rr, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + rr);
  ctx.lineTo(x + w, y + h - rr);
  ctx.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
  ctx.lineTo(x + rr, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - rr);
  ctx.lineTo(x, y + rr);
  ctx.quadraticCurveTo(x, y, x + rr, y);
  ctx.closePath();
}

/* soft radial light sprite, additive */
const glowCache = new Map();
function glowSprite(color, softness = 0.5) {
  const key = color + softness;
  if (glowCache.has(key)) return glowCache.get(key);
  const S = 256;
  const cv = createCanvas(S, S);
  const c = cv.getContext('2d');
  const g = c.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
  g.addColorStop(0, rgba(color, 1));
  g.addColorStop(softness * 0.5, rgba(color, 0.42));
  g.addColorStop(softness, rgba(color, 0.11));
  g.addColorStop(1, rgba(color, 0));
  c.fillStyle = g;
  c.fillRect(0, 0, S, S);
  glowCache.set(key, cv);
  return cv;
}
function glow(ctx, x, y, r, color, alpha = 1, softness = 0.5) {
  const spr = glowSprite(color, softness);
  const prev = ctx.globalCompositeOperation;
  ctx.globalCompositeOperation = 'lighter';
  ctx.globalAlpha *= alpha;
  ctx.drawImage(spr, x - r, y - r, r * 2, r * 2);
  ctx.globalAlpha /= alpha;
  ctx.globalCompositeOperation = prev;
}

/* horizontal light streak */
function streak(ctx, x, y, w, h, color, alpha = 1) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, w / 2);
  g.addColorStop(0, rgba(color, alpha));
  g.addColorStop(0.35, rgba(color, alpha * 0.35));
  g.addColorStop(1, rgba(color, 0));
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(1, h / w);
  ctx.translate(-x, -y);
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.arc(x, y, w / 2, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

/* cheap defocus: render fn into a downscaled buffer, draw back up */
const blurPool = [];
function blurred(ctx, w, h, k, drawFn, alpha = 1) {
  const bw = Math.max(2, Math.round(w / k)), bh = Math.max(2, Math.round(h / k));
  let cv = blurPool.find((p) => !p.busy && p.cv.width === bw && p.cv.height === bh);
  if (!cv) {
    cv = { cv: createCanvas(bw, bh), busy: false };
    blurPool.push(cv);
  }
  cv.busy = true;
  const c2 = cv.cv.getContext('2d');
  c2.clearRect(0, 0, bw, bh);
  c2.save();
  c2.scale(1 / k, 1 / k);
  drawFn(c2);
  c2.restore();
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(cv.cv, 0, 0, bw, bh, 0, 0, bw * k, bh * k);
  ctx.restore();
  cv.busy = false;
}

/* text with optional tracking + alpha + align.
   napi-rs ignores letterSpacing when aligning text, so we align by hand. */
function text(ctx, str, x, y, o = {}) {
  const {
    size = 48, font = 'InterMed', color = C.white, align = 'center',
    baseline = 'alphabetic', tracking = 0, alpha = 1, scale = 1, rot = 0, shadow = 0,
  } = o;
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.font = `${size}px ${font}`;
  ctx.letterSpacing = `${tracking}px`;
  ctx.textAlign = 'left';
  ctx.textBaseline = baseline;
  ctx.fillStyle = color;
  if (scale !== 1 || rot !== 0) {
    ctx.translate(x, y);
    if (rot) ctx.rotate(rot);
    ctx.scale(scale, scale);
    ctx.translate(-x, -y);
  }
  if (shadow) {
    ctx.shadowColor = 'rgba(0,0,0,0.55)';
    ctx.shadowBlur = shadow;
    ctx.shadowOffsetY = shadow * 0.25;
  }
  let dx = 0;
  if (align !== 'left' && tracking !== 0) {
    // advance width includes one extra tracking step
    const adv = ctx.measureText(str).width;
    if (align === 'center') dx = -adv / 2 + tracking / 2;
    else if (align === 'right') dx = -adv + tracking;
  } else if (align === 'center') {
    ctx.textAlign = 'center';
  } else if (align === 'right') {
    ctx.textAlign = 'right';
  }
  ctx.fillText(str, x + dx, y);
  ctx.restore();
}
function measure(ctx, str, size, font, tracking = 0) {
  ctx.save();
  ctx.font = `${size}px ${font}`;
  ctx.letterSpacing = `${tracking}px`;
  const w = ctx.measureText(str).width;
  ctx.restore();
  return w;
}

/* masked line reveal: slides up from behind a mask, per line */
function maskedLine(ctx, str, x, y, o = {}) {
  const { size = 80, font = 'InterBlack', color = C.white, progress = 1, align = 'center',
    tracking = 0, alpha = 1, lineFactor = 1.22, dir = 1 } = o;
  const p = clamp(progress);
  if (p <= 0) return;
  ctx.save();
  const pad = size * 0.55;
  ctx.beginPath();
  ctx.rect(x - 1400, y - size * 0.82, 2800, size * lineFactor + size * 0.12);
  ctx.clip();
  ctx.globalAlpha *= alpha;
  const dy = (1 - expoOut(p)) * size * lineFactor * dir;
  text(ctx, str, x, y + dy, { size, font, color, align, tracking, baseline: 'alphabetic' });
  ctx.restore();
}

/* image, cover-fit into rect, optional rounding + duotone */
function cover(ctx, im, x, y, w, h, o = {}) {
  const { r = 0, alpha = 1, dim = 0, tint = null, tintAlpha = 0, focusY = 0.5, focusX = 0.5, zoom = 1 } = o;
  const ir = im.width / im.height, br = w / h;
  let sw, sh, sx, sy;
  if (ir > br) { sh = im.height / zoom; sw = sh * br; sx = (im.width - sw) * focusX; sy = (im.height - sh) * focusY; }
  else { sw = im.width / zoom; sh = sw / br; sx = (im.width - sw) * focusX; sy = (im.height - sh) * focusY; }
  ctx.save();
  if (r) { roundRect(ctx, x, y, w, h, r); ctx.clip(); }
  ctx.globalAlpha *= alpha;
  ctx.drawImage(im, sx, sy, sw, sh, x, y, w, h);
  if (tint) {
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = rgba(tint, tintAlpha || 1);
    ctx.fillRect(x, y, w, h);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalCompositeOperation = 'overlay';
    ctx.fillStyle = rgba(tint, tintAlpha * 0.6);
    ctx.fillRect(x, y, w, h);
    ctx.globalCompositeOperation = 'source-over';
  }
  if (dim) { ctx.fillStyle = `rgba(0,0,0,${dim})`; ctx.fillRect(x, y, w, h); }
  ctx.restore();
}

/* film grain + vignette */
let grainCanvas = null;
function makeGrain() {
  const S = 300;
  grainCanvas = createCanvas(S, S);
  const c = grainCanvas.getContext('2d');
  const d = c.createImageData(S, S);
  for (let i = 0; i < S * S; i++) {
    const v = 120 + Math.floor(rnd(i * 1.37) * 135);
    d.data[i * 4] = v; d.data[i * 4 + 1] = v; d.data[i * 4 + 2] = v;
    d.data[i * 4 + 3] = 255;
  }
  c.putImageData(d, 0, 0);
}
function grain(ctx, t, alpha = 0.045) {
  if (!grainCanvas) makeGrain();
  const pat = ctx.createPattern(grainCanvas, 'repeat');
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.globalCompositeOperation = 'overlay';
  const ox = Math.floor(rnd(Math.floor(t * FPS)) * 300);
  const oy = Math.floor(rnd(Math.floor(t * FPS) + 7) * 300);
  ctx.translate(-ox, -oy);
  ctx.fillStyle = pat;
  ctx.fillRect(0, 0, W + 300, H + 300);
  ctx.restore();
}
let vigCanvas = null;
function vignette(ctx, strength = 0.55) {
  if (!vigCanvas) {
    vigCanvas = createCanvas(W, H);
    const c = vigCanvas.getContext('2d');
    const g = c.createRadialGradient(W * 0.5, H * 0.48, H * 0.18, W * 0.5, H * 0.5, H * 0.78);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(0.62, 'rgba(0,0,0,0.28)');
    g.addColorStop(1, 'rgba(0,0,0,0.86)');
    c.fillStyle = g;
    c.fillRect(0, 0, W, H);
  }
  ctx.save();
  ctx.globalAlpha = strength;
  ctx.drawImage(vigCanvas, 0, 0);
  ctx.restore();
}

/* base plate: deep emerald-black with a slow drifting ambient light */
function plate(ctx, t, o = {}) {
  const { tint = C.emerald, intensity = 1, drift = 0 } = o;
  ctx.fillStyle = C.void;
  ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(
    W * 0.5 + Math.sin(t * 0.35 + drift) * 120,
    H * 0.42 + Math.cos(t * 0.28 + drift) * 90, 0,
    W * 0.5, H * 0.5, H * 0.85);
  g.addColorStop(0, rgba(tint, 0.13 * intensity));
  g.addColorStop(0.42, rgba(C.forest, 0.5 * intensity));
  g.addColorStop(1, rgba('#020403', 1));
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

/* small ambient dust motes — ambient motion layer */
function dust(ctx, t, n = 26, alpha = 0.5, seed = 1) {
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const s = rnd(i * 3.1 + seed);
    const base = rnd(i * 7.7 + seed * 2);
    const x = ((base * W + t * (6 + s * 16)) % (W + 200)) - 100;
    const y = (rnd(i * 5.3 + seed) * H - t * (10 + s * 24) + H * 3) % H;
    const a = (0.06 + s * 0.16) * alpha * (0.6 + 0.4 * Math.sin(t * 1.3 + i));
    ctx.fillStyle = rgba(C.jade, a);
    ctx.beginPath();
    ctx.arc(x, y, 1.2 + s * 2.6, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

/* caption / eyebrow */
function eyebrow(ctx, str, x, y, o = {}) {
  text(ctx, str, x, y, {
    size: 26, font: 'InterSemi', color: C.lime, tracking: 8, align: o.align || 'center',
    alpha: o.alpha === undefined ? 1 : o.alpha, baseline: 'middle',
  });
}

/* fine divider that draws itself */
function hairline(ctx, x, y, w, p, color = C.lime, thickness = 2, alpha = 0.9) {
  if (p <= 0) return;
  ctx.save();
  ctx.globalAlpha *= alpha;
  const g = ctx.createLinearGradient(x - w / 2, 0, x + w / 2, 0);
  g.addColorStop(0, rgba(color, 0));
  g.addColorStop(0.15, rgba(color, 0.85));
  g.addColorStop(0.85, rgba(color, 0.85));
  g.addColorStop(1, rgba(color, 0));
  ctx.fillStyle = g;
  const ww = w * clamp(p);
  ctx.fillRect(x - ww / 2, y, ww, thickness);
  ctx.restore();
}

module.exports = {
  W, H, FPS, DUR, C, mix, rgba, rnd,
  clamp, lerp, inv, smoothstep, expoOut, expoIn, cubicOut, cubicIn, quintOut,
  inOutCubic, inOutQuint, sineInOut, backOut, spring, ez,
  text, measure, maskedLine, cover, roundRect, glow, streak, blurred, grain,
  vignette, plate, dust, eyebrow, hairline, img, preload, createCanvas,
};
