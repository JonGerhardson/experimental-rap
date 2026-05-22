#!/usr/bin/env python3
"""
track_kit — shared synthesis + io for the EXPERIMENTAL RAP album.
808s scribbled in numpy, talk pasted in from real David Antin recordings.
"""
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100

# ---------- io ----------
def read_wav(path):
    sr, x = wavfile.read(path)
    x = x.astype(np.float64)
    if x.ndim == 2:
        x = x.mean(axis=1)
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak
    if sr != SR:
        x = signal.resample(x, int(len(x) * SR / sr))
    return x

def write_wav(path, x):
    wavfile.write(path, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))

def highpass(x, fc, order=4):
    b, a = signal.butter(order, fc / (SR / 2), btype="high"); return signal.filtfilt(b, a, x)

def lowpass(x, fc, order=4):
    b, a = signal.butter(order, fc / (SR / 2), btype="low"); return signal.filtfilt(b, a, x)

def bandpass(x, lo, hi, order=4):
    b, a = signal.butter(order, [lo/(SR/2), hi/(SR/2)], btype="band"); return signal.filtfilt(b, a, x)

def norm(x, target=0.9):
    return x / (np.max(np.abs(x)) or 1.0) * target

def fade(x, t=0.01):
    n = min(int(t * SR), len(x) // 2)
    if n > 0:
        x[:n] *= np.linspace(0, 1, n); x[-n:] *= np.linspace(1, 0, n)
    return x

# ---------- drum/synth voices ----------
def make_808(note=49.0, dur=0.85, glide=4.0, decay=2.3, sat=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f = note * (1.0 + glide * np.exp(-t * 55))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    amp = np.exp(-t * decay)
    click = np.exp(-t * 700) * np.random.randn(n) * 0.25
    sig = body * amp + click
    sig = np.tanh(sig * sat) / np.tanh(sat)
    return fade(sig * 0.95, 0.004)

def make_kick(dur=0.3):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 150 * np.exp(-t * 30) + 50
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12)
    return fade(np.tanh(sig * 1.6) * 0.9, 0.002)

def make_hat(dur=0.045, open_=False, tone=7000):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = highpass(np.random.randn(n), tone)
    decay = np.exp(-t * (40 if open_ else 130))
    return fade(noise * decay * 0.35, 0.002)

def make_clap():
    n = int(0.18 * SR); t = np.arange(n) / SR
    noise = bandpass(np.random.randn(n), 1200, 4500)
    env = np.zeros(n)
    for off in (0.0, 0.009, 0.018):
        i = int(off * SR); env[i:] += np.exp(-(t[:n - i]) * 90)
    env += np.exp(-t * 16) * 0.6
    return fade(noise * env * 0.3, 0.002)

def make_snare(dur=0.2):
    n = int(dur * SR); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 22) * 0.5
    noise = bandpass(np.random.randn(n), 1500, 6000) * np.exp(-t * 28)
    return fade(np.tanh((tone + noise) * 1.3) * 0.55, 0.002)

def make_rim():
    n = int(0.04 * SR); t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 220)
    return fade(sig * 0.5, 0.001)

# ---------- effects ----------
def reverb(x, decay=0.4, mix=0.25, taps=18):
    out = x.copy()
    for k in range(1, taps):
        d = int((0.013 * k) * SR)
        if d < len(x):
            g = (decay ** k) * mix
            out[d:] += x[:len(x) - d] * g
    return out

def saturate(x, drive=1.1):
    return np.tanh(x * drive)

# ---------- placement ----------
def place(track, clip, start_s, gain=1.0):
    i = int(start_s * SR); j = i + len(clip)
    if j > len(track):
        clip = clip[:len(track) - i]; j = len(track)
    if i < len(track):
        track[i:j] += clip * gain

def sidechain_duck(drums, voice, depth=0.35, smooth=6):
    env = lowpass(np.abs(voice), smooth)
    env = env / (np.max(env) or 1)
    return drums * (1.0 - depth * env)

# ---------- mastering ----------
def master(mix, lufs_target_peak=0.97):
    mix = highpass(mix, 28)
    mix = np.tanh(mix * 1.05)
    return norm(mix, lufs_target_peak)


class Talk:
    """Loads a David Antin recording once; grab(t0,t1) returns a cleaned, hp'd, normalized segment."""
    def __init__(self, path, hp=110):
        self.audio = read_wav(path); self.hp = hp
    def grab(self, t0, t1, hp=None, fade_t=0.03, gain=1.0):
        seg = self.audio[int(t0 * SR):int(t1 * SR)].copy()
        seg = highpass(seg, hp or self.hp)
        seg = norm(seg, 0.95)
        return fade(seg, fade_t) * gain


