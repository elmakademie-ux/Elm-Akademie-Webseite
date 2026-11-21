#!/usr/bin/env python3
"""Erzeugt aus videos/<Niveau>/script.json alle abgeleiteten Dateien:

  videos/<N>/script.md          lesbares Drehbuch
  videos/<N>/edit_list.json     Schnittliste (Szenen, Clips, Audio, Reihenfolge)
  prompts/<N>/<SzeneID>.md      KI-Videoprompt je Szene
  prompts/<N>/prompts.json      alle Prompts maschinenlesbar
  subtitles/<N>.srt / .vtt      Untertitel
  subtitles/<N>.timeline.json   Zeitleiste (geschätzt oder aus echten Audiodauern)
  audio/<N>/manifest.json       TTS-Aufträge (OHNE API-Aufruf)
  audio/<N>/tts_script.md       Sprechertexte je Sprecher

Aufruf:  python3 scripts/build.py [A1 A2 B1 B2]
Kein Netzwerkzugriff, keine Kosten.
"""
import sys
from collections import defaultdict

from lib import *  # noqa: F401,F403


def render_markdown(script, chars, timeline, cues, prompts):
    L = []
    a = L.append
    a(f"# {script['title']}")
    a(f"\n**Niveau {script['level']} – {script['level_name']}** · Anrede: {script['form_of_address']} · "
      f"Zieldauer ca. {script['target_duration_sec'] // 60}:{script['target_duration_sec'] % 60:02d} min "
      f"(geschätzte Sprechzeit laut Zeitleiste: {fmt_ts(timeline[-1]['end'], True)[:8]})")
    a(f"\n*{script['subtitle']}*\n")
    a(f"**Lernziel:** {script['can_do']}\n")
    a(f"**YouTube-Titel:** {script['social']['title_youtube']}  \n**Hashtags:** {' '.join(script['social']['hashtags'])}\n")
    a("> Automatisch aus `script.json` erzeugt (`python3 scripts/build.py`). Änderungen bitte in der JSON-Datei vornehmen.\n")
    a("## Inhaltsübersicht\n")
    a("| Nr. | Szene | Typ | Figuren |\n|---|---|---|---|")
    labels = {"hook": "1 Hook", "intro": "2 Einführung Niveau", "dialog": "3–5 Szene/Dialog/Regie/Prompt",
              "vocab": "9 Wortschatz", "grammar": "10 Grammatik", "exercise": "11 Übung", "outro": "12 Abschluss"}
    for s in script["scenes"]:
        names = ", ".join(chars["characters"][c]["display_name"] for c in s["characters"])
        a(f"| {s['id']} | {s['title']} | {labels[s['type']]} | {names} |")
    a("")
    for s in script["scenes"]:
        a(f"\n---\n\n## {s['id']} · {s['title']}  _({s['type']})_\n")
        a(f"**Ort:** {s['location']}  ")
        a(f"**Beschreibung:** {s['description']}\n")
        a("**Regieanweisungen**\n")
        d = s["direction"]
        a(f"- **Kamera:** {d['camera']}\n- **Licht:** {d['lighting']}\n- **Animation/Schauspiel:** {d['animation']}\n- **Musik/Ton:** {d['music']}\n")
        a("**Dialog / Sprechertext**\n")
        a("| ID | Sprecher | Text (= Untertitel) | Betonung (nur TTS) |\n|---|---|---|---|")
        for i, ln in enumerate(s["lines"]):
            sp = chars["characters"][ln["speaker"]]["display_name"]
            pa = f" ⏸{ln['pause_after']:.0f}s" if ln.get("pause_after") else ""
            a(f"| {line_id(s, i)} | **{sp}** | {ln['text']}{pa} | {ln['emotion']} |")
        if s.get("on_screen"):
            a("\n**Einblendungen (in der Postproduktion, nicht von der KI zu rendern):** " + " · ".join(f"`{t}`" for t in s["on_screen"]))
        p = prompts[s["id"]]
        a(f"\n**KI-Videoprompt** (geschätzt {p['estimated_duration_sec']} s, {len(p['shots'])} Clip(s)): `prompts/{script['level']}/{s['id']}.md`\n")
        a("```text\n" + p["prompt"] + "\n```")
    a("\n---\n\n## 7 Sprechertexte je Stimme\n")
    by = defaultdict(list)
    for t in timeline:
        by[t["speaker"]].append(t)
    for sp, items in by.items():
        a(f"### {chars['characters'][sp]['display_name']}\n_Stimme: {chars['characters'][sp]['voice']}_\n")
        for t in items:
            a(f"- `{t['line_id']}` {t['text']}")
        a("")
    a("## 8 Untertitel\n")
    a(f"Dateien: `subtitles/{script['level']}.srt`, `subtitles/{script['level']}.vtt`. "
      "Text und Zeitleiste stammen aus derselben Quelle wie die Sprechertexte (Synchronität). "
      "Zeiten sind Schätzungen, bis echte Audiodauern vorliegen (`audio/<Niveau>/durations.json`, dann `build.py` erneut ausführen).\n")
    a("<details><summary>Untertitel-Tabelle anzeigen</summary>\n")
    a("| # | Start | Ende | Text |\n|---|---|---|---|")
    for i, c in enumerate(cues, 1):
        a(f"| {i} | {fmt_ts(c['start'])} | {fmt_ts(c['end'])} | {c['text'].replace(chr(10), ' / ')} |")
    a("\n</details>\n")
    a("## 9 Wortschatz\n")
    a("| Deutsch | English | Beispiel |\n|---|---|---|")
    for v in script["vocabulary"]:
        a(f"| {v['de']} | {v['en']} | {v['example']} |")
    a("\n## 10 Grammatik\n")
    for g in script["grammar"]:
        a(f"### {g['title']}\n{g['rule']}\n")
        for e in g["examples"]:
            a(f"- {e}")
        a("")
    ex = script["exercise"]
    a("## 11 Wiederholungsübung\n")
    a(f"**{ex['instruction']}**\n")
    for i, it in enumerate(ex["items"], 1):
        a(f"{i}. {it['prompt']}  →  **{it['answer']}**")
    a(f"\n**Sprechaufgabe:** {ex['speaking_task']}\n")
    a("## 12 Abschluss und Aufruf zum Mitmachen\n")
    outro = script["scenes"][-1]
    for i, ln in enumerate(outro["lines"]):
        a(f"- **{chars['characters'][ln['speaker']]['display_name']}:** {ln['text']}")
    a("")
    return "\n".join(L)


