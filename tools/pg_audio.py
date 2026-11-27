"""Master audio viral « Pirogues disparues — les 5 points clés » (wav 48 kHz mono, 72,5 s).
7 clips voice-02 · VO dès 0,15 s · écarts 0,35 s (rythme viral) · bed continu ·
whoosh aux frontières · impact + stinger sur le CTA final.
Run: pytools/bin/python tools/pg_audio.py
"""
import os
import numpy as np
import imageio_ffmpeg
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
DUR = 72.5

PLACEMENTS = [(1, 0.15), (2, 8.43), (3, 21.11), (4, 28.80), (5, 38.79), (6, 49.54), (7, 57.69)]
BOUNDS = [8.43, 21.11, 28.80, 38.79, 49.54, 57.69]


def load_mp3(path):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1',
                          '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def sine_bed(dur, freqs, amp=0.07, attack=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, a in zip(freqs, [1.0, 0.55, 0.35, 0.22]):
        out += (a * np.sin(2 * np.pi * f * t)).astype(np.float32)
    env = np.ones(n, np.float32)
    na = int(attack * SR)
    if na:
        env[:na] *= np.linspace(0, 1, na)
    return out / max(1e-6, np.max(np.abs(out))) * amp * env


def whoosh(dur=0.6, amp=0.09, reverse=False):
    n = int(dur * SR)
    rng = np.random.RandomState(13)
    noise = rng.randn(n).astype(np.float32)
    t = np.arange(n) / SR
    lfo = np.sin(2 * np.pi * 2.4 * t) * 0.5 + 0.5
    s = noise * (0.4 + 0.6 * lfo)
    env = np.linspace(0, 1, n) ** 2.0 if reverse else np.linspace(1, 0, n) ** 1.6
    return (s * env).astype(np.float32) * amp


def impact(amp=0.24):
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    f = 82 * np.exp(-t * 2.2)
    ph = np.cumsum(2 * np.pi * f / SR)
    body = np.sin(ph) * np.exp(-t * 2.6)
    rng = np.random.RandomState(17)
    click = rng.randn(n).astype(np.float32) * np.exp(-t * 26) * 0.4
    out = (body + click).astype(np.float32)
    return out / max(1e-6, np.max(np.abs(out))) * amp


def stinger(dur=5.0, amp=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, a, dcy in [(147, 1.0, 0.6), (220, 0.6, 0.8), (294, 0.42, 1.0), (440, 0.22, 1.3)]:
        out += (a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy)).astype(np.float32)
    return out / max(1e-6, np.max(np.abs(out))) * amp


def main():
    n = int(DUR * SR)
    master = np.zeros(n + SR * 2, np.float32)

    def put(sig, t0):
        i0 = int(t0 * SR)
        master[i0:i0 + len(sig)] += sig[:len(master) - i0]

    for k, t0 in PLACEMENTS:
        data = load_mp3(os.path.join(ROOT, f'audio/pg-{k}.mp3'))
        put(data, t0)
        print(f'pg-{k} @ {t0:.2f} ({len(data)/SR:.2f}s)')

    put(sine_bed(DUR, [110, 165, 220, 275], amp=0.07, attack=1.2), 0.0)
    for tb in BOUNDS:
        put(whoosh(0.6, amp=0.085), tb - 0.18)
        put(whoosh(0.45, amp=0.065, reverse=True), tb)
    put(impact(0.24), 57.69)
    put(stinger(5.0), 67.2)

    master = master[:n]
    master = np.tanh(master * 1.22) * 0.92
    pcm = (master * 32767).astype(np.int16)
    import wave as wavmod
    outp = os.path.join(ROOT, 'audio', 'pg-master.wav')
    with wavmod.open(outp, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', outp, f'{DUR:.2f}s')


if __name__ == '__main__':
    main()
