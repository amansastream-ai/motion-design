#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générique animé « Bureau Rose » : fond vert, effets roses animés, sous-titre LAMEX TV.

Rendu vidéo 1920x1080 à 30 fps (H.264, sans son). Aucun navigateur n'est nécessaire :
les images sont composées avec Pillow et NumPy, le texte est mis en forme avec
HarfBuzz (kerning de la police Montserrat), et l'encodage est fait par ffmpeg
(binaire fourni par le paquet imageio-ffmpeg).

Installation :
    pip install pillow numpy uharfbuzz imageio-ffmpeg

Usage :
    python3 render_bureau_rose.py                 # -> out/Bureau-Rose-generique.mp4
    python3 render_bureau_rose.py --still 6.5     # -> out/still-06.50s.png (contrôle visuel)

Pour changer les noms ou les rôles, modifier la liste PEOPLE ci-dessous.
"""

import argparse
import math
import os
import random
import subprocess
import sys

import numpy as np
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
OUT_DIR = os.path.join(HERE, "out")

W, H = 1920, 1080
FPS = 30
END_TIME = 21.8  # durée totale (secondes)

# ----------------------------------------------------------------- contenu
TITLE = "BUREAU ROSE"
TAGLINE = (
    "Mini-série de sensibilisation",
    "au cancer du sein et au cancer du col de l’utérus",
)
PEOPLE = [
    ("Mme FALL", "Directrice de Lamex Institut"),
    ("Awa", "La Secrétaire"),
    ("Moussa", "Le Comptable"),
    ("Fatou", "La Stagiaire"),
    ("Serigne SYLLA", "Réalisateur"),
]
CHANNEL_BOLD = "LAMEX TV"
CHANNEL_LIGHT = "Télévision"

# ----------------------------------------------------------------- couleurs
GREEN_TOP = (14, 133, 70)
GREEN_BOTTOM = (5, 80, 41)
GREEN_LIGHT = (70, 185, 115)
PINK_A = (255, 56, 146)      # rose vif (saturé : il reste rose sur le vert)
PINK_B = (255, 120, 190)     # rose clair
PINK_SOFT = (255, 214, 233)  # texte secondaire
WHITE = (255, 255, 255)

# ----------------------------------------------------------------- rythme
TITLE_OUT_T = 3.85           # début de la sortie du titre
CARD_START = 4.5             # apparition de la première carte
CARD_LEN = 3.1               # durée d'une carte (entrée + pause + sortie)
CARD_COUNT = len(PEOPLE)
OUTRO_T = CARD_START + CARD_LEN * CARD_COUNT  # 20.0 s

# ----------------------------------------------------------------- mise en page
CENTER_Y_TITLE = 465         # centre optique du titre
RULE_TOP_Y = 352
RULE_BOTTOM_Y = 735
TAG1_BASE_Y = 618
TAG2_BASE_Y = 680
NAME_CY = 470                # centre optique du nom
UNDERLINE_Y = 572
ROLE_BASE_Y = 668
SUB_BASE_Y = 1004            # ligne de base du sous-titre (bas à gauche)


# ================================================================= easing
def _bezier_coord(p1, p2, s):
    return 3 * (1 - s) ** 2 * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3


def make_bezier(x1, y1, x2, y2):
    """Courbe cubic-bezier façon CSS (points de contrôle (x1,y1) et (x2,y2))."""

    def ease(x):
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(48):
            mid = 0.5 * (lo + hi)
            if _bezier_coord(x1, x2, mid) < x:
                lo = mid
            else:
                hi = mid
        return _bezier_coord(y1, y2, 0.5 * (lo + hi))

    return ease


EASE_OUT = make_bezier(0.22, 1.0, 0.36, 1.0)  # entrées : décélération douce, sans rebond
EASE_IN = make_bezier(0.64, 0.0, 0.78, 0.0)   # sorties : accélération douce
EASE_IO = make_bezier(0.65, 0.0, 0.35, 1.0)   # mouvements symétriques


def clamp01(v):
    return 0.0 if v <= 0.0 else (1.0 if v >= 1.0 else v)


def prog(t, start, dur):
    return clamp01((t - start) / dur)


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(round(lerp(a, b, k))) for a, b in zip(c1, c2))


def anim(t, t_in, d_in, t_out, d_out, dy_in=0.0, dy_out=0.0):
    """Opacité et décalage vertical (px, négatif = vers le haut) : entrée puis sortie."""
    e_in = EASE_OUT(prog(t, t_in, d_in))
    e_out = EASE_IN(prog(t, t_out, d_out))
    return e_in * (1.0 - e_out), dy_in * (1.0 - e_in) - dy_out * e_out


def pink_at(t, phase=0.0):
    """Rose animé : oscille lentement entre rose vif et rose clair."""
    k = 0.5 + 0.5 * math.sin(2 * math.pi * t / 5.0 + phase)
    return mix(PINK_A, PINK_B, k)


# ================================================================= texte
class Font:
    """Police TTF : mise en forme HarfBuzz (kerning GPOS) + rendu Pillow."""

    def __init__(self, filename):
        self.path = os.path.join(FONT_DIR, filename)
        face = hb.Face(hb.Blob.from_file_path(self.path))
        self.hb_font = hb.Font(face)
        self.upem = face.upem
        self._pil = {}

    def pil(self, size):
        if size not in self._pil:
            self._pil[size] = ImageFont.truetype(self.path, size)
        return self._pil[size]

    def layout(self, text, size, tracking=0.0):
        """Retourne (positions x de chaque caractère, largeur totale sans l'espace final)."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {"liga": False, "clig": False, "calt": False})
        if len(buf.glyph_positions) != len(text):
            raise ValueError(f"Mise en forme inattendue pour {text!r}")
        s = size / self.upem
        xs, x = [], 0.0
        for pos in buf.glyph_positions:
            xs.append(x + pos.x_offset * s)
            x += pos.x_advance * s + tracking
        return xs, x - tracking


class TextMask:
    """Masque 'L' d'un texte, avec sa ligne de base et sa largeur."""

    def __init__(self, mask, base, width, pad):
        self.mask = mask
        self.base = base
        self.width = width
        self.pad = pad


def render_text(font, text, size, tracking=0.0, pad=30):
    xs, width = font.layout(text, size, tracking)
    pil = font.pil(size)
    asc, desc = pil.getmetrics()
    mask = Image.new("L", (int(math.ceil(width)) + 2 * pad, asc + desc + 2 * pad), 0)
    draw = ImageDraw.Draw(mask)
    base = pad + asc
    for ch, x in zip(text, xs):
        if not ch.isspace():
            draw.text((pad + x, base), ch, font=pil, fill=255, anchor="ls")
    return TextMask(mask, base, width, pad)


def fit_size(font, text, max_w, max_size, track_em=0.0, min_size=32):
    """Plus grande taille (par pas de 2 px) dont la largeur tient dans max_w."""
    size = max_size
    while size > min_size:
        if font.layout(text, size, track_em * size)[1] <= max_w:
            return size
        size -= 2
    return min_size


# ================================================================= formes
def radial_mask(radius, power=2.0, plateau=0.0):
    """Halo circulaire : 255 au centre (plateau optionnel), 0 au bord."""
    n = 2 * int(radius)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = n / 2.0
    d = np.sqrt((xx + 0.5 - c) ** 2 + (yy + 0.5 - c) ** 2) / radius
    a = np.clip((1.0 - d) / (1.0 - plateau), 0.0, 1.0) ** power
    return Image.fromarray((a * 255).astype(np.uint8))


def disc_mask(radius, feather):
    """Disque à bord doux."""
    m = int(math.ceil(radius + feather + 2))
    n = 2 * m
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx + 0.5 - m) ** 2 + (yy + 0.5 - m) ** 2)
    a = np.clip((radius - d) / feather + 0.5, 0.0, 1.0)
    a = a * a * (3.0 - 2.0 * a)
    return Image.fromarray((a * 255).astype(np.uint8))


