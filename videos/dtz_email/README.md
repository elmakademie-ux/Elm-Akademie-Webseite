# DTZ Schreiben – Eine E-Mail schreiben (ELM Akademie)

60-Sekunden-Lernvideo (1080 × 1920, 30 fps, MP4) für TikTok, Instagram Reels und YouTube Shorts.

## Projektstruktur
```
videos/dtz_email/
├── README.md        diese Anleitung
├── inhalt.py        Aufgabe, E-Mail-Text, Sprechertexte, Farben  ← hier bearbeiten
├── render.py        Technik: Zeitplan, E-Mail-Fenster mit Tipp-Animation, Karaoke-Untertitel, Export
├── bilder/logo.png  ELM-Logo
└── dtz_email.mp4    fertiges Video
```

## Ablauf
| Teil | Inhalt |
|---|---|
| Einleitung | „E-Mail schreiben – Deutsch-Test für Zuwanderer“ |
| 1 Aufgabe lesen | Aufgabenkarte, die 4 Punkte leuchten nacheinander auf |
| 2 Betreff | Betreff wird getippt und vorgelesen |
| 3 Anrede | „Sehr geehrte Damen und Herren,“ + Hinweis informell „Liebe Anna, / Lieber Tom,“ |
| 4 Alle Punkte | 4 Sätze werden getippt; jeder Satz hat die Farbe seines Punktes, auf der Aufgabenkarte erscheint ein Häkchen |
| 5 Schluss & Gruß | „Vielen Dank für Ihre Hilfe.“ – „Mit freundlichen Grüßen“ + Name |
| 6 Prüfen | Checkliste: alle 4 Punkte, Anrede, Gruß und Name |
| Abschluss | Logo, „Viel Erfolg beim DTZ!“, „Folge der ELM Akademie“ |

Alles, was gesprochen wird, steht auch auf dem Bildschirm: Erklärungen als Karaoke-Untertitel,
E-Mail-Teile werden genau dann getippt, wenn die Stimme sie vorliest.

## Bearbeiten (`inhalt.py`)
- `AUFGABE`, `PUNKTE`: die Prüfungsaufgabe.
- `EMAIL`: die Teile der Beispiel-E-Mail (Betreff, Anrede, p1–p4, Schluss, Gruß).
- `SCHRITTE`: Ablauf mit `("sagen", "Text")` und `("tippen", "teil")`.
- `AUSSPRACHE`: nur für die Stimme (z. B. „DTZ“ → „De Te Zett“), der Bildschirm zeigt den Originaltext.
- `SPRECHTEMPO`, `MUSIK_LAUTSTAERKE`, Farben.

Die Pausen werden automatisch so berechnet, dass das Video genau 60 Sekunden dauert.
Ist der Text zu lang, wird die Stimme automatisch etwas schneller.

## Neu exportieren
Voraussetzungen: Python 3, `pip install pillow numpy piper-tts`, `ffmpeg`.
```bash
cd videos/dtz_email
python3 render.py --preview   # Vorschaubilder in vorschau/
python3 render.py             # fertiges Video → dtz_email.mp4 (ca. 2 Minuten)
```

## Hinweise
- Stimme: „Thorsten“ (Piper TTS, CC0), KI-generiert → beim Posten als KI-Inhalt kennzeichnen.
- Musik wird vom Programm erzeugt, daher keine Lizenzfragen.
