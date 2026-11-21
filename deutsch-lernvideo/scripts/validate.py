#!/usr/bin/env python3
"""Qualitätssicherung für alle Drehbücher.

Prüft: Struktur/Vollständigkeit, GER-Niveau (Satzlänge, Konnektoren), Figuren-
Einheitlichkeit in den Prompts, Rechtschreib-/Typografie-Muster, Aussprache-
risiken, Untertitel-Synchronität und Lesetempo.

Aufruf:  python3 scripts/validate.py [A1 ...]      Exit-Code 1 bei Fehlern.
Hinweis: Das ersetzt KEIN muttersprachliches Lektorat und keine Hörprobe.
"""
import re
import sys

from lib import *  # noqa: F401,F403

REQUIRED_TYPES_ORDER = ["hook", "intro", "dialog", "vocab", "grammar", "exercise", "outro"]
DIRECTION_KEYS = ["camera", "lighting", "animation", "music"]
MAX_WORDS = {"A1": 10, "A2": 20, "B1": 30, "B2": 45}
MAX_CPS = {"A1": 13, "A2": 15, "B1": 18, "B2": 21}  # Zeichen pro Sekunde (Untertitel)
A1_FORBIDDEN = ["weil", "obwohl", "dass", "wenn", "denn", "deshalb", "trotzdem", "außerdem"]
REQUIRED_WORDS = {
    "A1": ["hallo", "guten morgen", "wie heißt du", "ich heiße", "woher kommst du", "ich komme aus", "freut mich"],
    "A2": ["weil", "wenn", "seit", "obwohl", "woher kommst du", "wo wohnst du"],
    "B1": ["weil", "obwohl", "deshalb", "trotzdem", "außerdem", "denn", "meiner meinung nach", "das ,"],
    "B2": ["allerdings", "sofern", "wären sie", "würde", "visitenkarte", "zusammenarbeit", "guten tag", "herr keller", "frau navarro"],
}
# häufige Fehler (Regex, Hinweis)
SPELL_PATTERNS = [
    (r"\s{2,}", "doppeltes Leerzeichen"),
    (r"\s[,.!?;:]", "Leerzeichen vor Satzzeichen"),
    (r"\"", "gerade Anführungszeichen – bitte „…“ verwenden"),
    (r"\.\.\.", "drei Punkte – bitte …"),
    (r"\bdas\s+selbe\b|\bim\s+selben\b", "dasselbe zusammen schreiben"),
    (r"\bstandart", "Standard"),
    (r"\bvielleicht\s+vieleicht", "Tippfehler"),
    (r"\bmitlerweile\b", "mittlerweile"),
    (r"\bgrad(e)?aus\b", "geradeaus"),
    (r"\bwiederspiegel", "widerspiegeln"),
    (r"\bTschüs\b", "Schreibung: Tschüss (einheitlich)"),
    (r"\bzu\s*Hause\b|\bnach\s*Hause\b", "prüfen: zu Hause / nach Hause"),
]


def err(errors, level, where, msg):
    errors.append(f"[{level}] {where}: {msg}")


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?:])\s+", text) if s.strip()]


