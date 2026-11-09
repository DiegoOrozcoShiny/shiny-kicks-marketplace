import numpy as np, sys
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 44100; DUR = 16.733; N = int(SR * DUR)
rng = np.random.default_rng(3)
def T(d): return np.arange(int(SR * d)) / SR
def lp(x, f, o=4): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=4): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def add(buf, sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf): return
    if i < 0: sig = sig[-i:]; i = 0
    n = min(len(sig), len(buf) - i)
    l = g * np.sqrt(0.5 * (1 - pan)); r = g * np.sqrt(0.5 * (1 + pan))
    buf[i:i + n, 0] += sig[:n] * l * 1.414; buf[i:i + n, 1] += sig[:n] * r * 1.414

# ---------- drum / instrument voices ----------
def kick():
    t = T(0.45); f = 48 + 85 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7.5)
    click = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 300) * 0.25
    return np.tanh((s + click) * 1.6) * 0.9
def snare():
    t = T(0.3)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.5
    nz = bp(rng.standard_normal(len(t)), 1200, 7000) * np.exp(-t * 16)
    return np.tanh((body + nz * 0.9) * 1.3) * 0.75
def hat(open_=False):
    t = T(0.25 if open_ else 0.06)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (14 if open_ else 70)) * 0.35
def clap():
    t = T(0.35); env = np.zeros(len(t))
    for d in (0, 0.011, 0.022):
        i = int(d * SR); env[i:] += np.exp(-(t[: len(t) - i]) * (90 if d < 0.02 else 18))
    return bp(rng.standard_normal(len(t)), 900, 5000) * env * 0.6
def sub_hit(f=45, d=0.7):
    t = T(d); fr = f + 60 * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 4) * 0.9
def rhodes(freqs, d):
    t = T(d); s = np.zeros(len(t))
    for f in freqs:
        s += (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6)
              + 0.08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 10))
    env = np.minimum(1, t / 0.01) * np.exp(-t * 0.9)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    return s * env * trem / len(freqs) * 0.55
def bass(f, d):
    t = T(d); s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    env = np.minimum(1, t / 0.005) * np.exp(-t * 1.8) * np.minimum(1, (d - t) / 0.03)
    return np.tanh(s * env * 1.4) * 0.55
def noise_sweep(d, f0, f1, rise=True):
    t = T(d); x = rng.standard_normal(len(t)); out = np.zeros(len(t)); seg = 512
    for i in range(0, len(t), seg):
        p = i / len(t); f = f0 * (f1 / f0) ** p
        out[i:i + seg] = bp(x[max(0, i - 2048):i + seg], f * 0.7, min(f * 1.4, 20000))[-len(x[i:i + seg]):]
    env = (t / d) ** 2 if rise else np.sin(np.pi * t / d) ** 2
    return out * env * 0.9
def bell(f, d=1.2, g=1):
    t = T(d); s = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * k) for m, a, k in [(1, 1, 3), (2.76, .5, 6), (5.4, .25, 9), (8.9, .12, 14)])
    return s * np.minimum(1, t / 0.002) * 0.35 * g
def tick():
    t = T(0.03); return hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 200) * 0.3

note = lambda m: 440 * 2 ** ((m - 69) / 12)

# ---------- music: boom-bap 92 BPM, downbeat at 2.8s ----------
BPM = 92; B = 60 / BPM; S16 = B / 4; BAR = 4 * B; T0 = 2.8
music_pre = np.zeros((N, 2)); music = np.zeros((N, 2))
chords = [[57, 60, 64, 67, 71], [53, 57, 60, 64], [50, 53, 57, 60, 64], [52, 55, 59, 62]]  # Am9 Fmaj7 Dm9 Em7
roots = [33, 29, 26, 28]
bars = range(-2, 6)
for b in bars:
    bt = T0 + b * BAR; ci = b % 4
    pre = bt < T0
    tgt = music_pre if pre else music
    add(tgt, rhodes([note(m) for m in chords[ci]], BAR + 0.6), bt, 0.9, 0)
    if not pre:
        add(tgt, bass(note(roots[ci] + 12), B * 1.5), bt, 1.0)
        add(tgt, bass(note(roots[ci] + 12), B * 0.9), bt + 10 * S16, 0.8)
    for st in range(16):
        t = bt + st * S16 + (0.028 if st % 4 == 2 else 0)  # swing
        if st in (0, 6, 10) or (st == 15 and b % 2): add(tgt, kick(), t, 1.0 if st != 15 else 0.6)
        if st in (4, 12) and not pre: add(tgt, snare(), t, 0.9); add(tgt, clap(), t, 0.25)
        if st % 2 == 0: add(tgt, hat(), t, 0.55 if st % 4 == 0 else 0.35, 0.3)
        if st == 14 and b % 2 == 1: add(tgt, hat(True), t, 0.3, 0.3)
