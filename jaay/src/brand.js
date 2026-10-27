'use strict';
/* JAAY brand system: mark, wordmark, device frame and the marketplace UI
   (UI content is built from the real catalogue data of athena-market.vercel.app) */
const K = require('./core');
const { C, text, roundRect, rgba, clamp, lerp, inv, expoOut, cubicOut, glow, cover, img, measure } = K;

/* ------------------------------------------------ real catalogue (live site) */
const PRODUCTS = [
  { name: 'Robe wax Africaine', price: '1 000 F', priceN: 1000, img: 'prod_dress_card.jpg', zoom: 1.5, cat: 'Mode', store: 'Teranga Style' },
  { name: 'Sac en cuir fait main', price: '5 000 F', priceN: 5000, img: 'prod_bag_card.jpg', zoom: 1.35, cat: 'Artisanat', store: 'Teranga Style' },
  { name: 'Bijoux en perles', price: '2 500 F', priceN: 2500, img: 'prod_bag_card.jpg', zoom: 1.35, cat: 'Artisanat', store: 'Teranga Style' },
  { name: 'Boubou brodé premium', price: '10 000 F', priceN: 10000, img: 'prod_dress_card.jpg', zoom: 1.5, cat: 'Mode', store: 'Teranga Style' },
  { name: 'Écouteurs Bluetooth', price: '50 000 F', priceN: 50000, img: 'prod_tech_card.jpg', zoom: 1.3, cat: 'Électronique', store: 'Dakar Tech' },
  { name: 'Montre connectée', price: '25 000 F', priceN: 25000, img: 'prod_tech_card.jpg', zoom: 1.3, cat: 'Électronique', store: 'Dakar Tech' },
  { name: 'Enceinte portable', price: '15 000 F', priceN: 15000, img: 'prod_tech_card.jpg', zoom: 1.3, cat: 'Électronique', store: 'Dakar Tech' },
  { name: 'Chargeur rapide 25W', price: '3 500 F', priceN: 3500, img: 'prod_tech_card.jpg', zoom: 1.3, cat: 'Électronique', store: 'Dakar Tech' },
  { name: 'Sérum éclat karité', price: '4 500 F', priceN: 4500, img: 'prod_beauty_card.jpg', zoom: 1.4, cat: 'Beauté & soins', store: 'Ndar Beauty' },
  { name: 'Sneakers urbaines', price: '18 000 F', priceN: 18000, img: 'prod_sneaker_card.jpg', zoom: 1.25, cat: 'Mode', store: 'Dakar Tech' },
];

/* --------------------------------------------------------------- JAAY mark */
function mark(ctx, x, y, s, o = {}) {
  const { alpha = 1, sheen = 0, morph = 1, dot = true } = o;
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.translate(x, y);
  ctx.scale(s / 200, s / 200);
  // tile
  const g = ctx.createLinearGradient(0, 0, 200, 200);
  g.addColorStop(0, '#0d3a28');
  g.addColorStop(0.55, '#08231a');
  g.addColorStop(1, '#0a1712');
  roundRect(ctx, 0, 0, 200, 200, 54);
  ctx.fillStyle = g;
  ctx.fill();
  ctx.lineWidth = 2;
  ctx.strokeStyle = rgba(C.emeraldHi, 0.35);
  ctx.stroke();
  // inner J
  ctx.save();
  roundRect(ctx, 0, 0, 200, 200, 54);
  ctx.clip();
  ctx.translate(0, (1 - morph) * 60);
  const jg = ctx.createLinearGradient(60, 40, 150, 170);
  jg.addColorStop(0, C.limeHi);
  jg.addColorStop(0.5, C.lime);
  jg.addColorStop(1, C.jade);
  ctx.strokeStyle = jg;
  ctx.lineWidth = 23;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(126, 52);
  ctx.lineTo(126, 118);
  ctx.bezierCurveTo(126, 150, 104, 162, 82, 152);
  ctx.stroke();
  if (dot) {
    ctx.fillStyle = C.gold;
    ctx.beginPath();
    ctx.arc(126, 32, 11, 0, Math.PI * 2);
    ctx.fill();
  }
  // glass sheen
  if (sheen > 0) {
    const sg = ctx.createLinearGradient(-200 + sheen * 600, 0, 60 + sheen * 600, 200);
    sg.addColorStop(0, 'rgba(255,255,255,0)');
    sg.addColorStop(0.5, 'rgba(255,255,255,0.30)');
    sg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = sg;
    ctx.fillRect(-200, 0, 600, 200);
  }
  ctx.restore();
  ctx.restore();
}

