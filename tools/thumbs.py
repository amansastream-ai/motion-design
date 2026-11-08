"""Générateur de miniatures réseaux sociaux — SNGAL INFOS.
Formats : 16:9 (1280x720 YouTube/Facebook/X) · 9:16 (1080x1920 TikTok/Shorts/Reels) · 4:5 (1080x1350 Instagram feed)
Run: pytools/bin/python tools/thumbs.py [serie ...]
"""
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FDIR = os.path.join(ROOT, 'assets', 'fonts')
Oswald = lambda s: ImageFont.truetype(os.path.join(FDIR, 'Oswald-700.ttf'), s)
Inter = lambda s, b=False: ImageFont.truetype(
    os.path.join(FDIR, 'Inter-600.ttf' if b else 'Inter-400.ttf'), s)

OUT = os.path.join(ROOT, 'thumbs')
C_TXT = (245, 248, 252)
C_MUT = (190, 200, 212)
C_GOLD = (240, 186, 48)
C_WARM = (236, 104, 52)
C_RED = (198, 40, 32)
C_DARK = (8, 12, 20)

SIZES = {
    '16x9': (1280, 720),
    '9x16': (1080, 1920),
    '4x5': (1080, 1350),
}

SERIES = {
    'dip-disque-or': {
        'imgs': ['image-search/dip-doundou-guiss-chanteur-s-n-galais-2.jpg',
                 'image-search/dip-doundou-guiss-chanteur-s-n-galais-1.jpg'],
        'title': ['DOUBLE', "DISQUE D'OR"],
        'sub': 'LNN + LFLF · AMC 2026',
        'tag': 'MUSIQUE',
        'accent': C_GOLD,
        'disc': True,
    },
    'dip-disque-or-B': {
        'imgs': ['image-search/dip-doundou-guiss-chanteur-s-n-galais-3.jpg',
                 'image-search/dip-doundou-guiss-chanteur-s-n-galais-4.jpg'],
        'title': ['LE RAP', 'AU SOMMET'],
        'sub': 'DIP DOUNDOU GUISS CERTIFIÉ OR',
        'tag': 'CULTURE',
        'accent': C_GOLD,
        'disc': True,
    },
    'kebemer-alerte': {
        'imgs': ['image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-1.jpg',
                 'image-search/k-b-mer-s-n-gal-h-pital-centre-de-sant-4.jpg'],
        'title': ['KÉBÉMER :', '548 CAS'],
        'sub': 'ALERTE SANITAIRE · SYNDROMES DIGESTIFS',
        'tag': 'SANTÉ',
        'accent': C_RED,
    },
    'kebemer-naufrage': {
        'imgs': ['image-search/pirogue-en-bois-surcharg-e-migrants-mer--1.jpg',
                 'image-search/plage-c-te-s-n-gal-pirogues-p-cheurs-oc--4.jpg'],
        'title': ['NAUFRAGE À', 'KÉBÉMER : 34 MORTS'],
        'sub': 'ENCORE DES JEUNES PERDUS EN MER',
        'tag': 'FAITS DIVERS',
        'accent': C_RED,
    },
    'lfr-2026-rejet': {
        'imgs': ['image-search/assembl-e-nationale-s-n-gal-s-ance-d-put-1.jpg',
                 'image-search/assembl-e-nationale-s-n-gal-s-ance-d-put-2.jpg'],
        'title': ['LFR 2026 :', 'REJETÉE'],
        'sub': '109 VOIX CONTRE, 20 POUR',
        'tag': 'POLITIQUE',
        'accent': C_WARM,
    },
    'lfr-2026-rejet-wolof': {
        'imgs': ['image-search/assembl-e-nationale-s-n-gal-s-ance-d-put-2.jpg',
                 'image-search/assembl-e-nationale-s-n-gal-s-ance-d-put-3.jpg'],
        'title': ['ASAMBEL YA', 'BAÑ NA LFR'],
        'sub': '109 VOIX · WOLOF',
        'tag': 'XIBAAR',
        'accent': C_WARM,
    },
    'vie-chere-greve': {
        'imgs': ['image-search/march-dakar-familles-denr-es-alimentaire-3.jpg',
                 'image-search/march-dakar-familles-denr-es-alimentaire-1.png',
                 'image-search/vie-ch-re-s-n-gal-inflation-prix-aliment-2.jpg'],
        'title': ['VIE CHÈRE', '& GRÈVE'],
        'sub': '72 HEURES · 21-23 OCTOBRE',
        'tag': 'ÉCONOMIE',
        'accent': C_WARM,
    },
    'greve-72h': {
        'imgs': ['image-search/gr-ve-manifestation-syndicale-s-n-gal-tr-1.jpg',
                 'image-search/gr-ve-manifestation-syndicale-s-n-gal-tr-2.jpg',
                 'image-search/transport-bus-services-publics-dakar-s-n-1.jpg'],
        'title': ['GRÈVE DE', '72 HEURES'],
        'sub': '21 · 22 · 23 OCTOBRE',
        'tag': 'SOCIÉTÉ',
        'accent': C_WARM,
    },
    'diodio-glow-skin': {
        'imgs': ['image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-2.jpg',
                 'image-search/diodio-glow-skin-mame-diarra-thiam-s-n-g-1.jpg'],
        'title': ['DIODIO :', 'LES FAITS'],
        'sub': 'ACCUSATIONS ≠ CULPABILITÉ',
        'tag': 'JUSTICE',
        'accent': C_RED,
    },
    'les-7-points-conference': {
        'imgs': ['image-search/h-micycle-assembl-e-nationale-d-put-s-s--1.jpg',
                 'image-search/assembl-e-nationale-du-s-n-gal-dakar-b-t-1.jpg',
                 'assets/press-conf.png'],
        'title': ['LFR 2026 :', 'LES 7 POINTS'],
        'sub': "CE QU'IL FAUT SAVOIR",
        'tag': 'POLITIQUE',
        'accent': C_GOLD,
    },
    'inondations-dakar': {
        'imgs': ['image-search/inondations-dakar-quartiers-noy-s-plui-1.jpg',
                 'image-search/inondations-dakar-quartiers-noy-s-plui-2.jpg',
                 'image-search/dakar-s-n-gal-littoral-vue-a-rienne-fron-1.jpg'],
        'title': ['INONDATIONS', 'À DAKAR'],
        'sub': 'LA VILLE SOUS L’EAU',
        'tag': 'URGENCE',
        'accent': C_RED,
    },
    'enquetes-parlementaires': {
        'imgs': ['image-search/h-micycle-assembl-e-nationale-d-put-s-s--2.jpg',
                 'image-search/assembl-e-nationale-du-s-n-gal-dakar-b-t-2.jpg'],
        'title': ['ENQUÊTES', 'PARLEMENTAIRES'],
        'sub': "CE QU'IL FAUT SAVOIR",
        'tag': 'POLITIQUE',
        'accent': C_STEEL if False else (110, 160, 220),
    },
}


