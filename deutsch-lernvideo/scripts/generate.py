#!/usr/bin/env python3
"""Planer für KI-Generierung (Sprache, Bilder, Video) – STANDARD: TROCKENLAUF.

  python3 scripts/generate.py plan            Mengen & optionale Kostenschätzung
  python3 scripts/generate.py tts   A1        (gesperrt, s. u.)
  python3 scripts/generate.py image           (gesperrt)
  python3 scripts/generate.py video A1 A1-S03 (gesperrt)

Sicherheit:
* `plan` führt KEINE Netzwerkaufrufe aus und kostet nichts.
* Alle anderen Befehle brechen ab, solange nicht --i-approve-costs gesetzt ist UND
  der Schlüssel als Umgebungsvariable vorhanden ist UND ein Adapter implementiert wurde.
* Es ist bewusst KEIN Adapter enthalten. Nach ausdrücklicher Freigabe des Auftraggebers
  kann je Anbieter eine Klasse in scripts/adapters/ ergänzt werden.
"""
import argparse
import os
import sys

from lib import *  # noqa: F401,F403


def plan():
    prov = load_json(ROOT / "scripts" / "providers.json")
    price_tts = os.environ.get("TTS_PRICE_PER_1K_CHARS")
    price_vid = os.environ.get("VIDEO_PRICE_PER_SEC")
    max_clip = float(os.environ.get("VIDEO_MAX_CLIP_SEC", MAX_CLIP_SEC))
    tot_chars = tot_clips = 0
    tot_sec = 0.0
    print(f"{'Video':6} {'Zeilen':>6} {'TTS-Zeichen':>12} {'Clips':>6} {'Videosek.':>10}")
    for lv in LEVELS:
        script = load_script(lv)
        chars = load_characters()
        wpm, gap = speaking_params(lv)
        lex = load_lexicon()
        n_lines = sum(len(s["lines"]) for s in script["scenes"])
        n_chars = sum(len(tts_text(l["text"], lex)) for s in script["scenes"] for l in s["lines"])
        clips = [sh for s in script["scenes"] for sh in chunk_shots(s, wpm, gap)]
        secs = sum(c["duration"] for c in clips)
        print(f"{lv:6} {n_lines:6d} {n_chars:12d} {len(clips):6d} {secs:10.0f}")
        tot_chars += n_chars; tot_clips += len(clips); tot_sec += secs
    print(f"{'Summe':6} {'':6} {tot_chars:12d} {tot_clips:6d} {tot_sec:10.0f}")
    print("\nHinweis: Clips sind Mindestmengen. Rechne mit 2–4 Versuchen pro Clip (Figuren-Konsistenz, Lippensynchronität).")
    if price_tts:
        print(f"Geschätzte TTS-Kosten (1 Durchlauf): {tot_chars / 1000 * float(price_tts):.2f} (Einheit deines Anbieters)")
    if price_vid:
        print(f"Geschätzte Video-Kosten (1 Durchlauf): {tot_sec * float(price_vid):.2f} (Einheit deines Anbieters)")
    if not (price_tts and price_vid):
        print("Preise nicht gesetzt (.env: TTS_PRICE_PER_1K_CHARS, VIDEO_PRICE_PER_SEC) – keine Kostenschätzung.")
    print("Anbieter-Konfiguration:", {k: v["provider"] for k, v in prov.items() if k != "note"})


def guarded(kind):
    print(f"'{kind}' ist gesperrt: Es werden keine kostenpflichtigen APIs aufgerufen.", file=sys.stderr)
    print("Voraussetzungen: (1) ausdrückliche Freigabe, (2) --i-approve-costs, (3) API-Schlüssel in .env, "
          "(4) implementierter Adapter in scripts/adapters/.", file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["plan", "tts", "image", "video"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--i-approve-costs", action="store_true")
    a = ap.parse_args()
    if a.command == "plan":
        plan()
    else:
        guarded(a.command)  # bewusst keine Implementierung


if __name__ == "__main__":
    main()
