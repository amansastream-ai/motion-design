"""Audio teaser 30 s « Séquestration présumée à Pikine » (master 48 kHz mono WAV).
VO = pk-1 intégrale (17,8 s) dès 0,15 s · whoosh transitions 6/12/17,9/23,5 ·
impact + stinger à 27 s · musique de plateau sur labels + endcard (17,9 -> 30).
Run: pytools/bin/python tools/pk_teaser_audio.py
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


def sine_bed(dur, freqs, amp=0.085, attack=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, a in zip(freqs, [1.0, 0.55, 0.35, 0.22]):
        out += (a * np.sin(2 * np.pi * f * t)).astype(np.float32)
    env = np.ones(n, np.float32)
    na = int(attack * SR)
    if na:
        env[:na] *= np.linspace(0, 1, na)
    env *= (1 - 0.5 * t / max(dur, 0.01))
    return out / max(1e-6, np.max(np.abs(out))) * amp * env


def whoosh(dur=0.8, amp=0.14, reverse=False):
    n = int(dur * SR)
    rng = np.random.RandomState(4)
    noise = rng.randn(n).astype(np.float32)
    t = np.arange(n) / SR
    lfo = (np.sin(2 * np.pi * 2.2 * t) * 0.5 + 0.5)
    s = noise * (0.4 + 0.6 * lfo)
    env = np.linspace(0, 1, n) ** 2.2 if reverse else np.linspace(1, 0, n) ** 1.6
    return (s * env).astype(np.float32) * amp


def impact(amp=0.28):
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
    for f, a, dcy in [(220, 1.0, 0.9), (330, 0.6, 1.1), (440, 0.42, 1.3), (660, 0.25, 1.6)]:
        out += (a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy)).astype(np.float32)
    return out / max(1e-6, np.max(np.abs(out))) * amp


def main():
    dur = DUR
    n = int(dur * SR)
    master = np.zeros(n + SR * 3, np.float32)

    def put(sig, t0):
        i0 = int(t0 * SR)
        master[i0:i0 + len(sig)] += sig[:len(master) - i0]

    vo = load_mp3(os.path.join(ROOT, 'audio', 'pk-1.mp3'))
    put(vo, 0.15)

    for tw in (6.0, 12.0, 17.9, 23.5):
        put(whoosh(0.8, amp=0.13, reverse=False), tw - 0.25)
        put(whoosh(0.7, amp=0.11, reverse=True), tw)

    put(sine_bed(12.1, [110, 165, 220], amp=0.075, attack=1.2), 17.9)
    put(impact(0.26), 27.0)
    put(stinger(2.9), 27.1)

    master = master[:n]
    master = np.tanh(master * 1.2) * 0.92
    pcm = (master * 32767).astype(np.int16)
    import wave as wavmod
    outp = os.path.join(ROOT, 'audio', 'pk-teaser-master.wav')
    with wavmod.open(outp, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', outp, f'{dur:.2f}s')


if __name__ == '__main__':
    main()
