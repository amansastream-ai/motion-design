"""Audio builder « Rejet LFR 2026 » — SNGAL INFOS. RÈGLES :
voix dès 0,15 s · écarts de 0,5 s max · SON AUDIBLE JUSQU'À LA FIN (pas de fade mou).
Durées mesurées : a10.83 b10.02 c8.10 d6.52 e8.10 f11.73 g11.90 h11.30 i9.94 hook12.41
"""
import os
import numpy as np
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100

WAVES = {
    'whoosh':  dict(kind='sweep', f0=950, f1=90, dur=0.20, amp=0.13),
    'impact':  dict(kind='burst', dur=0.14, amp=0.20),
}


def _wave(spec):
    d = spec['dur']
    n = int(SR * d)
    t = np.linspace(0, d, n, endpoint=False)
    if spec['kind'] == 'sweep':
        f = np.linspace(spec['f0'], spec['f1'], n)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * spec['amp']
    noise = np.random.randn(n)
    k = np.ones(300) / 300
    return np.convolve(noise, k, mode='same') * spec['amp']


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
    env = np.exp(-t * 1.4)
    return s / 2.2 * env * amp


def main():
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else '16x9'
    if which == '16x9':
        dur, out = 104.0, 'audio/lfr2-master.wav'
        # chaîne serrée : 0,15 s puis +0,5 s de pause max entre chaque voix
        vo = [('audio/lfr-a.mp3', 0.15), ('audio/lfr-b.mp3', 11.48), ('audio/lfr-c.mp3', 22.0),
              ('audio/lfr-d.mp3', 30.6), ('audio/lfr-e.mp3', 37.62), ('audio/lfr-f.mp3', 46.22),
              ('audio/lfr-g.mp3', 58.45), ('audio/lfr-h.mp3', 70.85), ('audio/lfr-i.mp3', 82.65)]
        whooshes = [0.15, 11.48, 22.0, 30.6, 37.62, 46.22, 58.45, 70.85, 82.65, 98.0]
        impacts = [0.15, 11.48, 82.65, 98.0]
        stingers = [98.0]
    elif which == '9x16':
        dur, out = 90.0, 'audio/lfr2-9x16-master.wav'
        vo = [('audio/lfr-a.mp3', 0.15), ('audio/lfr-b.mp3', 11.48), ('audio/lfr-c.mp3', 22.0),
              ('audio/lfr-d.mp3', 30.6), ('audio/lfr-f.mp3', 37.62), ('audio/lfr-g.mp3', 49.85),
              ('audio/lfr-h.mp3', 62.25), ('audio/lfr-i.mp3', 74.05)]
        whooshes = [0.15, 11.48, 22.0, 30.6, 37.62, 49.85, 62.25, 74.05, 84.0]
        impacts = [0.15, 37.62, 74.05, 84.0]
        stingers = [84.0]
    elif which == 'teaser':
        dur, out = 30.0, 'audio/lfr2-teaser-master.wav'
        vo = [('audio/lfr-hook.mp3', 0.15)]
        whooshes = [0.15, 12.56, 18.0, 23.5, 27.0]
        impacts = [0.15, 12.56, 27.0]
        stingers = [27.0]
    else:
        raise SystemExit('usage: lfr2_audio.py 16x9|9x16|teaser')

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
        w = _wave(WAVES['whoosh'])
        s = int(wh * SR)
        master[s:s + len(w)] += w
    for t0 in impacts:
        w = _wave(WAVES['impact'])
        s = int(t0 * SR)
        master[s:s + len(w)] += w
    for t0 in stingers:
        w = stinger()
        s = int(t0 * SR)
        master[s:s + len(w)] += w

    master = master[:n]
    # fade court : le son reste audible jusqu'à la fin
    fade_n = int(0.8 * SR)
    if n > fade_n:
        master[-fade_n:] *= np.linspace(1, 0.25, fade_n)

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
