"""« Naufrage au large de Kébémer — 34 morts » — 16:9 (2:06). SNGAL INFOS + logo.
TIMING EXACT : voix dès 0,15 s · écarts 0,5 s · son jusqu'à la dernière image.
Run: pytools/bin/python tools/render_nk_16x9.py
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
DUR = 126.5

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
    ('intro',    0,    13.65),   # a : 0.15 -> 13.15
    ('p1',   13.65,   25.28),   # b : 13.65 -> 24.78
    ('p2',   25.28,   38.91),   # c : 25.28 -> 38.41
    ('p3',   38.91,   50.11),   # d : 38.91 -> 49.61
    ('p4',   50.11,   61.23),   # e : 50.11 -> 60.73
    ('p5',   61.23,   72.26),   # f : 61.23 -> 71.76
    ('p6',   72.26,   84.36),   # g : 72.26 -> 83.86
    ('p7',   84.36,   95.87),   # h : 84.36 -> 95.37
    ('debate', 95.87, 117.5),   # i : 95.87 -> 105.81 + tableau
    ('outro', 117.5,  126.5),
]
SRC_LINE = 'Source : APS · AP · presse sénégalaise'

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
        text(d, (W - 40, y0 + 22 + (1 - k1) * 14), 'SNGAL INFOS · FAITS DIVERS', Inter(17, True), C_MUT, anchor='rm')
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
    text(d, (W - 26, 31), 'DAKAR · 8 NOV 2026', Inter(19, True), C_MUT, anchor='rm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 52, W, H], fill=(8, 13, 21, 235))
    d.line([(0, H - 52), (W, H - 52)], fill=C_RED + (255,), width=3)
    items = [
        'NAUFRAGE AU LARGE DE KÉBÉMER : 34 MORTS ET UN SEUL RESCAPÉ',
        'BILAN PROVISOIRE · DES DISPARUS SONT RECHERCHÉS',
        'VICTIMES PRINCIPALEMENT DE LÉONA ET DE THIÉPPE',
        'ROUTE DES CANARIES : 635 MORTS EN CINQ MOIS EN 2026',
    ]
    cycle = '     ·     '.join(items) + '     ·     '
    f = Inter(19)
    sp = textw(cycle, f)
    off = int((t * 75) % sp)
    y = H - 26
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')

def intro_scene(t):
    img = kb_src(os.path.join(ROOT, 'image-search/pirogue-en-bois-surcharg-e-migrants-mer--2.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 122)
    vignette(img, 0, 0, W, H)
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (64, 108), 'DRAME · ÉMIGRATION IRRÉGULIÈRE · LOUPPOUL, LOUGA', Inter(20, True), C_RED, stroke=2)
    for i, line in enumerate(['NAUFRAGE', 'AU LARGE DE', 'KÉBÉMER']):
        off = int((1 - ease(P(t, 0.1 + i * 0.1, 0.55 + i * 0.1))) * 30)
        text(d, (64 + off, 152 + i * 70), line, Oswald(68), C_TXT, stroke=2)
    p = ease(P(t, 0.7, 1.2))
    if p > 0:
        bar = Image.new('RGBA', (int(560 * p), 6), C_RED + (255,))
        img.paste(bar, (64, 392), bar)
        text(d, (64, 418), 'Encore des jeunes Sénégalais perdus en mer', Inter(21), C_TXT, stroke=2)
    lower_third(img, 'URGENCE · FAITS DIVERS', '34 MORTS, UN SEUL RESCAPÉ',
                'Un nombre indéterminé de personnes portées disparues', 'PROVISOIRE', C_RED,
                P(t, 0.9, 1.5), 'APS · AP · dimanche 8 novembre')
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
        'p1': ('image-search/pirogue-chou-e-plage-s-n-gal-migrants-na-1.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--1.jpg'),
        'p2': ('image-search/pirogue-en-bois-surcharg-e-migrants-mer--1.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--3.jpg'),
        'p3': ('image-search/pirogue-en-bois-surcharg-e-migrants-mer--4.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--3.jpg'),
        'p4': ('image-search/pirogue-chou-e-plage-s-n-gal-migrants-na-1.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--1.jpg'),
        'p5': ('image-search/pirogue-chou-e-plage-s-n-gal-migrants-na-1.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--2.jpg'),
        'p6': ('image-search/pirogue-chou-e-plage-s-n-gal-migrants-na-3.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--2.jpg'),
        'p7': ('image-search/pirogue-chou-e-plage-s-n-gal-migrants-na-1.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--4.jpg'),
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
        'p1': ('POINT 01 · BILAN PROVISOIRE', 'AU MOINS 34 MORTS',
               'Un seul rescapé · des disparus toujours recherchés',
               '34 MORTS', C_RED, 'APS · dimanche 8 novembre'),
        'p2': ('POINT 02 · CHRONOLOGIE', 'VENDREDI, SAMEDI, DIMANCHE',
               'Tébène : 4 corps · Lompoul : une vingtaine · puis +11',
               'DE 4 À 34', C_STEEL, 'Repêchages successifs'),
        'p3': ('POINT 03 · LES VICTIMES', 'LÉONA ET THIÉPPE EN DEUIL',
               'La plupart des victimes du département de Kébémer',
               'DEUIL', C_STEEL, 'Identification en cours'),
        'p4': ('POINT 04 · L\'ÉTAT PRÉSENT', 'SOLIDARITÉ AVEC LES FAMILLES',
               'Gouverneure de Louga sur place · ministre lundi',
               'SOLIDARITÉ', C_TEAL, None),
        'p5': ('POINT 05 · INCONNUS', 'CIRCONSTANCES À ÉTABLIR',
               'Passagers, point de départ : les recherches continuent',
               'ENQUÊTE', C_GOLD, 'Gendarmerie · sapeurs-pompiers'),
        'p6': ('POINT 06 · CONTEXTE', 'LA ROUTE DES CANARIES',
               '635 morts en cinq mois en 2026 (Caminando Fronteras)',
               '635 MORTS', C_WARM, 'Route de l\'Atlantique'),
        'p7': ('POINT 07 · RÉPONSES', 'LUTTE CONTRE LES PASSEURS',
               'Coopération régionale · insertion des jeunes',
               'MOBILISATION', C_TEAL, 'Communiqué du gouvernement'),
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
    panel(60, 540, 'LA JEUNESSE', 'RÊVES BRISÉS · LÉONA, THIÉPPE, TOUT UN PAYS', C_STEEL, p1)
    panel(680, 540, 'LES RESPONSABILITÉS', 'RÉSEAUX DE PASSEURS · ÉTAT · COOPÉRATION', C_WARM, p2)

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

    chip(60, 452, 540, '34 morts · 1 rescapé · des disparus', P(t - t0, 1.4, 1.8), C_RED)
    chip(680, 452, 540, '635 morts sur la route en 2026', P(t - t0, 1.6, 2.0), C_WARM)
    chip(60, 532, 540, 'Insertion socio-économique des jeunes', P(t - t0, 1.9, 2.3), C_TEAL)
    chip(680, 532, 540, 'Coopération régionale renforcée', P(t - t0, 2.1, 2.5), C_GOLD)

    text(d, (640, 100), 'JUSQU\'À QUAND ?', Oswald(34), C_TXT, anchor='mm')
    text(d, (640, 132), 'Encore des jeunes Sénégalais perdus en mer', Inter(18), C_MUT, anchor='mm')

    ys = ease(P(t - t0, 3.2, 3.9))
    if ys > 0:
        sc = Image.new('RGBA', (1160, 50), (22, 32, 46, int(240 * ys)))
        img.paste(sc, (60, 606), sc)
        d.rectangle([60, 606, 1219, 655], outline=C_GOLD + (int(220 * ys),), width=2)
        text(d, (80, 631), 'SYNTHÈSE · Entre émotion et colère, la question reste ouverte. Les recherches se poursuivent.',
             Inter(17, True), (232, 236, 244), anchor='lm')

    text(d, (640, 660), SRC_LINE, Inter(13, True), C_MUT, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img

def outro_scene(t, t0):
    img = kb_src(os.path.join(ROOT, 'image-search/pirogue-en-bois-surcharg-e-migrants-mer--3.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 165)
    d = ImageDraw.Draw(img, 'RGBA')
    appear = P(t - t0, 0, 0.3)
    text(d, (640, 235), '34 MORTS · DES DISPARUS', Oswald(50), C_TXT, anchor='mm')
    p = ease(appear)
    bar = Image.new('RGBA', (int(560 * p), 6), C_RED + (255,))
    img.paste(bar, (360, 288), bar)
    lines = [
        'Pensées aux familles de Léona et de Thiéppe',
        'Les recherches se poursuivent en mer',
        'Jusqu\'à quand ?',
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
    text(d, (640, 630), 'Faits divers · SNGAL INFOS', Inter(18, True), C_GOLD, anchor='mm')
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
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'kebemer-naufrage-16x9.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'nk-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.1f}s')

if __name__ == '__main__':
    main()
