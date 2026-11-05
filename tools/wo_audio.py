"""Audio builder « Rejet LFR 2026 » version WOLOF — SNGAL INFOS.
RÈGLES : voix dès 0,15 s · écarts 0,5 s max · son audible jusqu'à la fin.
Mesuré : a13.75 b12.47 c10.87 d8.63 e10.23 f12.15 g14.07 h14.39 i16.63 hook13.43
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
        dur, out = 124.0, 'audio/wo-master.wav'
        vo = [('audio/wo-a.mp3', 0.15), ('audio/wo-b.mp3', 14.40), ('audio/wo-c.mp3', 27.37),
              ('audio/wo-d.mp3', 38.74), ('audio/wo-e.mp3', 47.87), ('audio/wo-f.mp3', 58.60),
              ('audio/wo-g.mp3', 71.25), ('audio/wo-h.mp3', 85.82), ('audio/wo-i.mp3', 100.71)]
        whooshes = [0.15, 14.40, 27.37, 38.74, 47.87, 58.60, 71.25, 85.82, 100.71, 118.0, 121.2]
        impacts = [0.15, 14.40, 100.71, 118.0, 121.2]
        stingers = [118.0, 121.2]
    elif which == '9x16':
        dur, out = 90.0, 'audio/wo-9x16-master.wav'
        vo = [('audio/wo-b.mp3', 0.15), ('audio/wo-c.mp3', 13.12), ('audio/wo-f.mp3', 24.49),
              ('audio/wo-g.mp3', 37.14), ('audio/wo-h.mp3', 51.71), ('audio/wo-i.mp3', 66.60)]
        whooshes = [0.15, 13.12, 24.49, 37.14, 51.71, 66.60, 83.23]
        impacts = [0.15, 24.49, 66.60, 83.23]
        stingers = [83.23]
    elif which == 'teaser':
        dur, out = 30.0, 'audio/wo-teaser-master.wav'
        vo = [('audio/wo-hook.mp3', 0.15)]
        whooshes = [0.15, 13.58, 18.5, 23.5, 27.0]
        impacts = [0.15, 13.58, 27.0]
        stingers = [27.0]
    else:
        raise SystemExit('usage: wo_audio.py 16x9|9x16|teaser')

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
