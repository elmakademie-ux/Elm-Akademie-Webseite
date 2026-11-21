# Deutsch lernen – Begrüßung und sich vorstellen (A1–B2)

Vier eigenständige Lernvideos (A1, A2, B1, B2) mit den wiederkehrenden Figuren **Mia** und **Jonas**
(3D-Cartoon-Stil), geplant für YouTube, TikTok und Instagram.

**Stand:** Drehbücher, Prompts, Untertitel usw. sind fertig und geprüft. Zusätzlich gibt es eine **kostenlos
produzierte 2D-Version** aller vier Videos (`videos/<N>/<N>_9x16.mp4`). **Keine kostenpflichtige API wurde
aufgerufen, nichts wurde veröffentlicht.** Siehe [PROJEKTPLAN.md](PROJEKTPLAN.md).

## Struktur

```
deutsch-lernvideo/
├── README.md, PROJEKTPLAN.md
├── videos/{A1,A2,B1,B2}/
│   ├── script.json        ← QUELLE DER WAHRHEIT (hier bearbeiten)
│   ├── script.md          lesbares Drehbuch (erzeugt)
│   └── edit_list.json     Schnittliste je Szene (erzeugt)
├── prompts/<Niveau>/      KI-Videoprompt je Szene (.md) + prompts.json (erzeugt)
├── subtitles/             <Niveau>.srt / .vtt / .timeline.json (erzeugt)
├── audio/
│   ├── voices.json        Stimmbesetzung, Sprechtempo, Pausen
│   ├── pronunciation.json Aussprachehilfen (nur für TTS, nicht für Untertitel)
│   └── <Niveau>/          manifest.json + tts_script.md (erzeugt); später die MP3-Dateien
├── characters/            characters.json (Aussehen, Kleidung, Stimme), reference/ (Referenzbilder)
├── assets/                Stilrichtlinie, später Logo/Musik
├── clips/                 (später) fertige KI-Clips, nicht eingecheckt
└── scripts/               lib.py, build.py, validate.py, generate.py, assemble.py, providers.json
```

## Workflow

```bash
python3 scripts/build.py          # script.json → Markdown, Prompts, Untertitel, Audio-Manifeste
python3 scripts/validate.py       # Qualitätsprüfung (Exit-Code 1 bei Fehlern)
python3 scripts/generate.py plan  # Mengen und optionale Kostenschätzung – ohne Netzwerk
python3 scripts/assemble.py A1    # ffmpeg-Skript aus der Schnittliste (wird nicht ausgeführt)
```
Nur Python 3 (Standardbibliothek) wird benötigt.

Eine Szene ändern: In `videos/<N>/script.json` die Szene bearbeiten → `build.py` → `validate.py`.
Jede Szene hat eine ID (`A1-S03`) und jede Sprechzeile ebenfalls (`A1-S03-L02`); Prompts, Audio-Dateien
und Untertitel verwenden dieselben IDs, so lassen sich einzelne Szenen neu erzeugen und später zusammensetzen.

## Aufbau jedes Videos

| # | Anforderung | Szenentyp / Ort |
|---|---|---|
| 1 | Hook | Szene `…-S01` (`hook`) |
| 2 | Einführung zum Niveau | `…-S02` (`intro`) |
| 3 | Szenenbeschreibung | Feld `description`, `location` jeder Szene |
| 4 | Dialoge mit Sprecherzuordnung | `dialog`-Szenen, Feld `lines` |
| 5 | Regieanweisungen | Feld `direction` (Kamera, Licht, Animation, Musik) |
| 6 | KI-Videoprompts je Szene | `prompts/<N>/<SzeneID>.md` |
| 7 | Sprechertexte für KI-Stimmen | `audio/<N>/tts_script.md`, `manifest.json` |
| 8 | Untertitel | `subtitles/<N>.srt/.vtt` |
| 9 | Wortschatz | `vocabulary` + Szene `vocab` |
| 10 | Grammatik | `grammar` + Szene `grammar` |
| 11 | Wiederholungsübung | `exercise` + Szene `exercise` |
| 12 | Abschluss mit Mitmach-Aufruf | letzte Szene (`outro`) |

## Entscheidungen, die du ändern kannst

* **Reboot-Prinzip:** Jede Folge ist ein eigenes erstes Kennenlernen von Mia und Jonas. Aussehen, Kleidung und
  Stimmen sind immer identisch; nur die Lebensdaten (z. B. „seit einem Jahr in Köln“) ändern sich je Folge
  (`characters.json → episode_profiles`).
* **Figuren:** Namen (Mia Navarro aus Valencia, Jonas Keller aus Leipzig), Kleidung und Aussehen sind Vorschläge.
  In B2 kommt nur ein Namensschild hinzu. Kleidung ändern: `characters.json`, danach `build.py`.
