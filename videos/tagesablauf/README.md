# Mein Tagesablauf – A1-Lernvideo (ELM Akademie)

60-Sekunden-Lernvideo im Hochformat (1080 × 1920, 30 fps, MP4) für TikTok, Instagram Reels und YouTube Shorts.

## Projektstruktur

```
videos/
├── common/audio.py            Stimme (Piper TTS „Thorsten“) + Hintergrundmusik, für alle Videos
├── .cache/                    Stimmenmodell und Zwischendateien (wird automatisch angelegt, nicht in Git)
└── tagesablauf/
    ├── README.md              diese Anleitung
    ├── inhalt.py              ALLE Texte, Uhrzeiten, Farben, Dauer, Lautstärke  ← hier bearbeiten
    ├── render.py              Technik: Layout, Animationen, Untertitel, Export
    ├── bilder_ausschneiden.py schneidet die 7 Bilder + Logo aus der Collage
    ├── bilder/
    │   ├── collage_original.png   deine Original-Collage
    │   ├── 1_aufstehen.png … 7_fitness.png
    │   └── logo.png
    └── tagesablauf.mp4        fertiges Video
```

## Ablauf des Videos

| Zeit | Inhalt |
|---|---|
| 0–5 s | Einleitung: Bilder-Fächer, Titel „Mein Tagesablauf“, „Hallo! Ich erzähle euch …“ |
| 5–54 s | 7 Szenen à 7 s: Uhr dreht zur neuen Zeit, große Uhrzeit + Sprechweise („= halb sieben“), Foto mit Zoom, Verb-Etikett, Lernsatz mit farbigen Verben, Untertitel synchron zur Stimme, danach „Sprich nach!“ mit Zeitbalken |
| 54–60 s | „Das ist mein Tagesablauf!“, Wiederholung aller 7 Verben mit Uhrzeit, Aufruf + Logo |

Das ELM-Logo ist oben links durchgehend sichtbar. Der Hintergrund färbt sich vom Morgen (warm) zum Abend (lila).

## Video bearbeiten

Öffne **`inhalt.py`** – dort steht alles, was man normalerweise ändern möchte:

- **Lernsatz** (`satz`): Verben mit Sternchen markieren → werden orange und unterstrichen.
  Beispiel: `"Ich *stehe* um 06:30 Uhr *auf*."`
- **Sprechertext** (`sprecher`): wird vorgelesen und als Untertitel angezeigt.
- **Uhrzeit** (`zeit`) und **Sprechweise** (`sprechweise`, z. B. „Viertel vor acht“).
- **Verb-Etikett** (`verb`): erscheint am Bild und in der Wiederholung am Ende.
- **Bild** (`bild`): Dateiname im Ordner `bilder/`. Eigene Fotos einfach dort ablegen (Querformat ca. 1,15 : 1 ist ideal, wird sonst automatisch zugeschnitten).
- **Tempo der Stimme** (`SPRECHTEMPO`), **Musik-Lautstärke** (`MUSIK_LAUTSTAERKE`), **Farben**, **Dauer** der Teile.

> Wichtig: `INTRO_DAUER + 7 × SZENEN_DAUER + OUTRO_DAUER` ergibt die Gesamtlänge (aktuell 5 + 49 + 6 = 60 s).

Weitere Szenen? Einfach einen Eintrag in `SZENEN` ergänzen und die Dauer anpassen.

## Neu exportieren

Voraussetzungen: Python 3, `pip install pillow numpy piper-tts`, `ffmpeg`.
Das Stimmenmodell (~110 MB) wird beim ersten Lauf automatisch geladen.

```bash
cd videos/tagesablauf
python3 render.py --preview   # schnell: einzelne Vorschaubilder in vorschau/
python3 render.py             # komplettes Video → tagesablauf.mp4 (ca. 2–3 Minuten)
```

Erscheint beim Export „wenig Zeit zum Nachsprechen“, ist ein Sprechertext für 7 Sekunden zu lang –
Text kürzen oder `SZENEN_DAUER` erhöhen.

## Hinweise

- Stimme: „Thorsten“ (Piper TTS, Lizenz CC0, auch kommerziell nutzbar). Die Stimme ist KI-generiert →
  beim Posten auf TikTok/Instagram als KI-Inhalt kennzeichnen.
- Musik: wird vom Programm selbst erzeugt, daher keine Lizenzfragen.
- Die Fotos stammen aus der Collage (je ca. 350 px breit) und werden hochskaliert – mit größeren
  Einzelbildern (ab ca. 1000 px Breite) wird das Video schärfer.
