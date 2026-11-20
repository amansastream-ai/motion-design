"""Boost tanh du tail audio d'une vidéo (fix QC « son audible jusqu'au dernier frame »).
Réécrit le wav master sur les N dernières secondes (rampe douce) et remux sans réencoder la vidéo.
Run: pytools/bin/python tools/boost_tail.py <video.mp4> <master.wav> <out.mp4> [gain] [region_s]
"""
import os
import sys
import subprocess
import numpy as np
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000


def main():
    video, wav, out = sys.argv[1], sys.argv[2], sys.argv[3]
    gain = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
    region = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0

    import wave as wavmod
    with wavmod.open(os.path.join(ROOT, wav), 'rb') as w:
        sr = w.getframerate()
        # sr lu depuis le fichier (44,1 ou 48 kHz)
        p = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0

    n = int(region * sr)
    tail = p[-n:].copy()
    ramp = np.linspace(1.0, gain, len(tail))          # montée douce du gain
    p[-n:] = np.tanh(tail * ramp) * 0.95

    tmpwav = os.path.join(ROOT, 'audio', '_boost_tail.wav')
    pcm = (np.clip(p, -1, 1) * 32767).astype(np.int16)
    with wavmod.open(tmpwav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())

    subprocess.run([FFMPEG, '-y', '-i', os.path.join(ROOT, video), '-i', tmpwav,
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '192k', '-ac', '2',
                    os.path.join(ROOT, out) + '.remux.mp4'], capture_output=True, check=True)
    os.replace(os.path.join(ROOT, out) + '.remux.mp4', os.path.join(ROOT, out))
    os.unlink(tmpwav)
    print('wrote', out)


if __name__ == '__main__':
    main()
