"""Teaser 30 s « La vie chère et la grève » (16:9 + 9x16) — SNGAL INFOS + logo.
Run: pytools/bin/python tools/render_teaser_vc.py [16x9|9x16]
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
    ('image-search/march-dakar-familles-denr-es-alimentaire-4.webp', 'À DAKAR,', 'LES FAMILLES FONT FACE', C_WARM),
    ('image-search/gr-ve-manifestation-syndicale-s-n-gal-tr-2.jpg', 'GRÈVE DE 72 HEURES', '21 · 22 · 23 OCTOBRE', C_GOLD),
    ('image-search/vie-ch-re-s-n-gal-inflation-prix-aliment-3.webp', 'SALAIRES & PRIX', 'LE POUVOIR D\'ACHAT AU CŒUR', C_WARM),
]

def frame(t):
    img = Image.new('RGB', (W, H), C_BG)
    if t < 0.7:
        p = t / 0.7
        img = Image.new('RGB', (W, H), (int(255 * p), int(180 * p), int(60 * p)))
        lg = logo(int(160 * (W / 1280)))
        img.paste(lg, (int(W / 2 - lg.width / 2), int(H / 2 - lg.height / 2)), lg)
    elif t < 29.3:
        stages = [(0.7, 2.0), (2.0, 7.5), (7.5, 14.0), (14.0, 20.0), (20.0, 25.0), (25.0, 29.3)]
        si = 0
        for k, (a, b) in enumerate(stages):
            if a <= t < b:
                si = k
                break
        p = P(t, stages[si][0], stages[si][1])
        if si == 0:
            img = kb_src(os.path.join(ROOT, 'assets/press-conf.png'), W, H)
            dim(img, 150)
            d = ImageDraw.Draw(img, 'RGBA')
            text(d, (W / 2, H / 2), 'VIE CHÈRE', Oswald(int(120 * (W / 1280))), C_TXT, anchor='mm', stroke=2)
        elif si <= 3:
            path, l1, l2, accent = CARDS[si - 1]
            img = kb_src(os.path.join(ROOT, path), W, H)
            dim(img, 125)
            d = ImageDraw.Draw(img, 'RGBA')
            k = ease(P(p, 0, 0.14))
            off = int((1 - k) * 30)
            s1 = Oswald(int(104 * (W / 1280)))
            s2 = Oswald(int(60 * (W / 1280)))
            if FORMAT == '9x16':
                s1, s2 = Oswald(112), Oswald(66)
            text(d, (W / 2, H * 0.42 + off), l1, s1, C_TXT, anchor='mm', stroke=2)
            bar = Image.new('RGBA', (int(min(W - 120, textw(l1, s1) + 60) * k), 10), accent + (255,))
            img.paste(bar, (int((W - bar.width) / 2), int(H * 0.42 + 58 * (W / 1280))), bar)
            text(d, (W / 2, H * 0.42 + 132 * (W / 1280)), l2, s2, accent, anchor='mm', stroke=2)
        elif si == 4:
            img = kb_src(os.path.join(ROOT, 'image-search/march-dakar-familles-denr-es-alimentaire-2.jpg'), W, H)
            dim(img, 150)
            d = ImageDraw.Draw(img, 'RGBA')
            s = Oswald(int(96 * (W / 1280)))
            if FORMAT == '9x16':
                s = Oswald(104)
            text(d, (W / 2, H * 0.40), 'COMMENT TENIR', s, C_TXT, anchor='mm', stroke=2)
            text(d, (W / 2, H * 0.40 + 110 * (W / 1280)), 'JUSQU\'À LA FIN DU MOIS ?', s, C_GOLD, anchor='mm', stroke=2)
        else:
            img = kb_src(os.path.join(ROOT, 'assets/press-conf.png'), W, H)
            dim(img, 165)
            d = ImageDraw.Draw(img, 'RGBA')
            k = ease(P(p, 0, 0.12))
            lg = logo(int(90 * (W / 1280)))
            img.paste(lg, (int(W / 2 - lg.width / 2), int(H * 0.30)), lg)
            s = Oswald(int(84 * (W / 1280)))
            if FORMAT == '9x16':
                s = Oswald(92)
            text(d, (W / 2, H * 0.40 + 80 * (W / 1280)), 'LA SUITE', s, C_TXT, anchor='mm', stroke=2)
            text(d, (W / 2, H * 0.40 + 185 * (W / 1280)), 'DANS NOTRE REPORTAGE', s, C_GOLD, anchor='mm', stroke=2)
            bar = Image.new('RGBA', (int(560 * (W / 1280) * k), 8), C_WARM + (255,))
            img.paste(bar, (int((W - bar.width) / 2), int(H * 0.40 + 150 * (W / 1280))), bar)
            text(d, (W / 2, H * 0.40 + 320 * (W / 1280)), 'SNGAL INFOS · POLITIQUE ET SOCIÉTÉ',
                 Inter(int(28 * (W / 1280)), True), C_MUT, anchor='mm')
        d = ImageDraw.Draw(img, 'RGBA')
        text(d, (W / 2, H - 46 * (W / 1280) if FORMAT == '16x9' else H - 120),
             'SNGAL INFOS · EXTRAIT', Inter(int(18 * (W / 1280)) if FORMAT == '16x9' else 30, True),
             (120, 132, 148), anchor='mm')
        for bt in [2.0, 7.5, 14.0, 20.0, 25.0]:
            if bt <= t < bt + 0.1:
                dim(img, 200)
    else:
        p = P(t, 29.3, 30.0)
        img = Image.new('RGB', (W, H), (int(C_BG[0] + (1 - p) * 60), int(C_BG[1] + (1 - p) * 40), int(C_BG[2] + (1 - p) * 10)))
    return img

def main():
    tag = '16x9' if FORMAT == '16x9' else '9x16'
    out = os.path.join(ROOT, 'videos', f'vie-chere-greve-teaser-{tag}.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'vc-teaser-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', '-shortest', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out)

if __name__ == '__main__':
    main()
