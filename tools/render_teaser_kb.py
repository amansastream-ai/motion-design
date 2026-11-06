"""Teaser « Alerte sanitaire Kébémer » — 30 s, 16:9 et 9:16. SNGAL INFOS + logo.
Run: pytools/bin/python tools/render_teaser_kb.py [16x9|9x16]
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

FPS = 24
DUR = 30.0

C_BG = (7, 13, 22)
C_TXT = (232, 238, 246)
C_MUT = (138, 154, 172)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_RED = (214, 64, 48)

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

def cover(img, w, h, cy=0.35):
    im = img.convert('RGB')
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * cy)
    return im.crop((x, y, x + w, y + h))

def kb_src(path, w, h, cy=0.4):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.72 or im.height < h * 0.72:
        plate = cover(im, w, h, cy).filter(ImageFilter.GaussianBlur(26))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.34)
        sw, sh = im.size
        scale = min(w * 0.86 / sw, h * 0.86 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), (int((w - nw) / 2), int((h - nh) * cy)))
        return plate
    return cover(im, w, h, cy)

def text(d, xy, s, f, fill, anchor=None, stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

def dim(img, w, h, a=120):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, a))
    img.paste(ov, (0, 0), ov)

def header_bar(img, W):
    d = ImageDraw.Draw(img, 'RGBA')
    hh = 60 if W == 1280 else 110
    d.rectangle([0, 0, W, hh], fill=(9, 15, 24, 232))
    d.rectangle([0, 0, 8 if W == 1280 else 12, hh], fill=C_RED + (255,))
    lg = logo(44 if W == 1280 else 74)
    img.paste(lg, (18 if W == 1280 else 30, 8 if W == 1280 else 18), lg)
    text(d, (72 if W == 1280 else 124, 10 if W == 1280 else 55), 'SNGAL INFOS',
         Oswald(30 if W == 1280 else 48), (242, 246, 252), anchor='lm')

def stage(t, mode, W, H):
    if t < 13.07:
        img = kb_src(os.path.join(ROOT, 'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-4.jpg'), W, H)
        img = img.filter(ImageFilter.GaussianBlur(1.2))
        dim(img, W, H, 108 if W == 1280 else 118)
        d = ImageDraw.Draw(img, 'RGBA')
        if W == 1280:
            text(d, (64, 120), 'ALERTE SANITAIRE · KÉBÉMER', Inter(22, True), C_RED, stroke=2)
            for i, line in enumerate(['548 CAS', 'DE SYNDROMES', 'DIGESTIFS AIGUS']):
                off = int((1 - ease(P(t, 0.1 + i * 0.12, 0.6 + i * 0.12))) * 36)
                text(d, (64 + off, 190 + i * 88), line, Oswald(92), C_TXT, stroke=3)
            a = P(t, 1.2, 1.7)
            if a > 0:
                text(d, (64, 500), 'Une maladie mystérieuse · enquête de grande ampleur',
                     Inter(24), C_MUT, stroke=2)
            a = P(t, 8.0, 8.5)
            if a > 0:
                fw = Oswald(44).getbbox('LA SUITE DANS NOTRE REPORTAGE')[2] + 64
                b = Image.new('RGBA', (fw, 84), C_RED + (int(235 * a),))
                img.paste(b, (64, 560), b)
                text(d, (64 + fw / 2, 602), 'LA SUITE DANS NOTRE REPORTAGE',
                     Oswald(44), (255, 242, 238), anchor='mm')
        else:
            text(d, (54, 220), 'ALERTE SANITAIRE · KÉBÉMER', Inter(30, True), C_RED, stroke=2)
            for i, line in enumerate(['548 CAS', 'DE SYNDROMES', 'DIGESTIFS AIGUS']):
                off = int((1 - ease(P(t, 0.1 + i * 0.12, 0.6 + i * 0.12))) * 36)
                text(d, (54 + off, 320 + i * 150), line, Oswald(116), C_TXT, stroke=3)
            a = P(t, 1.2, 1.7)
            if a > 0:
                text(d, (54, 830), 'Maladie mystérieuse · enquête de grande ampleur',
                     Inter(34), C_MUT, stroke=2)
            a = P(t, 8.0, 8.5)
            if a > 0:
                fw = Oswald(52).getbbox('LA SUITE DANS NOTRE REPORTAGE')[2] + 76
                b = Image.new('RGBA', (fw, 110), C_RED + (int(235 * a),))
                img.paste(b, (54, 920), b)
                text(d, (54 + fw / 2, 975), 'LA SUITE DANS NOTRE REPORTAGE',
                     Oswald(52), (255, 242, 238), anchor='mm')
    elif t < 17.5:
        img = kb_src(os.path.join(ROOT, 'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-1.jpg'), W, H)
        img = img.filter(ImageFilter.GaussianBlur(1.2))
        dim(img, W, H, 122)
        d = ImageDraw.Draw(img, 'RGBA')
        a = P(t - 13.07, 0, 0.35)
        txts = ['AUCUN DÉCÈS', 'ENQUÊTE ET ANALYSES EN COURS'] if W == 1280 else ['AUCUN DÉCÈS', 'ENQUÊTE EN COURS']
        f1 = Oswald(84) if W == 1280 else Oswald(104)
        f2 = Inter(26) if W == 1280 else Inter(38)
        y1, y2 = (260, 380) if W == 1280 else (760, 930)
        x0 = 64 if W == 1280 else 54
        off = int((1 - ease(a)) * 30)
        text(d, (x0 + off, y1), txts[0], f1, C_TXT, stroke=3)
        if P(t - 13.07, 0.2, 0.5) > 0:
            text(d, (x0, y2), txts[1], f2, C_MUT, stroke=2)
    elif t < 22.0:
        img = kb_src(os.path.join(ROOT, 'image-search/h-pital-patients-soins-sant-s-n-gal-infi-3.jpg'), W, H)
        img = img.filter(ImageFilter.GaussianBlur(1.2))
        dim(img, W, H, 126)
        d = ImageDraw.Draw(img, 'RGBA')
        a = P(t - 17.5, 0, 0.35)
        x0 = 64 if W == 1280 else 54
        f1 = Oswald(84) if W == 1280 else Oswald(104)
        f2 = Inter(26) if W == 1280 else Inter(38)
        y1, y2 = (260, 380) if W == 1280 else (760, 930)
        off = int((1 - ease(a)) * 30)
        text(d, (x0 + off, y1), '548 CAS EN QUELQUES JOURS', f1, C_TXT, stroke=3)
        if P(t - 17.5, 0.2, 0.5) > 0:
            text(d, (x0, y2), 'Kébémer · région de Louga · SNGAL INFOS', f2, C_GOLD, stroke=2)
    else:
        img = kb_src(os.path.join(ROOT, 'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-2.jpg'), W, H)
        img = img.filter(ImageFilter.GaussianBlur(2.2))
        dim(img, W, H, 158)
        d = ImageDraw.Draw(img, 'RGBA')
        cx = W // 2
        lg = logo(80 if W == 1280 else 120)
        img.paste(lg, (cx - 40 if W == 1280 else cx - 60, 240 if W == 1280 else 720), lg)
        f = Oswald(64) if W == 1280 else Oswald(88)
        text(d, (cx, 380 if W == 1280 else 920), 'SNGAL INFOS', f, C_GOLD, anchor='mm')
        fs = Inter(22) if W == 1280 else Inter(32)
        text(d, (cx, 440 if W == 1280 else 1010), 'Santé publique · SNGAL INFOS', fs, C_MUT, anchor='mm')
    return img

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else '16x9'
    if which == '16x9':
        W, H = 1280, 720
        out = os.path.join(ROOT, 'videos', 'kebemer-alerte-teaser-16x9.mp4')
        wav = 'audio/kb-teaser-master.wav'
    else:
        W, H = 1080, 1920
        out = os.path.join(ROOT, 'videos', 'kebemer-alerte-teaser-9x16.mp4')
        wav = 'audio/kb-teaser-master.wav'
    tmp = out + '.tmp.mp4'
    proc = imageio_ffmpeg.write_frames(
        tmp, (W, H), pix_fmt_in='rgb24', fps=FPS, codec='libx264', quality=None,
        macro_block_size=1, ffmpeg_log_level='error',
        output_params=['-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
    proc.send(None)
    n = int(DUR * FPS)
    for fi in range(n):
        t = fi / FPS
        img = stage(t, which, W, H)
        header_bar(img, W)
        proc.send(np.asarray(img, dtype=np.uint8))
    proc.close()
    import subprocess
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, wav),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out)

if __name__ == '__main__':
    main()
