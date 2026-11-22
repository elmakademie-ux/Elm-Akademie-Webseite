"""
Erzeugt aus src/episode.json:
  public/assets/audio/line-XX.wav   Stimmen (Piper "Thorsten"; Lehrer tiefer, Schüler höher)
  public/assets/audio/sfx-*.wav     Comedy-Soundeffekte (selbst synthetisiert)
  public/assets/audio/music.wav     Hintergrundmusik (selbst erzeugt, keine Lizenzfragen)
  src/timeline.json                 Zeitplan in Frames (Zeilen, Wörter, Lautstärke, Schnitte, Effekte)

    python3 tools/make_audio.py <episode-id>      (Standard: classroom-comedy)
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "videos"))
from common.audio import SR, ensure_voice, make_music, speak, tone  # noqa: E402

EID = next((a for a in sys.argv[1:] if not a.startswith("-")), "classroom-comedy")
EP = json.load(open(ROOT / "src" / "episodes" / f"{EID}.json", encoding="utf-8"))
FPS = EP["fps"]
SFX_DIR = ROOT / "public" / "assets" / "audio"          # Effekte gemeinsam fuer alle Episoden
OUT = SFX_DIR / EID                                       # Stimmen und Musik je Episode
OUT.mkdir(parents=True, exist_ok=True)
LANG = EP.get("language", "de")
if LANG == "de":
    VOICES = {"teacher": dict(pitch=0.93, length=0.93), "student": dict(pitch=1.13, length=1.10)}
else:   # Englisch: zwei Piper-Maennerstimmen (Lehrer tiefer, Schueler heller)
    VOICES = {"teacher": dict(pitch=0.93, length=0.95), "student": dict(pitch=1.06, length=1.0)}
rng = np.random.default_rng(7)


def save(path, x, gain=0.9):
    x = x / (np.abs(x).max() + 1e-9) * gain
    pcm = (np.stack([x, x], 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------ Soundeffekte
def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def sfx_whoosh():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    sweep = lowpass(noise, 6) * np.sin(np.pi * t / 0.45) ** 2
    return sweep + 0.3 * lowpass(noise, 60) * np.sin(np.pi * t / 0.45)


def sfx_gasp():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 1.5
    return np.diff(rng.standard_normal(n), prepend=0) * lowpass(rng.standard_normal(n), 4) * env


def sfx_boing():
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    f = 300 + 260 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 4) + 120 * np.exp(-t * 3)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)


def sfx_alarm():
    out = np.zeros(int(1.25 * SR))
    for rep in range(2):
        for k in range(4):
            at = int((rep * 0.62 + k * 0.1) * SR)
            tn = tone(2350, 0.055, (1, 0.35))
            out[at:at + len(tn)] += np.sin(np.pi * np.arange(len(tn)) / len(tn)) * tn
    return out


def sfx_rimshot():
    out = np.zeros(int(1.4 * SR))
    for dt, f in ((0, 125), (0.17, 98)):
        n = int(0.3 * SR)
        t = np.arange(n) / SR
        k = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.4 * np.exp(-t * 22))) / SR) * np.exp(-t * 10)
        out[int(dt * SR):int(dt * SR) + n] += 0.9 * k
    for dt, dec, amp in ((0.36, 3.0, 0.45), (0.19, 14.0, 0.25)):
        n = int(0.9 * SR)
        noise = np.diff(rng.standard_normal(n), prepend=0) * np.exp(-np.arange(n) / SR * dec)
        out[int(dt * SR):int(dt * SR) + n] += amp * noise[:len(out) - int(dt * SR)]
    return out


def sfx_womp():
    out = np.zeros(int(1.9 * SR))
    for dt, f0, f1, ln in ((0.0, 233, 220, 0.4), (0.45, 208, 196, 0.4), (0.9, 185, 175, 0.4), (1.35, 165, 120, 0.5)):
        n = int(ln * SR)
        t = np.arange(n) / SR
        f = np.linspace(f0, f1, n) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
        saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
        out[int(dt * SR):int(dt * SR) + n] += lowpass(saw, 6) * np.minimum(1, t / 0.03) * np.exp(-t * 2.2)
    return out


def sfx_ding():
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1318.5 * t) + 0.4 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 4.5)


def sfx_slam():
    n = int(0.8 * SR)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * np.cumsum(90 * (1 + 2.0 * np.exp(-t * 30))) / SR) * np.exp(-t * 7)
    crack = lowpass(rng.standard_normal(n), 3) * np.exp(-t * 40)
    return thump + 0.8 * crack


SFX = {"ding": (sfx_ding, 0.5), "slam": (sfx_slam, 0.8), "whoosh": (sfx_whoosh, 0.55), "gasp": (sfx_gasp, 0.4), "boing": (sfx_boing, 0.5),
       "alarm": (sfx_alarm, 0.45), "rimshot": (sfx_rimshot, 0.75), "womp": (sfx_womp, 0.6)}
for name, (fn, gain) in SFX.items():
    save(SFX_DIR / f"sfx-{name}.wav", fn(), gain)


# ------------------------------------------------------------ Stimmen
def chunks(text):
    toks, out, i = text.split(), [], 0
    while i < len(toks):
        c = toks[i]
        if len(c.strip(".,!?")) <= 3 and i + 1 < len(toks) and c[-1] not in ".,!?":
            c += " " + toks[i + 1]
            i += 1
        out.append(c)
        i += 1
    return out


def ensure_en(name):
    import urllib.request
    from common.audio import CACHE
    CACHE.mkdir(parents=True, exist_ok=True)
    spk = name.split("-")[1]
    base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/{spk}/medium/"
    for f in (f"{name}.onnx", f"{name}.onnx.json"):
        if not (CACHE / f).exists():
            print("Lade Stimme:", f, flush=True)
            urllib.request.urlretrieve(base + f, CACHE / f)
    return CACHE / f"{name}.onnx"


def ensure_named(name):
    """Piper-Stimme nach Namen laden, z. B. 'de_DE-ramona-low' oder 'en_US-amy-medium'."""
    import urllib.request
    from common.audio import CACHE
    CACHE.mkdir(parents=True, exist_ok=True)
    lang_region, speaker, quality = name.split("-")
    base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{lang_region.split('_')[0]}/{lang_region}/{speaker}/{quality}/"
    for f in (f"{name}.onnx", f"{name}.onnx.json"):
        if not (CACHE / f).exists():
            print("Lade Stimme:", f, flush=True)
            urllib.request.urlretrieve(base + f, CACHE / f)
    return CACHE / f"{name}.onnx"


if "voices" in EP:      # eigene Stimmen je Episode: {"teacher": {"model": ..., "pitch": 1.0, "length": 1.0}, ...}
    MODELS = {k: ensure_named(v["model"]) for k, v in EP["voices"].items()}
    VOICES = {k: dict(pitch=v.get("pitch", 1.0), length=v.get("length", 1.0)) for k, v in EP["voices"].items()}
elif LANG == "de":
    MODELS = {"teacher": ensure_voice(), "student": ensure_voice()}
else:
    MODELS = {"teacher": ensure_en("en_US-ryan-medium"), "student": ensure_en("en_US-joe-medium")}
tmp = ROOT.parent / "videos" / ".cache" / "line_remotion.wav"
t = EP["start"]
lines, sfx_events, shots = [], [], []
for i, ln in enumerate(EP["lines"]):
    v = VOICES[ln["who"]]
    seg = speak(ln.get("say", ln["text"]), tmp, MODELS[ln["who"]], v["length"])
    if ln.get("loud"):                      # Schreien: lauter und etwas hoeher
        seg = np.clip(seg * 1.35, -1, 1)
    f = v["pitch"]
    seg = np.interp(np.arange(int(len(seg) / f)) * f, np.arange(len(seg)), seg).astype(np.float32)
    nz = np.nonzero(np.abs(seg) > 0.02)[0]
    s0, s1 = (nz[0] / SR, nz[-1] / SR) if len(nz) else (0, len(seg) / SR)
    seg = seg[max(0, int((s0 - 0.03) * SR)):int((s1 + 0.08) * SR)]
    name = f"line-{i + 1:02d}.wav"
    save(OUT / name, seg, 0.9)
    t += ln.get("pauseBefore", 0)
    dur = len(seg) / SR - 0.11
    a, b = round(t * FPS), round((t + dur) * FPS)
    blk = SR // FPS
    rms = np.sqrt(np.convolve(seg ** 2, np.ones(blk) / blk, mode="same"))
    ref = np.percentile(rms[rms > 0.01], 85) if (rms > 0.01).any() else 1
    env = [round(float(min(1, rms[int((k / FPS + 0.03) * SR)] / ref)), 2) if int((k / FPS + 0.03) * SR) < len(rms) else 0
           for k in range(b - a + 3)]
    ch = chunks(ln["text"])
    wts = [len(c) + (7 if c[-1] in ".?!" else 3 if c[-1] == "," else 0) for c in ch]
    acc, words = 0.0, []
    for c, w in zip(ch, wts):
        words.append(dict(text=c, start=a + round((b - a) * acc / sum(wts)), end=a + round((b - a) * (acc + w) / sum(wts))))
        acc += w
    lines.append(dict(id=i + 1, who=ln["who"], pose=ln["pose"], text=ln["text"], startFrame=a, endFrame=b,
                      audio=f"assets/audio/{EID}/{name}", words=words, env=env))
    for s in ln.get("sfx", []):
        at = (t + dur + ln.get("sfxAfterEnd", 0)) if s == "rimshot" else (t + ln.get("sfxDelay", 0))
        sfx_events.append(dict(file=f"assets/audio/sfx-{s}.wav", frame=round(at * FPS), volume=SFX[s][1]))
    t += dur + EP["pause"]

react = round((t - EP["pause"] + 0.2) * FPS)
total = react + round((EP["reactionSeconds"] + EP["outroSeconds"]) * FPS)
outro = react + round(EP["reactionSeconds"] * FPS)
for s in EP["reaction"].get("sfx", []):
    sfx_events.append(dict(file=f"assets/audio/sfx-{s}.wav", frame=react + 6, volume=SFX[s][1]))

# Schnitte: jede Zeile ein Bild, danach die Reaktion; vor jedem Schnitt ein Whoosh
cut_lead = 5
for k, ln in enumerate(lines):
    start = 0 if k == 0 else max(lines[k - 1]["endFrame"] + 1, ln["startFrame"] - cut_lead)
    shots.append(dict(pose=ln["pose"], who=ln["who"], startFrame=start))
shots.append(dict(pose=EP["reaction"]["pose"], who="teacher", startFrame=react))
for k, s in enumerate(shots):
    s["endFrame"] = shots[k + 1]["startFrame"] if k + 1 < len(shots) else outro
    if k:
        sfx_events.append(dict(file="assets/audio/sfx-whoosh.wav", frame=s["startFrame"] - 2, volume=SFX["whoosh"][1]))

music = make_music(total / FPS, [], 9999)
save(OUT / "music.wav", music, 0.9)
json.dump(dict(fps=FPS, totalFrames=total, reactionFrame=react, outroFrame=outro, lines=lines, shots=shots,
               sfx=sfx_events, stickers=EP["reaction"].get("stickers", [])),
          open(ROOT / "src" / "timelines" / f"{EID}.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"Dauer {total / FPS:.1f} s ({total} Frames), {len(lines)} Zeilen, {len(sfx_events)} Effekte")
