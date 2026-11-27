"""
TikTok "3 Dinge": Stimme (Piper "Thorsten", männlich, deutsch), Beat-Musik, Effekte und Zeitplan.

    python3 tools/make_tiktok_audio.py
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "videos"))
from common.audio import SR, ensure_voice, speak, tone  # noqa: E402

EP = json.load(open(ROOT / "src" / "tiktok" / "episode.json", encoding="utf-8"))
FPS = EP["fps"]
OUT = ROOT / "public" / "assets" / "tiktok"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(5)


def save(path, x, gain=0.9):
    x = x / (np.abs(x).max() + 1e-9) * gain
    pcm = (np.stack([x, x], 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def add(buf, sig, start):
    i = int(start * SR)
    if i < 0 or i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig


# ------------------------------------------------------------ Effekte
def sfx_pop():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 18) + 250) / SR) * np.exp(-t * 18)


def sfx_tick():
    m = int(0.05 * SR)
    t = np.arange(m) / SR
    return np.sin(2 * np.pi * 1400 * t) * np.exp(-t * 90) + 0.5 * np.sin(2 * np.pi * 700 * t) * np.exp(-t * 60)


def sfx_scratch():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 600 + 2500 * np.abs(np.sin(2 * np.pi * 3.5 * t))
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return lowpass(saw, 3) * np.minimum(1, t / 0.02) * np.exp(-t * 3.5) + 0.3 * lowpass(rng.standard_normal(n), 2) * np.exp(-t * 6)


def sfx_buzzer():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    saw = 2 * ((110 * t) % 1) - 1
    return lowpass(saw, 4) * np.minimum(1, t / 0.01) * np.exp(-t * 3)


def sfx_ampel():
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 60)


def sfx_ding():
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1318.5 * t) + 0.4 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t * 4.5)


def sfx_whoosh():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    return lowpass(noise, 6) * np.sin(np.pi * t / 0.45) ** 2 + 0.3 * lowpass(noise, 60) * np.sin(np.pi * t / 0.45)


SFX = {"pop": (sfx_pop, 0.7), "tick": (sfx_tick, 0.5), "scratch": (sfx_scratch, 0.6), "buzzer": (sfx_buzzer, 0.45),
       "ampel": (sfx_ampel, 0.4), "ding": (sfx_ding, 0.55), "whoosh": (sfx_whoosh, 0.6)}
for name, (fn, g) in SFX.items():
    save(OUT / f"sfx-{name}.wav", fn(), g)


# ------------------------------------------------------------ Beat-Musik
def beat_music(total, bpm=118):
    n = int((total + 1) * SR)
    buf = np.zeros(n)
    beat = 60 / bpm
    roots = [55.0, 43.65, 65.41, 49.0]                      # A, F, C, G (Tiefe)
    arps = [[440, 523.3, 659.3], [349.2, 440, 523.3], [523.3, 659.3, 784], [392, 493.9, 587.3]]
    t, bar = 0.0, 0
    while t < total:
        root, arp = roots[bar % 4], arps[bar % 4]
        for b in range(4):
            bt = t + b * beat
            kn = int(0.3 * SR)
            kt = np.arange(kn) / SR
            add(buf, 0.9 * np.sin(2 * np.pi * np.cumsum(48 + 90 * np.exp(-kt * 28)) / SR) * np.exp(-kt * 9), bt)      # Kick
            if b in (1, 3) and bar >= 1:                                                                          # Clap
                cn = int(0.12 * SR)
                noise = lowpass(rng.standard_normal(cn), 2)
                add(buf, 0.35 * noise * np.exp(-np.arange(cn) / SR * 30), bt)
            for h in (0, 1):                                                                                      # Hi-Hat
                hn = int(0.05 * SR)
                hat = np.diff(rng.standard_normal(hn), prepend=0) * np.exp(-np.arange(hn) / SR * 90)
                add(buf, (0.16 if h else 0.09) * hat, bt + h * beat / 2)
            # Bass-Puls
            for h in (0, 1):
                dn = int(0.22 * SR)
                dt = np.arange(dn) / SR
                add(buf, 0.45 * (np.sin(2 * np.pi * root * dt) + 0.4 * lowpass(2 * ((root * dt) % 1) - 1, 5)) * np.exp(-dt * 7),
                    bt + h * beat / 2)
        # Pluck-Arpeggio
        for k in range(8):
            fr = arp[k % 3] * (2 if k % 4 == 3 else 1)
            pn = int(0.3 * SR)
            pt = np.arange(pn) / SR
            add(buf, 0.12 * (lowpass(2 * ((fr * pt) % 1) - 1, 6)) * np.exp(-pt * 9), t + k * beat / 2)
        t += 4 * beat
        bar += 1
    buf = buf[: int(total * SR)]
    fi, fo = int(0.3 * SR), int(0.5 * SR)
    buf[:fi] *= np.linspace(0, 1, fi)
    buf[-fo:] *= np.linspace(1, 0, fo)
    return buf


# ------------------------------------------------------------ Stimme + Zeitplan
model = ensure_voice()
tmp = ROOT.parent / "videos" / ".cache" / "line_tiktok.wav"
v = EP["voice"]


def chunks(text):
    toks, out, i = text.split(), [], 0
    while i < len(toks):
        c = toks[i]
        if len(c.strip(".,!?:")) <= 3 and i + 1 < len(toks) and c[-1] not in ".,!?:":
            c += " " + toks[i + 1]
            i += 1
        out.append(c)
        i += 1
    return out


scenes, lines, sfx_events = [], [], []
t_scene = 0.0
for sc in EP["scenes"]:
    prev_end = None
    sc_lines = []
    for ln in sc["lines"]:
        seg = speak(ln.get("say", ln["text"]), tmp, model, v["length"])
        nz = np.nonzero(np.abs(seg) > 0.02)[0]
        s0, s1 = (nz[0] / SR, nz[-1] / SR) if len(nz) else (0, len(seg) / SR)
        seg = seg[max(0, int((s0 - 0.03) * SR)):int((s1 + 0.08) * SR)]
        dur = len(seg) / SR - 0.11
        start = ln["at"] if prev_end is None else prev_end + ln.get("gap", 0.3)
        prev_end = start + dur
        idx = len(lines)
        name = f"line-{idx + 1:02d}.wav"
        save(OUT / name, seg, 0.92)
        ch = chunks(ln["text"])
        wts = [len(c) + (7 if c[-1] in ".?!:" else 3 if c[-1] == "," else 0) for c in ch]
        a_abs, acc, words = t_scene + start, 0.0, []
        for c, w in zip(ch, wts):
            words.append(dict(text=c, start=round((a_abs + dur * acc / sum(wts)) * FPS), end=round((a_abs + dur * (acc + w) / sum(wts)) * FPS),
                              hot=any(h.lower() in c.lower() for h in ln.get("hot", []))))
            acc += w
        rec = dict(id=idx + 1, scene=sc["id"], text=ln["text"], startFrame=round(a_abs * FPS), endFrame=round((a_abs + dur) * FPS),
                   relStart=round(start * FPS), relEnd=round((start + dur) * FPS), audio=f"assets/tiktok/{name}", words=words)
        lines.append(rec)
        sc_lines.append(rec)
    end_voice = prev_end
    length = max(sc["target"], end_voice + sc.get("minTail", 1.0))
    for s in sc["sfx"]:
        base = s.get("at")
        if "afterLine" in s:
            base = (sc_lines[s["afterLine"]]["relEnd"] / FPS) + s.get("offset", 0)
        for r in range(s.get("repeat", 1)):
            sfx_events.append(dict(file=f"assets/tiktok/sfx-{s['name']}.wav", frame=round((t_scene + base + r * s.get("every", 0)) * FPS),
                                   volume=SFX[s["name"]][1]))
    scenes.append(dict(id=sc["id"], startFrame=round(t_scene * FPS), endFrame=round((t_scene + length) * FPS),
                       lines=[dict(relStart=l["relStart"], relEnd=l["relEnd"]) for l in sc_lines]))
    t_scene += length

total = round(t_scene * FPS)
save(OUT / "music.wav", beat_music(total / FPS), 0.9)
json.dump(dict(fps=FPS, totalFrames=total, scenes=scenes, lines=lines, sfx=sfx_events, music="assets/tiktok/music.wav"),
          open(ROOT / "src" / "timelines" / "tiktok-3-dinge.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"Dauer {total / FPS:.1f} s ({total} Frames); Szenen:", [(s['id'], round(s['startFrame'] / FPS, 1), round(s['endFrame'] / FPS, 1)) for s in scenes])
print("Zeilen:", [(l['id'], round(l['startFrame'] / FPS, 1), round(l['endFrame'] / FPS, 1)) for l in lines])
