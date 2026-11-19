"""« LFR 2026 : entrée en vigueur par décret » — reportage 16:9 (1:32).
SNGAL INFOS + logo. Sans journaliste (voix off seule).
TIMING EXACT : voix dès 0,15 s · écarts 0,5 s · son jusqu'à la dernière image.
Run: pytools/bin/python tools/render_lfr2_16x9.py
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

W, H, FPS = 1280, 720, 24
DUR = 92.5

C_BG = (7, 13, 22)
C_PANEL = (15, 23, 34)
C_PANEL2 = (23, 33, 46)
C_LINE = (28, 41, 56)
C_TXT = (232, 238, 246)
C_MUT = (138, 154, 172)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_TEAL = (42, 184, 162)
C_STEEL = (110, 160, 220)
C_RED = (214, 64, 48)

SEGS = [
    ('intro',  0,    16.81),   # a : 0.15 -> 16.31
    ('p1', 16.81,    33.55),   # b : 16.81 -> 33.05
    ('p2', 33.55,    46.97),   # c : 33.55 -> 46.47
    ('p3', 46.97,    56.98),   # d : 46.97 -> 56.48
    ('p4', 56.98,    68.90),   # e : 56.98 -> 68.40
    ('p5', 68.90,    77.93),   # f : 68.90 -> 77.43
    ('p6', 77.93,    87.14),   # g : 77.93 -> 87.14
    ('outro', 87.14, 92.5),
]
SRC_LINE = 'Source : Présidence de la République · APS · Gouvernement du Sénégal'

_LOGO_CACHE = {}

def logo(size):
    if size not in _LOGO_CACHE:
        lg = Image.open(os.path.join(ROOT, 'assets', 'logo-sngal.png')).convert('RGBA')
        _LOGO_CACHE[size] = lg.resize((size, size), Image.LANCZOS)
    return _LOGO_CACHE[size]

def seg_at(t):
    for i, (k, t0, t1) in enumerate(SEGS):
        if t0 <= t < t1:
            return i, k, t0, t1
    return len(SEGS) - 1, SEGS[-1][0], SEGS[-1][1], SEGS[-1][2]

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
    if im.width < w * 0.72 or im.height < h * 0.72:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(22))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.32)
        sw, sh = im.size
        scale = min(w * 0.82 / sw, h * 0.82 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), (int((w - nw) * cx), int((h - nh) * cy)))
        return plate
    return cover(im, w, h)

def text(d, xy, s, f, fill, anchor=None, stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

def textw(s, f):
    return f.getbbox(s)[2]

def vsplit_bg(drift=0.0):
    img = Image.new('RGB', (W, H), C_BG)
    img.paste(Image.new('RGB', (W, H), (10, 18, 28)), (W // 2, 0))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 26):
        a = 6 + int(5 * np.sin(2 * np.pi * (y / 240 + drift)))
        d.line([(W // 2, y), (W // 2, y + 12)], fill=(a + 20, a + 32, a + 48), width=2)
    return img

def blend_to_bg(base):
    grad = Image.new('RGB', (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, H, 2):
        k = y / H
        gd.rectangle([0, y, W, y + 2], fill=(int(6 + 10 * k), int(12 + 12 * k), int(20 + 14 * k)))
    return Image.blend(base, grad, 0.45)

def dim(img, x, y, w, h, a=120):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, a))
    img.paste(ov, (x, y), ov)

def vignette(img, x, y, w, h):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(26):
        d.rectangle([i * 2, i * 2, w - i * 2, h - i * 2], outline=(0, 0, 0, int(1 + i * 0.7)))
    img.paste(ov, (x, y), ov)

def lower_third(img, kicker, headline, sub, verdict, accent, appear, caveat=None):
    d = ImageDraw.Draw(img, 'RGBA')
    y0 = 480
    h = 220
    ph = int(ease(P(appear, 0, 0.22)) * h)
    if ph > 2:
        panel = Image.new('RGBA', (W, ph), (10, 16, 26, 238))
        img.paste(panel, (0, y0), panel)
        d.line([(0, y0), (W, y0)], fill=accent + (200,), width=3)
    k1 = ease(P(appear, 0.08, 0.26))
    if k1 > 0:
        text(d, (40, y0 + 22 + (1 - k1) * 14), kicker, Inter(19, True), accent, anchor='lm')
        text(d, (W - 40, y0 + 22 + (1 - k1) * 14), 'SNGAL INFOS · POLITIQUE', Inter(17, True), C_MUT, anchor='rm')
    k2 = ease(P(appear, 0.14, 0.34))
    if k2 > 0:
        size = 44
        f = Oswald(size)
        while textw(headline, f) > W - 90 and size > 28:
            size -= 2
            f = Oswald(size)
        text(d, (40, y0 + 78 + (1 - k2) * 22), headline, f, C_TXT, stroke=2)
    k3 = ease(P(appear, 0.26, 0.5))
    if k3 > 0 and sub:
        text(d, (40, y0 + 142 + (1 - k3) * 16), sub, Inter(21), C_MUT)
    if k3 > 0 and caveat:
        text(d, (40, y0 + 172), caveat, Inter(15), C_GOLD)
    k4 = ease(P(appear, 0.34, 0.6))
    if k4 > 0:
        fw = textw(verdict, Oswald(26)) + 44
        x = int(W - 40 - fw + (1 - k4) * 30)
        badge = Image.new('RGBA', (fw, 52), accent + (int(235 * k4),))
        img.paste(badge, (x, y0 + 128), badge)
        d2 = ImageDraw.Draw(img, 'RGBA')
        text(d2, (x + fw / 2, y0 + 155), verdict, Oswald(26), (12, 16, 24), anchor='mm')

def header_bar(img):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 60], fill=(9, 15, 24, 225))
    d.line([(0, 60), (W, 60)], fill=C_LINE + (255,), width=2)
    d.rectangle([0, 0, 8, 60], fill=C_RED + (255,))
    lg = logo(44)
    img.paste(lg, (18, 8), lg)
    text(d, (72, 10), 'SNGAL INFOS', Oswald(30), (242, 246, 252), anchor='lm')
    d.rectangle([262, 12, 426, 48], fill=(178, 32, 22, 235))
    text(d, (344, 31), 'LE JOURNAL', Inter(18, True), (255, 232, 226), anchor='mm')
    text(d, (W - 26, 31), 'DAKAR · 19 NOV 2026', Inter(19, True), C_MUT, anchor='rm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 52, W, H], fill=(8, 13, 21, 235))
    d.line([(0, H - 52), (W, H - 52)], fill=C_RED + (255,), width=3)
    items = [
        'LFR 2026 : ENTRÉE EN VIGUEUR PAR DÉCRET N° 2026-2416',
        'L\'ASSEMBLÉE NATIONALE AVAIT REJETÉ LE TEXTE LE 3 NOVEMBRE',
        'COMMUNIQUÉ DE LA PRÉSIDENCE SIGNÉ PAR OUMAR SAMBA BÂ',
        'DÉCISION DU PRÉSIDENT BASSIROU DIOMAYE FAYE LE 19 NOVEMBRE',
    ]
    cycle = '     ·     '.join(items) + '     ·     '
    f = Inter(19)
    sp = textw(cycle, f)
    off = int((t * 75) % sp)
    y = H - 26
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')

def intro_scene(t):
    img = kb_src(os.path.join(ROOT, 'image-search/lfr2-p2.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 122)
    vignette(img, 0, 0, W, H)
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (64, 108), 'DÉCISION OFFICIELLE · PRÉSIDENCE DE LA RÉPUBLIQUE', Inter(20, True), C_RED, stroke=2)
    for i, line in enumerate(['LFR 2026', 'ENTRE EN VIGUEUR', 'PAR DÉCRET']):
        off = int((1 - ease(P(t, 0.1 + i * 0.1, 0.55 + i * 0.1))) * 30)
        text(d, (64 + off, 152 + i * 70), line, Oswald(68), C_TXT, stroke=2)
    p = ease(P(t, 0.7, 1.2))
    if p > 0:
        bar = Image.new('RGBA', (int(560 * p), 6), C_RED + (255,))
        img.paste(bar, (64, 392), bar)
        text(d, (64, 418), 'Deux semaines après son rejet par l\'Assemblée nationale', Inter(21), C_TXT, stroke=2)
    lower_third(img, 'POLITIQUE · BUDGET', 'DÉCRET N° 2026-2416',
                'Signé le 19 novembre 2026 par le président Diomaye Faye', 'PAR DÉCRET', C_RED,
                P(t, 0.9, 1.5), 'Source : Présidence de la République')
    header_bar(img)
    ticker(img, t)
    return img

def point_scene(kind, t, t0):
    appear = P(t - t0, 0.02, 0.3)
    drift = t / 30
    img = vsplit_bg(drift)

    def insert_image(side, path, a=135, cy=0.42):
        x, w = (0, W // 2) if side == 'l' else (W // 2, W // 2)
        if path and os.path.exists(path):
            patch = kb_src(path, w, H, cy=cy)
        else:
            patch = vsplit_bg(drift)
        dim(patch, 0, 0, w, H, a)
        img.paste(patch, (x, 0))

    imgs = {
        'p1': ('image-search/lfr2-p1.jpg', 'image-search/lfr2-p2.jpg'),
        'p2': ('image-search/lfr2-p3.jpg', 'image-search/lfr2-p4.jpg'),
        'p3': ('image-search/lfr2-p4.jpg', 'image-search/lfr2-p1.jpg'),
        'p4': ('image-search/lfr2-p2.jpg', 'image-search/lfr2-p3.jpg'),
        'p5': ('image-search/lfr2-p1.jpg', 'image-search/lfr2-p2.jpg'),
        'p6': ('image-search/lfr2-p4.jpg', 'image-search/lfr2-p5.jpg'),
    }
    lpath, rpath = imgs[kind]
    insert_image('l', lpath, a=140)
    insert_image('r', rpath, a=112, cy=0.3)

    d = ImageDraw.Draw(img, 'RGBA')
    seam = int(ease(P(t - t0, 0, 0.25)) * H)
    if seam > 2:
        d.line([(W // 2, H // 2 - seam // 2), (W // 2, H // 2 + seam // 2)], fill=C_STEEL + (170,), width=3)

    i = int(kind[1])
    circle = int(ease(P(t - t0, 0, 0.2)) * 34)
    if circle > 2:
        d.ellipse([64 - 4, 112 - 4, 64 + circle * 2 + 4, 112 + circle * 2 + 4],
                  outline=C_GOLD + (255,), width=2)
        if circle >= 33:
            text(d, (64 + 34, 112 + 34), f'{i:02d}', Oswald(40), C_GOLD, anchor='mm')

    badges = {
        'p1': ('POINT 01 · LE DÉCRET', 'DÉCRET N° 2026-2416',
               'Mise en vigueur officielle de la loi de finances rectificative 2026',
               '19 NOVEMBRE 2026', C_RED, 'Communiqué signé par Oumar Samba Bâ'),
        'p2': ('POINT 02 · CHRONOLOGIE', 'DU REJET AU DÉCRET',
               '3 novembre : rejet de l\'Assemblée · 19 novembre : le décret',
               'DU 3 AU 19 NOVEMBRE', C_STEEL, 'Seize jours'),
        'p3': ('POINT 03 · LA POLÉMIQUE', 'MALGRÉ LE REJET',
               'Un texte rejeté par les députés, remis en vigueur par décret',
               'POLÉMIQUE', C_WARM, 'Question institutionnelle'),
        'p4': ('POINT 04 · LE CONTEXTE', 'LE RÔLE DE LA LFR',
               'Elle ajuste le budget de l\'État en cours d\'année',
               'BUDGET 2026', C_STEEL, 'Recettes · dépenses · priorités'),
        'p5': ('POINT 05 · L\'APPLICATION', 'LE TEXTE S\'APPLIQUE',
               'Dès sa signature, le budget rectificatif entre en vigueur',
               'EN VIGUEUR', C_TEAL, 'Pour tout l\'exercice 2026'),
        'p6': ('POINT 06 · LA QUESTION', 'LE DÉBAT RESTE OUVERT',
               'Urgence économique ou respect de la procédure ?',
               'SNGAL INFOS', C_GOLD, None),
    }
    kicker, headline, sub, verdict, accent, caveat = badges[kind]
    lower_third(img, kicker, headline, sub, verdict, accent, appear, caveat)
    header_bar(img)
    ticker(img, t)
    return img

def outro_scene(t, t0):
    img = kb_src(os.path.join(ROOT, 'image-search/lfr2-p3.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 165)
    d = ImageDraw.Draw(img, 'RGBA')
    appear = P(t - t0, 0, 0.3)
    text(d, (640, 235), 'LFR 2026 · PAR DÉCRET', Oswald(50), C_TXT, anchor='mm')
    p = ease(appear)
    bar = Image.new('RGBA', (int(560 * p), 6), C_RED + (255,))
    img.paste(bar, (360, 288), bar)
    lines = [
        'Décret n° 2026-2416 · 19 novembre 2026',
        'Bassirou Diomaye Faye · Oumar Samba Bâ',
        'Le débat reste ouvert',
    ]
    for i, line in enumerate(lines):
        a = P(t - t0, 0.25 + i * 0.18, 0.7 + i * 0.18)
        if a > 0:
            text(d, (640, 340 + i * 44), f'—  {line}', Inter(20), C_TXT if a > 0.9 else C_MUT, anchor='mm')
    a = P(t - t0, 1.1, 1.6)
    if a > 0:
        lg = logo(56)
        img.paste(lg, (505, 500), lg)
        text(d, (685, 528), 'SNGAL INFOS', Oswald(44), C_GOLD, anchor='lm')
    text(d, (640, 600), SRC_LINE, Inter(15, True), C_MUT, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img

def frame(t):
    i, kind, t0, t1 = seg_at(t)
    if kind == 'intro':
        img = intro_scene(t)
    elif kind == 'outro':
        img = outro_scene(t, t0)
    else:
        img = point_scene(kind, t, t0)
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'lfr2-decret-16x9.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'lfr2-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.1f}s')

if __name__ == '__main__':
    main()
