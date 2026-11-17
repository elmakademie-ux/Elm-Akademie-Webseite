"""Erzeugt die Stimmen (Mann fragt, Frau antwortet) für alle Vorlagen im Lernkarten-Studio.

Aufruf:  python3 stimmen_erzeugen.py ../index.html kerstin-low ../stimmen.js
Voraussetzungen: pip install piper-tts, ffmpeg, und im Ordner ./voices die Piper-Stimmen
de_DE-thorsten-medium.onnx(.json) und de_DE-kerstin-low.onnx(.json)
von https://huggingface.co/rhasspy/piper-voices (Ordner de/de_DE).
Neue Themen: zuerst als Vorlage in PRESETS in index.html eintragen, dann dieses Skript ausführen.
"""
import re, sys, json, wave, base64, subprocess, os, tempfile
VOICE_DIR = os.environ.get("VOICE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "voices"))
CLIP_DIR = tempfile.mkdtemp()
from piper import PiperVoice, SynthesisConfig
html = open(sys.argv[1]).read()
block = html[html.index("const PRESETS"):html.index("const $ =")]
titles = re.findall(r'title:\s*"([^"]+)"', block)
lines = re.findall(r'^\s*"([^"]+\|[^"]*)",?\s*$', block, re.M)
V = {"m": PiperVoice.load(os.path.join(VOICE_DIR, "de_DE-thorsten-medium.onnx")),
     "f": PiperVoice.load(os.path.join(VOICE_DIR, "de_DE-" + sys.argv[2] + ".onnx"))}
def fix_cedilla(voice):
    if "\u0327" in voice.config.phoneme_id_map: return
    orig = voice.phonemize
    def ph(text):
        out = []
        for sent in orig(text):
            merged = []
            for p in sent:
                if p == "\u0327" and merged and merged[-1] == "c": merged[-1] = "ç"
                else: merged.append(p)
            out.append(merged)
        return out
    voice.phonemize = ph
for vv in V.values(): fix_cedilla(vv)
cfg = SynthesisConfig(length_scale=1.12)
jobs = [("m", t[0].upper()+t[1:] + ".", t) for t in titles]
for l in lines:
    parts = [p.strip() for p in l.split("|")]
    if len(parts) > 1 and parts[1]: jobs.append(("m", parts[1], parts[1]))
    if len(parts) > 2 and parts[2]: jobs.append(("f", parts[2], parts[2]))
out = {}
os.makedirs(CLIP_DIR, exist_ok=True)
for i,(v,text,keytext) in enumerate(jobs):
    w = f"{CLIP_DIR}/{i}.wav"; m = f"{CLIP_DIR}/{i}.mp3"
    with wave.open(w, "wb") as wf: V[v].synthesize_wav(text, wf, syn_config=cfg)
    subprocess.run(["ffmpeg","-v","error","-y","-i",w,"-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.05","-ac","1","-ar","24000","-b:a","48k",m],check=True)
    key = v + "|" + keytext
    out[key] = "data:audio/mpeg;base64," + base64.b64encode(open(m,"rb").read()).decode()
open(sys.argv[3],"w").write("/* Vorab erzeugte Stimmen: m = Mann (fragt), f = Frau (antwortet). Erzeugt mit Piper TTS. */\nwindow.VOICE_CLIPS = " + json.dumps(out, ensure_ascii=False, indent=0) + ";\n")
print(len(out), "clips", os.path.getsize(sys.argv[3])//1024, "KB")
