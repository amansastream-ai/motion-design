#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
« Enquêtes parlementaires — des auditions au cœur de l'actualité »
Rendu broadcast 1920x1080 @ 30 fps — duplex, lower-thirds, habillage motion design.
Usage :
    python render_video.py           -> rend la vidéo complète + mux audio
    python render_video.py still T   -> écrit un frame de contrôle (videos/still-T.png)
"""
import os, sys, math, glob, subprocess, wave, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FPS = 30
W, H = 1920, 1080
DUR = 51.5
XFADE = 0.45
SR = 48000

FFMPEG = None
for c in [os.path.join(os.path.dirname(sys.executable), 'ffmpeg')] if False else []:
    pass
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = 'ffmpeg'

# ---------------------------------------------------------------- couleurs ---
NAVY_D   = (10, 18, 32)
NAVY     = (16, 30, 50)
NAVY_L   = (24, 44, 72)
INK      = (8, 13, 24)
WHITE    = (245, 247, 250)
MUTED    = (168, 186, 206)
GOLD     = (232, 186, 78)
RED      = (205, 52, 60)
TEAL     = (64, 160, 190)

# ------------------------------------------------------------------ polices ---
FONT_DIR = os.path.join(ROOT, 'assets', 'fonts')
def _font_path(fam, wght):
    p = os.path.join(FONT_DIR, f'{fam}-{wght}.ttf')
    return p if os.path.exists(p) else None

def font(fam, wght, size):
    p = _font_path(fam, wght)
    if p:
        return ImageFont.truetype(p, size)
    p = glob.glob('/usr/share/fonts/**/DejaVuSans*.ttf', recursive=True)
    return ImageFont.truetype(p[0] if p else None, size) if p else ImageFont.load_default(size)

F_CACHE = {}
def F(fam, wght, size):
    k = (fam, wght, size)
    if k not in F_CACHE:
        F_CACHE[k] = font(fam, wght, size)
    return F_CACHE[k]

# ------------------------------------------------------------------ easing ---
def clamp01(x): return 0.0 if x < 0 else (1.0 if x > 1 else x)
def seg(t, a, b): return clamp01((t - a) / max(1e-9, (b - a)))
def ease_out_cubic(x): x = clamp01(x); return 1 - (1 - x) ** 3
def ease_out_expo(x):
    x = clamp01(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
def ease_in_out(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)
def ease_in_cubic(x): x = clamp01(x); return x ** 3
def ease_out_quint(x): x = clamp01(x); return 1 - (1 - x) ** 5

# ------------------------------------------------------------------ images ---
def cover(im, w, h):
    sw, sh = im.size
    s = max(w / sw, h / sh)
    im2 = im.resize((max(w, int(sw * s + .5)), max(h, int(sh * s + .5))), Image.BILINEAR)
    x = (im2.size[0] - w) // 2
    y = (im2.size[1] - h) // 2
    return im2.crop((x, y, x + w, y + h))

def grade(im):
    """Étalonnage commun : léger refroidissement + contraste."""
    im = ImageEnhance.Color(im).enhance(0.92)
    im = ImageEnhance.Contrast(im).enhance(1.07)
    tint = Image.new(im.mode, im.size, (24, 40, 66))
    return Image.blend(im, tint, 0.07)

def load_rgb(path):
    im = Image.open(path).convert('RGB')
    return grade(im)

_KB_SRC = {}
def kb_src(path, key):
    if key not in _KB_SRC:
        im = load_rgb(path)
        _KB_SRC[key] = cover(im, int(W * 1.02), int(H * 1.02))
    return _KB_SRC[key]

def kb_frame(src, out_w, out_h, t, dur, z0=1.0, z1=1.12, px0=0.5, px1=0.5, py0=0.5, py1=0.5, ease=ease_in_out):
    p = ease(clamp01(t / dur))
    z = z0 + (z1 - z0) * p
    sw, sh = src.size
    cw, ch = sw / z, sh / z
    cx = (sw - cw) * (px0 + (px1 - px0) * p)
    cy = (sh - ch) * (py0 + (py1 - py0) * p)
    crop = src.crop((int(cx), int(cy), int(cx + cw), int(cy + ch)))
    return crop.resize((out_w, out_h), Image.BILINEAR)

# --------------------------------------------------------------- calques ---
def paste_rgba(base, img, x, y, alpha=1.0):
    if alpha <= 0.003 or img is None:
        return
    x, y = int(x), int(y)
    if x >= base.size[0] or y >= base.size[1]:
        return
    if alpha < 0.997:
        img = img.copy()
        img.putalpha(img.getchannel('A').point(lambda v: int(v * alpha)))
    base.paste(img, (x, y), img)

def text_img(text, fnt, fill, tracking=0):
    if tracking == 0:
        bbox = fnt.getbbox(text)
        w = max(1, bbox[2] - bbox[0] + 8)
        h = max(1, bbox[3] - bbox[1] + 8)
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((4 - bbox[0], 4 - bbox[1]), text, font=fnt, fill=fill)
        return img
    # letterspacing
    widths = [fnt.getbbox(ch)[2] - fnt.getbbox(ch)[0] for ch in text]
    heights = [fnt.getbbox(ch)[3] - fnt.getbbox(ch)[1] for ch in text]
    total = sum(widths) + tracking * (len(text) - 1) + 10
    h = max(heights) + 12 if heights else 20
    img = Image.new('RGBA', (max(1, total), max(1, h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 5
    for ch in text:
        bb = fnt.getbbox(ch)
        d.text((x - bb[0], 6 - bb[1]), ch, font=fnt, fill=fill)
        x += (bb[2] - bb[0]) + tracking
    return img

def rounded(w, h, r, fill, outline=None, width=0):
    img = Image.new('RGBA', (max(1, w), max(1, h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill, outline=outline, width=width)
    return img

_grad_cache = {}
def linear_grad(w, h, c0, c1, vertical=True):
    k = (w, h, c0, c1, vertical)
    if k in _grad_cache: return _grad_cache[k]
    img = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(img)
    n = h if vertical else w
    for i in range(n):
        p = i / max(1, n - 1)
        c = tuple(int(c0[j] + (c1[j] - c0[j]) * p) for j in range(3)) + (255,)
        if vertical:
            d.line([(0, i), (w, i)], fill=c)
        else:
            d.line([(i, 0), (i, h)], fill=c)
    _grad_cache[k] = img
    return img

_vig_cache = {}
def vignette(w, h, strength=0.55, power=1.6):
    k = (w, h, strength, power)
    if k in _vig_cache: return _vig_cache[k]
    y, x = np.ogrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    d = np.sqrt(((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2) / math.sqrt(2)
    a = np.clip((d - 0.35) / 0.65, 0, 1) ** power * strength
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 3] = (a * 255).astype(np.uint8)
    img = Image.fromarray(arr, 'RGBA')
    _vig_cache[k] = img
    return img

def scrim_bottom(w=1920, h=560, top_a=0, bot_a=210, color=INK):
    k = ('sb', w, h, top_a, bot_a, color)
    if k in _grad_cache: return _grad_cache[k]
    img = Image.new('RGBA', (w, h), color + (0,))
    arr = np.array(img)
    ramp = np.linspace(top_a, bot_a, h).astype(np.uint8)
    arr[..., 3] = ramp[:, None]
    out = Image.fromarray(arr, 'RGBA')
    _grad_cache[k] = out
    return out

_glow_cache = {}
def radial_glow(size, color, alpha=120):
    k = (size, color, alpha)
    if k in _glow_cache: return _glow_cache[k]
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    arr = np.zeros((size, size, 4), dtype=np.float32)
    y, x = np.ogrid[0:size, 0:size]
    d = np.sqrt((x - size/2) ** 2 + (y - size/2) ** 2) / (size / 2)
    a = np.clip(1 - d, 0, 1) ** 2.2 * alpha
    arr[..., 0] = color[0]; arr[..., 1] = color[1]; arr[..., 2] = color[2]
    arr[..., 3] = a
    out = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    _glow_cache[k] = out
    return out

_grid_cache = {}
def grid_layer(w, h, step=110, alpha=12, color=(150, 190, 230)):
    k = (w, h, step, alpha, color)
    if k in _grid_cache: return _grid_cache[k]
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=color + (alpha,), width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=color + (alpha,), width=1)
    _grid_cache[k] = img
    return img

# --------------------------------------------------------- éléments motion ---
def ease_enter(t, start, dur, ease=ease_out_expo):
    return ease(seg(t, start, start + dur))

def lower_third(main, sub, tag, name_size=48):
    """Barre basse façon régie : bloc accent + nom + rôle + pastille."""
    bar_w, bar_h = 1240, 108
    bar = Image.new('RGBA', (bar_w, bar_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(bar)
    d.rectangle([0, 0, bar_w, bar_h], fill=(12, 20, 34, 234))
    d.rectangle([0, 0, 10, bar_h], fill=RED + (255,))
    d.line([(0, 0), (bar_w, 0)], fill=(255, 255, 255, 26), width=1)
    # ombre douce
    shadow = bar.filter(ImageFilter.GaussianBlur(9))
    canvas = Image.new('RGBA', (bar_w + 40, bar_h + 40), (0, 0, 0, 0))
    canvas.paste(shadow, (20, 26), shadow)
    canvas.paste(bar, (20, 12), bar)
    fn = F('Oswald', 600, name_size)
    fs = F('Inter', 400, 27)
    t1 = text_img(main, fn, WHITE + (255,))
    t2 = text_img(sub, fs, MUTED + (255,))
    canvas.paste(t1, (20 + 34, 12 + 16), t1)
    canvas.paste(t2, (20 + 34, 12 + 16 + name_size + 10), t2)
    if tag:
        ft = F('Oswald', 500, 22)
        tt = text_img(tag, ft, (24, 30, 42, 255), tracking=3)
        pill_w = tt.size[0] + 36
        pill = rounded(pill_w, 46, 6, GOLD + (255,))
        px = 20 + bar_w - pill_w - 26
        canvas.paste(pill, (px, 12 + (bar_h - 46) // 2), pill)
        canvas.paste(tt, (px + 18, 12 + (bar_h - 46) // 2 + 10), tt)
    return canvas

TICK_TEXT = ("ASSEMBLÉE NATIONALE  ·  COMMISSIONS D’ENQUÊTE  ·  GESTION FONCIÈRE  ·  "
             "DOMAINE PUBLIC MARITIME  ·  TOTAL RETURN SWAP  ·  AUDITIONS DU 15 OCTOBRE 2026  ·  ")
_ticker_cache = None
def ticker_strip():
    global _ticker_cache
    if _ticker_cache is None:
        fnt = F('Inter', 500, 26)
        one = text_img(TICK_TEXT, fnt, (200, 215, 232, 255), tracking=1)
        strip = Image.new('RGBA', (one.size[0] * 2 + 40, one.size[1]), (0, 0, 0, 0))
        strip.paste(one, (0, 0), one)
        strip.paste(one, (one.size[0] + 40, 0), one)
        _ticker_cache = strip
    return _ticker_cache

def draw_ticker(frame, t, y=H - 46):
    strip = ticker_strip()
    band = Image.new('RGBA', (W, 52), (7, 12, 22, 210))
    paste_rgba(frame, band, 0, y - 6)
    d = ImageDraw.Draw(frame)
    d.line([(0, y - 6), (W, y - 6)], fill=(255, 255, 255, 18), width=1)
    speed = 130.0
    off = int(t * speed) % strip.size[0]
    paste_rgba(frame, strip, -off, y + 2)
    paste_rgba(frame, strip, -off + strip.size[0], y + 2)

def top_bar(frame, local_t, right_text="AUDITIONS · 15 OCT. 2026"):
    a = ease_enter(local_t, 0.15, 0.55)
    if a <= 0: return
    y = 34 + (1 - a) * -26
    fnt = F('Oswald', 500, 26)
    fnt2 = F('Inter', 500, 22)
    t1 = text_img("ENQUÊTES PARLEMENTAIRES", fnt, WHITE + (255,), tracking=2)
    paste_rgba(frame, t1, 56, y + 8, a)
    # puce rouge
    if a > 0.2:
        d = ImageDraw.Draw(frame)
        d.rectangle([56 - 22, y + 14, 56 - 12, y + 24], fill=RED + (int(255 * a),))
    t2 = text_img(right_text, fnt2, (210, 222, 236, 255), tracking=1)
    paste_rgba(frame, t2, W - 56 - t2.size[0], y + 12, a)

def accent_line(frame, x, y, w_now, h=6, color=RED, alpha=1.0):
    if w_now <= 0 or alpha <= 0: return
    d = ImageDraw.Draw(frame)
    d.rectangle([x, y, x + int(w_now), y + h], fill=color + (int(255 * alpha),))

# ---------------------------------------------------------------- segments ---
IM_AN1   = os.path.join(ROOT, 'image-search', 'assembl-e-nationale-du-s-n-gal-dakar-b-t-1.jpg')
IM_AN2   = os.path.join(ROOT, 'image-search', 'assembl-e-nationale-du-s-n-gal-dakar-b-t-2.jpg')
IM_CAD   = os.path.join(ROOT, 'image-search', 'cadastre-plan-cadastral-documents-foncie-3.jpg')
IM_MER   = os.path.join(ROOT, 'assets', 'dakar-coast.png')
IM_INTRO = os.path.join(ROOT, 'assets', 'intro-bg.png')
IM_TR1   = os.path.join(ROOT, 'image-search', 'trading-screens-stock-market-financial-c-1.jpg')
IM_TR2   = os.path.join(ROOT, 'image-search', 'trading-screens-stock-market-financial-c-2.jpg')

S_TITLE1, S_TITLE2 = "ENQUÊTES", "PARLEMENTAIRES"
T_SUB = "Des auditions au cœur de l’actualité"
T_KICK = "POLITIQUE NATIONALE"

def bg_intro_frame(t, zoom0=1.0, zoom1=1.07, px0=0.5, px1=0.52):
    src = kb_src(IM_INTRO, 'intro')
    frame = kb_frame(src, W, H, t, 6.0, zoom0, zoom1, px0, px1, 0.5, 0.5).convert('RGBA')
    # teinte navy + assombrissement
    tint = Image.new('RGBA', (W, H), NAVY_D + (255,))
    frame = Image.blend(frame, tint, 0.52)
    paste_rgba(frame, vignette(W, H, 0.5), 0, 0)
    paste_rgba(frame, grid_layer(W, H, 130, 10), 0, 0)
    # halos ambients dérivants
    g1 = radial_glow(980, (40, 110, 190), 60)
    g2 = radial_glow(760, (190, 70, 70), 36)
    paste_rgba(frame, g1, 180 + int(60 * math.sin(t * 0.35)), -160 + int(30 * math.cos(t * 0.28)))
    paste_rgba(frame, g2, 1150 + int(50 * math.cos(t * 0.3)), 420 + int(36 * math.sin(t * 0.22)))
    return frame

def seg_intro(t):
    frame = bg_intro_frame(t)
    # faisceau lumineux diagonal (ambiant)
    if t > 0.9:
        sw = linear_grad(460, 2200, (255, 255, 255), (255, 255, 255))
        arr = np.array(sw)
        ramp = np.clip(np.linspace(0, 26, 460), 0, 255).astype(np.uint8)
        arr[..., 3] = ramp[::-1][None, :]
        sweep = Image.fromarray(arr, 'RGBA').rotate(16, expand=True, resample=Image.BILINEAR)
        sx = -500 + int((t / 6.2) * 2600)
        paste_rgba(frame, sweep, sx, -300, 0.5)

    # badge
    a = ease_enter(t, 0.25, 0.6)
    if a > 0:
        fnt = F('Oswald', 500, 30)
        bt = text_img(T_KICK, fnt, (24, 30, 42, 255), tracking=5)
        pill = rounded(bt.size[0] + 52, 58, 8, GOLD + (255,))
        x, y = 170, 168 + (1 - a) * -34
        paste_rgba(frame, pill, x, y, a)
        paste_rgba(frame, bt, x + 26, y + 13, a)

    # titre (2 lignes, stagger)
    for i, (line, delay) in enumerate([(S_TITLE1, 0.75), (S_TITLE2, 0.93)]):
        a = ease_enter(t, delay, 0.85)
        if a <= 0: continue
        fnt = F('Oswald', 700, 132 if i == 0 else 118)
        ti = text_img(line, fnt, WHITE + (255,), tracking=2)
        y = 250 + i * 128 + (1 - a) * 58
        paste_rgba(frame, ti, 170, y, a)

    # ligne accent
    a = ease_enter(t, 1.45, 0.7, ease_out_quint)
    if a > 0:
        accent_line(frame, 172, 536, 560 * a, 6, RED, 1.0)

    # sous-titre
    a = ease_enter(t, 1.85, 0.7)
    if a > 0:
        fnt = F('Inter', 400, 46)
        ti = text_img(T_SUB, fnt, (214, 226, 240, 255))
        paste_rgba(frame, ti, 172, 574 + (1 - a) * 26, a)

    # date + institution
    a = ease_enter(t, 2.65, 0.7)
    if a > 0:
        fnt = F('Oswald', 600, 30)
        chip_t = text_img("15 OCTOBRE 2026", fnt, WHITE + (255,), tracking=3)
        chip = rounded(chip_t.size[0] + 44, 56, 6, (255, 255, 255, 18), outline=(255, 255, 255, 70), width=1)
        paste_rgba(frame, chip, 172, 686 + (1 - a) * 22, a)
        paste_rgba(frame, chip_t, 194, 698 + (1 - a) * 22, a)
        fnt2 = F('Inter', 500, 26)
        t2 = text_img("ASSEMBLÉE NATIONALE — SÉNÉGAL", fnt2, GOLD + (255,), tracking=2)
        paste_rgba(frame, t2, 172 + chip.size[0] + 28, 700 + (1 - a) * 22, a)

    # barres latérales décoratives (secondaire)
    d = ImageDraw.Draw(frame)
    d.rectangle([0, 0, 12, H], fill=(205, 52, 60, int(255 * 0.85)))
    d.rectangle([12, 0, 18, H], fill=(232, 186, 78, int(255 * 0.55)))
    return frame

def seg_an(t):
    src = kb_src(IM_AN1, 'an1')
    frame = kb_frame(src, W, H, t, 9.4, 1.04, 1.16, 0.42, 0.56, 0.42, 0.55).convert('RGBA')
    paste_rgba(frame, scrim_bottom(1920, 620, 0, 225), 0, H - 620)
    paste_rgba(frame, scrim_bottom(1920, 240, 120, 0), 0, 0)  # léger scrim haut
    top_bar(frame, t)

    # grand chiffre date
    a = ease_enter(t, 1.0, 0.9)
    if a > 0:
        fnum = F('Oswald', 700, 230)
        fmon = F('Oswald', 500, 44)
        n1 = text_img("15", fnum, WHITE + (255,))
        n2 = text_img("OCTOBRE 2026", fmon, GOLD + (255,), tracking=4)
        x = W - 320
        paste_rgba(frame, n1, x - n1.size[0] // 2, 120 + (1 - a) * 40, a * 0.92)
        paste_rgba(frame, n2, x - n2.size[0] // 2, 120 + n1.size[1] + 2 + (1 - a) * 40, a * 0.92)

    # lower third
    a = ease_enter(t, 0.55, 0.65)
    if a > 0:
        lt = lower_third("COMMISSIONS D’ENQUÊTE PARLEMENTAIRE",
                         "Deux commissions auditionnent des responsables ce jeudi 15 octobre",
                         "AUDITIONS", name_size=46)
        paste_rgba(frame, lt, 56 + (1 - a) * -420, H - 210, a)
    draw_ticker(frame, t)
    return frame

def seg_duplex(t):
    frame = Image.new('RGBA', (W, H), NAVY_D + (255,))
    paste_rgba(frame, linear_grad(W, H, NAVY_D, (19, 38, 64)), 0, 0)
    paste_rgba(frame, grid_layer(W, H, 110, 13), 0, 0)
    g1 = radial_glow(1100, (36, 100, 180), 55)
    paste_rgba(frame, g1, -220 + int(40 * math.sin(t * 0.4)), -200 + int(28 * math.cos(t * 0.31)))
    g2 = radial_glow(900, (180, 66, 66), 34)
    paste_rgba(frame, g2, 1250 + int(46 * math.cos(t * 0.27)), 520 + int(30 * math.sin(t * 0.33)))

    # entête
    a = ease_enter(t, 0.15, 0.55)
    if a > 0:
        fnt = F('Oswald', 600, 42)
        ti = text_img("FONCIER  &  DOMAINE PUBLIC MARITIME", fnt, WHITE + (255,), tracking=2)
        paste_rgba(frame, ti, (W - ti.size[0]) // 2, 78 + (1 - a) * -28, a)
        accent_line(frame, (W - 360) // 2, 138, 360 * a, 4, GOLD, 1.0)

    # panneaux duplex
    pw, ph = 846, 528
    gap = 44
    x0 = (W - 2 * pw - gap) // 2
    y0 = 190
    srcL = kb_src(IM_CAD, 'cad')
    imL = kb_frame(srcL, pw, ph, t, 10.4, 1.03, 1.14, 0.55, 0.42, 0.5, 0.55).convert('RGBA')
    srcR = kb_src(IM_MER, 'mer')
    imR = kb_frame(srcR, pw, ph, t, 10.4, 1.12, 1.02, 0.45, 0.55, 0.5, 0.45).convert('RGBA')

    def panel(img, x, y, a, label, tag_color):
        if a <= 0: return
        # ombre
        sh = rounded(pw + 40, ph + 40, 10, (0, 0, 0, 160))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        paste_rgba(frame, sh, x - 20, y - 8 + 12, a * 0.8)
        # image arrondie
        mask = Image.new('L', (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], 8, fill=255)
        tile = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
        tile.paste(img, (0, 0))
        tile.putalpha(mask)
        paste_rgba(frame, tile, x, y, a)
        # cadre
        fr = rounded(pw, ph, 8, None, outline=(255, 255, 255, 60), width=2)
        paste_rgba(frame, fr, x, y, a)
        # onglet label
        fnt = F('Oswald', 500, 26)
        lt = text_img(label, fnt, WHITE + (255,), tracking=2)
        tab = rounded(lt.size[0] + 36, 48, 6, tag_color + (235,))
        paste_rgba(frame, tab, x + 18, y + ph - 62, a)
        paste_rgba(frame, lt, x + 36, y + ph - 50, a)

    aL = ease_enter(t, 0.55, 0.7)
    aR = ease_enter(t, 0.67, 0.7)
    panel(imL, x0 + int((1 - aL) * -140), y0 + int((1 - aL) * 26), aL,
          "ÉCRAN 1 — LOTISSEMENTS & FONCIER", (176, 96, 28))
    panel(imR, x0 + pw + gap + int((1 - aR) * 140), y0 + int((1 - aR) * 26), aR,
          "ÉCRAN 2 — DOMAINE PUBLIC MARITIME", (24, 88, 130))

    # séparateur lumineux (secondaire)
    a = ease_enter(t, 1.0, 0.6)
    if a > 0:
        d = ImageDraw.Draw(frame)
        xs = x0 + pw + gap // 2
        d.line([(xs, y0 + 20), (xs, y0 + ph - 20)], fill=(255, 255, 255, int(46 * a)), width=2)

    # lower third
    a = ease_enter(t, 1.35, 0.65)
    if a > 0:
        lt = lower_third("DEMBA DIENG",
                         "Ancien directeur du Cadastre — avril 2019 à février 2023",
                         "AUDITION", name_size=52)
        paste_rgba(frame, lt, 56 + (1 - a) * -420, H - 210, a)
    draw_ticker(frame, t)
    return frame

def seg_trs(t):
    # fond : écrans de marché floutés (masque la basse résolution)
    src = kb_src(IM_TR2, 'tr2')
    frame = kb_frame(src, W, H, t, 10.4, 1.1, 1.0, 0.5, 0.5, 0.5, 0.5).convert('RGBA')
    frame = frame.filter(ImageFilter.GaussianBlur(16))
    tint = Image.new('RGBA', (W, H), (10, 22, 42, 255))
    frame = Image.blend(frame, tint, 0.62)
    paste_rgba(frame, vignette(W, H, 0.5), 0, 0)
    g = radial_glow(1000, (30, 90, 170), 60)
    paste_rgba(frame, g, 900 + int(50 * math.sin(t * 0.3)), -180)

    # carte photo insérée
    a = ease_enter(t, 0.35, 0.7)
    if a > 0:
        cw, ch = 660, 372
        src2 = kb_src(IM_TR1, 'tr1')
        card_img = kb_frame(src2, cw, ch, t, 10.4, 1.02, 1.12, 0.5, 0.45, 0.5, 0.55).convert('RGBA')
        sh = rounded(cw + 46, ch + 46, 12, (0, 0, 0, 170)).filter(ImageFilter.GaussianBlur(16))
        x, y = 120, 300
        paste_rgba(frame, sh, x - 23, y - 12 + 16, a * 0.85)
        card = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        mask = Image.new('L', (cw, ch), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, ch - 1], 8, fill=255)
        card.paste(card_img, (0, 0))
        card.putalpha(mask)
        paste_rgba(frame, card, x + int((1 - a) * -70), y, a)
        fr = rounded(cw, ch, 8, None, outline=(255, 255, 255, 80), width=2)
        paste_rgba(frame, fr, x + int((1 - a) * -70), y, a)

    # bloc titre droit
    x = 880
    a = ease_enter(t, 0.55, 0.6)
    if a > 0:
        fnt = F('Oswald', 500, 30)
        ki = text_img("MÉCANISMES FINANCIERS", fnt, GOLD + (255,), tracking=5)
        paste_rgba(frame, ki, x, 268 + (1 - a) * 26, a)
        accent_line(frame, x, 318, 300 * ease_enter(t, 0.7, 0.6, ease_out_quint), 4, RED, 1)

    for line, delay, size in [("TOTAL RETURN", 0.85, 96), ("SWAP (TRS)", 1.02, 96)]:
        a = ease_enter(t, delay, 0.75)
        if a <= 0: continue
        fnt = F('Oswald', 700, size)
        ti = text_img(line, fnt, WHITE + (255,) if "SWAP" not in line else GOLD + (255,))
        paste_rgba(frame, ti, x, 344 + (0 if line.startswith("TOTAL") else 100) + (1 - a) * 40, a)

    a = ease_enter(t, 1.3, 0.7)
    if a > 0:
        fnt = F('Inter', 400, 33)
        for i, ln in enumerate(["La commission examine le recours de l’État",
                                "à ces montages financiers"]):
            ti = text_img(ln, fnt, (206, 220, 236, 255))
            paste_rgba(frame, ti, x, 566 + i * 46 + (1 - a) * 22, a)

    # mini graphique animé (secondaire)
    a = seg(t, 1.9, 4.2)
    if a > 0:
        gx, gy, gw, gh = x, 700, 560, 120
        pts = [0.25, 0.32, 0.28, 0.42, 0.38, 0.55, 0.48, 0.62, 0.72, 0.68, 0.85]
        d = ImageDraw.Draw(frame)
        n_vis = max(2, int(a * (len(pts) - 1)) + 1)
        coords = []
        for i in range(n_vis):
            px = gx + int(gw * i / (len(pts) - 1))
            py = gy + int(gh * (1 - pts[i]))
            coords.append((px, py))
        if len(coords) >= 2:
            d.line(coords, fill=GOLD + (230,), width=4, joint='curve')
            lx, ly = coords[-1]
            d.ellipse([lx - 7, ly - 7, lx + 7, ly + 7], fill=RED + (255,))
        d.line([(gx, gy + gh + 16), (gx + gw, gy + gh + 16)], fill=(255, 255, 255, 40), width=1)

    a = ease_enter(t, 1.15, 0.65)
    if a > 0:
        lt = lower_third("AMADOU TIDIANE GAYE",
                         "Directeur général de la Comptabilité publique et du Trésor",
                         "AUDITION", name_size=52)
        paste_rgba(frame, lt, 56 + (1 - a) * -420, H - 210, a)
    draw_ticker(frame, t)
    return frame

def seg_enjeu(t):
    src = kb_src(IM_AN2, 'an2')
    frame = kb_frame(src, W, H, t, 10.4, 1.16, 1.02, 0.55, 0.45, 0.45, 0.5).convert('RGBA')
    # scrim directionnel gauche→droite
    grad = linear_grad(W, H, INK, INK, vertical=False)
    arr = np.array(grad)
    ramp = np.clip(np.linspace(232, 24, W), 0, 255).astype(np.uint8)
    arr[..., 3] = ramp[None, :]
    paste_rgba(frame, Image.fromarray(arr, 'RGBA'), 0, 0)
    paste_rgba(frame, vignette(W, H, 0.42), 0, 0)
    paste_rgba(frame, scrim_bottom(1920, 240, 120, 0), 0, 0)
    top_bar(frame, t)

    a = ease_enter(t, 0.35, 0.6)
    if a > 0:
        fnt = F('Oswald', 500, 30)
        ki = text_img("POURQUOI C’EST IMPORTANT", fnt, (24, 30, 42, 255), tracking=4)
        pill = rounded(ki.size[0] + 50, 56, 8, GOLD + (255,))
        paste_rgba(frame, pill, 110 + int((1 - a) * -60), 250, a)
        paste_rgba(frame, ki, 135 + int((1 - a) * -60), 262, a)

    cards = [
        ("TRANSPARENCE", "dans la gestion des ressources publiques", 0.75),
        ("RESPONSABILITÉ", "des institutions et des décideurs publics", 0.95),
    ]
    for title, sub, delay in cards:
        a = ease_enter(t, delay, 0.7)
        if a <= 0: continue
        cw2, ch2 = 860, 170
        card = rounded(cw2, ch2, 12, (14, 24, 42, 218), outline=(255, 255, 255, 46), width=1)
        y = 356 + (0 if title == "TRANSPARENCE" else 200)
        x = 110 + int((1 - a) * 90)
        paste_rgba(frame, card, x, y, a)
        d = ImageDraw.Draw(frame)
        d.rectangle([x, y + 26, x + 7, y + ch2 - 26], fill=RED + (int(255 * a),))
        ft = F('Oswald', 600, 52)
        fs = F('Inter', 400, 30)
        t1 = text_img(title, ft, WHITE + (255,), tracking=2)
        t2 = text_img(sub, fs, MUTED + (255,))
        paste_rgba(frame, t1, x + 40, y + 30, a)
        paste_rgba(frame, t2, x + 40, y + 98, a)

    a = ease_enter(t, 1.35, 0.65)
    if a > 0:
        lt = lower_third("CE QUE CHERCHENT LES DÉPUTÉS",
                         "Éclairer les responsabilités et les conditions de gestion publique",
                         "ENJEU", name_size=44)
        paste_rgba(frame, lt, 56 + (1 - a) * -420, H - 210, a)
    draw_ticker(frame, t)
    return frame

def seg_outro(t):
    frame = bg_intro_frame(6.4 - t * 0.9, zoom0=1.02, zoom1=1.0, px0=0.52, px1=0.5)
    a = ease_enter(t, 0.35, 0.8)
    if a > 0:
        fnt = F('Oswald', 500, 30)
        ki = text_img("ASSEMBLÉE NATIONALE — SÉNÉGAL", fnt, GOLD + (255,), tracking=6)
        paste_rgba(frame, ki, (W - ki.size[0]) // 2, 300 + (1 - a) * -30, a)
    a = ease_enter(t, 0.55, 0.85)
    if a > 0:
        fnt = F('Oswald', 700, 92)
        ti = text_img("ENQUÊTES PARLEMENTAIRES", fnt, WHITE + (255,), tracking=3)
        paste_rgba(frame, ti, (W - ti.size[0]) // 2, 366 + (1 - a) * 36, a)
        aw = ease_enter(t, 1.1, 0.7, ease_out_quint)
        if aw > 0:
            accent_line(frame, (W - int(420 * aw)) // 2, 500, 420 * aw, 5, RED, 1)
    a = ease_enter(t, 1.5, 0.8)
    if a > 0:
        fnt = F('Inter', 400, 34)
        ti = text_img("Politique nationale  —  Source : Seneweb", fnt, (200, 214, 230, 255))
        paste_rgba(frame, ti, (W - ti.size[0]) // 2, 540 + (1 - a) * 22, a)
    d = ImageDraw.Draw(frame)
    d.rectangle([0, 0, 12, H], fill=(205, 52, 60, 216))
    d.rectangle([12, 0, 18, H], fill=(232, 186, 78, 140))
    return frame

# ---------------------------------------------------------------- timeline ---
SEGS = [
    (0.0,  6.0,  seg_intro),
    (6.0,  15.0, seg_an),
    (15.0, 25.0, seg_duplex),
    (25.0, 35.0, seg_trs),
    (35.0, 45.0, seg_enjeu),
    (45.0, DUR,  seg_outro),
]

def render_frame(t):
    t = max(0.0, min(DUR - 1e-3, t))
    frame = None
    for i, (a, b, fn) in enumerate(SEGS):
        if a <= t < b:
            frame = fn(t - a)
            if t >= b - XFADE and i + 1 < len(SEGS):
                na, nb, nfn = SEGS[i + 1]
                p = ease_in_out((t - (b - XFADE)) / XFADE)
                nf = nfn(t - b + XFADE)
                frame = Image.blend(frame, nf, p)
            break
    if frame is None:
        frame = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    # fondus d'ouverture / fermeture
    if t < 0.5:
        f = 1 - t / 0.5
        frame = ImageEnhance.Brightness(frame).enhance(1 - f * 0.92)
    if t > DUR - 1.15:
        f = (t - (DUR - 1.15)) / 1.15
        frame = ImageEnhance.Brightness(frame).enhance(max(0.0, 1 - f * 1.0))
    return frame.convert('RGB')

# ------------------------------------------------------------------- audio ---
def build_audio():
    n = int(DUR * SR)
    t = np.arange(n) / SR

    # nappe ambiante (grave + quinte + octave, LFO lents)
    bed = (0.030 * np.sin(2 * np.pi * 55 * t) +
           0.024 * np.sin(2 * np.pi * 110 * t) * (1 + 0.25 * np.sin(2 * np.pi * 0.08 * t)) +
           0.018 * np.sin(2 * np.pi * 164.81 * t) * (1 + 0.3 * np.sin(2 * np.pi * 0.055 * t + 1.2)) +
           0.014 * np.sin(2 * np.pi * 220 * t) * (1 + 0.22 * np.sin(2 * np.pi * 0.07 * t + 0.4)))
    air = np.convolve(np.random.randn(n), np.ones(48) / 48, mode='same') * 0.010
    bed = bed + air

    def load_mp3(path):
        raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                             capture_output=True, check=True).stdout
        v = np.frombuffer(raw, dtype=np.float32).copy()
        m = np.abs(v).max()
        if m > 0:
            v *= 0.88 / m
        return v

    vo1 = load_mp3(os.path.join(ROOT, 'audio', 'vo-off-1.mp3'))
    vo2 = load_mp3(os.path.join(ROOT, 'audio', 'vo-off-2.mp3'))
    VO_START = [1.2, 36.5]
    vo_bus = np.zeros(n, dtype=np.float64)
    for v, s in zip((vo1, vo2), VO_START):
        i0 = int(s * SR)
        i1 = min(n, i0 + len(v))
        vo_bus[i0:i1] += v[:i1 - i0] * 1.0

    # ducking de la nappe sous la voix
    env = np.abs(vo_bus)
    k = int(0.22 * SR)
    env = np.convolve(env, np.ones(k) / k, mode='same')
    duck = 1.0 - 0.62 * np.clip(env * 5.5, 0, 1)
    bed = bed * duck

    # whooshes de transition
    def whoosh(dur=1.0, f0=880, f1=180, gain=0.16):
        m = int(dur * SR)
        tt = np.arange(m) / SR
        noise = np.convolve(np.random.randn(m), np.ones(6) / 6, mode='same')
        envw = np.exp(-tt * 3.2) * np.minimum(tt * 26, 1.0)
        f = f1 + (f0 - f1) * np.exp(-tt * 4.5)
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
        return (0.55 * noise + 0.3 * tone) * envw * gain

    fx = np.zeros(n)
    for b in [6.0, 15.0, 25.0, 35.0, 45.0]:
        w = whoosh(1.1)
        i0 = max(0, int((b - 0.28) * SR))
        i1 = min(n, i0 + len(w))
        fx[i0:i1] += w[:i1 - i0]

    # sting d'ouverture (titre)
    m = int(1.8 * SR)
    tt = np.arange(m) / SR
    boom = (np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 3.0) * 0.32 +
            np.sin(2 * np.pi * 78 * tt) * np.exp(-tt * 4.2) * 0.16 +
            np.sin(2 * np.pi * 1560 * tt) * np.exp(-tt * 7.0) * 0.045)
    i0 = int(0.62 * SR)
    i1 = min(n, i0 + m)
    fx[i0:i1] += boom[:i1 - i0]

    mix = bed * 1.0 + vo_bus * 1.05 + fx
    # léger clip doux + normalisation
    mix = np.tanh(mix * 1.25) * 0.82
    peak = np.abs(mix).max()
    if peak > 0:
        mix *= 0.94 / peak

    # stéréo légèrement décorrelée
    d1 = int(0.011 * SR)
    d2 = int(0.019 * SR)
    left = 0.86 * mix + 0.14 * np.concatenate([np.zeros(d1), mix[:-d1]])
    right = 0.86 * mix + 0.14 * np.concatenate([np.zeros(d2), mix[:-d2]])
    stereo = np.stack([left, right], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

    path = os.path.join(ROOT, 'audio', 'master.wav')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path

# -------------------------------------------------------------------- main ---
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
    if mode == 'still':
        t = float(sys.argv[2])
        img = render_frame(t)
        out = os.path.join(ROOT, 'videos', f'still-{t}.png')
        img.save(out)
        print('OK', out)
        return

    print('Rendu vidéo…')
    tmp = os.path.join(ROOT, 'videos', 'video-silent.mp4')
    cmd = [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    total = int(DUR * FPS)

    def _worker(i):
        return render_frame(i / FPS).tobytes()

    workers = max(1, min(8, os.cpu_count() or 2))
    print(f'  {total} frames, {workers} workers')
    try:
        from multiprocessing import Pool
        with Pool(processes=workers) as pool:
            for i, buf in enumerate(pool.imap(_worker, range(total), chunksize=4)):
                proc.stdin.write(buf)
                if i % 150 == 0:
                    print(f'  frame {i}/{total}')
    except Exception:
        for i in range(total):
            proc.stdin.write(_worker(i))
            if i % 150 == 0:
                print(f'  frame {i}/{total}')
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        sys.exit('ffmpeg video failed')
    print('Mix audio…')
    wav = build_audio()
    out = os.path.join(ROOT, 'videos', 'enquetes-parlementaires.mp4')
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', wav,
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', out], check=True)
    print('OK', out)

if __name__ == '__main__':
    main()
