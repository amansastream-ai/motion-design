#!/usr/bin/env python3
"""
JAAY — "1 000 F POUR COMMENCER GRAND."
Original score + sound design, synthesised from scratch (no samples, no
copyrighted material). Afro-futurist electronic bed at 100 BPM in D minor,
with a full SFX layer cut to picture.

Timeline constants here MUST match src/scenes.js (scene boundaries).
"""
import numpy as np, wave, os, math

SR = 48000
DUR = 45.0
N = int(SR * DUR)
BPM = 100.0
BEAT = 60.0 / BPM          # 0.6 s
BAR = BEAT * 4             # 2.4 s
STEP = BEAT / 4            # 16th = 0.15 s

# scene boundaries (mirror of TL in scenes.js)
S1, S2, S3, S4, S5, S6, S7 = 0.0, 4.6, 10.2, 16.2, 23.9, 30.4, 36.2

rng = np.random.default_rng(20260127)

music = np.zeros((N, 2), dtype=np.float64)
sfx = np.zeros((N, 2), dtype=np.float64)


# ----------------------------------------------------------------- helpers
def tt(dur):
    return np.arange(int(SR * dur)) / SR


def place(buf, sig, t0, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    n = min(len(sig), N - i0)
    if n <= 0:
        return
    s = sig[:n]
    if s.ndim == 1:
        lg = math.sqrt(max(0.0, 0.5 * (1 - pan)))
        rg = math.sqrt(max(0.0, 0.5 * (1 + pan)))
        buf[i0:i0 + n, 0] += s * gain * lg * 1.4142
        buf[i0:i0 + n, 1] += s * gain * rg * 1.4142
    else:
        buf[i0:i0 + n, 0] += s[:n, 0] * gain
        buf[i0:i0 + n, 1] += s[:n, 1] * gain


def env(n, a=0.002, d=0.2, curve=4.0):
    t = np.arange(n) / SR
    e = np.exp(-t / max(d, 1e-4) * curve / 4.0)
    if a > 0:
        e *= np.clip(t / a, 0, 1)
    return e


def lowpass(x, cutoff, order=2):
    # simple one-pole cascade (cheap, stable)
    y = x.copy()
    for _ in range(order):
        a = math.exp(-2 * math.pi * cutoff / SR)
        out = np.empty_like(y)
        acc = 0.0
        for i in range(len(y)):
            acc = (1 - a) * y[i] + a * acc
            out[i] = acc
        y = out
    return y


def lowpass_fast(x, cutoff, order=2):
    """FFT brick-ish low pass with soft slope (vectorised)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    resp = 1.0 / np.sqrt(1.0 + (f / cutoff) ** (2 * order))
    return np.fft.irfft(X * resp, len(x))


def highpass_fast(x, cutoff, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    resp = 1.0 / np.sqrt(1.0 + (cutoff / np.maximum(f, 1e-6)) ** (2 * order))
    return np.fft.irfft(X * resp, len(x))


def bandpass_fast(x, lo, hi, order=2):
    return lowpass_fast(highpass_fast(x, lo, order), hi, order)


def saw(freq, n, detune=0.0, harmonics=18):
    t = np.arange(n) / SR
    f = freq * (1 + detune)
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if f * k > SR / 2.2:
            break
        out += np.sin(2 * np.pi * f * k * t) / k
    return out * 0.5


def sine_sw(f0, f1, dur, decay=0.22, curve=3.0):
    """sine with exponential pitch sweep — kicks, log drums, sub hits"""
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t / (decay * 0.5))
    ph = 2 * np.pi * np.cumsum(f) / SR
    e = np.exp(-t / decay * curve)
    return np.sin(ph) * e


def noise(dur):
    return rng.standard_normal(int(SR * dur))


def add_at(arr, sig, t0):
    i0 = int(t0 * SR)
    n = min(len(sig), len(arr) - i0)
    if n > 0 and i0 >= 0:
        arr[i0:i0 + n] += sig[:n]


# ------------------------------------------------------------- instruments
def kick():
    body = sine_sw(118, 44, 0.42, decay=0.16, curve=3.2)
    click = highpass_fast(noise(0.012), 1800) * env(int(SR * 0.012), 0.0005, 0.004)
    body[:len(click)] += click * 0.35
    return body * 0.9


def log_drum(freq=98.0):
    t = tt(0.34)
    f = freq * (1 + 0.9 * np.exp(-t / 0.035))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.13)
    body += 0.35 * np.sin(2 * ph) * np.exp(-t / 0.07)
    body = np.tanh(body * 1.6) * 0.7
    return body


def hat(open_=False):
    d = 0.16 if open_ else 0.05
    n = noise(d)
    s = highpass_fast(n, 7000, 3)
    return s * env(len(s), 0.0008, d * 0.7)


def shaker():
    d = 0.12
    s = bandpass_fast(noise(d), 3800, 9500, 2)
    e = np.exp(-np.arange(len(s)) / (SR * 0.035))
    return s * e * 0.5


def clap():
    out = np.zeros(int(SR * 0.28))
    for k, off in enumerate([0.0, 0.008, 0.017, 0.03]):
        s = bandpass_fast(noise(0.12), 900, 4200, 2)
        s = s * np.exp(-np.arange(len(s)) / (SR * (0.03 + 0.02 * k)))
        add_at(out, s * (1.0 - 0.18 * k), off)
    return out * 0.55


def tom(freq=140.0):
    return sine_sw(freq * 1.5, freq, 0.5, decay=0.18)


def bell(freq=880.0, dur=0.9, bright=1.0):
    t = tt(dur)
    parts = [(1.0, 1.0, 1.0), (2.76, 0.5, 0.6), (5.4, 0.25, 0.4), (8.93, 0.12, 0.28)]
    out = np.zeros(len(t))
    for mult, amp, dec in parts:
        out += amp * np.sin(2 * np.pi * freq * mult * t) * np.exp(-t / (dur * 0.22 * dec))
    out *= np.clip(t / 0.002, 0, 1)
    return out * 0.4 * bright


def struck_metal(freq=523.0, dur=1.6):
    """coin / metallic shimmer — inharmonic partials"""
    t = tt(dur)
    out = np.zeros(len(t))
    for mult, amp, dec in [(1, .9, .55), (2.32, .55, .38), (3.83, .4, .3),
                           (5.11, .3, .24), (7.4, .2, .18), (9.9, .12, .13)]:
        out += amp * np.sin(2 * np.pi * freq * mult * t + rng.random() * 6) * np.exp(-t / (dur * dec))
    out *= np.clip(t / 0.001, 0, 1)
    return out * 0.32


def click(kind='ui'):
    d = 0.03 if kind == 'ui' else 0.06
    s = bandpass_fast(noise(d), 1400, 6200, 2)
    s *= np.exp(-np.arange(len(s)) / (SR * 0.008))
    tone = np.sin(2 * np.pi * (2100 if kind == 'ui' else 1250) * tt(d)) * np.exp(-tt(d) / 0.01) * 0.4
    return (s * 0.7 + tone) * 0.5


def whoosh(dur=0.9, up=True):
    n = noise(dur)
    t = tt(dur)
    # sweeping band-pass: implemented as time-varying emphasis via crossfade of bands
    lo = bandpass_fast(n, 300, 1400, 2)
    mid = bandpass_fast(n, 1200, 4200, 2)
    hi = bandpass_fast(n, 3500, 9500, 2)
    if up:
        w1 = np.clip(t / dur * 1.6, 0, 1)
        w2 = np.clip((t / dur - 0.25) * 1.9, 0, 1)
        w3 = np.clip((t / dur - 0.55) * 2.2, 0, 1)
    else:
        w1 = np.clip(1 - t / dur * 1.6, 0, 1)
        w2 = np.clip(1 - (t / dur - 0.25) * 1.9, 0, 1)
        w3 = np.clip(1 - (t / dur - 0.55) * 2.2, 0, 1)
    s = lo * w1 + mid * w2 + hi * w3
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    return s * e * 0.5


def riser(dur=2.0):
    n = noise(dur)
    t = tt(dur)
    s = bandpass_fast(n, 800, 7000, 2) * (t / dur) ** 2
    sweep = np.sin(2 * np.pi * np.cumsum(180 * (1 + 6 * (t / dur) ** 2)) / SR) * 0.12 * (t / dur) ** 2
    return (s * 0.7 + sweep)


def boom(dur=2.2, f0=70.0, f1=32.0):
    s = sine_sw(f0, f1, dur, decay=dur * 0.28, curve=3.0)
    rumble = lowpass_fast(noise(dur), 220, 2) * np.exp(-np.arange(int(SR * dur)) / (SR * 0.5)) * 0.25
    return s + rumble


def pad(freqs, dur, attack=0.8, release=1.2, cutoff=2200, width=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for i, f in enumerate(freqs):
        a = saw(f, n, detune=-0.0035 - 0.001 * i, harmonics=10)
        b = saw(f, n, detune=+0.0035 + 0.001 * i, harmonics=10)
        L += a
        R += b
    L = lowpass_fast(L, cutoff, 2)
    R = lowpass_fast(R, cutoff, 2)
    env_ = np.clip(t / attack, 0, 1) * np.clip((dur - t) / release, 0, 1)
    env_ = env_ ** 1.3
    return np.stack([L * env_, R * env_], axis=1) * 0.06 * width


def bass_note(freq, dur, bright=0.4):
    n = int(SR * dur)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 7):
        s += np.sin(2 * np.pi * freq * k * t) / (k ** 1.35)
    s = lowpass_fast(s, 260 + 900 * bright, 2)
    e = np.clip(t / 0.012, 0, 1) * np.exp(-t / (dur * 0.55))
    return s * e * 0.55


# ------------------------------------------------------------------- score
NOTE = {'D': 73.42, 'E': 82.41, 'F': 87.31, 'G': 98.0, 'A': 110.0, 'Bb': 116.54,
        'C': 130.81, 'D3': 146.83, 'F3': 174.61, 'G3': 196.0, 'A3': 220.0,
        'Bb3': 233.08, 'C4': 261.63, 'D4': 293.66, 'F4': 349.23, 'A4': 440.0}

PROG = [  # 4 bars, D minor progression
    ('D', ['D4', 'F4', 'A4']),
    ('Bb', ['D4', 'F4', 'Bb3']),
    ('F', ['C4', 'F4', 'A4']),
    ('C', ['C4', 'E', 'G3']),
]
ROOTS = {'D': 73.42, 'Bb': 116.54, 'F': 87.31, 'C': 65.41}

# --- pad bed across the whole piece (dynamic filtering per section)
for bar in range(int(DUR / BAR) + 1):
    t0 = bar * BAR
    if t0 >= DUR:
        break
    name, ch = PROG[bar % 4]
    freqs = [NOTE[c] for c in ch]
    # filter opens as the piece builds
    if t0 < S2:
        cut = 900
    elif t0 < S3:
        cut = 1500
    elif t0 < S4:
        cut = 1300
    elif t0 < S5:
        cut = 2000
    elif t0 < S6:
        cut = 2400
    else:
        cut = 1700
    p = pad([f / 2 for f in freqs], BAR * 1.15, attack=0.5, release=0.7, cutoff=cut)
    place(music, p, t0, gain=1.0)

# --- intro shimmer (0 – 4.6)
sh = bell(1046.5, 2.4, 0.6)
place(sfx, sh, 0.06, 0.22, pan=0.2)
place(sfx, bell(1568.0, 2.0, 0.5), 0.82, 0.12, pan=-0.3)
place(sfx, boom(2.4, 66, 30), 0.0, 0.95)
place(sfx, struck_metal(392.0, 2.2), 1.55, 0.5, pan=0.15)
place(sfx, whoosh(0.5, up=False), 1.42, 0.16)
place(sfx, click(), 2.0, 0.30, pan=-0.1)
place(sfx, boom(1.2, 90, 40), 2.05, 0.35)
place(sfx, click(), 2.32, 0.22, pan=0.1)
place(sfx, whoosh(1.0), 2.9, 0.20)
place(sfx, boom(1.6, 80, 34), 3.0, 0.5)

# --- groove (4.6 – 16.2)
t = S2
step = 0
while t < S3 - 0.05:
    bar_i = int(step // 16)
    bar_t = t
    s16 = step % 16
    # kick: 1, 2&, 3, 4&  (afro-skewed)
    if s16 in (0, 10) or (s16 == 6 and bar_i % 2 == 1):
        place(music, kick(), t, 0.85)
    # log drum melody
    LOG_PAT = [0, 3, 6, 8, 10, 14]
    if s16 in LOG_PAT:
        idx = LOG_PAT.index(s16)
        f = [98.0, 116.5, 98.0, 87.3, 130.8, 116.5][(idx + bar_i) % 6]
        place(music, log_drum(f), t, 0.34, pan=0.18 if idx % 2 else -0.18)
    # hats: swung 8ths
    if s16 % 2 == 0:
        swing = 0.012 if s16 % 4 == 2 else 0.0
        place(music, hat(), t + swing, 0.20, pan=0.3)
    # shaker 16ths with swing
    place(music, shaker(), t + (0.02 if s16 % 2 else 0.0), 0.10, pan=-0.25)
    # clap on 2 and 4
    if s16 in (4, 12):
        place(music, clap(), t, 0.26, pan=0.0)
    # bass
    if s16 in (0, 6, 10):
        root = ROOTS[PROG[bar_i % 4][0]]
        place(music, bass_note(root, 0.5, 0.5), t, 0.42)
    step += 1
    t = S2 + step * STEP

# --- breakdown (16.2 – 23.9) : space for the numbers
t = S3
step = 0
while t < S4 - 0.05:
    bar_i = int(step // 16)
    s16 = step % 16
    if s16 in (0, 8):
        place(music, log_drum(87.3), t, 0.22, pan=-0.1)
    if s16 in (4, 12):
        place(music, clap(), t, 0.20)
    if s16 % 4 == 2:
        place(music, shaker(), t, 0.11, pan=0.3)
    if s16 == 0:
        root = ROOTS[PROG[bar_i % 4][0]]
        place(music, bass_note(root * 2, 0.9, 0.25), t, 0.30)
    # tick-tock clock motif under the counters
    if s16 in (2, 6, 10, 14):
        place(music, click('tick'), t, 0.10, pan=0.35 if s16 % 8 == 2 else -0.35)
    step += 1
    t = S3 + step * STEP

# --- full section (23.9 – 30.4)
t = S4
step = 0
while t < S5 - 0.05:
    bar_i = int(step // 16)
    s16 = step % 16
    if s16 in (0, 3, 10, 14):
        place(music, kick(), t, 0.9)
    if s16 in (2, 5, 7, 9, 12, 15):
        f = [98.0, 130.8, 116.5, 146.8, 116.5, 98.0][(s16 + bar_i) % 6]
        place(music, log_drum(f), t, 0.30, pan=-0.2 if s16 % 2 else 0.2)
    if s16 % 2 == 1:
        place(music, hat(), t + 0.01, 0.17, pan=0.35)
    if s16 in (0, 8):
        place(music, hat(True), t, 0.12, pan=0.4)
    place(music, shaker(), t + (0.02 if s16 % 2 else 0.0), 0.12, pan=-0.3)
    if s16 in (4, 12):
        place(music, clap(), t, 0.30)
    if s16 in (0, 2, 6, 8, 11, 14):
        root = ROOTS[PROG[bar_i % 4][0]]
        place(music, bass_note(root, 0.34, 0.8), t, 0.44)
    if s16 in (13, 15) and bar_i % 2 == 1:
        place(music, tom(150), t, 0.22, pan=0.25)
    step += 1
    t = S4 + step * STEP

# --- climax build (30.4 – 36.2)
place(sfx, riser(2.4), S5 - 0.3, 0.34)
t = S5
step = 0
while t < S6 - 0.05:
    bar_i = int(step // 16)
    s16 = step % 16
    if s16 in (0, 5, 10):
        place(music, kick(), t, 0.9)
    if s16 in (4, 12):
        place(music, clap(), t, 0.34)
    if s16 % 2 == 0:
        place(music, hat(), t + (0.012 if s16 % 4 == 2 else 0), 0.16, pan=0.3)
    place(music, shaker(), t, 0.13, pan=-0.28)
    if s16 in (0, 3, 6, 9, 12, 15):
        f = [196.0, 146.8, 174.6, 233.1, 196.0, 261.6][(s16 + bar_i) % 6]
        place(music, log_drum(f), t, 0.26, pan=0.2 if s16 % 2 else -0.2)
    if s16 in (0, 8):
        place(music, bass_note(ROOTS[PROG[bar_i % 4][0]], 0.9, 0.5), t, 0.40)
    if bar_i >= 1 and s16 in (14, 15):
        place(music, tom(120 + 12 * s16), t, 0.26, pan=0.0)
    step += 1
    t = S5 + step * STEP

# --- outro (36.2 – 45)
place(sfx, boom(3.2, 62, 28), S6, 1.0)
place(sfx, whoosh(1.1, up=False), S6 - 0.55, 0.22)
# bell arpeggio: D minor, rising, spaced
arp = [(36.55, 587.33), (36.95, 698.46), (37.35, 880.0), (37.75, 1174.66)]
for (at, f) in arp:
    place(music, bell(f, 1.6, 0.8), at, 0.16, pan=(0.25 if int(at * 10) % 2 else -0.25))
# final logo sting
place(sfx, struck_metal(523.25, 2.6), 38.25, 0.32, pan=0.0)
place(sfx, bell(1046.5, 2.0, 0.7), 38.25, 0.14)
place(sfx, boom(2.6, 58, 26), 38.2, 0.6)
# pad tail
place(music, pad([NOTE['D3'], NOTE['F4'], NOTE['A4'], NOTE['D4']], 6.6, attack=0.6, release=2.4, cutoff=1500), 36.3, 1.15)

# --------------------------------------------------------------- SFX to cut
# scene transitions: whooshes + soft impacts
for (tb, big) in [(S2, 0.25), (S3, 0.3), (S4, 0.22), (S5, 0.3), (S6, 0.36)]:
    place(sfx, whoosh(0.85, up=True), tb - 0.42, big * 0.9)
    place(sfx, boom(1.0, 90, 40), tb - 0.05, big * 0.55)

# scene 2: message pops + typing + shutter
for i, at in enumerate([6.9, 7.6, 8.5]):
    place(sfx, click(), at, 0.22, pan=(-0.35 if i % 2 == 0 else 0.2))
place(sfx, click('tick'), 9.15, 0.16)
place(sfx, whoosh(0.7), 9.5, 0.18)
place(sfx, boom(1.2, 84, 36), 9.85, 0.35)

# scene 3: UI settles, phone lands, brand hit, price lift
place(sfx, click(), 10.45, 0.24, pan=0.1)
place(sfx, click(), 11.35, 0.18, pan=-0.2)
place(sfx, boom(1.8, 72, 32), 13.62, 0.75)
place(sfx, struck_metal(659.25, 1.8), 13.66, 0.26)
place(sfx, bell(1318.5, 1.4, 0.6), 14.32, 0.14, pan=0.2)
place(sfx, rising_tone := np.sin(2 * np.pi * np.cumsum(np.linspace(400, 1200, int(SR * 0.9))) / SR)
      * np.sin(np.pi * np.linspace(0, 1, int(SR * 0.9))) * 0.12, 14.55, 0.20)

# scene 4: sale → payment success → split → commission
place(sfx, click(), 16.55, 0.24, pan=-0.15)
# payment traveller
tv = highpass_fast(noise(0.8), 2500) * np.sin(np.pi * np.linspace(0, 1, int(SR * 0.8))) ** 2
place(sfx, tv, 17.15, 0.16)
place(sfx, bell(1567.98, 1.2, 0.7), 17.9, 0.24, pan=0.15)   # success chime
place(sfx, struck_metal(783.99, 1.4), 17.92, 0.16)
place(sfx, whoosh(0.6), 18.2, 0.16)
place(sfx, boom(1.4, 80, 34), 18.25, 0.5)
place(sfx, click(), 18.55, 0.24, pan=-0.4)
place(sfx, click(), 18.95, 0.22, pan=0.4)
# counters ticking up to 900 / 100
for i in range(9):
    place(sfx, click('tick'), 18.7 + i * 0.055, 0.08, pan=-0.4)
    place(sfx, click('tick'), 18.7 + i * 0.055, 0.08, pan=0.4)
place(sfx, whoosh(0.8), 20.35, 0.20)
place(sfx, boom(1.8, 74, 30), 20.5, 0.66)
place(sfx, struck_metal(523.25, 2.0), 20.55, 0.30)
place(sfx, bell(1046.5, 1.8, 0.7), 21.5, 0.14)

# scene 5: product cards whipping in + type hits
for i, at in enumerate([24.05, 24.2, 24.35, 24.5, 24.6]):
    place(sfx, whoosh(0.42, up=True), at, 0.10, pan=(-0.4 + 0.2 * i))
for at in [24.7, 26.6, 28.35]:
    place(sfx, boom(1.1, 96, 44), at, 0.36)
    place(sfx, click(), at + 0.02, 0.16)
place(sfx, whoosh(0.9), 29.55, 0.24)
place(sfx, boom(1.6, 70, 30), 29.7, 0.55)

# scene 6: particle convergence + logo assembly
conv = bandpass_fast(noise(3.0), 1200, 8000) * (np.linspace(0, 1, int(SR * 3.0)) ** 2.2)
place(sfx, conv, 30.35, 0.20)
place(sfx, boom(2.6, 64, 26), 33.4, 1.0)
place(sfx, struck_metal(523.25, 2.4), 33.42, 0.34)
place(sfx, bell(261.63, 2.2, 0.6), 33.45, 0.18)
place(sfx, whoosh(0.7), 33.2, 0.16)

# scene 7: CTA micro-interactions
place(sfx, click(), 36.6, 0.20, pan=0.2)
place(sfx, click(), 37.3, 0.16, pan=-0.2)
place(sfx, whoosh(0.5), 38.1, 0.14)

# ------------------------------------------------------------- mix + master
music = np.stack([lowpass_fast(music[:, 0], 12000, 2), lowpass_fast(music[:, 1], 12000, 2)], axis=1)

# sidechain duck music under the voice-over (rendered separately, approximated here
# by a segment envelope that matches the VO cue sheet in src/audio.js)
VO_SEGMENTS = [
    (0.35, 4.15), (4.75, 9.45), (10.3, 15.05), (16.35, 20.0),
    (20.65, 24.25), (24.75, 30.4), (31.05, 34.2), (36.35, 41.0),
]
duck = np.ones(N)
for (a, b) in VO_SEGMENTS:
    i0, i1 = int(a * SR), int(min(b, DUR) * SR)
    seg = np.ones(i1 - i0)
    fade = int(0.18 * SR)
    seg[:fade] = np.linspace(1, 0.58, fade)
    seg[-fade:] = np.linspace(0.58, 1, fade)
    duck[i0:i1] = np.minimum(duck[i0:i1], seg)
duck = lowpass_fast(duck, 12, 2)
music *= duck[:, None] * 0.9

mix = music + sfx * 0.9

# gentle bus compression + soft clip
peak = np.max(np.abs(mix))
mix = mix / max(peak, 1e-9) * 1.25
mix = np.tanh(mix * 0.85) * 0.92
mix = mix / max(np.max(np.abs(mix)), 1e-9) * 0.89     # ≈ -1 dBFS

# fade in/out
fi = int(0.15 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(1.3 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5

os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'build'), exist_ok=True)
out = os.path.join(os.path.dirname(__file__), '..', 'build', 'score.wav')
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
print('wrote', out, 'peak', float(np.max(np.abs(mix))), 'rms', float(np.sqrt(np.mean(mix ** 2))))
