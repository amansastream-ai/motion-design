"""
Générique LAMEX TV — rendu procédural (Python + Pillow + NumPy) encodé en MP4 via ffmpeg.

Durée : 10 s — 1920x1080 — 30 fps
Timeline :
  0.0 - 0.6 s   fondu depuis le noir, particules et rayons apparaissent
  0.3 - 1.6 s   le médaillon LAMEX TV arrive (zoom avec léger rebond)
  0.8 - 1.9 s   un anneau de lumière se dessine autour du logo
  1.3 - 2.2 s   flare horizontal au moment où le logo se pose
  2.2 - 3.2 s   premier reflet lumineux qui traverse le logo
  3.2 - 8.4 s   respiration douce du logo, rayons qui tournent, particules
  6.2 - 7.2 s   second reflet lumineux
  8.4 - 9.4 s   sortie : le logo s'estompe et grossit légèrement
  9.3 - 10 s    fondu vers le noir

Usage : python3 render_generique.py [chemin_logo] [chemin_sortie.mp4]
"""
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

W, H = 1920, 1080
FPS = 30
DUR = 10.0
N = int(FPS * DUR)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOGO_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets" / "logo" / "bon.png"
OUT_PATH = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "output" / "lamex-tv-generique.mp4"

LOGO_SIZE = 680          # taille d'affichage de base du médaillon (px)
GOLD = np.array([255, 214, 120], np.float32)
WHITE_GOLD = np.array([255, 238, 190], np.float32)


# ---------- utilitaires d'animation ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, a, b):
    return clamp((t - a) / (b - a))


def ease_io(x):
    return x * x * (3 - 2 * x)


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_out_back(x, s=1.5):
    c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2


def bump(t, a, b):
    p = prog(t, a, b)
    return math.sin(math.pi * p) if 0 < p < 1 else 0.0


# ---------- fond précalculé ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
CX, CY = W / 2, H / 2
RN = np.sqrt(((xx - CX) / (W / 2)) ** 2 + ((yy - CY) / (H / 2)) ** 2).astype(np.float32)
THETA = np.arctan2(yy - CY, xx - CX).astype(np.float32)

top = np.array([16, 22, 40], np.float32)
bot = np.array([2, 4, 9], np.float32)
g = (yy / H)[..., None]
BASE = top * (1 - g) + bot * g
BASE = BASE + np.exp(-(RN ** 2) / 0.30)[..., None] * np.array([46, 38, 24], np.float32)
BASE = BASE.astype(np.float32)

RAYS_BASE = (np.maximum(0, np.cos(THETA * 14)) ** 8 * np.exp(-(RN ** 2) / 0.9)).astype(np.float32)

# ---------- particules ----------
rng = random.Random(7)
PARTICLES = []
for _ in range(90):
    PARTICLES.append(dict(
        x=rng.random(), y=rng.random(), z=rng.uniform(0.3, 1.0),
        speed=rng.uniform(0.012, 0.035), phase=rng.uniform(0, math.tau),
        tw=rng.uniform(0.8, 2.2),
    ))

