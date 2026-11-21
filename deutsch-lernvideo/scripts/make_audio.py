#!/usr/bin/env python3
"""Kostenlose Sprachausgabe mit Piper (lokal, offline, keine API, keine Kosten).

  python3 scripts/make_audio.py [A1 A2 B1 B2]

Voraussetzung: pip install piper-tts, Stimmen in .cache/ (siehe README, Abschnitt „Kostenlose Produktion“).
Schreibt audio/<N>/<LineID>_<speaker>.wav und audio/<N>/durations.json (echte Dauern -> build.py).
Stimmen: Mia = ramona, Jonas = thorsten (CC0), Erzähler = karlsson. Lizenzen der M-AILABS-Stimmen vor
kommerzieller Nutzung prüfen.
"""
import sys
import wave

import numpy as np
from piper import PiperVoice, SynthesisConfig

from lib import *  # noqa: F401,F403

CACHE = ROOT / ".cache"
MODELS = {"mia": "de_DE-ramona-low", "jonas": "de_DE-thorsten-medium", "narrator": "de_DE-karlsson-low"}
# length_scale > 1 = langsamer
LENGTH = {"A1": 1.3, "A2": 1.12, "B1": 1.0, "B2": 0.96}
GAIN = {"mia": 1.0, "jonas": 1.0, "narrator": 1.0}


def trim(x, sr, thr=0.01, keep=0.06):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(keep * sr))
    b = min(len(x), idx[-1] + int(keep * sr))
    return x[a:b]


def synth(voice, text, scale):
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        voice.synthesize_wav(text, w, SynthesisConfig(length_scale=scale, noise_scale=0.6, noise_w_scale=0.7))
    buf.seek(0)
    with wave.open(buf) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return x, sr


def main():
    levels = sys.argv[1:] or LEVELS
    voices = {k: PiperVoice.load(str(CACHE / f"{m}.onnx")) for k, m in MODELS.items()}
    lex = load_lexicon()
    for lv in levels:
        script = load_script(lv)
        out = ROOT / "audio" / lv
        out.mkdir(parents=True, exist_ok=True)
        durs = {}
        for s in script["scenes"]:
            for i, ln in enumerate(s["lines"]):
                lid = line_id(s, i)
                sp = ln["speaker"]
                x, sr = synth(voices[sp], tts_text(ln["text"], lex), LENGTH[lv])
                x = trim(x, sr)
                peak = np.abs(x).max() + 1e-9
                x = x / peak * 0.85 * GAIN[sp]
                path = out / f"{lid}_{sp}.wav"
                with wave.open(str(path), "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
                    w.writeframes((x * 32767).astype(np.int16).tobytes())
                durs[lid] = round(len(x) / sr, 3)
        save_json(out / "durations.json", durs)
        print(f"{lv}: {len(durs)} Zeilen, Sprechzeit gesamt {sum(durs.values()):.0f} s")


if __name__ == "__main__":
    main()
