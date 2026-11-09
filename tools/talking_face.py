# -*- coding: utf-8 -*-
"""Animateur de presentatrice - SNGAL INFOS.

Portrait + textures de bouche (ferme/mi-ouverte/ouverte) + audio ->
video de parlant avec VRAIE synchronisation levres (modele de visemes MIT).

Technique : mel/TCN audio->visemes (tools/viseme_engine.py) -> parametres
continus (open/pucker/wide/press/ff) -> melange de textures labiales + champ
de deformation RBF (machoire, levres, clignements, balancement de tete).

Usage :
  pytools/bin/python tools/talking_face.py --audio audio/anchor-intro.mp4 \
      --out audio/anchor-intro-talking.mp4 --seconds 14.81
"""
import argparse
import os
import sys

import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viseme_engine import VisemeEngine, load_audio_16k  # noqa: E402

BASE_PORTRAIT = "assets/presenter/anchor-portrait.jpg"
TEX_MID = "assets/presenter/anchor-mouth-mid.jpg"
TEX_OPEN = "assets/presenter/anchor-mouth-open.jpg"

OUTER_LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409,
              270, 269, 267, 0, 37, 39, 40, 185]
INNER_LIPS = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324,
              318, 402, 317, 14, 87, 178, 88, 95]
UPPER_OUT = [37, 0, 267]
LOWER_OUT = [84, 17, 314]
UPPER_IN = [82, 13, 312]
LOWER_IN = [87, 14, 317]
CORNERS = [61, 291]
CHIN = [152]
JAW = [172, 136, 150, 149, 176, 148, 152, 377, 378, 400, 379, 365, 397, 288, 361]
NOSE = [1, 4, 5, 168, 195, 197, 55, 275]
LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 246, 388, 387, 386, 385, 384, 398]
L_EYE_TOP = [247, 159, 158, 157, 173, 133]
L_EYE_BOT = [7, 163, 144, 145, 153, 154, 155]
R_EYE_TOP = [463, 386, 385, 384, 398, 362]
R_EYE_BOT = [382, 381, 380, 374, 373, 374, 380, 381, 382]


