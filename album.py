#!/usr/bin/env python3
"""
WOULD THAT COUNT? — an experimental rap album.

The bit (from a Bluesky thread): "scribble an 808 in fruity loops and paste in a
David Antin talk and that's the whole thing — would that count?"  This builds the
whole thing: it downloads real David Antin talk-poem recordings, synthesizes a bed
for each track, pastes the talk over it, and masters 8 tagged MP3s.

Usage:
    python album.py                 # download assets + build & master all 8 tracks
    python album.py 1 6 8           # only those track numbers
    python album.py --no-master     # build raw WAVs only (skip ffmpeg mastering)
    python album.py --skip-download # assume antin_*.wav already present

Requires: python (numpy, scipy), yt-dlp and ffmpeg on PATH.
"""
import sys, os, gc, shutil, argparse, subprocess
import numpy as np
import track_kit as k
from track_kit import place, beat_grid, Talk

rng = np.random.default_rng(1968)

ALBUM = "WOULD THAT COUNT?"

# YouTube id -> local wav. These are the real David Antin recordings.
SOURCES = {
    "TFqOlTQu_n4": "antin_TFqOlTQu_n4.wav",   # discusses dream narrativity and desire
    "hQAahBcyYhw": "antin_hQAahBcyYhw.wav",   # from "The Black Plague"
    "kgcMDnyObSs": "antin_kgcMDnyObSs.wav",   # talking on Kathy Acker
    "7hLyj_CWjKU": "antin_7hLyj_CWjKU.wav",   # Psychoanalysis & Narrative, Kelly Writers House
    "ViWPGQaPrwI": "antin_ViWPGQaPrwI.wav",   # rethinking Freud
    "-4Xa0kwR27c": "antin_-4Xa0kwR27c.wav",   # Talk @ Galerie eof, Paris 2011
}
# which source id(s) each track needs (so partial builds only fetch what they use)
TRACK_SOURCES = {
    1: ["TFqOlTQu_n4"], 2: ["hQAahBcyYhw"], 3: ["kgcMDnyObSs"], 4: ["7hLyj_CWjKU"],
    5: ["ViWPGQaPrwI"], 6: ["ViWPGQaPrwI"], 7: ["TFqOlTQu_n4"], 8: ["-4Xa0kwR27c"],
}

def bed(total_s):
    return np.zeros(int(total_s * k.SR))

# ---------- assets ----------
def check_deps(need_ytdlp=True, need_ffmpeg=True):
    missing = []
    if need_ytdlp and not shutil.which("yt-dlp"):
        missing.append("yt-dlp (pip install yt-dlp)")
    if need_ffmpeg and not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    if missing:
        sys.exit("ERROR: missing required tool(s) on PATH:\n  - " + "\n  - ".join(missing))

def download_sources(ids):
    for sid in ids:
        fn = SOURCES[sid]
        if os.path.exists(fn):
            print(f"  have {fn}")
            continue
        print(f"  downloading {fn}  (youtube:{sid}) ...")
        subprocess.run(
            ["yt-dlp", "--no-warnings", "-x", "--audio-format", "wav",
             "-o", f"antin_{sid}.%(ext)s", "--", sid],
            check=True,
        )

# ---------- mastering ----------
def master(base, title, num):
    """loudnorm to -14 LUFS, export tagged 320k mp3."""
    raw = f"{base}_raw.wav"
    mwav = f"{base}_master.wav"
    safe = title.replace("?", "").replace("/", "-")
    mp3 = f"{num:02d} - {safe}.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", mwav], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mwav, "-b:a", "320k",
                    "-metadata", f"title={num:02d} - {title}",
                    "-metadata", "artist=David Antin",
                    "-metadata", f"album={ALBUM}", mp3], check=True)
    print(f"  mastered -> {mp3}")

