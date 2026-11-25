"""Audio teaser 30 s « TAS : le Sénégal conserve son titre 2025 » (48 kHz mono).
VO = ta-1 (13,1 s) dès 0,15 s · whoosh transitions · bed labels 13,5->30 ·
impact + stinger à 24 s (endcard).
Run: pytools/bin/python tools/ta_teaser_audio.py
"""
import os
import sys
import numpy as np
import imageio_ffmpeg
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
DUR = 30.0


def load_mp3(path):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1',
                          '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def sine_bed(dur, freqs, amp=0.08, attack=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, a in zip(freqs, [1.0, 0.55, 0.35, 0.22]):
        out += (a * np.sin(2 * np.pi * f * t)).astype(np.float32)
    env = np.ones(n, np.float32)
    na = int(attack * SR)
    if na:
        env[:na] *= np.linspace(0, 1, na)
    env *= (1 - 0.4 * t / max(dur, 0.01))
    return out / max(1e-6, np.max(np.abs(out))) * amp * env


def whoosh(dur=0.7, amp=0.13, reverse=False):
    n = int(dur * SR)
    rng = np.random.RandomState(5)
    noise = rng.randn(n).astype(np.float32)
    t = np.arange(n) / SR
    lfo = np.sin(2 * np.pi * 2.2 * t) * 0.5 + 0.5
    s = noise * (0.4 + 0.6 * lfo)
    env = np.linspace(0, 1, n) ** 2.2 if reverse else np.linspace(1, 0, n) ** 1.6
    return (s * env).astype(np.float32) * amp


def impact(amp=0.26):
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    f = 82 * np.exp(-t * 2.2)
    ph = np.cumsum(2 * np.pi * f / SR)
    body = np.sin(ph) * np.exp(-t * 2.6)
    rng = np.random.RandomState(9)
    click = rng.randn(n).astype(np.float32) * np.exp(-t * 26) * 0.4
    out = (body + click).astype(np.float32)
    return out / max(1e-6, np.max(np.abs(out))) * amp


def stinger(dur=2.9, amp=0.17):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, a, dcy in [(196, 1.0, 0.9), (294, 0.6, 1.1), (392, 0.42, 1.3), (588, 0.25, 1.6)]:
        out += (a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy)).astype(np.float32)
    return out / max(1e-6, np.max(np.abs(out))) * amp


def main():
    n = int(DUR * SR)
    master = np.zeros(n + SR * 3, np.float32)

    def put(sig, t0):
        i0 = int(t0 * SR)
        master[i0:i0 + len(sig)] += sig[:len(master) - i0]

    vo = load_mp3(os.path.join(ROOT, 'audio', 'ta-1.mp3'))
    put(vo, 0.15)

    for tw in (4.5, 9.0, 13.5, 19.0, 24.0):
        put(whoosh(0.7, amp=0.12), tw - 0.22)
        put(whoosh(0.55, amp=0.10, reverse=True), tw)

    put(sine_bed(16.5, [110, 165, 220], amp=0.075, attack=1.1), 13.5)
    put(impact(0.25), 24.0)
    put(stinger(2.9), 24.1)

    master = master[:n]
    master = np.tanh(master * 1.2) * 0.92
    pcm = (master * 32767).astype(np.int16)
    import wave as wavmod
    outp = os.path.join(ROOT, 'audio', 'ta-teaser-master.wav')
    with wavmod.open(outp, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', outp, f'{DUR:.2f}s')


if __name__ == '__main__':
    main()
