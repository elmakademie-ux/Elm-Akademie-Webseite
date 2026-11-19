# DTZ B1.1 – 15 Muster-E-Mails als Lernvideos (ELM Akademie)

Aus dem PDF „DTZ B1.1 – 15 Muster-E-Mails“ entsteht für jede E-Mail ein 60-Sekunden-Video
(1080 × 1920, 30 fps, MP4) für TikTok, Instagram Reels und YouTube Shorts.

> Hinweis aus dem PDF: Die Mustertexte sind Übungshilfen, keine offiziellen DTZ-Prüfungslösungen.

## Projektstruktur
```
videos/dtz_muster/
├── README.md       diese Anleitung
├── muster.py       die 5 Aufgaben und 15 E-Mails + Listen der Konnektoren/Modalverben  ← Texte hier
├── render.py       Video-Vorlage (Einstellungen ganz oben: Farben, Tempo, Musik, Aussprache)
├── bilder/logo.png ELM-Logo
└── ausgabe/        fertige Videos: dtz_aufgabe1_beispiel1.mp4 … dtz_aufgabe5_beispiel3.mp4
```

## Aufbau jedes Videos
1. **Einleitung**: „Aufgabe X · Beispiel Y“ + Thema, Farblegende Konnektor / Modalverb.
2. **Aufgabe**: Die Aufgabe wird vorgelesen (Wörter werden mitgelesen), die 4 Punkte leuchten nacheinander auf.
3. **E-Mail**: Betreff, Anrede, Absätze und Gruß werden getippt, während die Stimme genau diesen Text vorliest.
   - Jeder Absatz hat die Farbe des Punktes, den er beantwortet; auf der Aufgabenkarte erscheint ein Häkchen.
   - **Konnektoren** (weil, dass, deshalb, außerdem …) orange, **Modalverben** (möchte, kann, könnten …) lila.
   - Lange E-Mails scrollen automatisch mit.
4. **Abschluss**: „Wichtige Wörter“ aus genau dieser E-Mail, „Folge der ELM Akademie“, Logo.

Bildschirm und Stimme zeigen/sprechen immer denselben Text. Die Pausen zwischen den Absätzen werden
automatisch so gewählt, dass jedes Video genau 60 Sekunden dauert.

## Bearbeiten
- **Texte** in `muster.py`: `absaetze` ist eine Liste aus (Text, Punkt). Punkt 0–3 = welcher Aufgaben-Punkt
  beantwortet wird, `None` = kein eigener Punkt.
- **Farben, Sprechtempo, Musik, Aussprache-Hilfen** oben in `render.py` unter EINSTELLUNGEN.
- Weitere Konnektoren/Modalverben: Listen `KONNEKTOREN` / `MODALVERBEN` in `muster.py`.

## Exportieren
Voraussetzungen: Python 3, `pip install pillow numpy piper-tts`, `ffmpeg`.
```bash
cd videos/dtz_muster
python3 render.py 1              # Video Nr. 1 (Aufgabe 1 · Beispiel 1)
python3 render.py 4 5 6          # mehrere
python3 render.py alle           # alle 15 (ca. 2 Minuten pro Video)
python3 render.py 7 --preview    # nur Vorschaubilder in vorschau/
```
Nummern: 1–3 = Aufgabe 1, 4–6 = Aufgabe 2, 7–9 = Aufgabe 3, 10–12 = Aufgabe 4, 13–15 = Aufgabe 5.

## Gesamtvideo 16:9 (YouTube)
```bash
python3 render.py gesamt          # alle 15 E-Mails im Querformat + Einleitung + Satzmuster/Lerntipp
python3 render.py 3 --16x9        # einzelne E-Mail im Querformat
```
Ergebnis: `dtz_15_muster_emails_16x9.mp4` (1920 × 1080, ca. 15½ Minuten) und `kapitel_youtube.txt`
(Zeitmarken für die YouTube-Beschreibung → YouTube zeigt daraus Kapitel an).
Im Querformat steht links die Aufgabe mit den 4 Punkten und ein Grammatik-Feld, das die Konnektoren und
Modalverben der E-Mail live sammelt; rechts wird die E-Mail getippt. Zwischenteile liegen in `ausgabe_16x9/`
(nicht in Git; bereits fertige Teile werden beim nächsten Lauf wiederverwendet – zum Neu-Rendern dort löschen).

## Hinweise
- Stimme „Thorsten“ (Piper TTS, CC0), KI-generiert → beim Posten als KI-Inhalt kennzeichnen.
- Musik wird vom Programm erzeugt, daher keine Lizenzfragen.
