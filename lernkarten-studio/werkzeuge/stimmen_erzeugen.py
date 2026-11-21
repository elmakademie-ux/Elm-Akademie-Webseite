"""Erzeugt die Stimmen für alle Vorlagen im Lernkarten-Studio.

  Mann: Piper TTS, Stimme "thorsten-medium"
        (spricht Piper einen Satz undeutlich: Chatterbox nach referenz-mann.wav)
  Frau: Chatterbox Multilingual, Klang nach referenz-frau.wav
  Wer fragt und wer antwortet, steht pro Vorlage in "roles" ("mf" oder "fm").

Aufruf (aus diesem Ordner):
  python3 stimmen_erzeugen.py ../index.html ../stimmen.js

Voraussetzungen:
  pip install piper-tts chatterbox-tts faster-whisper   (PyTorch CPU reicht)
  ffmpeg
  ./voices/de_DE-thorsten-medium.onnx und .onnx.json
     von https://huggingface.co/rhasspy/piper-voices (Ordner de/de_DE/thorsten/medium)

Jeder Satz wird mit Whisper geprüft. Wenn die Erkennung nicht zum Text passt,
wird sie mit einem anderen Zufallswert neu erzeugt (bis zu 5 Versuche, die beste wird behalten).

Neue Themen: zuerst als Vorlage in PRESETS in index.html eintragen, dann dieses Skript ausführen.
Bereits vorhandene Aufnahmen in der Ausgabedatei werden wiederverwendet (--neu erzwingt alles neu).
"""
import base64, json, os, re, subprocess, sys, tempfile, wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.environ.get("VOICE_DIR", os.path.join(HERE, "voices"))
REF_FEMALE = os.path.join(HERE, "referenz-frau.wav")
REF_MALE = os.path.join(HERE, "referenz-mann.wav")   # nur für Sätze, die Piper undeutlich spricht
TMP = tempfile.mkdtemp()


def read_presets(html_path):
    """Liest alle Vorlagen. roles: "mf" = Mann fragt, Frau antwortet; "fm" = umgekehrt."""
    html = open(html_path, encoding="utf-8").read()
    block = html[html.index("const PRESETS"):html.index("const $ =")]
    jobs, seen = [], set()

    def add(v, text, keytext):
        if (v, keytext) not in seen:
            seen.add((v, keytext))
            jobs.append((v, text, keytext))

    for m in re.finditer(r'title:\s*"([^"]+)"(.*?)items:\s*\[(.*?)\]', block, re.S):
        title, middle, items = m.group(1), m.group(2), m.group(3)
        if re.search(r'mode:\s*"dialog"', middle):
            # Dialog: Zeilen "Name: Satz"; Stimme nach male/female
            mn = re.search(r'male:\s*"([^"]*)"', middle); fn = re.search(r'female:\s*"([^"]*)"', middle)
            male, female = (mn.group(1).lower() if mn else ""), (fn.group(1).lower() if fn else "")
            order = []
            for l in re.findall(r'"([^"]+)"', items):
                mm = re.match(r"^([^:]{1,30}):\s*(.+)$", l)
                if not mm:
                    continue
                who, text = mm.group(1).strip().lower(), mm.group(2).strip()
                if who not in order:
                    order.append(who)
                v = "f" if who == female else "m" if who == male else ("f" if order.index(who) % 2 else "m")
                add(v, text, text)
            continue
        r = re.search(r'roles:\s*"(\w\w)"', middle)
        roles = r.group(1) if r else "mf"
        q, a = roles[0], roles[1]
        tv = re.search(r'titleVoice:\s*"([\w-])"', middle)   # "-" = Titel nicht vorlesen
        if not (tv and tv.group(1) == "-"):
            add(tv.group(1) if tv else q, title[0].upper() + title[1:] + ".", title)
        for l in re.findall(r'"([^"]+\|[^"]*)"', items):
            parts = [p.strip() for p in l.split("|")]
            if len(parts) > 1 and parts[1]:
                add(q, parts[1], parts[1])
            if len(parts) > 2 and parts[2]:
                add(a, parts[2], parts[2])
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


