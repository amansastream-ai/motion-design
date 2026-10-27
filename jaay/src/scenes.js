'use strict';
/* JAAY — scene direction.
   Beats are driven by the French VO. Every scene carries three motion layers:
   primary (hero move) / secondary (UI, shadows, satellites) / ambient (dust, light drift). */
const K = require('./core');
const B = require('./brand');
const {
  W, H, C, text, roundRect, rgba, clamp, lerp, inv, ez, expoOut, expoIn, cubicOut,
  inOutCubic, inOutQuint, sineInOut, glow, cover, img, blur, grain, vignette, plate,
  dust, hairline, eyebrow, measure, blurred, streak, FPS, rnd,
} = K;
const { mark, wordmark, phone, phoneBody, phoneGlass, phoneFrameOnly, homeScreen, productScreen, dashboardScreen, productCard, PRODUCTS, waIcon, waBubble } = B;

const TL = {
  s1: [0.0, 4.6],
  s2: [4.6, 10.2],
  s3: [10.2, 16.2],
  s4: [16.2, 23.9],
  s5: [23.9, 30.4],
  s6: [30.4, 36.2],
  s7: [36.2, 45.0],
};
const NB = '\u2009'; // thin space — French thousands separator
const fmt = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, NB);

/* ============================================================ helpers ==== */

