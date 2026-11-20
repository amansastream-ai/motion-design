"""« Séquestration présumée à Pikine » — Short vertical 9:16 (1:52).
6 segments · voix voice-02 (mêmes clips que le 16:9) · SNGAL INFOS + logo.
ACCUSATIONS != CULPABILITÉ à l'écran (strip Inter). Anonymat victime préservé.
Run: pytools/bin/python tools/render_pk_9x16.py
"""
import os
import sys
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from glyphs import text_neq, textw_neq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FDIR = os.path.join(ROOT, 'assets', 'fonts')
Oswald = lambda s: ImageFont.truetype(os.path.join(FDIR, 'Oswald-700.ttf'), s)
Inter = lambda s, b=False: ImageFont.truetype(
    os.path.join(FDIR, 'Inter-600.ttf' if b else 'Inter-400.ttf'), s)

W, H, FPS = 1080, 1920, 24
DUR = 112.88

C_BG = (7, 13, 22)
C_PANEL = (14, 21, 32)
C_LINE = (30, 42, 58)
C_TXT = (238, 242, 248)
C_MUT = (148, 162, 178)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_TEAL = (42, 184, 162)
C_STEEL = (110, 160, 220)
C_RED = (214, 64, 48)

SEGS = [
    ('intro', 0,      18.47),
    ('j1',    18.47,  35.98),
    ('j2',    35.98,  55.24),
    ('j3',    55.24,  73.48),
    ('j4',    73.48,  88.15),
    ('j5',    88.15, 107.88),
    ('outro', 107.88, 112.88),
]
VERBATIM = 'ACCUSATIONS \u2260 CULPABILITÉ · SOURCE : LERAL.NET · SÉNÉGAL+1'

_LOGO_CACHE = {}

def logo(size):
    if size not in _LOGO_CACHE:
        lg = Image.open(os.path.join(ROOT, 'assets', 'logo-sngal.png')).convert('RGBA')
        _LOGO_CACHE[size] = lg.resize((size, size), Image.LANCZOS)
    return _LOGO_CACHE[size]

def seg_at(t):
    for k, t0, t1 in SEGS:
        if t0 <= t < t1:
            return k, t0, t1
    return SEGS[-1]

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
    if im.width < w * 0.62 or im.height < h * 0.62:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(24))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.30)
        sw, sh = im.size
        scale = min(w * 0.9 / sw, h * 0.9 / sh)
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
    for y in range(0, H, 30):
        a = 6 + int(5 * np.sin(2 * np.pi * (y / 300 + drift)))
        d.line([(W // 2, y), (W // 2, y + 14)], fill=(a + 20, a + 32, a + 48), width=2)
    return img

def blend_to_bg(base):
    grad = Image.new('RGB', (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, H, 2):
        k = y / H
        gd.rectangle([0, y, W, y + 2], fill=(int(6 + 10 * k), int(12 + 12 * k), int(20 + 14 * k)))
    return Image.blend(base, grad, 0.42)

def dim(img, x, y, w, h, a=120):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, a))
    img.paste(ov, (x, y), ov)

def vignette(img, x, y, w, h):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(26):
        d.rectangle([i * 2, i * 2, w - i * 2, h - i * 2], outline=(0, 0, 0, int(1 + i * 0.7)))
    img.paste(ov, (x, y), ov)

def bottom_verbatim(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 96, W, H], fill=(6, 10, 17, 240))
    d.line([(0, H - 96), (W, H - 96)], fill=C_STEEL + (255,), width=3)
    text_neq(d, (W / 2, H - 48), VERBATIM, Inter(20), (216, 226, 238), anchor='mm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 150, W, H - 96], fill=(8, 13, 21, 235))
    d.line([(0, H - 150), (W, H - 150)], fill=C_WARM + (255,), width=3)
    cycle = '   ·   '.join([
        'SÉQUESTRATION ET VIOLENCES DÉNONCÉES À PIKINE',
        'UN SUSPECT INTERPELLÉ · PRÉSOMPTION D\'INNOCENCE',
        'L\'ENQUÊTE EST EN COURS',
    ]) + '   ·   '
    f = Oswald(26)
    sp = textw(cycle, f)
    off = int((t * 90) % sp)
    y = H - 123
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')

def header_bar(img):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 140], fill=(9, 15, 24, 235))
    d.line([(0, 140), (W, 140)], fill=C_LINE + (255,), width=2)
    d.rectangle([0, 0, 12, 140], fill=C_RED + (255,))
    lg = logo(88)
    img.paste(lg, (30, 26), lg)
    text(d, (132, 46), 'SNGAL INFOS', Oswald(52), (242, 246, 252), anchor='lm')
    text(d, (132, 108), 'FAITS DIVERS · NOV 2026', Inter(22, True), C_WARM, anchor='lm')

