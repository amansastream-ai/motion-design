"""« Affaire Diodio Glow Skin » — 16:9 master (3:16). VO voice-02 calibrée sur les segments.
Run: pytools/bin/python tools/render_dio_16x9.py
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
DUR = 196.0

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
    ('intro',   0,   7), ('ctx',   7,  25),
    ('p1',    25,  43), ('p2',  43,  59), ('p3',  59,  77), ('p4',  77,  93),
    ('p5',    93, 110), ('p6', 110, 128), ('p7', 128, 143),
    ('debate', 143, 177), ('outro', 177, 196),
]
SRC_LINE = 'Source : Seneweb · PressAfrik · Xibaaru · Pulse Sénégal'

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
    y0 = 500
    h = 200
    ph = int(ease(P(appear, 0, 0.38)) * h)
    if ph > 2:
        panel = Image.new('RGBA', (W, ph), (10, 16, 26, 238))
        img.paste(panel, (0, y0), panel)
        d.line([(0, y0), (W, y0)], fill=accent + (200,), width=3)
    k1 = ease(P(appear, 0.14, 0.42))
    if k1 > 0:
        text(d, (40, y0 + 22 + (1 - k1) * 14), kicker, Inter(19, True), accent, anchor='lm')
        text(d, (W - 40, y0 + 22 + (1 - k1) * 14), 'INFO 7 · FAIT DIVERS', Inter(17, True), C_MUT, anchor='rm')
    k2 = ease(P(appear, 0.22, 0.52))
    if k2 > 0:
        size = 46
        f = Oswald(size)
        while textw(headline, f) > W - 90 and size > 30:
            size -= 2
            f = Oswald(size)
        text(d, (40, y0 + 78 + (1 - k2) * 22), headline, f, C_TXT, stroke=2)
    k3 = ease(P(appear, 0.38, 0.72))
    if k3 > 0 and sub:
        text(d, (40, y0 + 142 + (1 - k3) * 16), sub, Inter(21), C_MUT)
    if k3 > 0 and caveat:
        text(d, (40, y0 + 172), caveat, Inter(15), C_GOLD)
    k4 = ease(P(appear, 0.5, 0.85))
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
    d.rectangle([0, 0, 8, 60], fill=C_WARM + (255,))
    text(d, (26, 10), 'INFO 7', Oswald(30), (242, 246, 252), anchor='lm')
    d.rectangle([136, 12, 300, 48], fill=(178, 32, 22, 235))
    text(d, (218, 31), 'EN DIRECT', Inter(18, True), (255, 232, 226), anchor='mm')
    text(d, (W - 26, 31), 'DAKAR · 23 OCT 2026', Inter(19, True), C_MUT, anchor='rm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 52, W, H], fill=(8, 13, 21, 235))
    d.line([(0, H - 52), (W, H - 52)], fill=C_WARM + (255,), width=3)
    items = [
        'AFFAIRE DIODIO GLOW SKIN · GARDE À VUE À LA DIVISION SPÉCIALE DE CYBERSÉCURITÉ',
        '7 MILLIONS FCFA : MONTANT RAPPORTÉ PAR LA PRESSE',
        'DEUX VERSIONS : ATTAQUES PRÉSUMÉES OU AIDES SOCIALES',
        'MALAISE : ÉVACUATION À L\'HÔPITAL PRINCIPAL — SELON L\'AVOCAT',
        'LES ACCUSATIONS NE SONT PAS DES FAITS ÉTABLIS',
    ]
    cycle = '   ●   '.join(items) + '   ●   '
    f = Inter(19)
    sp = textw(cycle, f)
    off = int((t * 75) % sp)
    y = H - 26
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')

def intro_scene(t):
    img = kb_src(os.path.join(ROOT, 'image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-1.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 118)
    vignette(img, 0, 0, W, H)
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (64, 120), 'ACTUALITÉ JUDICIAIRE · 22–23 OCTOBRE 2026 · SÉNÉGAL', Inter(20, True), C_GOLD, stroke=2)
    for i, line in enumerate(['AFFAIRE', 'DIODIO GLOW SKIN :', 'GARDE À VUE À LA DSC']):
        off = int((1 - ease(P(t, 0.25 + i * 0.14, 0.9 + i * 0.14))) * 34)
        text(d, (64 + off, 165 + i * 72), line, Oswald(72), C_TXT, stroke=2)
    p = ease(P(t, 1.3, 2.1))
    if p > 0:
        bar = Image.new('RGBA', (int(560 * p), 6), C_WARM + (255,))
        img.paste(bar, (64, 412), bar)
        text(d, (64, 440), 'Ce que l\'on sait, ce qui est présumé, ce qui reste à confirmer', Inter(22), C_TXT, stroke=2)
    lower_third(img, 'ENQUÊTE · RÉSEAUX SOCIAUX', 'SEPT MILLIONS, DEUX VERSIONS',
                'Transferts d\'argent, attaques verbales présumées, version de la défense',
                'À LA UNE', C_WARM, P(t, 2.2, 3.2))
    header_bar(img)
    ticker(img, t)
    return img

def point_scene(kind, t, t0):
    appear = P(t - t0, 0.05, 0.5 + (18) / 34)
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
        'p1': ('image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-2.jpg',
               'image-search/tribunal-justice-cour-s-n-gal-palais-de--2.jpg'),
        'p2': ('image-search/enqu-te-cybers-curit-smartphone-r-seaux--1.webp',
               'image-search/rox-la-chanceli-re-rokhaya-fall-s-n-gal--3.jpg'),
        'p3': ('image-search/rox-la-chanceli-re-rokhaya-fall-s-n-gal--2.jpg',
               'image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-4.webp'),
        'p4': ('image-search/rox-la-chanceli-re-rokhaya-fall-s-n-gal--1.jpg',
               'image-search/rox-la-chanceli-re-rokhaya-fall-s-n-gal--4.webp'),
        'p5': ('image-search/tribunal-justice-cour-s-n-gal-palais-de--1.jpg',
               'image-search/enqu-te-cybers-curit-smartphone-r-seaux--3.jpg'),
        'p6': ('image-search/h-pital-soins-sant-s-n-gal-personnel-soi-1.jpg',
               'image-search/h-pital-soins-sant-s-n-gal-personnel-soi-4.jpg'),
        'p7': ('image-search/tribunal-justice-cour-s-n-gal-palais-de--4.jpg',
               'image-search/enqu-te-cybers-curit-smartphone-r-seaux--2.jpg'),
    }
    lpath, rpath = imgs[kind]
    insert_image('l', lpath, a=140)
    insert_image('r', rpath, a=112, cy=0.3)

    d = ImageDraw.Draw(img, 'RGBA')
    seam = int(ease(P(t - t0, 0, 0.5)) * H)
    if seam > 2:
        d.line([(W // 2, H // 2 - seam // 2), (W // 2, H // 2 + seam // 2)], fill=C_STEEL + (170,), width=3)

    i = int(kind[1])
    circle = int(ease(P(t - t0, 0, 0.4)) * 34)
    if circle > 2:
        d.ellipse([64 - 4, 112 - 4, 64 + circle * 2 + 4, 112 + circle * 2 + 4],
                  outline=C_GOLD + (255,), width=2)
        if circle >= 33:
            text(d, (64 + 34, 112 + 34), f'{i:02d}', Oswald(40), C_GOLD, anchor='mm')

    badges = {
        'p1': ('POINT 01 · JEUDI 22 OCTOBRE', 'L\'INTERPELLATION',
               'Garde à vue à la DSC, sur instruction du procureur Saliou Dicko — TGI de Pikine-Guédiawaye',
               'PROCÉDURE', C_STEEL, None),
        'p2': ('POINT 02 · ENQUÊTE', 'CE QUE CHERCHENT LES ENQUÊTEURS',
               'Transferts d\'argent, exploitation du téléphone de Rox — selon la presse',
               'SOUPÇONS', C_WARM, 'Selon la presse'),
        'p3': ('POINT 03 · ARGENT', 'LES 7 MILLIONS DE FCFA',
               'Rox aurait reçu cette somme de Diodio, une partie destinée à Adomo — selon la presse',
               '7 M FCFA', C_GOLD, 'Rapporté par la presse · non confirmé en justice'),
        'p4': ('POINT 04 · PERSONNES CITÉES', 'QUI FIGURE DANS LE DOSSIER ?',
               'Rox la Chancelière, Adomo, Kaliphone, Tata Nafi Cannes — mentions à distinguer des poursuites',
               'CITÉS', C_STEEL, 'Citations dans la presse'),
        'p5': ('POINT 05 · DROIT', 'LES QUALIFICATIONS PRÉSUMÉES',
               'Association de malfaiteurs · complicité d\'injures publiques en ligne',
               'PRÉSUMÉ', C_WARM, 'Aucune culpabilité établie par un tribunal'),
        'p6': ('POINT 06 · SANTÉ', 'LE VOLET MÉDICAL',
               'Malaise vers 23 h, évacuée à l\'Hôpital Principal de Dakar — selon son avocat',
               'MALAISE', C_GOLD, 'Selon la défense · pas de bulletin médical indépendant'),
        'p7': ('POINT 07 · PROCÉDURE', 'CE QUI RESTE À CONFIRMER',
               'Garde à vue → déferrement → poursuites éventuelles → jugement',
               'À SUIVRE', C_STEEL, 'Aucune décision définitive à ce stade'),
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
        ph = int(ease(appear) * 320)
        if ph < 2:
            return
        panel_img = Image.new('RGBA', (w, ph), C_PANEL + (255,))
        img.paste(panel_img, (x, 140))
        d.rectangle([x, 140, x + w - 1, 140 + ph - 1], outline=C_LINE + (255,), width=2)
        head = Image.new('RGBA', (w, 44), (side + (255,)))
        img.paste(head, (x, 140), head)
        text(d, (x + 14, 162), name, Oswald(26), (12, 16, 24), anchor='lm')
        text(d, (x + 14, 198), role, Inter(16, True), C_MUT)

    p1 = ease(P(t - t0, 0.2, 0.8))
    p2 = ease(P(t - t0, 0.7, 1.3))
    panel(60, 540, 'THÈSE DE L\'ENQUÊTE', 'PARQUET · DSC', C_WARM, p1)
    panel(680, 540, 'VERSION DE LA DÉFENSE', 'DIODIO · ROX', C_STEEL, p2)

    cd = ease(P(t - t0, 1.4, 2.0))
    if cd > 0:
        b = Image.new('RGBA', (92, 52), C_RED + (int(255 * cd),))
        img.paste(b, (594, 300), b)
        text(d, (640, 327), 'VS', Oswald(32), (255, 242, 238), anchor='mm')

    def chip(x, y, w, label, appear, accent):
        a = ease(appear)
        if a <= 0:
            return
        ch = Image.new('RGBA', (w, 78), C_PANEL2 + (int(255 * a),))
        img.paste(ch, (x, y), ch)
        d.rectangle([x, y, x + w - 1, y + 77], outline=C_LINE + (int(255 * a),), width=2)
        d.rectangle([x, y, x + 6, y + 77], fill=accent + (int(255 * a),))
        text(d, (x + 22, y + 38), label, Inter(19, True), (222, 230, 240), anchor='lm')

    chip(60, 480, 540, 'Transferts d\'argent examinés', P(t - t0, 1.6, 2.1), C_WARM)
    chip(680, 480, 540, 'Sommes destinées à des œuvres sociales', P(t - t0, 1.8, 2.3), C_STEEL)
    chip(60, 578, 540, 'Attaques verbales présumées', P(t - t0, 2.2, 2.7), C_GOLD)
    chip(680, 578, 540, 'Malaise : état de santé alerté', P(t - t0, 2.4, 2.9), C_TEAL)

    text(d, (640, 112), 'LE DÉBAT', Oswald(34), C_TXT, anchor='mm')
    text(d, (640, 136), 'Deux lectures opposées du dossier', Inter(18), C_MUT, anchor='mm')

    ys = ease(P(t - t0, 3.4, 4.2))
    if ys > 0:
        sc = Image.new('RGBA', (1160, 64), (22, 32, 46, int(240 * ys)))
        img.paste(sc, (60, 672), sc)
        d.rectangle([60, 672, 1219, 735], outline=C_GOLD + (int(220 * ys),), width=2)
        text(d, (80, 704), 'SYNTHÈSE · Un transfert ne suffit pas : la destination des fonds doit être établie. Accusations ≠ culpabilité.',
             Inter(19, True), (232, 236, 244), anchor='lm')

    text(d, (640, H - 78), SRC_LINE, Inter(16, True), C_MUT, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img

def outro_scene(t, t0):
    img = vsplit_bg(t / 22)
    img = blend_to_bg(img)
    d = ImageDraw.Draw(img, 'RGBA')
    appear = P(t - t0, 0, 0.5)
    text(d, (640, 215), '7 MILLIONS · 2 VERSIONS · DES QUESTIONS OUVERTES', Oswald(52), C_TXT, anchor='mm')
    p = ease(appear)
    bar = Image.new('RGBA', (int(560 * p), 6), C_WARM + (255,))
    img.paste(bar, (360, 268), bar)
    lines = [
        'Garde à vue à la DSC depuis le 22 octobre',
        '7 millions de FCFA : montant rapporté par la presse',
        'Rox, Adomo, Kaliphone : des mentions à distinguer des poursuites',
        'Malaise et évacuation : selon la défense',
        'Procédure en cours : aucune décision définitive',
    ]
    for i, line in enumerate(lines):
        a = P(t - t0, 0.3 + i * 0.22, 0.9 + i * 0.22)
        if a > 0:
            text(d, (640, 312 + i * 40), f'●  {line}', Inter(20), C_TXT if a > 0.9 else C_MUT, anchor='mm')
    a = P(t - t0, 1.8, 2.4)
    if a > 0:
        text(d, (640, 555), 'LES ACCUSATIONS NE SONT PAS DES FAITS ÉTABLIS', Oswald(36), C_GOLD, anchor='mm')
    text(d, (640, 615), SRC_LINE, Inter(17, True), C_MUT, anchor='mm')
    text(d, (640, 655), 'Politique et société · INFO 7', Inter(18, True), C_GOLD, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img

def frame(t):
    i, kind, t0, t1 = seg_at(t)
    p = P(t, t0, t1)
    if kind == 'intro':
        img = intro_scene(t - t0)
    elif kind == 'ctx':
        img = kb_src(os.path.join(ROOT, 'image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-4.webp'), W, H)
        img = blend_to_bg(img)
        dim(img, 0, 0, W, H, 118)
        vignette(img, 0, 0, W, H)
        lower_third(img, 'CONTEXTE · PROFIL', 'QUI EST DIODIO GLOW SKIN ?',
                    'Mame Diarra Thiam, 31 ans, commerçante de produits cosmétiques (selon Ndarinfo)',
                    'CONTEXTE', C_STEEL, P(t - t0, 0.1, 0.5 + (t1 - t0) / 30))
        header_bar(img)
        ticker(img, t)
    elif kind.startswith('p'):
        img = point_scene(kind, t, t0)
    elif kind == 'debate':
        img = debate_scene(t, t0)
    else:
        img = outro_scene(t, t0)

    if p < 0.05:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.55 * (1 - p / 0.05))
    if p > 0.94:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.4 * ((p - 0.94) / 0.06))
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'diodio-glow-skin-16x9.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'dio-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', '-shortest', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.0f}s')

if __name__ == '__main__':
    main()
