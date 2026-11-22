# Remotion-Comic: Klassen-Comedy (ELM Akademie)

Kurzvideo 1080 × 1920, 30 fps, ca. 17,5 s: Lehrer und Schüler Ali, deutsche Dialoge, große
Wort-für-Wort-Untertitel, Kamerafahrten, Übergänge, Soundeffekte, ELM-Logo.
**Fertig:** `out/classroom-comedy.mp4`

## Visuelle Vorlage
`public/assets/classroom-storyboard.png` (3 × 2) ist in `scene-01.png … scene-06.png` geschnitten.
Es werden **nur diese Bilder** verwendet (Zoom, Fahrt, Überblendung); es gibt keine neu gezeichneten
Figuren, das Aussehen bleibt exakt wie in der Vorlage.

## Aufbau
```
src/episode.json            Dialog, Posen, Effekte  ← hier neue Episoden schreiben
src/characters.ts           Figuren-Register: Lehrer und Schüler mit Posen (Bild, Fokus, Zoom)
src/components/Character.tsx  <Teacher/> und <Student/> (wiederverwendbar), wippen mit der Stimme
src/components/Subtitles.tsx  große synchrone Untertitel mit Namensschild
src/components/Header.tsx, Outro.tsx  Logo, Abzeichen, Abspann
src/ClassroomComedy.tsx     Schnitt, Übergänge, Ton
tools/make_audio.py         Stimmen (Piper "Thorsten"), Effekte, Musik, src/timeline.json
```

## Neue Episode / Änderungen
1. `src/episode.json` bearbeiten (`who`: teacher/student, `pose`, `text`, `sfx`).
   Neue Posen: Bild in `public/assets` ablegen und in `src/characters.ts` eintragen.
2. `npm run audio`   (Stimmen und Zeitplan neu erzeugen; braucht `pip install piper-tts numpy`)
3. Video rendern und Lautstärke angleichen:
```bash
npx remotion render ClassroomComedy out/raw.mp4
ffmpeg -y -i out/raw.mp4 -af loudnorm=I=-14:TP=-1.0:LRA=9 -c:v copy -c:a aac -b:a 192k -ar 48000 out/classroom-comedy.mp4
```
Vorschau im Browser: `npm run studio`.

Hinweis: Stimmen sind KI-generiert (Thorsten, CC0) → beim Posten als KI-Inhalt kennzeichnen.
