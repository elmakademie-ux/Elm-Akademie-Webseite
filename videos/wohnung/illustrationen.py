"""
Flache Raum-Illustrationen fuer "Meine Wohnung".
Koordinaten im Format 900 x 770; gezeichnet wird mit Supersampling fuer glatte Kanten.

    python3 illustrationen.py   -> speichert alle Illustrationen als PNG in illustrationen/
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BW, BH = 900, 770
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

C_DER, C_DIE, C_DAS = (37, 99, 235), (220, 38, 38), (22, 150, 74)


class P:
    """Kleiner Zeichen-Helfer mit Skalierung."""

    def __init__(self, scale, bg=(255, 255, 255)):
        self.s = scale
        self.img = Image.new("RGB", (int(BW * scale), int(BH * scale)), bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def _b(self, box):
        return [v * self.s for v in box]

    def rect(self, box, fill, r=0, outline=None, w=0):
        if r:
            self.d.rounded_rectangle(self._b(box), r * self.s, fill=fill, outline=outline,
                                     width=int(w * self.s))
        else:
            self.d.rectangle(self._b(box), fill=fill, outline=outline, width=int(w * self.s))

    def ell(self, box, fill, outline=None, w=0):
        self.d.ellipse(self._b(box), fill=fill, outline=outline, width=int(w * self.s))

    def circ(self, cx, cy, r, fill, outline=None, w=0):
        self.ell((cx - r, cy - r, cx + r, cy + r), fill, outline, w)

    def poly(self, pts, fill):
        self.d.polygon([(x * self.s, y * self.s) for x, y in pts], fill=fill)

    def line(self, pts, fill, w):
        self.d.line([(x * self.s, y * self.s) for x, y in pts], fill=fill, width=int(w * self.s),
                    joint="curve")

    def arc(self, box, a0, a1, fill, w):
        self.d.arc(self._b(box), a0, a1, fill=fill, width=int(w * self.s))

    def text(self, xy, txt, size, fill, anchor="mm"):
        f = ImageFont.truetype(FONT, int(size * self.s))
        self.d.text((xy[0] * self.s, xy[1] * self.s), txt, font=f, fill=fill, anchor=anchor)

    def vgrad(self, box, c0, c1):
        x0, y0, x1, y1 = box
        n = int((y1 - y0))
        for k in range(n):
            t = k / max(1, n - 1)
            c = tuple(int(c0[j] + (c1[j] - c0[j]) * t) for j in range(3))
            self.rect((x0, y0 + k, x1, y0 + k + 1.2), c)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


# ----------------------------------------------------------------- Bausteine
def room(p, wall, floor, plank=True, floor_y=560):
    p.rect((0, 0, BW, floor_y), wall)
    p.rect((0, floor_y, BW, BH), floor)
    if plank:
        for x in range(0, BW, 90):
            p.line([(x, floor_y), (x - 40, BH)], shade(floor, 0.93), 2)
        for y in (620, 690):
            p.line([(0, y), (BW, y)], shade(floor, 0.95), 1.5)
    p.rect((0, floor_y - 10, BW, floor_y + 4), shade(wall, 1.06))


def window(p, box, sky=(190, 222, 245), frame=(255, 255, 255)):
    x0, y0, x1, y1 = box
    p.rect((x0 - 10, y0 - 10, x1 + 10, y1 + 10), frame, 8)
    p.vgrad((x0, y0, x1, y1), sky, shade(sky, 1.1))
    p.ell((x0 + 20, y0 + 25, x0 + 90, y0 + 55), (255, 255, 255, 200))
    p.rect(((x0 + x1) / 2 - 5, y0, (x0 + x1) / 2 + 5, y1), frame)
    p.rect((x0, (y0 + y1) / 2 - 5, x1, (y0 + y1) / 2 + 5), frame)
    p.rect((x0 - 20, y1 + 8, x1 + 20, y1 + 22), frame, 5)


def plant(p, x, y, s=1.0, pot=(214, 120, 80)):
    p.poly([(x - 35 * s, y - 60 * s), (x + 35 * s, y - 60 * s), (x + 26 * s, y), (x - 26 * s, y)], pot)
    for ang, ln in ((-60, 95), (-30, 120), (0, 130), (30, 115), (60, 90), (-10, 100), (15, 105)):
        a = math.radians(ang - 90)
        ex, ey = x + math.cos(a) * ln * s, y - 60 * s + math.sin(a) * ln * s
        p.line([(x, y - 60 * s), (ex, ey)], (70, 140, 90), 5 * s)
        p.ell((ex - 22 * s, ey - 12 * s, ex + 22 * s, ey + 12 * s), (90, 170, 110))


def frame_pic(p, box, inner=(160, 200, 230)):
    x0, y0, x1, y1 = box
    p.rect(box, (60, 70, 90), 6)
    p.rect((x0 + 10, y0 + 10, x1 - 10, y1 - 10), inner)
    p.poly([(x0 + 10, y1 - 10), (x0 + (x1 - x0) * 0.4, y0 + (y1 - y0) * 0.35), (x0 + (x1 - x0) * 0.65, y1 - 10)],
           (100, 150, 120))
    p.poly([(x0 + (x1 - x0) * 0.45, y1 - 10), (x0 + (x1 - x0) * 0.72, y0 + (y1 - y0) * 0.5), (x1 - 10, y1 - 10)],
           (80, 125, 100))
    p.circ(x1 - 40, y0 + 40, 14, (250, 210, 100))


# ----------------------------------------------------------------- Szenen
def haus(p):
    p.vgrad((0, 0, BW, BH), (150, 205, 245), (225, 240, 252))
    p.circ(770, 110, 55, (255, 215, 100))
    for cx, cy, s in ((150, 110, 1.0), (620, 70, 0.8)):
        for dx, dy, r in ((0, 0, 38), (40, -15, 45), (85, 0, 36)):
            p.circ(cx + dx * s, cy + dy * s, r * s, (255, 255, 255, 235))
    p.rect((0, 690, BW, BH), (120, 175, 95))
    p.rect((0, 715, BW, BH), (170, 170, 175))
    # Baeume
    for x in (95, 805):
        p.rect((x - 12, 560, x + 12, 700), (130, 90, 60))
        p.circ(x, 520, 75, (80, 160, 95))
        p.circ(x - 35, 560, 50, (95, 175, 105))
    # Haus
    p.rect((190, 150, 710, 705), (238, 214, 190), 6)
    p.rect((175, 125, 725, 160), (90, 100, 120), 6)
    for j in range(4):
        for i in range(3):
            x, y = 245 + i * 150, 190 + j * 120
            if (i, j) == (1, 3):   # hier ist die Haustuer
                continue
            hl = (i, j) == (1, 1)
            glass = (255, 222, 120) if hl else (185, 215, 240)
            p.rect((x - 8, y - 8, x + 118, y + 88), (255, 255, 255), 6)
            p.rect((x, y, x + 110, y + 80), glass, 3)
            p.rect((x + 52, y, x + 58, y + 80), (255, 255, 255))
            if hl:
                p.rect((x - 25, y + 88, x + 135, y + 98), (90, 100, 120), 3)
                for k in range(9):
                    p.rect((x - 22 + k * 19, y + 98, x - 18 + k * 19, y + 125), (90, 100, 120))
                p.rect((x - 25, y + 122, x + 135, y + 130), (90, 100, 120), 3)
                for k, c in enumerate(((230, 90, 90), (250, 170, 60), (230, 90, 140))):
                    p.circ(x + 10 + k * 45, y + 85, 10, c)
    p.rect((405, 590, 495, 705), (150, 100, 65), 8)
    p.circ(480, 650, 5, (240, 200, 90))
    p.rect((385, 575, 515, 590), (90, 100, 120), 4)


def wohnzimmer(p):
    room(p, (240, 233, 222), (206, 170, 130))
    window(p, (360, 80, 560, 280))
    frame_pic(p, (610, 150, 800, 280))
    # Fernseher auf Lowboard
    p.rect((40, 450, 330, 560), (170, 120, 80), 10)
    p.rect((60, 470, 180, 540), shade((170, 120, 80), 0.9), 6)
    p.rect((190, 470, 310, 540), shade((170, 120, 80), 0.9), 6)
    p.rect((70, 300, 300, 435), (35, 40, 50), 10)
    p.rect((80, 310, 290, 425), (55, 70, 95), 6)
    p.poly([(90, 420), (160, 315), (200, 315), (130, 420)], (255, 255, 255, 30))
    p.rect((170, 435, 200, 450), (35, 40, 50))
    # Teppich
    p.ell((150, 640, 770, 750), (215, 125, 95))
    p.ell((200, 660, 720, 730), (230, 150, 120))
    # Sofa
    teal = (70, 135, 150)
    p.rect((470, 340, 860, 470), teal, 34)
    p.rect((455, 440, 875, 545), shade(teal, 0.88), 28)
    p.rect((430, 390, 500, 560), shade(teal, 0.8), 28)
    p.rect((830, 390, 900, 560), shade(teal, 0.8), 28)
    p.rect((515, 370, 650, 450), (240, 200, 110), 24)
    p.rect((680, 370, 810, 450), (235, 150, 120), 24)
    for x in (470, 850):
        p.rect((x, 555, x + 16, 585), (90, 70, 55), 3)
    # Couchtisch
    p.rect((300, 600, 620, 626), (185, 135, 92), 10)
    for x in (325, 580):
        p.rect((x, 624, x + 16, 700), (150, 105, 70), 4)
    p.circ(400, 590, 14, (255, 255, 255))
    p.rect((520, 570, 560, 600), (240, 120, 90), 5)
    plant(p, 380, 560, 0.75)


def kueche(p):
    room(p, (241, 244, 246), (205, 205, 210), plank=False)
    for x in range(0, BW, 70):
        for y in range(560, BH, 70):
            if (x // 70 + y // 70) % 2:
                p.rect((x, y, x + 70, y + 70), (190, 190, 198))
    # Fliesenspiegel
    p.rect((30, 290, 660, 432), (255, 255, 255))
    for x in range(30, 661, 45):
        p.line([(x, 290), (x, 432)], (220, 228, 235), 2)
    for y in range(290, 433, 35):
        p.line([(30, y), (660, y)], (220, 228, 235), 2)
    sage = (140, 178, 160)
    # Oberschraenke
    for k in range(4):
        x = 30 + k * 158
        p.rect((x, 80, x + 150, 270), sage, 8)
        p.rect((x + 70, 220, x + 80, 255), (240, 240, 240), 4)
    # Unterschraenke + Arbeitsplatte
    p.rect((30, 450, 660, 650), sage, 8)
    for k in range(4):
        x = 30 + k * 158
        if k == 2:
            continue
        p.rect((x + 8, 470, x + 150, 640), shade(sage, 0.94), 6)
        p.rect((x + 120, 520, x + 128, 580), (240, 240, 240), 4)
    # Herd / Backofen
    p.rect((346, 460, 488, 645), (50, 55, 65), 8)
    p.rect((360, 500, 474, 610), (30, 35, 45), 6)
    p.rect((365, 470, 470, 482), (200, 200, 205), 4)
    for k in range(4):
        p.circ(370 + k * 32, 490, 6, (200, 200, 205))
    p.rect((20, 428, 670, 455), (120, 90, 70), 6)
    p.rect((350, 420, 485, 430), (30, 30, 35), 3)
    # Topf
    p.rect((370, 365, 470, 422), (220, 80, 70), 10)
    p.rect((360, 358, 480, 370), shade((220, 80, 70), 0.85), 5)
    p.rect((410, 345, 430, 360), (60, 60, 60), 4)
    for k, x in enumerate((395, 420, 445)):
        p.arc((x - 10, 300 - k * 4, x + 10, 345), 100, 260, (200, 210, 220), 4)
    # Spuele
    p.rect((80, 426, 260, 440), (160, 170, 180), 4)
    p.arc((150, 330, 230, 420), 180, 360, (170, 180, 190), 10)
    p.rect((222, 370, 234, 430), (170, 180, 190), 4)
    # Kuehlschrank
    p.rect((690, 110, 870, 660), (222, 228, 234), 14)
    p.rect((690, 300, 870, 310), (195, 200, 208))
    for y0, y1 in ((150, 260), (340, 470)):
        p.rect((705, y0, 717, y1), (160, 170, 180), 5)
    p.rect((700, 120, 860, 140), (255, 255, 255, 110), 8)
    p.rect((760, 160, 800, 200), (250, 200, 80), 6)


def schlafzimmer(p):
    room(p, (232, 229, 242), (200, 165, 128))
    frame_pic(p, (280, 120, 470, 240), inner=(70, 80, 130))
    for x, y in ((320, 150), (360, 175), (420, 145)):
        p.circ(x, y, 4, (255, 240, 200))
    # Nachttisch + Lampe
    p.rect((40, 450, 160, 600), (190, 150, 110), 8)
    p.rect((52, 470, 148, 520), shade((190, 150, 110), 0.9), 5)
    p.rect((95, 400, 105, 450), (90, 90, 100))
    p.poly([(60, 400), (140, 400), (125, 350), (75, 350)], (250, 215, 120))
    p.ell((40, 330, 160, 420), (255, 230, 150, 60))
    # Bett
    navy = (60, 80, 125)
    p.rect((175, 290, 600, 450), navy, 28)
    p.rect((165, 420, 610, 610), (245, 245, 250), 18)
    p.rect((165, 470, 610, 615), (235, 190, 100), 18)
    p.rect((165, 470, 610, 495), shade((235, 190, 100), 0.9), 6)
    p.rect((215, 365, 370, 440), (255, 255, 255), 26)
    p.rect((405, 365, 560, 440), (255, 255, 255), 26)
    for x in (180, 585):
        p.rect((x, 605, x + 14, 640), (90, 70, 55), 3)
    # Schrank
    wood = (196, 155, 112)
    p.rect((640, 110, 875, 620), wood, 10)
    p.rect((655, 125, 755, 600), shade(wood, 0.93), 6)
    p.rect((760, 125, 860, 600), shade(wood, 0.93), 6)
    p.rect((740, 330, 748, 400), (240, 230, 210), 4)
    p.rect((767, 330, 775, 400), (240, 230, 210), 4)
    p.rect((650, 620, 670, 640), (90, 70, 55))
    p.rect((845, 620, 865, 640), (90, 70, 55))
    p.ell((230, 650, 640, 750), (175, 160, 210))


def bad(p):
    room(p, (226, 239, 246), (200, 205, 212), plank=False)
    for x in range(0, BW, 60):
        p.line([(x, 0), (x, 560)], (205, 222, 232), 2)
    for y in range(0, 560, 60):
        p.line([(0, y), (BW, y)], (205, 222, 232), 2)
    for x in range(0, BW, 80):
        p.line([(x, 560), (x, BH)], (185, 190, 198), 2)
    # Dusche
    p.rect((30, 80, 310, 650), (205, 230, 245), 6)
    p.rect((150, 70, 160, 140), (170, 180, 190))
    p.rect((150, 70, 230, 80), (170, 180, 190))
    p.ell((105, 135, 205, 165), (170, 180, 190))
    for k in range(16):
        x = 115 + (k * 37) % 90
        y = 190 + (k * 53) % 300
        p.line([(x, y), (x - 6, y + 30)], (110, 170, 220), 4)
    p.rect((30, 80, 310, 650), (255, 255, 255, 60), 6, outline=(160, 175, 190), w=6)
    p.line([(170, 80), (170, 650)], (160, 175, 190), 4)
    p.rect((20, 640, 320, 660), (230, 235, 240), 5)
    # Handtuch
    p.rect((330, 230, 345, 245), (150, 160, 170))
    p.rect((318, 245, 360, 390), (240, 130, 110), 8)
    # Spiegel + Waschbecken
    p.rect((395, 120, 555, 360), (175, 185, 195), 70)
    p.rect((405, 130, 545, 350), (215, 235, 245), 62)
    p.line([(430, 290), (500, 180)], (255, 255, 255), 8)
    p.line([(455, 310), (515, 215)], (255, 255, 255), 4)
    p.rect((365, 470, 585, 650), (255, 255, 255), 10)
    p.rect((380, 490, 470, 635), (238, 242, 246), 6)
    p.rect((480, 490, 570, 635), (238, 242, 246), 6)
    p.rect((350, 435, 600, 478), (250, 252, 255), 18)
    p.rect((460, 395, 480, 440), (170, 180, 190), 5)
    p.rect((460, 395, 505, 407), (170, 180, 190), 5)
    # Toilette
    p.rect((690, 330, 810, 450), (255, 255, 255), 14)
    p.rect((735, 345, 765, 355), (190, 200, 210), 4)
    p.rect((665, 440, 835, 500), (250, 252, 255), 26)
    p.poly([(700, 495), (800, 495), (785, 640), (715, 640)], (255, 255, 255))
    p.rect((660, 640, 850, 652), (225, 230, 236), 4)


def kinderzimmer(p):
    room(p, (220, 242, 233), (220, 185, 140))
    # Wimpelkette
    cols = [(240, 110, 100), (250, 190, 70), (100, 170, 230), (130, 200, 130), (200, 130, 220)]
    p.arc((-50, -120, 950, 160), 20, 160, (120, 120, 140), 3)
    for k in range(11):
        x = 40 + k * 80
        y = 20 + 120 * math.sin(math.pi * (x + 50) / 1000) * 0.95
        p.poly([(x - 22, y), (x + 22, y), (x, y + 45)], cols[k % 5])
    for x, y in ((120, 220), (760, 200), (450, 230)):
        p.poly([(x, y - 18), (x + 6, y - 5), (x + 19, y - 5), (x + 8, y + 4), (x + 12, y + 18),
                (x, y + 10), (x - 12, y + 18), (x - 8, y + 4), (x - 19, y - 5), (x - 6, y - 5)], (250, 200, 80))
    # Kinderbett
    p.rect((50, 330, 95, 610), (240, 200, 150), 14)
    p.rect((395, 410, 430, 610), (240, 200, 150), 12)
    p.rect((70, 470, 420, 580), (255, 255, 255), 14)
    p.rect((150, 470, 420, 585), (110, 165, 230), 14)
    for x, y in ((210, 510), (290, 540), (360, 500), (250, 560)):
        p.circ(x, y, 7, (255, 225, 110))
    p.rect((90, 430, 200, 485), (255, 255, 255), 20)
    # Regal + Buecher
    p.rect((520, 250, 860, 266), (200, 160, 120), 4)
    x = 535
    for k, (w, h) in enumerate(((30, 80), (24, 70), (36, 88), (28, 64), (40, 76), (22, 84))):
        p.rect((x, 250 - h, x + w, 250), cols[k % 5], 4)
        x += w + 6
    p.circ(800, 220, 28, (240, 120, 100))
    # Schreibtisch + Lampe + Stuhl
    p.rect((520, 430, 860, 452), (240, 200, 150), 6)
    p.rect((535, 452, 553, 620), (220, 180, 130))
    p.rect((760, 452, 850, 620), (230, 190, 140), 6)
    p.rect((770, 470, 840, 530), shade((230, 190, 140), 0.93), 4)
    p.rect((770, 545, 840, 605), shade((230, 190, 140), 0.93), 4)
    p.line([(600, 430), (620, 360), (660, 345)], (90, 100, 120), 6)
    p.poly([(645, 335), (690, 350), (675, 380), (640, 365)], (250, 190, 70))
    p.rect((610, 390, 700, 430), (255, 255, 255), 4)
    p.rect((590, 470, 690, 488), (240, 120, 100), 6)
    p.rect((600, 380, 680, 475), (240, 120, 100), 16)
    p.rect((598, 488, 610, 600), (200, 100, 85))
    p.rect((670, 488, 682, 600), (200, 100, 85))
    # Spielzeug
    p.circ(470, 680, 42, (240, 90, 90))
    p.arc((428, 638, 512, 722), 200, 340, (255, 255, 255), 10)
    br = (180, 120, 75)
    p.circ(300, 690, 38, br)
    p.circ(300, 640, 28, br)
    p.circ(280, 618, 11, br)
    p.circ(320, 618, 11, br)
    p.circ(300, 645, 9, (230, 190, 150))
    for k, c in enumerate(((100, 170, 230), (250, 190, 70), (130, 200, 130))):
        p.rect((700 + k * 22 - (k == 2) * 22, 690 - k * 44 + (k == 2) * 0, 744 + k * 22 - (k == 2) * 22,
                734 - k * 44), c, 5)


def balkon(p):
    p.vgrad((0, 0, BW, 470), (140, 195, 240), (220, 236, 250))
    p.circ(700, 110, 50, (255, 215, 100))
    for x, w, h, c in ((0, 120, 260, (170, 185, 205)), (110, 90, 200, (150, 165, 190)),
                       (190, 140, 300, (165, 180, 200)), (520, 110, 230, (150, 165, 190)),
                       (620, 150, 280, (170, 185, 205)), (760, 140, 210, (155, 170, 195))):
        p.rect((x, 470 - h, x + w, 470), c)
        for wy in range(470 - h + 20, 460, 40):
            for wx in range(x + 15, x + w - 15, 30):
                p.rect((wx, wy, wx + 12, wy + 18), (215, 225, 240))
    # Lichterkette
    p.arc((-100, -60, 1000, 200), 15, 165, (90, 90, 100), 3)
    for k in range(14):
        a = math.radians(15 + k * 150 / 13)
        x = 450 + 550 * math.cos(a)
        y = 70 + 130 * math.sin(a)
        p.circ(x, y + 6, 9, (255, 220, 110))
    # Boden + Gelaender
    p.rect((0, 640, BW, BH), (205, 180, 155))
    for x in range(0, BW, 100):
        p.line([(x, 640), (x - 30, BH)], (190, 165, 140), 2)
    p.rect((0, 460, BW, 476), (80, 90, 105), 4)
    for x in range(10, BW, 38):
        p.rect((x, 476, x + 6, 640), (80, 90, 105))
    p.rect((0, 632, BW, 645), (80, 90, 105))
    # Blumenkasten
    p.rect((330, 430, 570, 462), (200, 110, 80), 6)
    for k in range(7):
        x = 350 + k * 33
        p.circ(x, 420, 15, (90, 170, 110))
        p.circ(x, 410, 9, ((240, 100, 120), (250, 200, 80), (240, 140, 200))[k % 3])
    plant(p, 90, 650, 1.1)
    plant(p, 820, 650, 1.0, pot=(190, 110, 80))
    # Tisch + Stuehle
    p.ell((360, 560, 540, 595), (255, 255, 255))
    p.rect((443, 590, 457, 690), (200, 205, 210))
    p.ell((400, 682, 500, 698), (200, 205, 210))
    p.rect((420, 530, 450, 572), (255, 255, 255, 200), 6)
    p.circ(480, 560, 12, (240, 120, 90))
    for x, d in ((255, 1), (575, -1)):
        p.rect((x, 520, x + 70, 545), (240, 150, 90), 10)
        p.rect((x - 5, 590, x + 75, 610), (240, 150, 90), 8)
        p.rect((x + (0 if d > 0 else 60), 520, x + (10 if d > 0 else 70), 700), (210, 125, 70))
        p.rect((x + (60 if d > 0 else 0), 600, x + (70 if d > 0 else 10), 700), (210, 125, 70))


def gesamt(p):
    p.vgrad((0, 0, BW, BH), (215, 235, 250), (245, 248, 252))
    p.rect((0, 715, BW, BH), (120, 175, 95))
    p.poly([(450, 40), (70, 245), (830, 245)], (90, 100, 130))
    p.poly([(450, 75), (130, 245), (770, 245)], (110, 122, 155))
    p.rect((100, 240, 800, 720), (250, 246, 238), 6, outline=(90, 100, 130), w=10)
    rooms = [
        ((110, 250, 340, 480), (232, 229, 242), "das", "Schlafzimmer", C_DAS),
        ((340, 250, 570, 480), (220, 242, 233), "das", "Kinderzimmer", C_DAS),
        ((570, 250, 790, 480), (226, 239, 246), "das", "Badezimmer", C_DAS),
        ((110, 480, 340, 710), (241, 244, 246), "die", "Küche", C_DIE),
        ((340, 480, 790, 710), (240, 233, 222), "das", "Wohnzimmer", C_DAS),
    ]
    for (x0, y0, x1, y1), wall, art, noun, col in rooms:
        p.rect((x0, y0, x1, y1), wall)
        p.rect((x0, y1 - 40, x1, y1), (215, 185, 145))
    for x in (340, 570):
        p.rect((x - 5, 250, x + 5, 480), (90, 100, 130))
    p.rect((340 - 5, 480, 340 + 5, 710), (90, 100, 130))
    p.rect((100, 475, 800, 487), (90, 100, 130))
    # Mini-Moebel
    p.rect((150, 370, 300, 440), (235, 190, 100), 12)
    p.rect((150, 345, 205, 375), (255, 255, 255), 10)
    p.rect((380, 390, 500, 440), (110, 165, 230), 10)
    p.circ(530, 420, 20, (240, 90, 90))
    p.rect((600, 330, 680, 440), (205, 230, 245), 4, outline=(160, 175, 190), w=4)
    p.rect((700, 400, 770, 440), (255, 255, 255), 8)
    p.rect((130, 560, 200, 670), (222, 228, 234), 8)
    p.rect((210, 610, 320, 670), (140, 178, 160), 6)
    p.rect((520, 600, 760, 670), (70, 135, 150), 18)
    p.rect((560, 610, 640, 640), (240, 200, 110), 10)
    p.rect((380, 590, 480, 670), (35, 40, 50), 6)
    # Balkon rechts
    p.rect((800, 420, 885, 432), (90, 100, 130))
    for x in range(805, 886, 16):
        p.rect((x, 380, x + 5, 420), (90, 100, 130))
    p.rect((800, 375, 885, 382), (90, 100, 130))
    p.circ(850, 360, 16, (90, 170, 110))
    # Beschriftungen (Artikel farbig)
    for (x0, y0, x1, y1), wall, art, noun, col in rooms:
        cx = (x0 + x1) / 2
        w = max(len(noun) * 15 + 30, 120)
        p.rect((cx - w / 2, y0 + 14, cx + w / 2, y0 + 82), (255, 255, 255, 235), 14)
        p.text((cx, y0 + 34), art, 22, col)
        p.text((cx, y0 + 62), noun, 25, col)
    p.rect((806, 286, 884, 344), (255, 255, 255, 240), 12, outline=C_DER, w=3)
    p.text((845, 303), "der", 18, C_DER)
    p.text((845, 327), "Balkon", 18, C_DER)
    # Herz
    p.circ(438, 140, 16, (240, 90, 110))
    p.circ(462, 140, 16, (240, 90, 110))
    p.poly([(424, 148), (476, 148), (450, 178)], (240, 90, 110))


DRAW = dict(haus=haus, wohnzimmer=wohnzimmer, kueche=kueche, schlafzimmer=schlafzimmer, bad=bad,
            kinderzimmer=kinderzimmer, balkon=balkon, gesamt=gesamt)


def render(key, out_w):
    """Illustration in Breite out_w (Seitenverhaeltnis 900:770) rendern."""
    ss = out_w / BW * 2
    p = P(ss)
    DRAW[key](p)
    return p.img.resize((out_w, int(out_w * BH / BW)), Image.LANCZOS)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "illustrationen"
    out.mkdir(exist_ok=True)
    for k in DRAW:
        render(k, BW).save(out / f"{k}.png")
        print("gespeichert:", k)
