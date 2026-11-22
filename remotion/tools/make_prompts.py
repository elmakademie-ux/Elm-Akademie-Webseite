"""
Erzeugt aus Episode + Zeitplan eine Anleitung zum Animieren der Szenenbilder mit einem
Bild-zu-Video-Werkzeug (Runway, Kling, Hailuo, Veo ...):  video-prompts/<id>.md

    python3 tools/make_prompts.py <episode-id>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EID = next((a for a in sys.argv[1:] if not a.startswith("-")), "classroom-comedy")
EP = json.load(open(ROOT / "src" / "episodes" / f"{EID}.json", encoding="utf-8"))
TL = json.load(open(ROOT / "src" / "timelines" / f"{EID}.json", encoding="utf-8"))
SCENE = {"teacher/pointing": "scene-01", "student/explaining": "scene-02", "teacher/glasses": "scene-03",
         "student/thumb": "scene-04", "teacher/shocked": "scene-05", "teacher/tired": "scene-06",
         "student/satisfied": "scene-06"}
MOTION = {
    "teacher/pointing": "The angry teacher leans forward and shouts while pointing his finger at the student; the student rolls his eyes and keeps his arms crossed. Slow push-in.",
    "student/explaining": "The cheeky student talks, tilts his head, gestures with his open hand, pupils move, eyebrows play. Slight camera push-in.",
    "teacher/glasses": "The strict teacher pushes his glasses with his finger, narrows his eyes and talks in a stern way. Slow push-in.",
    "student/thumb": "The student proudly points a thumb at his own chest, talks and laughs, small head and shoulder movement.",
    "teacher/shocked": "The teacher is shocked, eyes wide, mouth open, talks/shouts with strong mouth movement, head jerks slightly.",
    "teacher/tired": "The teacher sighs and lets his shoulders drop, the student smiles with closed eyes and puts hands on hips.",
    "student/satisfied": "The student grins confidently and nods slightly.",
}
STYLE = ("2D cartoon, flat colours, thick black outlines. Keep both characters EXACTLY like the reference image "
         "(face, hair, glasses, clothes, colours), keep the same classroom, no style change, no new characters, "
         "no text, no subtitles. Vertical 9:16, 24-30 fps, natural lip-sync.")
out = [f"# {EP['title']} – Clips für Bild-zu-Video\n",
       "Pro Szene ein Clip aus dem Szenenbild (`public/assets/scene-0X.png`) erzeugen. Wenn das Werkzeug "
       "eine **Audio-/Lip-Sync-Funktion** hat, die Sprachdatei der Zeile hochladen. Der Clip sollte mindestens "
       "so lang sein wie angegeben.\n", f"**Stil-Zusatz für jeden Prompt:** {STYLE}\n"]
for sh in TL["shots"]:
    key = f"{sh['who']}/{sh['pose']}"
    line = next((l for l in TL["lines"] if l["startFrame"] >= sh["startFrame"] and l["endFrame"] <= sh["endFrame"] + 12), None)
    secs = (sh["endFrame"] - sh["startFrame"]) / TL["fps"] + 0.4
    out += [f"## {SCENE.get(key, '?')} – {key}  (Clip ≥ {secs:.1f} s)",
            f"- Bild: `public/assets/{SCENE.get(key, 'scene-0X')}.png`"]
    if line:
        out += [f"- Sprecher/Text: {line['who']}: „{line['text']}“", f"- Sprachdatei: `{line['audio']}`"]
    else:
        out += ["- Reaktion ohne Text (Seufzer)"]
    out += [f"- Prompt: {MOTION.get(key, '')} {STYLE}", f"- Speichern als: `public/assets/clips/{sh['who']}-{sh['pose']}.mp4`\n"]
out += ["## Clips einsetzen",
        "In `src/clips.json` eintragen (Länge in Frames bei 30 fps = Sekunden × 30):",
        "```json", '{ "teacher/pointing": { "file": "assets/clips/teacher-pointing.mp4", "frames": 90 } }', "```",
        "Danach wie gewohnt rendern; Untertitel, Ton, Schnitte und Logo bleiben unverändert.\n"]
(ROOT / "video-prompts").mkdir(exist_ok=True)
open(ROOT / "video-prompts" / f"{EID}.md", "w", encoding="utf-8").write("\n".join(out))
print("OK", EID)
