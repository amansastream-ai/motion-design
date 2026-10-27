'use strict';
/* JAAY — renderer.
   Usage:
     node src/render.js --stills 0.6,2.2,5.5,12,19,27,33,41   → PNG stills in ../out/stills
     node src/render.js --video [--from 0 --to 45] [--fps 60]  → raw.rgb stream (pipe to ffmpeg)
   The renderer writes raw RGBA-free RGB24 frames to stdout when --pipe is passed.
*/
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');
const K = require('./core');
const S = require('./scenes');
const { W, H, FPS, DUR } = K;
const TL = S.TL;
const BOUNDS = [
  [TL.s1[1], 's1s2'], [TL.s2[1], 's2s3'], [TL.s3[1], 's3s4'],
  [TL.s4[1], 's4s5'], [TL.s5[1], 's5s6'], [TL.s6[1], 's6s7'],
];

const main = createCanvas(W, H);
const mctx = main.getContext('2d');
const buf = createCanvas(W, H);
const bctx = buf.getContext('2d');

/* how the cut between two scenes behaves */
function transitionFor(t, boundary) {
  const p = (t - (boundary - 0.30)) / 0.60; // 0..1 across the cut
  return p;
}

function sceneIndex(T) {
  const t = TL;
  if (T < t.s2[0]) return 0;
  if (T < t.s3[0]) return 1;
  if (T < t.s4[0]) return 2;
  if (T < t.s5[0]) return 3;
  if (T < t.s6[0]) return 4;
  if (T < t.s7[0]) return 5;
  return 6;
}

function drawScene(ctx, i, T) {
  const key = ['s1', 's2', 's3', 's4', 's5', 's6', 's7'][i];
  const [a, b] = TL[key];
  const t = T - a;
  if (i === 1) S.scene2(ctx, t, T);
  else S.SCENES[i](ctx, t);
}

const FADE = 0.34; // half-window of each crossfade

function renderFrame(ctx, T) {
  ctx.save();
  ctx.globalAlpha = 1;
  // find if we are near a boundary
  let near = null;
  for (const [b] of BOUNDS) {
    if (T > b - FADE && T < b + FADE) near = b;
  }
  if (!near) {
    drawScene(ctx, sceneIndex(T), T);
  } else {
    const p = (T - (near - FADE)) / (FADE * 2); // 0..1
    const e = K.inOutCubic(p);
    const prevIdx = BOUNDS.findIndex(([b]) => b === near);
    const nextIdx = prevIdx + 1;
    // outgoing (with slight push / scale for continuity)
    const outA = 1 - e;
    const inA = e;
    if (outA > 0.002) {
      ctx.save();
      ctx.globalAlpha = outA;
      // outgoing scenes drift out slightly (camera keeps moving)
      const push = 1 + 0.05 * e;
      ctx.translate(W / 2, H / 2); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
      drawScene(ctx, prevIdx, T);
      ctx.restore();
    }
    if (inA > 0.002) {
      ctx.save();
      ctx.globalAlpha = inA;
      const push = 1 + 0.055 * (1 - e);
      ctx.translate(W / 2, H / 2); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
      drawScene(ctx, nextIdx, T);
      ctx.restore();
    }
    // light wipe through the cut (secondary transition layer)
    const lw = Math.sin(e * Math.PI);
    if (lw > 0.01) {
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      K.glow(ctx, W / 2, H * (0.3 + 0.4 * e), 1100, K.C.emerald, 0.16 * lw, 0.6);
      ctx.restore();
    }
  }
  // global exposure ramp in/out of the film
  if (T < 0.12) {
    ctx.fillStyle = `rgba(0,0,0,${1 - T / 0.12})`;
    ctx.fillRect(0, 0, W, H);
  }
  if (T > DUR - 0.5) {
    ctx.fillStyle = `rgba(0,0,0,${Math.max(0, (T - (DUR - 0.5)) / 0.5) * 0.55})`;
    ctx.fillRect(0, 0, W, H);
  }
  ctx.restore();
}

function frameRGB(T) {
  mctx.setTransform(1, 0, 0, 1, 0, 0);
  mctx.clearRect(0, 0, W, H);
  renderFrame(mctx, T);
  // RGB24 via getImageData (drop alpha)
  const d = mctx.getImageData(0, 0, W, H).data;
  const out = Buffer.allocUnsafe(W * H * 3);
  for (let i = 0, j = 0; i < d.length; i += 4, j += 3) {
    out[j] = d[i]; out[j + 1] = d[i + 1]; out[j + 2] = d[i + 2];
  }
  return out;
}

/* ------------------------------------------------------------------ CLI */
const args = process.argv.slice(2);

(async () => {
await K.preload();

const has = (f) => args.includes(f);
const val = (f, def) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : def; };

if (has('--stills')) {
  const times = (val('--stills', '0') || '').split(',').map(Number).filter((n) => !isNaN(n));
  const dir = path.join(__dirname, '..', 'out', 'stills');
  fs.mkdirSync(dir, { recursive: true });
  times.forEach((T) => {
    mctx.clearRect(0, 0, W, H);
    renderFrame(mctx, T);
    const f = path.join(dir, `t${T.toFixed(2).padStart(5, '0')}.png`);
    fs.writeFileSync(f, main.toBuffer('image/png'));
    console.log('wrote', f);
  });
}

if (has('--pipe')) {
  const from = Number(val('--from', 0));
  const to = Number(val('--to', DUR));
  const fps = Number(val('--fps', FPS));
  const n0 = Math.round(from * fps), n1 = Math.round(to * fps);
  const stream = fs.createWriteStream(val('--out', '/dev/stdout'), { flags: 'w' });
  let n = n0;
  const t0 = Date.now();
  const step = () => {
    let ok = true;
    while (n < n1) {
      const T = n / fps;
      const frame = frameRGB(T);
      ok = stream.write(frame);
      n++;
      if (!ok) { stream.once('drain', step); return; }
      if ((n - n0) % 60 === 0) {
        const el = (Date.now() - t0) / 1000;
        process.stderr.write(`frame ${n}/${n1} · ${((n - n0) / el).toFixed(1)} fps · ${T.toFixed(2)}s\n`);
      }
    }
    stream.end();
  };
  step();
}

})();

module.exports = { renderFrame, frameRGB, main, mctx };
