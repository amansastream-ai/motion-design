"""« Pirogues disparues — les 5 points clés » — format 16:9 (1:12) viral.
SNGAL INFOS · Direct spécial du 27 nov 2026 · 7 segments · voice-02.
Run: pytools/bin/python tools/render_pg_16x9.py
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
DUR = 72.5

C_BG = (7, 13, 22)
C_TXT = (238, 242, 248)
C_MUT = (146, 160, 176)
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
SRC = 'Source : SNGAL INFOS · Direct spécial du 27 novembre 2026'

CARDS = {
    'hook': dict(img='image-search/pg-yoff-quai.jpg', num=None,
                 kicker='SNGAL INFOS · DIRECT SPÉCIAL',
                 lines=['PIROGUES DISPARUES'],
                 subs=['Les 5 points clés de notre grand débat'],
                 accent=C_RED),
    's1': dict(img='image-search/pg-yoff-quai.jpg', num='01',
               kicker='POINT 01 · L\'ALERTE',
               lines=['PIROGUES SANS NOUVELLES'],
               subs=['Yoff · Ngor · Ouakam · Cambérène · Thiaroye',
                     'Naufrages à Yenne, Sendou et Thieppe'],
               accent=C_RED),
    's2': dict(img='image-search/pg-yoff-plage.jpg', num='02',
               kicker='POINT 02 · LES FAMILLES',
               lines=['L\'ATTENTE DÉSESPÉRÉE'],
               subs=['Des centaines de familles attendent un signe de vie',
                     'Au Sénégal comme dans la diaspora'],
               accent=C_WARM),
    's3': dict(img='image-search/pg-mer-secours.jpg', num='03',
               kicker='POINT 03 · LA DÉRIVE',
               lines=['ROUTE DES CANARIES'],
               subs=['Des embarcations dérivent des semaines en mer',
                     '« Barça ou Barsakh »'],
               accent=C_TEAL),
    's4': dict(img='image-search/pg-port-secours.jpg', num='04',
               kicker='POINT 04 · L\'ENQUÊTE',
               lines=['RÉSEAUX DE PASSEURS'],
               subs=['Enquêtes judiciaires en cours',
                     'Opérations de la Marine nationale sénégalaise'],
               accent=C_STEEL),
    's5': dict(img='image-search/pg-yoff-plage.jpg', num='05',
               kicker='POINT 05 · LES RÉACTIONS',
               lines=['SÉNÉGAL & DIASPORA'],
               subs=['Témoignages · réponse des autorités',
                     'Pistes de solutions pour la jeunesse'],
               accent=C_GOLD),
    'out': dict(img='image-search/pg-yoff-quai.jpg', num=None,
                kicker='LE DIRECT INTÉGRAL',
                lines=['SUR SNGAL INFOS'],
                subs=['Partagez cette info, elle peut sauver une vie',
                      'WhatsApp Studio : +221 77 679 28 21 · sngal.info'],
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
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(22))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.32)
        sw, sh = im.size
        scale = min(w * 0.88 / sw, h * 0.88 / sh)
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
    return Image.blend(base, grad, 0.45)

def scrim_left(img, a=210):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x in range(0, W, 4):
        k = x / W
        aa = int(a * max(0.0, 1.0 - k * 1.45))
        d.rectangle([x, 0, x + 4, H], fill=(5, 9, 16, aa))
    img.paste(ov, (0, 0), ov)

def header(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 60], fill=(9, 15, 24, 225))
    d.line([(0, 60), (W, 60)], fill=(28, 41, 56, 255), width=2)
    d.rectangle([0, 0, 8, 60], fill=C_RED + (255,))
    lg = logo(44)
    img.paste(lg, (18, 8), lg)
    text(d, (72, 10), 'SNGAL INFOS', Oswald(30), (242, 246, 252), anchor='lm')
    d.rectangle([262, 12, 426, 48], fill=(178, 32, 22, 235))
    text(d, (344, 31), 'LE JOURNAL', Inter(18, True), (255, 232, 226), anchor='mm')
    text(d, (W - 26, 31), 'DIRECT SPÉCIAL · NOV 2026', Inter(19, True), C_MUT, anchor='rm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 52, W, H], fill=(8, 13, 21, 235))
    d.line([(0, H - 52), (W, H - 52)], fill=C_RED + (255,), width=3)
    cycle = '     ·     '.join([
        'PIROGUES PORTÉES DISPARUES : YOFF, NGOR, OUAKAM, CAMBÉRÈNE, THIAROYE',
        'NAUFRAGES À YENNE, SENDOU ET THIEPPE',
        'ROUTE DES CANARIES : DES EMBARCATIONS À LA DÉRIVE',
        'DIRECT INTÉGRAL SUR SNGAL INFOS · #PIROGUESDISPARUES',
    ]) + '     ·     '
    f = Inter(19)
    sp = f.getbbox(cycle)[2]
    off = int((t * 75) % sp)
    text(d, (-off, H - 26), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, H - 26), cycle, f, (214, 224, 236), anchor='lm')

def frame(t):
    kind, t0, t1 = seg_at(t)
    c = CARDS[kind]
    img = blend_to_bg(kb_src(os.path.join(ROOT, c['img']), W, H))
    scrim_left(img, 225 if kind != 'out' else 245)
    d = ImageDraw.Draw(img, 'RGBA')
    rel = t - t0

    if c['num']:
        a = ease(P(rel, 0, 0.25))
        if a > 0:
            r = int(64 * a)
            cx, cy = W - 130, 160
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c['accent'] + (255,), width=3)
            if a > 0.6:
                text(d, (cx, cy), c['num'], Oswald(58), c['accent'], anchor='mm')

    k0 = ease(P(rel, 0.02, 0.2))
    if k0 > 0:
        text(d, (56, 128 + (1 - k0) * 14), c['kicker'], Inter(20, True), c['accent'], stroke=2)

    for i, line in enumerate(c['lines']):
        a = ease(P(rel, 0.08 + i * 0.12, 0.34 + i * 0.12))
        if a > 0:
            size = 62
            f = Oswald(size)
            while f.getbbox(line)[2] > W - 320 and size > 40:
                size -= 2
                f = Oswald(size)
            text(d, (56 + (1 - a) * 26, 176 + i * 76), line, f,
                 C_TXT if i == 0 else c['accent'], stroke=2)

    ab = ease(P(rel, 0.36, 0.55))
    if ab > 0:
        bar = Image.new('RGBA', (int(520 * ab), 6), c['accent'] + (255,))
        img.paste(bar, (56, 356), bar)

    for j, s in enumerate(c['subs']):
        a = ease(P(rel, 0.5 + j * 0.16, 0.8 + j * 0.16))
        if a > 0:
            text(d, (56, 392 + j * 40), s, Inter(22), C_TXT if a > 0.85 else C_MUT, stroke=1)

    if kind == 'out':
        a = ease(P(rel, 1.6, 2.1))
        if a > 0:
            bw, bh = int(360 * a), int(64 * a)
            badge = Image.new('RGBA', (bw, bh), (232, 178, 42, int(255 * a)))
            img.paste(badge, (56, 500), badge)
            if a > 0.75:
                text(d, (56 + bw / 2, 532), 'ABONNEZ-VOUS', Oswald(34), (12, 16, 24), anchor='mm')
        a2 = ease(P(rel, 2.2, 2.7))
        if a2 > 0:
            lg = logo(56)
            img.paste(lg, (440, 504), lg)
            text(d, (512, 532), 'SNGAL INFOS', Oswald(40), C_GOLD, anchor='lm')

    text(d, (56, H - 76), SRC, Inter(14, True), C_MUT)
    header(img, t)
    ticker(img, t)
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'pirogues-disparues-16x9.mp4')
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
