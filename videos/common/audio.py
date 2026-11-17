"""
Tonspur fuer das Lerntipps-Reel: Sprecherstimme (Piper TTS, Stimme "Thorsten", CC0)
+ selbst erzeugte Hintergrundmusik (keine Lizenzfragen) + Signalton pro Tipp.

Wird von render.py aufgerufen. Die Stimme wird beim ersten Lauf
automatisch heruntergeladen (~110 MB, in videos/.cache, nicht im Git).
"""
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

import numpy as np

SR = 44100
CACHE = Path(__file__).resolve().parent.parent / ".cache"
VOICE = "de_DE-thorsten-high"
VOICE_URL = ("https://huggingface.co/rhasspy/piper-voices/resolve/main/"
             "de/de_DE/thorsten/high/")

BPM = 84
MUSIC_VOL = 0.22      # Musik-Lautstaerke ohne Sprache
DUCK = 0.55           # Absenkung waehrend gesprochen wird (0..1)


# ----------------------------------------------------------------- Stimme
def ensure_voice():
    CACHE.mkdir(parents=True, exist_ok=True)
    model = CACHE / f"{VOICE}.onnx"
    for name in (f"{VOICE}.onnx", f"{VOICE}.onnx.json"):
        p = CACHE / name
        if not p.exists():
            print("Lade Stimme herunter:", name, flush=True)
            urllib.request.urlretrieve(VOICE_URL + name, p)
    return model


def read_wav(path):
    with wave.open(str(path)) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        x_new = np.arange(int(len(data) * SR / sr)) / SR
        data = np.interp(x_new, np.arange(len(data)) / sr, data)
    return data


def speak(text, out_path, model, length_scale=0.97):
    subprocess.run(
        [sys.executable, "-m", "piper", "-m", str(model), "-f", str(out_path),
         "--length-scale", str(length_scale), "--sentence-silence", "0.15"],
        input=text.encode(), check=True, stderr=subprocess.DEVNULL)
    return read_wav(out_path)


# ----------------------------------------------------------------- Musik
def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def tone(freq, dur, harmonics=(1.0,), detune=0.0):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for k, a in enumerate(harmonics, 1):
        s += a * np.sin(2 * np.pi * freq * k * t)
        if detune:
            s += a * np.sin(2 * np.pi * freq * k * (1 + detune) * t)
    return s


def add(buf, sig, start):
    i = int(start * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i: i + len(sig)] += sig


def make_music(total, tip_starts, drums_from):
    buf = np.zeros(int(total * SR) + SR)
    beat = 60 / BPM
    bar = 4 * beat
    # Cmaj7 - Am7 - Fmaj7 - G6 (ruhig, freundlich)
    chords = [[48, 55, 64, 71], [45, 52, 60, 67], [41, 48, 57, 64], [43, 50, 59, 64]]
    t, ci = 0.0, 0
    while t < total:
        ch = chords[ci % 4]
        # Flaechenklang
        dur = bar + 1.2
        n = int(dur * SR)
        env = np.minimum(1, np.arange(n) / (0.9 * SR)) * np.minimum(1, (n - np.arange(n)) / (1.2 * SR))
        for note in ch:
            add(buf, 0.05 * env * tone(midi(note), dur, (1, 0.35, 0.12), 0.003), t)
        # Bass
        bn = int(bar * SR)
        benv = np.exp(-np.arange(bn) / SR * 1.2)
        add(buf, 0.10 * benv * tone(midi(ch[0] - 12), bar, (1, 0.25)), t)
        # Arpeggio (Achtel)
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12]
        for k, note in enumerate(arp):
            at = t + k * beat / 2
            if at < 2.5:
                continue
            pn = int(0.6 * SR)
            penv = np.exp(-np.arange(pn) / SR * 7) * np.minimum(1, np.arange(pn) / 80)
            add(buf, 0.035 * penv * tone(midi(note), 0.6, (1, 0.3, 0.1)), at)
        # Schlagzeug (sanft), ab drums_from
        for b in range(4):
            bt = t + b * beat
            if bt < drums_from:
                continue
            if b in (0, 2):
                kn = int(0.35 * SR)
                kt = np.arange(kn) / SR
                f = 50 + 70 * np.exp(-kt * 25)
                kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-kt * 9)
                add(buf, 0.22 * kick, bt)
            hn = int(0.06 * SR)
            hat = np.random.default_rng(int(bt * 1000)).standard_normal(hn)
            hat = np.diff(hat, prepend=0) * np.exp(-np.arange(hn) / SR * 70)
            add(buf, 0.012 * hat, bt + beat / 2)
        t += bar
        ci += 1
    # Signalton bei jedem Tipp
    for st in tip_starts:
        for f, d in ((1567.98, 0), (2093.0, 0.07)):
            cn = int(1.2 * SR)
            cenv = np.exp(-np.arange(cn) / SR * 4.5)
            add(buf, 0.06 * cenv * tone(f, 1.2, (1, 0.15)), st + d)
    buf = buf[: int(total * SR)]
    # Ein-/Ausblenden
    fi, fo = int(0.8 * SR), int(2.5 * SR)
    buf[:fi] *= np.linspace(0, 1, fi)
    buf[-fo:] *= np.linspace(1, 0, fo)
    return buf / (np.abs(buf).max() + 1e-9)


# ----------------------------------------------------------------- Mischen
def build_audio(total, voice_lines, tip_starts, drums_from, out_wav):
    """voice_lines: Liste (startzeit_s, text)."""
    music = make_music(total, tip_starts, drums_from) * MUSIC_VOL
    voice = np.zeros_like(music)
    try:
        model = ensure_voice()
        tmp = CACHE / "line.wav"
        for start, text in voice_lines:
            seg = speak(text, tmp, model)
            room = len(voice) - int(start * SR)
            if len(seg) > room:
                print(f"Warnung: Sprechtext bei {start}s ist zu lang und wird abgeschnitten.")
            add(voice, seg * 0.9, start)
    except Exception as e:  # ohne Stimme trotzdem Musik liefern
        print("Stimme nicht verfuegbar, nur Musik:", e)

    # Ducking: Musik leiser, solange gesprochen wird
    win = int(0.25 * SR)
    env = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 6, 0, 1)
    smooth = int(0.3 * SR)
    env = np.convolve(env, np.ones(smooth) / smooth, mode="same")
    mix = music * (1 - DUCK * env) + voice
    mix /= np.abs(mix).max() + 1e-9
    mix *= 0.89

    pcm = (np.stack([mix, mix], axis=1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_wav