def textw(s, f):
    return f.getbbox(s)[2]


def cover_crop(im, w, h, focus=0.36):
    im = im.convert('RGB')
    sw, sh = im.size
    scale = max(w / sw, h / sh)
    nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * focus)
    return im.crop((x, y, x + w, y + h))


def load_img(cands, w, h, focus=0.36):
    for p in cands:
        path = os.path.join(ROOT, p)
        if os.path.exists(path):
            return cover_crop(Image.open(path), w, h, focus)
    plate = Image.new('RGB', (w, h), (20, 28, 40))
    d = ImageDraw.Draw(plate)
    for i in range(0, w + h, 40):
        d.line([(i, 0), (i - h, h)], fill=(28, 38, 54), width=2)
    return plate


def scrim_v(img, frac=0.52, strength=225):
    """Voile dégradé du bas vers le haut."""
    w, h = img.size
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    start = int(h * (1 - frac))
    for y in range(start, h):
        k = (y - start) / max(1, h - start)
        d.line([(0, y), (w, y)], fill=(4, 8, 16, int(strength * (0.15 + 0.85 * k))))
    img.paste(ov, (0, 0), ov)
    return img


def scrim_left(img, frac=0.62, strength=225):
    w, h = img.size
    ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    end = int(w * frac)
    for x in range(0, end):
        k = 1 - x / max(1, end)
        d.line([(x, 0), (x, h)], fill=(4, 8, 16, int(strength * (0.12 + 0.88 * k))))
    img.paste(ov, (0, 0), ov)
    return img