def finish(name, drums, voice_only, duck=0.33):
    N = min(len(drums), len(voice_only))
    drums, voice_only = drums[:N], voice_only[:N]
    drums = k.sidechain_duck(drums, voice_only, depth=duck)
    mix = k.master(drums + voice_only)
    k.write_wav(f"{name}_raw.wav", mix)
    print(f"  wrote {name}_raw.wav  ({N/k.SR:.1f}s)")

# ============================================================
# T1 — "would that count?"  (dream narrativity & desire)
# 72bpm 808 trap; opens cold on the deadpan "didn't seem too clever"
# ============================================================
def t1():
    print("T1 would that count?")
    t = Talk("antin_TFqOlTQu_n4.wav", hp=110)
    clever = t.grab(304.3, 307.7)   # "this didn't seem to me too clever an idea" — OPENER
    hook   = t.grab(0.0, 5.6)       # "...theory of narrative, which changes the nature of the game"
    verse  = t.grab(121.5, 179.4)   # crime story -> "nobody's desire is central to the shaping..."
    tail   = t.grab(307.3, 318.3)   # "...often accused of being unscientific"
    BPM = 72; BEAT, b = beat_grid(BPM)
    BARS = 38; total = b(BARS) + 2
    drums = bed(total)
    n_low, n_mid, n_high = k.make_808(36.7), k.make_808(49.0), k.make_808(55.0)
    clap, hat, hat_o = k.make_clap(), k.make_hat(), k.make_hat(0.12, open_=True)
    for bar in range(BARS):
        place(drums, n_low, b(bar, 0), 1.0)
        place(drums, n_mid, b(bar, 2.5), .85)
        if bar % 4 == 3: place(drums, n_high, b(bar, 3.5), .8)
        if bar % 2 == 1: place(drums, n_low, b(bar, 1.75), .7)
        if bar >= 4: place(drums, clap, b(bar, 2.0), .9)
        if bar >= 2:
            for kk in range(8):
                place(drums, hat, b(bar, kk * .5), .9 if kk % 2 == 0 else .6)
            if bar % 4 == 2:
                for kk in range(6): place(drums, hat, b(bar, 3.0) + kk * (BEAT / 8), .5)
            if bar % 8 == 7: place(drums, hat_o, b(bar, 3.5), .7)
    drums = np.tanh(drums * 1.1) * 0.95
    v = bed(total)
    place(v, clever, b(0, 1.0), 1.2)   # cold open
    place(v, hook,   b(4, 0), 1.15)
    place(v, verse,  b(10, 0), 1.2)    # the stick-up, floats past the bar lines
    place(v, tail,   b(32, 0), 1.15)
    N = min(len(drums), len(v)); drums, v = drums[:N], v[:N]
    env = k.lowpass(np.abs(v), 6); env = env / (np.max(env) or 1); duck = 1 - 0.35 * env
    intro = np.ones(N)
    g0, g1 = int(b(0) * k.SR), int(b(4) * k.SR)
    intro[g0:g1] = np.linspace(.15, .55, g1 - g0)   # pull the beat back under the cold open
    mix = k.master(drums * 0.85 * duck * intro + v)
    k.write_wav("t1_count_raw.wav", mix)
    print(f"  wrote t1_count_raw.wav  ({N/k.SR:.1f}s)")
    del t; gc.collect()

