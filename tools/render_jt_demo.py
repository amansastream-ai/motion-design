"""Démo JT SNGAL INFOS — présentatrice à l'antenne + reportage (16:9, 1:13).
Aïssatou Ndiaye (voice-06) présente à l'image (VRAIE synchronisation levres,
clips animes par tools/talking_face.py), puis les images + la voix off
(voice-02) comme d'habitude, sign-off presentatrice, outro.
Run: pytools/bin/python tools/render_jt_demo.py
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
DUR = 73.0

C_BG = (7, 13, 22)
C_PANEL = (15, 23, 34)
C_LINE = (28, 41, 56)
C_TXT = (232, 238, 246)
C_MUT = (138, 154, 172)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_STEEL = (110, 160, 220)
C_RED = (214, 64, 48)

SEGS = [
    ('anchor1',  0,    14.81),
    ('p1',   14.81,   24.95),
    ('p2',   24.95,   37.78),
    ('p3',   37.78,   51.50),
    ('p4',   51.50,   61.81),
    ('anchor2', 61.81, 66.50),
    ('outro', 66.50,  73.0),
]
ANCHOR_VIDEOS = {
    'anchor1': (os.path.join(ROOT, 'audio', 'anchor-intro-talking.mp4'), 0.0),
    'anchor2': (os.path.join(ROOT, 'audio', 'anchor-outro-talking.mp4'), 61.81),
}
CLIP_FPS = 25.0

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

def text(d, xy, s, f, fill, anchor=None, stroke=0):
    d.text(xy, s, font=f, fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

def textw(s, f):
    return f.getbbox(s)[2]

def kb_src(path, w, h, cx=0.5, cy=0.42):
    im = Image.open(path).convert('RGB')
    if im.width < w * 0.72 or im.height < h * 0.72:
        plate = cover(im, w, h).filter(ImageFilter.GaussianBlur(22))
        plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.32)
        sw, sh = im.size
        scale = min(w * 0.82 / sw, h * 0.82 / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        plate.paste(im.resize((nw, nh), Image.LANCZOS), (int((w - nw) * cx), int((h - nh) * cy)))
        return plate
    return cover(im, w, h)

def cover(img, w, h):
    im = img.convert('RGB')
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * 0.38)
    return im.crop((x, y, x + w, y + h))

def dim(img, x, y, w, h, a=120):
    ov = Image.new('RGBA', (w, h), (0, 0, 0, a))
    img.paste(ov, (x, y), ov)

def header_bar(img):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, 0, W, 60], fill=(9, 15, 24, 225))
    d.line([(0, 60), (W, 60)], fill=C_LINE + (255,), width=2)
    d.rectangle([0, 0, 8, 60], fill=C_RED + (255,))
    lg = logo(44)
    img.paste(lg, (18, 8), lg)
    text(d, (72, 10), 'SNGAL INFOS', Oswald(30), (242, 246, 252), anchor='lm')
    d.rectangle([262, 12, 426, 48], fill=(178, 32, 22, 235))
    text(d, (344, 31), 'LE JOURNAL', Inter(18, True), (255, 232, 226), anchor='mm')
    text(d, (W - 26, 31), 'DAKAR · 8 NOV 2026', Inter(19, True), C_MUT, anchor='rm')

def ticker(img, t):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle([0, H - 52, W, H], fill=(8, 13, 21, 235))
    d.line([(0, H - 52), (W, H - 52)], fill=C_RED + (255,), width=3)
    items = [
        'LE JOURNAL DE SNGAL INFOS',
        'NAUFRAGE AU LARGE DE KÉBÉMER : 34 MORTS ET UN SEUL RESCAPÉ',
        'ENCORE DES JEUNES PERDUS EN MER · JUSQU\'À QUAND ?',
    ]
    cycle = '     ·     '.join(items) + '     ·     '
    f = Inter(19)
    sp = textw(cycle, f)
    off = int((t * 75) % sp)
    y = H - 26
    text(d, (-off, y), cycle, f, (214, 224, 236), anchor='lm')
    text(d, (-off + sp, y), cycle, f, (214, 224, 236), anchor='lm')


# ---------- lecture des clips presentatrice (lip-sync reel) ----------
class ClipReader:
    """Lecture sequentielle avec cache d'une frame (les segments sont lus dans l'ordre)."""
    def __init__(self, path):
        import cv2
        self.cv2 = cv2
        self.cap = cv2.VideoCapture(path)
        self.last = -1
        self.frame = None

    def get(self, idx):
        if idx == self.last and self.frame is not None:
            return self.frame
        if idx != self.last + 1:
            self.cap.set(self.cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = self.cap.read()
        if not ok:
            self.cap.set(self.cv2.CAP_PROP_POS_FRAMES, max(0, idx - 1))
            ok, fr = self.cap.read()
        self.frame = fr
        self.last = idx
        return fr


CLIPS = {}
FOCUS_Y = 0.26


def setup():
    for k, (path, _t0) in ANCHOR_VIDEOS.items():
        CLIPS[k] = ClipReader(path)


def panelize(fr_bgr, zoom=1.0):
    """Frame clip (portrait 1376x1712) -> panneau WxH (cover, biais vertical FOCUS_Y)."""
    im = Image.fromarray(fr_bgr[:, :, ::-1])
    sw, sh = im.size
    scale = max(W / sw, H / sh) * zoom
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - W) // 2
    y = int((nh - H) * FOCUS_Y)
    return im.crop((x, y, x + W, y + H)).convert('RGB')


def anchor_scene(kind, t, t0):
    appear = P(t - t0, 0.02, 0.3)
    path, v0 = ANCHOR_VIDEOS[kind]
    fi = max(0, int((t - v0) * CLIP_FPS))
    fr = CLIPS[kind].get(fi)
    prog = P(t - t0, 0, 6)
    zoom = 1.008 + 0.012 * ease(prog)
    img = panelize(fr, zoom=zoom)

    d = ImageDraw.Draw(img, 'RGBA')
    grad = Image.new('RGBA', (700, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for x in range(700):
        a = int(212 * (1 - x / 700) ** 1.25)
        gd.line([(x, 0), (x, H)], fill=(7, 12, 20, a))
    img.paste(grad, (0, 0), grad)

    if kind == 'anchor1':
        text(d, (56, 120), 'SNGAL INFOS · LE JOURNAL', Inter(20, True), C_RED, stroke=2)
        for i, line in enumerate(['NAUFRAGE', 'AU LARGE DE', 'KÉBÉMER']):
            off = int((1 - ease(P(t - t0, 0.1 + i * 0.1, 0.55 + i * 0.1))) * 26)
            text(d, (56 + off, 168 + i * 64), line, Oswald(62), C_TXT, stroke=2)
        p = ease(P(t - t0, 0.7, 1.2))
        if p > 0:
            bar = Image.new('RGBA', (int(480 * p), 6), C_RED + (255,))
            img.paste(bar, (56, 372), bar)
            text(d, (56, 398), '34 morts · 1 rescapé · des disparus', Inter(21), C_TXT, stroke=2)
    else:
        text(d, (56, 140), 'SNGAL INFOS · LE JOURNAL', Inter(20, True), C_RED, stroke=2)
        for i, line in enumerate(['MERCI', 'D\'AVOIR', 'REGARDÉ']):
            off = int((1 - ease(P(t - t0, 0.1 + i * 0.1, 0.55 + i * 0.1))) * 26)
            text(d, (56 + off, 188 + i * 64), line, Oswald(62), C_TXT, stroke=2)
        p = ease(P(t - t0, 0.6, 1.1))
        if p > 0:
            bar = Image.new('RGBA', (int(480 * p), 6), C_RED + (255,))
            img.paste(bar, (56, 388), bar)
            text(d, (56, 414), 'Toutes nos pensées vont aux familles', Inter(21), C_TXT, stroke=2)

    y0 = 480
    panel = Image.new('RGBA', (W, 220), (10, 16, 26, 232))
    img.paste(panel, (0, y0), panel)
    d.line([(0, y0), (W, y0)], fill=C_GOLD + (200,), width=3)
    k1 = ease(P(appear, 0.08, 0.3))
    if k1 > 0:
        text(d, (40, y0 + 26), 'AÏSSATOU NDIAYE', Oswald(36), C_TXT, stroke=2)
        text(d, (40, y0 + 80), 'Présentatrice du journal · SNGAL INFOS', Inter(21), C_GOLD)
        fw = textw('EN DIRECT', Oswald(24)) + 44
        b = Image.new('RGBA', (fw, 48), (178, 32, 22, 235))
        img.paste(b, (W - 40 - fw, y0 + 30), b)
        text(d, (W - 40 - fw / 2, y0 + 55), 'EN DIRECT', Oswald(24), (255, 232, 226), anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img


def point_scene(kind, t, t0):
    appear = P(t - t0, 0.02, 0.3)
    img = Image.new('RGB', (W, H), C_BG)
    img.paste(Image.new('RGB', (W, H), (10, 18, 28)), (W // 2, 0))

    def insert_image(side, path, a=135, cy=0.42):
        x, w = (0, W // 2) if side == 'l' else (W // 2, W // 2)
        patch = kb_src(os.path.join(ROOT, path), w, H, cy=cy) if os.path.exists(os.path.join(ROOT, path)) else Image.new('RGB', (w, H), C_BG)
        dim(patch, 0, 0, w, H, a)
        img.paste(patch, (x, 0))

    imgs = {
        'p1': ('image-search/pirogue-chou-e-plage-s-n-gal-migrants-na-1.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--1.jpg'),
        'p2': ('image-search/pirogue-en-bois-surcharg-e-migrants-mer--1.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--3.jpg'),
        'p3': ('image-search/pirogue-chou-e-plage-s-n-gal-migrants-na-3.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--2.jpg'),
        'p4': ('image-search/pirogue-en-bois-surcharg-e-migrants-mer--4.jpg',
               'image-search/pirogue-en-bois-surcharg-e-migrants-mer--3.jpg'),
    }
    lpath, rpath = imgs[kind]
    insert_image('l', lpath, a=140)
    insert_image('r', rpath, a=112, cy=0.3)

    d = ImageDraw.Draw(img, 'RGBA')
    i = int(kind[1])
    circle = int(ease(P(t - t0, 0, 0.2)) * 34)
    if circle > 2:
        d.ellipse([64 - 4, 112 - 4, 64 + circle * 2 + 4, 112 + circle * 2 + 4],
                  outline=C_GOLD + (255,), width=2)
        if circle >= 33:
            text(d, (64 + 34, 112 + 34), f'{i:02d}', Oswald(40), C_GOLD, anchor='mm')

    badges = {
        'p1': ('LE BILAN', '34 MORTS, UN SEUL RESCAPÉ',
               'Des disparus sont toujours recherchés',
               'PROVISOIRE', C_RED, 'APS · dimanche 8 novembre'),
        'p2': ('LA CHRONOLOGIE', 'VENDREDI, SAMEDI, DIMANCHE',
               'Tébène : 4 corps · Lompoul : une vingtaine · puis +11',
               'DE 4 À 34', C_STEEL, None),
        'p3': ('LE CONTEXTE', 'LA ROUTE DES CANARIES',
               '635 morts en cinq mois en 2026 (Caminando Fronteras)',
               '635 MORTS', C_WARM, None),
        'p4': ('LA QUESTION', 'JUSQU\'À QUAND ?',
               'Entre émotion et colère, la question reste ouverte',
               'SNGAL INFOS', C_GOLD, None),
    }
    kicker, headline, sub, verdict, accent, caveat = badges[kind]
    y0 = 480
    ph = int(ease(appear) * 220)
    if ph > 2:
        panel = Image.new('RGBA', (W, ph), (10, 16, 26, 238))
        img.paste(panel, (0, y0), panel)
        d.line([(0, y0), (W, y0)], fill=accent + (200,), width=3)
    k1 = ease(P(appear, 0.08, 0.26))
    if k1 > 0:
        text(d, (40, y0 + 22), kicker, Inter(19, True), accent, anchor='lm')
        text(d, (W - 40, y0 + 22), 'SNGAL INFOS · LE JOURNAL', Inter(17, True), C_MUT, anchor='rm')
    k2 = ease(P(appear, 0.14, 0.34))
    if k2 > 0:
        size = 44
        f = Oswald(size)
        while textw(headline, f) > W - 90 and size > 28:
            size -= 2
            f = Oswald(size)
        text(d, (40, y0 + 78), headline, f, C_TXT, stroke=2)
    k3 = ease(P(appear, 0.26, 0.5))
    if k3 > 0:
        text(d, (40, y0 + 142), sub, Inter(21), C_MUT)
        if caveat:
            text(d, (40, y0 + 172), caveat, Inter(15), C_GOLD)
    k4 = ease(P(appear, 0.34, 0.6))
    if k4 > 0:
        fw = textw(verdict, Oswald(26)) + 44
        x = int(W - 40 - fw + (1 - k4) * 30)
        badge = Image.new('RGBA', (fw, 52), accent + (int(235 * k4),))
        img.paste(badge, (x, y0 + 128), badge)
        text(d, (x + fw / 2, y0 + 155), verdict, Oswald(26), (12, 16, 24), anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img


def outro_scene(t, t0):
    img = Image.new('RGB', (W, H), C_BG)
    d = ImageDraw.Draw(img, 'RGBA')
    text(d, (640, 250), 'LE JOURNAL', Oswald(56), C_TXT, anchor='mm')
    bar = Image.new('RGBA', (int(560 * ease(P(t - t0, 0, 0.4))), 6), C_RED + (255,))
    img.paste(bar, (360, 300), bar)
    lines = ['Merci de votre confiance', 'Aïssatou Ndiaye · toute la rédaction']
    for i, line in enumerate(lines):
        a = P(t - t0, 0.15 + i * 0.16, 0.5 + i * 0.16)
        if a > 0:
            text(d, (640, 344 + i * 42), f'—  {line}', Inter(20), C_TXT if a > 0.9 else C_MUT, anchor='mm')
    a = P(t - t0, 1.0, 1.5)
    if a > 0:
        lg = logo(56)
        img.paste(lg, (505, 470), lg)
        text(d, (685, 498), 'SNGAL INFOS', Oswald(44), C_GOLD, anchor='lm')
    text(d, (640, 590), 'Le journal · SNGAL INFOS', Inter(18, True), C_GOLD, anchor='mm')
    header_bar(img)
    ticker(img, t)
    return img


def frame(t):
    i, kind, t0, t1 = seg_at(t)
    if kind.startswith('anchor'):
        img = anchor_scene(kind, t, t0)
    elif kind.startswith('p'):
        img = point_scene(kind, t, t0)
    else:
        img = outro_scene(t, t0)
    return img


def main():
    setup()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'videos', 'jt-demo-16x9.mp4')
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
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'jt-demo-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out, f'{DUR:.0f}s')

if __name__ == '__main__':
    main()