function ring(ctx, x, y, r, a, w = 2, color = C.jade) {
  if (a <= 0 || r <= 0) return;
  ctx.save();
  ctx.globalAlpha *= a;
  ctx.strokeStyle = color;
  ctx.lineWidth = w;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

/* cinematic top/bottom gradients for legibility over photography */
function scrims(ctx, topA = 0.75, botA = 0.9, midA = 0.0) {
  let g = ctx.createLinearGradient(0, 0, 0, H * 0.42);
  g.addColorStop(0, `rgba(3,6,5,${topA})`);
  g.addColorStop(1, 'rgba(3,6,5,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H * 0.42);
  g = ctx.createLinearGradient(0, H * 0.5, 0, H);
  g.addColorStop(0, 'rgba(3,6,5,0)');
  g.addColorStop(0.55, `rgba(3,6,5,${botA * 0.7})`);
  g.addColorStop(1, `rgba(3,6,5,${botA})`);
  ctx.fillStyle = g;
  ctx.fillRect(0, H * 0.5, W, H * 0.5);
  if (midA) { ctx.fillStyle = `rgba(3,10,7,${midA})`; ctx.fillRect(0, 0, W, H); }
}

/* 3D coin: gold 1 000 F piece under macro orbit */
function coin(ctx, x, y, r, ang, o = {}) {
  const { alpha = 1, sweep = 0, emboss = true, detail = true } = o;
  const f = Math.max(0.055, Math.abs(Math.cos(ang)));
  const dir = Math.cos(ang) >= 0 ? 1 : -1;
  const depth = r * 0.085 * (0.35 + 0.65 * Math.sqrt(f));
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.translate(x, y);

  /* ---- cylinder edge (the rim we see when the coin turns away) */
  const ex = -dir * depth;
  const edgeG = ctx.createLinearGradient(0, -r, 0, r);
  edgeG.addColorStop(0, '#8a6420');
  edgeG.addColorStop(0.18, '#d9b56b');
  edgeG.addColorStop(0.42, '#f0d8a2');
  edgeG.addColorStop(0.62, '#b08a3e');
  edgeG.addColorStop(0.86, '#6f4d14');
  edgeG.addColorStop(1, '#4a3210');
  ctx.beginPath();
  ctx.ellipse(ex, 0, r * f, r, 0, 0, Math.PI * 2);
  ctx.fillStyle = edgeG;
  ctx.fill();
  // reeded ticks on the rim
  if (detail && f > 0.12) {
    ctx.save();
    ctx.globalAlpha *= 0.32;
    ctx.strokeStyle = '#4a3210';
    ctx.lineWidth = Math.max(1, r * 0.012);
    for (let i = 0; i < 46; i++) {
      const a2 = (i / 46) * Math.PI * 2;
      const px = ex + Math.cos(a2) * r * f * 0.985;
      const py = Math.sin(a2) * r * 0.985;
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(px + Math.sin(a2) * r * 0.03, py - Math.cos(a2) * r * 0.012);
      ctx.stroke();
    }
    ctx.restore();
  }

  /* ---- face */
  const fg = ctx.createRadialGradient(-r * f * 0.34, -r * 0.42, r * 0.06, 0, 0, r * 1.12);
  fg.addColorStop(0, '#fff3d4');
  fg.addColorStop(0.22, '#f3d99f');
  fg.addColorStop(0.48, '#dcb673');
  fg.addColorStop(0.72, '#b98f47');
  fg.addColorStop(0.9, '#8d6828');
  fg.addColorStop(1, '#6d4c16');
  ctx.beginPath();
  ctx.ellipse(0, 0, r * f, r, 0, 0, Math.PI * 2);
  ctx.fillStyle = fg;
  ctx.fill();

  // conic metal interference
  if (f > 0.14) {
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(0, 0, r * f, r, 0, 0, Math.PI * 2);
    ctx.clip();
    const cg = ctx.createConicGradient(ang * 0.9 - 1.2, 0, 0);
    cg.addColorStop(0, 'rgba(255,246,220,0.28)');
    cg.addColorStop(0.18, 'rgba(120,86,30,0.22)');
    cg.addColorStop(0.36, 'rgba(255,240,205,0.20)');
    cg.addColorStop(0.58, 'rgba(96,66,18,0.26)');
    cg.addColorStop(0.78, 'rgba(255,248,225,0.24)');
    cg.addColorStop(1, 'rgba(255,246,220,0.28)');
    ctx.fillStyle = cg;
    ctx.fillRect(-r, -r, r * 2, r * 2);
    // darker bottom for grounding
    const gsh = ctx.createLinearGradient(0, r * 0.15, 0, r);
    gsh.addColorStop(0, 'rgba(60,40,8,0)');
    gsh.addColorStop(1, 'rgba(60,40,8,0.42)');
    ctx.fillStyle = gsh;
    ctx.fillRect(-r, 0, r * 2, r);
    // top-left key light
    const key = ctx.createRadialGradient(-r * f * 0.36, -r * 0.5, 0, -r * f * 0.36, -r * 0.5, r * 1.15);
    key.addColorStop(0, 'rgba(255,252,238,0.30)');
    key.addColorStop(0.5, 'rgba(255,250,230,0.06)');
    key.addColorStop(1, 'rgba(255,250,230,0)');
    ctx.fillStyle = key;
    ctx.fillRect(-r, -r, r * 2, r * 2);
    ctx.restore();
  }

  // inner struck ring
  ctx.beginPath();
  ctx.ellipse(0, 0, r * f * 0.865, r * 0.865, 0, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(94,64,16,0.5)';
  ctx.lineWidth = Math.max(1.1, r * 0.014);
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(0, 0, r * f * 0.895, r * 0.895, 0, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(255,246,215,0.32)';
  ctx.lineWidth = Math.max(0.8, r * 0.008);
  ctx.stroke();

  /* ---- engraving: dark cut + light lower lip (emboss) */
  if (emboss && f > 0.13) {
    ctx.save();
    ctx.scale(f, 1);
    const tSize = r * 0.40;
    const cut = 'rgba(48,30,4,1)';
    const lip = 'rgba(255,250,232,0.55)';
    // main figure
    text(ctx, fmt(1000), 0, -r * 0.035, { size: tSize, font: 'SGBold', color: cut, baseline: 'middle', tracking: -r * 0.026 });
    text(ctx, fmt(1000), 0, -r * 0.035 + r * 0.009, { size: tSize, font: 'SGBold', color: lip, baseline: 'middle', tracking: -r * 0.026 });
    // currency
    text(ctx, 'F CFA', 0, r * 0.325, { size: r * 0.135, font: 'InterBold', color: cut, baseline: 'middle', tracking: r * 0.028 });
    text(ctx, 'F CFA', 0, r * 0.325 + r * 0.008, { size: r * 0.135, font: 'InterBold', color: lip, baseline: 'middle', tracking: r * 0.028 });
    // marque above
    if (detail) {
      ctx.beginPath();
      ctx.arc(0, -r * 0.44, r * 0.05, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,244,214,0.30)';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(0, -r * 0.452, r * 0.05, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(74,50,12,0.8)';
      ctx.fill();
    }
    ctx.restore();
  }

  /* ---- specular: rim highlight + travelling sweep */
  if (f > 0.1) {
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(0, 0, r * f, r, 0, 0, Math.PI * 2);
    ctx.clip();
    ctx.globalCompositeOperation = 'lighter';
    // rim light top
    ctx.lineWidth = r * 0.028;
    ctx.strokeStyle = 'rgba(255,250,228,0.55)';
    ctx.beginPath();
    ctx.ellipse(0, 0, r * f * 0.975, r * 0.975, 0, Math.PI * 1.08, Math.PI * 1.92);
    ctx.stroke();
    // rim light bottom-left (cool bounce)
    ctx.lineWidth = r * 0.035;
    ctx.strokeStyle = 'rgba(255,238,196,0.22)';
    ctx.beginPath();
    ctx.ellipse(0, 0, r * f * 0.968, r * 0.968, 0, Math.PI * 0.6, Math.PI * 1.35);
    ctx.stroke();
    // sweep
    const p = clamp(sweep);
    if (p > 0.001 && p < 0.999) {
      const gx = -r * f * 1.4 + p * r * f * 2.8;
      const g = ctx.createLinearGradient(gx - r * 0.35, -r, gx + r * 0.35, r);
      g.addColorStop(0, 'rgba(255,255,255,0)');
      g.addColorStop(0.45, 'rgba(255,253,244,0.42)');
      g.addColorStop(0.55, 'rgba(255,253,244,0.42)');
      g.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = g;
      ctx.fillRect(-r, -r, r * 2, r * 2);
    }
    ctx.restore();
  }

  // edge occlusion where face meets rim
  ctx.beginPath();
  ctx.ellipse(ex * 0.5, 0, r * f, r, 0, Math.PI * 0.5, Math.PI * 1.5);
  ctx.strokeStyle = 'rgba(0,0,0,0.16)';
  ctx.lineWidth = Math.max(1.2, r * 0.02);
  ctx.stroke();
  ctx.restore();
}

/* particle burst helper */
function burst(ctx, x, y, t, dur, n, o = {}) {
  const { color = C.gold, spread = 620, size = 3, alpha = 1, seed = 3 } = o;
  const p = clamp(t / dur);
  if (p <= 0 || p >= 1) return;
  const e = expoOut(p);
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const a = rnd(i * 1.7 + seed) * Math.PI * 2;
    const d = (0.35 + rnd(i * 4.3 + seed) * 0.65) * spread * e;
    const x2 = x + Math.cos(a) * d;
    const y2 = y + Math.sin(a) * d * 0.8 - p * 40;
    const al = (1 - p) * (0.35 + rnd(i * 9.1) * 0.65) * alpha;
    ctx.fillStyle = rgba(color, al);
    ctx.beginPath();
    ctx.arc(x2, y2, size * (0.4 + rnd(i * 2.9) * 1.3) * (1 - p * 0.55), 0, Math.PI * 2);
    ctx.fill();
    if (rnd(i * 5.5) > 0.7) {
      ctx.strokeStyle = rgba(color, al * 0.5);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - Math.cos(a) * d * 0.12, y2 - Math.sin(a) * d * 0.1); ctx.stroke();
    }
  }
  ctx.restore();
}

/* ============================================================= SCENE 1 ==== */
/* 0.0–4.6  The impossible hook: particle → coin → kinetic type */
function scene1(ctx, t) {
  ctx.fillStyle = C.void;
  ctx.fillRect(0, 0, W, H);
  const cx = W / 2, cy = H * 0.445;

  // ambient bloom behind
  const amb = 0.10 + 0.06 * Math.sin(t * 1.4) + (t > 1.5 && t < 2.1 ? 0.25 : 0);
  glow(ctx, cx, cy, 620, C.emerald, amb * 0.5, 0.62);
  glow(ctx, cx, cy, 300, C.gold, 0.05 + (t > 0.4 && t < 1.7 ? 0.10 : 0), 0.55);

  /* ---- act 1: the particle (0 – 0.55) */
  const ignite = ez(t, 0.02, 0.5, sineInOut);
  const dotR = 2.2 + 3.4 * ignite;
  if (t < 0.75) {
    const a = ignite * (1 - inv(0.55, 0.75, t) * 0.6);
    glow(ctx, cx, cy, 40 + 120 * ignite, C.limeHi, a * 0.9, 0.35);
    ctx.fillStyle = rgba('#ffffff', a);
    ctx.beginPath(); ctx.arc(cx, cy, dotR, 0, Math.PI * 2); ctx.fill();
  }
  // expanding shock rings
  [0, 0.12].forEach((d, i) => {
    const p = inv(0.42 + d, 1.25 + d, t);
    if (p > 0 && p < 1) {
      ring(ctx, cx, cy, 20 + expoOut(p) * (420 + i * 220), (1 - p) * 0.5 * (1 - i * 0.4), 1.6 - i * 0.6, i ? C.jade : C.lime);
    }
  });

  /* ---- act 2: the coin (0.45 – 1.75) */
  const coinIn = ez(t, 0.42, 1.05, expoOut);
  const coinOut = 1 - ez(t, 1.45, 1.78, expoIn);
  const coinA = clamp(coinIn) * clamp(coinOut);
  if (coinA > 0.001) {
    const r = 214 * (0.55 + 0.45 * coinIn) * (1 + 0.10 * inOutCubic(clamp(inv(1.45, 1.78, t))));
    const ang = -0.30 + 1.22 * inOutCubic(clamp(inv(0.42, 1.95, t)));
    // converging light filaments (secondary layer)
    ctx.save();
    for (let i = 0; i < 26; i++) {
      const a = rnd(i * 2.3) * Math.PI * 2;
      const dist = (260 + rnd(i * 8.1) * 460) * (1 - coinIn);
      const al = (1 - coinIn) * 0.5;
      if (al <= 0) continue;
      const x1 = cx + Math.cos(a) * dist, y1 = cy + Math.sin(a) * dist * 0.9;
      ctx.strokeStyle = rgba(i % 3 ? C.jade : C.gold, al);
      ctx.lineWidth = 1.1;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(cx + Math.cos(a) * r * 0.4, cy + Math.sin(a) * r * 0.4); ctx.stroke();
    }
    ctx.restore();
    // contact glow
    glow(ctx, cx, cy, r * 2.2, C.gold, 0.16 * coinA, 0.6);
    // shadow pool
    const sg = ctx.createRadialGradient(cx, cy + r * 1.5, 4, cx, cy + r * 1.5, r * 1.7);
    sg.addColorStop(0, `rgba(0,0,0,${0.5 * coinA})`);
    sg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = sg;
    ctx.fillRect(cx - r * 2, cy, r * 4, r * 2.2);

    coin(ctx, cx, cy, r, ang, { alpha: coinA, sweep: clamp(inv(0.55, 1.6, t)), emboss: true });
  }

  // transformation flash + burst
  burst(ctx, cx, cy, t - 1.52, 0.9, 70, { color: '#f6e2b8', spread: 740, size: 2.6, alpha: 0.85, seed: 11 });

  const flash = ez(t, 1.48, 1.78, cubicOut) * (1 - ez(t, 1.78, 2.3, cubicOut));
  if (flash > 0.001) {
    // light the object, not the frame: keep the blacks intact
    glow(ctx, cx, cy, 520 * flash, C.limeHi, 0.22 * flash, 0.62);
    glow(ctx, cx, cy, 980 * flash, C.emerald, 0.10 * flash, 0.7);
  }

  /* ---- act 3: "1 000 F" (1.9 – 2.95) */
  const t1exit = ez(t, 2.66, 3.02, expoIn);
  if (t1exit < 1) {
    const p1 = ez(t, 1.92, 2.6, expoOut);
    const yBase = H * 0.505 - t1exit * 130;
    ctx.save();
    ctx.globalAlpha *= 1 - t1exit;
    // eyebrow
    const ep = ez(t, 2.12, 2.72, expoOut);
    ctx.save();
    ctx.globalAlpha *= ep;
    ctx.translate(0, (1 - ep) * 16);
    eyebrow(ctx, 'POUR COMMENCER GRAND', W / 2, yBase - 246, { alpha: 0.92 });
    ctx.restore();
    hairline(ctx, W / 2, yBase - 206, 340, ez(t, 2.16, 2.95, expoOut), C.lime, 1.4, 0.62);
    // number
    maskedLineY(ctx, fmt(1000), W / 2, yBase, { size: 206, font: 'SGBold', p: p1, tracking: -9, color: '#ffffff' });
    // currency
    const cp = ez(t, 2.3, 2.95, expoOut);
    ctx.save();
    ctx.globalAlpha *= cp;
    ctx.translate(0, (1 - cp) * 14);
    text(ctx, 'F CFA', W / 2, yBase + 74, { size: 42, font: 'InterMed', color: C.lime, tracking: 22 });
    ctx.restore();
    glow(ctx, W / 2, yBase - 60, 560, C.lime, 0.09, 0.62);
    ctx.restore();
  }

  /* ---- act 4: the question (2.95 – 4.6) */
  if (t > 2.94) {
    const out = ez(t, 4.26, 4.6, expoIn);
    ctx.save();
    ctx.globalAlpha *= 1 - out;
    // soft light bed behind the type (no object: keep the composition pure)
    glow(ctx, W / 2, H * 0.34, 640, C.gold, 0.05 * ez(t, 3.0, 3.9), 0.7);
    glow(ctx, W / 2, H * 0.5, 760, C.emerald, 0.17, 0.6);
    K.maskedLine(ctx, 'ET SI TOUT', W / 2, H * 0.455, { size: 100, font: 'InterBlack', progress: ez(t, 2.96, 3.5, expoOut), tracking: -4 });
    K.maskedLine(ctx, 'COMMENÇAIT', W / 2, H * 0.53, { size: 100, font: 'InterBlack', progress: ez(t, 3.14, 3.68, expoOut), tracking: -4 });
    ctx.save();
    ctx.globalAlpha *= ez(t, 3.36, 4.0, expoOut);
    text(ctx, 'ici', W / 2 - 96, H * 0.53 + 128, { size: 132, font: 'SerifIt', color: C.goldHi || '#f6e2b8', tracking: -1, align: 'center' });
    text(ctx, '?', W / 2 + 114, H * 0.53 + 128, { size: 110, font: 'InterBlack', color: C.lime, tracking: -2, align: 'center' });
    ctx.restore();
    ctx.save();
    ctx.globalAlpha *= ez(t, 3.9, 4.35, expoOut);
    hairline(ctx, W / 2, H * 0.53 + 186, 220, 1, C.lime, 1.4, 0.5);
    ctx.restore();
    ctx.restore();
  }

  dust(ctx, t, 30, 0.55, 2);
  vignette(ctx, 0.5);
  grain(ctx, t, 0.05);
}

/* masked reveal with y baseline (shared) */
function maskedLineY(ctx, str, x, y, o = {}) {
  const { size = 100, font = 'InterBlack', p = 1, tracking = 0, color = C.white, alpha = 1 } = o;
  if (p <= 0) return;
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, y - size * 0.86, W, size * 1.16);
  ctx.clip();
  text(ctx, str, x, y + (1 - expoOut(clamp(p))) * size * 1.1, { size, font, color, tracking, alpha });
  ctx.restore();
}

/* ============================================================= SCENE 2 ==== */
/* 4.6–10.2  The entrepreneur: Dakar atelier, phone in hand, UI comes alive */
function scene2(ctx, t, T) {
  const hero = img('hero_merchant.jpg');
  /* camera: slow push-in (primary) */
  const zoom = 1.015 + 0.085 * inOutCubic(clamp(t / 5.6));
  ctx.fillStyle = '#06100c';
  ctx.fillRect(0, 0, W, H);
  const ih = H * 1.10;
  const iw = ih * (hero.width / hero.height);
  ctx.save();
  ctx.translate(W / 2 + 18 - t * 5, H * 0.5);
  ctx.scale(zoom, zoom);
  ctx.translate(-W / 2, -H * 0.5);
  ctx.drawImage(hero, W / 2 - iw / 2, -ih * 0.055, iw, ih);
  ctx.restore();

  /* grade: warm key, emerald shadow, keep the subject readable */
  ctx.save();
  ctx.globalCompositeOperation = 'soft-light';
  ctx.fillStyle = 'rgba(24,140,96,0.30)';
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
  const topG = ctx.createLinearGradient(0, 0, 0, H * 0.40);
  topG.addColorStop(0, 'rgba(3,10,7,0.86)');
  topG.addColorStop(1, 'rgba(3,10,7,0)');
  ctx.fillStyle = topG;
  ctx.fillRect(0, 0, W, H * 0.40);
  const botG = ctx.createLinearGradient(0, H * 0.42, 0, H);
  botG.addColorStop(0, 'rgba(3,9,7,0)');
  botG.addColorStop(0.45, 'rgba(3,9,7,0.55)');
  botG.addColorStop(1, 'rgba(2,7,5,0.97)');
  ctx.fillStyle = botG;
  ctx.fillRect(0, H * 0.42, W, H * 0.58);
  // corner falloff
  const cg = ctx.createRadialGradient(W * 0.5, H * 0.42, H * 0.22, W * 0.5, H * 0.5, H * 0.76);
  cg.addColorStop(0, 'rgba(0,0,0,0)');
  cg.addColorStop(1, 'rgba(2,8,6,0.66)');
  ctx.fillStyle = cg;
  ctx.fillRect(0, 0, W, H);

  /* premium light sweep on entry */
  const sp = inv(0.05, 1.2, t);
  if (sp > 0 && sp < 1) {
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.translate(W * (0.1 + sp * 0.95), H * 0.16);
    ctx.rotate(-0.26);
    const g = ctx.createLinearGradient(-220, 0, 220, 0);
    g.addColorStop(0, 'rgba(255,248,214,0)');
    g.addColorStop(0.5, `rgba(255,248,214,${0.18 * Math.sin(sp * Math.PI)})`);
    g.addColorStop(1, 'rgba(255,248,214,0)');
    ctx.fillStyle = g;
    ctx.fillRect(-260, 0, 520, H * 1.2);
    ctx.restore();
  }

  /* kicker */
  const kp = ez(t, 0.35, 0.95, expoOut);
  ctx.save();
  ctx.globalAlpha *= kp;
  ctx.translate(0, (1 - kp) * 12);
  roundRect(ctx, 76, 176, 268, 44, 22);
  ctx.fillStyle = 'rgba(5,18,12,0.5)';
  ctx.fill();
  ctx.strokeStyle = rgba(C.lime, 0.26);
  ctx.lineWidth = 1.2;
  ctx.stroke();
  ctx.beginPath(); ctx.arc(100, 198, 4.4, 0, Math.PI * 2); ctx.fillStyle = C.lime; ctx.fill();
  text(ctx, 'DAKAR, SÉNÉGAL', 116, 199, { size: 20, font: 'InterSemi', color: '#e9f3ea', align: 'left', baseline: 'middle', tracking: 4.4 });
  ctx.restore();

  /* headline beats */
  const ph1 = ez(t, 0.55, 1.2, expoOut);
  const out1 = ez(t, 1.95, 2.35, expoIn);
  const ph2 = ez(t, 2.12, 2.8, expoOut);
  const fly = ez(t, 4.62, 5.66, inOutQuint);

  /* phone */
  const enter = ez(t, 1.4, 2.4, expoOut);
  const phoneW = 352;
  const px = lerp(W * 0.60, W / 2, fly) + (1 - enter) * 90;
  const py = lerp(H * 0.395, H * 0.5, fly) + (1 - enter) * 210;
  const pScale = (0.94 + 0.06 * enter) * (1 + fly * 4.1);
  const pAlpha = enter;
  if (pAlpha > 0.002) {
    const scroll = Math.min(140, Math.max(0, t - 2.0) * 34);
    phone(ctx, px, py, phoneW * pScale, {
      alpha: pAlpha,
      tilt: -0.05 + 0.05 * enter - fly * 0.05,
      hideShadow: fly > 0.25,
      screenFn: (c2, sw, sh) => homeScreen(c2, sw, sh, { t: t - 1.45, scroll }),
    });
    glow(ctx, px, py + phoneW * 0.62 * pScale, phoneW * 1.2 * pScale, C.emerald, 0.14 * pAlpha, 0.62);
  }

  /* WhatsApp exchange, top-left (secondary layer) */
  if (t > 2.25 && fly < 0.4) {
    const wx = 74, wy = H * 0.245;
    ctx.save();
    ctx.globalAlpha *= 1 - fly * 2.5;
    waBubble(ctx, 'Bonjour, la robe wax est dispo ?', wx, wy, { mine: false, p: ez(t, 2.25, 2.8, expoOut), maxW: 250 });
    waBubble(ctx, 'Oui 😊 1 000 F. Livraison demain.', wx, wy + 84, { mine: true, p: ez(t, 3.0, 3.55, expoOut), maxW: 232 });
    const tp = ez(t, 3.6, 3.95, expoOut) * (1 - ez(t, 4.5, 4.85, cubicOut));
    if (tp > 0.01) {
      ctx.save();
      ctx.globalAlpha *= tp;
      roundRect(ctx, wx, wy + 158, 76, 34, 17);
      ctx.fillStyle = 'rgba(255,255,255,0.08)';
      ctx.fill();
      for (let i = 0; i < 3; i++) {
        const b = 0.4 + 0.6 * Math.max(0, Math.sin(t * 6 - i * 0.9));
        ctx.fillStyle = rgba(C.jade, 0.3 + b * 0.55);
        ctx.beginPath(); ctx.arc(wx + 22 + i * 16, wy + 175 - b * 2, 3.6, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
    }
    ctx.restore();
  }

  /* headline typography — lower third, left aligned */
  const hx = 84;
  ctx.save();
  ctx.globalAlpha *= 1 - out1;
  if (ph1 > 0.001) {
    K.maskedLine(ctx, 'TU AS DES', hx, H * 0.775, { size: 92, font: 'InterBlack', progress: ph1, tracking: -3.4, align: 'left' });
    K.maskedLine(ctx, 'PRODUITS ?', hx, H * 0.775 + 100, { size: 92, font: 'InterBlack', progress: ez(t, 0.7, 1.35, expoOut), tracking: -3.4, align: 'left', color: C.lime });
  }
  ctx.restore();
  ctx.save();
  ctx.globalAlpha *= ph2 * (1 - fly * 1.5);
  if (ph2 > 0.001) {
    K.maskedLine(ctx, 'CRÉE TA', hx, H * 0.775, { size: 92, font: 'InterBlack', progress: ph2, tracking: -3.4, align: 'left' });
    K.maskedLine(ctx, 'BOUTIQUE.', hx, H * 0.775 + 100, { size: 92, font: 'InterBlack', progress: ez(t, 2.3, 3.0, expoOut), tracking: -3.4, align: 'left', color: C.lime });
  }
  ctx.restore();

  /* product card satellite, left (secondary) */
  if (t > 3.95) {
    const cp = ez(t, 3.95, 4.6, expoOut);
    ctx.save();
    ctx.globalAlpha *= cp * (1 - fly * 2);
    ctx.translate(0, (1 - cp) * 46);
    ctx.save();
    ctx.translate(150, H * 0.60);
    ctx.rotate(-0.045 + Math.sin((t - 3.95) * 1.1) * 0.014);
    productCard(ctx, PRODUCTS[0], -108, -140, 216, 280, { progress: 1, r: 20 });
    glow(ctx, 0, 0, 200, C.emerald, 0.14 * cp, 0.62);
    ctx.restore();
    ctx.restore();
  }

  /* push-in bloom into the next scene */
  const bloom = ez(t, 5.34, 5.66, expoIn);
  if (bloom > 0) glow(ctx, W / 2, H / 2, 1000, C.jade, 0.30 * bloom, 0.55);
  dust(ctx, t, 16, 0.32, 5);
  grain(ctx, t, 0.05);
  vignette(ctx, 0.42);
}

/* ============================================================= SCENE 3 ==== */
/* 10.2–16.2  JAAY reveal: the real marketplace UI pulls back into the device,
   the device then becomes a product hero and the brand lockup lands. */
function scene3(ctx, t) {
  plate(ctx, t, { tint: C.emerald, intensity: 1.0, drift: 1.2 });
  glow(ctx, W * 0.5, H * 0.34, 980, C.emerald, 0.26, 0.66);
  glow(ctx, W * 0.8, H * 0.14, 640, C.jade, 0.09, 0.65);

  /* ---- camera: full-bleed UI → device → device as hero */
  const pull = ez(t, 0.06, 1.5, inOutQuint);        // screen fills → device
  const push = ez(t, 3.0, 4.3, inOutQuint);        // device → hero product shot
  const phoneW = lerp(lerp(700, 508, pull), 372, push);
  const cx = W / 2;
  const cy = lerp(lerp(H * 0.5, H * 0.515, pull), H * 0.315, push);
  const radius = phoneW * 0.115;
  const frameA = ez(t, 1.05, 1.95, expoOut);

  /* ---- device body behind the screen */
  if (frameA > 0.004) {
    phoneBody(ctx, cx, cy, phoneW, {
      alpha: frameA, shadow: 1 - push * 0.75, glowAmt: 0.75, sheen: 0,
    });
  }

  /* ---- the real marketplace UI */
  ctx.save();
  roundRect(ctx, cx - phoneW / 2, cy - phoneW * (844 / 390) / 2, phoneW, phoneW * (844 / 390), radius);
  ctx.clip();
  ctx.translate(cx - phoneW / 2, cy - phoneW * (844 / 390) / 2);
  ctx.scale(phoneW / 390, phoneW / 390);
  homeScreen(ctx, 390, 844, { t: 0.25 + t, scroll: Math.min(90, Math.max(0, t - 0.8) * 22) });
  // screen recedes slightly so type can live above it
  const dimP = ez(t, 2.2, 3.4, expoOut) * 0.20;
  if (dimP > 0.002) {
    ctx.fillStyle = `rgba(4,11,8,${dimP * 0.42})`;
    ctx.fillRect(0, 0, 390, 844);
  }
  ctx.restore();

  /* ---- glass + frame edge on top of the screen */
  ctx.save();
  roundRect(ctx, cx - phoneW / 2, cy - phoneW * (844 / 390) / 2, phoneW, phoneW * (844 / 390), radius);
  ctx.clip();
  ctx.globalCompositeOperation = 'overlay';
  ctx.fillStyle = 'rgba(150,255,205,0.10)';
  ctx.fillRect(cx - phoneW / 2, cy - phoneW * (844 / 390) / 2, phoneW, phoneW * (844 / 390));
  ctx.restore();
  phoneGlass(ctx, cx, cy, phoneW, { sheen: 1 });
  if (frameA > 0.004) {
    phoneBody(ctx, cx, cy, phoneW, { alpha: frameA, shadow: 0, glowAmt: 0, ringOnly: true });
  }

  /* ---- light sweep across the device glass */
  const glassSweep = inv(1.5, 2.9, t);
  if (glassSweep > 0 && glassSweep < 1) {
    ctx.save();
    roundRect(ctx, cx - phoneW / 2, cy - phoneW * (844 / 390) / 2, phoneW, phoneW * (844 / 390), radius);
    ctx.clip();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha *= Math.sin(glassSweep * Math.PI) * 0.5;
    ctx.translate(cx + (-1 + glassSweep * 2.4) * phoneW * 0.9, cy);
    ctx.rotate(-0.32);
    const g = ctx.createLinearGradient(-120, 0, 120, 0);
    g.addColorStop(0, 'rgba(255,255,255,0)');
    g.addColorStop(0.5, 'rgba(255,255,255,0.35)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(-140, -H, 280, H * 2);
    ctx.restore();
  }

  /* ---- brand block (lands with the device as hero) */
  const bIn = ez(t, 3.82, 4.62, expoOut);
  const mSize = 92;
  const mY = 1118;
  if (bIn > 0.002) {
    ctx.save();
    ctx.globalAlpha *= bIn;
    ctx.translate(0, (1 - bIn) * 26);
    glow(ctx, cx, mY, 190, C.emerald, 0.24, 0.62);
    mark(ctx, cx - mSize / 2, mY - mSize / 2, mSize, { alpha: 1, sheen: clamp(inv(4.5, 5.6, t)), morph: bIn });
    ctx.restore();
  }
  const wIn = ez(t, 3.98, 4.75, expoOut);
  if (wIn > 0.002) {
    ctx.save();
    ctx.globalAlpha *= wIn;
    const wy = 1330 + (1 - wIn) * 20;
    wordmark(ctx, cx, wy, 152, { tracking: Math.round(-0.055 * 152 + (1 - wIn) * 24) });
    glow(ctx, cx, wy - 46, 330, C.lime, 0.085 * wIn, 0.62);
    ctx.restore();
  }
  const tagIn = ez(t, 4.3, 5.0, expoOut);
  if (tagIn > 0.002) {
    ctx.save();
    ctx.globalAlpha *= tagIn;
    ctx.translate(0, (1 - tagIn) * 18);
    text(ctx, 'TA BOUTIQUE EN LIGNE', cx, 1404, { size: 28, font: 'InterMed', color: '#dfeade', tracking: 10 });
    ctx.restore();
  }
  hairline(ctx, cx, 1440, 400, ez(t, 4.45, 5.25, expoOut), C.lime, 1.4, 0.62);

  /* price */
  const priceIn = ez(t, 4.62, 5.4, expoOut);
  if (priceIn > 0.002) {
    ctx.save();
    ctx.globalAlpha *= priceIn;
    ctx.translate(0, (1 - priceIn) * 26);
    text(ctx, 'DÈS', cx, 1468, { size: 26, font: 'InterSemi', color: C.jade, tracking: 13 });
    ctx.save();
    ctx.translate(cx, 1616);
    const ng = ctx.createLinearGradient(-230, -70, 230, 50);
    ng.addColorStop(0, '#ffffff');
    ng.addColorStop(0.5, '#f2ffe0');
    ng.addColorStop(1, '#c8f45f');
    text(ctx, fmt(1000), 0, 0, { size: 152, font: 'SGBold', color: ng, tracking: -7 });
    const sw = inv(5.0, 5.95, t);
    if (sw > 0 && sw < 1) {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha *= 0.45 * Math.sin(sw * Math.PI);
      const g2 = ctx.createLinearGradient(-260 + sw * 520, -110, -150 + sw * 520, 70);
      g2.addColorStop(0, 'rgba(255,255,255,0)');
      g2.addColorStop(0.5, 'rgba(255,255,255,0.9)');
      g2.addColorStop(1, 'rgba(255,255,255,0)');
      text(ctx, fmt(1000), 0, 0, { size: 152, font: 'SGBold', color: g2, tracking: -7 });
      ctx.restore();
    }
    ctx.restore();
    text(ctx, 'F CFA', cx, 1704, { size: 34, font: 'InterBold', color: C.lime, tracking: 16 });
    glow(ctx, cx, 1596, 430, C.lime, 0.07 * priceIn, 0.64);
    ctx.restore();
  }

  dust(ctx, t, 22, 0.4, 9);
  vignette(ctx, 0.5);
  grain(ctx, t, 0.045);
}

/* ============================================================= SCENE 4 ==== */
/* 16.2–23.9  The business model, crystal clear */
function scene4(ctx, t) {
  plate(ctx, t, { tint: C.emerald, intensity: 0.85, drift: 2.4 });
  const cx = W / 2;

  /* beat 1 — the sale (0 – 1.9) */
  const sellP = ez(t, 0.05, 0.85, expoOut);
  const sellOut = ez(t, 1.55, 2.0, expoIn);
  if (sellOut < 1) {
    ctx.save();
    ctx.globalAlpha *= 1 - sellOut;
    // receipt card
    const cardW = 700, cardH = 300;
    const cy = H * 0.40 - (1 - sellP) * 40;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.translate(0, -sellOut * 60);
    roundRect(ctx, -cardW / 2, 0, cardW, cardH, 26);
    ctx.fillStyle = 'rgba(9,22,16,0.92)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(200,244,95,0.16)';
    ctx.lineWidth = 1.4;
    ctx.stroke();
    // product row
    ctx.save();
    roundRect(ctx, -cardW / 2 + 26, 26, 108, 108, 16);
    ctx.clip();
    cover(ctx, img(PRODUCTS[0].img), -cardW / 2 + 26, 26, 108, 108);
    ctx.restore();
    text(ctx, 'Robe wax Africaine', -cardW / 2 + 154, 58, { size: 26, font: 'InterSemi', color: '#eef5ef', align: 'left' });
    text(ctx, 'Teranga Style · Dakar', -cardW / 2 + 154, 86, { size: 17, font: 'InterReg', color: '#8fa39a', align: 'left' });
    // status pill
    const stP = ez(t, 0.6, 1.15, expoOut);
    ctx.save();
    ctx.globalAlpha *= stP;
    roundRect(ctx, cardW / 2 - 234, 36, 208, 40, 20);
    ctx.fillStyle = 'rgba(37,211,102,0.14)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(37,211,102,0.4)';
    ctx.lineWidth = 1;
    ctx.stroke();
    waIcon(ctx, cardW / 2 - 212, 56, 22, C.wa);
    text(ctx, 'Vente confirmée', cardW / 2 - 190, 57, { size: 18, font: 'InterSemi', color: '#9ff0c0', align: 'left', baseline: 'middle' });
    ctx.restore();
    // divider
    ctx.fillStyle = 'rgba(255,255,255,0.09)';
    ctx.fillRect(-cardW / 2 + 26, 158, cardW - 52, 1);
    text(ctx, 'PRIX DE VENTE', -cardW / 2 + 34, 212, { size: 19, font: 'InterMed', color: '#8fa39a', align: 'left', tracking: 3 });
    text(ctx, fmt(1000) + ' F', cardW / 2 - 34, 232, { size: 62, font: 'SGBold', color: '#ffffff', align: 'right', tracking: -2 });
    ctx.restore();
    // payment indicator travelling across screen (secondary)
    const trav = inv(0.9, 1.7, t);
    if (trav > 0 && trav < 1) {
      const px = lerp(-80, W + 80, inOutCubic(trav));
      const py = H * 0.40 + 300 + Math.sin(trav * Math.PI) * -40;
      glow(ctx, px, py, 120, C.lime, 0.5 * Math.sin(trav * Math.PI), 0.5);
      streak(ctx, px, py, 420, 46, C.limeHi || C.lime, 0.5 * Math.sin(trav * Math.PI));
    }
    ctx.restore();
  }

  /* beat 2 — the split (1.9 – 4.3) */
  const splitP = ez(t, 2.0, 3.0, expoOut);
  const splitOut = ez(t, 4.15, 4.65, expoIn);
  if (splitP > 0 && splitOut < 1) {
    ctx.save();
    ctx.globalAlpha *= (1 - splitOut);
    text(ctx, 'LA VENTE SE PARTAGE', cx, H * 0.20, { size: 24, font: 'InterSemi', color: C.jade, tracking: 9, alpha: ez(t, 2.0, 2.6), baseline: 'middle' });
    // origin number
    text(ctx, fmt(1000) + ' F', cx, H * 0.285, { size: 58, font: 'SGBold', color: '#ffffff', tracking: -2 });
    // expanding split lines
    const lineP = ez(t, 2.25, 3.05, expoOut);
    ctx.save();
    ctx.strokeStyle = rgba(C.lime, 0.5 * lineP);
    ctx.lineWidth = 2;
    const y0 = H * 0.315;
    const spread = 189 * lineP;
    ctx.beginPath();
    ctx.moveTo(cx, y0);
    ctx.lineTo(cx, y0 + 60 * lineP);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx - spread, y0 + 60 * lineP);
    ctx.quadraticCurveTo(cx - spread * 0.5, y0 + 60 * lineP, cx, y0 + 60 * lineP);
    ctx.quadraticCurveTo(cx + spread * 0.5, y0 + 60 * lineP, cx + spread, y0 + 60 * lineP);
    ctx.stroke();
    [1, -1].forEach((s) => {
      ctx.beginPath();
      ctx.moveTo(cx + s * spread, y0 + 60 * lineP);
      ctx.lineTo(cx + s * spread, y0 + 60 * lineP + 74 * lineP);
      ctx.stroke();
    });
    ctx.restore();
    // two amounts
    const counterP = Math.min(1, ez(t, 2.35, 3.75, expoOut));
    const vSeller = Math.min(900, Math.round(900 * counterP));
    const vJaay = Math.min(100, Math.round(100 * counterP));
    const colW = 342;
    // seller
    ctx.save();
    ctx.translate(cx - 360, H * 0.404);
    roundRect(ctx, 0, 0, colW, 250, 24);
    ctx.fillStyle = 'rgba(12,40,28,0.85)';
    ctx.fill();
    ctx.strokeStyle = rgba(C.lime, 0.30);
    ctx.lineWidth = 1.4;
    ctx.stroke();
    text(ctx, 'POUR TOI', 32, 46, { size: 20, font: 'InterSemi', color: C.lime, align: 'left', tracking: 5 });
    text(ctx, fmt(vSeller), 32, 148, { size: 84, font: 'SGBold', color: '#ffffff', align: 'left', tracking: -4 });
    text(ctx, 'F CFA', 34 + measure(ctx, fmt(vSeller), 84, 'SGBold', -4) + 12, 148, { size: 24, font: 'InterMed', color: '#9fb4a7', align: 'left' });
    text(ctx, 'sur une vente de 1 000 F', 32, 206, { size: 19, font: 'InterReg', color: '#8fa39a', align: 'left' });
    ctx.restore();
    // jaay
    ctx.save();
    ctx.translate(cx + 18, H * 0.404);
    roundRect(ctx, 0, 0, colW, 250, 24);
    ctx.fillStyle = 'rgba(26,22,12,0.85)';
    ctx.fill();
    ctx.strokeStyle = rgba(C.gold, 0.28);
    ctx.lineWidth = 1.4;
    ctx.stroke();
    text(ctx, 'POUR JAAY', 30, 46, { size: 20, font: 'InterSemi', color: C.gold, align: 'left', tracking: 5 });
    text(ctx, fmt(vJaay), 30, 148, { size: 84, font: 'SGBold', color: C.goldHi || '#f6e2b8', align: 'left', tracking: -4 });
    text(ctx, 'F CFA', 32 + measure(ctx, fmt(vJaay), 84, 'SGBold', -4) + 10, 148, { size: 24, font: 'InterMed', color: '#b5a58a', align: 'left' });
    text(ctx, '= 10 % du prix', 32, 206, { size: 19, font: 'InterReg', color: '#9a8d76', align: 'left' });
    ctx.restore();
    ctx.restore();
  }

  /* beat 3 — the 10 % statement + proportion bar (4.3 – 7.7) */
  const stP = ez(t, 4.45, 5.3, expoOut);
  if (stP > 0) {
    ctx.save();
    ctx.globalAlpha *= stP;
    eyebrow(ctx, 'COMMISSION', cx, H * 0.20 + (1 - stP) * 16, { alpha: 0.9 });
    // "10 %" giant
    ctx.save();
    ctx.translate(cx, H * 0.34);
    const sc = 0.92 + 0.08 * stP;
    ctx.scale(sc, sc);
    const g = ctx.createLinearGradient(-240, -120, 240, 90);
    g.addColorStop(0, '#ffffff');
    g.addColorStop(0.6, '#eaffc0');
    g.addColorStop(1, '#c8f45f');
    text(ctx, '10 %', 0, 0, { size: 210, font: 'SGBold', color: g, tracking: -8 });
    ctx.restore();
    text(ctx, 'DE COMMISSION PAR VENTE', cx, H * 0.405 + (1 - stP) * 18, { size: 30, font: 'InterSemi', color: '#dbe7dd', tracking: 7 });

    // proportion bar: 90 / 10
    const barP = ez(t, 5.1, 6.3, inOutQuint);
    const bx = 130, by = H * 0.475, bw = W - 260, bh = 54;
    ctx.save();
    roundRect(ctx, bx, by, bw, bh, 27);
    ctx.fillStyle = 'rgba(255,255,255,0.07)';
    ctx.fill();
    // seller segment
    roundRect(ctx, bx, by, Math.max(28, (bw - 6) * 0.9 * barP), bh, 27);
    const bg = ctx.createLinearGradient(bx, by, bx + bw, by);
    bg.addColorStop(0, '#19c47c');
    bg.addColorStop(1, '#0f9f63');
    ctx.fillStyle = bg;
    ctx.fill();
    // jaay segment grows from the right
    const jw = Math.max(0, (bw - 6) * 0.1 * barP);
    if (jw > 1) {
      roundRect(ctx, bx + bw - jw - 3, by + 3, jw, bh - 6, (bh - 6) / 2);
      ctx.fillStyle = C.gold;
      ctx.fill();
    }
    ctx.restore();
    ctx.save();
    ctx.globalAlpha *= ez(t, 5.6, 6.4);
    text(ctx, '90 % POUR TOI', bx + 26, by + bh / 2 + 1, { size: 19, font: 'InterBold', color: '#04231a', align: 'left', baseline: 'middle', tracking: 2.5 });
    text(ctx, '10 %', bx + bw - 30, by + bh / 2 + 1, { size: 17, font: 'InterBold', color: '#332a12', align: 'right', baseline: 'middle', tracking: 1.5 });
    ctx.restore();

    // footnote
    const noteP = ez(t, 6.0, 6.8, expoOut);
    ctx.save();
    ctx.globalAlpha *= noteP;
    text(ctx, 'Calculée automatiquement — uniquement sur une vente confirmée.', cx, H * 0.545, { size: 20, font: 'InterReg', color: '#8ea398' });
    // activation card
    const aP = ez(t, 6.3, 7.2, expoOut);
    ctx.save();
    ctx.globalAlpha *= aP;
    ctx.translate(0, (1 - aP) * 24);
    const ay = H * 0.585;
    roundRect(ctx, 130, ay, W - 260, 128, 24);
    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(200,244,95,0.18)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    text(ctx, 'ACTIVATION DE TA BOUTIQUE', 160, ay + 42, { size: 17, font: 'InterSemi', color: '#a9bbb0', align: 'left', tracking: 4 });
    text(ctx, fmt(1000) + ' F CFA', 160, ay + 90, { size: 44, font: 'SGBold', color: C.lime, align: 'left', tracking: -1.5 });
    text(ctx, 'une seule fois', W - 160, ay + 84, { size: 19, font: 'InterReg', color: '#8ea398', align: 'right' });
    ctx.restore();
    ctx.restore();
    ctx.restore();
  }

  dust(ctx, t, 18, 0.32, 4);
  vignette(ctx, 0.5);
  grain(ctx, t, 0.045);
}

/* ============================================================= SCENE 5 ==== */
/* 23.9–30.4  The business universe: product choreography */
function scene5(ctx, t) {
  plate(ctx, t, { tint: C.emerald, intensity: 0.95, drift: 3.1 });

  /* headline beats */
  const beats = [
    { a: 0.15, out: 2.0, l1: 'TES', l2: 'PRODUITS.', color: C.white },
    { a: 2.05, out: 3.85, l1: 'TA', l2: 'BOUTIQUE.', color: C.limeHi },
    { a: 3.9, out: 6.5, l1: 'TON', l2: 'BUSINESS.', color: C.white },
  ];

  /* product tiles fly through 3D-ish space, driven by time */
  const tiles = [
    { p: PRODUCTS[0], a: 0.0, x: 0.26, y: 0.34, s: 0.86, rot: -0.10 },
    { p: PRODUCTS[4], a: 0.12, x: 0.74, y: 0.31, s: 0.74, rot: 0.11 },
    { p: PRODUCTS[8], a: 0.26, x: 0.20, y: 0.55, s: 0.68, rot: 0.07 },
    { p: PRODUCTS[9], a: 0.38, x: 0.79, y: 0.52, s: 0.80, rot: -0.09 },
    { p: PRODUCTS[1], a: 0.5, x: 0.44, y: 0.62, s: 0.62, rot: 0.04 },
  ];
  // hero product zoom mid-scene
  const heroZoom = ez(t, 2.5, 3.6, inOutQuint) * (1 - ez(t, 4.0, 5.0, inOutQuint));
  const tilesOut = ez(t, 5.3, 6.2, inOutQuint);

  tiles.forEach((tl, i) => {
    const inP = ez(t, 0.1 + i * 0.09, 1.15 + i * 0.09, expoOut);
    if (inP <= 0) return;
    const floatY = Math.sin(t * 0.9 + i * 1.7) * 16;
    const floatX = Math.cos(t * 0.7 + i * 2.1) * 10;
    const tw = 300 * tl.s;
    const th = tw * 1.28;
    let s = (0.9 + 0.1 * inP) * (1 - heroZoom * 0.55);
    let rot = tl.rot + Math.sin(t * 0.6 + i) * 0.03 + heroZoom * tl.rot * 2;
    // parallax push
    const isHero = i === 0 || i === 3;
    const drawTile = (c2) => {
      c2.translate(W / 2 + tx, ty);
      c2.rotate(rot);
      const depth = 1 - Math.abs(tl.x - 0.5) * 0.4;
      c2.scale(s * depth, s * depth);
      c2.save();
      roundRect(c2, -tw / 2, -th / 2, tw, th, 22);
      c2.clip();
      cover(c2, img(tl.p.img), -tw / 2, -th / 2, tw, th * 0.74);
      const gg = c2.createLinearGradient(0, th * 0.30, 0, th / 2);
      gg.addColorStop(0, 'rgba(5,12,9,0)');
      gg.addColorStop(1, 'rgba(5,12,9,1)');
      c2.fillStyle = gg;
      c2.fillRect(-tw / 2, th * 0.3, tw, th * 0.2);
      c2.fillStyle = '#0a1712';
      c2.fillRect(-tw / 2, th * 0.5 - th * 0.24, tw, th * 0.24);
      text(c2, tl.p.name, -tw / 2 + 20, th * 0.5 - th * 0.115, { size: 15 * tl.s, font: 'InterSemi', color: '#eef5ef', align: 'left' });
      text(c2, tl.p.price, -tw / 2 + 20, th * 0.5 - th * 0.035, { size: 19 * tl.s, font: 'SGBold', color: C.lime, align: 'left' });
      c2.restore();
      roundRect(c2, -tw / 2, -th / 2, tw, th, 22);
      c2.strokeStyle = 'rgba(255,255,255,0.14)';
      c2.lineWidth = 1.2;
      c2.stroke();
    };
    ctx.save();
    ctx.globalAlpha *= inP * (1 - tilesOut);
    // depth-of-field: background cards get soft focus
    const tx = (tl.x - 0.5) * W + floatX + (tl.x - 0.5) * heroZoom * 220;
    const ty = tl.y * H + floatY - tl.a * 40 - tilesOut * 900;
    if (isHero) {
      glow(ctx, W / 2 + tx, ty, tw * 0.95, i === 0 ? C.emerald : C.gold, 0.16 * inP, 0.62);
      drawTile(ctx);
    } else {
      blurred(ctx, W, H, 3, (c2) => { c2.globalAlpha = 0.85; drawTile(c2); }, 1);
    }
    ctx.restore();
  });

  // kinetic type blocks
  beats.forEach((b, bi) => {
    if (t < b.a || t > b.out + 0.5) return;
    const inP = ez(t, b.a, b.a + 0.62, expoOut);
    const outP = ez(t, b.out - 0.45, b.out, expoIn);
    const y = H * 0.845;
    ctx.save();
    ctx.globalAlpha *= 1 - outP;
    if (bi === 0) {
      // oversized two-line stack, tight tracking
      K.maskedLine(ctx, b.l1, W / 2 - 150, y - 96, { size: 112, font: 'InterBlack', progress: inP, tracking: -5, align: 'left' });
      K.maskedLine(ctx, b.l2, W / 2 - 150, y, { size: 112, font: 'InterBlack', progress: ez(t, b.a + 0.12, b.a + 0.8), tracking: -5, align: 'left', color: C.lime });
    } else if (bi === 1) {
      // centered, letterspaced, with side rules
      ctx.save();
      ctx.globalAlpha *= inP;
      text(ctx, b.l1, W / 2, y - 84, { size: 44, font: 'InterMed', color: '#dfeade', tracking: 26 });
      ctx.restore();
      K.maskedLine(ctx, b.l2, W / 2, y + 24, { size: 138, font: 'InterBlack', progress: inP, tracking: -6, color: C.lime });
    } else {
      // split-diagonal energetic stack
      K.maskedLine(ctx, b.l1, W / 2 + 30, y - 92, { size: 108, font: 'InterBlack', progress: inP, tracking: -4, align: 'right' });
      K.maskedLine(ctx, b.l2, W / 2 + 30, y + 16, { size: 108, font: 'InterBlack', progress: ez(t, b.a + 0.1, b.a + 0.75), tracking: -4, align: 'right', color: C.jade });
    }
    ctx.restore();
  });

  // scene-ending phone rising, then dissolving
  const phP = ez(t, 5.35, 6.15, expoOut);
  if (phP > 0) {
    const w = 318;
    ctx.save();
    ctx.globalAlpha *= phP * (1 - ez(t, 6.35, 6.5, cubicOut));
    phone(ctx, W / 2, H * 0.40, w, {
      screenFn: (c2, sw, sh) => productScreen(c2, sw, sh, { t: t - 5.35 + 1.1 }),
      tilt: 0, shadow: 0.7, glowAmt: 0.7,
    });
    ctx.restore();
  }

  dust(ctx, t, 24, 0.4, 12);
  vignette(ctx, 0.55);
  grain(ctx, t, 0.045);
}

/* ============================================================= SCENE 6 ==== */
/* 30.4–36.2  Climax: particles converge into the JAAY mark */
const NP = 900;
const PARTICLES = Array.from({ length: NP }, (_, i) => {
  const a = rnd(i * 1.31) * Math.PI * 2;
  const r = 300 + rnd(i * 2.77) * 1100;
  return {
    a, r,
    z: 0.4 + rnd(i * 5.13),
    s: 0.7 + rnd(i * 8.41) * 2.6,
    delay: rnd(i * 3.71) * 0.85,
    spin: 0.4 + rnd(i * 9.7) * 1.5,
    gx: (rnd(i * 6.19) - 0.5) * 300,
    gy: (rnd(i * 7.31) - 0.5) * 300,
  };
});

function scene6(ctx, t) {
  ctx.fillStyle = '#020504';
  ctx.fillRect(0, 0, W, H);

  /* volumetric shafts (ambient) */
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 5; i++) {
    const a = -0.9 + i * 0.42 + Math.sin(t * 0.3 + i) * 0.05;
    ctx.save();
    ctx.translate(W / 2 + Math.sin(t * 0.4 + i * 1.3) * 60, H * 0.1);
    ctx.rotate(a);
    const g = ctx.createLinearGradient(0, 0, 0, H * 0.9);
    const al = 0.028 + 0.014 * Math.sin(t * 0.7 + i * 2);
    g.addColorStop(0, rgba(C.emerald, al * 1.6));
    g.addColorStop(0.6, rgba(C.emerald, al * 0.4));
    g.addColorStop(1, rgba(C.emerald, 0));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.moveTo(-18, 0); ctx.lineTo(18, 0); ctx.lineTo(70, H); ctx.lineTo(-70, H);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }
  ctx.restore();

  const mx = W / 2, my = H * 0.415;
  const mSize = 300;
  // slow push-in + breathing: the climax never becomes a still frame
  const camS = 1 + 0.028 * K.inOutCubic(clamp(t / 5.8)) + 0.004 * Math.sin(t * 1.15);
  ctx.save();
  ctx.translate(mx, my); ctx.scale(camS, camS); ctx.translate(-mx, -my);
  const conv = ez(t, 0.35, 3.05, expoOut);     // convergence progress
  const form = ez(t, 1.55, 3.35, expoOut);     // mark materialises
  const wordP = ez(t, 2.85, 3.6, expoOut);

  // ambient glow bed
  glow(ctx, mx, my, 900, C.emerald, 0.10 + conv * 0.16, 0.62);
  glow(ctx, mx, my, 340, C.lime, 0.05 + form * 0.12, 0.6);

  /* particle convergence */
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < NP; i++) {
    const p = PARTICLES[i];
    const lp = clamp((conv - p.delay * 0.35) / (1 - p.delay * 0.3));
    const early = 0.55 + 0.45 * ez(t, 0.15, 0.9, expoOut);
    const ang = p.a + t * 0.35 * p.spin * (1 - lp);
    const rad = p.r * (1 - expoIn(lp) * 0.93) * (1 - lp * 0.02);
    const x = mx + Math.cos(ang) * rad * 1.15 + p.gx * lp * 0.9;
    const y = my + Math.sin(ang) * rad * 0.85 + p.gy * lp * 0.9;
    const life = Math.sin(Math.PI * clamp(lp * 1.15)) * 0.5 + 0.12;
    const al = life * (0.55 + p.z * 0.55) * early * (1 - form * 0.7);
    if (al <= 0.004) continue;
    ctx.fillStyle = rgba(i % 7 === 0 ? C.limeHi || C.lime : (i % 3 === 0 ? C.gold : C.jade), al);
    const sz = p.s * 1.35 * (0.75 + 0.35 * Math.sin(t * 3 + i));
    ctx.beginPath();
    ctx.arc(x, y, sz, 0, Math.PI * 2);
    ctx.fill();
    // streak trails on fast movers
    if (p.z > 1.0 && lp < 0.9) {
      ctx.strokeStyle = rgba(C.jade, al * 0.35);
      ctx.lineWidth = Math.max(0.6, sz * 0.5);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(mx + Math.cos(ang - 0.16) * rad * 1.15 + p.gx * lp, my + Math.sin(ang - 0.16) * rad * 0.85 + p.gy * lp);
      ctx.stroke();
    }
  }
  ctx.restore();

  /* the mark assembles */
  if (form > 0.001) {
    const s = mSize * (0.82 + 0.18 * form);
    ctx.save();
    ctx.translate(mx, my);
    // ring of light collapsing into the tile edge
    ring(ctx, 0, 0, s * (1.25 - 0.25 * form), (1 - form) * 0.8 + 0.1, 1.6, C.lime);
    ctx.globalAlpha *= form;
    glow(ctx, 0, 0, s * 1.5, C.emerald, 0.3 * form, 0.6);
    mark(ctx, -s / 2, -s / 2, s, { alpha: 1, morph: form, sheen: clamp(inv(2.6, 3.9, t)) });
    ctx.restore();

    // reflection under mark
    ctx.save();
    ctx.globalAlpha *= 0.13 * form;
    ctx.translate(mx, my + s * 0.86);
    ctx.scale(1, -0.45);
    mark(ctx, -s / 2, -s * 0.5, s, { alpha: 0.7, dot: false, morph: 1 });
    ctx.restore();
  }

  /* wordmark */
  if (wordP > 0.001) {
    const y = my + mSize * 0.5 + 150;
    ctx.save();
    ctx.globalAlpha *= wordP;
    ctx.translate(0, (1 - wordP) * 26);
    wordmark(ctx, W / 2, y, 208, { tracking: Math.round(-0.055 * 208 + (1 - wordP) * 30) });
    glow(ctx, W / 2, y - 60, 380, C.lime, 0.09 * wordP, 0.62);
    ctx.restore();
  }

  /* tagline */
  const tag1 = ez(t, 3.5, 4.2, expoOut);
  const tag2 = ez(t, 3.72, 4.45, expoOut);
  if (tag1 > 0) {
    ctx.save();
    ctx.globalAlpha *= 1 - ez(t, 5.75, 5.8, cubicOut);
    K.maskedLine(ctx, 'LE COMMERCE EN LIGNE', W / 2, H * 0.775, { size: 40, font: 'InterMed', progress: tag1, tracking: 6 });
    K.maskedLine(ctx, 'À TA PORTÉE.', W / 2, H * 0.845, { size: 62, font: 'InterBlack', progress: tag2, tracking: -1.5, color: C.limeHi });
    ctx.restore();
  }

  // final bloom
  const bloom = ez(t, 2.9, 3.6, expoOut);
  if (bloom > 0) glow(ctx, mx, my, 1100, C.emerald, 0.06 * bloom, 0.7);

  ctx.restore();
  dust(ctx, t, 20, 0.3, 21);
  vignette(ctx, 0.62);
  grain(ctx, t, 0.05);
}

/* ============================================================= SCENE 7 ==== */
/* 36.2–45.0  Final brand frame */
function scene7(ctx, t) {
  plate(ctx, t, { tint: C.emerald, intensity: 0.8, drift: 4.2 });
  const camS = 1 + 0.022 * inOutCubic(clamp(t / 8.6));
  ctx.save();
  ctx.translate(W / 2, H * 0.42); ctx.scale(camS, camS); ctx.translate(-W / 2, -H * 0.42);
  // subtle premium backdrop: fine radial rings
  ctx.save();
  ctx.globalAlpha *= 0.10;
  for (let i = 0; i < 4; i++) {
    ring(ctx, W / 2, H * 0.34, 200 + i * 130 + Math.sin(t * 0.5 + i) * 8, 0.5 - i * 0.1, 1, C.jade);
  }
  ctx.restore();
  glow(ctx, W / 2, H * 0.26, 760, C.emerald, 0.16, 0.66);
  glow(ctx, W / 2, H * 0.34, 300, C.lime, 0.08, 0.6);

  /* logo lockup */
  const logoP = ez(t, 0.1, 0.85, expoOut);
  const mS = 128;
  const mY = H * 0.178;
  ctx.save();
  ctx.globalAlpha *= logoP;
  ctx.translate(W / 2, mY);
  ctx.scale(0.86 + 0.14 * logoP, 0.86 + 0.14 * logoP);
  mark(ctx, -mS / 2, -mS / 2, mS, { alpha: 1, sheen: clamp(inv(0.6, 1.9, t) * 0.6) });
  ctx.restore();

  const wp = ez(t, 0.32, 1.05, expoOut);
  ctx.save();
  ctx.globalAlpha *= wp;
  wordmark(ctx, W / 2, H * 0.178 + mS * 0.5 + 106, 132, { tracking: Math.round(-0.055 * 132 + (1 - wp) * 22) });
  ctx.restore();

  /* headline */
  K.maskedLine(ctx, 'TA BOUTIQUE', W / 2, H * 0.386, { size: 82, font: 'InterBlack', progress: ez(t, 0.62, 1.35, expoOut), tracking: -2.6 });
  K.maskedLine(ctx, 'EN LIGNE', W / 2, H * 0.386 + 90, { size: 82, font: 'InterBlack', progress: ez(t, 0.76, 1.5, expoOut), tracking: -2.6 });

  // price
  const prP = ez(t, 1.15, 1.95, expoOut);
  ctx.save();
  ctx.globalAlpha *= prP;
  ctx.translate(0, (1 - prP) * 22);
  text(ctx, 'DÈS', W / 2, H * 0.548, { size: 30, font: 'InterMed', color: C.jade, tracking: 12 });
  ctx.save();
  ctx.translate(W / 2, H * 0.634);
  const g = ctx.createLinearGradient(-230, -80, 230, 60);
  g.addColorStop(0, '#ffffff');
  g.addColorStop(0.55, '#f0ffd8');
  g.addColorStop(1, '#c8f45f');
  text(ctx, fmt(1000) + ' F CFA', 0, 0, { size: 104, font: 'SGBold', color: g, tracking: -3.5 });
  ctx.restore();
  ctx.restore();

  // commission pill
  const pillP = ez(t, 1.7, 2.45, expoOut);
  ctx.save();
  ctx.globalAlpha *= pillP;
  ctx.translate(0, (1 - pillP) * 18);
  const pw = 600, ph = 66;
  roundRect(ctx, W / 2 - pw / 2, H * 0.676, pw, ph, ph / 2);
  ctx.fillStyle = 'rgba(230,195,132,0.10)';
  ctx.fill();
  ctx.strokeStyle = rgba(C.gold, 0.42);
  ctx.lineWidth = 1.4;
  ctx.stroke();
  text(ctx, '10 % DE COMMISSION PAR VENTE', W / 2, H * 0.676 + ph / 2 + 1, { size: 25, font: 'InterSemi', color: C.goldHi || '#f6e2b8', tracking: 3.4, baseline: 'middle' });
  ctx.restore();

  // CTA
  const ctaP = ez(t, 2.2, 3.0, expoOut);
  if (ctaP > 0) {
    const cy = H * 0.752;
    const cw = 560, ch = 92;
    // breathing glow (ambient)
    const breathe = 0.55 + 0.45 * Math.sin(t * 1.8);
    glow(ctx, W / 2, cy + ch / 2, 320, C.lime, 0.08 + 0.07 * breathe, 0.6);
    ctx.save();
    ctx.globalAlpha *= ctaP;
    ctx.translate(W / 2, cy + ch / 2);
    ctx.scale(0.9 + 0.1 * ctaP, 0.9 + 0.1 * ctaP);
    roundRect(ctx, -cw / 2, -ch / 2, cw, ch, ch / 2);
    const cg = ctx.createLinearGradient(0, -ch / 2, 0, ch / 2);
    cg.addColorStop(0, '#d9ff7a');
    cg.addColorStop(1, '#8fe23f');
    ctx.fillStyle = cg;
    ctx.fill();
    // sheen sweeps
    ctx.save();
    ctx.clip();
    [3.3, 5.6, 7.4].forEach((st) => {
      const sp = inv(st, st + 0.75, t);
      if (sp > 0 && sp < 1) {
        const gx = -cw + sp * cw * 2.2;
        const gg = ctx.createLinearGradient(gx - 90, 0, gx + 90, 0);
        gg.addColorStop(0, 'rgba(255,255,255,0)');
        gg.addColorStop(0.5, 'rgba(255,255,255,0.65)');
        gg.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = gg;
        ctx.fillRect(-cw / 2, -ch / 2, cw, ch);
      }
    });
    ctx.restore();
    text(ctx, 'REJOINS JAAY', 0, 2, { size: 36, font: 'InterBold', color: '#06251a', tracking: 2.6, baseline: 'middle' });
    // arrow
    ctx.save();
    ctx.strokeStyle = '#06251a';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    const ax = 176 + Math.sin(t * 2.4) * 4;
    ctx.beginPath(); ctx.moveTo(ax, 1); ctx.lineTo(ax + 20, 1); ctx.moveTo(ax + 13, -7); ctx.lineTo(ax + 21, 1); ctx.lineTo(ax + 13, 9); ctx.stroke();
    ctx.restore();
    ctx.restore();
  }

  // URL
  const urlP = ez(t, 2.8, 3.6, expoOut);
  ctx.save();
  ctx.globalAlpha *= urlP;
  ctx.translate(0, (1 - urlP) * 14);
  text(ctx, 'athena-market.vercel.app', W / 2, H * 0.845, { size: 27, font: 'InterMed', color: '#b9cbbd', tracking: 0.6 });
  ctx.restore();

  // credit block (mandatory, always legible)
  const crP = ez(t, 3.35, 4.2, expoOut);
  if (crP > 0) {
    const y = H * 0.888;
    ctx.save();
    ctx.globalAlpha *= crP;
    hairline(ctx, W / 2, y - 46, 300, ez(t, 3.3, 4.1), C.gold, 1.2, 0.5);
    text(ctx, 'Offert par Serigne SYLLA', W / 2, y + 2, { size: 26, font: 'InterSemi', color: '#e9f1e8', tracking: 0.4 });
    text(ctx, '77 201 90 77', W / 2, y + 40, { size: 26, font: 'InterMed', color: C.goldHi || '#f6e2b8', tracking: 2.2 });
    ctx.restore();
  }

  ctx.restore();
  dust(ctx, t, 14, 0.22, 33);
  vignette(ctx, 0.45);
  grain(ctx, t, 0.04);
}

module.exports = {
  TL, scene1, scene2, scene3, scene4, scene5, scene6, scene7,
  SCENES: [scene1, scene2, scene3, scene4, scene5, scene6, scene7],
  maskedLineY, coin,
};
