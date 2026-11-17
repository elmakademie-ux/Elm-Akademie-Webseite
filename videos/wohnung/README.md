# Meine Wohnung – A1-Lernvideo (ELM Akademie)

60-Sekunden-Lernvideo im Hochformat (1080 × 1920, 30 fps, MP4) für TikTok, Instagram Reels und YouTube Shorts.

## Projektstruktur

```
videos/wohnung/
├── README.md            diese Anleitung
├── inhalt.py            ALLE Texte, Wörter, Farben, Dauer  ← hier bearbeiten
├── illustrationen.py    zeichnet 8 Raum-Illustrationen (Ersatz, falls keine Fotos)
├── bilder_ausschneiden.py  schneidet die 8 Fotos aus der Collage (ohne Text-Schilder)
├── render.py            Technik: Zeitplan, Animationen, Karaoke-Untertitel, Export
├── bilder/              collage_original.png, haus.png … gesamt.png, logo.png
└── meine_wohnung.mp4    fertiges Video
```
Stimme und Musik kommen aus `videos/common/audio.py` (gemeinsam für alle Videos).

## Ablauf

| Teil | Inhalt |
|---|---|
| Einleitung (~4 s) | Titel, Artikel-Farben **der** (blau) · **die** (rot) · **das** (grün), „Hallo! Ich zeige euch meine Wohnung.“ |
| 8 Szenen | Überschrift mit farbigem Artikel, Illustration mit sanftem Zoom und Übergang, gesprochener Satz als Karaoke-Untertitel (Nomen in Artikelfarbe), jedes neue Wort groß eingeblendet + vorgesprochen + Markierung im Bild, danach „Sprich nach!“-Pause |
| Abschluss (~6 s) | „Wie ist deine Wohnung?“ – „Meine Wohnung ist … groß / klein / schön / gemütlich“, Logo, „ELM Akademie – Deutsch lernen“ |

**Was gesprochen wird, steht genau so auf dem Bildschirm** (beides kommt aus demselben Feld `saetze`).
Die Pausen zum Nachsprechen werden automatisch so berechnet, dass das Video exakt 60 Sekunden dauert.

## Bearbeiten

In **`inhalt.py`**:
- `saetze`: Sätze einer Szene (gesprochen + angezeigt).
- `woerter`: neue Wörter (mit Artikel), werden groß gezeigt und vorgesprochen.
- `pins`: wo das Wort im Bild markiert wird (x, y im Format 900 × 770).
- `VOKABELN`: bestimmt die Artikelfarbe der Nomen in allen Sätzen automatisch.
- `SPRECHTEMPO`, `MUSIK_LAUTSTAERKE`, `GESAMTDAUER`, Farben.

**Fotos oder Illustrationen:** In `inhalt.py` steht `BILDQUELLE = "fotos"` (aktuell) oder `"illustrationen"`.
Die Fotos stammen aus deiner Collage: `bilder_ausschneiden.py` schneidet nur den Fotostreifen zwischen
Titel- und Satzschild aus, damit keine Texte im Bild stehen, die vom gesprochenen Text abweichen.
Eigenes Foto: z. B. `bilder/kueche.jpg` ersetzen (Querformat ca. 1,7 : 1) und `foto_pins` anpassen
(Position von 0 bis 1, 0,0 = oben links).

## Neu exportieren

Voraussetzungen: Python 3, `pip install pillow numpy piper-tts`, `ffmpeg`.

```bash
cd videos/wohnung
python3 render.py --preview     # Vorschaubilder in vorschau/
python3 render.py               # fertiges Video → meine_wohnung.mp4 (ca. 2–3 Minuten)
python3 illustrationen.py       # optional: Illustrationen einzeln als PNG ansehen
```

Meldet der Export „Texte sind für die Gesamtdauer zu lang“, Sätze kürzen oder `SPRECHTEMPO` verkleinern.

## Hinweise
- Stimme: „Thorsten“ (Piper TTS, CC0) – KI-generiert, beim Posten als KI-Inhalt kennzeichnen.
- Musik und Illustrationen werden vom Programm selbst erzeugt – keine Lizenzfragen.