def gold_disc(size):
    """Disque d'or dessiné (dégradé radial + sillons + reflet)."""
    S = size * 3
    disc = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(disc)
    cx = cy = S // 2
    for r in range(S // 2, 0, -1):
        k = r / (S / 2)
        ang_light = 0.55 + 0.45 * (1 - k)
        col = (
            int(min(255, (252 * ang_light) + 18)),
            int(min(255, (198 * ang_light) + 12)),
            int(min(255, (64 * ang_light) + 8)),
            255,
        )
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    # sillons
    for r in range(int(S * 0.16), int(S * 0.47), max(2, S // 110)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(120, 88, 20, 70), width=max(1, S // 400))
    # étiquette centrale
    r0 = int(S * 0.155)
    d.ellipse([cx - r0, cy - r0, cx + r0, cy + r0], fill=(238, 240, 244, 255))
    d.ellipse([cx - r0, cy - r0, cx + r0, cy + r0], outline=(200, 160, 60, 255), width=max(2, S // 160))
    hole = max(2, S // 90)
    d.ellipse([cx - hole, cy - hole, cx + hole, cy + hole], fill=(80, 70, 60, 255))
    # reflet spéculaire
    hl = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([int(S * 0.12), int(S * 0.08), int(S * 0.62), int(S * 0.42)],
               fill=(255, 255, 255, 46))
    hl = hl.filter(ImageFilter.GaussianBlur(S // 40))
    disc = Image.alpha_composite(disc, hl)
    return disc.resize((size, size), Image.LANCZOS)


def draw_text_block(d, img, x, y, lines, size, fill, stroke=3, max_w=None):
    f = Oswald(size)
    if max_w:
        while max(textw(l, f) for l in lines) > max_w and size > 30:
            size -= 4
            f = Oswald(size)
    yy = y
    for l in lines:
        d.text((x, yy), l, font=f, fill=fill, anchor='lt',
               stroke_width=stroke, stroke_fill=(10, 12, 18))
        yy += int(size * 1.06)
    return yy


def logo_bug(img, x, y, size, d):
    lg = Image.open(os.path.join(ROOT, 'assets', 'logo-sngal.png')).convert('RGBA')
    lg = lg.resize((size, size), Image.LANCZOS)
    img.paste(lg, (x, y), lg)
    return x + size


def make_thumb(series_key, spec, fmt):
    w, h = SIZES[fmt]
    img = load_img(spec['imgs'], w, h, focus=0.34 if fmt != '16x9' else 0.3)
    if fmt == '16x9':
        img = scrim_left(img, 0.66, 232)
    else:
        img = scrim_v(img, 0.58 if fmt == '9x16' else 0.55, 232)
    d = ImageDraw.Draw(img, 'RGBA')

    accent = spec['accent']
    title = spec['title']
    sub = spec['sub']

    if fmt == '16x9':
        m = 56
        nx = logo_bug(img, m, m, 72, d)
        d.text((nx + 14, m + 36), 'SNGAL INFOS', font=Oswald(38), fill=C_TXT, anchor='lm',
               stroke_width=2, stroke_fill=(10, 12, 18))
        tag = spec['tag']
        tw = textw(tag, Inter(22, True)) + 36
        d.rectangle([m, h - 70, m + tw, h - 26], fill=accent + (255,))
        d.text((m + tw / 2, h - 48), tag, font=Inter(22, True), fill=(12, 16, 24), anchor='mm')
        y = draw_text_block(d, img, m, int(h * 0.32), title, 108, C_TXT, 4, max_w=int(w * 0.52))
        bar = Image.new('RGBA', (min(int(w * 0.44), textw(sub, Inter(30, True)) + 40), 10), accent + (255,))
        img.paste(bar, (m, y + 10), bar)
        d.text((m, y + 42), sub, font=Inter(30, True), fill=accent, anchor='lt',
               stroke_width=2, stroke_fill=(10, 12, 18))
        if spec.get('disc'):
            disc = gold_disc(300)
            img.paste(disc, (w - 360, h // 2 - 150), disc)
    else:
        m = 64
        nx = logo_bug(img, m, m, 110, d)
        d.text((nx + 18, m + 55), 'SNGAL INFOS', font=Oswald(54), fill=C_TXT, anchor='lm',
               stroke_width=3, stroke_fill=(10, 12, 18))
        tag = spec['tag']
        tw = textw(tag, Inter(30, True)) + 52
        d.rectangle([m, h - 200, m + tw, h - 140], fill=accent + (255,))
        d.text((m + tw / 2, h - 170), tag, font=Inter(30, True), fill=(12, 16, 24), anchor='mm')
        if fmt == '9x16':
            y0 = int(h * 0.55)
            size = 150
        else:
            y0 = int(h * 0.52)
            size = 132
        y = draw_text_block(d, img, m, y0, title, size, C_TXT, 5, max_w=w - 2 * m)
        bar = Image.new('RGBA', (min(w - 2 * m, textw(sub, Inter(42, True)) + 56), 14), accent + (255,))
        img.paste(bar, (m, y + 16), bar)
        d.text((m, y + 60), sub, font=Inter(42, True), fill=accent, anchor='lt',
               stroke_width=3, stroke_fill=(10, 12, 18))
        if spec.get('disc'):
            disc = gold_disc(340 if fmt == '9x16' else 300)
            img.paste(disc, (w - (400 if fmt == '9x16' else 360), int(h * 0.30)), disc)

    out = os.path.join(OUT, f'{series_key}-thumb-{fmt}.jpg')
    img.save(out, 'JPEG', quality=90)
    kb = os.path.getsize(out) / 1024
    print(f'{os.path.basename(out)}  {w}x{h}  {kb:.0f} KB')


def main():
    os.makedirs(OUT, exist_ok=True)
    keys = sys.argv[1:] or list(SERIES.keys())
    for k in keys:
        spec = SERIES[k]
        for fmt in SIZES:
            make_thumb(k, spec, fmt)


if __name__ == '__main__':
    main()
