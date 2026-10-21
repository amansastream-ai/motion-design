"""Audio builder « Grève 72h » — voix voice-02, clips calibrés sur les minutes du montage."""
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
        # Durées mesurées : a14.65 b11.81 c12.88 d13.27 e12.77 f11.68 g11.52 h14.29 i12.20
        dur, out = 200.0, 'audio/g72-master.wav'
        vo = [('audio/g72-a.mp3', 7.3), ('audio/g72-b.mp3', 24.3), ('audio/g72-c.mp3', 42.3),
              ('audio/g72-d.mp3', 59.3), ('audio/g72-e.mp3', 77.3), ('audio/g72-f.mp3', 95.3),
              ('audio/g72-g.mp3', 112.3), ('audio/g72-h.mp3', 129.3), ('audio/g72-i.mp3', 147.3)]
        whooshes = [7.0, 24.0, 42.0, 59.0, 77.0, 95.0, 112.0, 129.0, 147.0, 180.0]
        impacts = [7.0, 24.0, 147.0, 180.0]
    elif which == '9x16':
        dur, out = 90.0, 'audio/g72-9x16-master.wav'
        vo = [('audio/g72-b.mp3', 6.3), ('audio/g72-c.mp3', 22.3),
              ('audio/g72-d.mp3', 38.3), ('audio/g72-i.mp3', 54.3)]
        whooshes = [6.0, 22.0, 38.0, 54.0, 70.0, 80.0]
        impacts = [6.0, 22.0, 54.0]
    elif which == 'teaser':
        dur, out = 30.0, 'audio/g72-teaser-master.wav'
        vo = [('audio/g72-hook.mp3', 2.0)]
        whooshes = [2.0, 7.0, 12.0, 17.0, 22.0]
        impacts = [2.0, 17.0, 22.0]
    else:
        raise SystemExit('usage: g72_audio.py 16x9|9x16|teaser')

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
