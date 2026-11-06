"""« Alerte sanitaire à Kébémer » — 16:9 (2:27). SNGAL INFOS + logo.
TIMING EXACT : voix dès 0,15 s · écarts 0,5 s · son jusqu'à la dernière image.
Run: pytools/bin/python tools/render_kb_16x9.py
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
DUR = 147.0

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
    ('intro',    0,    16.90),   # a : 0.15 -> 16.40
    ('p1',   16.90,   32.76),    # b : 16.90 -> 32.26
    ('p2',   32.76,   45.97),    # c : 32.76 -> 45.47
    ('p3',   45.97,   62.28),    # d : 45.97 -> 61.78
    ('p4',   62.28,   78.40),    # e : 62.28 -> 77.90
    ('p5',   78.40,   94.12),    # f : 78.40 -> 93.62
    ('p6',   94.12,  108.35),    # g : 94.12 -> 107.85
    ('p7',  108.35,  125.60),    # h : 108.35 -> 125.10
    ('debate', 125.60, 141.0),   # i : 125.60 -> 139.33 + tableau
    ('outro', 141.0,  147.0),
]
SRC_LINE = 'Source : ministère de la Santé et de l\'Hygiène publique · presse sénégalaise'

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
        text(d, (W - 40, y0 + 22 + (1 - k1) * 14), 'SNGAL INFOS · SANTÉ', Inter(17, True), C_MUT, anchor='rm')
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
    text(d, (344, 31), 'EN DIRECT', Inter(18, True), (255, 232, 226), anchor='mm')
    text(d, (W - 26, 31), 'DAKAR · 6 NOV 2026', Inter(19, True), C_MUT, anchor='rm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 52, W, H], fill=(8, 13, 21, 235))
    d.line([(0, H - 52), (W, H - 52)], fill=C_RED + (255,), width=3)
    items = [
        'KÉBÉMER : 548 CAS DE SYNDROMES DIGESTIFS AIGUS',
        '+65 CAS EN 24 HEURES · 9 SITES DU DISTRICT',
        'ÉTAT DES PATIENTS STABLE · AUCUN DÉCÈS',
        'PISTE : TOXI-INFECTION ALIMENTAIRE OU HYDRIQUE',
        'SAMU : 1515',
    ]
    cycle = '     ·     '.join(items) + '     ·     '
    f = Inter(19)
    sp = textw(cycle, f)
    off = int((t * 75) % sp)
    y = H - 26
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')

def intro_scene(t):
    img = kb_src(os.path.join(ROOT, 'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-4.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 112)
    vignette(img, 0, 0, W, H)
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (64, 108), 'SANTÉ · RÉGION DE LOUGA · KÉBÉMER', Inter(20, True), C_RED, stroke=2)
    for i, line in enumerate(['ALERTE', 'SANITAIRE', 'À KÉBÉMER']):
        off = int((1 - ease(P(t, 0.1 + i * 0.1, 0.55 + i * 0.1))) * 30)
        text(d, (64 + off, 152 + i * 70), line, Oswald(68), C_TXT, stroke=2)
    p = ease(P(t, 0.7, 1.2))
    if p > 0:
        bar = Image.new('RGBA', (int(560 * p), 6), C_RED + (255,))
        img.paste(bar, (64, 392), bar)
        text(d, (64, 418), '548 cas de syndromes digestifs aigus en quelques jours', Inter(21), C_TXT, stroke=2)
    lower_third(img, 'URGENCE · SANTÉ PUBLIQUE', '548 CAS EN QUELQUES JOURS',
                'Une flambée qui inquiète fortement les populations', 'ALERTE', C_RED,
                P(t, 0.9, 1.5))
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
        'p1': ('image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-1.jpg',
               'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-3.png'),
        'p2': ('image-search/h-pital-patients-soins-sant-s-n-gal-infi-1.png',
               'image-search/h-pital-soins-sant-s-n-gal-personnel-soi-1.jpg'),
        'p3': ('image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-3.png',
               'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-2.jpg'),
        'p4': ('image-search/h-pital-patients-soins-sant-s-n-gal-infi-3.jpg',
               'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-4.jpg'),
        'p5': ('image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-1.jpg',
               'image-search/h-pital-patients-soins-sant-s-n-gal-infi-2.png'),
        'p6': ('image-search/h-pital-patients-soins-sant-s-n-gal-infi-4.jpg',
               'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-2.jpg'),
        'p7': ('image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-3.png',
               'image-search/h-pital-patients-soins-sant-s-n-gal-infi-1.png'),
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
        'p1': ('POINT 01 · BILAN OFFICIEL', '548 CAS, DONT 65 EN 24 HEURES',
               'Neuf sites distincts du district sanitaire de Kébémer',
               '548 CAS', C_RED, 'MSHP · 6 novembre, 10 h 30'),
        'p2': ('POINT 02 · ÉTAT DES PATIENTS', 'LEUR ÉTAT EST STABLE',
               '3 personnes sous observation · aucun cas grave ni décès',
               'RASSURANT', C_TEAL, None),
        'p3': ('POINT 03 · RECTIFICATIF', 'DES RUMEURS DÉMENTIES',
               '56 cas les premiers jours · chiffres alarmants corrigés',
               'OFFICIEL', C_STEEL, 'Ministère de la Santé'),
        'p4': ('POINT 04 · LES SYMPTÔMES', 'DIARRHÉES, VOMISSEMENTS, FIÈVRE',
               'Syndromes digestifs aigus · piste TIAC à confirmer',
               'TIAC', C_WARM, 'Piste à confirmer'),
        'p5': ('POINT 05 · ENQUÊTE', 'LA SOURCE COMMUNE RECHERCHÉE',
               'Louga + Prévention · COUS & Institut Pasteur de Dakar',
               'RECHERCHE', C_GOLD, None),
        'p6': ('POINT 06 · LA PISTE', 'ALIMENTAIRE OU HYDRIQUE ?',
               'Eau ou aliments contaminés · analyses en cours',
               'À CONFIRMER', C_WARM, 'Investigations en cours'),
        'p7': ('POINT 07 · CONSIGNES', 'HYGIÈNE ET VIGILANCE',
               'Consulter sans tarder en cas de symptômes · SAMU : 1515',
               'SAMU 1515', C_GOLD, 'Diarrhées · vomissements · fièvre'),
    }
    kicker, headline, sub, verdict, accent, caveat = badges[kind]
    lower_third(img, kicker, headline, sub, verdict, accent, appear, caveat)
    header_bar(img)
    ticker(img, t)
    return img

def debate_scene(t, t0):
    img = vsplit_bg(t / 26)
    d = ImageDraw.Draw(img, 'RGBA')
    card = Image.new('RGBA', (W, 570), (11, 18, 29, 218))
    img.paste(card, (0, 76), card)

    def panel(x, w, name, role, side, appear):
        ph = int(ease(appear) * 290)
        if ph < 2:
            return
        panel_img = Image.new('RGBA', (w, ph), C_PANEL + (255,))
        img.paste(panel_img, (x, 150))
        d.rectangle([x, 150, x + w - 1, 150 + ph - 1], outline=C_LINE + (255,), width=2)
        head = Image.new('RGBA', (w, 44), (side + (255,)))
        img.paste(head, (x, 150), head)
        text(d, (x + 14, 172), name, Oswald(26), (12, 16, 24), anchor='lm')
        text(d, (x + 14, 208), role, Inter(16, True), C_MUT)

    p1 = ease(P(t - t0, 0.1, 0.5))
    p2 = ease(P(t - t0, 0.45, 0.9))
    panel(60, 540, 'POPULATIONS', 'KÉBÉMER · NEUF SITES TOUCHÉS', C_STEEL, p1)
    panel(680, 540, 'AUTORITÉS SANITAIRES', 'MSHP · LOUGA · PRÉVENTION · COUS', C_WARM, p2)

    cd = ease(P(t - t0, 1.0, 1.5))
    if cd > 0:
        b = Image.new('RGBA', (92, 52), C_RED + (int(255 * cd),))
        img.paste(b, (594, 269), b)
        text(d, (640, 296), 'VS', Oswald(32), (255, 242, 238), anchor='mm')

    def chip(x, y, w, label, appear, accent):
        a = ease(appear)
        if a <= 0:
            return
        ch = Image.new('RGBA', (w, 72), C_PANEL2 + (int(255 * a),))
        img.paste(ch, (x, y), ch)
        d.rectangle([x, y, x + w - 1, y + 71], outline=C_LINE + (int(255 * a),), width=2)
        d.rectangle([x, y, x + 6, y + 71], fill=accent + (int(255 * a),))
        text(d, (x + 22, y + 36), label, Inter(19, True), (222, 230, 240), anchor='lm')

    chip(60, 452, 540, 'Hygiène alimentaire et hydrique', P(t - t0, 1.4, 1.8), C_TEAL)
    chip(680, 452, 540, 'Source commune recherchée', P(t - t0, 1.6, 2.0), C_WARM)
    chip(60, 532, 540, 'Symptômes : consulter sans tarder', P(t - t0, 1.9, 2.3), C_GOLD)
    chip(680, 532, 540, 'SAMU : 1515', P(t - t0, 2.1, 2.5), C_RED)

    text(d, (640, 100), 'LE DÉBAT', Oswald(34), C_TXT, anchor='mm')
    text(d, (640, 132), 'Quelle est l\'origine exacte de cette contamination ?', Inter(18), C_MUT, anchor='mm')

    ys = ease(P(t - t0, 3.2, 3.9))
    if ys > 0:
        sc = Image.new('RGBA', (1160, 50), (22, 32, 46, int(240 * ys)))
        img.paste(sc, (60, 606), sc)
        d.rectangle([60, 606, 1219, 655], outline=C_GOLD + (int(220 * ys),), width=2)
        text(d, (80, 631), 'SYNTHÈSE · Les résultats des analyses (COUS, Institut Pasteur) sont attendus. Vigilance maintenue.',
             Inter(17, True), (232, 236, 244), anchor='lm')

    text(d, (640, 660), SRC_LINE, Inter(13, True), C_MUT, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img

def outro_scene(t, t0):
    img = vsplit_bg(t / 22)
    img = blend_to_bg(img)
    d = ImageDraw.Draw(img, 'RGBA')
    appear = P(t - t0, 0, 0.3)
    text(d, (640, 235), 'KÉBÉMER · 548 CAS · AUCUN DÉCÈS', Oswald(50), C_TXT, anchor='mm')
    p = ease(appear)
    bar = Image.new('RGBA', (int(560 * p), 6), C_RED + (255,))
    img.paste(bar, (360, 288), bar)
    lines = [
        'Syndrome digestif aigu · piste TIAC à confirmer',
        '9 sites du district de Louga · état stable',
        'Enquête et analyses en cours',
        'Vigilance et hygiène · SAMU : 1515',
    ]
    for i, line in enumerate(lines):
        a = P(t - t0, 0.15 + i * 0.16, 0.5 + i * 0.16)
        if a > 0:
            text(d, (640, 330 + i * 42), f'—  {line}', Inter(20), C_TXT if a > 0.9 else C_MUT, anchor='mm')
    a = P(t - t0, 1.2, 1.7)
    if a > 0:
        lg = logo(56)
        img.paste(lg, (505, 535), lg)
        text(d, (685, 563), 'SNGAL INFOS', Oswald(44), C_GOLD, anchor='lm')
    text(d, (640, 630), 'Santé publique · SNGAL INFOS', Inter(18, True), C_GOLD, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img

def frame(t):
    i, kind, t0, t1 = seg_at(t)
    if kind == 'intro':
        img = intro_scene(t - t0)
    elif kind.startswith('p'):
        img = point_scene(kind, t, t0)
    elif kind == 'debate':
        img = debate_scene(t, t0)
    else:
        img = outro_scene(t, t0)
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'kebemer-alerte-16x9.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'kb-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.0f}s')

if __name__ == '__main__':
    main()