def ring_mask(radius, thickness):
    """Anneau anti-crénelé."""
    m = int(math.ceil(radius + thickness + 3))
    n = 2 * m
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.sqrt((xx + 0.5 - m) ** 2 + (yy + 0.5 - m) ** 2)
    a = np.clip(thickness / 2.0 + 0.5 - np.abs(d - radius), 0.0, 1.0)
    return Image.fromarray((a * 255).astype(np.uint8))


def sparkle_mask(size=160):
    """Étoile à 4 branches (scintillement)."""
    c = size / 2.0
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    u = (xx + 0.5 - c) / (c * 0.94)
    v = (yy + 0.5 - c) / (c * 0.94)
    f = (np.sqrt(np.abs(u)) + np.sqrt(np.abs(v))) ** 2  # = 1 sur le contour de l'étoile
    star = np.clip((1.0 - f) / 0.08 + 0.02, 0.0, 1.0)
    core = np.exp(-(u * u + v * v) * 12.0)
    return Image.fromarray((np.clip(star + 0.85 * core, 0.0, 1.0) * 255).astype(np.uint8))


def band_mask(width, height):
    """Bande verticale douce, utilisée pour les balayages roses entre les cartes."""
    x = np.linspace(-1.0, 1.0, width, dtype=np.float32)
    prof = np.clip(1.0 - np.abs(x), 0.0, 1.0) ** 1.2
    arr = np.broadcast_to(prof[None, :], (height, width))
    return Image.fromarray((arr * 255).astype(np.uint8))


