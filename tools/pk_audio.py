"""Audio builder « Séquestration présumée à Pikine » (FR).
RÈGLES : voix dès 0,15 s · écarts 0,5 s max · son audible jusqu'à la fin.
Ordre : 1 2 3 4 5 6 7 8 10 9 (9 = voix du débat).
Run: pytools/bin/python tools/pk_audio.py
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


def load_mp3(path):
    import subprocess, tempfile, wave as wavmod
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
        wav_path = tf.name
    subprocess.run([FFMPEG, '-y', '-v', 'quiet', '-i', path, '-ar', str(SR),
                    '-ac', '1', wav_path], check=True)
    with wavmod.open(wav_path, 'rb') as w:
        data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    os.unlink(wav_path)
    return data


def main():
    import sys
    short = 'short' in sys.argv
    if short:
        order = [1, 2, 4, 6, 8, 9]
        hold, outro_len, out_name = 4.0, 5.0, 'audio/pk-short-master.wav'
    else:
        order = [1, 2, 3, 4, 5, 6, 7, 8, 10, 9]   # 9 = voix du débat (en dernier)
        hold, outro_len, out_name = 8.0, 6.0, 'audio/pk-master.wav'
    clips = []
    t = 0.15
    for k in order:
        data = load_mp3(os.path.join(ROOT, f'audio/pk-{k}.mp3'))
        clips.append((k, t, data))
        print(f'pk-{k} @ {t:.2f} ({len(data)/SR:.2f}s)')
        t += len(data) / SR + 0.5
    debate_end = clips[-1][1] + len(clips[-1][2]) / SR   # fin voix finale
    outro_start = debate_end + hold                       # plateau final
    dur = outro_start + outro_len
    print(f'debate_end={debate_end:.2f} outro_start={outro_start:.2f} DUR={dur:.2f}')

    n = int(SR * dur)
    master = np.zeros(n + SR * 10)
    for k, t0, data in clips:
        i0 = int(t0 * SR)
        master[i0:i0 + len(data)] += data

    starts = [t0 for _, t0, _ in clips] + [outro_start]
    for t0 in starts:
        w = _wave('sweep', 0.9, 0.11)
        i0 = int(t0 * SR)
        master[i0:i0 + len(w)] += w
    for t0 in [0.15, outro_start]:
        w = _wave('noise', 0.5, 0.16)
        i0 = int(t0 * SR)
        master[i0:i0 + len(w)] += w
    s = stinger()
    i0 = int((outro_start + 0.15) * SR)
    master[i0:i0 + len(s)] += s

    bed = sine_bed(outro_len, [110, 165, 220], amp=0.085)
    i0 = int(outro_start * SR)
    master[i0:i0 + len(bed)] += bed

    master = master[:n]
    master = np.tanh(master * 1.25) * 0.92
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
