#!/usr/bin/env python3
"""Render the ATHENA lesson as a narrated, captioned 1080p motion-design video.

Requires Pillow and imageio-ffmpeg. Narration clips are generated separately and
kept out of Git; see production/narration.json for the transcript and timings.
"""
from __future__ import annotations

import json
import math
import re
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT / "production"
AUDIO_DIR = PRODUCTION / "audio"
TEMP = PRODUCTION / "tmp_render"
EXPORTS = ROOT / "exports"
OUTPUT = EXPORTS / "ATHENA-cours-1-comprendre-l-IA.mp4"
SRT = PRODUCTION / "ATHENA-cours-1-fr.srt"
CHAPTERS = json.loads((PRODUCTION / "narration.json").read_text(encoding="utf-8"))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

WIDTH, HEIGHT, FPS = 1920, 1080, 24
SPEED = 0.85
XFADE_FRAMES = 12
XFADE = XFADE_FRAMES / FPS
TOTAL_SECONDS = sum(ch["duration"] for ch in CHAPTERS)

NAVY = "#081B2A"
NAVY2 = "#102D3D"
NAVY3 = "#18394A"
TEAL = "#21C6B7"
TEAL_DARK = "#087F7B"
CREAM = "#F7F1E5"
WHITE = "#FFFCF4"
CORAL = "#F28A64"
YELLOW = "#F2C14E"
INK = "#102331"
MUTED = "#91A9B6"
LINE = "#315363"
RED = "#E76566"
GREEN = "#6ED2A4"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_SANS = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_SERIF = FONT_DIR / "DejaVuSerif-Bold.ttf"
FONT_MONO = FONT_DIR / "DejaVuSansMono.ttf"


def font(size: int, kind: str = "sans") -> ImageFont.FreeTypeFont:
    path = {"sans": FONT_SANS, "bold": FONT_BOLD, "serif": FONT_SERIF, "mono": FONT_MONO}[kind]
    return ImageFont.truetype(str(path), size=size)


FONTS = {
    "micro": font(20, "bold"),
    "small": font(25),
    "small_bold": font(25, "bold"),
    "body": font(32),
    "body_bold": font(32, "bold"),
    "card": font(36, "bold"),
    "card_body": font(27),
    "title": font(76, "serif"),
    "title_sans": font(78, "bold"),
    "hero": font(112, "serif"),
    "hero_sans": font(100, "bold"),
    "big_num": font(128, "bold"),
    "mono": font(27, "mono"),
}


def ffmpeg_run(args: list[str], *, cwd: Path | None = None) -> None:
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *args]
    print("$", " ".join(shlex.quote(x) for x in cmd[:8]), "...", flush=True)
    result = subprocess.run(cmd, cwd=str(cwd or ROOT), text=True, capture_output=True)
    if result.returncode:
        print(result.stderr[-6000:], file=sys.stderr)
        raise RuntimeError(f"ffmpeg exited with code {result.returncode}")


def mix_color(a: str, b: str, t: float) -> str:
    a = a.lstrip("#")
    b = b.lstrip("#")
    vals = [round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(vals)


def make_background(chapter_no: int, progress: float) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT))
    d = ImageDraw.Draw(image)
    top = (6, 22, 34)
    bottom = (12, 36, 51)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        c = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        d.line((0, y, WIDTH, y), fill=c)
    # Subtle geometric atmosphere; kept low contrast so diagrams stay primary.
    d.ellipse((1280, -330, 2110, 500), fill="#0D2D3B")
    d.ellipse((-340, 700, 360, 1400), fill="#0A2433")
    for x in range(54, WIDTH - 40, 52):
        for y in range(164, 980, 52):
            d.ellipse((x, y, x + 2, y + 2), fill="#173444")
    # Header.
    d.text((92, 38), "ATHENA", font=font(28, "bold"), fill=TEAL)
    d.text((246, 43), "COURS 01  /  COMPRENDRE L’IA", font=font(22, "bold"), fill=CREAM)
    title = CHAPTERS[chapter_no - 1]["title"].upper()
    badge_w = max(180, int(d.textlength(title, font=FONTS["micro"])) + 52)
    d.rounded_rectangle((WIDTH - badge_w - 94, 39, WIDTH - 94, 91), radius=22, fill=NAVY2, outline=LINE, width=2)
    d.text((WIDTH - badge_w - 68, 53), title, font=FONTS["micro"], fill=CREAM)
    d.text((WIDTH - 90, 101), f"{chapter_no:02d} / 10", font=font(17, "bold"), fill=MUTED, anchor="ra")
    # Top progress line, so bottom captions stay unobstructed.
    x0, x1, py = 92, WIDTH - 92, 124
    d.rounded_rectangle((x0, py, x1, py + 5), radius=3, fill="#1B3D4C")
    if progress > 0:
        d.rounded_rectangle((x0, py, x0 + int((x1 - x0) * min(1, progress)), py + 5), radius=3, fill=TEAL)
    return image


