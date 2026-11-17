"""Erzeugt die Stimmen für alle Vorlagen im Lernkarten-Studio.

  Mann (Frage, Überschrift): Piper TTS, Stimme "thorsten-medium"
  Frau (Antwort):            Chatterbox Multilingual, Klang nach referenz-frau.wav

Aufruf (aus diesem Ordner):
  python3 stimmen_erzeugen.py ../index.html ../stimmen.js

Voraussetzungen:
  pip install piper-tts chatterbox-tts faster-whisper   (PyTorch CPU reicht)
  ffmpeg
  ./voices/de_DE-thorsten-medium.onnx und .onnx.json
     von https://huggingface.co/rhasspy/piper-voices (Ordner de/de_DE/thorsten/medium)

Jede Antwort wird mit Whisper geprüft. Wenn die Erkennung nicht zum Text passt,
wird sie mit einem anderen Zufallswert neu erzeugt (bis zu 5 Versuche, die beste wird behalten).

Neue Themen: zuerst als Vorlage in PRESETS in index.html eintragen, dann dieses Skript ausführen.
Bereits vorhandene Aufnahmen in der Ausgabedatei werden wiederverwendet (--neu erzwingt alles neu).
"""
import base64, json, os, re, subprocess, sys, tempfile, wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.environ.get("VOICE_DIR", os.path.join(HERE, "voices"))
REF_FEMALE = os.path.join(HERE, "referenz-frau.wav")
TMP = tempfile.mkdtemp()


def read_presets(html_path):
    html = open(html_path, encoding="utf-8").read()
    block = html[html.index("const PRESETS"):html.index("const $ =")]
    titles = re.findall(r'title:\s*"([^"]+)"', block)
    lines = re.findall(r'^\s*"([^"]+\|[^"]*)",?\s*$', block, re.M)
    jobs = [("m", t[0].upper() + t[1:] + ".", t) for t in titles]
    for l in lines:
        parts = [p.strip() for p in l.split("|")]
        if len(parts) > 1 and parts[1]:
            jobs.append(("m", parts[1], parts[1]))
        if len(parts) > 2 and parts[2]:
            jobs.append(("f", parts[2], parts[2]))
    return jobs


# ---------- Mann: Piper ----------
_piper = None


def male_wav(text, out):
    global _piper
    from piper import PiperVoice, SynthesisConfig
    if _piper is None:
        _piper = PiperVoice.load(os.path.join(VOICE_DIR, "de_DE-thorsten-medium.onnx"))
    with wave.open(out, "wb") as wf:
        _piper.synthesize_wav(text, wf, syn_config=SynthesisConfig(length_scale=1.12))


# ---------- Frau: Chatterbox ----------
_cb = None


def female_wav(text, out, seed):
    global _cb
    import torch, torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    if _cb is None:
        torch.set_num_threads(os.cpu_count() or 4)
        _cb = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    torch.manual_seed(seed)
    w = _cb.generate(text, language_id="de", audio_prompt_path=REF_FEMALE,
                     exaggeration=0.4, cfg_weight=0.5, temperature=0.7)
    torchaudio.save(out, w, _cb.sr)


# ---------- Prüfung mit Whisper ----------
_asr = None


def spoken(text):
    """Zahlen als Wörter, damit die Stimme sie sicher richtig spricht: 38,5 -> achtunddreißig Komma fünf."""
    from num2words import num2words
    def rep(m):
        whole, frac = m.group(1), m.group(2)
        out = num2words(int(whole), lang="de")
        if frac:
            out += " Komma " + " ".join(num2words(int(d), lang="de") for d in frac)
        return out
    return re.sub(r"(\d+)(?:,(\d+))?", rep, text)


SAME = {"cairo": "kairo"}


def words(t):
    w = re.sub(r"[^\wäöüß ]", " ", spoken(t).lower().replace("-", " ")).split()
    return [SAME.get(x, x) for x in w]


def distance(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
    return d[-1]


def recognised_ok(path, text):
    global _asr
    from faster_whisper import WhisperModel
    if _asr is None:
        _asr = WhisperModel("small", device="cpu", compute_type="int8")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, dtype=np.float32)
    heard = " ".join(s.text for s in _asr.transcribe(x, language="de", beam_size=5)[0])
    return distance(words(heard), words(text)), heard.strip()


def to_mp3(src, dst):
    # trim silence at both ends, same loudness for both voices
    af = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
          "apad=pad_dur=0.05,loudnorm=I=-16:TP=-1.5:LRA=11")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ac", "1", "-ar", "44100",
                    "-b:a", "96k", dst], check=True)


def main():
    html_path, out_path = sys.argv[1], sys.argv[2]
    fresh = "--neu" in sys.argv
    old = {}
    if os.path.exists(out_path) and not fresh:
        s = open(out_path, encoding="utf-8").read()
        old = json.loads(s[s.index("{"):s.rindex("}") + 1])
    result = {}
    for i, (v, text, keytext) in enumerate(read_presets(html_path)):
        key = v + "|" + keytext
        if key in old:
            result[key] = old[key]
            continue
        wav, mp3 = f"{TMP}/{i}.wav", f"{TMP}/{i}.mp3"
        if v == "m":
            male_wav(text, wav)
        else:
            best = None
            for attempt in range(5):
                cand = f"{TMP}/{i}-{attempt}.wav"
                female_wav(spoken(text), cand, seed=1 + attempt)
                err, heard = recognised_ok(cand, text)
                if best is None or err < best[0]:
                    best = (err, cand)
                if err == 0:
                    break
                print(f"  Versuch {attempt + 1} passt nicht: „{heard}“", flush=True)
            os.replace(best[1], wav)
            if best[0]:
                print(f"  WARNUNG: beste Version hat noch {best[0]} Fehler – bitte anhören", flush=True)
        to_mp3(wav, mp3)
        result[key] = "data:audio/mpeg;base64," + base64.b64encode(open(mp3, "rb").read()).decode()
        print(f"{key}", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("/* Vorab erzeugte Stimmen: m = Mann (Piper, Thorsten), f = Frau (Chatterbox). "
                "Erzeugt mit werkzeuge/stimmen_erzeugen.py */\n")
        f.write("window.VOICE_CLIPS = " + json.dumps(result, ensure_ascii=False, indent=0) + ";\n")
    print(len(result), "Aufnahmen,", os.path.getsize(out_path) // 1024, "KB")


if __name__ == "__main__":
    main()
