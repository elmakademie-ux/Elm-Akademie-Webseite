# Remotion-Comic: Klassen-Comedy (ELM Akademie)

Kurzvideo 1080 × 1920, 30 fps, ca. 17,5 s: Lehrer und Schüler Ali, deutsche Dialoge, große
Wort-für-Wort-Untertitel, Kamerafahrten, Übergänge, Soundeffekte, ELM-Logo.
**Fertig (YouTube Shorts, ohne Logo):** alle Videos liegen in `../shorts/` (Titel und Beschreibungen in `../shorts/BESCHREIBUNGEN.md`).
Neu rendern: `tools/render_shorts.sh [episode-id ...]`.

## Visuelle Vorlage
`public/assets/classroom-storyboard.png` (3 × 2) ist in `scene-01.png … scene-06.png` geschnitten.
Es werden **nur diese Bilder** verwendet (Zoom, Fahrt, Überblendung); es gibt keine neu gezeichneten
Figuren, das Aussehen bleibt exakt wie in der Vorlage.

## Aufbau
```
src/episodes/<id>.json      Dialog, Posen, Effekte  ← hier neue Episoden schreiben
src/timelines/<id>.json     (automatisch) Zeitplan, Wörter, Lautstärke
src/episodes.ts             Liste aller Episoden
src/characters.ts           Figuren-Register: Lehrer und Schüler mit Posen (Bild, Fokus, Zoom)
src/components/Character.tsx  <Teacher/> und <Student/> (wiederverwendbar), wippen mit der Stimme
src/components/Subtitles.tsx  große synchrone Untertitel mit Namensschild
src/components/Header.tsx, Outro.tsx  Logo, Abzeichen, Abspann
src/Episode.tsx             Schnitt, Übergänge, Ton (für jede Episode)
tools/make_audio.py         Stimmen (Piper "Thorsten"), Effekte, Musik, src/timeline.json
```

## Neue Episode
1. `src/episodes/<id>.json` anlegen (Vorlage: `homework-excuse.json`): `who` teacher/student, `pose`, `text`, `sfx`
   (gasp, alarm, boing, ding, slam, rimshot, womp). Neue Posen: Bild in `public/assets` und Eintrag in `src/characters.ts`.
2. `python3 tools/make_audio.py <id>`   (Stimmen und Zeitplan; braucht `pip install piper-tts numpy`)
3. Episode in `src/episodes.ts` eintragen, dann rendern und Lautstärke angleichen:
```bash
npx remotion render <id> out/raw_<id>.mp4
ffmpeg -y -i out/raw_<id>.mp4 -af loudnorm=I=-14:TP=-1.0:LRA=9 -c:v copy -c:a aac -b:a 192k -ar 48000 out/<id>.mp4
```
Vorschau im Browser: `npm run studio`.

Hinweis: Stimmen sind KI-generiert (Thorsten, CC0) → beim Posten als KI-Inhalt kennzeichnen.

## Echte Animation (Bild-zu-Video)
Die Figuren in den Szenenbildern sind Standbilder. Für Mundbewegung, Augen, Gesten wie im
KI-Cartoon-Beispiel: aus jedem Szenenbild mit einem Bild-zu-Video-Werkzeug (z. B. Runway, Kling, Hailuo, Veo)
einen Clip erzeugen. `python3 tools/make_prompts.py <id>` schreibt dafür `video-prompts/<id>.md`
(Prompt, Mindestlänge, Sprachdatei je Szene). Clips nach `public/assets/clips/` legen und in
`src/clips.json` eintragen; die Komposition nutzt dann den Clip statt des Bildes.

## Szene 1 – "The Surprise Test" (neue Besetzung)
Vorlage: `public/assets/surprise-test/classroom-storyboard.png` → `scene-01.png … scene-06.png`
(Lehrerin mit lockigen roten Haaren, Schüler im gelben Hoodie; Figuren in `src/characters.ts` als `teacher_f`, `student_y`).
- Komponente: `src/SurpriseTestScene.tsx` (Sequence, AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig)
- Gesamte Episode: `src/SurpriseTestEpisode.tsx` (weitere Szenen in `SCENES` anreihen)
- Ton: `python3 tools/make_scene_audio.py` (englische Stimme Piper "Amy", Betonung, Effekt, Klassenzimmer-Atmosphäre)
- Rendern: `npx remotion render surprise-test out/raw_surprise.mp4`, dann wie oben mit `loudnorm` → `out/surprise-test-scene1.mp4`

## Englische Episoden
`"language": "en"` in der Episode-JSON nimmt zwei englische Piper-Männerstimmen (Lehrer: Ryan, Schüler: Joe); `names` ersetzt die Namensschilder, `cta` den Abspann-Text, `say` den gesprochenen Text (z. B. Schreien ohne Großbuchstaben), `loud` macht die Zeile lauter.

## Shorts-Format
Kein Logo, kein Abspann; das Video endet auf der Pointe und läuft in den Anfang (Loop). Unten ca. 420 px, oben ca. 150 px
und rechts ca. 120 px bleiben frei von Text (Shorts-Oberfläche). Zweite Besetzung per `"cast"` in der Episode-JSON
(`teacher_f`, `student_y`, Stimmen per `"voices"`).
