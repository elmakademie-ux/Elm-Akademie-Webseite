# Comic-Videos (ELM Akademie)

Strichmännchen-Dialoge im Klassenzimmer, 1080 × 1920, 30 fps, für Reels, TikTok und Shorts.
Große Wort-für-Wort-Untertitel (Sprecher mit Namensschild und Farbe), Stimmen, Musik, Logo.

```
videos/comic/
├── render.py                    Engine (Figuren, Szene, Untertitel, Ton)
├── folgen/<name>.py             Dialog einer Folge  ← hier bearbeiten / neue Folge anlegen
└── ausgabe/<name>.mp4           fertige Videos
```

## Neue Folge
`folgen/schlauer_schueler.py` kopieren, Titel und `ZEILEN` ändern (wer = "L" Lehrer / "A" Ali,
Text, Gesichtsausdruck `le`/`ae`, Arme `la`/`aa`, `prop` = "wecker" oder "zzz"), dann:
```bash
cd videos/comic
python3 render.py <name> --preview   # Vorschaubilder in vorschau/
python3 render.py <name>             # Video → ausgabe/<name>.mp4 (ca. 1 Minute)
```
Voraussetzungen: Python 3, `pip install pillow numpy piper-tts`, `ffmpeg`.
Die Stimme wird beim ersten Lauf automatisch geladen (~110 MB, nicht im Git).

## Hinweis
Stimmen: „Thorsten“ (Piper TTS, CC0), KI-generiert, für Lehrer tiefer und für Ali höher gestellt.
Beim Posten als KI-Inhalt kennzeichnen. Musik wird vom Programm erzeugt.
