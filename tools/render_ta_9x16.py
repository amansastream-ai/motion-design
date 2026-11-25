"""« TAS : le Sénégal conserve son titre 2025 » — Short vertical 9:16 (1:45).
6 segments · voice-02 · plateaux fiches · SNGAL INFOS + logo · Source : Afrik+1.
Run: pytools/bin/python tools/render_ta_9x16.py
"""
import os
import sys
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FDIR = os.path.join(ROOT, 'assets', 'fonts')
Oswald = lambda s: ImageFont.truetype(os.path.join(FDIR, 'Oswald-700.ttf'), s)
Inter = lambda s, b=False: ImageFont.truetype(
    os.path.join(FDIR, 'Inter-600.ttf' if b else 'Inter-400.ttf'), s)

W, H, FPS = 1080, 1920, 24
DUR = 105.0

C_BG = (7, 13, 22)
C_PANEL = (14, 21, 32)
C_LINE = (30, 42, 58)
C_TXT = (238, 242, 248)
C_MUT = (148, 162, 178)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_TEAL = (42, 184, 162)
C_STEEL = (110, 160, 220)
C_RED = (214, 64, 48)

SEGS = [
    ('intro', 0.0,  19.0),
    ('j1',   19.0,  32.0),
    ('j2',   32.0,  45.0),
    ('j3',   45.0,  60.0),
    ('j4',   60.0,  73.0),
    ('j5',   73.0,  90.0),
    ('outro', 90.0, 105.0),
]
VERBATIM = 'SOURCE : AFRIK+1 · DÉCISION DU TAS · 24 NOVEMBRE 2026'

PLATS = {
    'intro': (13.7, 'CE QUE DIT LA DÉCISION',
              ['Forfait CAF annulé', 'Finale 1-0 rétablie', 'Titre 2025 conservé'], C_GOLD),
    'j1': (27.8, 'LAUSANNE · 24 NOV',
           ['Le TAS tranche', 'Favorable au Sénégal', 'Face à la CAF et au Maroc'], C_STEEL),
    'j2': (39.1, 'FINALE RÉTABLIE',
           ['1-0 après prolongation', 'Le résultat tient', 'Score rétabli'], C_GOLD),
    'j3': (55.4, 'LE LITIGE',
           ['FSF face à la CAF', 'Et au Maroc', 'La décision fait référence'], C_RED),
    'j4': (68.2, 'LE TAS EN BREF',
           ['Instance du sport mondial', 'Basée à Lausanne', 'Sentences contraignantes'], C_STEEL),
    'j5': (81.3, 'QUESTIONS OUVERTES',
           ['Réactions de la CAF ?', 'Et le Maroc ?', 'La suite du feuilleton ?'], C_TEAL),
}

_LOGO_CACHE = {}

def logo(size):
    if size not in _LOGO_CACHE:
        lg = Image.open(os.path.join(ROOT, 'assets', 'logo-sngal.png')).convert('RGBA')
        _LOGO_CACHE[size] = lg.resize((size, size), Image.LANCZOS)
    return _LOGO_CACHE[size]

def seg_at(t):
    for k, t0, t1 in SEGS:
        if t0 <= t < t1:
            return k, t0, t1
    return SEGS[-1]

def P(v, a, b):
    return max(0.0, min(1.0, (v - a) / (b - a))) if a != b else 1.0

def ease(p):
    return 1 - (1 - p) ** 3

def cover(img, w, h):
    im = img.convert('RGB')
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * 0.38)
    return im.crop((x, y, x + w, y + h))

def kb_src(path, w, h, cx=0.5, cy=0.42):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.62 or im.height < h * 0.62:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(24))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.30)
        sw, sh = im.size
        scale = min(w * 0.9 / sw, h * 0.9 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), (int((w - nw) * cx), int((h - nh) * cy)))
        return plate
    return cover(im, w, h)

def text(d, xy, s, f, fill, anchor=None, stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

def textw(s, f):
    return f.getbbox(s)[2]

def blend_to_bg(base):
    grad = Image.new('RGB', (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, H, 2):
        k = y / H
        gd.rectangle([0, y, W, y + 2], fill=(int(6 + 10 * k), int(12 + 12 * k), int(20 + 14 * k)))
    return Image.blend(base, grad, 0.42)

def dim(img, x, y, w, h, a=120):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, a))
    img.paste(ov, (x, y), ov)

