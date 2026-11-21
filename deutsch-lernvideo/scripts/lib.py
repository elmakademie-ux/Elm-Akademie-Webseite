"""Gemeinsame Funktionen für das Deutsch-Lernvideo-Projekt.

Quelle der Wahrheit sind die Dateien videos/<Niveau>/script.json,
characters/characters.json und audio/voices.json. Alles andere
(Markdown, Prompts, Untertitel, Audio-Manifeste) wird daraus erzeugt.
Dieses Modul ruft KEINE externen Dienste auf.
"""
from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ["A1", "A2", "B1", "B2"]

# Maximale Länge eines KI-Videoclips in Sekunden (anpassbar je nach Anbieter)
MAX_CLIP_SEC = 8.0
SUBTITLE_MAX_CHARS_PER_LINE = 42
SUBTITLE_MAX_LINES = 2
SCENE_LEAD_IN = 0.6
SCENE_TAIL = 0.6
# Untertitel bleiben während einer Denk-/Nachsprechpause bis zu so viele Sekunden stehen
MAX_HOLD_SEC = 2.0

STYLE_BLOCK = (
    "High-end 3D animated feature-film look in the style of a major animation studio: "
    "appealing, friendly, expressive characters with natural facial expressions and accurate lip-sync, "
    "modern colorful environments, cinematic lighting, professional camera work, smooth natural motion, "
    "soft global illumination, rich but clean color palette."
)
NEGATIVE_BLOCK = (
    "no text, no letters, no subtitles, no logos, no watermarks, no extra characters in the foreground, "
    "no change of hairstyle, hair color, clothing or face between shots, no distorted hands or faces, "
    "no photorealistic humans, no scary or uncanny expressions"
)
FRAMING_BLOCK = (
    "9:16 vertical master frame (1080x1920) for TikTok / Reels / Shorts; compose for portrait: "
    "characters in medium shots or close-ups stacked vertically, wide shots only with vertical depth "
    "(sky/foreground), keep faces in the middle 60% of the frame, leave the lower fifth free for subtitles "
    "and the top tenth free for platform UI."
)


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_script(level: str) -> dict:
    return load_json(ROOT / "videos" / level / "script.json")


def load_characters() -> dict:
    return load_json(ROOT / "characters" / "characters.json")


def load_voices() -> dict:
    return load_json(ROOT / "audio" / "voices.json")


def load_lexicon() -> dict:
    return load_json(ROOT / "audio" / "pronunciation.json")["replacements"]


def line_id(scene: dict, idx: int) -> str:
    return f"{scene['id']}-L{idx + 1:02d}"


def word_count(text: str) -> int:
    return len(re.findall(r"[\wÄÖÜäöüß-]+", text))


def line_duration(text: str, wpm: float) -> float:
    return max(0.8, word_count(text) / (wpm / 60.0))


def speaking_params(level: str):
    v = load_voices()
    return v["speech_rate_wpm"][level], v["pause_between_lines_sec"][level]


def tts_text(text: str, lexicon: dict) -> str:
    out = text
    for key, val in lexicon.items():
        out = re.sub(rf"(?<![\wÄÖÜäöüß]){re.escape(key)}(?![\wÄÖÜäöüß])", val, out)
    return out


def build_timeline(script: dict, durations: dict | None = None) -> list[dict]:
    """Schätzt (oder liest aus echten Audiodauern) Start/Ende jeder Zeile.

    durations: optionale Zuordnung {line_id: Sekunden} aus echten Audiodateien
    (audio/<Niveau>/durations.json). So werden Untertitel später exakt
    synchronisiert, ohne das Skript zu ändern.
    """
    wpm, gap = speaking_params(script["level"])
    durations = durations or {}
    t = 0.0
    out = []
    for scene in script["scenes"]:
        t += SCENE_LEAD_IN
        scene_start = t
        for i, ln in enumerate(scene["lines"]):
            lid = line_id(scene, i)
            dur = durations.get(lid, line_duration(ln["text"], wpm))
            out.append({
                "line_id": lid, "scene": scene["id"], "speaker": ln["speaker"],
                "text": ln["text"], "start": round(t, 3), "end": round(t + dur, 3),
                "estimated": lid not in durations,
                "hold": min(ln.get("pause_after", 0.0), MAX_HOLD_SEC),
            })
            t += dur + gap + ln.get("pause_after", 0.0)
        t += SCENE_TAIL
        scene["_start"], scene["_end"] = round(scene_start - SCENE_LEAD_IN, 3), round(t, 3)
    return out


def split_cues(text: str) -> list[str]:
    """Teilt einen Satz in Untertitel-Häppchen (max. 2 Zeilen à 42 Zeichen)."""
    limit = SUBTITLE_MAX_CHARS_PER_LINE * SUBTITLE_MAX_LINES
    if len(text) <= limit and _fits(text):
        return [text]
    parts = re.split(r"(?<=[.!?:;])\s+", text)
    cues, cur = [], ""
    for p in parts:
        if len(p) > limit:  # an Kommas teilen
            sub = re.split(r"(?<=,)\s+", p)
        else:
            sub = [p]
        for s in sub:
            if cur and len(cur) + 1 + len(s) > limit:
                cues.append(cur)
                cur = s
            else:
                cur = f"{cur} {s}".strip()
    if cur:
        cues.append(cur)
    # Sicherstellen, dass jedes Häppchen in 2 Zeilen à 42 Zeichen passt
    final = []
    for c in cues:
        final.extend(_force_fit(c))
    return final