def story_card(kind, path, lines, kicker, accent, t, t0, appear):
    img = kb_src(path, W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 128)
    vignette(img, 0, 0, W, H)
    d = ImageDraw.Draw(img, 'RGBA')
    ph = int(ease(P(t - t0, 0, 0.22)) * 150)
    if ph > 2:
        panel = Image.new('RGBA', (W, ph), (8, 13, 21, 235))
        img.paste(panel, (0, 180), panel)
        d.rectangle([60, 180, 132, 180 + ph], fill=accent + (255,))
        text(d, (60, 252), kicker, Inter(24, True), (232, 238, 246), anchor='lm')
    k1 = ease(P(t - t0, 0.12, 0.34))
    if k1 > 0:
        text(d, (60 + (1 - k1) * 24, 420), lines[0], Oswald(72), C_TXT, stroke=2)
    k2 = ease(P(t - t0, 0.22, 0.48))
    if k2 > 0:
        text(d, (60 + (1 - k2) * 24, 520), lines[1], Oswald(72), accent, stroke=2)
    k3 = ease(P(t - t0, 0.42, 0.7))
    if k3 > 0:
        bar = Image.new('RGBA', (int(660 * k3), 8), accent + (255,))
        img.paste(bar, (60, 660), bar)
        if k3 > 0.5:
            text(d, (60, 700), 'La parole aux victimes.', Inter(28), C_TXT, anchor='lm')
            text(d, (60, 742), 'La justice suivra son cours.', Inter(28), C_TXT, anchor='lm')
    header_bar(img)
    ticker(img, t)
    bottom_verbatim(img, t)
    return img

CARDS = {
    'intro': dict(kind='intro',
                  img='image-search/pikine-s-n-gal-rue-ville-banlieue-dakar-2.jpg',
                  lines=['SÉQUESTRATION', 'PRÉSUMÉE À PIKINE'], kicker='PIKINE · FAITS DIVERS', accent=C_WARM),
    'j1': dict(kind='j1', img='image-search/pikine-s-n-gal-rue-ville-banlieue-dakar-2.jpg',
               lines=['UNE FAUSSE', "PROMESSE D'EMPLOI"], kicker='LE RÉCIT', accent=C_STEEL),
    'j2': dict(kind='j2', img='image-search/commissariat-police-gendarmerie-s-n-gal--1.jpg',
               lines=['UN SUSPECT', 'INTERPELLÉ'], kicker="L'INTERPELLATION", accent=C_RED),
    'j3': dict(kind='j3', img='image-search/pikine-s-n-gal-rue-ville-banlieue-dakar-2.jpg',
               lines=['FAUSSES OFFRES', "D'EMPLOI"], kicker='LE PIÈGE', accent=C_GOLD),
    'j4': dict(kind='j4', img='image-search/palais-de-justice-tribunal-dakar-s-n-gal-2.jpg',
               lines=['CE QUE', 'DIT LA LOI'], kicker='LE CADRE LÉGAL', accent=C_STEEL),
    'j5': dict(kind='j5', img='image-search/commissariat-police-gendarmerie-s-n-gal--1.jpg',
               lines=['ENQUÊTE', 'EN COURS'], kicker='LE DÉBAT', accent=C_TEAL),
}

def outro_card(t, t0):
    img = kb_src(os.path.join(ROOT, 'image-search/palais-de-justice-tribunal-dakar-s-n-gal-2.jpg'), W, H)
    img = blend_to_bg(img)
    dim(img, 0, 0, W, H, 155)
    d = ImageDraw.Draw(img, 'RGBA')
    appear = P(t - t0, 0, 0.3)
    text(d, (W / 2, 620), 'LA SUITE DANS', Oswald(72), C_TXT, anchor='mm')
    text(d, (W / 2, 720), 'LE REPORTAGE', Oswald(72), C_GOLD, anchor='mm')
    p = ease(appear)
    bar = Image.new('RGBA', (int(660 * p), 8), C_WARM + (255,))
    img.paste(bar, ((W - 660) // 2, 800), bar)
    text_neq(d, (W / 2, 880), 'Accusations \u2260 culpabilité · présomption d\'innocence', Inter(30), C_TXT, anchor='mm')
    a = P(t - t0, 0.5, 1.1)
    if a > 0:
        lg = logo(120)
        img.paste(lg, (W // 2 - 170, 990), lg)
        text(d, (W // 2 + 10, 1055), 'SNGAL INFOS', Oswald(64), C_GOLD, anchor='lm')
    text(d, (W / 2, 1140), 'Source : Leral.net · Sénégal+1', Inter(26, True), C_MUT, anchor='mm')
    header_bar(img)
    ticker(img, t)
    bottom_verbatim(img, t)
    return img

def frame(t):
    kind, t0, t1 = seg_at(t)
    if kind == 'outro':
        return outro_card(t, t0)
    c = CARDS[kind]
    return story_card(c['kind'], os.path.join(ROOT, c['img']), c['lines'], c['kicker'],
                      c['accent'], t, t0, P(t - t0, 0, 0.3))

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'pikine-sequestration-9x16.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'pk-short-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.1f}s')

if __name__ == '__main__':
    main()
