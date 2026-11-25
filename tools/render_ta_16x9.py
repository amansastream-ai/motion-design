"""« TAS : le Sénégal conserve son titre 2025 » — reportage 16:9 (3:00) + débat.
SNGAL INFOS + logo. Source : Afrik+1. VO voice-02 · plateaux fiches animées pour
la durée (jamais les pauses) · débat « la joie du Sénégal / les instances ».
Run: pytools/bin/python tools/render_ta_16x9.py
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
DUR = 180.0

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
    ('intro',  0.0,   21.0),   # ta-1 @0.15 (13.13) + plateau
    ('p1',    21.0,   35.0),   # ta-2 @21.15 (8.31) + plateau
    ('p2',    35.0,   47.5),   # ta-3 @35.15 (7.93) + plateau
    ('p3',    47.5,   60.0),   # ta-4 @47.65 (6.61) + plateau
    ('p4',    60.0,   74.0),   # ta-5 @60.15 (8.82) + plateau
    ('p5',    74.0,   88.5),   # ta-6 @74.15 (9.89) + plateau
    ('p6',    88.5,  101.0),   # ta-7 @88.65 (5.71) + plateau
    ('p7',   101.0,  115.5),   # ta-8 @101.15 (7.72) + plateau
    ('p8',   115.5,  130.0),   # ta-10 @115.65 (8.31) + plateau
    ('debate', 130.0, 165.0),  # ta-9 @130.15 (7.80) + tableau
    ('outro', 165.0, 180.0),
]
SRC_LINE = 'Source : Afrik+1 · décision du TAS du 24 novembre 2026'

# plateaux : (début absolu, titre, [lignes], accent)
PLATS = {
    'intro': (13.6, 'CE QUE DIT LA DÉCISION',
              ['Forfait CAF annulé', 'Finale 1-0 après prolongation rétablie',
               'Titre de champion d\'Afrique 2025 conservé'], C_GOLD),
    'p1': (29.8, 'LA DÉCISION DU TAS',
           ['24 novembre 2026 · Lausanne', 'Favorable au Sénégal',
            'Rendue face à la CAF et au Maroc'], C_STEEL),
    'p2': (43.4, 'LE FORFAIT ANNULÉ',
           ['La CAF avait déclaré le Sénégal forfait', 'Le TAS annule cette décision',
            'Le statu quo revient à la finale'], C_RED),
    'p3': (54.6, 'FINALE RÉTABLIE',
           ['1-0 après prolongation', 'Le résultat des Lions tient',
            'Le score est rétabli'], C_GOLD),
    'p4': (69.3, 'TITRE 2025',
           ['Le Sénégal conserve son titre', 'Champion d\'Afrique 2025',
            'Officiellement, après la décision du TAS'], C_GOLD),
    'p5': (84.4, 'AU CŒUR DU LITIGE',
           ['Fédération sénégalaise de football', 'Face à la CAF', 'Et au Maroc'], C_STEEL),
    'p6': (94.7, 'L\'AFRIQUE RÉAGIT',
           ['Une vague de réactions', 'Dans la presse sportive',
            'Sur la scène médiatique africaine'], C_TEAL),
    'p7': (109.2, 'LE TAS EN BREF',
           ['Instance arbitrale du sport mondial', 'Basée à Lausanne',
            'Ses sentences s\'imposent aux fédérations'], C_STEEL),
    'p8': (124.3, 'QUESTIONS OUVERTES',
           ['Réactions officielles de la CAF ?', 'Et le Maroc ?',
            'La suite du feuilleton ?'], C_WARM),
}

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
    if im.width < w * 0.68 or im.height < h * 0.68:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(22))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.32)
        sw, sh = im.size
        scale = min(w * 0.84 / sw, h * 0.84 / sh)
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

def header_bar(img):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 60], fill=(9, 15, 24, 225))
    d.line([(0, 60), (W, 60)], fill=C_LINE + (255,), width=2)
    d.rectangle([0, 0, 8, 60], fill=C_GOLD + (255,))
    lg = logo(44)
    img.paste(lg, (18, 8), lg)
    text(d, (72, 10), 'SNGAL INFOS', Oswald(30), (242, 246, 252), anchor='lm')
    d.rectangle([262, 12, 426, 48], fill=(178, 32, 22, 235))
    text(d, (344, 31), 'LE JOURNAL', Inter(18, True), (255, 232, 226), anchor='mm')
    text(d, (W - 26, 31), 'DAKAR · 24 NOV 2026', Inter(19, True), C_MUT, anchor='rm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 52, W, H], fill=(8, 13, 21, 235))
    d.line([(0, H - 52), (W, H - 52)], fill=C_GOLD + (255,), width=3)
    cycle = '     ·     '.join([
        'LE TAS ANNULE LE FORFAIT DÉCRÉTÉ PAR LA CAF',
        'FINALE RÉTABLIE : SÉNÉGAL 1-0 APRÈS PROLONGATION',
        'LE SÉNÉGAL CONSERVE SON TITRE DE CHAMPION D\'AFRIQUE 2025',
        'SOURCE : AFRIK+1 · RÉACTIONS DANS LA PRESSE SPORTIVE AFRICAINE',
    ]) + '     ·     '
    f = Inter(19)
    sp = textw(cycle, f)
    off = int((t * 75) % sp)
    y = H - 26
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')

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
        text(d, (W - 40, y0 + 22 + (1 - k1) * 14), 'SNGAL INFOS · SPORT', Inter(17, True), C_MUT, anchor='rm')
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

def plateau(img, t, spec):
    if spec is None:
        return
    t0, title, lines, accent = spec
    a = ease(P(t, t0, t0 + 0.45))
    if a <= 0:
        return
    d = ImageDraw.Draw(img, 'RGBA')
    x0, y0, x1, y1 = 220, 132, 1060, 452
    card = Image.new('RGBA', (x1 - x0, y1 - y0), (11, 18, 29, int(238 * a)))
    img.paste(card, (x0, y0), card)
    d.rectangle([x0, y0, x1, y1], outline=C_LINE + (int(255 * a),), width=2)
    d.rectangle([x0, y0, x0 + 8, y1], fill=accent + (int(255 * a),))
    at = ease(P(t, t0 + 0.1, t0 + 0.6))
    if at > 0:
        text(d, (x0 + 40, y0 + 52), title, Oswald(42), accent, anchor='lm')
        bar = Image.new('RGBA', (int(560 * at), 5), accent + (255,))
        img.paste(bar, (x0 + 40, y0 + 88), bar)
    for i, line in enumerate(lines):
        al = ease(P(t, t0 + 0.55 + i * 0.4, t0 + 1.05 + i * 0.4))
        if al > 0:
            text(d, (x0 + 40 + (1 - al) * 26, y0 + 130 + i * 52), line, Inter(26),
                 C_TXT if al > 0.85 else C_MUT)
            d.ellipse([x0 + 22, y0 + 138 + i * 52, x0 + 34, y0 + 150 + i * 52],
                      fill=accent + (int(255 * al),))

def intro_scene(t):
    img = kb_src(os.path.join(ROOT, 'image-search/ta-lions-trophee.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 128)
    vignette(img, 0, 0, W, H)
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (64, 108), 'SPORT · DÉCISION DU TAS · LAUSANNE', Inter(20, True), C_GOLD, stroke=2)
    for i, line in enumerate(['LE SÉNÉGAL', 'CONSERVE SON', 'TITRE 2025']):
        off = int((1 - ease(P(t, 0.1 + i * 0.1, 0.55 + i * 0.1))) * 30)
        text(d, (64 + off, 152 + i * 70), line, Oswald(68), C_TXT if i < 2 else C_GOLD, stroke=2)
    p = ease(P(t, 0.7, 1.2))
    if p > 0:
        bar = Image.new('RGBA', (int(560 * p), 6), C_GOLD + (255,))
        img.paste(bar, (64, 392), bar)
        text(d, (64, 418), 'Le TAS annule le forfait de la CAF et rétablit la finale 1-0',
             Inter(21), C_TXT, stroke=2)
    lower_third(img, 'SPORT · DÉCISION DU TAS', 'LE TAS DONNE RAISON AU SÉNÉGAL',
                'Finale 1-0 après prolongation rétablie · titre 2025 conservé',
                'DÉCISION', C_GOLD, P(t, 0.9, 1.5), 'Source : Afrik+1')
    plateau(img, t, PLATS['intro'])
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

    PA = 'image-search/ta-lions-parade.jpg'
    TR = 'image-search/ta-lions-trophee.jpg'
    LA = 'image-search/ta-lausanne.jpg'
    imgs = {
        'p1': (LA, TR), 'p2': (LA, PA), 'p3': (TR, PA), 'p4': (TR, PA),
        'p5': (LA, TR), 'p6': (PA, TR), 'p7': (LA, PA), 'p8': (TR, LA),
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
        'p1': ('POINT 01 · LA DÉCISION', 'LE TAS TRANCHE',
               'Lausanne · 24 novembre · en faveur du Sénégal', 'LAUSANNE', C_STEEL, None),
        'p2': ('POINT 02 · L\'ANNULATION', 'LE FORFAIT ANNULÉ',
               'La décision de la CAF qui déclarait le Sénégal forfait tombe',
               'ANNULATION', C_RED, None),
        'p3': ('POINT 03 · LA FINALE', '1-0 APRÈS PROLONGATION',
               'Le résultat des Lions est rétabli', 'RÉTABLI', C_GOLD, None),
        'p4': ('POINT 04 · LE TITRE', 'CHAMPION D\'AFRIQUE 2025',
               'Le Sénégal conserve officiellement son titre', 'TITRE 2025', C_GOLD,
               'Source : Afrik+1'),
        'p5': ('POINT 05 · LE LITIGE', 'FSF FACE À LA CAF ET AU MAROC',
               'La Fédération sénégalaise de football a porté l\'affaire',
               'LITIGE', C_STEEL, None),
        'p6': ('POINT 06 · LES RÉACTIONS', 'L\'AFRIQUE RÉAGIT',
               'Presse sportive · scène médiatique africaine', 'RÉACTIONS', C_TEAL, None),
        'p7': ('POINT 07 · LE TAS', 'CE QU\'EST LE TAS',
               'Le Tribunal arbitral du sport de Lausanne', 'CADRE', C_STEEL, None),
        'p8': ('POINT 08 · EN SUSPENS', 'CE QUI RESTE À SAVOIR',
               'Réactions officielles · suites du feuilleton', 'À SUIVRE', C_WARM, None),
    }
    kicker, headline, sub, verdict, accent, caveat = badges[kind]
    lower_third(img, kicker, headline, sub, verdict, accent, appear, caveat)
    plateau(img, t, PLATS.get(kind))
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

    p1 = ease(P(t - t0, 0.15, 0.7))
    p2 = ease(P(t - t0, 0.6, 1.15))
    panel(60, 540, 'LA JOIE DU SÉNÉGAL', 'UN TITRE CONFIRMÉ · 1-0 RÉTABLI', C_GOLD, p1)
    panel(680, 540, 'LES INSTANCES', 'CAF ET MAROC · RÉACTIONS À VENIR', C_STEEL, p2)

    cd = ease(P(t - t0, 1.5, 2.0))
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

    chip(60, 452, 540, 'Finale 1-0 après prolongation', P(t - t0, 8.5, 9.2), C_GOLD)
    chip(680, 452, 540, 'Forfait annulé par le TAS', P(t - t0, 9.5, 10.2), C_RED)
    chip(60, 532, 540, 'Titre 2025 conservé', P(t - t0, 10.8, 11.5), C_GOLD)
    chip(680, 532, 540, 'Réactions en Afrique', P(t - t0, 12.0, 12.7), C_TEAL)

    text(d, (640, 100), 'LE TITRE EST DE RETOUR', Oswald(34), C_TXT, anchor='mm')
    text(d, (640, 132), 'Entre l\'émotion sénégalaise et les instances du football',
         Inter(18), C_MUT, anchor='mm')

    ys = ease(P(t - t0, 16.0, 16.9))
    if ys > 0:
        sc = Image.new('RGBA', (1160, 50), (22, 32, 46, int(240 * ys)))
        img.paste(sc, (60, 606), sc)
        d.rectangle([60, 606, 1219, 655], outline=C_GOLD + (int(220 * ys),), width=2)
        text(d, (80, 631), 'SYNTHÈSE · Le TAS a tranché : le titre 2025 reste aux Lions.',
             Inter(17, True), (232, 236, 244), anchor='lm')

    text(d, (640, 660), SRC_LINE, Inter(13, True), C_MUT, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img

def outro_scene(t, t0):
    img = kb_src(os.path.join(ROOT, 'image-search/ta-lions-parade.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 165)
    d = ImageDraw.Draw(img, 'RGBA')
    appear = P(t - t0, 0, 0.3)
    text(d, (640, 235), 'LE TITRE RESTE AUX LIONS', Oswald(50), C_TXT, anchor='mm')
    p = ease(appear)
    bar = Image.new('RGBA', (int(560 * p), 6), C_GOLD + (255,))
    img.paste(bar, (360, 288), bar)
    lines = [
        'Le TAS rétablit le Sénégal',
        'Finale 1-0 après prolongation',
        'Champion d\'Afrique 2025',
    ]
    for i, line in enumerate(lines):
        a = P(t - t0, 0.4 + i * 0.5, 1.0 + i * 0.5)
        if a > 0:
            text(d, (640, 340 + i * 44), f'—  {line}', Inter(20),
                 C_TXT if a > 0.9 else C_MUT, anchor='mm')
    a = P(t - t0, 2.6, 3.3)
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
        return intro_scene(t)
    if kind == 'debate':
        return debate_scene(t, t0)
    if kind == 'outro':
        return outro_scene(t, t0)
    return point_scene(kind, t, t0)

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'tas-titre-2025-16x9.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'ta-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.1f}s')

if __name__ == '__main__':
    main()
