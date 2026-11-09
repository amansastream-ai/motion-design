# -*- coding: utf-8 -*-
"""Moteur de visemes audio -> bouche (SNGAL INFOS).

Modèle TCN audio->visemes (MIT, InterviewFlowAI "viseme-model.bin") porté en
numpy : mel 80 (Hann 400 / hop 160 / nfft 512) puis TCN dilate residuel ReLU
(128 ch, k=3, dilations 1-2-4-8-16) -> 22 classes de visemes.

Entrees : wav/ mp3 (via ffmpeg) -> parametres de bouche continus par frame :
  open (ouverture machoire), pucker (arrondi), wide (elargi), press (levres
  pressees), ff (levre inferieure rentree - f/v).
"""
import json
import struct
import subprocess
import wave

import numpy as np

VOCAB = ["sil", "aa", "aa", "O", "E", "E", "I", "U", "O", "aa", "O", "aa",
         "kk", "RR", "nn", "SS", "CH", "TH", "FF", "DD", "kk", "PP"]

# Forme de bouche par viseme (open, pucker, wide, press, ff).
SHAPES = {
    "sil": (0.03, 0.05, 0.10, 0.00, 0.00),
    "PP":  (0.00, 0.06, 0.10, 0.90, 0.00),
    "FF":  (0.13, 0.04, 0.16, 0.25, 0.85),
    "TH":  (0.30, 0.02, 0.16, 0.00, 0.00),
    "DD":  (0.30, 0.02, 0.22, 0.00, 0.00),
    "kk":  (0.38, 0.02, 0.15, 0.00, 0.00),
    "CH":  (0.28, 0.48, 0.02, 0.00, 0.00),
    "SS":  (0.22, 0.12, 0.48, 0.00, 0.00),
    "nn":  (0.32, 0.02, 0.20, 0.00, 0.00),
    "RR":  (0.30, 0.38, 0.00, 0.00, 0.00),
    "aa":  (0.85, 0.05, 0.42, 0.00, 0.00),
    "E":   (0.55, 0.00, 0.55, 0.00, 0.00),
    "I":   (0.36, 0.00, 0.75, 0.00, 0.00),
    "O":   (0.62, 0.62, 0.00, 0.00, 0.00),
    "U":   (0.38, 0.95, 0.00, 0.00, 0.00),
}
SHAPE_KEYS = ("open", "pucker", "wide", "press", "ff")


def load_model(path):
    data = open(path, "rb").read()
    hlen = struct.unpack("<I", data[:4])[0]
    hdr = json.loads(data[4:4 + hlen].decode())
    raw = np.frombuffer(data[4 + hlen:], dtype=np.float32)
    tensors = {}
    for t in hdr["tensors"]:
        shape = tuple(t["shape"])
        n = int(np.prod(shape))
        tensors[t["name"]] = raw[t["offset"]:t["offset"] + n].reshape(shape).copy()
    hdr["tensors"] = tensors
    return hdr