def get_landmarks(img_bgr):
    import mediapipe as mp
    h, w = img_bgr.shape[:2]
    with mp.solutions.face_mesh.FaceMesh(static_image_mode=True, refine_landmarks=True,
                                         max_num_faces=1, min_detection_confidence=0.5) as fm:
        res = fm.process(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    if not res.multi_face_landmarks:
        raise RuntimeError("Aucun visage detecte")
    lms = np.array([[p.x * w, p.y * h] for p in res.multi_face_landmarks[0].landmark],
                   dtype=np.float32)
    return lms


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


class TalkingFace:
    def __init__(self, portrait=BASE_PORTRAIT, tex_mid=TEX_MID, tex_open=TEX_OPEN,
                 seed=42):
        self.base = cv2.imread(portrait)
        self.lm = get_landmarks(self.base)
        self.h, self.w = self.base.shape[:2]
        self.rng = np.random.default_rng(seed)

        # geometrie de reference
        self.mouth_c = self.lm[OUTER_LIPS].mean(axis=0)
        self.mw = float(np.linalg.norm(self.lm[291] - self.lm[61]))
        self.mh0 = 0.36 * self.mw          # hauteur d'ouverture max (px)
        self.eye_h = 0.22 * self.mw        # hauteur d'oeil ref (px)

        # texture alignees + masques
        self.tex_mid = self._align_texture(cv2.imread(tex_mid))
        self.tex_open = self._align_texture(cv2.imread(tex_open))
        self._build_masks()

        # grille deformation
        ys, xs = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.gx, self.gy = xs, ys
        self._build_rbf()

        # calendrier de clignements
        self._schedule_blinks()

    # ---------- textures ----------
    def _align_texture(self, tex):
        lm_t = get_landmarks(tex)
        idx = [1, 33, 263, 61, 291, 13, 14, 152]
        src = lm_t[idx]
        dst = self.lm[idx]
        M, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)
        aligned = cv2.warpAffine(tex, M, (self.w, self.h),
                                 flags=cv2.INTER_LANCZOS4,
                                 borderMode=cv2.BORDER_REPLICATE)
        return self._harmonize(aligned)

    def _harmonize(self, tex):
        """Ajuste la couleur de la texture sur le portrait (LAB, zone bouche)."""
        mask = np.zeros((self.h, self.w), np.uint8)
        pts = np.round(self.lm[OUTER_LIPS]).astype(np.int32)
        cv2.fillConvexPoly(mask, cv2.convexHull(pts), 255)
        mask = cv2.dilate(mask, np.ones((9, 9), np.uint8))
        sel = mask > 0
        lab_b = cv2.cvtColor(self.base, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab_t = cv2.cvtColor(tex, cv2.COLOR_BGR2LAB).astype(np.float32)
        for c in range(3):
            mb, sb = lab_b[:, :, c][sel].mean(), lab_b[:, :, c][sel].std() + 1e-3
            mt, st = lab_t[:, :, c][sel].mean(), lab_t[:, :, c][sel].std() + 1e-3
            lab_t[:, :, c] = (lab_t[:, :, c] - mt) / st * sb + mb
        return cv2.cvtColor(np.clip(lab_t, 0, 255).astype(np.uint8),
                            cv2.COLOR_LAB2BGR)

    def _build_masks(self):
        pts = np.round(self.lm[OUTER_LIPS]).astype(np.int32)
        m = np.zeros((self.h, self.w), np.uint8)
        cv2.fillConvexPoly(m, cv2.convexHull(pts), 255)
        r = max(6, int(0.10 * self.mw))
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r, 2 * r)))
        self.lip_mask = cv2.GaussianBlur(m.astype(np.float32) / 255.0,
                                         (0, 0), 0.055 * self.mw)[..., None]
        # emprise bouche (bbox) pour le melange rapide
        x0, y0 = self.lm[OUTER_LIPS].min(axis=0) - 1.3 * self.mw
        x1, y1 = self.lm[OUTER_LIPS].max(axis=0) + 1.3 * self.mw
        self.mroi = (max(0, int(x0)), max(0, int(y0)),
                     min(self.w, int(x1)), min(self.h, int(y1)))

    # ---------- RBF ----------
    def _splat_field(self, anchors_idx, deltas, sigma):
        """Diffuse les deltas des ancres -> champ (h, w, 2) via flou gaussien."""
        num = np.zeros((self.h, self.w, 2), np.float32)
        den = np.zeros((self.h, self.w, 1), np.float32)
        for i, d in zip(anchors_idx, deltas):
            x, y = self.lm[i]
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < self.w and 0 <= yi < self.h:
                num[yi, xi] += d
                den[yi, xi, 0] += 1.0
        num = cv2.GaussianBlur(num, (0, 0), sigma)
        den = cv2.GaussianBlur(den, (0, 0), sigma).reshape(self.h, self.w, 1)
        return num / (den + 1e-4)

    def _build_rbf(self):
        self.sigma_mouth = 0.16 * self.mw
        self.sigma_eye = 0.10 * self.mw
        # ancres rigides (delta nul) : nez + front-bas pour tenir le haut du visage
        self.rigid = NOSE + [10, 151, 67, 103, 332, 297, 389, 251]
        # bouche : levres + menton + machoire
        self.mouth_anchors = (OUTER_LIPS + INNER_LIPS + UPPER_OUT + LOWER_OUT +
                              UPPER_IN + LOWER_IN + CORNERS + CHIN + JAW)
        self.eye_anchors = (L_EYE_TOP + L_EYE_BOT + R_EYE_TOP + R_EYE_BOT)

    def _mouth_deltas(self, o, p, wd, pr, ff, atten):
        d = {}
        s = self.mh0
        cx, cy = self.mouth_c
        for i in UPPER_OUT + UPPER_IN:
            dx, dy = 0.0, -o * (0.16 if i in UPPER_OUT else 0.12) * s * atten
            dy += pr * 0.05 * s
            dy += -wd * 0.03 * s
            d[i] = np.array([dx, dy], np.float32)
        for i in LOWER_OUT + LOWER_IN:
            dx, dy = 0.0, o * (0.62 if i in LOWER_OUT else 0.52) * s * atten
            dy -= ff * 0.13 * s
            dy -= pr * 0.04 * s
            d[i] = np.array([dx, dy], np.float32)
        for i in CORNERS:
            sign = 1.0 if self.lm[i][0] > cx else -1.0
            dx = sign * (wd * 0.10 - p * 0.17) * self.mw
            dy = o * 0.05 * s * atten + p * 0.02 * s
            d[i] = np.array([dx, dy], np.float32)
        # pucker : resserrement horizontal general des levres
        for i in OUTER_LIPS + INNER_LIPS:
            lx, ly = self.lm[i]
            v = d.get(i, np.zeros(2, np.float32)).copy()
            v[0] += (cx - lx) / self.mw * p * 0.13 * self.mw
            v[1] += (cy - ly) / self.mw * p * 0.05 * self.mw
            d[i] = v
        # machoire / menton : toujours (pas d'attenuation texture)
        d[152] = d.get(152, np.zeros(2, np.float32)) + np.array([0, o * 0.30 * s], np.float32)
        for i in JAW:
            if i == 152:
                continue
            v = d.get(i, np.zeros(2, np.float32)).copy()
            v[1] += o * 0.20 * s
            d[i] = v
        return d

    def _eye_deltas(self, blink):
        d = {}
        drop = blink * 0.78 * self.eye_h
        lift = blink * 0.15 * self.eye_h
        for i in L_EYE_TOP + R_EYE_TOP:
            d[i] = np.array([0, drop], np.float32)
        for i in L_EYE_BOT + R_EYE_BOT:
            d[i] = np.array([0, -lift], np.float32)
        return d

    # ---------- clignements / balancement ----------
    def _schedule_blinks(self):
        t, marks = 0.6, []
        while t < 200:
            marks.append(t)
            t += float(self.rng.uniform(2.6, 5.6))
        self.blinks = marks

    def _blink_at(self, t):
        for b in self.blinks:
            if b - 0.02 <= t < b + 0.16:
                u = (t - b)
                if u < 0.06:
                    return smoothstep(u / 0.06)
                return 1.0 - smoothstep((u - 0.06) / 0.10)
        return 0.0

    def _sway(self, t, energy):
        e = 0.55 + 0.45 * energy
        theta = np.deg2rad(0.42 * np.sin(2 * np.pi * t / 7.3 + 1.2) * e)
        tx = 3.0 * np.sin(2 * np.pi * t / 9.1 + 0.4) * e
        ty = 2.2 * np.sin(2 * np.pi * t / 6.4 + 2.1) * e
        z = 1.0 + 0.0045 * np.sin(2 * np.pi * t / 11.3 + 0.8)
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s], [s, c]], np.float32) * z
        return R, tx, ty

    # ---------- rendu ----------
    def render(self, audio_path, out_path, seconds=None, fps=25, crf=17):
        import imageio_ffmpeg
        from viseme_engine import load_model  # noqa: F401

        audio = load_audio_16k(audio_path)
        if seconds is not None:
            n = int(round(seconds * 16000))
            if len(audio) < n:
                audio = np.concatenate([audio, np.zeros(n - len(audio), np.float32)])
            else:
                audio = audio[:n]

        eng = VisemeEngine()
        prm = eng.params(audio, fps=fps)
        n_frames = len(prm["open"])
        if seconds is not None:
            n_frames = int(round(seconds * fps))
            for k in prm:
                if len(prm[k]) < n_frames:
                    prm[k] = np.concatenate([prm[k], np.zeros(n_frames - len(prm[k]), np.float32)])
                else:
                    prm[k] = prm[k][:n_frames]

        writer = imageio_ffmpeg.write_frames(
            out_path, size=(self.w, self.h), fps=fps,
            quality=max(1, min(10, int(round((51 - crf) / 5.1)))),
            codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
            macro_block_size=1)
        writer.send(None)

        x0, y0, x1, y1 = self.mroi
        for f in range(n_frames):
            t = f / fps
            o = float(prm["open"][f])
            p = float(prm["pucker"][f])
            wd = float(prm["wide"][f])
            pr = float(prm["press"][f])
            ff = float(prm["ff"][f])
            energy = float(prm["speech"][f])

            # textures : poids continus
            open_eff = o * (1.0 - 0.55 * pr)
            w_o = smoothstep((open_eff - 0.42) / 0.34)
            w_m = smoothstep((open_eff - 0.14) / 0.30) * (1.0 - w_o)
            w_c = max(0.0, 1.0 - w_m - w_o)

            canvas = self.base.copy()
            if w_m + w_o > 0.003:
                mroi_mask = self.lip_mask[y0:y1, x0:x1]
                mix = (w_c * self.base[y0:y1, x0:x1] +
                       w_m * self.tex_mid[y0:y1, x0:x1] +
                       w_o * self.tex_open[y0:y1, x0:x1])
                canvas[y0:y1, x0:x1] = (
                    self.base[y0:y1, x0:x1] * (1 - mroi_mask) + mix * mroi_mask
                ).astype(np.uint8)

            # attenue la deformation des levres quand les textures portent l'ouverture
            atten = 1.0 - 0.70 * w_o - 0.40 * w_m
            mouth_d = self._mouth_deltas(o, p, wd, pr, ff, atten)
            blink = self._blink_at(t)
            eye_d = self._eye_deltas(blink)

            # champ de deformation : ancres rigides nulles + bouche (large),
            # puis yeux (serre) separement
            anchors = self.rigid + list(mouth_d.keys())
            deltas = ([np.zeros(2, np.float32)] * len(self.rigid) +
                      [mouth_d[i] for i in mouth_d])
            field = self._splat_field(anchors, deltas, self.sigma_mouth)
            fe = self._splat_field(list(eye_d.keys()), [eye_d[i] for i in eye_d],
                                   self.sigma_eye)

            # balancement global
            R, tx, ty = self._sway(t, energy)
            xc, yc = self.w / 2.0, self.h / 2.0
            gx = (R[0, 0] * (self.gx - xc) + R[0, 1] * (self.gy - yc) + xc + tx) - self.gx
            gy = (R[1, 0] * (self.gx - xc) + R[1, 1] * (self.gy - yc) + yc + ty) - self.gy

            map_x = np.ascontiguousarray(
                self.gx + gx + field[:, :, 0] + fe[:, :, 0], dtype=np.float32)
            map_y = np.ascontiguousarray(
                self.gy + gy + field[:, :, 1] + fe[:, :, 1], dtype=np.float32)

            frame = cv2.remap(canvas, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE)
            writer.send(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).tobytes())
            if f % 50 == 0:
                print(f"  frame {f}/{n_frames} open={o:.2f} pucker={p:.2f}", flush=True)
        writer.close()
        print(f"OK {out_path} ({n_frames} frames @ {fps} fps)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--crf", type=int, default=17)
    args = ap.parse_args()
    tf = TalkingFace()
    tf.render(args.audio, args.out, seconds=args.seconds, fps=args.fps, crf=args.crf)


if __name__ == "__main__":
    main()