def wrapped_lines(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=f) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, f: ImageFont.FreeTypeFont,
                 fill: str, width: int, spacing: int = 10, align: str = "left") -> int:
    lines = wrapped_lines(draw, text, f, width)
    draw.multiline_text(xy, "\n".join(lines), font=f, fill=fill, spacing=spacing, align=align)
    bbox = draw.multiline_textbbox(xy, "\n".join(lines), font=f, spacing=spacing, align=align)
    return bbox[3] - bbox[1]


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = CREAM,
         outline: str | None = None, radius: int = 26, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width if outline else 1)


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, fill: str = NAVY2,
         color: str = CREAM, f: ImageFont.FreeTypeFont | None = None, pad_x: int = 22, pad_y: int = 12) -> tuple[int, int]:
    f = f or FONTS["small_bold"]
    bb = draw.textbbox((0, 0), label, font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle((x, y, x + w + pad_x * 2, y + h + pad_y * 2), radius=(h + pad_y * 2) // 2, fill=fill)
    draw.text((x + pad_x, y + pad_y - bb[1]), label, font=f, fill=color)
    return w + pad_x * 2, h + pad_y * 2


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = TEAL, width: int = 8) -> None:
    draw.line((start, end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 20
    p1 = (end[0] - size * math.cos(angle - math.pi / 6), end[1] - size * math.sin(angle - math.pi / 6))
    p2 = (end[0] - size * math.cos(angle + math.pi / 6), end[1] - size * math.sin(angle + math.pi / 6))
    draw.polygon([end, p1, p2], fill=color)


def icon(draw: ImageDraw.ImageDraw, name: str, center: tuple[int, int], size: int, color: str = TEAL) -> None:
    cx, cy = center
    x0, y0, x1, y1 = cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2
    lw = max(5, size // 14)
    if name in {"chat", "text"}:
        draw.rounded_rectangle((x0 + 6, y0 + 7, x1 - 6, y1 - 14), radius=size // 7, outline=color, width=lw)
        draw.polygon([(x0 + size // 4, y1 - 14), (x0 + size // 4 + 5, y1 - 2), (x0 + size // 2, y1 - 14)], fill=color)
        if name == "chat":
            for i in range(3):
                px = x0 + size // 3 + i * size // 6
                draw.ellipse((px - 5, cy - 2, px + 5, cy + 8), fill=color)
        else:
            draw.line((x0 + size // 4, y0 + size // 3, x1 - size // 4, y0 + size // 3), fill=color, width=lw)
            draw.line((x0 + size // 4, cy, x1 - size // 4, cy), fill=color, width=lw)
    elif name in {"image", "photo"}:
        draw.rounded_rectangle((x0 + 5, y0 + 5, x1 - 5, y1 - 5), radius=size // 8, outline=color, width=lw)
        draw.ellipse((x0 + size // 2, y0 + size // 4, x0 + size // 2 + size // 7, y0 + size // 4 + size // 7), fill=color)
        draw.line((x0 + size // 6, y1 - size // 4, cx - 4, cy + 4, cx + size // 8, cy - 2, x1 - size // 7, y1 - size // 4), fill=color, width=lw, joint="curve")
    elif name == "phone":
        draw.rounded_rectangle((x0 + size // 5, y0 + 2, x1 - size // 5, y1 - 2), radius=size // 7, outline=color, width=lw)
        draw.line((cx - size // 9, y0 + size // 6, cx + size // 9, y0 + size // 6), fill=color, width=lw)
        draw.ellipse((cx - 5, y1 - size // 6 - 5, cx + 5, y1 - size // 6 + 5), fill=color)
    elif name in {"voice", "mic"}:
        draw.rounded_rectangle((cx - size // 7, y0 + size // 9, cx + size // 7, cy + size // 7), radius=size // 7, outline=color, width=lw)
        draw.arc((cx - size // 3, cy - size // 7, cx + size // 3, y1 - size // 8), 0, 180, fill=color, width=lw)
        draw.line((cx, y1 - size // 8, cx, y1 - 2), fill=color, width=lw)
        draw.line((cx - size // 5, y1 - 2, cx + size // 5, y1 - 2), fill=color, width=lw)
    elif name in {"play", "video"}:
        draw.rounded_rectangle((x0 + 3, y0 + 8, x1 - 3, y1 - 8), radius=size // 8, outline=color, width=lw)
        draw.polygon([(cx - size // 10, cy - size // 5), (cx - size // 10, cy + size // 5), (cx + size // 5, cy)], fill=color)
    elif name == "code":
        draw.line((cx - size // 10, y0 + size // 4, x0 + size // 5, cy, cx - size // 10, y1 - size // 4), fill=color, width=lw, joint="curve")
        draw.line((cx + size // 10, y0 + size // 4, x1 - size // 5, cy, cx + size // 10, y1 - size // 4), fill=color, width=lw, joint="curve")
        draw.line((cx + size // 10, y0 + size // 5, cx - size // 10, y1 - size // 5), fill=color, width=lw)
    elif name == "filter":
        draw.polygon([(x0 + size // 6, y0 + size // 5), (x1 - size // 6, y0 + size // 5), (cx + size // 9, cy), (cx + size // 9, y1 - size // 8), (cx - size // 9, y1 - size // 8), (cx - size // 9, cy)], outline=color)
        draw.line((x0 + size // 6, y0 + size // 5, x1 - size // 6, y0 + size // 5, cx + size // 9, cy, cx + size // 9, y1 - size // 8), fill=color, width=lw, joint="curve")
        draw.line((cx - size // 9, y1 - size // 8, cx - size // 9, cy, x0 + size // 6, y0 + size // 5), fill=color, width=lw, joint="curve")
    elif name == "target":
        for r in (size // 2 - 4, size // 3, size // 6):
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=lw)
        draw.line((cx, cy, x1 - 5, y0 + 5), fill=color, width=lw)
    elif name == "pin":
        draw.ellipse((cx - size // 4, y0 + 2, cx + size // 4, cy + size // 6), outline=color, width=lw)
        draw.ellipse((cx - size // 11, y0 + size // 5, cx + size // 11, y0 + size // 5 + size // 5), fill=color)
        draw.polygon([(cx - size // 4 + 2, cy), (cx + size // 4 - 2, cy), (cx, y1 - 2)], fill=color)
    elif name in {"shield", "check"}:
        pts = [(cx, y0 + 2), (x1 - 6, y0 + size // 5), (x1 - size // 8, cy + size // 5), (cx, y1 - 2), (x0 + size // 8, cy + size // 5), (x0 + 6, y0 + size // 5)]
        draw.polygon(pts, outline=color)
        draw.line(pts + [pts[0]], fill=color, width=lw, joint="curve")
        if name == "check":
            draw.line((cx - size // 5, cy, cx - size // 20, cy + size // 6, cx + size // 4, cy - size // 5), fill=color, width=lw, joint="curve")
    elif name == "lock":
        draw.rounded_rectangle((x0 + size // 5, cy - size // 10, x1 - size // 5, y1 - size // 10), radius=size // 12, outline=color, width=lw)
        draw.arc((cx - size // 5, y0 + size // 10, cx + size // 5, cy + size // 7), 180, 360, fill=color, width=lw)
        draw.ellipse((cx - 5, cy + size // 8, cx + 5, cy + size // 8 + 10), fill=color)
    elif name == "search":
        draw.ellipse((x0 + size // 9, y0 + size // 9, cx + size // 8, cy + size // 8), outline=color, width=lw)
        draw.line((cx + size // 10, cy + size // 10, x1 - size // 8, y1 - size // 8), fill=color, width=lw)
    elif name == "doc":
        draw.rounded_rectangle((x0 + size // 6, y0 + 2, x1 - size // 6, y1 - 2), radius=size // 10, outline=color, width=lw)
        for i in range(3):
            yy = y0 + size // 3 + i * size // 6
            draw.line((x0 + size // 4, yy, x1 - size // 4, yy), fill=color, width=lw)
    elif name == "spark":
        draw.line((cx, y0 + 2, cx, y1 - 2), fill=color, width=lw)
        draw.line((x0 + 2, cy, x1 - 2, cy), fill=color, width=lw)
        draw.line((x0 + size // 5, y0 + size // 5, x1 - size // 5, y1 - size // 5), fill=color, width=max(3, lw - 2))
        draw.line((x0 + size // 5, y1 - size // 5, x1 - size // 5, y0 + size // 5), fill=color, width=max(3, lw - 2))
    elif name == "eye":
        draw.arc((x0 + 3, cy - size // 4, x1 - 3, cy + size // 4), 180, 360, fill=color, width=lw)
        draw.arc((x0 + 3, cy - size // 4, x1 - 3, cy + size // 4), 0, 180, fill=color, width=lw)
        draw.ellipse((cx - size // 10, cy - size // 10, cx + size // 10, cy + size // 10), fill=color)
    else:
        draw.ellipse((x0 + 4, y0 + 4, x1 - 4, y1 - 4), outline=color, width=lw)
        draw.text((cx, cy), "?", font=font(size // 2, "bold"), fill=color, anchor="mm")


def card_with_icon(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], name: str, title: str,
                   detail: str = "", accent: str = TEAL, highlighted: bool = False) -> None:
    x0, y0, x1, y1 = box
    fill = CREAM if highlighted else NAVY2
    fg = INK if highlighted else CREAM
    muted = "#405864" if highlighted else MUTED
    card(draw, box, fill=fill, outline=accent if not highlighted else None, radius=26, width=3)
    icon(draw, name, (x0 + 75, y0 + 76), 76, accent if highlighted else accent)
    draw.text((x0 + 136, y0 + 43), title, font=FONTS["card"], fill=fg)
    if detail:
        draw_wrapped(draw, (x0 + 38, y0 + 142), detail, FONTS["card_body"], muted, x1 - x0 - 76, spacing=7)


def title_block(draw: ImageDraw.ImageDraw, text: str, y: int = 185, color: str = CREAM,
                size: int = 72, max_width: int = 1440, x: int = 120, kind: str = "serif") -> int:
    f = font(size, kind)
    return draw_wrapped(draw, (x, y), text, f, color, max_width, spacing=9)


def draw_shop(draw: ImageDraw.ImageDraw, x: int, y: int, scale: int = 1) -> None:
    w, h = 590 * scale, 390 * scale
    # Building, awning and door; generic shop, not a real business.
    draw.rounded_rectangle((x, y + 105 * scale, x + w, y + h), radius=22 * scale, fill=CREAM)
    draw.rectangle((x + 22 * scale, y + 110 * scale, x + w - 22 * scale, y + 158 * scale), fill=TEAL_DARK)
    awn_y = y + 50 * scale
    draw.rectangle((x + 10 * scale, awn_y, x + w - 10 * scale, y + 110 * scale), fill=CORAL)
    stripe_w = 82 * scale
    for sx in range(x + 10 * scale, x + w - 10 * scale, stripe_w):
        draw.rectangle((sx, awn_y, min(sx + stripe_w // 2, x + w - 10 * scale), y + 110 * scale), fill=YELLOW)
    draw.rectangle((x + 50 * scale, y + 170 * scale, x + 340 * scale, y + 350 * scale), fill="#CDEBE2", outline=TEAL_DARK, width=5 * scale)
    draw.line((x + 195 * scale, y + 170 * scale, x + 195 * scale, y + 350 * scale), fill=TEAL_DARK, width=4 * scale)
    draw.rectangle((x + 390 * scale, y + 170 * scale, x + 530 * scale, y + h), fill=NAVY2, outline=TEAL_DARK, width=5 * scale)
    draw.ellipse((x + 505 * scale, y + 260 * scale, x + 519 * scale, y + 274 * scale), fill=YELLOW)
    # Clothing rack and simple garments behind the window.
    rack_y = y + 260 * scale
    draw.line((x + 70 * scale, rack_y, x + 320 * scale, rack_y), fill=TEAL_DARK, width=5 * scale)
    for i, c in enumerate((CORAL, YELLOW, TEAL, "#A7BCE0")):
        gx = x + 95 * scale + i * 52 * scale
        draw.line((gx, rack_y, gx, rack_y + 16 * scale), fill=INK, width=3 * scale)
        draw.polygon([(gx - 20 * scale, rack_y + 16 * scale), (gx + 20 * scale, rack_y + 16 * scale), (gx + 25 * scale, rack_y + 82 * scale), (gx - 25 * scale, rack_y + 82 * scale)], fill=c)


def scene_01(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        chip(draw, 125, 195, "UNE QUESTION SIMPLE", fill="#174D58", color=TEAL)
        draw.multiline_text((120, 290), "C’EST QUOI\nL’IA ?", font=font(112, "serif"), fill=CREAM, spacing=8)
        draw.text((128, 565), "L’intelligence artificielle,\nsans jargon.", font=font(37), fill=MUTED, spacing=11)
        # Three floating idea cards.
        cards = [(900, 260, 1350, 445, "chat", "TEXTE", TEAL), (1375, 260, 1800, 445, "image", "IMAGES", YELLOW), (1125, 490, 1600, 675, "phone", "OUTILS", CORAL)]
        for x0, y0, x1, y1, ic, label, accent in cards:
            card(draw, (x0, y0, x1, y1), fill=NAVY2, outline=LINE)
            icon(draw, ic, (x0 + 105, (y0 + y1) // 2), 105, accent)
            draw.text((x0 + 190, y0 + 72), label, font=font(34, "bold"), fill=CREAM)
        draw.ellipse((1668, 550, 1760, 642), outline=TEAL, width=5)
        icon(draw, "spark", (1714, 596), 52, TEAL)
    else:
        title_block(draw, "EST-CE QU’UNE MACHINE PENSE COMME UN HUMAIN ?", y=235, size=79, max_width=1050)
        draw.text((130, 535), "La question mérite une réponse simple.", font=font(34), fill=MUTED)
        card(draw, (1230, 250, 1735, 760), fill=NAVY2, outline=TEAL, radius=36, width=3)
        draw.ellipse((1370, 320, 1595, 545), outline=TEAL, width=9)
        draw.text((1482, 435), "?", font=font(144, "bold"), fill=CREAM, anchor="mm")
        chip(draw, 1335, 615, "ON VA VÉRIFIER", fill="#174D58", color=TEAL)
        for i, col in enumerate((CORAL, YELLOW, TEAL)):
            draw.ellipse((280 + i * 84, 700, 314 + i * 84, 734), fill=col)


def scene_02(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        chip(draw, 125, 190, "LEÇON 01", fill="#174D58", color=TEAL)
        draw.text((120, 285), "ATHENA", font=font(117, "serif"), fill=TEAL)
        draw_wrapped(draw, (128, 440), "COMPRENDRE L’INTELLIGENCE ARTIFICIELLE", font(69, "bold"), CREAM, 900, spacing=8)
        draw.text((132, 690), "Apprendre sans jargon · exemples concrets", font=font(30), fill=MUTED)
        # Abstract Dakar map motif, deliberately schematic.
        pts = [(1320, 250), (1460, 270), (1505, 345), (1620, 380), (1570, 458), (1660, 540), (1560, 610), (1520, 720), (1420, 665), (1380, 565), (1280, 520), (1310, 420), (1230, 340), (1320, 250)]
        draw.line(pts, fill=TEAL, width=8, joint="curve")
        draw.ellipse((1430, 410, 1495, 475), fill=CORAL)
        draw.ellipse((1450, 430, 1475, 455), fill=CREAM)
        draw.text((1260, 780), "DAKAR", font=font(27, "bold"), fill=CREAM)
    else:
        title_block(draw, "DES EXEMPLES POUR LES ÉTUDES, LA FORMATION ET LE TRAVAIL", y=205, size=67, max_width=1580)
        cards = [
            ((140, 405, 650, 730), "doc", "ÉTUDES", "Comprendre une notion", TEAL),
            ((705, 405, 1215, 730), "target", "FORMATION", "Préparer un exercice", YELLOW),
            ((1270, 405, 1780, 730), "spark", "ACTIVITÉS", "Préparer un brouillon", CORAL),
        ]
        for box, ic, heading, detail, color in cards:
            card_with_icon(draw, box, ic, heading, detail, color)
        draw.text((140, 815), "En collaboration avec LAMEX INSTITUT · Parcelles Assainies, Dakar", font=font(27), fill=MUTED)


def scene_03(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        title_block(draw, "L’IA, C’EST UN ENSEMBLE DE MÉTHODES ET DE PROGRAMMES", y=194, size=63, max_width=1630)
        labels = [(150, 465, 575, 660, "INFORMATIONS", TEAL), (745, 465, 1175, 660, "IA", YELLOW), (1345, 465, 1770, 660, "TÂCHES", CORAL)]
        for x0, y0, x1, y1, label, color in labels:
            card(draw, (x0, y0, x1, y1), fill=NAVY2, outline=color, radius=30, width=4)
            draw.text(((x0 + x1) // 2, (y0 + y1) // 2), label, font=font(36, "bold"), fill=CREAM, anchor="mm")
        arrow(draw, (610, 562), (710, 562), TEAL, 8)
        arrow(draw, (1210, 562), (1310, 562), TEAL, 8)
        for i in range(7):
            xx = 205 + i * 47
            draw.ellipse((xx, 710, xx + 13, 723), fill=(TEAL, YELLOW, CORAL)[i % 3])
        draw.text((150, 770), "La machine traite des informations pour réaliser certaines tâches.", font=font(31), fill=MUTED)
    elif state == 1:
        title_block(draw, "DES TÂCHES QU’ON ASSOCIE SOUVENT À L’INTELLIGENCE", y=198, size=62, max_width=1630)
        items = [
            ((130, 390, 650, 625), "image", "RECONNAÎTRE", "des formes", TEAL),
            ((700, 390, 1220, 625), "chat", "COMPRENDRE", "une question", YELLOW),
            ((1270, 390, 1790, 625), "filter", "CLASSER", "des informations", CORAL),
        ]
        for box, ic, heading, detail, color in items:
            card_with_icon(draw, box, ic, heading, detail, color)
        card_with_icon(draw, (420, 640, 930, 820), "play", "RECOMMANDER", "un contenu", TEAL)
        card_with_icon(draw, (990, 640, 1500, 820), "text", "PRODUIRE", "un texte", YELLOW)
    else:
        title_block(draw, "UNE IA N’EST PAS FORCÉMENT UN ROBOT", y=220, size=75, max_width=1370)
        draw.text((130, 400), "Elle peut être dans un site, une appli ou un téléphone.", font=font(34), fill=MUTED)
        for i, (ic, label, color) in enumerate((("phone", "TÉLÉPHONE", TEAL), ("doc", "SITE WEB", YELLOW), ("chat", "APPLICATION", CORAL))):
            x = 145 + i * 565
            card(draw, (x, 560, x + 450, 795), fill=NAVY2, outline=LINE)
            icon(draw, ic, (x + 100, 677), 92, color)
            draw.text((x + 175, 646), label, font=font(29, "bold"), fill=CREAM)
        chip(draw, 130, 845, "ELLE TRAITE DES INFORMATIONS · ELLE NE RESSENT PAS D’ÉMOTIONS", fill="#174D58", color=TEAL)


def scene_04(draw: ImageDraw.ImageDraw, state: int) -> None:
    title_block(draw, "DEUX GRANDES FAMILLES D’USAGES", y=205, size=75, max_width=1600)
    # Two contrasting panels remain clear and comparable.
    card(draw, (120, 370, 900, 835), fill=NAVY2, outline=TEAL, radius=34, width=3)
    card(draw, (1020, 370, 1800, 835), fill=NAVY2, outline=CORAL, radius=34, width=3)
    chip(draw, 165, 410, "ANALYSER OU RECOMMANDER", fill="#174D58", color=TEAL, f=font(24, "bold"))
    chip(draw, 1065, 410, "GÉNÉRER DU CONTENU", fill="#49323A", color=CORAL, f=font(24, "bold"))
    left = [("voice", "Commande vocale"), ("filter", "Filtre anti-spam"), ("play", "Vidéo conseillée"), ("image", "Image classée")]
    for i, (ic, label) in enumerate(left):
        row = i // 2
        col = i % 2
        x = 160 + col * 365
        y = 505 + row * 150
        icon(draw, ic, (x + 48, y + 44), 66, TEAL if state == 0 or i < 2 else MUTED)
        draw.text((x + 96, y + 30), label, font=font(25, "bold"), fill=CREAM if state == 0 or i < 2 else MUTED)
    right = [("text", "Brouillon de texte"), ("image", "Nouvelle image"), ("code", "Code")]
    for i, (ic, label) in enumerate(right):
        x = 1080 + i * 225
        icon(draw, ic, (x + 78, 600), 100, CORAL if state == 1 or i == 0 else MUTED)
        draw.text((x + 78, 700), label, font=font(23, "bold"), fill=CREAM, anchor="mm")
    draw.text((160, 785), "Filtrer · reconnaître · classer", font=font(26), fill=MUTED)
    draw.text((1080, 785), "Créer un contenu à partir d’une consigne", font=font(26), fill=MUTED)


def scene_05(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        title_block(draw, "L’IA GÉNÉRATIVE PRODUIT UN CONTENU À PARTIR D’UNE CONSIGNE", y=195, size=61, max_width=1640)
        steps = [(140, "CONSIGNE", TEAL), (725, "MODÈLE", YELLOW), (1310, "RÉPONSE", CORAL)]
        for x, label, color in steps:
            card(draw, (x, 475, x + 430, 685), fill=NAVY2, outline=color, radius=32, width=4)
            draw.text((x + 215, 580), label, font=font(39, "bold"), fill=CREAM, anchor="mm")
        arrow(draw, (590, 580), (690, 580), TEAL, 8)
        arrow(draw, (1175, 580), (1275, 580), TEAL, 8)
        for row in range(3):
            for col in range(7 - row):
                xx = 805 + col * 44 + row * 20
                yy = 740 + row * 31
                draw.rounded_rectangle((xx, yy, xx + 27, yy + 20), radius=6, fill=(TEAL, YELLOW, CORAL)[(row + col) % 3])
    elif state == 1:
        title_block(draw, "TEXTE · IMAGE · VOIX · CODE", y=215, size=77, max_width=1450)
        # Token-like blocks grow into a response bubble, without depicting a mind.
        card(draw, (140, 420, 605, 710), fill=NAVY2, outline=TEAL)
        icon(draw, "chat", (370, 530), 100, TEAL)
        draw.text((370, 650), "TA CONSIGNE", font=font(27, "bold"), fill=CREAM, anchor="mm")
        for i, color in enumerate((TEAL, YELLOW, CORAL, TEAL, YELLOW, CORAL)):
            x = 710 + i * 53
            y = 545 + (i % 2) * 56
            draw.rounded_rectangle((x, y, x + 34, y + 28), radius=7, fill=color)
        arrow(draw, (1080, 585), (1200, 585), TEAL, 8)
        card(draw, (1240, 420, 1780, 710), fill=CREAM, radius=30)
        draw.text((1305, 474), "BROUILLON", font=font(29, "bold"), fill=INK)
        for i, w in enumerate((370, 420, 320, 390)):
            draw.rounded_rectangle((1305, 540 + i * 42, 1305 + w, 554 + i * 42), radius=7, fill="#8FA3A9")
    else:
        card(draw, (175, 300, 1745, 745), fill=CREAM, radius=40)
        icon(draw, "search", (425, 520), 145, CORAL)
        draw.text((570, 395), "UNE RÉPONSE FLUIDE", font=font(57, "bold"), fill=INK)
        draw.text((570, 510), "≠", font=font(76, "bold"), fill=CORAL)
        draw.text((690, 528), "UNE PREUVE", font=font(62, "bold"), fill=INK)
        draw.text((570, 640), "Toujours vérifier les faits importants.", font=font(32), fill="#405864")
        chip(draw, 130, 820, "L’OUTIL PEUT SE TROMPER AVEC ASSURANCE", fill="#49323A", color=CORAL)


def scene_06(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        chip(draw, 130, 190, "EXEMPLE FICTIF · DAKAR", fill="#174D58", color=TEAL)
        draw_shop(draw, 150, 345, 1)
        draw.text((825, 310), "UNE BOUTIQUE\nDE VÊTEMENTS", font=font(67, "serif"), fill=CREAM, spacing=8)
        draw.text((830, 515), "Préparer un brouillon\npour une nouvelle collection.", font=font(35), fill=MUTED, spacing=11)
        card(draw, (1260, 640, 1730, 850), fill=NAVY2, outline=LINE)
        icon(draw, "phone", (1350, 745), 78, TEAL)
        draw.text((1410, 700), "MESSAGE", font=font(23, "bold"), fill=CREAM)
        for i, w in enumerate((225, 290, 180)):
            draw.rounded_rectangle((1410, 752 + i * 26, 1410 + w, 765 + i * 26), radius=6, fill="#65808A")
    elif state == 1:
        title_block(draw, "UNE BONNE CONSIGNE DONNE LE CADRE", y=205, size=70, max_width=1600)
        card(draw, (160, 365, 1760, 785), fill=CREAM, radius=32)
        chip(draw, 210, 415, "POUR LA BOUTIQUE", fill="#D8F1E9", color=TEAL_DARK)
        lines = [
            ("TÂCHE", "Rédige un message WhatsApp"),
            ("FORMAT", "50 mots maximum · français simple"),
            ("TON", "Chaleureux"),
            ("LIMITE", "N’invente ni prix, ni adresse, ni numéro"),
        ]
        y = 500
        for label, value in lines:
            draw.text((220, y), label, font=font(24, "bold"), fill=TEAL_DARK)
            draw.text((430, y - 3), value, font=font(30, "bold"), fill=INK)
            y += 66
    else:
        title_block(draw, "L’IA PROPOSE. LA PERSONNE RELIT ET COMPLÈTE.", y=200, size=65, max_width=1600)
        card(draw, (290, 365, 1630, 800), fill=CREAM, radius=34)
        chip(draw, 350, 405, "EXEMPLE À VÉRIFIER", fill="#FBE2D9", color="#B64A40")
        draw_wrapped(draw, (365, 500), "Bonjour ! Découvrez notre nouvelle collection. Écris-nous pour en savoir plus.", font(39, "bold"), INK, 1130, spacing=12)
        draw.line((365, 650, 1545, 650), fill="#D8D0C1", width=3)
        draw.text((365, 685), "Prix : [à compléter]   ·   Adresse : [à compléter]", font=font(27, "bold"), fill="#52636B")
        chip(draw, 365, 740, "BROUILLON, PAS UNE INFORMATION VÉRIFIÉE", fill="#174D58", color=TEAL, f=font(22, "bold"))


def scene_07(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        title_block(draw, "LES 4 REPÈRES D’UNE CONSIGNE UTILE", y=210, size=75, max_width=1600)
        items = [
            ("pin", "CONTEXTE", "Où et pour qui ?", TEAL),
            ("target", "TÂCHE", "Que veux-tu faire ?", YELLOW),
            ("doc", "FORMAT", "Quelle forme ?", CORAL),
            ("shield", "LIMITES", "Que faut-il éviter ?", GREEN),
        ]
        for i, (ic, title, detail, color) in enumerate(items):
            x = 120 + i * 445
            card_with_icon(draw, (x, 420, x + 400, 740), ic, title, detail, color, highlighted=(state == 0 and i == 0))
            if i < 3:
                arrow(draw, (x + 408, 580), (x + 438, 580), MUTED, 5)
        draw.text((145, 825), "Contexte  →  Tâche  →  Format  →  Limites", font=font(32, "bold"), fill=CREAM)
    elif state == 1:
        title_block(draw, "EXEMPLE : PRÉPARER UN ATELIER À DAKAR", y=205, size=67, max_width=1650)
        rows = [
            ("CONTEXTE", "Adultes débutants · Dakar", TEAL),
            ("TÂCHE", "Proposer un plan de cours", YELLOW),
            ("FORMAT", "45 min · 3 parties · 1 exercice", CORAL),
            ("LIMITES", "Ne rien inventer · dire quoi vérifier", GREEN),
        ]
        y = 380
        for label, value, color in rows:
            card(draw, (155, y, 1765, y + 92), fill=NAVY2, outline=LINE, radius=20)
            chip(draw, 182, y + 18, label, fill=color, color=INK, f=font(21, "bold"), pad_x=15, pad_y=9)
            draw.text((500, y + 25), value, font=font(31, "bold"), fill=CREAM)
            y += 115
    else:
        card(draw, (190, 330, 1730, 735), fill=CREAM, radius=38)
        icon(draw, "check", (420, 530), 140, TEAL_DARK)
        draw.text((565, 405), "PLUS CLAIRE", font=font(62, "bold"), fill=INK)
        draw.text((565, 520), "≠", font=font(76, "bold"), fill=CORAL)
        draw.text((680, 535), "GARANTIE D’EXACTITUDE", font=font(46, "bold"), fill=INK)
        draw.text((565, 640), "La consigne aide ; la vérification reste nécessaire.", font=font(29), fill="#405864")
        chip(draw, 160, 805, "CONTEXTE  ·  TÂCHE  ·  FORMAT  ·  LIMITES", fill="#174D58", color=TEAL)


def scene_08(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        title_block(draw, "TROIS BONS RÉFLEXES", y=205, size=82, max_width=1450)
        cards = [
            ((120, 390, 670, 810), "search", "VÉRIFIER", "Dates · prix · chiffres · noms", CORAL),
            ((685, 390, 1235, 810), "lock", "PROTÉGER", "Mot de passe · identité · données privées", TEAL),
            ((1250, 390, 1800, 810), "check", "GARDER SON\nJUGEMENT", "Relire et décider soi-même", YELLOW),
        ]
        for box, ic, heading, detail, color in cards:
            x0, y0, x1, y1 = box
            card(draw, box, fill=NAVY2, outline=color, radius=30, width=3)
            icon(draw, ic, (x0 + 110, y0 + 112), 112, color)
            draw.multiline_text((x0 + 52, y0 + 218), heading, font=font(35, "bold"), fill=CREAM, spacing=7)
            draw_wrapped(draw, (x0 + 52, y0 + 322), detail, font(26), MUTED, x1 - x0 - 104, spacing=7)
    elif state == 1:
        title_block(draw, "NE PARTAGE PAS TES DONNÉES CONFIDENTIELLES", y=205, size=67, max_width=1640)
        card(draw, (190, 375, 1730, 790), fill=NAVY2, outline=TEAL, radius=34, width=3)
        icon(draw, "lock", (415, 560), 150, TEAL)
        data = [("MOT DE PASSE", CORAL), ("PIÈCE D’IDENTITÉ", YELLOW), ("DOSSIER NOMINATIF", CORAL)]
        for i, (label, color) in enumerate(data):
            y = 435 + i * 105
            card(draw, (650, y, 1500, y + 76), fill="#173B4A", outline=LINE, radius=18)
            draw.text((700, y + 20), label, font=font(30, "bold"), fill=CREAM)
            draw.line((675, y + 39, 1470, y + 39), fill=color, width=4)
        draw.text((650, 790), "Ne transmettre que les informations nécessaires.", font=font(29), fill=MUTED)
    else:
        title_block(draw, "UNE IA PEUT AIDER. C’EST À TOI DE DÉCIDER.", y=220, size=73, max_width=1580)
        for i, (ic, label, color) in enumerate((("search", "Vérifier les faits", CORAL), ("lock", "Protéger les données", TEAL), ("check", "Garder son jugement", YELLOW))):
            x = 150 + i * 570
            card_with_icon(draw, (x, 490, x + 500, 735), ic, label.upper(), "", color)
        chip(draw, 150, 815, "L’OUTIL PROPOSE · LA PERSONNE VÉRIFIE ET CHOISIT", fill="#174D58", color=TEAL)


def scene_09(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        chip(draw, 130, 190, "À TOI DE JOUER", fill="#174D58", color=TEAL)
        title_block(draw, "CHOISIS UNE TÂCHE SIMPLE", y=285, size=82, max_width=1450)
        labels = ["CONTEXTE", "TÂCHE", "FORMAT", "LIMITES"]
        colors = [TEAL, YELLOW, CORAL, GREEN]
        for i, label in enumerate(labels):
            x = 125 + i * 440
            card(draw, (x, 535, x + 400, 770), fill=NAVY2, outline=colors[i], radius=26, width=3)
            draw.ellipse((x + 34, 580, x + 90, 636), fill=colors[i])
            draw.text((x + 112, 596), label, font=font(30, "bold"), fill=CREAM)
            draw.line((x + 40, 690, x + 350, 690), fill=LINE, width=3)
            draw.line((x + 40, 728, x + 300, 728), fill=LINE, width=3)
        draw.text((135, 835), "Exemple : préparer un message fictif pour une petite activité.", font=font(28), fill=MUTED)
    else:
        title_block(draw, "AVANT DE VALIDER, DEMANDE-TOI…", y=230, size=74, max_width=1510)
        card(draw, (170, 405, 1750, 790), fill=CREAM, radius=36)
        icon(draw, "search", (420, 590), 122, TEAL_DARK)
        draw_wrapped(draw, (545, 495), "Qu’est-ce qui doit être vérifié ?", font(44, "bold"), INK, 1020, spacing=12)
        draw_wrapped(draw, (545, 615), "Quelles informations personnelles as-tu évité de partager ?", font(34), "#405864", 1050, spacing=9)
        chip(draw, 645, 830, "PAUSE RÉFLEXION", fill="#174D58", color=TEAL)


def scene_10(draw: ImageDraw.ImageDraw, state: int) -> None:
    if state == 0:
        title_block(draw, "À RETENIR", y=205, size=84, max_width=1000)
        items = [
            ((130, 385, 680, 745), "filter", "L’IA ANALYSE\nOU GÉNÈRE", "Différents outils, différentes tâches", TEAL),
            ((685, 385, 1235, 745), "search", "VÉRIFIER\nLES RÉPONSES", "Une réponse fluide peut se tromper", CORAL),
            ((1240, 385, 1790, 745), "lock", "PROTÉGER\nSES DONNÉES", "Garder son jugement", YELLOW),
        ]
        for box, ic, heading, detail, color in items:
            x0, y0, x1, y1 = box
            card(draw, box, fill=NAVY2, outline=color, radius=28, width=3)
            icon(draw, ic, (x0 + 100, y0 + 88), 88, color)
            draw.multiline_text((x0 + 44, y0 + 160), heading, font=font(32, "bold"), fill=CREAM, spacing=6)
            draw_wrapped(draw, (x0 + 44, y0 + 265), detail, font(23), MUTED, x1 - x0 - 88, spacing=6)
    else:
        chip(draw, 130, 230, "PROCHAINE LEÇON", fill="#174D58", color=TEAL)
        draw.text((125, 340), "ATHENA", font=font(118, "serif"), fill=TEAL)
        draw_wrapped(draw, (130, 505), "UTILISER CHATGPT\nPAS À PAS", font(82, "bold"), CREAM, 1120, spacing=10)
        draw.text((135, 765), "Abonne-toi pour suivre les prochains cours.", font=font(32), fill=MUTED)
        card(draw, (1370, 360, 1770, 760), fill=NAVY2, outline=TEAL, radius=40, width=3)
        icon(draw, "spark", (1570, 500), 150, YELLOW)
        draw.text((1570, 655), "ATHENA × LAMEX", font=font(25, "bold"), fill=CREAM, anchor="mm")
        draw.text((1450, 820), "Parcelles Assainies · Dakar", font=font(22), fill=MUTED)


SCENE_DRAWERS = [
    [lambda d: scene_01(d, 0), lambda d: scene_01(d, 1)],
    [lambda d: scene_02(d, 0), lambda d: scene_02(d, 1)],
    [lambda d: scene_03(d, 0), lambda d: scene_03(d, 1), lambda d: scene_03(d, 2)],
    [lambda d: scene_04(d, 0), lambda d: scene_04(d, 1)],
    [lambda d: scene_05(d, 0), lambda d: scene_05(d, 1), lambda d: scene_05(d, 2)],
    [lambda d: scene_06(d, 0), lambda d: scene_06(d, 1), lambda d: scene_06(d, 2)],
    [lambda d: scene_07(d, 0), lambda d: scene_07(d, 1), lambda d: scene_07(d, 2)],
    [lambda d: scene_08(d, 0), lambda d: scene_08(d, 1), lambda d: scene_08(d, 2)],
    [lambda d: scene_09(d, 0), lambda d: scene_09(d, 1)],
    [lambda d: scene_10(d, 0), lambda d: scene_10(d, 1)],
]


def make_slide(chapter_index: int, state_index: int, progress: float, path: Path) -> None:
    im = make_background(chapter_index + 1, progress)
    d = ImageDraw.Draw(im)
    SCENE_DRAWERS[chapter_index][state_index](d)
    im.save(path, format="PNG", optimize=True)


def render_chapter(chapter_index: int, chapter: dict, progress: float) -> Path:
    chapter_no = chapter_index + 1
    slides: list[Path] = []
    states = SCENE_DRAWERS[chapter_index]
    for state_index in range(len(states)):
        img = TEMP / f"scene-{chapter_no:02d}-{state_index + 1:02d}.png"
        make_slide(chapter_index, state_index, progress, img)
        slides.append(img)

    n = len(slides)
    target_frames = int(chapter["duration"] * FPS)
    raw_frames = target_frames + XFADE_FRAMES * (n - 1)
    base_frames, extra = divmod(raw_frames, n)
    frame_counts = [base_frames + (1 if i < extra else 0) for i in range(n)]
    durations = [frames / FPS for frames in frame_counts]

    args: list[str] = []
    for slide, dur in zip(slides, durations):
        args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.6f}", "-i", str(slide)]

    filters: list[str] = []
    for i, dur in enumerate(durations):
        filters.append(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:flags=lanczos,"
            f"zoompan=z='min(1+on*0.000035,1.035)':"
            f"x='iw/2-(iw/zoom/2)+sin(on/135)*3':"
            f"y='ih/2-(ih/zoom/2)+sin(on/170)*2':"
            f"d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
            f"fps={FPS},trim=duration={dur:.6f},format=yuv420p[v{i}]"
        )
    current = "v0"
    accumulated = durations[0]
    for i in range(1, n):
        offset = accumulated - XFADE
        out = f"x{i}"
        filters.append(f"[{current}][v{i}]xfade=transition=fadeblack:duration={XFADE:.6f}:offset={offset:.6f}[{out}]")
        current = out
        accumulated += durations[i] - XFADE

    final_filters = [f"[{current}]trim=duration={chapter['duration']}"]
    if chapter_index == 0:
        final_filters.append("fade=t=in:st=0:d=0.8")
    if chapter_index == len(CHAPTERS) - 1:
        final_filters.append(f"fade=t=out:st={chapter['duration'] - 0.8}:d=0.8")
    filters.append(",".join(final_filters) + "[vout]")

    output = TEMP / f"chapter-{chapter_no:02d}.mp4"
    args += [
        "-filter_complex", ";".join(filters), "-map", "[vout]", "-an",
        "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-movflags", "+faststart", str(output),
    ]
    print(f"Rendering chapter {chapter_no:02d}/10 · {chapter['title']} · {chapter['duration']} s", flush=True)
    ffmpeg_run(args)
    return output


def split_caption_text(text: str, max_words: int = 11, max_chars: int = 84) -> list[str]:
    # Keep punctuation with its phrase and avoid a one-word orphan at a caption boundary.
    sentences = re.split(r"(?<=[.!?;:])\s+", text.strip())
    chunks: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        start = 0
        while start < len(words):
            remaining = len(words) - start
            take = min(max_words, remaining)
            if remaining > max_words and 0 < remaining - take < 4:
                take -= 4 - (remaining - take)
            while take > 5 and len(" ".join(words[start:start + take])) > max_chars:
                take -= 1
            if remaining > take and 0 < remaining - take < 4:
                take -= 4 - (remaining - take)
            take = max(1, take)
            chunks.append(" ".join(words[start:start + take]))
            start += take
    return chunks


def srt_time(seconds: float) -> str:
    ms = max(0, round(seconds * 1000))
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, milli = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milli:03d}"


def make_srt() -> None:
    entries: list[str] = []
    offset = 0.0
    number = 1
    for idx, ch in enumerate(CHAPTERS):
        chunks = split_caption_text(ch["text"])
        audio_path = AUDIO_DIR / f"{ch['id']}-{audio_slug(idx)}.mp3"
        source_duration = media_duration(audio_path)
        speech_duration = min(source_duration / SPEED - 0.25, ch["duration"] - 0.2)
        weights = [max(1, len(re.sub(r"\W", "", item))) for item in chunks]
        total_weight = sum(weights)
        t = offset
        for item, weight in zip(chunks, weights):
            duration = speech_duration * weight / total_weight
            start = t
            end = t + duration
            lines = textwrap.wrap(item, width=46, break_long_words=False, break_on_hyphens=False)
            if len(lines) > 2:
                lines = [" ".join(lines[:2]), " ".join(lines[2:])]
            entries.append(f"{number}\n{srt_time(start)} --> {srt_time(end)}\n" + "\n".join(lines))
            number += 1
            t = end
        offset += ch["duration"]
    SRT.write_text("\n\n".join(entries) + "\n", encoding="utf-8")


def audio_slug(index: int) -> str:
    return ["accroche", "presentation", "definition", "exemples", "generative", "boutique", "bonnes-consignes", "limites", "exercice", "conclusion"][index]


def media_duration(path: Path) -> float:
    result = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path), "-f", "null", "-"],
                            text=True, capture_output=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read duration for {path}: {result.stderr[-1000:]}")
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def build_voice_track(output: Path) -> None:
    args: list[str] = []
    for idx, ch in enumerate(CHAPTERS):
        path = AUDIO_DIR / f"{ch['id']}-{audio_slug(idx)}.mp3"
        if not path.exists():
            raise FileNotFoundError(f"Missing narration clip: {path}")
        args += ["-i", str(path)]
    filters: list[str] = []
    for idx, ch in enumerate(CHAPTERS):
        filters.append(
            f"[{idx}:a]atempo={SPEED},aresample=48000,"
            f"apad,atrim=duration={ch['duration']},asetpts=PTS-STARTPTS[a{idx}]"
        )
    concat_inputs = "".join(f"[a{i}]" for i in range(len(CHAPTERS)))
    filters.append(f"{concat_inputs}concat=n={len(CHAPTERS)}:v=0:a=1,"
                   f"afade=t=in:st=0:d=0.35,"
                   f"afade=t=out:st={TOTAL_SECONDS - 1.2}:d=1.2,"
                   f"loudnorm=I=-18:TP=-1.5:LRA=7[voice]")
    args += ["-filter_complex", ";".join(filters), "-map", "[voice]", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(output)]
    print("Building the French narration track", flush=True)
    ffmpeg_run(args)


def main() -> None:
    TEMP.mkdir(parents=True, exist_ok=True)
    EXPORTS.mkdir(parents=True, exist_ok=True)
    total = TOTAL_SECONDS
    if total != 530:
        print(f"Note: timeline totals {total} seconds.", flush=True)

    chapter_videos: list[Path] = []
    offset = 0
    for idx, chapter in enumerate(CHAPTERS):
        chapter_videos.append(render_chapter(idx, chapter, offset / total))
        offset += chapter["duration"]

    concat_list = TEMP / "chapters.txt"
    concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in chapter_videos), encoding="utf-8")
    silent_video = TEMP / "silent-video.mp4"
    ffmpeg_run(["-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", "-movflags", "+faststart", str(silent_video)])

    voice = TEMP / "voiceover.m4a"
    build_voice_track(voice)
    make_srt()

    # Burn French captions into the final file.  The sidecar SRT is also kept in production/.
    subtitle_path = SRT.as_posix().replace("\\", "/").replace(":", r"\:")
    style = "FontName=DejaVu Sans,Fontsize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&HAA081827,BackColour=&H99081727,BorderStyle=3,Outline=0.5,Shadow=0,Alignment=2,MarginL=110,MarginR=110,MarginV=25,WrapStyle=2"
    vf = f"subtitles=filename='{subtitle_path}':force_style='{style}'"
    ffmpeg_run([
        "-i", str(silent_video), "-i", str(voice),
        "-vf", vf, "-map", "0:v:0", "-map", "1:a:0",
        "-t", str(TOTAL_SECONDS), "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k",
        "-ar", "48000", "-movflags", "+faststart", str(OUTPUT),
    ])
    print(f"\nExported: {OUTPUT}", flush=True)
    print(f"Duration: {TOTAL_SECONDS // 60}:{TOTAL_SECONDS % 60:02d} · 1920×1080 · {FPS} fps", flush=True)
    print(f"Size: {OUTPUT.stat().st_size / (1024 * 1024):.1f} MB", flush=True)


if __name__ == "__main__":
    main()
