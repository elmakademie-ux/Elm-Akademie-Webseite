# Projektplan: Videoreihe „Begrüßung, sich vorstellen und Namen kennenlernen“

## 1. Ziel und Umfang
Vier eigenständige Lernvideos (A1, A2, B1, B2) mit denselben Figuren (Mia, Jonas), 3D-Cartoon-Look,
deutschen Untertiteln, für YouTube (16:9), TikTok/Instagram (9:16-Zuschnitt).

## 2. Lieferumfang (Phase 1 – erledigt)
| Video | Szenen | Zeilen | Untertitel | geschätzte Länge | Setting |
|---|---|---|---|---|---|
| A1 | 10 | 41 | 42 | ca. 3:35 | Park am Morgen; du |
| A2 | 11 | 47 | 55 | ca. 5:40 | erster Arbeitstag, Büro; du |
| B1 | 10 | 47 | 70 | ca. 5:25 | Geburtstagsparty; du |
| B2 | 10 | 42 | 70 | ca. 4:45 | Fachkonferenz; Sie |

Je Video: Hook, Niveau-Einführung, Dialogszenen, Wortschatz, Grammatik, Übung, Abschluss.
Dazu: Prompts je Szene, Sprechertexte/TTS-Manifest, SRT/VTT, Schnittliste, Validierung.

## 3. Didaktische Progression
| Niveau | Satzbau | Inhalte |
|---|---|---|
| A1 | kurze Hauptsätze (≤ 10 Wörter), langsam | Hallo, Guten Morgen, Name, Herkunft, Freut mich, Tschüss; ich/du-Verbformen; W-Fragen |
| A2 | einfache Nebensätze (weil, wenn, obwohl), seit + Dativ, Perfekt | Kollegen, Herkunft/Wohnort, Aufenthaltsdauer, Deutschkenntnisse, Erfahrungen |
| B1 | Konnektoren (weil, obwohl, deshalb, trotzdem, außerdem, denn), Relativsatz | Party-Smalltalk, gemeinsame Bekannte, Beruf, Erfahrungen, Meinungen begründen |
| B2 | komplexe Sätze, Konjunktiv II, sofern/allerdings, Relativsatz mit Präposition, formell (Sie) | Konferenz, Tätigkeiten, Fachthemen (KI im Unterricht), Argumentation, Visitenkarten, Zusammenarbeit |

## 4. Produktionsphasen
| Phase | Inhalt | Status | Freigabe nötig? |
|---|---|---|---|
| 1 | Drehbücher, Prompts, Untertitel, Struktur, QA-Skripte | **fertig** | – |
| 2 | Lektorat durch Muttersprachler/Lehrkraft, Korrekturen in `script.json` | offen | nein |
| 3 | Referenzbilder Mia/Jonas erzeugen, auswählen, freigeben | offen | **ja (Kosten)** |
| 4 | Stimmen auswählen und testen (kurzer Probelauf) | offen | **ja (Kosten)** |
| 5 | Pilot: eine Szene (z. B. A1-S04) komplett erzeugen, Konsistenz prüfen | offen | **ja (Kosten)** |
| 6 | Restliche Szenen erzeugen, Audiodauern → Untertitel-Sync | offen | **ja (Kosten)** |
| 7 | Schnitt, Einblendungen, Musik, Endcard, Export 16:9 und 9:16 | offen | nein |
| 8 | Veröffentlichung (Metadaten liegen in `script.json → social`) | offen | **ja (ausdrücklich)** |

## 5. Mengengerüst (für die Kostenplanung)
`python3 scripts/generate.py plan`: ca. 11.600 TTS-Zeichen und mindestens 168 Clips (ca. 1.100 Videosekunden)
für einen Durchlauf. Praktisch 2–4 Versuche pro Clip einplanen. Preise sind nicht hinterlegt und müssen
beim gewählten Anbieter erfragt werden.

## 6. Risiken und Gegenmaßnahmen
| Risiko | Gegenmaßnahme |
|---|---|
| Figuren sehen von Clip zu Clip anders aus | feste Textblöcke in jedem Prompt, Referenzbilder, Checkliste, Pilot vor Serie |
| Falsche deutsche Schrift im KI-Video | Text im Prompt verboten, Einblendungen in der Postproduktion |
| Lippen passen nicht zur Sprache | Modelle mit Audioeingabe/Lip-Sync-Schritt; Clips ≤ 8 s an Zeilengrenzen |
| Untertitel laufen asynchron | Zeiten aus echten Audiodauern (`durations.json`) neu berechnen |
| Aussprache von Abkürzungen/Namen | `pronunciation.json`, Hörprobe vor der Serie |
| Sprachliche Fehler | `validate.py`, Lektorat in Phase 2 |
| Ungewollte Kosten/Veröffentlichung | kein Adapter implementiert, Schlüssel nur in `.env`, Freigabe je Phase |

## 7. Erweiterbarkeit
Neues Thema/Niveau: Ordner `videos/<Name>/script.json` nach dem Muster anlegen, in `LEVELS`
(`scripts/lib.py`) und `voices.json` (Tempo/Pausen) eintragen, `build.py` und `validate.py` ausführen.
Weitere Sprachen für Untertitel: Zeilen in `script.json` um Felder wie `text_en` ergänzen und `build.py` erweitern.