function wordmark(ctx, x, y, size, o = {}) {
  const { alpha = 1, color = C.white, tracking = -0.055 * size, align = 'center', font = 'InterBlack' } = o;
  text(ctx, 'JAAY', x, y, { size, font, color, tracking, align, alpha, baseline: 'alphabetic' });
}

/* ------------------------------------------------------------ device frame */
const SW = 390, SH = 844;

/* body + shadow + edge (optionally ring-only so UI can sit underneath) */
function phoneBody(ctx, cx, cy, w, o = {}) {
  const { h = w * (SH / SW), alpha = 1, shadow = 1, glowAmt = 0.6, bezel = 11, tilt = 0, ringOnly = false } = o;
  const bh = h + bezel * 2, bw = w + bezel * 2;
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.translate(cx, cy);
  const sx = Math.cos(tilt * 0.55);
  ctx.transform(sx, tilt * 0.12, 0, 1 / Math.max(0.92, sx), 0, 0);
  if (shadow) {
    const sg = ctx.createRadialGradient(0, bh / 2 + 70, 10, 0, bh / 2 + 70, bw * 0.95);
    sg.addColorStop(0, `rgba(0,0,0,${0.7 * shadow})`);
    sg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.save();
    ctx.translate(0, bh / 2 + 40);
    ctx.scale(1, 0.16);
    ctx.fillStyle = sg;
    ctx.beginPath();
    ctx.arc(0, 0, bw * 0.9, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
  if (glowAmt) glow(ctx, 0, 0, bw * 0.8, C.emerald, 0.16 * glowAmt, 0.55);
  const bg = ctx.createLinearGradient(-bw / 2, -bh / 2, bw / 2, bh / 2);
  bg.addColorStop(0, '#2a3831');
  bg.addColorStop(0.16, '#0d1512');
  bg.addColorStop(0.84, '#090f0d');
  bg.addColorStop(1, '#374940');
  const outer = () => roundRect(ctx, -bw / 2, -bh / 2, bw, bh, w * 0.145);
  if (ringOnly) {
    // stroke a thick rounded ring, clipped to the body, so the screen stays untouched
    ctx.save();
    outer();
    ctx.clip();
    outer();
    ctx.lineWidth = bezel * 2;
    ctx.strokeStyle = bg;
    ctx.stroke();
    ctx.restore();
    ctx.lineWidth = 1.4;
    ctx.strokeStyle = 'rgba(214,246,190,0.26)';
    roundRect(ctx, -w / 2, -h / 2, w, h, w * 0.115); ctx.stroke();
  } else {
    outer();
    ctx.fillStyle = bg;
    ctx.fill();
    // side buttons
    ctx.fillStyle = '#2d3d35';
    roundRect(ctx, bw / 2 - 2, -bh * 0.24, 3.5, bh * 0.10, 2); ctx.fill();
    roundRect(ctx, -bw / 2 - 1.5, -bh * 0.22, 3.5, bh * 0.06, 2); ctx.fill();
    // bezel edge highlight
    ctx.lineWidth = 1.8;
    ctx.strokeStyle = 'rgba(214,246,190,0.32)';
    outer(); ctx.stroke();
  }
  ctx.restore();
}

/* island + glass overlay */
function phoneGlass(ctx, cx, cy, w, o = {}) {
  const { h = w * (SH / SW), alpha = 1, sheen = 1, tilt = 0, island = true } = o;
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.translate(cx, cy);
  const sx = Math.cos(tilt * 0.55);
  ctx.transform(sx, tilt * 0.12, 0, 1 / Math.max(0.92, sx), 0, 0);
  if (island) {
    roundRect(ctx, -w * 0.155, -h / 2 + w * 0.030, w * 0.31, w * 0.078, w * 0.04);
    ctx.fillStyle = '#000';
    ctx.fill();
  }
  if (sheen) {
    ctx.save();
    roundRect(ctx, -w / 2, -h / 2, w, h, w * 0.115);
    ctx.clip();
    const sg = ctx.createLinearGradient(-w / 2, -h / 2, w * 0.1, h / 2);
    sg.addColorStop(0, 'rgba(255,255,255,0.15)');
    sg.addColorStop(0.3, 'rgba(255,255,255,0.03)');
    sg.addColorStop(0.52, 'rgba(255,255,255,0)');
    sg.addColorStop(1, 'rgba(255,255,255,0.05)');
    ctx.fillStyle = sg;
    ctx.fillRect(-w / 2, -h / 2, w, h);
    ctx.restore();
  }
  ctx.restore();
}

function phone(ctx, cx, cy, w, o = {}) {
  const { screenFn = null, tilt = 0, rotZ = 0, alpha = 1, shadow = 1, sheen = 1, glowAmt = 0.6, hideShadow = false } = o;
  const h = o.h || w * (SH / SW);
  ctx.save();
  ctx.globalAlpha *= alpha;
  if (rotZ) {
    ctx.translate(cx, cy); ctx.rotate(rotZ); ctx.translate(-cx, -cy);
  }
  phoneBody(ctx, cx, cy, w, { h, tilt, shadow: hideShadow ? 0 : shadow, glowAmt, alpha: 1 });
  if (screenFn) {
    ctx.save();
    roundRect(ctx, cx - w / 2, cy - h / 2, w, h, w * 0.115);
    ctx.clip();
    ctx.translate(cx - w / 2, cy - h / 2);
    ctx.scale(w / SW, h / SH);
    screenFn(ctx, SW, SH);
    ctx.restore();
  }
  phoneGlass(ctx, cx, cy, w, { h, tilt, sheen, alpha: 1 });
  ctx.restore();
}

/* frame only, screen left transparent (for continuous camera pull-backs) */
function phoneFrameOnly(ctx, cx, cy, w, o = {}) {
  const h = o.h || w * (SH / SW);
  phoneBody(ctx, cx, cy, w, { ...o, h, shadow: o.shadow === undefined ? 0 : o.shadow, ringOnly: true });
  phoneGlass(ctx, cx, cy, w, { ...o, h });
}

/* -------------------------------------------------------------- UI pieces */
function statusBar(ctx, w, color = '#eaf3ec') {
  text(ctx, '9:41', 26, 32, { size: 15, font: 'InterSemi', color, align: 'left', baseline: 'middle' });
  const x = w - 74;
  for (let i = 0; i < 4; i++) ctx.fillRect(x + i * 6, 34 - i * 3, 4, 4 + i * 3);
  ctx.fillStyle = color;
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.6;
  roundRect(ctx, w - 40, 24, 24, 12, 3.5); ctx.stroke();
  ctx.fillRect(w - 37, 27, 15, 6);
  ctx.fillRect(w - 14.5, 28, 2, 4);
  // wifi
  ctx.beginPath(); ctx.arc(w - 54, 34, 7, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke();
  ctx.beginPath(); ctx.arc(w - 54, 34, 3.4, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke();
}

function chip(ctx, label, x, y, o = {}) {
  const { active = false, size = 11, padX = 13, h = 30 } = o;
  ctx.font = `${size}px InterMed`;
  const w = ctx.measureText(label).width + padX * 2;
  roundRect(ctx, x, y, w, h, h / 2);
  if (active) { ctx.fillStyle = C.lime; ctx.fill(); }
  else { ctx.fillStyle = 'rgba(255,255,255,0.07)'; ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1; ctx.stroke(); }
  text(ctx, label, x + w / 2, y + h / 2 + 0.5, { size, font: 'InterMed', color: active ? '#08231a' : '#d7e3d9', align: 'center', baseline: 'middle' });
  return w;
}

function waIcon(ctx, x, y, s, color = C.wa) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s / 20, s / 20);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(0, 0, 10, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#06281a';
  ctx.lineWidth = 1.9;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(-4.4, 5.2);
  ctx.lineTo(-3.1, 2.6);
  ctx.bezierCurveTo(-5.2, -0.2, -4.6, -3.2, -2, -4.6);
  ctx.bezierCurveTo(0.6, -6, 3.6, -4.4, 4.6, -1.6);
  ctx.bezierCurveTo(5.6, 1.2, 3.6, 4.4, 0.8, 4.8);
  ctx.stroke();
  ctx.restore();
}

function productCard(ctx, p, x, y, w, h, o = {}) {
  const { progress = 1, r = 16, card = '#13251d', pressed = 0, badge = true, name = true, price = true } = o;
  const e = clamp(progress);
  if (e <= 0) return;
  ctx.save();
  ctx.globalAlpha *= e;
  ctx.translate(x + w / 2, y + h / 2 + (1 - expoOut(e)) * 26);
  const ps = 1 - pressed * 0.03;
  ctx.scale(ps, ps);
  ctx.translate(-w / 2, -h / 2);
  roundRect(ctx, 0, 0, w, h, r);
  ctx.fillStyle = card;
  ctx.fill();
  ctx.save();
  roundRect(ctx, 0, 0, w, h, r);
  ctx.clip();
  const ih = h * (name ? 0.66 : 1);
  cover(ctx, img(p.img), 0, 0, w, ih, { focusY: 0.5, zoom: p.zoom || 1.05 });
  ctx.fillStyle = 'rgba(6,14,10,0.04)';
  ctx.fillRect(0, 0, w, ih);
  if (name) {
    text(ctx, p.name, 13, ih + 24, { size: 13, font: 'InterSemi', color: '#eef5ef', align: 'left', baseline: 'alphabetic' });
    if (price) text(ctx, p.price, 13, ih + 52, { size: 16, font: 'SGBold', color: C.lime, align: 'left', baseline: 'alphabetic', tracking: -0.2 });
  }
  ctx.restore();
  if (badge) {
    roundRect(ctx, 10, 10, 62, 22, 11);
    ctx.fillStyle = 'rgba(6,20,13,0.72)';
    ctx.fill();
    text(ctx, 'En stock', 41, 21.5, { size: 10.5, font: 'InterMed', color: C.jade, align: 'center', baseline: 'middle' });
  }
  ctx.restore();
}

/* ----------------------------------------------------------- HOME SCREEN */
function homeScreen(ctx, w, h, o = {}) {
  const { t = 0, p = 1, scroll = 0, tap = -1 } = o;
  const bgG = ctx.createLinearGradient(0, 0, 0, h);
  bgG.addColorStop(0, '#0a1a13');
  bgG.addColorStop(0.5, '#071410');
  bgG.addColorStop(1, '#06100c');
  ctx.fillStyle = bgG;
  ctx.fillRect(0, 0, w, h);
  glow(ctx, w * 0.82, 70, 250, C.emerald, 0.15 * p, 0.6);
  statusBar(ctx, w);

  /* ---- sticky header */
  const hp = K.ez(t, 0.0, 0.45);
  mark(ctx, 22, 62, 30, { alpha: hp, dot: false });
  text(ctx, 'Jaay', 62, 80, { size: 26, font: 'InterBlack', color: '#f2f7f2', align: 'left', tracking: -1, alpha: hp });
  text(ctx, 'Fait à Dakar', 63, 96, { size: 10, font: 'InterMed', color: C.jade, align: 'left', tracking: 0.4, alpha: hp * 0.9 });
  ctx.save();
  roundRect(ctx, w - 62, 60, 36, 36, 18);
  ctx.fillStyle = '#0f3a28';
  ctx.fill();
  ctx.clip();
  cover(ctx, img('hero_merchant.jpg'), w - 62, 60, 36, 36, { focusY: 0.14, zoom: 1.1 });
  ctx.restore();

  /* ---- scrolling content */
  const y0 = 108;
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, y0, w, h - y0 - 62);
  ctx.clip();
  ctx.translate(0, -scroll);

  // search
  const sp = K.ez(t, 0.12, 0.62);
  const sy = y0 + 6;
  ctx.save();
  ctx.globalAlpha *= sp;
  ctx.translate(0, (1 - sp) * 14);
  roundRect(ctx, 20, sy, w - 40, 38, 12);
  ctx.fillStyle = 'rgba(255,255,255,0.075)';
  ctx.fill();
  ctx.strokeStyle = 'rgba(200,244,95,0.16)';
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.strokeStyle = '#8fa39a';
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.arc(38, sy + 18, 6, 0, Math.PI * 2); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(42.5, sy + 22.5); ctx.lineTo(48, sy + 28); ctx.stroke();
  text(ctx, 'Rechercher un produit…', 56, sy + 19, { size: 12, font: 'InterReg', color: '#7f9188', align: 'left', baseline: 'middle' });
  ctx.restore();

  // category chips
  let cx = 20;
  const cp = K.ez(t, 0.22, 0.72);
  ctx.save();
  ctx.globalAlpha *= cp;
  ['Tout', 'Mode', 'Beauté', 'Électronique', 'Artisanat'].forEach((c, i) => {
    cx += chip(ctx, c, cx, sy + 50, { active: i === 0, size: 10.5, h: 27 }) + 7;
  });
  ctx.restore();

  // hero banner
  const bp = K.ez(t, 0.3, 0.85);
  ctx.save();
  ctx.globalAlpha *= bp;
  const by = sy + 92;
  roundRect(ctx, 20, by, w - 40, 88, 16);
  const bg2 = ctx.createLinearGradient(20, by, w - 20, by + 88);
  bg2.addColorStop(0, '#11784c');
  bg2.addColorStop(1, '#0a2a1c');
  ctx.fillStyle = bg2;
  ctx.fill();
  ctx.save();
  roundRect(ctx, 20, by, w - 40, 88, 16);
  ctx.clip();
  glow(ctx, w - 50, by + 16, 120, C.lime, 0.22, 0.6);
  ctx.restore();
  text(ctx, 'Ta boutique en 5 minutes', 36, by + 34, { size: 15, font: 'InterBold', color: '#f6fbf2', align: 'left', tracking: -0.2 });
  text(ctx, '1 000 F CFA — activation unique', 36, by + 55, { size: 10.5, font: 'InterMed', color: 'rgba(230,255,175,0.92)', align: 'left' });
  roundRect(ctx, 36, by + 64, 96, 20, 10);
  ctx.fillStyle = C.lime;
  ctx.fill();
  text(ctx, 'Créer ma boutique', 84, by + 74.5, { size: 8.8, font: 'InterSemi', color: '#08231a', align: 'center', baseline: 'middle' });
  ctx.restore();

  // section title
  text(ctx, 'Produits populaires', 22, sy + 208, { size: 14, font: 'InterBold', color: '#eaf3ec', align: 'left', tracking: -0.2 });
  text(ctx, 'Voir tout', w - 22, sy + 208, { size: 10, font: 'InterMed', color: C.jade, align: 'right' });

  // product grid
  const cw = (w - 54) / 2, chh = cw * 1.34;
  PRODUCTS.slice(0, 6).forEach((pr, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const pp = K.ez(t, 0.36 + i * 0.05, 0.95 + i * 0.05);
    productCard(ctx, pr, 20 + col * (cw + 14), sy + 226 + row * (chh + 14), cw, chh, {
      progress: pp, pressed: tap === i ? 1 : 0,
    });
  });
  ctx.restore();

  /* ---- bottom navigation (screen space) */
  const navY = h - 62;
  ctx.fillStyle = 'rgba(8,18,14,0.98)';
  ctx.fillRect(0, navY - 12, w, 74);
  ctx.strokeStyle = 'rgba(255,255,255,0.07)';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, navY - 12); ctx.lineTo(w, navY - 12); ctx.stroke();
  ['Accueil', 'Catalogue', 'Boutique', 'Profil'].forEach((l, i) => {
    const x = (w / 8) * (2 * i + 1);
    const act = i === 0;
    ctx.fillStyle = act ? C.lime : '#5f7168';
    ctx.beginPath();
    ctx.arc(x, navY + 8, 4.6, 0, Math.PI * 2);
    ctx.fill();
    text(ctx, l, x, navY + 28, { size: 8.4, font: 'InterMed', color: act ? C.lime : '#5f7168', align: 'center', baseline: 'middle' });
  });
  // home indicator
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  roundRect(ctx, w / 2 - 44, h - 14, 88, 4, 2);
  ctx.fill();
}

/* -------------------------------------------------------- PRODUCT SCREEN */
function productScreen(ctx, w, h, o = {}) {
  const { t = 0, p = 1 } = o;
  const pr = PRODUCTS[0];
  ctx.fillStyle = '#050c09';
  ctx.fillRect(0, 0, w, h);
  statusBar(ctx, w);
  // big image
  const ih = h * 0.42;
  ctx.save();
  ctx.globalAlpha *= K.ez(t, 0, 0.5);
  cover(ctx, img(pr.img), 0, 0, w, ih, { focusY: 0.42 });
  const fade = ctx.createLinearGradient(0, ih * 0.55, 0, ih);
  fade.addColorStop(0, 'rgba(5,12,9,0)');
  fade.addColorStop(1, 'rgba(5,12,9,1)');
  ctx.fillStyle = fade;
  ctx.fillRect(0, ih * 0.55, w, ih * 0.45);
  ctx.restore();
  // back chevron
  ctx.strokeStyle = '#eaf3ec';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(34, 46); ctx.lineTo(26, 54); ctx.lineTo(34, 62); ctx.stroke();
  // store row
  const sp = K.ez(t, 0.15, 0.6);
  ctx.save();
  ctx.globalAlpha *= sp;
  roundRect(ctx, 20, ih - 8, w - 40, 46, 13);
  ctx.fillStyle = 'rgba(255,255,255,0.06)';
  ctx.fill();
  ctx.beginPath(); ctx.arc(40, ih + 15, 12, 0, Math.PI * 2); ctx.fillStyle = '#0f3a28'; ctx.fill();
  text(ctx, 'TS', 40, ih + 15.5, { size: 9, font: 'InterBold', color: C.lime, align: 'center', baseline: 'middle' });
  text(ctx, 'Teranga Style', 58, ih + 11, { size: 11.5, font: 'InterSemi', color: '#eaf3ec', align: 'left' });
  text(ctx, 'Boutique vérifiée · Dakar', 58, ih + 25, { size: 8.6, font: 'InterReg', color: '#8fa39a', align: 'left' });
  text(ctx, 'Suivre', w - 36, ih + 16, { size: 9.6, font: 'InterSemi', color: C.lime, align: 'right' });
  ctx.restore();
  // title/price
  const tp = K.ez(t, 0.22, 0.7);
  ctx.save();
  ctx.globalAlpha *= tp;
  ctx.translate(0, (1 - tp) * 16);
  text(ctx, pr.name, 22, ih + 74, { size: 20, font: 'InterBold', color: '#f2f7f2', align: 'left', tracking: -0.4 });
  text(ctx, pr.price, 22, ih + 108, { size: 30, font: 'SGBold', color: C.lime, align: 'left', tracking: -0.6 });
  roundRect(ctx, 22, ih + 120, 74, 22, 11);
  ctx.fillStyle = 'rgba(79,224,163,0.14)';
  ctx.fill();
  text(ctx, 'En stock', 59, ih + 131, { size: 9.6, font: 'InterMed', color: C.jade, align: 'center', baseline: 'middle' });
  ctx.restore();
  // description
  const dp = K.ez(t, 0.3, 0.78);
  ctx.save();
  ctx.globalAlpha *= dp;
  text(ctx, 'Robe en wax africain, coupe ajustée,', 22, ih + 168, { size: 10.4, font: 'InterReg', color: '#93a69c', align: 'left' });
  text(ctx, 'finitions main. Livraison à Dakar.', 22, ih + 185, { size: 10.4, font: 'InterReg', color: '#93a69c', align: 'left' });
  ctx.restore();
  // options: size + colour
  const op = K.ez(t, 0.34, 0.82);
  ctx.save();
  ctx.globalAlpha *= op;
  text(ctx, 'TAILLE', 22, ih + 218, { size: 8.6, font: 'InterMed', color: '#7f9188', align: 'left', tracking: 2.4 });
  let sx = 22;
  ['S', 'M', 'L', 'XL'].forEach((sz, i) => {
    roundRect(ctx, sx, ih + 228, 40, 32, 9);
    if (i === 2) { ctx.fillStyle = 'rgba(200,244,95,0.16)'; ctx.fill(); ctx.strokeStyle = rgba(C.lime, 0.5); }
    else { ctx.fillStyle = 'rgba(255,255,255,0.05)'; ctx.fill(); ctx.strokeStyle = 'rgba(255,255,255,0.10)'; }
    ctx.lineWidth = 1;
    ctx.stroke();
    text(ctx, sz, sx + 20, ih + 244, { size: 11, font: 'InterSemi', color: i === 2 ? C.lime : '#cfdcd3', align: 'center', baseline: 'middle' });
    sx += 46;
  });
  ctx.restore();
  ctx.save();
  ctx.globalAlpha *= op;
  text(ctx, 'COULEUR', 240, ih + 218, { size: 8.6, font: 'InterMed', color: '#7f9188', align: 'left', tracking: 2.4 });
  [['#c8f45f', true], ['#0f9f63', false], ['#e6c384', false]].forEach(([col, on], i) => {
    ctx.beginPath(); ctx.arc(252 + i * 32, ih + 244, 11, 0, Math.PI * 2);
    ctx.fillStyle = col; ctx.fill();
    if (on) { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.arc(252 + i * 32, ih + 244, 14.5, 0, Math.PI * 2); ctx.stroke(); }
  });
  ctx.restore();
  // trust strip
  const tp2 = K.ez(t, 0.44, 0.9);
  ctx.save();
  ctx.globalAlpha *= tp2;
  const ty = ih + 292;
  roundRect(ctx, 20, ty, w - 40, 56, 13);
  ctx.fillStyle = 'rgba(255,255,255,0.045)';
  ctx.fill();
  [['Livraison Dakar', '24 h'], ['Paiement', 'à la livraison'], ['Vendeur', 'vérifié']].forEach((cell, i) => {
    const bx = 20 + (w - 40) * (i / 3) + 18;
    text(ctx, cell[0], bx, ty + 22, { size: 8.2, font: 'InterReg', color: '#7f9188', align: 'left' });
    text(ctx, cell[1], bx, ty + 38, { size: 10.4, font: 'InterSemi', color: i === 2 ? C.jade : '#e6eee8', align: 'left' });
    if (i < 2) { ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(20 + (w - 40) * ((i + 1) / 3), ty + 14, 1, 28); }
  });
  ctx.restore();
  // CTA
  const ctp = K.ez(t, 0.38, 0.9);
  ctx.save();
  ctx.globalAlpha *= ctp;
  ctx.translate(0, (1 - ctp) * 20);
  roundRect(ctx, 20, h - 112, w - 40, 50, 15);
  const cg = ctx.createLinearGradient(0, h - 112, 0, h - 62);
  cg.addColorStop(0, '#2ee08a');
  cg.addColorStop(1, '#0f9f63');
  ctx.fillStyle = cg;
  ctx.fill();
  waIcon(ctx, 46, h - 87, 20, '#8ff0b5');
  text(ctx, 'Renseignements sur WhatsApp', 66, h - 86, { size: 11.6, font: 'InterSemi', color: '#03251a', align: 'left', baseline: 'middle' });
  roundRect(ctx, 20, h - 54, w - 40, 30, 12);
  ctx.fillStyle = 'rgba(255,255,255,0.05)';
  ctx.fill();
  text(ctx, 'Partager le produit', w / 2, h - 39, { size: 10, font: 'InterMed', color: '#c9d6cd', align: 'center', baseline: 'middle' });
  ctx.restore();
}

/* ------------------------------------------------------ DASHBOARD SCREEN */
function dashboardScreen(ctx, w, h, o = {}) {
  const { t = 0 } = o;
  const bgG = ctx.createLinearGradient(0, 0, 0, h);
  bgG.addColorStop(0, '#08140f');
  bgG.addColorStop(1, '#040a07');
  ctx.fillStyle = bgG;
  ctx.fillRect(0, 0, w, h);
  statusBar(ctx, w);
  text(ctx, 'Ma boutique', 22, 92, { size: 21, font: 'InterBlack', color: '#f2f7f2', align: 'left', tracking: -0.5 });
  text(ctx, 'teranga-style.jaay.sn', 22, 110, { size: 9.4, font: 'InterReg', color: '#7f9188', align: 'left' });
  roundRect(ctx, w - 84, 76, 62, 24, 12);
  ctx.fillStyle = 'rgba(200,244,95,0.14)';
  ctx.fill();
  ctx.beginPath(); ctx.arc(w - 72, 88, 3, 0, Math.PI * 2); ctx.fillStyle = C.lime; ctx.fill();
  text(ctx, 'En ligne', w - 50, 89, { size: 8.6, font: 'InterMed', color: C.lime, align: 'center', baseline: 'middle' });
  // revenue card
  const rp = K.ez(t, 0.1, 0.6);
  ctx.save();
  ctx.globalAlpha *= rp;
  ctx.translate(0, (1 - rp) * 18);
  roundRect(ctx, 20, 136, w - 40, 118, 18);
  const cg = ctx.createLinearGradient(20, 136, w - 20, 254);
  cg.addColorStop(0, '#0d5c3c');
  cg.addColorStop(1, '#08301f');
  ctx.fillStyle = cg;
  ctx.fill();
  text(ctx, 'Encaissé ce mois', 38, 168, { size: 10.4, font: 'InterMed', color: 'rgba(226,255,158,0.8)', align: 'left' });
  text(ctx, '900 F', 38, 214, { size: 44, font: 'SGBold', color: '#ffffff', align: 'left', tracking: -1 });
  text(ctx, 'sur 1 000 F de vente', 150, 212, { size: 10, font: 'InterReg', color: 'rgba(255,255,255,0.6)', align: 'left' });
  roundRect(ctx, w - 118, 246, 96, 0.1, 0);
  ctx.fillStyle = 'rgba(255,255,255,0.16)';
  ctx.fillRect(w - 120, 246, 98, 1);
  // mini bars
  for (let i = 0; i < 12; i++) {
    const bh = 8 + Math.abs(Math.sin(i * 1.7)) * 26;
    ctx.fillStyle = i > 8 ? C.lime : 'rgba(255,255,255,0.22)';
    ctx.fillRect(w - 124 + i * 8, 236 - bh, 4.6, bh);
  }
  ctx.restore();
  // stats
  const stats = [['Ventes', '1'], ['Commission 10 %', '100 F'], ['Net', '900 F']];
  stats.forEach((s, i) => {
    const p = K.ez(t, 0.24 + i * 0.08, 0.75 + i * 0.08);
    ctx.save();
    ctx.globalAlpha *= p;
    const x = 20 + i * ((w - 40 - 20) / 3 + 10);
    const ww = (w - 40 - 20) / 3;
    roundRect(ctx, x, 268, ww, 66, 14);
    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    ctx.fill();
    text(ctx, s[0], x + 12, 290, { size: 8.6, font: 'InterMed', color: '#8fa39a', align: 'left' });
    text(ctx, s[1], x + 12, 316, { size: 17, font: 'SGBold', color: i === 1 ? '#f0d9a8' : (i === 2 ? C.lime : '#eaf3ec'), align: 'left', tracking: -0.4 });
    ctx.restore();
  });
  // products list
  text(ctx, 'Mes produits', 22, 372, { size: 13, font: 'InterBold', color: '#eaf3ec', align: 'left' });
  PRODUCTS.slice(0, 5).forEach((pr, i) => {
    const p = K.ez(t, 0.4 + i * 0.06, 0.9 + i * 0.06);
    ctx.save();
    ctx.globalAlpha *= p;
    const y = 386 + i * 74;
    roundRect(ctx, 20, y, w - 40, 64, 13);
    ctx.fillStyle = 'rgba(255,255,255,0.045)';
    ctx.fill();
    ctx.save();
    roundRect(ctx, 28, y + 8, 48, 48, 10);
    ctx.clip();
    cover(ctx, img(pr.img), 28, y + 8, 48, 48);
    ctx.restore();
    text(ctx, pr.name, 88, y + 27, { size: 10.6, font: 'InterSemi', color: '#eaf3ec', align: 'left' });
    text(ctx, pr.price + '  ·  En stock', 88, y + 44, { size: 9, font: 'InterReg', color: '#8fa39a', align: 'left' });
    text(ctx, '···', w - 34, y + 32, { size: 14, font: 'InterBold', color: '#5f7168', align: 'right' });
    ctx.restore();
  });
}

/* ----------------------------------------------------- WhatsApp exchange */
function waBubble(ctx, str, x, y, o = {}) {
  const { mine = false, p = 1, size = 12.5, maxW = 240 } = o;
  const e = clamp(p);
  if (e <= 0) return;
  ctx.save();
  ctx.font = `${size}px InterReg`;
  const words = str.split(' ');
  const lines = [];
  let cur = '';
  words.forEach((wd) => {
    const test = cur ? cur + ' ' + wd : wd;
    if (ctx.measureText(test).width > maxW) { lines.push(cur); cur = wd; } else cur = test;
  });
  lines.push(cur);
  const lh = size * 1.35;
  const h = lines.length * lh + 18;
  const w = Math.max(...lines.map((l) => ctx.measureText(l).width)) + 28;
  const bx = mine ? x - w : x;
  ctx.globalAlpha *= e;
  ctx.translate(0, (1 - expoOut(e)) * 10);
  roundRect(ctx, bx, y, w, h, 12);
  ctx.fillStyle = mine ? '#0b3d2c' : 'rgba(255,255,255,0.08)';
  ctx.fill();
  ctx.strokeStyle = mine ? 'rgba(37,211,102,0.35)' : 'rgba(255,255,255,0.10)';
  ctx.lineWidth = 1;
  ctx.stroke();
  lines.forEach((l, i) => text(ctx, l, bx + 14, y + 15 + i * lh, { size, font: 'InterReg', color: mine ? '#d8f7e4' : '#e6eee8', align: 'left' }));
  text(ctx, mine ? '9:24' : '9:23', bx + w - 12, y + h - 8, { size: 7.4, font: 'InterReg', color: 'rgba(255,255,255,0.35)', align: 'right', baseline: 'middle' });
  ctx.restore();
  return h;
}

module.exports = {
  PRODUCTS, mark, wordmark, phone, phoneBody, phoneGlass, phoneFrameOnly, homeScreen, productScreen, dashboardScreen,
  productCard, chip, waIcon, waBubble, statusBar,
};