# pre-drop filtered + tension gap
music_pre = np.stack([lp(music_pre[:, c], 900) for c in range(2)], 1) * 1.3
gap0, gap1 = int(2.55 * SR), int(T0 * SR); music_pre[gap0:gap1] *= np.linspace(1, 0, gap1 - gap0)[:, None]
music_pre[gap1:] = 0
music[:gap1] = 0
music += music_pre
# crackle
cr = np.zeros(N); idx = rng.integers(0, N, 900); cr[idx] = rng.uniform(-1, 1, 900)
cr = hp(cr, 2000) * 0.18 + lp(rng.standard_normal(N), 400) * 0.004
music += np.stack([cr, np.roll(cr, 200)], 1)
# outro: lowpass sweep from 14.0, stop drums at final hit 16.1
lpd = np.stack([lp(music[:, c], 500) for c in range(2)], 1)
m = np.clip((np.arange(N) / SR - 13.9) / 0.6, 0, 1)[:, None]
music = music * (1 - m) + lpd * m * 1.25
end = int(16.1 * SR); music[end:] *= np.exp(-np.arange(N - end) / SR * 12)[:, None]

# ---------- SFX ----------
sfx = np.zeros((N, 2))
add(sfx, sub_hit(42, 1.0), 0.0, 1.0); add(sfx, hp(rng.standard_normal(int(.25 * SR)), 300) * np.exp(-T(.25) * 18) * .5, 0.0, 0.7)
add(sfx, sub_hit(40, 0.8), 0.38, 0.8)
for i in range(11): add(sfx, tick(), 1.55 + i * 0.037, 0.8, (-0.3 if i % 2 else 0.3))
add(sfx, noise_sweep(0.3, 300, 6000), 2.45, 0.7)
add(sfx, sub_hit(55, 0.35) * 0.6 + lp(rng.standard_normal(int(.35 * SR)), 500) * np.exp(-T(.35) * 25) * 0.6, 2.55, 0.8)
add(sfx, sub_hit(38, 1.2), T0, 1.0)
add(sfx, bell(1568), 2.85, 0.9, 0.1); add(sfx, bell(2349, 1.0, 0.6), 2.9, 0.6, -0.2)
add(sfx, noise_sweep(0.55, 3000, 14000, False) * 0.35, 3.3, 0.6, 0.4)
for tt in (6.3, 8.2, 10.4):
    add(sfx, clap(), tt, 0.9); add(sfx, sub_hit(50, 0.5), tt, 0.7)
add(sfx, noise_sweep(0.6, 400, 9000), 9.0, 0.6)
# cha-ching
add(sfx, bell(2093, 0.5, 0.8), 10.85, 0.8, -0.2); add(sfx, bell(2637, 1.2, 1), 10.97, 0.9, 0.2)
coins = np.zeros(int(0.6 * SR))
for _ in range(14):
    i = rng.integers(0, len(coins) - 4000); f = rng.uniform(4000, 7500); tt = T(0.09)
    coins[i:i + len(tt)] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 45) * 0.25
add(sfx, coins, 10.95, 0.8, 0.1)
for i in range(4): add(sfx, tick() * 2, 12.2 + i * 0.13, 0.6)
add(sfx, noise_sweep(0.27, 500, 10000), 13.3, 0.75)
add(sfx, sub_hit(45, 0.9), 13.95, 0.6); add(sfx, bell(1760, 1.5, 0.5), 13.95, 0.5)
add(sfx, sub_hit(36, 0.9), 16.1, 1.0); add(sfx, clap(), 16.1, 0.6)

def master(x, name):
    x = np.tanh(x * 1.1)
    x = x / np.max(np.abs(x)) * 0.89
    x[-int(0.12 * SR):] *= np.linspace(1, 0, int(0.12 * SR))[:, None]
    wavfile.write(name, SR, (x * 32767).astype(np.int16))
master(music * 0.75 + sfx * 0.8, 'mix_music_sfx.wav')
master(sfx, 'mix_sfx_only.wav')
print('ok')
