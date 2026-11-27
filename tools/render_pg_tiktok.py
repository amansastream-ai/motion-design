"""« Pirogues disparues — les 5 points clés » — format TikTok 9:16 (1:12) viral.
SNGAL INFOS · Direct spécial du 27 nov 2026 · 7 segments · voice-02.
Run: pytools/bin/python tools/render_pg_tiktok.py
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
DUR = 72.5

C_BG = (7, 13, 22)
C_TXT = (240, 244, 250)
C_MUT = (152, 166, 182)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_TEAL = (42, 184, 162)
C_STEEL = (110, 160, 220)
C_RED = (214, 64, 48)

SEGS = [
    ('hook', 0.00,  8.43),
    ('s1',   8.43, 21.11),
    ('s2',  21.11, 28.80),
    ('s3',  28.80, 38.79),
    ('s4',  38.79, 49.54),
    ('s5',  49.54, 57.69),
    ('out', 57.69, 72.50),
]
SRC = 'SNGAL INFOS · DIRECT SPÉCIAL · 27 NOV 2026'

CARDS = {
    'hook': dict(img='image-search/pg-yoff-quai.jpg', num=None,
                 kicker='SNGAL INFOS · DIRECT SPÉCIAL',
                 lines=['PIROGUES', 'DISPARUES'],
                 subs=['Les 5 points clés de notre grand débat'],
                 accent=C_RED),
    's1': dict(img='image-search/pg-yoff-quai.jpg', num='01',
               kicker='POINT 01 · L\'ALERTE',
               lines=['PIROGUES SANS', 'NOUVELLES'],
               subs=['Yoff · Ngor · Ouakam · Cambérène · Thiaroye',
                     'Naufrages à Yenne, Sendou et Thieppe'],
               accent=C_RED),
    's2': dict(img='image-search/pg-yoff-plage.jpg', num='02',
               kicker='POINT 02 · LES FAMILLES',
               lines=['L\'ATTENTE', 'DÉSESPÉRÉE'],
               subs=['Des centaines de familles', 'attendent un signe de vie'],
               accent=C_WARM),
    's3': dict(img='image-search/pg-mer-secours.jpg', num='03',
               kicker='POINT 03 · LA DÉRIVE',
               lines=['ROUTE DES', 'CANARIES'],
               subs=['Des embarcations dérivent des semaines en mer',
                     '« Barça ou Barsakh »'],
               accent=C_TEAL),
    's4': dict(img='image-search/pg-port-secours.jpg', num='04',
               kicker='POINT 04 · L\'ENQUÊTE',
               lines=['RÉSEAUX DE', 'PASSEURS'],
               subs=['Enquêtes judiciaires en cours',
                     'Opérations de la Marine nationale'],
               accent=C_STEEL),
    's5': dict(img='image-search/pg-yoff-plage.jpg', num='05',
               kicker='POINT 05 · LES RÉACTIONS',
               lines=['SÉNÉGAL &', 'DIASPORA'],
               subs=['Témoignages · réponse des autorités',
                     'Pistes de solutions pour la jeunesse'],
               accent=C_GOLD),
    'out': dict(img='image-search/pg-yoff-quai.jpg', num=None,
                kicker='LE DIRECT INTÉGRAL',
                lines=['SUR SNGAL', 'INFOS'],
                subs=['Partagez cette info, elle peut sauver une vie',
                      'WhatsApp Studio : +221 77 679 28 21'],
                accent=C_GOLD),
}

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

def kb_src(path, w, h):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.62 or im.height < h * 0.62:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(24))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.30)
        sw, sh = im.size
        scale = min(w * 0.92 / sw, h * 0.92 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), ((w - nw) // 2, (h - nh) // 2))
        return plate
    return cover(im, w, h)

def text(d, xy, s, f, fill, anchor=None, stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

def blend_to_bg(base):
    grad = Image.new('RGB', (W, H))
    gd = ImageDraw.Draw(grad)
    for y in range(0, H, 2):
        k = y / H
        gd.rectangle([0, y, W, y + 2], fill=(int(6 + 10 * k), int(12 + 12 * k), int(20 + 14 * k)))
    return Image.blend(base, grad, 0.42)

def dim(img, a):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, a))
    img.paste(ov, (0, 0), ov)

def vignette(img):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(26):
        d.rectangle([i * 2, i * 2, W - i * 2, H - i * 2], outline=(0, 0, 0, int(1 + i * 0.8)))
    img.paste(ov, (0, 0), ov)

def header(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 140], fill=(9, 15, 24, 235))
    d.line([(0, 140), (W, 140)], fill=C_LINE if False else (30, 42, 58, 255), width=2)
    d.rectangle([0, 0, 12, 140], fill=(214, 64, 48, 255))
    lg = logo(88)
    img.paste(lg, (30, 26), lg)
    text(d, (132, 46), 'SNGAL INFOS', Oswald(52), (242, 246, 252), anchor='lm')
    text(d, (132, 108), 'DIRECT SPÉCIAL · NOV 2026', Inter(22, True), (232, 92, 42), anchor='lm')

def bottom(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 150, W, H], fill=(8, 13, 21, 238))
    d.line([(0, H - 150), (W, H - 150)], fill=(214, 64, 48, 255), width=3)
    cycle = '   ·   '.join([
        'PIROGUES PORTÉES DISPARUES : YOFF · NGOR · OUAKAM · CAMBÉRÈNE · THIAROYE',
        'NAUFRAGES À YENNE · SENDOU · THIEPPE',
        'ROUTE DES CANARIES : EMBARCATIONS À LA DÉRIVE',
        '#PIROGUESDISPARUES',
    ]) + '   ·   '
    f = Oswald(27)
    sp = f.getbbox(cycle)[2]
    off = int((t * 95) % sp)
    text(d, (-off, H - 118), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, H - 118), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (W / 2, H - 48), SRC, Inter(22, True), (152, 166, 182), anchor='mm')

def frame(t):
    kind, t0, t1 = seg_at(t)
    c = CARDS[kind]
    img = blend_to_bg(kb_src(os.path.join(ROOT, c['img']), W, H))
    dim(img, 132 if kind != 'out' else 168)
    vignette(img)
    d = ImageDraw.Draw(img, 'RGBA')
    rel = t - t0

    if c['num']:
        a = ease(P(rel, 0, 0.25))
        if a > 0:
            x1, y1 = W - 60, 300
            d.rectangle([x1 - int(200 * a), y1, x1, y1 + int(200 * a)],
                        fill=(9, 15, 24, int(215 * a)))
            d.rectangle([x1 - int(200 * a), y1, x1 - int(200 * a) + 12, y1 + int(200 * a)],
                        fill=c['accent'] + (int(255 * a),))
            if a > 0.6:
                text(d, (x1 - 94, y1 + 102), c['num'], Oswald(120), c['accent'], anchor='mm')

    k0 = ease(P(rel, 0.02, 0.2))
    if k0 > 0:
        text(d, (70, 300 + (1 - k0) * 18), c['kicker'], Inter(30, True), c['accent'], anchor='lm')

    for i, line in enumerate(c['lines']):
        a = ease(P(rel, 0.08 + i * 0.12, 0.34 + i * 0.12))
        if a > 0:
            text(d, (70 + (1 - a) * 30, 420 + i * 128), line, Oswald(104),
                 C_TXT if i == 0 else c['accent'], stroke=2)

    ab = ease(P(rel, 0.36, 0.55))
    if ab > 0:
        bar = Image.new('RGBA', (int(720 * ab), 10), c['accent'] + (255,))
        img.paste(bar, (70, 700), bar)

    for j, s in enumerate(c['subs']):
        a = ease(P(rel, 0.5 + j * 0.16, 0.8 + j * 0.16))
        if a > 0:
            text(d, (70, 760 + j * 64), s, Inter(36), C_TXT if a > 0.85 else C_MUT)

    if kind == 'out':
        a = ease(P(rel, 1.6, 2.1))
        if a > 0:
            bw, bh = int(620 * a), int(110 * a)
            x0 = 70
            y0 = 960
            badge = Image.new('RGBA', (bw, bh), (232, 178, 42, int(255 * a)))
            img.paste(badge, (x0, y0), badge)
            if a > 0.75:
                text(d, (x0 + bw / 2, y0 + bh / 2), 'ABONNEZ-VOUS', Oswald(56), (12, 16, 24), anchor='mm')
        a2 = ease(P(rel, 2.2, 2.7))
        if a2 > 0:
            lg = logo(96)
            img.paste(lg, (70, 1120), lg)
            text(d, (190, 1168), 'SNGAL INFOS', Oswald(52), C_GOLD, anchor='lm')

    header(img, t)
    bottom(img, t)
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'pirogues-disparues-tiktok.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'pg-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.1f}s')

if __name__ == '__main__':
    main()