# ============================================================
# T2 — "demonstration of bones"  (The Black Plague)
# industrial: marching toms, metallic clangs, sub drone, distortion
# ============================================================
def t2():
    print("T2 demonstration of bones")
    t = Talk("antin_hQAahBcyYhw.wav", hp=120)
    bones = t.grab(28.6, 79.3)     # "a demonstration of bones cut through by a sore..."
    black = t.grab(98.7, 127.4)    # "pitch black powder... black bone black bone black"
    eye   = t.grab(143.6, 148.5)   # "why does the eye see a thing more clearly in dreams"
    BPM = 84; BEAT, b = beat_grid(BPM)
    BARS = 30; total = b(BARS) + 2
    drums = bed(total)
    sub = k.make_808(36.7, dur=1.0, glide=2.0, decay=2.0, sat=2.6)
    tomA, tomB = k.tom(98, .4), k.tom(146, .3)
    clang = k.metallic(520, .5, gain=.22); clang2 = k.metallic(330, .6, gain=.18)
    dr = k.drone([36, 43], total, detune=.012, gain=.16, lp=900)
    drums[:len(dr)] += dr
    for bar in range(BARS):
        place(drums, sub, b(bar, 0), 1.0)
        place(drums, sub, b(bar, 2.5), .8)
        # marching toms — relentless quarter feel with pickups
        for beat in (0, 1, 2, 3):
            place(drums, tomA if beat % 2 == 0 else tomB, b(bar, beat), .6)
        if bar % 2 == 1:
            place(drums, tomB, b(bar, 3.5), .5)
        # metallic clangs on the offbeats
        place(drums, clang, b(bar, 1.5), 1.0)
        if bar % 4 == 2:
            place(drums, clang2, b(bar, 3.0), 1.0)
    drums = k.saturate(drums, 1.3) * 0.92
    v = bed(total)
    place(v, bones, b(2, 0), 1.15)
    place(v, black, b(16, 0), 1.2)
    place(v, eye,   b(26, 0), 1.25)
    finish("t2_bones", drums, v, duck=.4)
    del t; gc.collect()

