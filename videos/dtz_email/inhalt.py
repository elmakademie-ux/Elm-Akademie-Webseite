"""
INHALT des Lernvideos "DTZ Schreiben – Eine E-Mail schreiben"
=============================================================
Alles, was gesprochen wird, steht genau so auf dem Bildschirm:
  ("sagen", "...")   -> Stimme + Untertitel (Karaoke)
  ("tippen", "id")   -> Stimme liest den E-Mail-Teil vor, während er im E-Mail-Fenster getippt wird
Danach neu exportieren:  python3 render.py   (siehe README.md)
"""

NIVEAU = "DTZ · Schreiben"
TITEL = "E-Mail schreiben"
UNTERTITEL = "Deutsch-Test für Zuwanderer"

# Die Prüfungsaufgabe (wird im Video als Karte gezeigt)
AUFGABE = ("Sie haben am Montag einen Termin beim Arzt, können aber nicht kommen. "
           "Schreiben Sie eine E-Mail an die Praxis.")
PUNKTE = ["Termin absagen", "Grund", "neuer Termin", "Frage"]

EMAIL_AN = "praxis@beispiel.de"

# Teile der E-Mail (werden getippt und vorgelesen)
EMAIL = {
    "betreff": "Absage meines Termins am Montag",
    "anrede": "Sehr geehrte Damen und Herren,",
    "p1": "leider kann ich am Montag um 10 Uhr nicht zu meinem Termin kommen.",
    "p2": "Mein Sohn ist krank und ich muss zu Hause bleiben.",
    "p3": "Ist am Mittwoch oder Donnerstag ein Termin frei?",
    "p4": "Muss ich etwas zum Termin mitbringen?",
    "schluss": "Vielen Dank für Ihre Hilfe.",
    "gruss": "Mit freundlichen Grüßen\nAhmad Karimi",
}
# welcher E-Mail-Teil zu welchem Aufgaben-Punkt gehört (für Farben und Häkchen)
PUNKT_ZU_TEIL = {"p1": 0, "p2": 1, "p3": 2, "p4": 3}

INFORMELL = "informell: Liebe Anna, / Lieber Tom,"

# Ablauf: Einleitung, 6 Schritte, Abschluss
EINLEITUNG = [("sagen", "DTZ Schreiben: So schreibst du eine gute E-Mail.")]
SCHRITTE = [
    dict(titel="Aufgabe lesen", ablauf=[
        ("sagen", "Lies zuerst die Aufgabe genau. Du musst zu allen vier Punkten etwas schreiben.")]),
    dict(titel="Betreff", ablauf=[
        ("sagen", "Schreib einen kurzen Betreff."),
        ("tippen", "betreff")]),
    dict(titel="Anrede", ablauf=[
        ("sagen", "Dann kommt die Anrede. Formell schreibst du:"),
        ("tippen", "anrede"),
        ("sagen", "Informell schreibst du zum Beispiel: Liebe Anna.")]),
    dict(titel="Alle Punkte", ablauf=[
        ("sagen", "Jetzt schreibst du zu jedem Punkt ein oder zwei Sätze."),
        ("tippen", "p1"), ("tippen", "p2"), ("tippen", "p3"), ("tippen", "p4")]),
    dict(titel="Schluss & Gruß", ablauf=[
        ("sagen", "Zum Schluss ein kurzer Satz, dann der Gruß und dein Name."),
        ("tippen", "schluss"), ("tippen", "gruss")]),
    dict(titel="Prüfen", ablauf=[
        ("sagen", "Prüfe am Ende: Hast du alle Punkte, die Anrede und den Gruß?")]),
]
CHECKLISTE = ["alle 4 Punkte", "Anrede", "Gruß und Name"]
ABSCHLUSS = [("sagen", "Viel Erfolg beim DTZ! Folge der ELM Akademie.")]

# Aussprache-Hilfen nur für die Stimme (auf dem Bildschirm bleibt der Originaltext)
AUSSPRACHE = {"DTZ": "De Te Zett", "10 Uhr": "zehn Uhr", "E-Mail": "Imeil"}

GESAMTDAUER = 60.0
SPRECHTEMPO = 1.0            # größer = langsamer
MUSIK_LAUTSTAERKE = 0.14

# Farben
FARBE_TEXT = (27, 54, 104)
FARBE_AKZENT = (237, 140, 20)
FARBE_HINTERGRUND = (244, 246, 250)
FARBEN_PUNKTE = [(237, 140, 20), (124, 77, 255), (0, 150, 136), (233, 30, 99)]
FARBE_OK = (46, 160, 90)