* **Anrede:** A1–B1 „du“, B2 „Sie“ (Konferenz). Der Erzähler spricht die Zuschauer immer mit „du“ an.
* **Sprecher:** Mia, Jonas und ein Erzähler (Off-Stimme für Hook, Einführung, Grammatik, Übung).
* **Format:** 9:16-Hochformat (1080 × 1920) für TikTok, Reels und Shorts. Die Prompts verlangen Hochformat-Komposition. Für YouTube-Querformat wäre ein eigener 16:9-Durchlauf nötig (`FRAMING_BLOCK` in `scripts/lib.py` ändern).
* **Text im Bild:** KI-Videomodelle schreiben deutsche Wörter oft falsch. Darum verbieten die Prompts Text;
  Einblendungen (`on_screen`) und Untertitel werden in der Postproduktion gesetzt.
* **Dauer:** Die Zeiten sind Schätzungen (Wörter/Sprechtempo + Pausen): A1 ≈ 3:35, A2 ≈ 5:40, B1 ≈ 5:25, B2 ≈ 4:45.
  Für Kurzformate lassen sich Szenen einzeln verwenden (z. B. nur eine Dialogszene plus Hook).

## Integration von KI-Diensten (geplant, noch nicht aktiv)

1. **Referenzbilder:** Mit `characters.json → reference_image_prompts` je Figur ein Charakterblatt erzeugen,
   prüfen und nach `characters/reference/` legen. Diese Bilder in jedem Videoaufruf als Bildeingabe verwenden.
2. **Sprache:** `audio/<N>/manifest.json` enthält je Zeile Text, SSML, Stimme (Umgebungsvariable) und Zieldatei.
   Nach dem Erzeugen die echten Dauern in `audio/<N>/durations.json` (`{"A1-S03-L01": 1.8, …}`) eintragen
   und `build.py` ausführen – Untertitel und Schnittliste werden dann exakt synchron.
3. **Video:** `prompts/<N>/prompts.json` liefert Prompt, Clip-Aufteilung (≤ 8 s) und Referenzbilder je Szene.
   Lippensynchronität entweder über Modelle mit Audioeingabe oder über einen separaten Lip-Sync-Schritt.
4. **Zusammenbau:** `assemble.py` erzeugt das lokale ffmpeg-Skript.

Zugangsdaten **ausschließlich** über Umgebungsvariablen (`.env.example` → `.env`, wird nicht eingecheckt).
`generate.py` hat bewusst keine Anbieter-Adapter und bricht bei `tts`/`image`/`video` ab.
Vor jedem kostenpflichtigen Schritt: Freigabe einholen, `generate.py plan` mit eingetragenen Preisen ansehen.

## Qualitätssicherung

`validate.py` prüft automatisch:
Szenenaufbau und Pflichtfelder · GER-Niveau (max. Satzlänge, A1 ohne Nebensatz-Konnektoren, Pflicht-
Strukturen je Niveau) · Du/Sie-Konsistenz · Figurenbeschreibung in jedem Prompt, keine abweichende Kleidung ·
Typografie und typische Fehlermuster · Ziffern/Abkürzungen (Aussprache) · Untertitel (max. 2 Zeilen × 42 Zeichen,
Lesetempo, keine Überlappung, Text identisch mit dem Sprechtext) · Wortschatz kommt im Skript vor ·
Übungslösungen werden gesprochen.

**Grenzen:** Das ersetzt kein muttersprachliches Lektorat. Vor der Produktion empfohlen: (1) Texte von einer
Lehrkraft lesen lassen, (2) Stimmen und Aussprache hören („Kölsch“, „Tandempartnerin“, „KI“), (3) Figuren-Konsistenz
an generierten Clips visuell prüfen (`characters.json → consistency_checklist`), (4) Untertitel gegen das fertige Audio abgleichen.

## Kostenlose Produktion (2D-Version, bereits erzeugt)

| Video | Datei | Länge |
|---|---|---|
| A1 | `videos/A1/A1_9x16.mp4` | 2:43 |
| A2 | `videos/A2/A2_9x16.mp4` | 4:07 |
| B1 | `videos/B1/B1_9x16.mp4` | 4:19 |
| B2 | `videos/B2/B2_9x16.mp4` | 4:32 |

1080 × 1920, 30 fps, mit Sprache, Hintergrundmusik, Untertiteln (28 Zeichen/Zeile) und Endcard.

```bash
pip install piper-tts                      # einmalig; Stimmen nach .cache/ laden (siehe scripts/make_audio.py)
python3 scripts/make_audio.py              # Sprache (Piper, lokal) + audio/<N>/durations.json
python3 scripts/build.py && python3 scripts/validate.py   # Untertitel mit echten Dauern
python3 scripts/render2d.py A1 A2 B1 B2    # Video; --still 5,20 für Standbilder, --seconds 10 für Probelauf
```
* Figuren und Hintergründe werden in `scripts/anim_art.py` gezeichnet; Layout/Animation in `scripts/render2d.py`.
* **Stimmen:** Mia = ramona, Jonas = thorsten (CC0), Erzähler = karlsson (Piper, de_DE). Die Stimmen klingen
  synthetisch. Die Lizenz der M-AILABS-Stimmen (ramona, karlsson) vor kommerzieller Nutzung prüfen.
* **Grenzen:** 2D statt 3D-Kinolook; Lippenbewegung folgt der Lautstärke, nicht den Lauten; Aussprache nicht
  per Hörprobe geprüft. Die KI-Prompts in `prompts/` bleiben für eine spätere 3D-Version nutzbar.
