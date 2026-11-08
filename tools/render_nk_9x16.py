"""Short « Naufrage au large de Kébémer » — 9:16 (1:30). SNGAL INFOS + logo.
TIMING EXACT : voix dès 0,15 s · écarts 0,5 s · son jusqu'à la dernière image.
Chaines : a@0.15 b@13.65 c@25.28 d@38.91 g@50.11 h@62.21 i@73.72 (fin 83.66, outro 83.66-90).
Run: pytools/bin/python tools/render_nk_9x16.py
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
DUR = 90.0

C_BG = (7, 13, 22)
C_PANEL = (15, 23, 34)
C_LINE = (28, 41, 56)
C_TXT = (232, 238, 246)
C_MUT = (138, 154, 172)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_TEAL = (42, 184, 162)
C_STEEL = (110, 160, 220)
C_RED = (214, 64, 48)

SEGS = [
    ('intro',  0,     13.65),   # a
    ('j1',   13.65,   25.28),   # b
    ('j2',   25.28,   38.91),   # c
    ('j3',   38.91,   50.11),   # d
    ('j4',   50.11,   62.21),   # g
    ('j5',   62.21,   73.72),   # h
    ('j6',   73.72,   83.66),   # i
    ('outro', 83.66,  90.0),
]

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
    y = int((nh - h) * 0.32)
    return im.crop((x, y, x + w, y + h))

def kb_src(path, w, h, cy=0.4):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.72 or im.height < h * 0.72:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(26))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.34)
        sw, sh = im.size
        scale = min(w * 0.86 / sw, h * 0.86 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), (int((w - nw) / 2), int((h - nh) * cy)))
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
        gd.rectangle([0, y, W, y + 2], fill=(int(6 + 8 * k), int(12 + 10 * k), int(20 + 12 * k)))
    return Image.blend(base, grad, 0.5)

def dim(img, x, y, w, h, a=120):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, a))
    img.paste(ov, (x, y), ov)

def header_bar(img):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 110], fill=(9, 15, 24, 232))
    d.line([(0, 110), (W, 110)], fill=C_LINE + (255,), width=3)
    d.rectangle([0, 0, 12, 110], fill=C_RED + (255,))
    lg = logo(74)
    img.paste(lg, (30, 18), lg)
    text(d, (124, 55), 'SNGAL INFOS', Oswald(48), (242, 246, 252), anchor='lm')
    d.rectangle([W - 300, 28, W - 30, 86], fill=(178, 32, 22, 235))
    text(d, (W - 165, 57), 'KÉBÉMER · 8 NOV', Inter(22, True), (255, 232, 226), anchor='mm')

def story_card(img, kicker, headline, sub, badge, accent, appear):
    d = ImageDraw.Draw(img, 'RGBA')
    a = ease(P(appear, 0, 0.2))
    if a <= 0:
        return
    ph = int(a * 420)
    panel = Image.new('RGBA', (W, ph), (11, 18, 29, 238))
    img.paste(panel, (0, H - 420), panel)
    d.line([(0, H - 420), (W, H - 420)], fill=accent + (200,), width=4)
    k1 = ease(P(appear, 0.06, 0.24))
    if k1 > 0:
        text(d, (54, H - 382 + (1 - k1) * 16), kicker, Inter(26, True), accent, stroke=2)
    k2 = ease(P(appear, 0.12, 0.32))
    if k2 > 0:
        size = 58
        f = Oswald(size)
        while textw(headline, f) > W - 110 and size > 34:
            size -= 3
            f = Oswald(size)
        text(d, (54, H - 322 + (1 - k2) * 24), headline, f, C_TXT, stroke=2)
    k3 = ease(P(appear, 0.22, 0.44))
    if k3 > 0 and sub:
        text(d, (54, H - 228), sub, Inter(28), C_MUT)
    k4 = ease(P(appear, 0.3, 0.55))
    if k4 > 0 and badge:
        fw = textw(badge, Oswald(34)) + 56
        x = int(54)
        b = Image.new('RGBA', (fw, 72), accent + (int(235 * k4),))
        img.paste(b, (x, H - 160), b)
        text(d, (x + fw / 2, H - 124), badge, Oswald(34), (12, 16, 24), anchor='mm')

def outro_card(img, t, t0):
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (W // 2, 700), 'PENSÉES', Oswald(110), C_TXT, anchor='mm', stroke=2)
    text(d, (W // 2, 820), 'AUX FAMILLES', Oswald(110), C_TXT, anchor='mm', stroke=2)
    p = ease(P(t - t0, 0.1, 0.5))
    bar = Image.new('RGBA', (int(640 * p), 10), C_RED + (255,))
    img.paste(bar, (220, 910), bar)
    for i, line in enumerate(['Léona · Thiéppe · tout un pays',
                              'Recherches toujours en cours',
                              'Jusqu\'à quand ?']):
        a = P(t - t0, 0.25 + i * 0.18, 0.7 + i * 0.18)
        if a > 0:
            text(d, (W // 2, 1000 + i * 78), line, Inter(36), C_TXT if a > 0.9 else C_MUT,
                 anchor='mm')
    a = P(t - t0, 1.1, 1.6)
    if a > 0:
        lg = logo(92)
        img.paste(lg, (370, 1280), lg)
        text(d, (W // 2, 1430), 'SNGAL INFOS', Oswald(64), C_GOLD, anchor='mm')
        text(d, (W // 2, 1520), 'Faits divers · SNGAL INFOS', Inter(26, True), C_MUT, anchor='mm')

def frame(t):
    i, kind, t0, t1 = seg_at(t)
    appear = t - t0
    bg = {
        'intro': 'image-search/pirogue-en-bois-surcharg-e-migrants-mer--4.jpg',
        'j1': 'image-search/pirogue-en-bois-surcharg-e-migrants-mer--2.jpg',
        'j2': 'image-search/plage-c-te-s-n-gal-pirogues-p-cheurs-oc--4.jpg',
        'j3': 'image-search/plage-c-te-s-n-gal-pirogues-p-cheurs-oc--1.jpg',
        'j4': 'image-search/pirogue-en-bois-surcharg-e-migrants-mer--1.jpg',
        'j5': 'image-search/plage-c-te-s-n-gal-pirogues-p-cheurs-oc--3.jpg',
        'j6': 'image-search/pirogue-en-bois-surcharg-e-migrants-mer--3.jpg',
        'outro': 'image-search/plage-c-te-s-n-gal-pirogues-p-cheurs-oc--4.jpg',
    }[kind]
    img = kb_src(os.path.join(ROOT, bg), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 120)

    cards = {
        'intro': ('FAITS DIVERS · LOUGA', 'NAUFRAGE À KÉBÉMER', '34 morts · 1 rescapé · des disparus', 'PROVISOIRE', C_RED),
        'j1': ('BILAN PROVISOIRE', '34 MORTS', 'Un seul rescapé · disparus recherchés', '8 NOVEMBRE', C_RED),
        'j2': ('CHRONOLOGIE', 'VENDREDI → DIMANCHE', 'Tébène · Lompoul · +11 corps', '4 → 21 → 34', C_STEEL),
        'j3': ('LES VICTIMES', 'LÉONA & THIÉPPE', 'Le département de Kébémer en deuil', 'DEUIL', C_STEEL),
        'j4': ('CONTEXTE', 'ROUTE DES CANARIES', '635 morts en cinq mois en 2026', '635 MORTS', C_WARM),
        'j5': ('RÉPONSES', 'LUTTE CONTRE LES PASSEURS', 'Coopération · insertion des jeunes', 'MOBILISATION', C_TEAL),
        'j6': ('ÉMOTION & COLÈRE', 'JUSQU\'À QUAND ?', 'La question reste ouverte', 'SNGAL INFOS', C_GOLD),
    }
    if kind != 'outro':
        kicker, headline, sub, badge, accent = cards[kind]
        story_card(img, kicker, headline, sub, badge, accent, appear)
    else:
        outro_card(img, t, t0)
    header_bar(img)
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'kebemer-naufrage-9x16.mp4')
    tmp = out + '.tmp.mp4'
    proc = imageio_ffmpeg.write_frames(
        tmp, (W, H), pix_fmt_in='rgb24', fps=FPS, codec='libx264', quality=None,
        macro_block_size=1, ffmpeg_log_level='error',
        output_params=['-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
    proc.send(None)
    n = int(DUR * FPS)
    for fi in range(n):
        proc.send(np.asarray(frame(fi / FPS), dtype=np.uint8))
        if fi % (FPS * 20) == 0:
            print(f'  frame {fi}/{n}')
    proc.close()
    import subprocess
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'nk-9x16-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.0f}s')

if __name__ == '__main__':
    main()
