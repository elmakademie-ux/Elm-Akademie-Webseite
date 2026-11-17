"""
INHALT des Lernvideos "Mein Tagesablauf" (A1)
=============================================
Hier stehen alle Texte, Uhrzeiten und Bilder. Nach einer Änderung einfach
neu exportieren:  python3 render.py   (siehe README.md)

Markierung für farbige Verben:  *Wort*   Beispiel: "Um halb sieben *stehe* ich *auf*."
"""

TITEL = "Mein Tagesablauf"
UNTERTITEL = "Alltag & Routinen"
NIVEAU = "Deutsch · A1"

# Einleitung (Sekunde 0 bis INTRO_DAUER)
INTRO_SPRECHER = "Hallo! Ich erzähle euch von meinem Tagesablauf."

# Die sieben Szenen
#   zeit        = große Uhrzeit (HH:MM)
#   sprechweise = wie man die Uhrzeit sagt (kleiner Hinweis unter der Uhr)
#   verb        = Infinitiv für das Etikett am Bild und die Wiederholung am Ende
#   satz        = wird GESPROCHEN und genau so auf dem Bildschirm gezeigt
#                 (Verben mit *...* markieren – die Sternchen werden nicht vorgelesen)
#   bild        = Datei im Ordner bilder/
SZENEN = [
    dict(zeit="06:30", sprechweise="halb sieben", verb="aufstehen",
         satz="Um halb sieben *stehe* ich *auf*.", bild="1_aufstehen.png"),
    dict(zeit="06:40", sprechweise="zwanzig vor sieben", verb="Zähne putzen",
         satz="Danach *putze* ich mir die Zähne.", bild="2_zaehne.png"),
    dict(zeit="07:00", sprechweise="sieben Uhr", verb="frühstücken",
         satz="Um sieben Uhr *frühstücke* ich.", bild="3_fruehstueck.png"),
    dict(zeit="07:20", sprechweise="zwanzig nach sieben", verb="sich anziehen",
         satz="Anschließend *ziehe* ich mich *an*.", bild="4_umziehen.png"),
    dict(zeit="07:45", sprechweise="Viertel vor acht", verb="zur Arbeit gehen",
         satz="Um Viertel vor acht *gehe* ich zur Arbeit.", bild="5_arbeit.png"),
    dict(zeit="17:00", sprechweise="fünf Uhr nachmittags", verb="einkaufen gehen",
         satz="Am Nachmittag *gehe* ich *einkaufen*.", bild="6_einkaufen.png"),
    dict(zeit="18:30", sprechweise="halb sieben abends", verb="Fitness machen",
         satz="Am Abend *mache* ich Fitness.", bild="7_fitness.png"),
]

# Abschluss
OUTRO_TITEL = "Das ist mein Tagesablauf!"
OUTRO_SPRECHER = "Das ist mein Tagesablauf!"
OUTRO_AUFRUF = "Folge der ELM Akademie!"

# Hinweis, der nach jedem Satz zum Nachsprechen auffordert
NACHSPRECHEN = "Sprich nach!"

# Zeiten in Sekunden: INTRO + 7 × SZENE + OUTRO = 60
INTRO_DAUER = 5.0
SZENEN_DAUER = 7.0
OUTRO_DAUER = 6.0

# Stimme: 1.0 = normal, größer = langsamer (für A1 etwas langsamer)
SPRECHTEMPO = 1.08
# Musik-Lautstärke (0 = aus, 0.2 = leise)
MUSIK_LAUTSTAERKE = 0.18

# Farben (R, G, B) – angelehnt an das ELM-Logo
FARBE_HINTERGRUND = (248, 245, 239)
FARBE_TEXT = (27, 54, 104)        # Dunkelblau
FARBE_VERB = (237, 140, 20)       # Orange für Verben
FARBE_AKZENT = (46, 140, 90)      # Grün
FARBE_GRAU = (110, 118, 135)
