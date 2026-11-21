"""
Folge 2: Der schlaue Schüler   (Lehrer "L" und Schüler Ali "A")

Jede Zeile: wer, text, optional
  le / ae : Gesichtsausdruck Lehrer / Ali
            (neutral, annoyed, puzzled, innocent, smug, suspicious, shocked, grin, tired)
  la / aa : Arme Lehrer (hips, point, palm, shrug, facepalm) / Ali (rest, explain, shrug, scratch, chin)
            je ein Paar (linker Arm, rechter Arm)
  prop    : "wecker" (Wecker klingelt im Bild) oder "zzz"
  pause_davor : zusätzliche Pause in Sekunden (für den Witz)
Nicht angegebene Werte bleiben wie in der Zeile davor.
"""

TITEL = ("Der schlaue", "Schüler")
UNTERTITEL = "Deutsch lernen · ELM Akademie"

START = 2.6            # Sekunde, in der der Dialog beginnt (davor Titel)
PAUSE = 0.34           # Pause zwischen den Sätzen
REAKTION_DAUER = 2.3   # Zeit nach dem letzten Satz (Lachen, Facepalm)
OUTRO_DAUER = 3.2      # Logo-Abspann

AUSSPRACHE = {}

ZEILEN = [
    dict(wer="L", text="Ali, warum kommst du jeden Tag zu spät?",
         le="annoyed", la=("hips", "point"), ae="innocent"),
    dict(wer="A", text="Herr Lehrer, ich habe ein Problem mit meinem Wecker.",
         ae="innocent", aa=("rest", "explain"), le="annoyed", la=("hips", "hips")),
    dict(wer="L", text="Was ist denn das Problem?",
         le="puzzled", la=("hips", "palm"), ae="neutral", aa=("rest", "rest")),
    dict(wer="A", text="Er klingelt immer, wenn ich schlafe!",
         ae="grin", aa=("explain", "explain"), le="puzzled", la=("hips", "hips"), prop="wecker"),
    dict(wer="L", text="Dann stell ihn früher!",
         le="annoyed", la=("hips", "point"), ae="neutral", aa=("rest", "chin")),
    dict(wer="A", text="Das habe ich gemacht.",
         ae="smug", aa=("rest", "shrug"), le="suspicious", la=("hips", "hips")),
    dict(wer="L", text="Und?",
         le="suspicious", la=("hips", "palm"), ae="smug", aa=("rest", "rest")),
    dict(wer="A", text="Jetzt schlafe ich noch länger!",
         ae="grin", aa=("shrug", "shrug"), le="suspicious", la=("hips", "hips"),
         pause_davor=0.45, prop="zzz"),
]

# Pointe: Lehrer fasst sich an den Kopf, Ali grinst
REAKTION = dict(le="tired", la=("hips", "facepalm"), ae="grin", aa=("rest", "scratch"))
