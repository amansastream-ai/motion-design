"""Audio builder « Naufrage au large de Kébémer » — SNGAL INFOS (FR).
RÈGLES : voix dès 0,15 s · écarts 0,5 s max · son audible jusqu'à la fin.
Mesuré : a13.00 b11.13 c13.13 d10.70 e10.62 f10.53 g11.60 h11.01 i9.94 hook11.22
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
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else '16x9'
    if which == '16x9':
        dur, out = 126.5, 'audio/nk-master.wav'
        vo = [('audio/nk-a.mp3', 0.15), ('audio/nk-b.mp3', 13.65), ('audio/nk-c.mp3', 25.28),
              ('audio/nk-d.mp3', 38.91), ('audio/nk-e.mp3', 50.11), ('audio/nk-f.mp3', 61.23),
              ('audio/nk-g.mp3', 72.26), ('audio/nk-h.mp3', 84.36), ('audio/nk-i.mp3', 95.87)]
        whooshes = [0.15, 13.65, 25.28, 38.91, 50.11, 61.23, 72.26, 84.36, 95.87, 117.5, 121.5, 123.8]
        impacts = [0.15, 13.65, 95.87, 117.5, 121.5, 123.8]
        stingers = [117.5, 121.5, 123.8]
    elif which == '9x16':
        dur, out = 90.0, 'audio/nk-9x16-master.wav'
        vo = [('audio/nk-a.mp3', 0.15), ('audio/nk-b.mp3', 13.65), ('audio/nk-c.mp3', 25.28),
              ('audio/nk-d.mp3', 38.91), ('audio/nk-g.mp3', 50.11), ('audio/nk-h.mp3', 62.21),
              ('audio/nk-i.mp3', 73.72)]
        whooshes = [0.15, 13.65, 25.28, 38.91, 50.11, 62.21, 73.72, 83.66, 87.0]
        impacts = [0.15, 25.28, 73.72, 83.66, 87.0]
        stingers = [83.66, 87.0]
    elif which == 'teaser':
        dur, out = 30.0, 'audio/nk-teaser-master.wav'
        vo = [('audio/nk-hook.mp3', 0.15)]
        whooshes = [0.15, 11.37, 15.8, 20.3, 25.5, 27.6]
        impacts = [0.15, 11.37, 20.3, 25.5, 27.6]
        stingers = [20.3, 25.5, 27.6]
    else:
        raise SystemExit('usage: nk_audio.py 16x9|9x16|teaser')

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
        master[-fade_n:] *= np.linspace(1, 0.55, fade_n)

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
