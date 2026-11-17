"""
Schneidet die 8 Fotos aus bilder/collage_original.png (1672 × 941).
Ausgeschnitten wird nur der Fotostreifen zwischen Titelschild und Satzschild,
damit keine Texte im Bild stehen, die vom gesprochenen Text abweichen.

    python3 bilder_ausschneiden.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent

# (links, oben, rechts, unten) – Seitenverhältnis ca. 1,71 : 1 (wie die Bildkarte)
AUSSCHNITTE = {
    "haus.png": (70, 155, 407, 352),
    "wohnzimmer.png": (480, 155, 817, 352),
    "kueche.png": (900, 155, 1237, 352),
    "schlafzimmer.png": (1320, 155, 1657, 352),
    "bad.png": (0, 487, 359, 697),
    "kinderzimmer.png": (470, 487, 829, 697),
    "balkon.png": (874, 487, 1233, 697),
    "gesamt.png": (1290, 487, 1617, 678),
}


def main():
    im = Image.open(HERE / "bilder" / "collage_original.png").convert("RGB")
    for name, box in AUSSCHNITTE.items():
        im.crop(box).save(HERE / "bilder" / name)
        print("gespeichert:", name)


if __name__ == "__main__":
    main()
