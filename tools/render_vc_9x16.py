"""« La vie chère et la grève » — 9x16 Short (90 s), voix ENCHAÎNÉES (0,85 s). SNGAL INFOS + logo.
Run: pytools/bin/python tools/render_vc_9x16.py
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
C_TEAL = (42, 184, 162)

SEGS = [
    ('intro', 0, 6.2), ('j1', 6.2, 17.68), ('j2', 17.68, 28.38), ('j3', 28.38, 38.56),
    ('j4', 38.56, 49.39), ('j5', 49.39, 59.57), ('j6', 59.57, 70.5), ('outro', 70.5, 90),
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
    lg = logo(96)
    img.paste(lg, (36, 27), lg)
    text(d, (150, 75), 'SNGAL INFOS', Oswald(52), (242, 246, 252), anchor='lm')
    d.rectangle([W - 330, 38, W - 40, 112], fill=(178, 32, 22, 235))
    text(d, (W - 185, 75), tag, Inter(30, True), (255, 232, 226), anchor='mm')

def ticker_v(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    y = H - 130
    d.rectangle([0, y, W, H], fill=(8, 13, 21, 238))
    d.line([(0, y), (W, y)], fill=C_WARM + (255,), width=6)
    items = ['VIE CHÈRE', 'GRÈVE 72 H · 21-23 OCT', 'SALAIRES & POUVOIR D\'ACHAT',
             'LES FAMILLES S\'ORGANISENT', 'SNGAL INFOS']
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
    appear = P(t - t0, 0, 0.3)
    ph = int(ease(appear) * 480)
    if ph > 2:
        panel = Image.new('RGBA', (W, ph), (10, 16, 26, 238))
        img.paste(panel, (0, 1330), panel)
        d.line([(0, 1330), (W, 1330)], fill=accent + (220,), width=6)
    if num:
        text(d, (48, 1180), num, Oswald(150), accent, stroke=3)
    k = ease(P(t - t0, 0.08, 0.4))
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
    k2 = ease(P(t - t0, 0.3, 0.65))
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
        img = kb_src(os.path.join(ROOT, 'image-search/march-dakar-familles-denr-es-alimentaire-4.webp'), W, H, cy=0.3)
        dim(img, 0, 0, W, H, 130)
        d = ImageDraw.Draw(img, 'RGBA')
        for i2, line in enumerate(['VIE', 'CHÈRE', 'À DAKAR']):
            off = int((1 - ease(P(t, 0.1 + i2 * 0.1, 0.55 + i2 * 0.1))) * 40)
            text(d, (60 + off, 620 + i2 * 175), line, Oswald(155), C_TXT, stroke=2)
        a = P(t, 0.9, 1.5)
        if a > 0:
            bar = Image.new('RGBA', (int(700 * a), 12), C_WARM + (255,))
            img.paste(bar, (60, 1180), bar)
            text(d, (60, 1230), 'Comment les familles font-elles face ?', Inter(40), C_TXT, stroke=2)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)
    elif kind == 'j1':
        img = mini_card(t, t0, 'image-search/march-dakar-familles-denr-es-alimentaire-3.jpg',
                        '01', 'LE PANIER EXPLOSE', 'Riz, huile, pain, transport : les prix grimpent',
                        'BUDGET', C_WARM, None)
    elif kind == 'j2':
        img = mini_card(t, t0, 'image-search/march-dakar-familles-denr-es-alimentaire-2.jpg',
                        '02', 'LES FAMILLES ARBITRENT', 'Dépenses réduites, achats reportés',
                        'QUOTIDIEN', C_GOLD, None)
    elif kind == 'j3':
        img = mini_card(t, t0, 'image-search/gr-ve-manifestation-syndicale-s-n-gal-tr-1.jpg',
                        '03', 'SALAIRES', 'Suivre la hausse des prix : la revendication',
                        'CONFLIT', C_STEEL, None)
    elif kind == 'j4':
        img = mini_card(t, t0, 'image-search/gr-ve-manifestation-syndicale-s-n-gal-tr-2.jpg',
                        '04', 'GRÈVE DE 72 H', 'Du 21 au 23 octobre, plusieurs secteurs',
                        'MOBILISATION', C_WARM, None)
    elif kind == 'j5':
        img = mini_card(t, t0, 'image-search/gr-ve-manifestation-syndicale-s-n-gal-tr-3.jpg',
                        '05', 'LES SYNDICATS', 'Salaires, aides ciblées, ménages vulnérables',
                        '3 DEMANDES', C_STEEL, None)
    elif kind == 'j6':
        img = mini_card(t, t0, 'image-search/vie-ch-re-s-n-gal-inflation-prix-aliment-3.webp',
                        '06', 'POUVOIR D\'ACHAT', 'La question qui domine le débat',
                        'ENJEU', C_TEAL, None)
    else:
        img = kb_src(os.path.join(ROOT, 'assets/press-conf.png'), W, H)
        dim(img, 0, 0, W, H, 150)
        d = ImageDraw.Draw(img, 'RGBA')
        text(d, (W / 2, 560), 'COMMENT', Oswald(110), C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, 720), 'TENIR JUSQU\'À', Oswald(100), C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, 880), 'LA FIN DU MOIS ?', Oswald(100), C_GOLD, anchor='mm', stroke=2)
        a = P(t - t0, 0.4, 1.0)
        if a > 0:
            lg = logo(90)
            img.paste(lg, (int(W / 2 - 220), 1060), lg)
            text(d, (int(W / 2 - 110), 1105), 'SNGAL INFOS', Oswald(56), C_GOLD, anchor='lm')
            text(d, (W / 2, 1280), 'La suite sur SNGAL INFOS', Inter(42), C_TXT, anchor='mm', stroke=2)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)

    if p < 0.05:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.5 * (1 - p / 0.05))
    if p > 0.94:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.45 * ((p - 0.94) / 0.06))
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'vie-chere-greve-9x16.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'vc-9x16-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', '-shortest', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.0f}s')

if __name__ == '__main__':
    main()
