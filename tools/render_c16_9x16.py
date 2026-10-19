"""« Les 7 points » — 9x16 Short (90 s), voix journaliste (voice-02).
Run: pytools/bin/python tools/render_c16_9x16.py
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

SEGS = [
    ('intro', 0, 6), ('j1', 6, 25), ('j2', 25, 55),
    ('j3', 55, 72), ('recap', 72, 82), ('outro', 82, 90),
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
    x = (nw - w) // 2
    y = int((nh - h) * 0.38)
    return im.crop((x, y, x + w, y + h))

def kb_src(path, w, h, cx=0.5, cy=0.4):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.72 or im.height < h * 0.72:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(26))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.30)
        sw, sh = im.size
        scale = min(w * 0.86 / sw, h * 0.62 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        fg = im.resize((nw, nh), Image.LANCZOS)
        plate.paste(fg, (int((w - nw) * cx), int((h - nh) * cy)))
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
    items = ['LA LFR 2026 À L\'EXAMEN', 'GASOIL 755→867 : NON CONFIRMÉ',
             'SUBVENTIONS −30 %', 'LE PRES « SABOTÉ » ?', 'UN DÉFI AU PREMIER MINISTRE']
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
        img = kb_src(os.path.join(ROOT, 'image-search/ousmane-sonko-conf-rence-de-presse-micro-4.jpg'), W, H, cy=0.3)
        dim(img, 0, 0, W, H, 130)
        d = ImageDraw.Draw(img, 'RGBA')
        for i2, line in enumerate(['7 POINTS', 'QUI FONT', 'DÉBAT']):
            off = int((1 - ease(P(t, 0.15 + i2 * 0.12, 0.7 + i2 * 0.12))) * 40)
            text(d, (60 + off, 620 + i2 * 175), line, Oswald(160), C_TXT, stroke=2)
        a = P(t, 1.2, 1.8)
        if a > 0:
            bar = Image.new('RGBA', (int(700 * a), 12), C_WARM + (255,))
            img.paste(bar, (60, 1180), bar)
            text(d, (60, 1230), 'Ousmane Sonko · conférence du 19 octobre 2026', Inter(40), C_TXT, stroke=2)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)
    elif kind == 'j1':
        stage = (t - t0) // 6.7
        cards = [
            (os.path.join('image-search/ousmane-sonko-conf-rence-de-presse-micro-1.jpg'),
             '01', 'PASTEF DIT NON', 'PASTEF ne votera pas la LFR en l\'état', 'NON', C_WARM, None),
            (os.path.join('image-search/station-service-pompe-gasoil-prix-carbur-2.jpg'),
             '02', 'GASOIL 755 → 867 FCFA', 'Une hausse potentielle — non confirmée', 'MENACE', C_GOLD,
             'Hausse non confirmée'),
            (os.path.join('assets/gas-station.png'),
             '03', 'SUBVENTIONS −30 %', '790 → 552 milliards de FCFA', '−30 %', C_WARM,
             'À confronter aux documents officiels'),
        ]
        if stage >= 3:
            stage = 2
        c = cards[int(stage)]
        img = mini_card(t, t0 + stage * 6.7, c[0], c[1], c[2], c[3], c[4], c[5], c[6])
    elif kind == 'j2':
        stage = 0 if (t - t0) < 15 else 1
        cards = [
            (os.path.join('image-search/station-service-pompe-gasoil-prix-carbur-3.jpg'),
             '05', 'LE PRES « SABOTÉ »', '« Un excellent plan » — environ 300 Md générés', 'ACCUSATION', C_WARM,
             'Accusation : réponse contradictoire'),
            (os.path.join('image-search/ahmadou-al-amine-l-premier-ministre-s-n--2.jpg'),
             '07', 'LE DÉFI AU PM', 'Un débat public face au Premier ministre', 'DÉFI', C_GOLD, None),
        ]
        c = cards[stage]
        img = mini_card(t, t0 + stage * 15, c[0], c[1], c[2], c[3], c[4], c[5], c[6])
    elif kind == 'j3':
        img = kb_src(os.path.join(ROOT, 'assets/press-conf.png'), W, H)
        dim(img, 0, 0, W, H, 135)
        d = ImageDraw.Draw(img, 'RGBA')
        a = ease(P(t - t0, 0, 0.5))
        panel = Image.new('RGBA', (W - 100, 420), (12, 20, 32, int(238 * a)))
        img.paste(panel, (50, 800), panel)
        d.rectangle([50, 800, W - 51, 1220], outline=C_GOLD + (int(230 * a),), width=4)
        text(d, (W / 2, 900), 'ENTRE REFUS ET EXAMEN,', Oswald(58), C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, 980), 'QUEL BUDGET POUR', Oswald(58), C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, 1060), 'LES SÉNÉGALAIS ?', Oswald(58), C_GOLD, anchor='mm', stroke=2)
        text(d, (W / 2, 1150), 'Le texte est à la croisée des chemins', Inter(36), C_MUT, anchor='mm')
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)
    elif kind == 'recap':
        img = kb_src(os.path.join(ROOT, 'image-search/ousmane-sonko-conf-rence-de-presse-micro-2.jpg'), W, H)
        dim(img, 0, 0, W, H, 165)
        d = ImageDraw.Draw(img, 'RGBA')
        text(d, (W / 2, 420), 'LES 7 POINTS', Oswald(110), C_TXT, anchor='mm', stroke=2)
        items = [
            '01 · PASTEF dit non à la LFR', '02 · Gasoil 755 → 867 FCFA ?',
            '03 · Subventions −30 %', '04 · Éducation & routes en baisse',
            '05 · Le PRES « saboté » ?', '06 · Divergences au sommet',
            '07 · Défi : un débat au PM',
        ]
        for i2, line in enumerate(items):
            a = P(t - t0, 0.2 + i2 * 0.12, 0.7 + i2 * 0.12)
            if a > 0:
                text(d, (W / 2, 560 + i2 * 86), line, Inter(42), C_TXT if a > 0.9 else C_MUT, anchor='mm', stroke=1)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)
    else:
        img = kb_src(os.path.join(ROOT, 'assets/press-conf.png'), W, H)
        dim(img, 0, 0, W, H, 150)
        d = ImageDraw.Draw(img, 'RGBA')
        text(d, (W / 2, 620), 'SUIVEZ', Oswald(120), C_TXT, anchor='mm', stroke=2)
        text(d, (W / 2, 780), 'INFO 7', Oswald(150), C_GOLD, anchor='mm', stroke=2)
        text(d, (W / 2, 1000), 'politique · société · débat', Inter(44), C_MUT, anchor='mm')
        a = P(t - t0, 0.6, 1.2)
        if a > 0:
            bar = Image.new('RGBA', (int(700 * a), 12), C_WARM + (255,))
            img.paste(bar, (190, 1100), bar)
            text(d, (W / 2, 1210), 'Le détail dans notre reportage', Inter(42), C_TXT, anchor='mm', stroke=2)
        header_v(img, 'EN DIRECT')
        ticker_v(img, t)

    if p < 0.05:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.5 * (1 - p / 0.05))
    if p > 0.94:
        img = Image.blend(img, Image.new('RGB', (W, H), C_BG), 0.45 * ((p - 0.94) / 0.06))
    return img

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'les-7-points-conference-9x16.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'c9-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', '-shortest', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.0f}s')

if __name__ == '__main__':
    main()
