"""Teaser 30 s (300x300 + 1920x1080) « Séquestration présumée à Pikine ».
SNGAL INFOS · VO pk-1 intégrale · labels « ACCUSATIONS ≠ CULPABILITÉ » (Inter).
Run: pytools/bin/python tools/render_teaser_pk.py [square|wide|all]
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

FPS = 24
DUR = 30.0

C_BG = (7, 13, 22)
C_TXT = (238, 242, 248)
C_MUT = (148, 162, 178)
C_WARM = (232, 92, 42)
C_GOLD = (232, 178, 42)
C_RED = (214, 64, 48)
C_STEEL = (110, 160, 220)
C_TEAL = (42, 184, 162)

PA = 'image-search/ta-lions-parade.jpg'
LA = 'image-search/ta-lausanne.jpg'
JU = 'image-search/ta-lions-trophee.jpg'

CARDS = [
    (0, 4.5, PA, ['LE TITRE 2025', 'RESTE AUX LIONS'], C_GOLD),
    (4.5, 9, LA, ['LE TAS', 'ANNULE LE FORFAIT'], C_RED),
    (9, 13.5, JU, ['FINALE 1-0', 'RÉTABLIE'], C_GOLD),
]
LABELS = [
    (13.5, 19, ['CHAMPION', "D'AFRIQUE 2025"], C_GOLD),
    (19, 24, ['LA SUITE', 'SUR SNGAL INFOS'], C_TEAL),
]
END = (24.0, 30.0)
TRANS = 0.35

STAGES = (
    [(t0, t1, 'card', (img, lines, accent)) for (t0, t1, img, lines, accent) in CARDS]
    + [(t0, t1, 'label', (lines, accent)) for (t0, t1, lines, accent) in LABELS]
    + [(END[0], END[1], 'end', None)]
)


class R:
    def __init__(self, W, H, alpha_ref=1200):
        self.W, self.H = W, H
        self.f = max(W, H) / alpha_ref

    def fs(self, px):
        return max(12, int(px * self.f))

    def logo(self, size):
        lg = Image.open(os.path.join(ROOT, 'assets', 'logo-sngal.png')).convert('RGBA')
        return lg.resize((size, size), Image.LANCZOS)

    def cover(self, img, w, h):
        im = img.convert('RGB')
        sw, sh = im.size
        scale = max(w / sw, h / sh)
        nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
        im = im.resize((nw, nh), Image.LANCZOS)
        x = (nw - w) // 2
        y = int((nh - h) * 0.38)
        return im.crop((x, y, x + w, y + h))

    def kb(self, path, w, h):
        im = Image.open(os.path.join(ROOT, path)).convert('RGB')
        if im.width < w * 0.62 or im.height < h * 0.62:
            plate = self.cover(im, w, h).filter(ImageFilter.GaussianBlur(self.fs(22)))
            plate = Image.blend(plate, Image.new('RGB', (w, h), C_BG), 0.30)
            sw, sh = im.size
            scale = min(w * 0.88 / sw, h * 0.88 / sh)
            nw, nh = int(sw * scale), int(sh * scale)
            plate.paste(im.resize((nw, nh), Image.LANCZOS), ((w - nw) // 2, (h - nh) // 2))
            return plate
        return self.cover(im, w, h)

    def blend(self, base):
        grad = Image.new('RGB', (self.W, self.H))
        gd = ImageDraw.Draw(grad)
        for y in range(0, self.H, 2):
            k = y / self.H
            gd.rectangle([0, y, self.W, y + 2], fill=(int(6 + 10 * k), int(12 + 12 * k), int(20 + 14 * k)))
        return Image.blend(base, grad, 0.42)

    def dim(self, img, a):
        ov = Image.new('RGBA', (self.W, self.H), (0, 0, 0, a))
        img.paste(ov, (0, 0), ov)

    def vignette(self, img):
        ov = Image.new('RGBA', (self.W, self.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for i in range(int(self.fs(26))):
            d.rectangle([i * 2, i * 2, self.W - i * 2, self.H - i * 2], outline=(0, 0, 0, int(1 + i * 0.7)))
        img.paste(ov, (0, 0), ov)

    def text(self, d, xy, s, f, fill, anchor=None, stroke=0):
        d.text(xy, s, font=f, fill=fill, anchor=anchor,
               stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)

    def brand_top(self, img):
        d = ImageDraw.Draw(img, 'RGBA')
        ls = self.fs(64)
        lg = self.logo(ls)
        img.paste(lg, (self.fs(28), self.fs(22)), lg)
        self.text(d, (self.fs(28) + ls + self.fs(14), self.fs(30)), 'SNGAL INFOS',
                  Oswald(self.fs(36)), (242, 246, 252), anchor='lm')
        self.text(d, (self.fs(28) + ls + self.fs(14), self.fs(80)), 'SPORT · TAS',
                  Inter(self.fs(20), True), C_WARM, anchor='lm')

    def brand_bottom(self, img, t):
        d = ImageDraw.Draw(img, 'RGBA')
        bar = Image.new('RGBA', (int(self.W * 0.62), self.fs(6)), C_WARM + (255,))
        img.paste(bar, ((self.W - bar.width) // 2, self.H - self.fs(120)), bar)
        self.text(d, (self.W / 2, self.H - self.fs(82)), 'Le titre 2025 reste aux Lions',
                 Inter(self.fs(26), True), (222, 230, 240), anchor='mm')
        self.text(d, (self.W / 2, self.H - self.fs(44)), 'SNGAL INFOS · SPORT',
                  Inter(self.fs(19), True), C_MUT, anchor='mm')

    def card(self, img, lines, accent, t):
        img = self.blend(self.kb(img, self.W, self.H))
        self.dim(img, 128)
        self.vignette(img)
        d = ImageDraw.Draw(img, 'RGBA')
        self.brand_top(img)
        p = t
        y0 = int(self.H * 0.36)
        for i, line in enumerate(lines):
            a = max(0.0, min(1.0, (p - i * 0.1) / 0.3))
            if a <= 0:
                continue
            size = self.fs(78)
            f = Oswald(size)
            self.text(d, (self.W * 0.5 + (1 - a) * self.fs(24), y0 + i * self.fs(100)),
                      line, f, C_TXT if i == 0 else accent, anchor='lm', stroke=2)
        a = max(0.0, min(1.0, (p - 0.3) / 0.35))
        if a > 0:
            bar = Image.new('RGBA', (int(self.W * 0.62 * a), self.fs(8)), accent + (255,))
            img.paste(bar, ((self.W - bar.width) // 2, y0 + self.fs(210)), bar)
        self.brand_bottom(img, t)
        return img

    def label(self, lines, accent, t):
        img = self.blend(self.kb(PA, self.W, self.H))
        self.dim(img, 175)
        self.vignette(img)
        d = ImageDraw.Draw(img, 'RGBA')
        self.brand_top(img)
        y0 = int(self.H * 0.38)
        for i, line in enumerate(lines):
            a = max(0.0, min(1.0, (t - i * 0.1) / 0.3))
            if a <= 0:
                continue
            self.text(d, (self.W * 0.5, y0 + i * self.fs(110)), line,
                      Oswald(self.fs(92)), C_TXT if i == 0 else accent, anchor='mm', stroke=2)
        self.brand_bottom(img, t)
        return img

    def end(self, t):
        img = self.blend(self.kb(JU, self.W, self.H))
        self.dim(img, 185)
        d = ImageDraw.Draw(img, 'RGBA')
        self.text(d, (self.W / 2, self.H * 0.34), 'LA SUITE', Oswald(self.fs(86)), C_TXT, anchor='mm')
        self.text(d, (self.W / 2, self.H * 0.34 + self.fs(100)), 'DANS NOTRE REPORTAGE',
                  Oswald(self.fs(56)), C_GOLD, anchor='mm')
        a = max(0.0, min(1.0, t / 0.4))
        bar = Image.new('RGBA', (int(self.W * 0.62 * a), self.fs(8)), C_WARM + (255,))
        img.paste(bar, ((self.W - bar.width) // 2, int(self.H * 0.34 + self.fs(170))), bar)
        ls = self.fs(72)
        lg = self.logo(ls)
        x0 = int(self.W / 2 - ls * 1.6)
        img.paste(lg, (x0, int(self.H * 0.60)), lg)
        self.text(d, (x0 + ls + self.fs(14), int(self.H * 0.60) + ls // 2), 'SNGAL INFOS',
                  Oswald(self.fs(46)), C_GOLD, anchor='lm')
        self.text(d, (self.W / 2, self.H * 0.78), 'Champion d\'Afrique 2025',
                 Inter(self.fs(30), True), (222, 230, 240), anchor='mm')
        return img

    def frame(self, t):
        for (t0, t1, kind, data) in STAGES:
            if t0 <= t < t1:
                p = (t - t0) / (t1 - t0)
                if kind == 'card':
                    img = self.card(data[0], data[1], data[2], p)
                elif kind == 'label':
                    img = self.label(data[0], data[1], p)
                else:
                    img = self.end(p)
                if t < t0 + TRANS:
                    a = (t - t0) / TRANS
                    img = Image.eval(img, lambda v: int(v * (0.25 + 0.75 * a)))
                return img
        return self.end(1.0)


def render(stage, out):
    W, H = (300, 300) if stage == 'square' else (1920, 1080)
    r = R(W, H)
    tmp = out + '.tmp.mp4'
    proc = imageio_ffmpeg.write_frames(
        tmp, (W, H), pix_fmt_in='rgb24', fps=FPS, codec='libx264', quality=None,
        macro_block_size=1, ffmpeg_log_level='error',
        output_params=['-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p'])
    proc.send(None)
    n = int(DUR * FPS)
    for fi in range(n):
        proc.send(np.asarray(r.frame(fi / FPS), dtype=np.uint8))
        if fi % (FPS * 12) == 0:
            print(f'  {stage} frame {fi}/{n}')
    proc.close()
    import subprocess
    subprocess.run([FFMPEG, '-y', '-i', tmp, '-i', os.path.join(ROOT, 'audio', 'ta-teaser-master.wav'),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-ac', '2',
                    '-map', '0:v:0', '-map', '1:a:0', out],
                   capture_output=True, check=True)
    os.unlink(tmp)
    print('wrote', out)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    jobs = {
        'square': os.path.join(ROOT, 'videos', 'teaser-tas-titre-2025-300x300.mp4'),
        'wide': os.path.join(ROOT, 'videos', 'teaser-tas-titre-2025-16x9.mp4'),
    }
    for k, outp in jobs.items():
        if what in ('all', k):
            render(k, outp)


if __name__ == '__main__':
    main()