def vignette(img, x, y, w, h):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(26):
        d.rectangle([i * 2, i * 2, w - i * 2, h - i * 2], outline=(0, 0, 0, int(1 + i * 0.7)))
    img.paste(ov, (x, y), ov)

def bottom_verbatim(img):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 96, W, H], fill=(6, 10, 17, 240))
    d.line([(0, H - 96), (W, H - 96)], fill=C_GOLD + (255,), width=3)
    text(d, (W / 2, H - 48), VERBATIM, Inter(20), (216, 226, 238), anchor='mm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 150, W, H - 96], fill=(8, 13, 21, 235))
    d.line([(0, H - 150), (W, H - 150)], fill=C_GOLD + (255,), width=3)
    cycle = '   ·   '.join([
        'LE TAS ANNULE LE FORFAIT DE LA CAF',
        'SÉNÉGAL 1-0 APRÈS PROLONGATION · RÉTABLI',
        'CHAMPION D\'AFRIQUE 2025',
    ]) + '   ·   '
    f = Oswald(26)
    sp = textw(cycle, f)
    off = int((t * 90) % sp)
    y = H - 123
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')

def header_bar(img):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 140], fill=(9, 15, 24, 235))
    d.line([(0, 140), (W, 140)], fill=C_LINE + (255,), width=2)
    d.rectangle([0, 0, 12, 140], fill=C_GOLD + (255,))
    lg = logo(88)
    img.paste(lg, (30, 26), lg)
    text(d, (132, 46), 'SNGAL INFOS', Oswald(52), (242, 246, 252), anchor='lm')
    text(d, (132, 108), 'SPORT · TAS · 24 NOV 2026', Inter(22, True), C_GOLD, anchor='lm')

def plateau_v(img, t, spec):
    if spec is None:
        return
    t0, title, lines, accent = spec
    a = ease(P(t, t0, t0 + 0.45))
    if a <= 0:
        return
    d = ImageDraw.Draw(img, 'RGBA')
    x0, y0, x1, y1 = 90, 1120, W - 90, 1560
    card = Image.new('RGBA', (x1 - x0, y1 - y0), (11, 18, 29, int(238 * a)))
    img.paste(card, (x0, y0), card)
    d.rectangle([x0, y0, x1, y1], outline=C_LINE + (int(255 * a),), width=3)
    d.rectangle([x0, y0, x0 + 12, y1], fill=accent + (int(255 * a),))
    at = ease(P(t, t0 + 0.1, t0 + 0.6))
    if at > 0:
        text(d, (x0 + 44, y0 + 62), title, Oswald(52), accent, anchor='lm')
        bar = Image.new('RGBA', (int(660 * at), 6), accent + (255,))
        img.paste(bar, (x0 + 44, y0 + 112), bar)
    for i, line in enumerate(lines):
        al = ease(P(t, t0 + 0.55 + i * 0.4, t0 + 1.05 + i * 0.4))
        if al > 0:
            text(d, (x0 + 44 + (1 - al) * 26, y0 + 160 + i * 84), line, Inter(34),
                 C_TXT if al > 0.85 else C_MUT)
            d.ellipse([x0 + 20, y0 + 172 + i * 84, x0 + 38, y0 + 190 + i * 84],
                      fill=accent + (int(255 * al),))

def story_card(kind, path, lines, kicker, accent, t, t0):
    img = kb_src(path, W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 128)
    vignette(img, 0, 0, W, H)
    d = ImageDraw.Draw(img, 'RGBA')
    ph = int(ease(P(t - t0, 0, 0.22)) * 150)
    if ph > 2:
        panel = Image.new('RGBA', (W, ph), (8, 13, 21, 235))
        img.paste(panel, (0, 180), panel)
        d.rectangle([60, 180, 132, 180 + ph], fill=accent + (255,))
        text(d, (60, 252), kicker, Inter(24, True), (232, 238, 246), anchor='lm')
    k1 = ease(P(t - t0, 0.12, 0.34))
    if k1 > 0:
        text(d, (60 + (1 - k1) * 24, 420), lines[0], Oswald(72), C_TXT, stroke=2)
    k2 = ease(P(t - t0, 0.22, 0.48))
    if k2 > 0:
        text(d, (60 + (1 - k2) * 24, 520), lines[1], Oswald(72), accent, stroke=2)
    k3 = ease(P(t - t0, 0.42, 0.7))
    if k3 > 0:
        bar = Image.new('RGBA', (int(660 * k3), 8), accent + (255,))
        img.paste(bar, (60, 660), bar)
        if k3 > 0.5:
            text(d, (60, 700), 'Le titre 2025 reste aux Lions.', Inter(28), C_TXT, anchor='lm')
            text(d, (60, 742), 'La décision du TAS fait foi.', Inter(28), C_TXT, anchor='lm')
    plateau_v(img, t, PLATS.get(kind))
    header_bar(img)
    ticker(img, t)
    bottom_verbatim(img)
    return img

