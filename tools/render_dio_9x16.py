"""« Affaire Diodio Glow Skin » — 9x16 Short (90 s), voice-02 (clips b, d, g, i) calibrés.
Run: pytools/bin/python tools/render_dio_9x16.py
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
C_TXT = (232, 238, 246)
C_MUT = (138, 154, 172)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_STEEL = (110, 160, 220)

SEGS = [
    ('intro', 0, 6), ('j1', 6, 23), ('j2', 23, 40),
    ('j3', 40, 57), ('j4', 57, 72), ('recap', 72, 82), ('outro', 82, 90),
]

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
    return im.crop(((nw - w) // 2, int((nh - h) * 0.38), (nw - w) // 2 + w, int((nh - h) * 0.38) + h))

def kb_src(path, w, h, cx=0.5, cy=0.4):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.72 or im.height < h * 0.72:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(26))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.30)
        sw, sh = im.size
        scale = min(w * 0.86 / sw, h * 0.62 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), (int((w - nw) * cx), int((h - nh) * cy)))
        return plate
    return cover(im, w, h)

def text(d, xy, s, f, fill, anchor=None, stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

def textw(s, f):
    return f.getbbox(s)[2]

def dim(img, x, y, w, h, a=120):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, a))
    img.paste(ov, (x, y), ov)

def header_v(img, tag):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 150], fill=(9, 15, 24, 230))
    d.rectangle([0, 0, 14, 150], fill=C_WARM + (255,))
    text(d, (40, 75), 'INFO 7', Oswald(52), (242, 246, 252), anchor='lm')
    d.rectangle([W - 330, 38, W - 40, 112], fill=(178, 32, 22, 235))
    text(d, (W - 185, 75), tag, Inter(30, True), (255, 232, 226), anchor='mm')

def ticker_v(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    y = H - 130
    d.rectangle([0, y, W, H], fill=(8, 13, 21, 238))
    d.line([(0, y), (W, y)], fill=C_WARM + (255,), width=6)
    items = ['GARDE À VUE À LA DSC', '7 MILLIONS FCFA : SELON LA PRESSE',
             'DEUX VERSIONS', 'MALAISE : SELON LA DÉFENSE', 'ACCUSATIONS ≠ FAITS ÉTABLIS']
    cycle = '  ●  '.join(items) + '  ●  '
    f = Inter(36)
    sp = textw(cycle, f)
    off = int((t * 130) % sp)
    text(d, (-off, y + 62), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y + 62), cycle, f, (214, 224, 236), anchor='lm')

def mini_card(t, t0, img_path, num, title, fact, verdict, accent, caveat=None):
    img = kb_src(os.path.join(ROOT, img_path), W, H, cy=0.4)
    dim(img, 0, 0, W, H, 112)
    d = ImageDraw.Draw(img, 'RGBA')
    appear = P(t - t0, 0, 0.5)
    ph = int(ease(appear) * 480)
    if ph > 2:
        panel = Image.new('RGBA', (W, ph), (10, 16, 26, 238))
        img.paste(panel, (0, 1330), panel)
        d.line([(0, 1330), (W, 1330)], fill=accent + (220,), width=6)
    if num:
        text(d, (48, 1180), num, Oswald(150), accent, stroke=3)
    k = ease(P(t - t0, 0.15, 0.6))
    if k > 0:
        size = 74
        f = Oswald(size)
        while textw(title, f) > W - 100 and size > 44:
            size -= 3
            f = Oswald(size)
        text(d, (48, 1380 + (1 - k) * 20), title, f, C_TXT, stroke=2)
        text(d, (48, 1520), fact, Inter(38), C_MUT)
        if caveat:
            text(d, (48, 1590), caveat, Inter(30), C_GOLD)
    k2 = ease(P(t - t0, 0.45, 0.85))
    if k2 > 0:
        fw = textw(verdict, Oswald(46)) + 70
        b = Image.new('RGBA', (fw, 100), accent + (int(235 * k2),))
        img.paste(b, (W - 40 - fw, 1120), b)
        d2 = ImageDraw.Draw(img, 'RGBA')
        text(d2, (W - 40 - fw / 2, 1172), verdict, Oswald(46), (12, 16, 24), anchor='mm')
    header_v(img, 'EN DIRECT')
    ticker_v(img, t)
    return img

def frame(t):
    i, kind, t0, t1 = seg_at(t)
    p = P(t, t0, t1)
    if kind == 'intro':
        img = kb_src(os.path.join(ROOT, 'image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-1.jpg'), W, H, cy=0.3)
        dim(img, 0, 0, W, H, 130)
        d = ImageDraw.Draw(img, 'RGBA')
        for i2, line in enumerate(['AFFAIRE', 'DIODIO', 'GLOW SKIN']):
            off = int((1 - ease(P(t, 0.15 + i2 * 0.12, 0.7 + i2 * 0.12))) * 40)
            text(d, (60 + off, 620 + i2 * 175), line, Oswald(150), C_TXT, stroke=2)
        a = P(t, 1.2, 1.8)
        if a > 0:
            bar = Image.new('RGBA', (int(700 * a), 12), C_WARM + (255,))
            img.paste(bar, (60, 1180), bar)
            text(d, (60, 1230), 'Garde à vue · 22–23 octobre 2026', Inter(40), C_TXT, stroke=2)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)
    elif kind == 'j1':
        img = mini_card(t, t0, 'image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-2.jpg',
                        '01', 'INTERPELLÉE', '22 octobre · garde à vue à la cybersécurité',
                        'GAV', C_STEEL, None)
    elif kind == 'j2':
        img = mini_card(t, t0, 'image-search/rox-la-chanceli-re-rokhaya-fall-s-n-gal--2.jpg',
                        '02', '7 MILLIONS FCFA', 'Rox aurait reçu cette somme de Diodio',
                        'ARGENT', C_GOLD, 'Rapporté par la presse')
    elif kind == 'j3':
        img = mini_card(t, t0, 'image-search/h-pital-soins-sant-s-n-gal-personnel-soi-1.jpg',
                        '03', 'MALAISE & HÔPITAL', 'Évacuée à l\'Hôpital Principal de Dakar',
                        'SANTÉ', C_WARM, 'Selon son avocat')
    elif kind == 'j4':
        img = mini_card(t, t0, 'image-search/tribunal-justice-cour-s-n-gal-palais-de--1.jpg',
                        '04', 'DEUX VERSIONS', 'Attaques présumées ou aides sociales ?',
                        'ENQUÊTE', C_STEEL, 'Accusations ≠ faits établis')
    elif kind == 'recap':
        img = kb_src(os.path.join(ROOT, 'image-search/enqu-te-cybers-curit-smartphone-r-seaux--1.webp'), W, H)
        dim(img, 0, 0, W, H, 165)
        d = ImageDraw.Draw(img, 'RGBA')
        text(d, (W / 2, 420), 'CE QU\'IL FAUT SAVOIR', Oswald(100), C_TXT, anchor='mm', stroke=2)
        items = [
            '● Garde à vue à la DSC · 22 octobre',
            '● 7 M FCFA : montant rapporté par la presse',
            '● Rox, Adomo, Kaliphone : des mentions',
            '● Malaise : selon la défense',
            '● Procédure en cours, sans décision définitive',
        ]
        for i2, line in enumerate(items):
            a = P(t - t0, 0.2 + i2 * 0.14, 0.7 + i2 * 0.14)
            if a > 0:
                text(d, (W / 2, 580 + i2 * 96), line, Inter(42), C_TXT if a > 0.9 else C_MUT, anchor='mm', stroke=1)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)
    else:
        img = kb_src(os.path.join(ROOT, 'assets/press-conf.png'), W, H)
        dim(img, 0, 0, W, H, 150)
        d = ImageDraw.Draw(img, 'RGBA')
        text(d, (W / 2, 560), 'ACCUSATIONS', Oswald(110), C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, 720), '≠ FAITS ÉTABLIS', Oswald(110), C_GOLD, anchor='mm', stroke=2)
        text(d, (W / 2, 950), 'politique · société · débat', Inter(44), C_MUT, anchor='mm')
        a = P(t - t0, 0.6, 1.2)
        if a > 0:
            bar = Image.new('RGBA', (int(700 * a), 12), C_WARM + (255,))
            img.paste(bar, (190, 1060), bar)
            text(d, (W / 2, 1180), 'La suite sur INFO 7', Inter(42), C_TXT, anchor='mm', stroke=2)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)

    if p < 0.05:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.5 * (1 - p / 0.05))
    if p > 0.94:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.45 * ((p - 0.94) / 0.06))
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'diodio-glow-skin-9x16.mp4')
    tmp = out + '.tmp.mp4'
    proc = imageio_ffmpeg.write_frames(
        tmp, (W, H), pix_fmt_in='rgb24', fps=FPS, codec='libx264', quality=None,
        macro_block_size=1, ffmpeg_log_level='error',
        output_params=['-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
    proc.send(None)
    n = int(DUR * FPS)
    for fi in range(n):
        proc.send(np.asarray(frame(fi / FPS), dtype=np.uint8))
        if fi % (FPS * 25) == 0:
            print(f'  frame {fi}/{n}')
    proc.close()
    import subprocess
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'dio-9x16-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', '-shortest', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.0f}s')

if __name__ == '__main__':
    main()
