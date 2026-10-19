"""Audio builder for the « Les 7 points » series (voice-02): 16:9, 9x16, teaser."""
import os
import numpy as np
import imageio_ffmpeg
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100

WAVES = {
    'whoosh':  dict(kind='sweep', f0=950, f1=90, dur=0.20, amp=0.13),
    'impact':  dict(kind='burst', dur=0.14, amp=0.20),
}


def _wave(spec, dur=None):
    d = dur or spec['dur']
    n = int(SR * d)
    t = np.linspace(0, d, n, endpoint=False)
    if spec['kind'] == 'sweep':
        f = np.linspace(spec['f0'], spec['f1'], n)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * spec['amp']
    noise = np.random.randn(n)
    k = np.ones(300) / 300
    noise = np.convolve(noise, k, mode='same')
    return noise * spec['amp']


def sine_bed(dur, freqs, amp=0.05):
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
        dur, out = 210.0, 'audio/c16-master.wav'
        vo = [('audio/c16-a.mp3', 2.3), ('audio/c16-b.mp3', 24.3), ('audio/c16-c.mp3', 42.3),
              ('audio/c16-d.mp3', 63.3), ('audio/c16-e.mp3', 84.3), ('audio/c16-f.mp3', 103.3),
              ('audio/c16-g.mp3', 121.3), ('audio/c16-h.mp3', 139.3), ('audio/c16-i.mp3', 158.3)]
        whooshes = [7.0, 24.0, 42.0, 63.0, 84.0, 103.0, 121.0, 139.0, 158.0, 192.0]
    elif which == '9x16':
        dur, out = 90.0, 'audio/c9-master.wav'
        # j2 = P5 (c16-f) + P7 (c16-h), j3 = synthèse (c16-i) — mêmes voix voice-02
        vo = [('audio/c9-j1.mp3', 5.8), ('audio/c16-f.mp3', 25.8),
              ('audio/c16-h.mp3', 40.2), ('audio/c16-i.mp3', 55.4)]
        whooshes = [6.0, 25.0, 40.0, 55.0, 72.0, 82.0]
    elif which == 'teaser':
        dur, out = 30.0, 'audio/teaser-c16-master.wav'
        vo = [('audio/c9-j1.mp3', 2.0)]
        whooshes = [2.0, 9.0, 16.0, 23.0, 28.0]
    else:
        raise SystemExit('usage: c16_audio.py 16x9|9x16|teaser')

    n = int(SR * dur)
    master = np.zeros(n + SR * 40)
    for name, t0 in vo:
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            print('missing', name)
            continue
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
            tw = tf.name
        subprocess.run([FFMPEG, '-y', '-i', p, '-ar', str(SR), '-ac', '1', tw],
                       capture_output=True, check=True)
        seg = np.zeros(int(SR * 40))
        import wave as wavmod
        with wavmod.open(tw, 'rb') as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        seg[:len(data)] = data.astype(np.float32) / 32768.0
        os.unlink(tw)
        start = int(t0 * SR)
        seg = seg[:int(38 * SR)]
        n_fit = min(len(seg), len(master) - start)
        if n_fit > 0:
            master[start:start + n_fit] += seg[:n_fit]

    bed = sine_bed(dur + 2, [110, 165, 220], amp=0.038)
    master[:len(bed)] += bed

    for wh in whooshes:
        w = _wave(WAVES['whoosh'])
        s = int(wh * SR)
        master[s:s + len(w)] += w
    for t0 in [7.0, 24.0, 42.0, 158.0, 192.0] if which == '16x9' else [6.0, 26.0, 58.0]:
        w = _wave(WAVES['impact'])
        s = int(t0 * SR)
        master[s:s + len(w)] += w

    master = master[:n]
    fade_n = int(2.0 * SR)
    if n > fade_n:
        master[-fade_n:] *= np.linspace(1, 0, fade_n) ** 2
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