def build(level):
    script = load_script(level)
    chars = load_characters()
    wpm, gap = speaking_params(level)
    lex = load_lexicon()

    dur_file = ROOT / "audio" / level / "durations.json"
    durations = load_json(dur_file) if dur_file.exists() else None
    timeline = build_timeline(script, durations)
    cues = build_cues(timeline)

    # Prompts
    prompts = {}
    for s in script["scenes"]:
        prompts[s["id"]] = scene_prompt(script, s, chars, wpm, gap)
    pdir = ROOT / "prompts" / level
    pdir.mkdir(parents=True, exist_ok=True)
    for s in script["scenes"]:
        p = prompts[s["id"]]
        md = [f"# {s['id']} · {s['title']}\n",
              f"Typ: {s['type']} · geschätzte Dauer: {p['estimated_duration_sec']} s\n",
              "Referenzbilder (als Bildeingabe verwenden): " + (", ".join(f"`{r}`" for r in p["reference_images"]) or "–") + "\n",
              "## Videoprompt\n", "```text\n" + p["prompt"] + "\n```\n",
              "## Clip-Aufteilung (max. %.0f s je Clip)\n" % MAX_CLIP_SEC]
        for n, sh in enumerate(p["shots"], 1):
            texts = "; ".join(f"{chars['characters'][s['lines'][i]['speaker']]['display_name']}: „{s['lines'][i]['text']}“" for i in sh["lines"])
            md.append(f"{n}. ca. {sh['duration']} s – {texts}")
        if p["on_screen_text_overlay"]:
            md.append("\n## Einblendungen (Postproduktion)\n" + " · ".join(p["on_screen_text_overlay"]))
        (pdir / f"{s['id']}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    save_json(pdir / "prompts.json", {"level": level, "scenes": list(prompts.values())})

    # Untertitel
    sdir = ROOT / "subtitles"
    sdir.mkdir(exist_ok=True)
    srt = []
    vtt = ["WEBVTT\n"]
    for i, c in enumerate(cues, 1):
        srt.append(f"{i}\n{fmt_ts(c['start'])} --> {fmt_ts(c['end'])}\n{c['text']}\n")
        name = chars["characters"][c["speaker"]]["display_name"]
        vtt.append(f"{i}\n{fmt_ts(c['start'], False)} --> {fmt_ts(c['end'], False)}\n<v {name}>{c['text']}\n")
    (sdir / f"{level}.srt").write_text("\n".join(srt), encoding="utf-8")
    (sdir / f"{level}.vtt").write_text("\n".join(vtt), encoding="utf-8")
    save_json(sdir / f"{level}.timeline.json", {"level": level, "lines": timeline})

    # Audio-Manifest (keine API-Aufrufe!)
    voices = load_voices()
    rate = {"A1": "-20%", "A2": "-10%", "B1": "0%", "B2": "0%"}[level]
    items = []
    for s in script["scenes"]:
        for i, ln in enumerate(s["lines"]):
            lid = line_id(s, i)
            tt = tts_text(ln["text"], lex)
            items.append({
                "line_id": lid, "scene": s["id"], "speaker": ln["speaker"],
                "voice_env": voices["roles"][ln["speaker"]]["env_voice_id"],
                "text": ln["text"], "tts_text": tt, "emotion": ln["emotion"],
                "ssml": f'<speak><prosody rate="{rate}">{tt}</prosody></speak>',
                "pause_after_sec": round(gap + ln.get("pause_after", 0.0), 2),
                "output_file": f"audio/{level}/{lid}_{ln['speaker']}.mp3",
                "status": "pending",
            })
    save_json(ROOT / "audio" / level / "manifest.json", {
        "level": level, "language": "de-DE", "speech_rate_wpm": wpm,
        "total_characters": sum(len(i["tts_text"]) for i in items), "items": items})
    tts = [f"# Sprechertexte {level}\n"]
    for sp in chars["characters"]:
        mine = [i for i in items if i["speaker"] == sp]
        if not mine:
            continue
        tts.append(f"## {chars['characters'][sp]['display_name']} ({len(mine)} Zeilen)\n_{chars['characters'][sp]['voice']}_\n")
        tts += [f"- `{i['line_id']}` {i['tts_text']}  _({i['emotion']})_" for i in mine]
        tts.append("")
    (ROOT / "audio" / level / "tts_script.md").write_text("\n".join(tts), encoding="utf-8")

    # Schnittliste
    edl = {"level": level, "title": script["title"], "scenes": [{
        "scene_id": s["id"], "type": s["type"], "start_est": s["_start"], "end_est": s["_end"],
        "clips": [f"clips/{level}/{s['id']}_c{n:02d}.mp4" for n in range(1, len(prompts[s['id']]['shots']) + 1)],
        "audio_lines": [f"audio/{level}/{line_id(s, i)}_{ln['speaker']}.mp3" for i, ln in enumerate(s["lines"])],
        "overlay_text": s.get("on_screen", [])} for s in script["scenes"]],
        "subtitles": f"subtitles/{level}.srt"}
    save_json(ROOT / "videos" / level / "edit_list.json", edl)

    (ROOT / "videos" / level / "script.md").write_text(
        render_markdown(script, chars, timeline, cues, prompts), encoding="utf-8")
    print(f"{level}: {len(script['scenes'])} Szenen, {len(timeline)} Zeilen, {len(cues)} Untertitel, "
          f"~{timeline[-1]['end']:.0f} s, {sum(len(i['tts_text']) for i in items)} TTS-Zeichen")


if __name__ == "__main__":
    for lv in (sys.argv[1:] or LEVELS):
        build(lv)
