#!/usr/bin/env python3
"""Erzeugt aus der Schnittliste ein ffmpeg-Skript (lokal, kostenlos).

  python3 scripts/assemble.py A1        schreibt output/A1_assemble.sh und listet fehlende Dateien

Das Skript wird NICHT automatisch ausgeführt. Es setzt voraus, dass pro Szene fertige
Clips unter clips/<Niveau>/ liegen (clips/A1/A1-S03_c01.mp4 …), und brennt die Untertitel
(subtitles/<Niveau>.srt) ein. Audio wird je Szene aus den Zeilen-MP3s gebaut (Pausen
siehe audio/<Niveau>/manifest.json); sobald echte Audiodauern bekannt sind, in
audio/<Niveau>/durations.json eintragen und `build.py` neu starten.
"""
import sys

from lib import *  # noqa: F401,F403


def main():
    level = sys.argv[1] if len(sys.argv) > 1 else "A1"
    edl = load_json(ROOT / "videos" / level / "edit_list.json")
    missing, listing = [], []
    for sc in edl["scenes"]:
        for c in sc["clips"]:
            if not (ROOT / c).exists():
                missing.append(c)
            listing.append(f"file '{ROOT / c}'")
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    (out / f"{level}_concat.txt").write_text("\n".join(listing) + "\n", encoding="utf-8")
    sh = [
        "#!/usr/bin/env bash", "set -euo pipefail", f"cd '{ROOT}'",
        f"ffmpeg -f concat -safe 0 -i output/{level}_concat.txt -c copy output/{level}_raw.mp4",
        "# TODO: Sprach-Spur je Szene zusammensetzen (adelay) und mit der Musik mischen",
        f"ffmpeg -i output/{level}_raw.mp4 -vf \"subtitles=subtitles/{level}.srt:force_style='FontSize=22,Outline=2'\" "
        f"-c:a copy output/{level}_final.mp4",
    ]
    (out / f"{level}_assemble.sh").write_text("\n".join(sh) + "\n", encoding="utf-8")
    print(f"Schnittliste: {len(listing)} Clips, davon fehlen {len(missing)}.")
    for m in missing[:8]:
        print("  fehlt:", m)
    if len(missing) > 8:
        print(f"  … und {len(missing) - 8} weitere")
    print(f"Skript: output/{level}_assemble.sh (nicht ausgeführt)")


if __name__ == "__main__":
    main()