def check_level(level):
    errors, warns = [], []
    script = load_script(level)
    chars = load_characters()
    lex = load_lexicon()
    voices = load_voices()
    wpm, gap = speaking_params(level)

    # 1) Struktur
    types = [s["type"] for s in script["scenes"]]
    order = [REQUIRED_TYPES_ORDER.index(t) for t in types]
    if order != sorted(order):
        err(errors, level, "Aufbau", f"Szenenfolge nicht Hook→Intro→Dialoge→Wortschatz→Grammatik→Übung→Abschluss: {types}")
    for t in REQUIRED_TYPES_ORDER:
        if t not in types:
            err(errors, level, "Aufbau", f"Szenentyp fehlt: {t}")
    ids = [s["id"] for s in script["scenes"]]
    if len(ids) != len(set(ids)):
        err(errors, level, "Aufbau", "doppelte Szenen-IDs")
    for k in ["vocabulary", "grammar", "exercise"]:
        if not script.get(k):
            err(errors, level, k, "fehlt oder leer")
    full_text = []
    speakers_in_dialog = set()
    for s in script["scenes"]:
        w = s["id"]
        if not s["id"].startswith(level + "-"):
            err(errors, level, w, "ID passt nicht zum Niveau")
        for k in ["title", "location", "description", "visual"]:
            if not s.get(k):
                err(errors, level, w, f"Feld fehlt: {k}")
        for k in ("location", "camera", "lighting"):
            if not s.get("prompt_en", {}).get(k):
                err(errors, level, w, f"prompt_en.{k} (englischer Prompt-Text) fehlt")
        for k in DIRECTION_KEYS:
            if not s.get("direction", {}).get(k):
                err(errors, level, w, f"Regieanweisung fehlt: {k}")
        if not s.get("lines"):
            err(errors, level, w, "keine Sprechzeilen")
        for c in s["characters"]:
            if c not in chars["characters"]:
                err(errors, level, w, f"unbekannte Figur {c}")
        for i, ln in enumerate(s["lines"]):
            lw = line_id(s, i)
            if ln["speaker"] not in voices["roles"]:
                err(errors, level, lw, f"Sprecher ohne Stimme: {ln['speaker']}")
            if ln["speaker"] != "narrator" and ln["speaker"] not in s["characters"]:
                err(errors, level, lw, f"Sprecher {ln['speaker']} ist nicht in der Szene aufgeführt")
            if s["type"] == "dialog":
                speakers_in_dialog.add(ln["speaker"])
            t = ln["text"]
            full_text.append(t)
            if not re.search(r"[.!?…“]$", t):
                err(errors, level, lw, "Satz endet ohne Satzzeichen")
            if t[0].islower() and s["type"] != "vocab":
                err(errors, level, lw, "beginnt klein")
            if t.count("„") != t.count("“"):
                err(errors, level, lw, "„“ nicht ausgeglichen")
            for pat, msg in SPELL_PATTERNS:
                if re.search(pat, t):
                    (warns if msg.startswith("prüfen") else errors).append(f"[{level}] {lw}: {msg}")
            # GER-Niveau
            for sent in sentences(t):
                n = word_count(sent)
                if n > MAX_WORDS[level]:
                    err(errors, level, lw, f"Satz zu lang für {level} ({n} Wörter > {MAX_WORDS[level]}): {sent}")
            if level == "A1" and s["type"] != "grammar":
                low = t.lower()
                for bad in A1_FORBIDDEN:
                    if re.search(rf"\b{bad}\b", low):
                        err(errors, level, lw, f"Konnektor „{bad}“ ist für A1 zu schwer")
            # Aussprache
            if re.search(r"\d", tts_text(t, lex)):
                err(errors, level, lw, "Ziffern im Sprechtext – Zahlen ausschreiben")
            for tok in re.findall(r"\b[A-ZÄÖÜ]{2,}[a-zäöü]*[A-ZÄÖÜ]*\b", t):
                if tok not in lex and not tok.isdigit():
                    warns.append(f"[{level}] {lw}: Abkürzung „{tok}“ ohne Eintrag in audio/pronunciation.json")
            for key in lex:
                if key in t and tts_text(t, lex) == t and lex[key] != key:
                    err(errors, level, lw, f"Lexikon-Eintrag „{key}“ wurde nicht angewendet")
            # Du/Sie-Konsistenz in Figuren-Dialogen
            if ln["speaker"] != "narrator" and s["type"] == "dialog":
                low = " " + t.lower() + " "
                if script["form_of_address"] == "du" and re.search(r"(?<=[\wäöüß,] )Sie\b|\bIhnen\b|\bIhr(e|en|em)?\b", t):
                    err(errors, level, lw, "Sie-Form in einem „du“-Video")
                if script["form_of_address"] == "Sie" and re.search(r"\b(du|dich|dir|dein|deine)\b", low):
                    err(errors, level, lw, "du-Form in einem „Sie“-Video")
        # Prompt-Prüfung: Figurenblöcke, verbotene Abweichungen
        p = scene_prompt(script, s, chars, wpm, gap)["prompt"]
        for c in s["characters"]:
            cd = chars["characters"][c]
            if "appearance" in cd and cd["appearance"] not in p:
                err(errors, level, w, f"Prompt enthält Figurenbeschreibung von {c} nicht")
        v = (s["visual"] + " " + " ".join(s["prompt_en"].values())).lower()
        for bad in [r"blazer", r"\bsuit\b", r"jacket", r"\bhat\b", r"glasses", r"beard", r"ponytail", r"blonde", r"red hair", r"uniform"]:
            if re.search(bad, v):
                err(errors, level, w, f"Figuren-Konsistenz: „{bad}“ widerspricht characters.json")
        if "no text" not in p:
            err(errors, level, w, "Negativ-Prompt gegen Text fehlt")
    # Pflicht-Dialogfiguren
    for sp in ("mia", "jonas"):
        if sp not in speakers_in_dialog:
            err(errors, level, "Dialoge", f"{sp} spricht in keinem Dialog")

    # 2) Niveau-Pflichtinhalte
    blob = " ".join(full_text).lower().replace(" ,", ",")
    for w in REQUIRED_WORDS[level]:
        if w == "das ,":
            if not re.search(r"\bdas\s+\w+\s+\w+\s+\w+\s*(entwickelt)", blob) and "unternehmen, das" not in blob:
                err(errors, level, "Niveau", "Relativsatz („Unternehmen, das …“) fehlt")
        elif w not in blob:
            err(errors, level, "Niveau", f"Pflichtinhalt fehlt: „{w}“")

    # 3) Wortschatz im Skript auffindbar?
    for v in script["vocabulary"]:
        keys = re.split(r"\s*/\s*", re.sub(r"[!?…()]", "", v["de"]).strip())
        found = False
        for k in keys:
            toks = [t for t in re.findall(r"[\wäöüÄÖÜß]+", k.lower()) if t not in ("der", "die", "das", "den", "dem", "sich", "etwas", "jemanden", "einem", "einen", "für", "nach")]
            stem = [t[:5] for t in toks]
            if stem and all(any(st in blob for st in [x]) for x in stem):
                found = True
        if not found:
            warns.append(f"[{level}] Wortschatz „{v['de']}“ kommt im Skript nicht vor")
        if v["example"] and not v["example"][0].isupper() and not v["example"][0].isdigit():
            errors.append(f"[{level}] Wortschatz-Beispiel beginnt klein: {v['example']}")

    # 4) Übung: Lösung wird vorgesprochen
    ex_scene = [s for s in script["scenes"] if s["type"] == "exercise"][0]
    ex_text = " ".join(l["text"] for l in ex_scene["lines"]).lower()
    for it in script["exercise"]["items"]:
        if it["answer"].lower().rstrip(".") not in ex_text and level != "A2":
            err(errors, level, "Übung", f"Lösung „{it['answer']}“ wird in der Übungsszene nicht gesprochen")

    # 5) Untertitel & Synchronität
    timeline = build_timeline(script)
    cues = build_cues(timeline)
    by_line = {}
    for c in cues:
        by_line.setdefault(c["line_id"], []).append(c["plain"])
    for t in timeline:
        rebuilt = " ".join(by_line[t["line_id"]])
        if rebuilt != t["text"]:
            err(errors, level, t["line_id"], "Untertitel weichen vom Sprechtext ab")
    prev_end = 0.0
    for i, c in enumerate(cues, 1):
        lines = c["text"].split("\n")
        if len(lines) > SUBTITLE_MAX_LINES or any(len(x) > SUBTITLE_MAX_CHARS_PER_LINE for x in lines):
            err(errors, level, f"Untertitel {i}", "mehr als 2 Zeilen bzw. >28 Zeichen/Zeile")
        dur = c["end"] - c["start"]
        if c["start"] < prev_end - 1e-6:
            err(errors, level, f"Untertitel {i}", "überlappt mit vorherigem")
        prev_end = c["end"]
        cps = len(c["plain"]) / dur
        if cps > MAX_CPS[level]:
            warns.append(f"[{level}] Untertitel {i}: Lesetempo {cps:.1f} Zeichen/s > {MAX_CPS[level]} ({c['plain'][:40]}…)")
        if dur < 0.6:
            warns.append(f"[{level}] Untertitel {i}: sehr kurz ({dur:.2f} s)")
    tot = timeline[-1]["end"]
    if abs(tot - script["target_duration_sec"]) / script["target_duration_sec"] > 0.25:
        warns.append(f"[{level}] geschätzte Dauer {tot:.0f} s weicht >25 % von target_duration_sec={script['target_duration_sec']} ab")
    return errors, warns


def main():
    levels = sys.argv[1:] or LEVELS
    all_err = []
    for lv in levels:
        e, w = check_level(lv)
        print(f"== {lv}: {len(e)} Fehler, {len(w)} Hinweise")
        for x in e:
            print("  FEHLER ", x)
        for x in w:
            print("  Hinweis", x)
        all_err += e
    print("\nErgebnis:", "BESTANDEN" if not all_err else f"{len(all_err)} Fehler")
    sys.exit(1 if all_err else 0)


if __name__ == "__main__":
    main()
