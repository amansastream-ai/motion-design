"""Audio builder « Vie chère & grève » — voice-02, voix ENCHAÎNÉES (gap 0,85 s, plus de silences de 4-5 s).
Durées mesurées : a13.69 b10.58 c9.85 d9.33 e9.98 f11.05 g9.33 h10.37 i9.85 hook11.94
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


def sine_bed(dur, freqs, amp=0.038):
    n = int(SR * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    bed = np.zeros(n)
    for i, f in enumerate(freqs):
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * (1 / (8 + 3 * i)) * t)
        bed += np.sin(2 * np.pi * f * t) * lfo * (0.55 ** i)
    return bed / max(1e-9, np.max(np.abs(bed))) * amp


def main():
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else '16x9'
    if which == '16x9':
        # Enchaînement serré : chaque voix démarre 0,85 s après la fin de la précédente.
        dur, out = 152.0, 'audio/vc-master.wav'
        vo = [('audio/vc-a.mp3', 6.5), ('audio/vc-b.mp3', 21.04), ('audio/vc-c.mp3', 32.47),
              ('audio/vc-d.mp3', 43.17), ('audio/vc-e.mp3', 53.35), ('audio/vc-f.mp3', 64.18),
              ('audio/vc-g.mp3', 76.08), ('audio/vc-h.mp3', 86.26), ('audio/vc-i.mp3', 97.48)]
        whooshes = [6.2, 20.74, 32.17, 42.87, 53.05, 63.88, 75.78, 85.96, 97.18, 130.0]
        impacts = [6.2, 20.74, 97.18, 130.0]
    elif which == '9x16':
        dur, out = 90.0, 'audio/vc-9x16-master.wav'
        vo = [('audio/vc-b.mp3', 6.5), ('audio/vc-c.mp3', 17.93), ('audio/vc-d.mp3', 28.63),
              ('audio/vc-e.mp3', 38.81), ('audio/vc-g.mp3', 49.64), ('audio/vc-i.mp3', 59.82)]
        whooshes = [6.2, 17.68, 28.38, 38.56, 49.39, 59.57, 70.5]
        impacts = [6.2, 38.56, 59.57]
    elif which == 'teaser':
        dur, out = 30.0, 'audio/vc-teaser-master.wav'
        vo = [('audio/vc-hook.mp3', 2.0)]
        whooshes = [2.0, 7.5, 14.0, 20.0, 25.0]
        impacts = [2.0, 14.0, 20.0]
    else:
        raise SystemExit('usage: vc_audio.py 16x9|9x16|teaser')

    n = int(SR * dur)
    master = np.zeros(n + SR * 40)
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

    bed = sine_bed(dur + 2, [110, 165, 220])
    master[:len(bed)] += bed

    for wh in whooshes:
        w = _wave(WAVES['whoosh'])
        s = int(wh * SR)
        master[s:s + len(w)] += w
    for t0 in impacts:
        w = _wave(WAVES['impact'])
        s = int(t0 * SR)
        master[s:s + len(w)] += w

    master = master[:n]
    fade_n = int(2.0 * SR)
    if n > fade_n:
        master[-fade_n:] *= np.linspace(1, 0, fade_n) ** 2

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
