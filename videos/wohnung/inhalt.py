"""
INHALT des Lernvideos "Meine Wohnung" (A1)
==========================================
Hier stehen alle Texte, Wörter und Farben. Danach neu exportieren:  python3 render.py
(siehe README.md)

Wichtig: Jeder Satz wird GESPROCHEN und genau so auf dem Bildschirm gezeigt.
Nomen aus der Wortliste werden automatisch in der Farbe ihres Artikels markiert.
"""

TITEL = "Meine Wohnung"
NIVEAU = "Deutsch · A1"

INTRO_SATZ = "Hallo! Ich zeige euch meine Wohnung."

# Wortschatz: bestimmt auch die Farben der Nomen in allen Sätzen
VOKABELN = [
    "die Wohnung", "das Wohnzimmer", "die Küche", "das Schlafzimmer", "das Badezimmer",
    "das Kinderzimmer", "der Balkon", "das Sofa", "der Tisch", "der Kühlschrank",
    "das Bett", "der Schrank", "die Dusche", "das Waschbecken",
]

# Szenen
#   bild    = Illustration (haus, wohnzimmer, kueche, schlafzimmer, bad, kinderzimmer, balkon,
#             gesamt). Liegt in bilder/ ein Foto mit diesem Namen (z. B. bilder/kueche.jpg),
#             wird das Foto statt der Illustration verwendet.
#   titel   = Überschrift (mit Artikel = farbig)
#   saetze  = werden gesprochen + als Untertitel (Karaoke) gezeigt
#   woerter = neue Wörter: werden groß eingeblendet, vorgesprochen, dann Pause zum Nachsprechen
#   pins    = Position des Wortes im Bild (x, y) im Bildformat 900 × 770
SZENEN = [
    dict(bild="haus", titel="die Wohnung",
         saetze=["Meine Wohnung ist sehr schön."],
         woerter=["die Wohnung"], pins={"die Wohnung": (450, 335)}),
    dict(bild="wohnzimmer", titel="das Wohnzimmer",
         saetze=["Hier ist das Wohnzimmer.", "Dort sehe ich fern und entspanne mich."],
         woerter=["das Wohnzimmer", "das Sofa", "der Tisch"],
         pins={"das Sofa": (690, 445), "der Tisch": (460, 612)}),
    dict(bild="kueche", titel="die Küche",
         saetze=["Das ist die Küche. Hier koche ich."],
         woerter=["die Küche", "der Kühlschrank"], pins={"der Kühlschrank": (770, 280)}),
    dict(bild="schlafzimmer", titel="das Schlafzimmer",
         saetze=["Hier ist mein Schlafzimmer. Hier schlafe ich."],
         woerter=["das Schlafzimmer", "das Bett", "der Schrank"],
         pins={"das Bett": (390, 525), "der Schrank": (760, 300)}),
    dict(bild="bad", titel="das Badezimmer",
         saetze=["Das ist das Badezimmer. Hier dusche ich."],
         woerter=["das Badezimmer", "die Dusche", "das Waschbecken"],
         pins={"die Dusche": (170, 330), "das Waschbecken": (470, 452)}),
    dict(bild="kinderzimmer", titel="das Kinderzimmer",
         saetze=["Das ist das Kinderzimmer."],
         woerter=["das Kinderzimmer"], pins={}),
    dict(bild="balkon", titel="der Balkon",
         saetze=["Meine Wohnung hat auch einen Balkon."],
         woerter=["der Balkon"], pins={}),
    dict(bild="gesamt", titel="Meine Wohnung",
         saetze=["Ich fühle mich in meiner Wohnung sehr wohl!"],
         woerter=[], pins={}),
]

# Abschluss
OUTRO_FRAGE = "Wie ist deine Wohnung?"          # wird auch gesprochen
OUTRO_SATZ_ANFANG = "Meine Wohnung ist …"
OUTRO_ADJEKTIVE = ["groß", "klein", "schön", "gemütlich"]
OUTRO_MARKE = "ELM Akademie – Deutsch lernen"

NACHSPRECHEN = "Sprich nach!"

# Gesamtlänge in Sekunden (die Pausen zum Nachsprechen werden automatisch angepasst)
GESAMTDAUER = 60.0
SPRECHTEMPO = 1.05          # größer = langsamer
MUSIK_LAUTSTAERKE = 0.16

# Farben (R, G, B)
FARBE_DER = (37, 99, 235)     # blau
FARBE_DIE = (220, 38, 38)     # rot
FARBE_DAS = (22, 150, 74)     # grün
FARBE_TEXT = (27, 54, 104)
FARBE_HINTERGRUND = (246, 244, 239)
FARBE_NACHSPRECHEN = (46, 140, 90)
