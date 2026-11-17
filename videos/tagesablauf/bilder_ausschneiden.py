"""
Schneidet die 7 Szenenbilder und das Logo aus der Collage bilder/collage_original.png.
Nur nötig, wenn du die Collage austauschst oder Ausschnitte ändern willst.

    python3 bilder_ausschneiden.py

Ausschnitte: (links, oben, rechts, unten) in Pixeln der Collage (1672 × 941).
Die eingebauten Uhrzeit-/Text-Schilder und Pfeile der Collage werden ausgespart.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
COLLAGE = HERE / "bilder" / "collage_original.png"

AUSSCHNITTE = {
    "1_aufstehen.png": (10, 72, 380, 394),
    "2_zaehne.png": (440, 72, 790, 376),
    "3_fruehstueck.png": (845, 72, 1195, 376),
    "4_umziehen.png": (1250, 73, 1620, 395),
    "5_arbeit.png": (130, 552, 470, 848),
    "6_einkaufen.png": (640, 552, 980, 848),
    "7_fitness.png": (1215, 552, 1555, 848),
}
LOGO = (1508, 6, 1668, 104)


def main():
    im = Image.open(COLLAGE).convert("RGB")
    # Logo oben rechts in Bild 4 mit dem Wandstück darunter überdecken
    x0, x1, y0, y1 = 1488, 1672, 0, 122
    src = im.crop((x0, y1, x1, y1 + (y1 - y0))).transpose(Image.FLIP_TOP_BOTTOM)
    patched = im.copy()
    patched.paste(src, (x0, y0))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rectangle((x0 + 6, y0, x1, y1 - 4), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(6))
    im4 = Image.composite(patched.filter(ImageFilter.GaussianBlur(3)), im, mask)

    for name, box in AUSSCHNITTE.items():
        (im4 if name.startswith("4_") else im).crop(box).save(HERE / "bilder" / name)
        print("gespeichert:", name)
    im.crop(LOGO).save(HERE / "bilder" / "logo.png")
    print("gespeichert: logo.png")


if __name__ == "__main__":
    main()