# ---------- logo ----------
logo_img = Image.open(LOGO_PATH).convert("RGBA")
LOGO_NATIVE = logo_img.size[0]
# carré garanti
side = max(logo_img.size)
if logo_img.size[0] != logo_img.size[1]:
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(logo_img, ((side - logo_img.size[0]) // 2, (side - logo_img.size[1]) // 2))
    logo_img = sq

# halo doré précalculé à partir du contour alpha du logo
halo_alpha = logo_img.split()[3].resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
halo_alpha_arr = np.asarray(halo_alpha, np.float32) / 255.0 * 1.25


def paste_over(dst, src_rgb, src_a, x0, y0, opacity=1.0):
    h, w = src_a.shape
    x1, y1 = max(0, x0), max(0, y0)
    x2, y2 = min(W, x0 + w), min(H, y0 + h)
    if x1 >= x2 or y1 >= y2 or opacity <= 0:
        return
    sa = (src_a[y1 - y0:y2 - y0, x1 - x0:x2 - x0] * opacity)[..., None]
    sc = src_rgb[y1 - y0:y2 - y0, x1 - x0:x2 - x0]
    d = dst[y1:y2, x1:x2]
    dst[y1:y2, x1:x2] = sc * sa + d * (1 - sa)


def add_light(dst, color, alpha, x0, y0):
    h, w = alpha.shape
    x1, y1 = max(0, x0), max(0, y0)
    x2, y2 = min(W, x0 + w), min(H, y0 + h)
    if x1 >= x2 or y1 >= y2:
        return
    a = alpha[y1 - y0:y2 - y0, x1 - x0:x2 - x0][..., None]
    dst[y1:y2, x1:x2] += color * a


# ---------- rendu d'une image ----------
def render_frame(t):
    frame = BASE.copy()

    # fondu d'entrée / sortie global
    fade_in = ease_io(prog(t, 0.0, 0.6))
    fade_out = 1 - ease_io(prog(t, 9.3, 10.0))
    global_fade = fade_in * fade_out

    # rayons tournants derrière le logo
    ray_op = prog(t, 0.2, 1.5) * (1 - prog(t, 8.4, 9.4))
    if ray_op > 0:
        phase = t * 0.35
        rays = (np.maximum(0, np.cos(THETA * 14 - phase)) ** 8) * np.exp(-(RN ** 2) / 0.9)
        frame += (rays * 14.0 * ray_op)[..., None] * WHITE_GOLD / 255.0

    # particules
    for p in PARTICLES:
        y = (p["y"] - p["speed"] * t * 30 * p["z"] * 0.25) % 1.0
        x = p["x"] + 0.012 * math.sin(t * 0.8 + p["phase"]) * p["z"]
        px, py = x * W, y * H
        r = 1.2 + 2.2 * p["z"]
        tw = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * p["tw"] + p["phase"]))
        intensity = tw * p["z"] * 0.9 * global_fade * (1 - prog(t, 8.8, 9.5))
        if intensity <= 0.01:
            continue
        rad = int(r * 3)
        x0, y0 = int(px) - rad, int(py) - rad
        ys, xs = np.mgrid[0:2 * rad + 1, 0:2 * rad + 1].astype(np.float32)
        d2 = (xs - rad) ** 2 + (ys - rad) ** 2
        kern = np.exp(-d2 / (2 * r * r)) * intensity
        add_light(frame, WHITE_GOLD, kern, x0, y0)

    # logo
    scale_in = ease_out_back(prog(t, 0.35, 1.6), 1.2)
    logo_op = ease_out_cubic(prog(t, 0.35, 1.0))
    breathe = 1 + 0.012 * math.sin(t * 1.2) * prog(t, 2.5, 3.0)
    exit_k = ease_io(prog(t, 8.4, 9.4))
    scale = (0.6 + 0.4 * scale_in) * breathe * (1 + 0.07 * exit_k)
    opacity = logo_op * (1 - exit_k)
    S = max(8, int(round(LOGO_SIZE * scale)))

    if opacity > 0.001:
        # halo doré pulsant
        halo_op = (0.22 + 0.18 * bump(t, 1.2, 2.4)) * logo_op * (1 - exit_k) * global_fade
        hsz = max(8, int(round(LOGO_SIZE * scale)))
        ha = np.asarray(Image.fromarray((halo_alpha_arr * 255).astype(np.uint8)).resize((hsz, hsz), Image.BILINEAR), np.float32) / 255.0
        add_light(frame, GOLD, ha * halo_op, int(CX - hsz / 2), int(CY - hsz / 2))

        # disque blanc de fond (comme le logo d'origine), anti-aliasé
        dy_, dx_ = np.mgrid[0:S, 0:S].astype(np.float32)
        rr = np.sqrt((dx_ - (S - 1) / 2) ** 2 + (dy_ - (S - 1) / 2) ** 2)
        disc_a = np.clip(S / 2 * 0.995 - rr + 0.5, 0, 1).astype(np.float32)
        disc_rgb = np.full((S, S, 3), 250.0, np.float32)
        paste_over(frame, disc_rgb, disc_a, int(round(CX - S / 2)), int(round(CY - S / 2)), opacity * global_fade)

        # logo redimensionné
        lg = logo_img.resize((S, S), Image.LANCZOS)
        arr = np.asarray(lg, np.float32)
        rgb = arr[..., :3].copy()
        alpha = arr[..., 3] / 255.0

        # reflets lumineux diagonaux
        ys_l, xs_l = np.mgrid[0:S, 0:S].astype(np.float32)
        u = (xs_l + ys_l) / (2 * S)
        for a, b in ((2.2, 3.2), (6.2, 7.2)):
            if a <= t <= b:
                c = -0.25 + 1.5 * ease_io(prog(t, a, b))
                band = np.exp(-((u - c) / 0.035) ** 2) * alpha
                rgb = np.clip(rgb + band[..., None] * 230.0, 0, 255)

        x0 = int(round(CX - S / 2))
        y0 = int(round(CY - S / 2))
        paste_over(frame, rgb, alpha, x0, y0, opacity * global_fade)

        # anneau de lumière qui se dessine
        ring_p = ease_io(prog(t, 0.8, 1.9))
        ring_fade = 1 - ease_io(prog(t, 8.4, 9.2))
        if ring_p > 0 and ring_fade > 0:
            R = S / 2 + 9
            box = int(R + 12)
            ys_r, xs_r = np.mgrid[-box:box + 1, -box:box + 1].astype(np.float32)
            dist = np.sqrt(xs_r ** 2 + ys_r ** 2)
            ring_w = 2.5
            ring_mask = np.clip(ring_w / 2 + 0.7 - np.abs(dist - R), 0, 1)
            ang = (np.arctan2(ys_r, xs_r) + math.pi / 2) % math.tau
            ring_mask *= (ang <= ring_p * math.tau).astype(np.float32)
            ring_mask *= 0.9 * ring_fade * global_fade
            add_light(frame, WHITE_GOLD, ring_mask, int(round(CX)) - box, int(round(CY)) - box)

    # flare horizontal au posé du logo
    flare_k = bump(t, 1.3, 2.4) * (1 - exit_k) * global_fade
    if flare_k > 0.001:
        vert = np.exp(-((yy - CY) / 3.0) ** 2)
        horiz = np.exp(-((xx - CX) / (W * 0.32)) ** 2)
        frame += (vert * horiz * 160 * flare_k)[..., None] * WHITE_GOLD / 255.0

    # fondu final vers le noir
    frame *= global_fade
    return np.clip(frame, 0, 255).astype(np.uint8)


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOGO_PATH.exists():
        sys.exit(f"Logo introuvable : {LOGO_PATH}")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUT_PATH),
    ]
    ffmpeg_bin = FFMPEG_BIN
    cmd[0] = ffmpeg_bin
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        t = i / FPS
        frame = render_frame(t)
        proc.stdin.write(frame.tobytes())
        if i % 30 == 0:
            print(f"frame {i}/{N}", flush=True)
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        sys.exit("ffmpeg a échoué")
    print(f"OK -> {OUT_PATH}")


def _find_ffmpeg():
    import shutil
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("ffmpeg introuvable")


FFMPEG_BIN = _find_ffmpeg()

if __name__ == "__main__":
    main()