def beat_grid(bpm):
    BEAT = 60.0 / bpm
    def b(bar, beat=0.0):
        return (bar * 4 + beat) * BEAT
    return BEAT, b


# ============================================================
# melodic + textural voices (album expansion — beyond the 808)
# ============================================================
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)

def _adsr(n, a, d, s, r):
    a, d, r = int(a*SR), int(d*SR), int(r*SR)
    a, d, r = max(a,1), max(d,1), max(r,1)
    sus = max(n - a - d - r, 0)
    env = np.concatenate([
        np.linspace(0, 1, a),
        np.linspace(1, s, d),
        np.full(sus, s),
        np.linspace(s, 0, r),
    ])
    return env[:n] if len(env) >= n else np.pad(env, (0, n-len(env)))

def _osc(wave, phase):
    if wave == "sine":  return np.sin(phase)
    if wave == "saw":   return signal.sawtooth(phase)
    if wave == "square":return signal.square(phase, 0.5)
    if wave == "tri":   return signal.sawtooth(phase, 0.5)
    return np.sin(phase)

def synth(freq, dur, wave="saw", detune=0.0, voices=1, a=.01, d=.1, s=.7, r=.12,
          gain=.3, lp=None):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for v in range(voices):
        df = freq * (1 + detune * (v - (voices-1)/2) / max(voices,1))
        out += _osc(wave, 2*np.pi*df*t)
    out /= max(voices, 1)
    out *= _adsr(n, a, d, s, r)
    if lp: out = lowpass(out, lp)
    return fade(out * gain, 0.005)

def chord(midis, dur, wave="saw", **kw):
    n = int(dur * SR); out = np.zeros(n)
    for m in midis:
        v = synth(mtof(m), dur, wave=wave, **kw)
        out[:len(v)] += v
    return out / max(len(midis), 1) ** 0.5

def epiano(freq, dur, gain=.3):
    """FM-ish Rhodes: carrier + decaying modulator."""
    n = int(dur * SR); t = np.arange(n) / SR
    mod = np.sin(2*np.pi*freq*2*t) * np.exp(-t*6) * 3.0
    car = np.sin(2*np.pi*freq*t + mod)
    env = np.exp(-t*3.2)
    return fade(car * env * gain, 0.004)

def drone(midis, dur, detune=0.008, gain=.25, lp=2200):
    n = int(dur * SR); out = np.zeros(n)
    for m in midis:
        f = mtof(m)
        out += synth(f, dur, wave="saw", detune=detune, voices=3,
                     a=.4, d=.2, s=.9, r=.5, gain=1.0, lp=lp)
    out /= max(len(midis),1) ** 0.5
    return out * gain

def crackle(dur, density=900, gain=.12):
    n = int(dur * SR)
    out = np.zeros(n)
    k = int(dur * density)
    idx = np.random.randint(0, n, k)
    out[idx] = np.random.randn(k)
    out = bandpass(out, 1500, 9000)
    out += highpass(np.random.randn(n), 5000) * 0.02   # surface hiss
    return out * gain

def shaker(dur=0.06):
    n = int(dur*SR); t = np.arange(n)/SR
    return fade(highpass(np.random.randn(n), 6000) * np.exp(-t*55) * 0.3, 0.002)

def tom(freq=110, dur=0.35):
    n = int(dur*SR); t = np.arange(n)/SR
    f = freq * (1 + 0.8*np.exp(-t*25))
    sig = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*9)
    return fade(np.tanh(sig*1.3)*0.7, 0.002)

def metallic(freq=520, dur=0.4, gain=.3):
    n = int(dur*SR); t = np.arange(n)/SR
    sig = np.zeros(n)
    for r in (1.0, 1.71, 2.43, 3.17, 4.51):   # inharmonic partials
        sig += np.sin(2*np.pi*freq*r*t)
    sig *= np.exp(-t*7) / 5
    return fade(highpass(sig, 400) * gain, 0.002)

def bleep(midi, dur=0.12, wave="sine", gain=.3):
    return synth(mtof(midi), dur, wave=wave, a=.003, d=.03, s=.5, r=.05, gain=gain)

def pitch_speed(x, semitones):
    """Tape-style: resample to shift pitch AND speed together (chopped/screwed)."""
    ratio = 2 ** (semitones / 12.0)
    n = int(len(x) / ratio)
    return signal.resample(x, n)