def build_background():
    """Fond vert en dégradé + vignette sombre fixe sur les bords."""
    ys = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None, None]
    col = np.array(GREEN_TOP, np.float32) * (1 - ys) + np.array(GREEN_BOTTOM, np.float32) * ys
    arr = np.ascontiguousarray(np.broadcast_to(col, (H, W, 3))).astype(np.uint8)
    bg = Image.fromarray(arr).convert("RGBA")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.80)) ** 2)
    vign = np.clip((d - 0.55) / 0.75, 0.0, 1.0) ** 1.6 * 0.55
    dark = Image.new("RGBA", (W, H), (2, 42, 22, 0))
    dark.putalpha(Image.fromarray((vign * 255).astype(np.uint8)))
    bg.alpha_composite(dark)
    return bg


# ================================================================= composition
def paint(target, mask, color, x, y, alpha=1.0):
    """Compose un masque 'L' teinté de `color` sur `target` (RGBA) en (x, y)."""
    if alpha <= 0.0:
        return
    x, y = int(round(x)), int(round(y))
    mw, mh = mask.size
    tw, th = target.size
    x0, y0 = max(0, -x), max(0, -y)
    x1, y1 = min(mw, tw - x), min(mh, th - y)
    if x1 <= x0 or y1 <= y0:
        return
    m = mask.crop((x0, y0, x1, y1)) if (x0, y0, x1, y1) != (0, 0, mw, mh) else mask
    if alpha < 1.0:
        m = m.point([int(round(v * alpha)) for v in range(256)])
    layer = Image.new("RGBA", m.size, (int(color[0]), int(color[1]), int(color[2]), 0))
    layer.putalpha(m)
    target.alpha_composite(layer, dest=(x + x0, y + y0))


def paint_center(target, mask, color, cx, cy, alpha=1.0):
    paint(target, mask, color, cx - mask.width / 2.0, cy - mask.height / 2.0, alpha)


def paint_text(target, tm, color, x_left, baseline, alpha=1.0):
    paint(target, tm.mask, color, x_left - tm.pad, baseline - tm.base, alpha)