def mel_filterbank(sr, nfft, n_mels, fmin, fmax):
    hz2mel = lambda f: 2595.0 * np.log10(1.0 + f / 700.0)
    mel2hz = lambda m: 700.0 * (10.0 ** (m / 2595.0) - 1.0)
    pts = mel2hz(np.linspace(hz2mel(fmin), hz2mel(fmax), n_mels + 2))
    bins = np.arange(nfft // 2 + 1) * sr / nfft
    fb = np.zeros((n_mels, nfft // 2 + 1), dtype=np.float32)
    for i in range(n_mels):
        lo, ctr, hi = pts[i], pts[i + 1], pts[i + 2]
        up = (bins - lo) / max(ctr - lo, 1e-9)
        dn = (hi - bins) / max(hi - ctr, 1e-9)
        fb[i] = np.maximum(0.0, np.minimum(up, dn))
    return fb


def _conv1(x, w, b):
    # x: (T, C) ; w: (O, C, 1) -> (T, O)
    return x @ w[:, :, 0].T + b


def _conv3_causal(x, w, b, dilation):
    # x: (T, C) ; w: (O, C, 3) dilate causal, taps [t-2d, t-d, t] -> (T, O)
    T = x.shape[0]
    out = np.tile(b.astype(np.float32), (T, 1))
    for v in range(3):
        shift = (2 - v) * dilation
        if shift == 0:
            xs = x
        elif shift >= T:
            continue
        else:
            xs = np.concatenate([np.zeros((shift, x.shape[1]), np.float32), x[:T - shift]])
        out += xs @ w[:, :, v].T
    return out


def _softmax(z, temp=0.65):
    z = z / temp
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def load_audio_16k(path):
    """Charge un fichier audio via ffmpeg -> float32 mono 16 kHz."""
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-v", "quiet", "-i", str(path), "-f", "s16le", "-ac", "1",
           "-ar", "16000", "pipe:1"]
    pcm = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


class VisemeEngine:
    def __init__(self, model_path="assets/models/viseme-model.bin"):
        self.m = load_model(model_path)
        self.fb = mel_filterbank(self.m["SR"], self.m["NFFT"], self.m["N_MELS"],
                                 self.m["FMIN"], self.m["FMAX"])
        self.win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(self.m["WIN"]) / self.m["WIN"])).astype(np.float32)

    def probs(self, audio16k):
        """(N,) float32 16 kHz -> (T, 22) probabilites softmax."""
        WIN, HOP, NFFT = self.m["WIN"], self.m["HOP"], self.m["NFFT"]
        pad = (HOP - (len(audio16k) - WIN) % HOP) % HOP
        x = np.concatenate([audio16k, np.zeros(WIN + pad, np.float32)])
        n_frames = (len(x) - WIN) // HOP + 1
        idx = np.arange(WIN)[None, :] + HOP * np.arange(n_frames)[:, None]
        frames = x[idx] * self.win[None, :]
        spec = np.fft.rfft(frames, NFFT, axis=1)
        power = (spec.real ** 2 + spec.imag ** 2).astype(np.float32)
        mel = np.log(power @ self.fb.T + self.m["LOG_FLOOR"])
        mel = (mel - self.m["tensors"]["mean"][None, :]) / self.m["tensors"]["std"][None, :]
        t = self.m["tensors"]
        h = _conv1(mel, t["inp.weight"], t["inp.bias"])
        for k, d in enumerate(self.m["dilations"]):
            f = _conv3_causal(h, t[f"blocks.{k}.weight"], t[f"blocks.{k}.bias"], d)
            h = h + np.maximum(0.0, f)
        logits = _conv1(h, t["out.weight"], t["out.bias"])
        return _softmax(logits.astype(np.float32))

    def params(self, audio16k, fps=25.0, smooth=0.10):
        """Probabilites -> parametres de bouche echantillonnes a fps.

        Retourne dict de tableaux (n_frames,) : open, pucker, wide, press, ff, speech.
        """
        p = self.probs(audio16k)                     # (T, 22) a 100 Hz
        n_frames = int(np.ceil(p.shape[0] * (self.m["HOP"] / self.m["SR"]) * fps))
        # parametres continus par framemodele 100 Hz
        acc = np.zeros((p.shape[0], len(SHAPE_KEYS)), np.float32)
        for c, name in enumerate(VOCAB):
            s = SHAPES[name]
            acc += p[:, c:c + 1] * np.asarray(s, np.float32)[None, :]
        speech = 1.0 - p[:, 0]                       # 1 - sil
        # reechantillonnage 100 Hz -> fps, lineaire
        t_src = np.arange(p.shape[0]) * (self.m["HOP"] / self.m["SR"])
        t_dst = (np.arange(n_frames) + 0.5) / fps
        out = {}
        for i, k in enumerate(SHAPE_KEYS):
            out[k] = np.interp(t_dst, t_src, acc[:, i]).astype(np.float32)
        out["speech"] = np.interp(t_dst, t_src, speech).astype(np.float32)
        # lissage exponentiel (coarticulation douce)
        a = float(np.exp(-1.0 / max(1.0, fps * smooth)))
        for k, v in out.items():
            y = np.empty_like(v)
            accv = v[0]
            for i in range(len(v)):
                accv = a * accv + (1 - a) * v[i]
                y[i] = accv
            out[k] = y
        return out
