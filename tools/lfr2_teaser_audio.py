"""Teaser audio « LFR 2026 : par décret » — 30 s.
hook 11.42 s dès 0,15 · cta 6.10 s dès 12.56 · battements aux cartes.
Run: pytools/bin/python tools/lfr2_teaser_audio.py
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


def stinger(dur=2.8, amp=0.28):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    s = (np.sin(2 * np.pi * 220 * t) + 0.7 * np.sin(2 * np.pi * 330 * t)
         + 0.5 * np.sin(2 * np.pi * 440 * t))
    return s / 2.2 * np.exp(-t * 0.7) * amp


def main():
    dur, out = 30.0, 'audio/lfr2-decret-teaser-master.wav'
    vo = [('audio/lfr2-t-hook.mp3', 0.15), ('audio/lfr2-t-cta.mp3', 12.56)]
    whooshes = [0.15, 4.5, 8.5, 12.56, 18.0, 23.5, 27.0]
    impacts = [0.15, 27.0]
    stingers = [27.1]

    n = int(SR * dur)
    master = np.zeros(n + SR * 5)
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
        w = _wave('sweep', 0.8, 0.12)
        i0 = int(t0 * SR)
        master[i0:i0 + len(w)] += w
    for t0 in impacts:
        w = _wave('noise', 0.5, 0.17)
        i0 = int(t0 * SR)
        master[i0:i0 + len(w)] += w
    for t0 in stingers:
        s = stinger()
        i0 = int(t0 * SR)
        master[i0:i0 + len(s)] += s

    bed = sine_bed(3.0, [110, 165, 220], amp=0.10)
    i0 = int(27.0 * SR)
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
