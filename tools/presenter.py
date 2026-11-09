"""Présentatrice à l'antenne — SNGAL INFOS (module réutilisable).

Technique « talking head » légère : 3 états de bouche (fermé / mi-ouvert / ouvert)
alignés sur le portrait de base, animés par l'enveloppe RMS de la voix.
Chaque état est recadré autour de SON PROPRE centre de bouche puis collé (masque
elliptique adouci) sur la base : les images ne diffèrent que dans la zone bouche,
le fondu entre états est donc sans fantôme.

Usage:
    face = AnchorFace()
    states = face.panel_states(panel_w, panel_h, cy=0.32)   # 3 images prêtes
    env = face.frame_states('audio/anchor-intro.mp3', fps, n_frames)
    img = face.blend_frame(states, env[i], zoom=0.02, t=t)
"""
import os
import subprocess
import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100

# centres de bouche estimés (fractions x, y) + demie-fenêtre de recadrage
BASE_MOUTH = (0.505, 0.345)
MID_MOUTH = (0.500, 0.357)
OPEN_MOUTH = (0.497, 0.360)
HALF_WIN = (0.155, 0.135)


class AnchorFace:
    def __init__(self, base='assets/presenter/anchor-portrait.jpg',
                 mid='assets/presenter/anchor-mouth-mid.jpg',
                 open_='assets/presenter/anchor-mouth-open.jpg'):
        self.base_img = Image.open(os.path.join(ROOT, base)).convert('RGB')
        self.states = self._build_states(
            os.path.join(ROOT, mid), os.path.join(ROOT, open_))

    def _mouth_window(self, img, mc):
        w, h = img.size
        cx, cy = mc[0] * w, mc[1] * h
        hw, hh = HALF_WIN[0] * w, HALF_WIN[1] * h
        return (int(cx - hw), int(cy - hh), int(cx + hw), int(cy + hh))

    def _feather(self, size):
        m = Image.new('L', size, 0)
        d = ImageDraw.Draw(m)
        w, h = size
        d.ellipse([int(w * 0.16), int(h * 0.16), int(w * 0.84), int(h * 0.84)], fill=255)
        return m.filter(ImageFilter.GaussianBlur(radius=max(8, w // 18)))

    def _paste_mouth(self, base_copy, variant_path, variant_mouth):
        var = Image.open(variant_path).convert('RGB')
        vb = self._mouth_window(var, variant_mouth)
        crop = var.crop(vb)
        bb = self._mouth_window(self.base_img, BASE_MOUTH)
        target_size = (bb[2] - bb[0], bb[3] - bb[1])
        crop = crop.resize(target_size, Image.LANCZOS)
        base_copy.paste(crop, (bb[0], bb[1]), self._feather(target_size))

    def _build_states(self, mid_path, open_path):
        s0 = self.base_img
        s1 = self.base_img.copy()
        self._paste_mouth(s1, mid_path, MID_MOUTH)
        s2 = self.base_img.copy()
        self._paste_mouth(s2, open_path, OPEN_MOUTH)
        return [s0, s1, s2]

    def panel_states(self, panel_w, panel_h, cy=0.30):
        """Les 3 états recadrés « portrait » pour un panneau de scène."""
        out = []
        for st in self.states:
            im = st.copy()
            sw, sh = im.size
            scale = max(panel_w / sw, panel_h / sh)
            nw, nh = int(sw * scale + 0.5), int(sh * scale + 0.5)
            im = im.resize((nw, nh), Image.LANCZOS)
            x = (nw - panel_w) // 2
            y = int((nh - panel_h) * cy)
            out.append(im.crop((x, y, x + panel_w, y + panel_h)))
        return out

    @staticmethod
    def frame_states(wav_path, fps, n_frames):
        """Enveloppe RMS par image → état flottant 0..2 (lissé, sans saut)."""
        import tempfile, wave as wavmod
        p = os.path.join(ROOT, wav_path) if not os.path.isabs(wav_path) else wav_path
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
            tw = tf.name
        subprocess.run([FFMPEG, '-y', '-i', p, '-ar', str(SR), '-ac', '1', tw],
                       capture_output=True, check=True)
        with wavmod.open(tw, 'rb') as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        os.unlink(tw)
        sig = data.astype(np.float32) / 32768.0
        spf = SR / fps
        env = np.zeros(n_frames)
        for i in range(n_frames):
            a, b = int(i * spf), int((i + 1) * spf)
            seg = sig[a:b] if b > a else sig[a:a + 1]
            env[i] = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
        ref = np.percentile(env[env > 0.01], 92) if np.any(env > 0.01) else 1.0
        env = np.clip(env / max(1e-6, ref), 0, 1.4)
        states = np.zeros(n_frames)
        cur = 0.0
        for i in range(n_frames):
            tgt = 2.0 if env[i] > 0.62 else (1.0 if env[i] > 0.28 else 0.0)
            cur += (tgt - cur) * 0.38
            states[i] = cur
        return states

    @staticmethod
    def blend_frame(states, s, zoom=0.0, bob=0.0):
        """Image composite pour l'état flottant s (0..2), zoom lent + respiration."""
        i0 = int(min(2, max(0, s)))
        i1 = min(2, i0 + 1)
        frac = float(np.clip(s - i0, 0, 1))
        img = Image.blend(states[i0], states[i1], frac) if frac > 0.001 else states[i0]
        if zoom > 0 or abs(bob) > 0.001:
            w, h = img.size
            z = 1.0 - zoom
            cw, ch = int(w * z), int(h * z)
            x = (w - cw) // 2
            y = int((h - ch) * 0.36 + bob * h)
            img = img.crop((x, y, x + cw, y + ch)).resize((w, h), Image.BILINEAR)
        return img
