"""
Szene 1 "The Surprise Test": englische Frauenstimme (Piper "Amy"), betontes "SURPRISE TEST",
Dramatik-Effekt, Klassenzimmer-Atmosphaere und Zeitplan (src/timelines/surprise-test.json).

    python3 tools/make_scene_audio.py
"""
import json
import sys
import urllib.request
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "videos"))
from common.audio import CACHE, SR, add, read_wav, speak, tone  # noqa: E402

FPS = 30
OUT = ROOT / "public" / "assets" / "surprise-test"
VOICE = "en_US-amy-medium"
URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/"
rng = np.random.default_rng(11)


def ensure_voice():
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in (f"{VOICE}.onnx", f"{VOICE}.onnx.json"):
        if not (CACHE / name).exists():
            print("Lade Stimme:", name, flush=True)
            urllib.request.urlretrieve(URL + name, CACHE / name)
    return CACHE / f"{VOICE}.onnx"


def save(path, x, gain=0.9):
    x = x / (np.abs(x).max() + 1e-9) * gain
    pcm = (np.stack([x, x], 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def trim(seg, pad=0.02):
    nz = np.nonzero(np.abs(seg) > 0.02)[0]
    if not len(nz):
        return seg
    return seg[max(0, nz[0] - int(pad * SR)):nz[-1] + int(pad * SR)]


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


# ------------------------------------------------------------ Stimme
model = ensure_voice()
tmp = CACHE / "line_scene.wav"
p1 = trim(speak("Today, we're having a", tmp, model, 0.9))
p2 = trim(speak("surprise test!", tmp, model, 1.1))
f = 1.03                                            # "surprise test" etwas hoeher und lauter
p2 = np.interp(np.arange(int(len(p2) / f)) * f, np.arange(len(p2)), p2).astype(np.float32)
p2 = np.clip(p2 * 1.3, -1, 1)
gap = np.zeros(int(0.07 * SR), dtype=np.float32)
voice = np.concatenate([p1, gap, p2]).astype(np.float32)
n1, n2 = len(p1) / SR, len(p2) / SR
dur = len(voice) / SR

BEFORE = 0.9                                       # Sekunden Vorlauf (Blick, Augenbraue)
AFTER = 1.0                                        # Sekunden Haltepose
t0 = BEFORE
f0 = round(t0 * FPS)
f1 = round((t0 + dur) * FPS)
total = f1 + round(AFTER * FPS)
words_src = [("Today,", 0.0, n1 * 0.30), ("we're having a", n1 * 0.30, n1), ("SURPRISE TEST!", n1 + 0.07, dur)]
words = [dict(text=t, start=f0 + round(a * FPS), end=f0 + round(b * FPS), hot=(t.startswith("SURPRISE"))) for t, a, b in words_src]

blk = SR // FPS
rms = np.sqrt(np.convolve(voice ** 2, np.ones(blk) / blk, mode="same"))
ref = np.percentile(rms[rms > 0.01], 85)
env = [round(float(min(1, rms[min(len(rms) - 1, int(k / FPS * SR))] / ref)), 2) for k in range(f1 - f0 + 3)]

# ------------------------------------------------------------ Effekte
def sting():
    out = np.zeros(int(1.4 * SR))
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    out[:n] += 0.9 * np.sin(2 * np.pi * np.cumsum(95 * (1 + 1.2 * np.exp(-t * 20))) / SR) * np.exp(-t * 4)
    for at, notes, ln, amp in ((0.0, (174.6, 261.6, 349.2), 0.22, 0.5), (0.26, (155.6, 233.1, 311.1), 0.9, 0.8)):
        m = int(ln * SR)
        tt = np.arange(m) / SR
        env_ = np.minimum(1, tt / 0.01) * np.exp(-tt * (3 if ln > 0.5 else 8))
        for fr in notes:
            sig = lowpass(2 * ((fr * tt) % 1) - 1, 5) * env_
            i = int(at * SR)
            out[i:i + m] += amp * 0.35 * sig
    return out


def ambience(sec):
    n = int((sec + 0.5) * SR)
    t = np.arange(n) / SR
    room = lowpass(rng.standard_normal(n), 60) * 0.8
    murmur = lowpass(rng.standard_normal(n), 14) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t + 1.3)) ** 2 * 0.25
    amb = room + murmur
    for k in range(int(sec) + 1):                  # leises Ticken der Wanduhr
        m = int(0.02 * SR)
        click = np.sin(2 * np.pi * 1700 * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 220)
        add(amb, 0.55 * click, 0.4 + k * 1.0)
    return amb / (np.abs(amb).max() + 1e-9)


save(OUT / "voice.wav", voice, 0.9)
save(OUT / "sfx-sting.wav", sting(), 0.85)
save(OUT / "ambience.wav", ambience(total / FPS), 0.9)

sting_frame = f0 + round((n1 + 0.07) * FPS) - 1
cut1 = f0 - 3
cut2 = f1 + 2
sfx = [dict(file="assets/surprise-test/sfx-sting.wav", frame=sting_frame, volume=0.55),
       dict(file="assets/audio/sfx-whoosh.wav", frame=cut1 - 2, volume=0.4),
       dict(file="assets/audio/sfx-whoosh.wav", frame=cut2 - 2, volume=0.3)]
json.dump(dict(fps=FPS, totalFrames=total, cut1=cut1, cut2=cut2, voiceStart=f0, voiceEnd=f1, hotFrame=sting_frame,
               voice="assets/surprise-test/voice.wav", ambience="assets/surprise-test/ambience.wav",
               words=words, env=env, sfx=sfx),
          open(ROOT / "src" / "timelines" / "surprise-test.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"Dauer {total / FPS:.2f} s ({total} Frames), Stimme {dur:.2f} s ab {t0:.2f} s")
