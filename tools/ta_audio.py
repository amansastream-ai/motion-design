"""Master audio « TAS : le Sénégal conserve son titre 2025 » (wav 48 kHz mono).
LONG (3:00) : 10 clips voice-02, VO dès 0,15 s par segment, bed continu + whoosh
aux frontières + stinger outro. Les plateaux (fiches animées) portent la durée —
règle : allonger par textes/plateaux, jamais les pauses.
Run: pytools/bin/python tools/ta_audio.py [short]
"""
import os
import sys
import numpy as np
import imageio_ffmpeg
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000


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


def whoosh(dur=0.7, amp=0.085, reverse=False):
    n = int(dur * SR)
    rng = np.random.RandomState(7)
    noise = rng.randn(n).astype(np.float32)
    t = np.arange(n) / SR
    lfo = np.sin(2 * np.pi * 2.0 * t) * 0.5 + 0.5
    s = noise * (0.4 + 0.6 * lfo)
    env = np.linspace(0, 1, n) ** 2.0 if reverse else np.linspace(1, 0, n) ** 1.6
    return (s * env).astype(np.float32) * amp


def impact(amp=0.24):
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    f = 84 * np.exp(-t * 2.4)
    ph = np.cumsum(2 * np.pi * f / SR)
    body = np.sin(ph) * np.exp(-t * 2.6)
    rng = np.random.RandomState(11)
    click = rng.randn(n).astype(np.float32) * np.exp(-t * 26) * 0.35
    out = (body + click).astype(np.float32)
    return out / max(1e-6, np.max(np.abs(out))) * amp


def stinger(dur=4.0, amp=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for f, a, dcy in [(196, 1.0, 0.7), (294, 0.6, 0.9), (392, 0.42, 1.1), (588, 0.22, 1.4)]:
        out += (a * np.sin(2 * np.pi * f * t) * np.exp(-t * dcy)).astype(np.float32)
    return out / max(1e-6, np.max(np.abs(out))) * amp


def main():
    short = 'short' in sys.argv
    if short:
        placements = [(1, 0.15), (2, 19.15), (4, 32.15), (6, 45.15), (8, 60.15), (9, 73.15)]
        bounds = [19, 32, 45, 60, 73, 90]
        dur, outro_start, out_name = 105.0, 90.0, 'audio/ta-short-master.wav'
    else:
        placements = [(1, 0.15), (2, 21.15), (3, 35.15), (4, 47.65), (5, 60.15), (6, 74.15),
                      (7, 88.65), (8, 101.15), (10, 115.65), (9, 130.15)]
        bounds = [21, 35, 47.5, 60, 74, 88.5, 101, 115.5, 130, 165]
        dur, outro_start, out_name = 180.0, 165.0, 'audio/ta-master.wav'

    n = int(dur * SR)
    master = np.zeros(n + SR * 2, np.float32)

    def put(sig, t0):
        i0 = int(t0 * SR)
        master[i0:i0 + len(sig)] += sig[:len(master) - i0]

    for k, t0 in placements:
        data = load_mp3(os.path.join(ROOT, f'audio/ta-{k}.mp3'))
        put(data, t0)
        print(f'ta-{k} @ {t0:.2f} ({len(data)/SR:.2f}s)')

    put(sine_bed(dur, [110, 165, 220, 275], amp=0.068, attack=1.4), 0.0)
    for tb in bounds[:-1]:
        put(whoosh(0.7, amp=0.08), tb - 0.2)
        put(whoosh(0.55, amp=0.06, reverse=True), tb)
    put(impact(0.22), outro_start)
    put(stinger(4.0), outro_start + 0.1)

    master = master[:n]
    master = np.tanh(master * 1.22) * 0.92
    pcm = (master * 32767).astype(np.int16)
    import wave as wavmod
    with wavmod.open(os.path.join(ROOT, out_name), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', out_name, f'{dur:.2f}s')


if __name__ == '__main__':
    main()
