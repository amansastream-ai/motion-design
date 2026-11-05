"""Audio builder « Dip Doundou Guiss — double disque d'or » — SNGAL INFOS (FR).
RÈGLES : voix dès 0,15 s · écarts 0,5 s max · son audible jusqu'à la fin.
Mesuré : a12.67 b19.28 c15.35 d15.06 e23.85 f17.54 g16.63 h16.15 i14.71 hook15.74
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


def sine_bed(dur, freqs, amp=0.075):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    bed = np.zeros(n)
    for i, f in enumerate(freqs):
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (1 / (8 + 3 * i)) * t)
        bed += np.sin(2 * np.pi * f * t) * lfo * (0.55 ** i)
    return bed / max(1e-9, np.max(np.abs(bed))) * amp


def stinger(dur=2.4, amp=0.16):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    s = (np.sin(2 * np.pi * 220 * t) + 0.7 * np.sin(2 * np.pi * 330 * t)
         + 0.5 * np.sin(2 * np.pi * 440 * t))
    return s / 2.2 * np.exp(-t * 1.4) * amp


def main():
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else '16x9'
    if which == '16x9':
        dur, out = 163.0, 'audio/dg-master.wav'
        vo = [('audio/dg-a.mp3', 0.15), ('audio/dg-b.mp3', 13.32), ('audio/dg-c.mp3', 33.10),
              ('audio/dg-d.mp3', 48.95), ('audio/dg-e.mp3', 64.51), ('audio/dg-f.mp3', 88.86),
              ('audio/dg-g.mp3', 106.90), ('audio/dg-h.mp3', 124.03), ('audio/dg-i.mp3', 140.68)]
        whooshes = [0.15, 13.32, 33.10, 48.95, 64.51, 88.86, 106.90, 124.03, 140.68, 157.0, 160.2]
        impacts = [0.15, 13.32, 140.68, 157.0, 160.2]
        stingers = [157.0, 160.2]
    elif which == '9x16':
        dur, out = 90.0, 'audio/dg-9x16-master.wav'
        vo = [('audio/dg-b.mp3', 0.15), ('audio/dg-g.mp3', 19.93), ('audio/dg-f.mp3', 37.06),
              ('audio/dg-h.mp3', 55.10), ('audio/dg-i.mp3', 71.75)]
        whooshes = [0.15, 19.93, 37.06, 55.10, 71.75, 86.46]
        impacts = [0.15, 37.06, 71.75, 86.46]
        stingers = [86.46]
    elif which == 'teaser':
        dur, out = 30.0, 'audio/dg-teaser-master.wav'
        vo = [('audio/dg-hook.mp3', 0.15)]
        whooshes = [0.15, 15.89, 19.5, 23.0, 26.5]
        impacts = [0.15, 15.89, 23.0, 26.5]
        stingers = [23.0, 26.5]
    else:
        raise SystemExit('usage: dg_audio.py 16x9|9x16|teaser')

    n = int(SR * dur)
    master = np.zeros(n + SR * 20)
    for name, t0 in vo:
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            print('missing', name)
            continue
        import subprocess, tempfile, wave as wavmod
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
            tw = tf.name
        subprocess.run([FFMPEG, '-y', '-i', p, '-ar', str(SR), '-ac', '1', tw],
                       capture_output=True, check=True)
        with wavmod.open(tw, 'rb') as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        seg = np.zeros(int(SR * 38))
        seg[:len(data)] = data.astype(np.float32) / 32768.0
        os.unlink(tw)
        start = int(t0 * SR)
        seg = seg[:int(38 * SR)]
        n_fit = min(len(seg), len(master) - start)
        if n_fit > 0:
            master[start:start + n_fit] += seg[:n_fit]

    bed = sine_bed(dur, [110, 165, 220])
    master[:len(bed)] += bed

    for wh in whooshes:
        w = _wave('sweep', 0.20, 0.13)
        s = int(wh * SR)
        master[s:s + len(w)] += w
    for t0 in impacts:
        w = _wave('burst', 0.14, 0.20)
        s = int(t0 * SR)
        master[s:s + len(w)] += w
    for t0 in stingers:
        w = stinger()
        s = int(t0 * SR)
        master[s:s + len(w)] += w

    master = master[:n]
    fade_n = int(0.5 * SR)
    if n > fade_n:
        master[-fade_n:] *= np.linspace(1, 0.4, fade_n)

    master = np.tanh(master * 1.25) * 0.85
    peak = np.max(np.abs(master))
    if peak > 0.97:
        master *= 0.97 / peak
    pcm = (master * 32767).astype(np.int16)
    import wave as wavmod
    with wavmod.open(os.path.join(ROOT, out), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print('wrote', out, f'{dur}s')


if __name__ == '__main__':
    main()
