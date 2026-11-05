"""Teaser 30 s « Dip Doundou Guiss — double disque d'or » (16:9 + 9x16) — voix dès 0,15 s, son jusqu'à la fin.
Run: pytools/bin/python tools/render_teaser_dg.py [16x9|9x16]
"""
import os
import subprocess
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

FPS = 24
DUR = 30.0
C_BG = (7, 13, 22)
C_TXT = (232, 238, 246)
C_MUT = (138, 154, 172)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)

FORMAT = '16x9'
ARGS = [a for a in sys.argv[1:] if a in ('16x9', '9x16')]
if ARGS:
    FORMAT = ARGS[0]
if FORMAT == '16x9':
    W, H = 1280, 720
else:
    W, H = 1080, 1920

_LOGO_CACHE = {}

def logo(size):
    if size not in _LOGO_CACHE:
        lg = Image.open(os.path.join(ROOT, 'assets', 'logo-sngal.png')).convert('RGBA')
        _LOGO_CACHE[size] = lg.resize((size, size), Image.LANCZOS)
    return _LOGO_CACHE[size]

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
    return im.crop(((nw - w) // 2, int((nh - h) * 0.36), (nw - w) // 2 + w, int((nh - h) * 0.36) + h))

def kb_src(path, w, h, cy=0.38):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.72 or im.height < h * 0.72:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(24))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.32)
        sw, sh = im.size
        scale = min(w * 0.85 / sw, h * 0.7 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), (int((w - nw) / 2), int((h - nh) * cy)))
        return plate
    return cover(im, w, h)

def text(d, xy, s, f, fill, anchor=None, stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

def textw(s, f):
    return f.getbbox(s)[2]

def dim(img, a):
    ov = Image.new('RGBA', img.size, (0, 0, 0, a))
    img.paste(ov, (0, 0), ov)

CARDS = [
    ('image-search/dip-doundou-guiss-chanteur-s-n-galais-1.jpg', 'DIP DOUNDOU GUISS', 'DOUBLE DISQUE D\'OR', C_GOLD),
    ('image-search/disque-d-or-certification-disque-or-albu-1.jpg', 'LNN & LFLF', 'CERTIFIÉS OR · AMC', C_GOLD),
    ('image-search/dip-doundou-guiss-chanteur-s-n-galais-3.jpg', 'LE RAP SÉNÉGALAIS', 'AU SOMMET', C_WARM),
]

def frame(t):
    img = Image.new('RGB', (W, H), C_BG)
    if t < 15.89:
        if t < 5.5:
            path, l1, l2, accent = CARDS[0]
        elif t < 11.0:
            path, l1, l2, accent = CARDS[1]
        else:
            path, l1, l2, accent = CARDS[2]
        img = kb_src(os.path.join(ROOT, path), W, H)
        dim(img, 125)
        d = ImageDraw.Draw(img, 'RGBA')
        s1 = Oswald(int(96 * (W / 1280)))
        s2 = Oswald(int(58 * (W / 1280)))
        if FORMAT == '9x16':
            s1, s2 = Oswald(104), Oswald(64)
        while textw(l1, s1) > W * 0.92:
            s1 = Oswald(s1.size - 4)
        text(d, (W / 2, H * 0.42), l1, s1, C_TXT, anchor='mm', stroke=2)
        bar = Image.new('RGBA', (min(W - 120, textw(l1, s1) + 60), 10), accent + (255,))
        img.paste(bar, (int((W - bar.width) / 2), int(H * 0.42 + 58 * (W / 1280))), bar)
        text(d, (W / 2, H * 0.42 + 132 * (W / 1280)), l2, s2, accent, anchor='mm', stroke=2)
        lg = logo(int(64 * (W / 1280)))
        img.paste(lg, (24, 24), lg)
        d2 = ImageDraw.Draw(img, 'RGBA')
        text(d2, (24 + lg.width + 12, 24 + lg.height // 2), 'SNGAL INFOS',
             Oswald(int(30 * (W / 1280))), C_TXT, anchor='lm', stroke=2)
    elif t < 23.0:
        stages = [(15.89, 19.5), (19.5, 23.0)]
        labels = [('UNE ANNÉE', 'DE CONSÉCRATION', C_WARM),
                  ('JOJ DAKAR 2026', 'UNE PREMIÈRE AFRICAINE', C_GOLD)]
        si = 0
        for k, (a, b) in enumerate(stages):
            if a <= t < b:
                si = k
                break
        l1, l2, accent = labels[si]
        img = kb_src(os.path.join(ROOT, 'image-search/dip-doundou-guiss-chanteur-s-n-galais-2.jpg'), W, H)
        dim(img, 150)
        d = ImageDraw.Draw(img, 'RGBA')
        s = Oswald(int(88 * (W / 1280)))
        if FORMAT == '9x16':
            s = Oswald(96)
        text(d, (W / 2, H * 0.40), l1, s, C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, H * 0.40 + 110 * (W / 1280)), l2, s, accent, anchor='mm', stroke=2)
        for bt in (15.89, 19.5):
            if bt <= t < bt + 0.1:
                dim(img, 200)
    else:
        img = kb_src(os.path.join(ROOT, 'image-search/disque-d-or-certification-disque-or-albu-3.jpg'), W, H)
        dim(img, 165)
        d = ImageDraw.Draw(img, 'RGBA')
        lg = logo(int(90 * (W / 1280)))
        img.paste(lg, (int(W / 2 - lg.width / 2), int(H * 0.28)), lg)
        s = Oswald(int(76 * (W / 1280)))
        if FORMAT == '9x16':
            s = Oswald(84)
        text(d, (W / 2, H * 0.40 + 60 * (W / 1280)), 'LA SUITE', s, C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, H * 0.40 + 165 * (W / 1280)), 'DANS NOTRE REPORTAGE', s, C_GOLD, anchor='mm', stroke=2)
        bar = Image.new('RGBA', (int(560 * (W / 1280)), 8), C_WARM + (255,))
        img.paste(bar, (int((W - bar.width) / 2), int(H * 0.40 + 130 * (W / 1280))), bar)
        text(d, (W / 2, H * 0.40 + 300 * (W / 1280)), 'SNGAL INFOS · CULTURE',
             Inter(int(28 * (W / 1280)), True), C_MUT, anchor='mm')
        if 23.0 <= t < 23.1:
            dim(img, 200)
    return img

def main():
    tag = '16x9' if FORMAT == '16x9' else '9x16'
    out = os.path.join(ROOT, 'videos', f'dip-disque-or-teaser-{tag}.mp4')
    tmp = out + '.tmp.mp4'
    proc = imageio_ffmpeg.write_frames(
        tmp, (W, H), pix_fmt_in='rgb24', fps=FPS, codec='libx264', quality=None,
        macro_block_size=1, ffmpeg_log_level='error',
        output_params=['-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
    proc.send(None)
    n = int(DUR * FPS)
    for fi in range(n):
        proc.send(np.asarray(frame(fi / FPS), dtype=np.uint8))
    proc.close()
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'dg-teaser-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out)

if __name__ == '__main__':
    main()