# ============================================================
# T3 — "twenty bucks for the refrigerator"  (Kathy Acker memoir)
# cinematic boom-bap: warm minor pad, vinyl crackle, kick/snare, sub
# ============================================================
def t3():
    print("T3 twenty bucks for the refrigerator")
    t = Talk("antin_kgcMDnyObSs.wav", hp=110)
    drive = t.grab(93.5, 152.9)    # 1968 desert drive -> "they killed Kennedy"
    fridge= t.grab(296.5, 320.9)   # Hitler photos -> "twenty bucks for the refrigerator"
    ny    = t.grab(324.6, 338.6)   # "if San Diego was America, what was New York?"
    BPM = 85; BEAT, b = beat_grid(BPM)
    BARS = 40; total = b(BARS) + 2
    drums = bed(total)
    kick, snare, hat = k.make_kick(), k.make_snare(), k.make_hat(0.05, tone=8000)
    sub = k.make_808(41.2, dur=.8, glide=2.5, decay=2.6, sat=2.0)  # E
    cr = k.crackle(total, density=1100, gain=.10); drums[:len(cr)] += cr
    # melancholy Am pad, changing every 4 bars: Am - F - C - G
    prog = [[57,60,64],[53,57,60],[48,52,55,60],[55,59,62]]
    for i, ch in enumerate(prog * (BARS // 16 + 1)):
        st = b(i * 4, 0)
        pad = k.chord(ch, BEAT * 16, wave="tri", a=.3, d=.4, s=.8, r=.6, gain=.12, lp=2400)
        place(drums, pad, st, 1.0)
        if st > total: break
    for bar in range(BARS):
        place(drums, sub, b(bar, 0), 1.0)
        place(drums, kick, b(bar, 0), .9)
        place(drums, kick, b(bar, 2.5), .7)
        place(drums, snare, b(bar, 1), .9)
        place(drums, snare, b(bar, 3), .9)
        for kk in range(8):
            place(drums, hat, b(bar, kk * .5), .5 if kk % 2 else .75)
    drums = k.saturate(drums, 1.05) * .9
    v = bed(total)
    place(v, drive,  b(4, 0), 1.15)
    place(v, fridge, b(26, 0), 1.2)
    place(v, ny,     b(36, 0), 1.2)
    finish("t3_refrigerator", drums, v, duck=.3)
    del t; gc.collect()

# ============================================================
# T4 — "the i and the id"  (Kelly Writers House, Freud/German)
# jazzy lounge: Rhodes chords, rim/brush swing, walking sub
# ============================================================
def t4():
    print("T4 the i and the id")
    t = Talk("antin_7hLyj_CWjKU.wav", hp=110)
    german = t.grab(116.0, 128.3)  # "screw this, I read German... I'm going to find out what he said"
    occ    = t.grab(132.3, 157.9)  # bizetsung / Lufthansa bathroom / army invests a city
    idd    = t.grab(168.5, 182.8)  # "what the hell is the id? It's Latin for id... the i and the id"
    BPM = 96; BEAT, b = beat_grid(BPM)
    swing = BEAT * 0.12
    BARS = 34; total = b(BARS) + 2
    drums = bed(total)
    rim, hat, kick = k.make_rim(), k.make_hat(0.04, tone=9000), k.make_kick(.25)
    # Rhodes ii-V-I-vi in C: Dm7 G7 Cmaj7 Am7
    prog = [[50,53,57,60],[43,47,53,57],[48,52,55,59],[45,48,52,55]]
    walk = [[38,40,41,43],[31,33,35,38],[36,38,40,43],[33,35,36,38]]
    for i in range(BARS):
        ch = prog[i % 4]
        for n in ch:
            place(drums, k.epiano(k.mtof(n), BEAT * 3.6, gain=.16), b(i, 0.5 if (i%2) else 0.0), 1.0)
        # walking sub bass, one note per beat
        for beat in range(4):
            wn = walk[i % 4][beat]
            place(drums, k.synth(k.mtof(wn), BEAT * .9, wave="sine", a=.005, d=.1, s=.6, r=.1, gain=.28), b(i, beat), 1.0)
        # brushed swing: rim on 2 & 4, hats in swung 8ths
        place(drums, rim, b(i, 1), .8); place(drums, rim, b(i, 3), .8)
        if i >= 2:
            place(drums, kick, b(i, 0), .7)
            for kk in range(4):
                place(drums, hat, b(i, kk), .55)
                place(drums, hat, b(i, kk + 0.5) + swing, .4)
    drums *= .85
    v = bed(total)
    place(v, german, b(2, 0), 1.15)
    place(v, occ,    b(12, 0), 1.15)
    place(v, idd,    b(26, 0), 1.2)
    finish("t4_id", drums, v, duck=.3)
    del t; gc.collect()

# ============================================================
# T5 — "think in yiddish"  (rethinking Freud)
# warm bright arpeggio synth, soft kick, shaker
# ============================================================
def t5():
    print("T5 think in yiddish")
    t = Talk("antin_ViWPGQaPrwI.wav", hp=110)
    nat  = t.grab(12.6, 43.3)      # "thinking knows no nationality... Yiddish... Hungarian... Russian"
    doc  = t.grab(102.9, 106.4)    # "he's a much better thinker than a doctor"
    poet = t.grab(262.9, 273.5)    # "the most brilliant German poets of the 20th century"
    BPM = 110; BEAT, b = beat_grid(BPM)
    BARS = 40; total = b(BARS) + 2
    drums = bed(total)
    kick, sh = k.make_kick(.22), k.shaker()
    sub = k.make_808(43.7, dur=.6, glide=2.0, decay=3.0, sat=1.8)
    # bright Dmaj-ish arpeggio: D F# A E, 16th notes
    arp = [62, 66, 69, 74, 76, 74, 69, 66]
    pad = k.chord([50, 57, 62, 66], total, wave="tri", a=.5, d=.5, s=.8, r=.8, gain=.07, lp=2600)
    drums[:len(pad)] += pad
    for bar in range(BARS):
        for s16 in range(8):
            n = arp[(bar * 8 + s16) % len(arp)]
            place(drums, k.synth(k.mtof(n), BEAT * .45, wave="tri", a=.005, d=.08, s=.4, r=.08, gain=.16, lp=4000), b(bar, s16 * .5), 1.0)
        if bar >= 4:
            place(drums, sub, b(bar, 0), .9)
            place(drums, kick, b(bar, 0), .7); place(drums, kick, b(bar, 2), .6)
            for kk in range(4):
                place(drums, sh, b(bar, kk + .5), .6)
    drums *= .85
    v = bed(total)
    place(v, nat,  b(4, 0), 1.1)
    place(v, doc,  b(24, 0), 1.2)
    place(v, poet, b(32, 0), 1.15)
    finish("t5_yiddish", drums, v, duck=.28)
    del t; gc.collect()

# ============================================================
# T6 — "full of happy cocaine"  (rethinking Freud)
# chopped & screwed: voice pitched DOWN, detuned drone, slow trap hats
# ============================================================
def t6():
    print("T6 full of happy cocaine")
    t = Talk("antin_ViWPGQaPrwI.wav", hp=90)
    coke = t.grab(106.0, 168.4)    # cocaine section -> "full of happy cocaine"
    coke = k.pitch_speed(coke, -4) # screwed: down a major third, slower
    coke = k.norm(coke, 0.95)
    BPM = 67; BEAT, b = beat_grid(BPM)
    BARS = 26; total = max(b(BARS) + 2, len(coke)/k.SR + b(3))
    drums = bed(total)
    sub = k.make_808(34.6, dur=1.1, glide=3.0, decay=1.8, sat=2.4)  # detuned low
    hat = k.make_hat(0.05, tone=7500)
    dr = k.drone([34, 41, 46], total, detune=.02, gain=.14, lp=1100)  # woozy detuned
    drums[:len(dr)] += dr
    for bar in range(int(total/(BEAT*4))):
        place(drums, sub, b(bar, 0), 1.0)
        if bar % 2 == 1: place(drums, sub, b(bar, 2.75), .7)
        # lazy triplet-ish hats with rolls
        for kk in range(4):
            place(drums, hat, b(bar, kk), .5)
        if bar % 4 == 3:
            for kk in range(6):
                place(drums, hat, b(bar, 3.0) + kk * (BEAT/6), .4)
    drums = k.saturate(drums, 1.1) * .9
    v = bed(total)
    place(v, coke, b(2, 0), 1.2)
    finish("t6_cocaine", drums, v, duck=.32)
    del t; gc.collect()

# ============================================================
# T7 — "the negative form of desire"  (dream narrativity)
# glitch/IDM: clicky perc, sine bleep arps, fast hats
# ============================================================
def t7():
    print("T7 the negative form of desire")
    t = Talk("antin_TFqOlTQu_n4.wav", hp=120)
    wish = t.grab(273.7, 307.4)    # "all dreams are wishful fulfillments... what about my nightmare?"
    vec  = t.grab(347.2, 367.0)    # "imagine it as a linear vector... the negative form of desire"
    BPM = 130; BEAT, b = beat_grid(BPM)
    BARS = 44; total = b(BARS) + 2
    drums = bed(total)
    rim, hat = k.make_rim(), k.make_hat(0.03, tone=10000)
    sub = k.make_808(49.0, dur=.4, glide=2.0, decay=3.5, sat=1.6)
    # sine bleep arpeggio (cold, mathy): pentatonic-ish
    bl = [72, 79, 75, 84, 77, 72, 80, 75]
    for bar in range(BARS):
        place(drums, sub, b(bar, 0), .9)
        if bar % 2: place(drums, sub, b(bar, 1.5), .6)
        # glitchy clicks (rim) on shifting 16ths
        for kk in (0, 3, 6, 7, 10, 11, 14):
            if (bar + kk) % 5 != 0:
                place(drums, rim, b(bar, kk * .25), .5)
        # fast hats
        for kk in range(16):
            place(drums, hat, b(bar, kk * .25), .35 if kk % 2 else .5)
        # bleep arp every other bar
        if bar % 2 == 0:
            for s16 in range(8):
                n = bl[(bar*4 + s16) % len(bl)]
                place(drums, k.bleep(n, .12, wave="sine", gain=.16), b(bar, s16 * .5), 1.0)
    drums *= .82
    v = bed(total)
    place(v, wish, b(4, 0), 1.15)
    place(v, vec,  b(26, 0), 1.2)
    finish("t7_desire", drums, v, duck=.3)
    del t; gc.collect()

# ============================================================
# T8 — "it is narrow it is dark"  (Galerie eof) — ambient closer
# long drone, deep sub pulses, chimes, reverb-drenched voice, no beat
# ============================================================
def t8():
    print("T8 it is narrow it is dark")
    t = Talk("antin_-4Xa0kwR27c.wav", hp=100)
    gorge = t.grab(103.4, 127.2)   # "it is narrow, it is dark, it is open... it is deep, it is shallow"
    exp   = t.grab(172.0, 176.6)   # "an experience is not a story necessarily, although it may be"
    gorge = k.reverb(gorge, decay=.5, mix=.35)
    exp   = k.reverb(exp, decay=.55, mix=.4)
    BPM = 60; BEAT, b = beat_grid(BPM)
    BARS = 26; total = b(BARS) + 4
    pad = bed(total)
    dr = k.drone([36, 43, 48, 55], total, detune=.01, gain=.18, lp=1600)
    pad[:len(dr)] += dr
    sub = k.make_808(36.7, dur=1.6, glide=1.5, decay=1.2, sat=2.0)
    for bar in range(0, BARS, 2):
        place(pad, sub, b(bar, 0), .8)              # deep pulse every 2 bars
    # sparse chimes drifting
    chime_notes = [84, 88, 91, 79, 86]
    for i in range(BARS):
        if i % 3 == 0:
            n = chime_notes[i % len(chime_notes)]
            ch = k.reverb(k.bleep(n, .5, wave="sine", gain=.12), decay=.5, mix=.4)
            place(pad, ch, b(i, rng.choice([0, 1.5, 2.5])), 1.0)
    pad *= .9
    v = bed(total)
    place(v, gorge, b(3, 0), 1.1)
    place(v, exp,   b(20, 0), 1.15)
    finish("t8_gorge", pad, v, duck=.15)
    del t; gc.collect()

# num -> (raw basename, title, build fn)
TRACKS = {
    1: ("t1_count",        "would that count?",                  t1),
    2: ("t2_bones",        "demonstration of bones",             t2),
    3: ("t3_refrigerator", "twenty bucks for the refrigerator",  t3),
    4: ("t4_id",           "the i and the id",                   t4),
    5: ("t5_yiddish",      "think in yiddish",                   t5),
    6: ("t6_cocaine",      "full of happy cocaine",              t6),
    7: ("t7_desire",       "the negative form of desire",        t7),
    8: ("t8_gorge",        "it is narrow it is dark",            t8),
}

def main():
    ap = argparse.ArgumentParser(description="Build the WOULD THAT COUNT? album.")
    ap.add_argument("tracks", nargs="*", type=int, help="track numbers (default: all 1-8)")
    ap.add_argument("--no-master", action="store_true", help="build raw WAVs only, skip ffmpeg")
    ap.add_argument("--skip-download", action="store_true", help="assume antin_*.wav already present")
    args = ap.parse_args()

    want = args.tracks or sorted(TRACKS)
    bad = [n for n in want if n not in TRACKS]
    if bad:
        sys.exit(f"no such track(s): {bad}  (valid: 1-8)")

    check_deps(need_ytdlp=not args.skip_download, need_ffmpeg=not args.no_master)

    print(f"=== {ALBUM} — building tracks {want} ===")
    if not args.skip_download:
        print("[1/2] assets")
        ids = sorted({sid for n in want for sid in TRACK_SOURCES[n]})
        download_sources(ids)

    print("[2/2] tracks")
    for n in want:
        base, title, fn = TRACKS[n]
        fn()
        if not args.no_master:
            master(base, title, n)
    print("done.")

if __name__ == "__main__":
    main()
