"""Audio builder « LFR 2026 entre en vigueur par décret » (FR).
RÈGLES : voix dès 0,15 s · écarts 0,5 s max · son audible jusqu'à la fin.
Mesuré : a16.16 b16.24 c12.92 d9.51 e11.42 f8.53 g9.21
Run: pytools/bin/python tools/lfr2_audio.py
"""
import os
import numpy as np
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100


def _wave(kind, dur, amp, f0=950, f1=90):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    if kind == 'sweep':
        f = np.linspace(f0, f1, n)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * amp
    noise = np.random.randn(n)
    k = np.ones(300) / 300
    return np.convolve(noise, k, mode='same') * amp


def sine_bed(dur, freqs, amp=0.09):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    bed = np.zeros(n)
    for i, f in enumerate(freqs):
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (1 / (8 + 3 * i)) * t)
        bed += np.sin(2 * np.pi * f * t) * lfo * (0.55 ** i)
    return bed / max(1e-9, np.max(np.abs(bed))) * amp


def stinger(dur=3.2, amp=0.26):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    s = (np.sin(2 * np.pi * 220 * t) + 0.7 * np.sin(2 * np.pi * 330 * t)
         + 0.5 * np.sin(2 * np.pi * 440 * t))
    return s / 2.2 * np.exp(-t * 0.7) * amp


def main():
    dur, out = 92.5, 'audio/lfr2-master.wav'
    vo = [('audio/lfr2-a.mp3', 0.15), ('audio/lfr2-b.mp3', 16.81),
          ('audio/lfr2-c.mp3', 33.55), ('audio/lfr2-d.mp3', 46.97),
          ('audio/lfr2-e.mp3', 56.98), ('audio/lfr2-f.mp3', 68.90),
          ('audio/lfr2-g.mp3', 77.93)]
    whooshes = [0.15, 16.81, 33.55, 46.97, 56.98, 68.90, 77.93, 87.14]
    impacts = [0.15, 87.14]
    stingers = [87.30]

    n = int(SR * dur)
    master = np.zeros(n + SR * 10)
    for name, t0 in vo:
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            print('missing', name)
            continue
        import subprocess, tempfile, wave as wavmod
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
            wav_path = tf.name
        subprocess.run([FFMPEG, '-y', '-v', 'quiet', '-i', p, '-ar', str(SR),
                        '-ac', '1', wav_path], check=True)
        with wavmod.open(wav_path, 'rb') as w:
            data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        os.unlink(wav_path)
        i0 = int(t0 * SR)
        master[i0:i0 + len(data)] += data
        print(f'  {name} @ {t0} ({len(data)/SR:.2f}s)')

    for t0 in whooshes:
        w = _wave('sweep', 0.9, 0.11)
        i0 = int(t0 * SR)
        master[i0:i0 + len(w)] += w
    for t0 in impacts:
        w = _wave('noise', 0.5, 0.16)
        i0 = int(t0 * SR)
        master[i0:i0 + len(w)] += w
    for t0 in stingers:
        s = stinger()
        i0 = int(t0 * SR)
        master[i0:i0 + len(s)] += s

    bed = sine_bed(5.36, [110, 165, 220], amp=0.085)
    i0 = int(87.14 * SR)
    master[i0:i0 + len(bed)] += bed

    master = master[:n]
    master = np.tanh(master * 1.25) * 0.92
    pcm = (master * 32767).astype(np.int16)
    import wave as wavmod
    with wavmod.open(os.path.join(ROOT, out), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('wrote', out, f'{dur}s')


if __name__ == '__main__':
    main()