CARDS = {
    'intro': dict(img='image-search/ta-lions-trophee.jpg',
                  lines=['LE SÉNÉGAL', 'CONSERVE SON TITRE'], kicker='TAS · 24 NOVEMBRE', accent=C_GOLD),
    'j1': dict(img='image-search/ta-lausanne.jpg',
               lines=['LE TAS', 'TRANCHE À LAUSANNE'], kicker='LA DÉCISION', accent=C_STEEL),
    'j2': dict(img='image-search/ta-lions-trophee.jpg',
               lines=['FINALE 1-0', 'RÉTABLIE'], kicker='LA FINALE', accent=C_GOLD),
    'j3': dict(img='image-search/ta-lions-parade.jpg',
               lines=['FACE À LA CAF', 'ET AU MAROC'], kicker='LE LITIGE', accent=C_RED),
    'j4': dict(img='image-search/ta-lausanne.jpg',
               lines=['CE QU\'EST', 'LE TAS'], kicker='LE CADRE', accent=C_STEEL),
    'j5': dict(img='image-search/ta-lions-parade.jpg',
               lines=['LA SUITE', 'DU FEUILLETON'], kicker='EN SUSPENS', accent=C_TEAL),
}

def outro_card(t, t0):
    img = kb_src(os.path.join(ROOT, 'image-search/ta-lions-parade.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 155)
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (W / 2, 620), 'CHAMPION', Oswald(72), C_TXT, anchor='mm')
    text(d, (W / 2, 720), "D'AFRIQUE 2025", Oswald(72), C_GOLD, anchor='mm')
    p = ease(P(t - t0, 0, 0.3))
    bar = Image.new('RGBA', (int(660 * p), 8), C_GOLD + (255,))
    img.paste(bar, ((W - 660) // 2, 800), bar)
    text(d, (W / 2, 880), 'Le titre reste aux Lions', Inter(30), C_TXT, anchor='mm')
    a = P(t - t0, 1.2, 2.0)
    if a > 0:
        lg = logo(120)
        img.paste(lg, (W // 2 - 170, 990), lg)
        text(d, (W / 2 + 10, 1055), 'SNGAL INFOS', Oswald(64), C_GOLD, anchor='lm')
    text(d, (W / 2, 1140), 'Source : Afrik+1 · décision du TAS', Inter(26, True), C_MUT, anchor='mm')
    header_bar(img)
    ticker(img, t)
    bottom_verbatim(img)
    return img

def frame(t):
    kind, t0, t1 = seg_at(t)
    if kind == 'outro':
        return outro_card(t, t0)
    c = CARDS[kind]
    return story_card(kind, os.path.join(ROOT, c['img']), c['lines'], c['kicker'],
                      c['accent'], t, t0)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'tas-titre-2025-9x16.mp4')
    tmp = out + '.tmp.mp4'
    proc = imageio_ffmpeg.write_frames(
        tmp, (W, H), pix_fmt_in='rgb24', fps=FPS, codec='libx264', quality=None,
        macro_block_size=1, ffmpeg_log_level='error',
        output_params=['-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
    proc.send(None)
    n = int(DUR * FPS)
    for fi in range(n):
        proc.send(np.asarray(frame(fi / FPS), dtype=np.uint8))
        if fi % (FPS * 25) == 0:
            print(f'  frame {fi}/{n}')
    proc.close()
    import subprocess
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'ta-short-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.1f}s')

if __name__ == '__main__':
    main()