def paint_rule(target, cx, cy, w, h, color, alpha=1.0):
    w = max(1, int(round(w)))
    h = max(1, int(round(h)))
    paint(target, Image.new("L", (w, h), 255), color, cx - w / 2.0, cy - h / 2.0, alpha)


def drift_item(rng, r, mask, alpha, speed=(12, 26), sway=(10, 40), tx=(7, 14), ta=(3.0, 6.0)):
    """Élément qui monte lentement avec un léger balancement (bulle, anneau, particule)."""
    return {
        "mask": mask,
        "r": r,
        "x0": rng.uniform(0, W),
        "y0": rng.uniform(0, H + 200),
        "speed": rng.uniform(*speed) + 0.10 * r,
        "ax": rng.uniform(*sway),
        "tx": rng.uniform(*tx),
        "px": rng.uniform(0, 2 * math.pi),
        "alpha": alpha,
        "ta": rng.uniform(*ta),
        "pa": rng.uniform(0, 2 * math.pi),
        "pc": rng.uniform(0, 2 * math.pi),
    }


# ================================================================= scène
class Scene:
    def __init__(self):
        self.font_xb = Font("Montserrat-ExtraBold.ttf")
        self.font_b = Font("Montserrat-Bold.ttf")
        self.font_sb = Font("Montserrat-SemiBold.ttf")
        self.font_m = Font("Montserrat-Medium.ttf")

        # tailles adaptées à la largeur de l'écran
        self.title_size = fit_size(self.font_xb, TITLE, 1520, 230, track_em=0.03)
        self.title_track = 0.03 * self.title_size
        self.name_size = min(fit_size(self.font_xb, n, 1500, 156) for n, _ in PEOPLE)
        self.role_size = 50
        self.role_track = 6.0

        # fond et halos (pré-calculés une fois)
        self.bg = build_background()
        self.light = radial_mask(620, 2.0)
        self.glow_title = radial_mask(780, 1.6, plateau=0.2)
        self.glow_card = radial_mask(560, 1.5, plateau=0.2)
        self.band = band_mask(560, H)
        self.spark = sparkle_mask(160)
        self.gy, self.gx = np.mgrid[0:H, 0:W].astype(np.float32)

        # titre : chaque lettre est animée séparément
        self.title_xs, self.title_w = self.font_xb.layout(TITLE, self.title_size, self.title_track)
        self.title_left = W / 2 - self.title_w / 2
        self.title_base = CENTER_Y_TITLE + 0.35 * self.title_size
        self.title_chars = {
            ch: render_text(self.font_xb, ch, self.title_size, 0.0, pad=30)
            for ch in set(TITLE) if not ch.isspace()
        }
        self.tag1 = render_text(self.font_sb, TAGLINE[0], 46)
        self.tag2 = render_text(self.font_m, TAGLINE[1], 42)

        # cartes des personnes
        self.cards = []
        for name, role in PEOPLE:
            nm = render_text(self.font_xb, name, self.name_size, 0.0, pad=30)
            rm = render_text(self.font_sb, role.upper(), self.role_size, self.role_track, pad=30)
            self.cards.append((nm, rm))

        # sous-titre bas à gauche
        self.ch_bold = render_text(self.font_b, CHANNEL_BOLD, 30, 2.0, pad=20)
        self.ch_light = render_text(self.font_m, CHANNEL_LIGHT, 30, 0.6, pad=20)

        # éléments roses flottants (déterministes)
        rng = random.Random(11)
        self.bokeh = []        # bulles pleines à bord doux
        for _ in range(16):
            r = rng.uniform(8, 30)
            self.bokeh.append(drift_item(rng, r, disc_mask(r, r * rng.uniform(0.15, 0.3)),
                                         rng.uniform(0.7, 0.95)))
        self.bubbles = []      # bulles en anneau
        for _ in range(8):
            r = rng.uniform(14, 36)
            self.bubbles.append(drift_item(rng, r, ring_mask(r, 2.5), rng.uniform(0.6, 0.9),
                                           speed=(10, 22), sway=(14, 34)))
        self.dots = []         # particules nettes
        for _ in range(26):
            r = rng.uniform(2.5, 5.5)
            self.dots.append(drift_item(rng, r, disc_mask(r, 1.2), 1.0,
                                        speed=(22, 44), sway=(6, 18), tx=(5, 9), ta=(2.0, 3.0)))

    # ------------------------------------------------------------- éléments
    def _ambient(self, img, t):
        cx = W / 2 + 640 * math.cos(2 * math.pi * t / 23.0)
        cy = H / 2 + 300 * math.sin(2 * math.pi * t / 17.0)
        paint_center(img, self.light, GREEN_LIGHT, cx, cy, 0.22)

    def _drift(self, img, t, items, safe_zone=False):
        for o in items:
            m = o["r"] + 40.0
            y = ((o["y0"] - o["speed"] * t) % (H + 2 * m)) - m
            x = o["x0"] + o["ax"] * math.sin(2 * math.pi * t / o["tx"] + o["px"])
            edge = clamp01((y + m) / m) * clamp01((H + m - y) / m)
            a = o["alpha"] * (0.85 + 0.15 * math.sin(2 * math.pi * t / o["ta"] + o["pa"])) * edge
            if safe_zone:  # un peu plus discret derrière le texte central
                a *= 1.0 - 0.3 * clamp01(1.0 - abs(x - W / 2) / 900.0) * clamp01(1.0 - abs(y - 500.0) / 260.0)
            paint_center(img, o["mask"], pink_at(t, o["pc"]), x, y, a)

    def _title(self, img, t):
        e_out = EASE_IN(prog(t, TITLE_OUT_T, 0.6))
        vis = 1.0 - e_out
        if vis <= 0.0:
            return
        lift = -30.0 * e_out
        cy = CENTER_Y_TITLE + lift

        # halo rose qui respire, puis deux ondes
        halo = 0.55 * EASE_OUT(prog(t, 0.0, 1.2)) * vis
        halo *= 0.9 + 0.1 * math.sin(2 * math.pi * t / 3.2)
        paint_center(img, self.glow_title, pink_at(t), W / 2, cy, halo)
        for t0 in (0.22, 0.52):
            p = prog(t, t0, 1.7)
            if 0.0 < p < 1.0:
                ring = ring_mask(60 + 1000 * EASE_OUT(p), 1.5 + 3.5 * (1 - p))
                paint_center(img, ring, pink_at(t, 0.5), W / 2, cy, 0.85 * (1 - p) ** 1.3 * vis)

        # filets roses qui s'ouvrent depuis le centre
        for y, t0 in ((RULE_TOP_Y, 0.55), (RULE_BOTTOM_Y, 1.65)):
            w = 960 * EASE_OUT(prog(t, t0, 1.0))
            if w >= 2:
                paint_rule(img, W / 2, y, w, 3, pink_at(t, 1.2), vis)

        # lettres qui montent une à une (décalage léger, sans rebond)
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        letters = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for i, ch in enumerate(TITLE):
            if ch.isspace():
                continue
            e = EASE_OUT(prog(t, 0.42 + 0.055 * i, 0.9))
            if e <= 0.0:
                continue
            tm = self.title_chars[ch]
            x = self.title_left + self.title_xs[i]
            y = self.title_base + lift + 80.0 * (1.0 - e)
            paint_text(shadow, tm, pink_at(t, 0.8), x + 9, y + 11, e * vis)  # ombre rose décalée
            paint_text(letters, tm, WHITE, x, y, e * vis)

        # reflet rose qui balaie les lettres une fois posées
        p = prog(t, 2.25, 1.1)
        if 0.0 < p < 1.0:
            a_letters = np.asarray(letters.getchannel("A"), dtype=np.float32) / 255.0
            xc = lerp(self.title_left - 160, self.title_left + self.title_w + 160, EASE_IO(p))
            band = np.exp(-(((self.gx - xc - 0.35 * (self.gy - cy)) / 48.0) ** 2))
            glint = Image.new("RGBA", (W, H), PINK_B + (0,))
            glint.putalpha(Image.fromarray((band * a_letters * 0.95 * 255 * vis).astype(np.uint8)))
            letters.alpha_composite(glint)

        img.alpha_composite(shadow)
        img.alpha_composite(letters)

        # slogan
        a1, d1 = anim(t, 1.45, 0.8, TITLE_OUT_T, 0.6, dy_in=26, dy_out=30)
        if a1 > 0:
            paint_text(img, self.tag1, WHITE, W / 2 - self.tag1.width / 2, TAG1_BASE_Y + d1, a1)
        a2, d2 = anim(t, 1.62, 0.8, TITLE_OUT_T, 0.6, dy_in=26, dy_out=30)
        if a2 > 0:
            paint_text(img, self.tag2, PINK_SOFT, W / 2 - self.tag2.width / 2, TAG2_BASE_Y + d2, a2)

    def _card(self, img, t, k):
        start = CARD_START + CARD_LEN * k
        u = t - start
        if u < -0.1 or u > CARD_LEN + 0.1:
            return
        nm, rm = self.cards[k]
        cx = W / 2

        # halo rose derrière le texte
        halo = 0.70 * EASE_OUT(prog(u, 0.0, 0.9)) * (1.0 - EASE_IN(prog(u, 2.5, 0.6)))
        if halo > 0:
            halo *= 0.92 + 0.08 * math.sin(2 * math.pi * t / 3.4)
            paint_center(img, self.glow_card, pink_at(t), cx, NAME_CY + 20, halo)

        # deux ondes roses qui partent du nom
        for t0 in (0.04, 0.34):
            p = prog(u, t0, 1.5)
            if 0.0 < p < 1.0:
                ring = ring_mask(70 + 760 * EASE_OUT(p), 1.0 + 3.5 * (1 - p))
                paint_center(img, ring, pink_at(t, 1.0), cx, NAME_CY, 0.8 * (1 - p) ** 1.4)

        # étincelles autour du nom (quatre positions, scintillement décalé)
        half = nm.width / 2
        slots = [
            (-half - 70, -64, 74, "pink"),
            (half + 58, -88, 54, "white"),
            (-half - 24, 96, 40, "white"),
            (half + 44, 78, 62, "pink"),
        ]
        for j, (dx, dy_, size, kind) in enumerate(slots):
            p = prog(u, 0.55 + 0.16 * j, 0.95)
            if 0.0 < p < 1.0:
                env = math.sin(math.pi * p)
                sz = max(4, int(size * (0.35 + 0.65 * env)))
                spark = self.spark.resize((sz, sz), Image.Resampling.BICUBIC)
                spark = spark.rotate(70 * p * (1 if j % 2 == 0 else -1), resample=Image.Resampling.BICUBIC)
                col = pink_at(t, 2.0 * j) if kind == "pink" else WHITE
                paint_center(img, spark, col, cx + dx, NAME_CY + dy_, env ** 0.8)

        # nom (glisse vers le haut, fondu)
        a, dy = anim(u, 0.04, 0.85, 2.42, 0.55, dy_in=40, dy_out=30)
        if a > 0:
            paint_text(img, nm, WHITE, cx - nm.width / 2, NAME_CY + 0.35 * self.name_size + dy, a)

        # filet rose qui se déploie sous le nom
        sc = EASE_OUT(prog(u, 0.36, 0.7)) * (1.0 - EASE_IN(prog(u, 2.45, 0.5)))
        if sc > 0.01:
            paint_rule(img, cx, UNDERLINE_Y, 280 * sc, 6, pink_at(t, 2.0))

        # fonction (rôle), en capitales espacées
        a2, dy2 = anim(u, 0.22, 0.85, 2.36, 0.55, dy_in=24, dy_out=24)
        if a2 > 0:
            paint_text(img, rm, PINK_SOFT, cx - rm.width / 2, ROLE_BASE_Y + dy2, a2)

    def _streaks(self, img, t):
        """Balayage rose entre deux cartes (et entre le titre et la première carte)."""
        for k in range(CARD_COUNT):
            b = CARD_START + CARD_LEN * k
            p = prog(t, b - 0.42, 0.84)
            if 0.0 < p < 1.0:
                xc = lerp(-440, W + 440, EASE_IO(p))
                paint(img, self.band, pink_at(t, 3.0), xc - self.band.width / 2, 0,
                      0.42 * math.sin(math.pi * p))

    def _outro(self, img, t):
        for t0 in (OUTRO_T, OUTRO_T + 0.3):
            p = prog(t, t0, 1.8)
            if 0.0 < p < 1.0:
                ring = ring_mask(80 + 1100 * EASE_OUT(p), 1.0 + 5.0 * (1 - p))
                paint_center(img, ring, pink_at(t, 4.0), W / 2, H / 2, 0.7 * (1 - p) ** 1.2)

    def _channel(self, img, t):
        """Sous-titre « LAMEX TV Télévision », petit, en bas à gauche."""
        a, dy = anim(t, 0.9, 0.9, 99.0, 1.0, dy_in=18)
        if a <= 0:
            return
        bar_h = 30 * EASE_OUT(prog(t, 1.0, 0.7))
        if bar_h >= 1:
            paint_rule(img, 99, SUB_BASE_Y - 0.35 * 30 + dy, 6, bar_h, pink_at(t, 2.0), a)
        paint_text(img, self.ch_bold, WHITE, 120, SUB_BASE_Y + dy, a)
        paint_text(img, self.ch_light, PINK_SOFT, 120 + self.ch_bold.width + 12, SUB_BASE_Y + dy, a)

    def _fade(self, img, t):
        f = EASE_IO(prog(t, 0.0, 0.7)) * (1.0 - EASE_IO(prog(t, END_TIME - 0.9, 0.9)))
        if f >= 0.999:
            return img
        return Image.blend(Image.new("RGBA", img.size, (0, 0, 0, 255)), img, max(f, 0.0))

    # ------------------------------------------------------------- image
    def frame(self, t):
        img = self.bg.copy()
        self._ambient(img, t)
        self._drift(img, t, self.bokeh, safe_zone=True)
        self._drift(img, t, self.bubbles, safe_zone=True)
        self._drift(img, t, self.dots)
        self._title(img, t)
        for k in range(CARD_COUNT):
            self._card(img, t, k)
        self._streaks(img, t)
        self._outro(img, t)
        self._channel(img, t)
        return self._fade(img, t)


# ================================================================= export
def find_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def main():
    ap = argparse.ArgumentParser(description="Rendu du générique « Bureau Rose ».")
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "Bureau-Rose-generique.mp4"))
    ap.add_argument("--still", type=float, default=None,
                    help="exporte une image PNG à ce temps (secondes) au lieu de la vidéo")
    args = ap.parse_args()

    scene = Scene()

    if args.still is not None:
        os.makedirs(OUT_DIR, exist_ok=True)
        path = os.path.join(OUT_DIR, f"still-{args.still:05.2f}s.png")
        scene.frame(args.still).convert("RGB").save(path)
        print(path)
        return

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    total = int(round(END_TIME * FPS))
    cmd = [
        find_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-movflags", "+faststart", args.out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for i in range(total):
            proc.stdin.write(scene.frame(i / FPS).convert("RGB").tobytes())
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        sys.exit(code)
    print(args.out)


if __name__ == "__main__":
    main()