def _fits(text: str) -> bool:
    ls = wrap_cue(text).split("\n")
    return len(ls) <= SUBTITLE_MAX_LINES and all(len(x) <= SUBTITLE_MAX_CHARS_PER_LINE for x in ls)


def _force_fit(text: str) -> list[str]:
    if _fits(text):
        return [text]
    words = text.split()
    mid = len(words) // 2
    return _force_fit(" ".join(words[:mid])) + _force_fit(" ".join(words[mid:]))


def wrap_cue(text: str) -> str:
    if len(text) <= SUBTITLE_MAX_CHARS_PER_LINE:
        return text
    lines = textwrap.wrap(text, width=SUBTITLE_MAX_CHARS_PER_LINE, break_long_words=False)
    if len(lines) <= SUBTITLE_MAX_LINES:
        # ausgewogenere Zeilen: nach der Mitte teilen
        words = text.split()
        best = None
        for k in range(1, len(words)):
            a, b = " ".join(words[:k]), " ".join(words[k:])
            if max(len(a), len(b)) <= SUBTITLE_MAX_CHARS_PER_LINE:
                score = abs(len(a) - len(b))
                if best is None or score < best[0]:
                    best = (score, a, b)
        if best:
            return f"{best[1]}\n{best[2]}"
    return "\n".join(lines)


def build_cues(timeline: list[dict]) -> list[dict]:
    cues = []
    for entry in timeline:
        pieces = split_cues(entry["text"])
        total = sum(len(p) for p in pieces)
        dur = entry["end"] - entry["start"]
        t = entry["start"]
        for p in pieces:
            d = dur * len(p) / total
            cues.append({
                "line_id": entry["line_id"], "speaker": entry["speaker"],
                "start": round(t, 3), "end": round(t + d, 3),
                "text": wrap_cue(p), "plain": p,
            })
            t += d
        if cues and cues[-1]["line_id"] == entry["line_id"]:
            cues[-1]["end"] = round(cues[-1]["end"] + entry.get("hold", 0.0), 3)
    return cues


def fmt_ts(sec: float, comma: bool = True) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    sep = "," if comma else "."
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def chunk_shots(scene: dict, wpm: float, gap: float) -> list[dict]:
    """Teilt eine Szene an Zeilengrenzen in Clips <= MAX_CLIP_SEC."""
    shots, cur, cur_dur = [], [], 0.0
    for i, ln in enumerate(scene["lines"]):
        d = line_duration(ln["text"], wpm) + gap + ln.get("pause_after", 0.0)
        if cur and cur_dur + d > MAX_CLIP_SEC:
            shots.append({"lines": cur, "duration": round(cur_dur, 1)})
            cur, cur_dur = [], 0.0
        cur.append(i)
        cur_dur += d
    if cur:
        shots.append({"lines": cur, "duration": round(cur_dur, 1)})
    return shots


def character_block(chars: dict, ids: list[str]) -> str:
    out = []
    for cid in ids:
        c = chars["characters"][cid]
        if "appearance" not in c:
            continue
        out.append(f"{c['display_name'].upper()}: {c['appearance']}; wearing {c['wardrobe']}.")
    return " ".join(out)


def episode_props(chars: dict, level: str, ids: list[str]) -> str:
    prof = chars["episode_profiles"][level]
    return prof.get("props_en", "")


def scene_prompt(script: dict, scene: dict, chars: dict, wpm: float, gap: float) -> dict:
    pe = scene["prompt_en"]
    ids = [c for c in scene["characters"]]
    dialogue = []
    for i, ln in enumerate(scene["lines"]):
        who = chars["characters"][ln["speaker"]]
        dialogue.append(
            f"{who['display_name']} ({ln['emotion']}) says in German: \"{ln['text']}\""
        )
    shots = chunk_shots(scene, wpm, gap)
    est = round(sum(s["duration"] for s in shots), 1)
    prompt = "\n".join([
        f"STYLE: {STYLE_BLOCK}",
        f"CHARACTERS (must look identical in every shot; use the provided reference images): "
        f"{character_block(chars, ids)}",
        f"PROPS THIS EPISODE: {episode_props(chars, script['level'], ids)}",
        f"LOCATION: {pe['location']}.",
        f"ACTION: {scene['visual']}",
        f"CAMERA: {pe['camera']}.",
        f"LIGHTING: {pe['lighting']}.",
        "DIALOGUE (German, speech pace "
        f"{'slow and very clear' if script['level'] == 'A1' else 'clear and natural'}; "
        "lip-sync to the supplied audio track): " + " | ".join(dialogue),
        f"MUSIC / AMBIENCE: {script['music_en']}, very low in the mix. Keep music low so the speech stays clearly intelligible.",
        f"FRAMING: {FRAMING_BLOCK}",
        f"NEGATIVE: {NEGATIVE_BLOCK}",
    ])
    return {
        "scene_id": scene["id"], "title": scene["title"], "type": scene["type"],
        "estimated_duration_sec": est, "shots": shots, "prompt": prompt,
        "reference_images": [f"characters/reference/{c}.png" for c in ids if "appearance" in chars["characters"][c]],
        "on_screen_text_overlay": scene.get("on_screen", []),
    }