def chatterbox_wav(text, out, seed, ref):
    global _cb
    import torch, torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    if _cb is None:
        torch.set_num_threads(os.cpu_count() or 4)
        _cb = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    torch.manual_seed(seed)
    w = _cb.generate(text, language_id="de", audio_prompt_path=ref,
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
    # Buchstabieren: N-A-S-E-R-I -> En, A, Es, E, Er, I
    text = re.sub(r"\b[A-ZÄÖÜ](?:-[A-ZÄÖÜ])+\b",
                  lambda m: ", ".join(LETTERS[c] for c in m.group(0).split("-")), text)
    for short, said in SAY_AS.items():
        text = re.sub(r"\b" + re.escape(short) + r"\b", said, text)
    # Postleitzahl (5 Ziffern) Ziffer für Ziffer: 44135 -> vier vier eins drei fünf
    text = re.sub(r"\b(\d)\s?(\d)\s?(\d)\s?(\d)\s?(\d)\b",
                  lambda m: " ".join(num2words(int(d), lang="de") for d in m.groups()), text)
    return re.sub(r"(\d+)(?:,(\d+))?", rep, text)


LETTERS = {"A": "A", "B": "Be", "C": "Ce", "D": "De", "E": "E", "F": "Ef", "G": "Ge", "H": "Ha", "I": "I",
           "J": "Jott", "K": "Ka", "L": "El", "M": "Em", "N": "En", "O": "O", "P": "Pe", "Q": "Ku", "R": "Er",
           "S": "Es", "T": "Te", "U": "U", "V": "Vau", "W": "We", "X": "Ix", "Y": "Ypsilon", "Z": "Zett",
           "Ä": "Ä", "Ö": "Ö", "Ü": "Ü"}
SAY_AS = {"DTZ": "De Te Zett", "A2/B1": "A zwei, B eins"}   # Abkürzungen so, wie man sie spricht


SAME = {"cairo": "kairo", "baghdad": "bagdad", "autowerkstadt": "autowerkstatt", "jonas": "yonas", "bagdat": "bagdad", "sarah": "sara", "tschüs": "tschüss", "tschüß": "tschüss"}   # gleiche Aussprache, andere Schreibweise
VOCAB = ""   # Namen, Länder, Sprachen aus den Vorlagen, damit Whisper seltene Wörter kennt


def vocab_hint(jobs):
    names = set()
    for _, text, _ in jobs:
        for w in re.findall(r"(?<=[\s,])([A-ZÄÖÜ][a-zäöüß]+)", text):
            names.add(w)
    return ("Wörter: " + ", ".join(sorted(names)) + ".") if names else ""


def words(t):
    w = re.sub(r"[^\wäöüß ]", " ", spoken(t).lower().replace("-", " ")).split()
    w = [LETTERS.get(x.upper(), x).lower() if len(x) == 1 and x.isalpha() else x for x in w]   # einzelne Buchstaben
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
    # mehrere Dekodierungen: ein klarer Satz wird bei allen richtig erkannt
    total, worst = 0, ""
    for temp in (0.0, 0.4, 0.8):
        heard = " ".join(s.text for s in _asr.transcribe(x, language="de", beam_size=5, temperature=temp,
                                                         initial_prompt=VOCAB or None)[0])
        same = re.sub(r"[^a-zäöüß]", "", " ".join(words(heard))) == re.sub(r"[^a-zäöüß]", "", " ".join(words(text)))
        err = 0 if same else distance(words(heard), words(text))   # "Sprechenteil" = "Sprechen Teil"
        if err and not worst:
            worst = heard.strip()
        total += err
    return total, worst or heard.strip()


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
    global VOCAB
    result = {}
    jobs = read_presets(html_path)
    VOCAB = vocab_hint(jobs)
    for i, (v, text, keytext) in enumerate(jobs):
        key = v + "|" + keytext
        if key in old:
            result[key] = old[key]
            continue
        wav, mp3 = f"{TMP}/{i}.wav", f"{TMP}/{i}.mp3"
        best = None
        if v == "m":
            male_wav(spoken(text), wav)
            err, heard = recognised_ok(wav, text)
            best = (err, wav)
            if err:
                print(f"  Piper undeutlich: „{heard}“ – versuche Chatterbox im Thorsten-Klang", flush=True)
        if v == "f" or best[0]:
            ref = REF_FEMALE if v == "f" else REF_MALE
            for attempt in range(5):
                cand = f"{TMP}/{i}-{attempt}.wav"
                chatterbox_wav(spoken(text), cand, seed=1 + attempt, ref=ref)
                err, heard = recognised_ok(cand, text)
                if best is None or err < best[0]:
                    best = (err, cand)
                if err == 0:
                    break
                print(f"  Versuch {attempt + 1} passt nicht: „{heard}“", flush=True)
            if best[1] != wav:
                os.replace(best[1], wav)
            if best[0]:
                print(f"  WARNUNG: beste Version hat noch {best[0]} Fehler – bitte anhören", flush=True)
        to_mp3(wav, mp3)
        result[key] = "data:audio/mpeg;base64," + base64.b64encode(open(mp3, "rb").read()).decode()
        print(f"{key}", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("/* Vorab erzeugte Stimmen: m = Mann (Thorsten), f = Frau (Chatterbox). "
                "Erzeugt mit werkzeuge/stimmen_erzeugen.py */\n")
        f.write("window.VOICE_CLIPS = " + json.dumps(result, ensure_ascii=False, indent=0) + ";\n")
    print(len(result), "Aufnahmen,", os.path.getsize(out_path) // 1024, "KB")


if __name__ == "__main__":
    main()
