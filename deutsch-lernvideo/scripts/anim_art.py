"""Gezeichnete 2D-Figuren (Mia, Jonas) und Hintergründe für render2d.py.

Alles wird mit PIL im Code gezeichnet (Supersampling für glatte Kanten) – keine externen Bilder,
keine Kosten, keine Lizenzfragen. Aussehen und Kleidung folgen characters/characters.json.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 3  # Supersampling
W, H = 1080, 1920
BG_MARGIN = 60  # Rand für Kamerazoom

PALETTE = {
    "mia": {
        "skin": (214, 160, 120), "skin_d": (190, 135, 98), "hair": (62, 38, 30), "hair_l": (96, 62, 48),
        "cloth": (231, 176, 38), "cloth_d": (196, 140, 22), "inner": (250, 250, 250),
        "eye": (74, 44, 28), "lip": (150, 60, 62),
    },
    "jonas": {
        "skin": (240, 200, 168), "skin_d": (214, 168, 138), "hair": (110, 72, 42), "hair_l": (140, 98, 62),
        "cloth": (86, 128, 178), "cloth_d": (62, 98, 146), "inner": (250, 250, 250),
        "eye": (96, 100, 56), "lip": (170, 84, 84),
    },
}
CW, CH = 520, 900  # Zeichenfläche einer Figur (Design-Koordinaten)
TORSO = {"mia": (92, 428), "jonas": (74, 446)}
ARM_W, ARM_H, ARM_PIVOT = 100, 450, (50, 50)


def _canvas(w, h, scale):
    k = scale * SS
    return Image.new("RGBA", (int(round(w * k)), int(round(h * k))), (0, 0, 0, 0)), k


def _down(im, scale):
    size = (max(1, int(round(im.width / SS))), max(1, int(round(im.height / SS))))
    return im.resize(size, Image.LANCZOS)


def _e(d, k, box, **kw):
    d.ellipse([v * k for v in box], **kw)


def _r(d, k, box, r=0, **kw):
    d.rounded_rectangle([v * k for v in box], radius=r * k, **kw)


def _p(d, k, pts, **kw):
    d.polygon([(x * k, y * k) for x, y in pts], **kw)


def _l(d, k, pts, w=4, **kw):
    d.line([(x * k, y * k) for x, y in pts], width=int(w * k), **kw)


# ------------------------------------------------------------------ Figur
def head_sprite(kind, mouth, blink, scale):
    c = PALETTE[kind]
    im, k = _canvas(CW, 600, scale)
    d = ImageDraw.Draw(im)
    if kind == "mia":
        _e(d, k, (108, 82, 412, 372), fill=c["hair"])
    else:
        for ex in (146, 374):
            _e(d, k, (ex - 26, 226, ex + 26, 288), fill=c["skin_d"])
    # Gesicht
    face = (146, 120, 374, 362) if kind == "mia" else (140, 118, 380, 366)
    _e(d, k, face, fill=c["skin"])
    # Wangen
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    _e(od, k, (172, 272, 218, 312), fill=(240, 120, 120, 90))
    _e(od, k, (302, 272, 348, 312), fill=(240, 120, 120, 90))
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    # Nase
    d.arc([v * k for v in (246, 252, 276, 286)], 15, 165, fill=c["skin_d"], width=int(4 * k))
    # Augenbrauen
    for ex, sgn in ((206, 1), (314, -1)):
        _l(d, k, [(ex - 26, 207), (ex, 199), (ex + 26, 207)], w=7, fill=c["hair"], joint="curve")
    # Augen
    for ex in (206, 314):
        if blink:
            d.arc([v * k for v in (ex - 20, 226, ex + 20, 254)], 10, 170, fill=c["eye"], width=int(5 * k))
        else:
            _e(d, k, (ex - 17, 218, ex + 17, 262), fill=(255, 255, 255))
            _e(d, k, (ex - 13, 222, ex + 13, 260), fill=c["eye"])
            _e(d, k, (ex - 6, 228, ex + 2, 237), fill=(255, 255, 255))
    # Mund
    mx, my = 260, 314
    if mouth == 0:
        d.arc([v * k for v in (mx - 30, my - 22, mx + 30, my + 18)], 25, 155, fill=c["lip"], width=int(6 * k))
    elif mouth == 1:
        _e(d, k, (mx - 18, my - 6, mx + 18, my + 10), fill=(112, 36, 46))
    elif mouth == 2:
        _e(d, k, (mx - 24, my - 10, mx + 24, my + 22), fill=(112, 36, 46))
        _e(d, k, (mx - 14, my + 8, mx + 14, my + 22), fill=(226, 110, 120))
    else:
        _e(d, k, (mx - 30, my - 14, mx + 30, my + 30), fill=(112, 36, 46))
        _r(d, k, (mx - 22, my - 12, mx + 22, my - 1), r=3, fill=(255, 255, 255))
        _e(d, k, (mx - 16, my + 12, mx + 16, my + 30), fill=(226, 110, 120))
    # Haare vorn
    if kind == "mia":
        _e(d, k, (104, 170, 184, 480), fill=c["hair"])
        _e(d, k, (336, 170, 416, 480), fill=c["hair"])
        for y in (430, 470):
            _e(d, k, (112, y - 20, 176, y + 40), fill=c["hair"])
            _e(d, k, (344, y - 20, 408, y + 40), fill=c["hair"])
        _e(d, k, (134, 88, 388, 208), fill=c["hair"])
        _p(d, k, [(134, 160), (200, 215), (170, 290), (134, 280)], fill=c["hair"])
        _p(d, k, [(388, 160), (330, 195), (350, 290), (388, 280)], fill=c["hair"])
        d.arc([v * k for v in (150, 96, 330, 200)], 200, 300, fill=c["hair_l"], width=int(7 * k))
        for ex in (150, 370):  # Ohrringe
            d.arc([v * k for v in (ex - 15, 292, ex + 15, 322)], 0, 360, fill=(200, 205, 214), width=int(4 * k))
    else:
        for (a, b, cc, dd) in ((140, 96, 220, 160), (196, 64, 290, 130), (262, 62, 352, 132), (318, 84, 388, 160)):
            _e(d, k, (a, b, cc, dd), fill=c["hair"])
        _e(d, k, (136, 90, 384, 200), fill=c["hair"])
        _p(d, k, [(136, 150), (250, 150), (210, 205), (136, 215)], fill=c["hair"])
        _r(d, k, (138, 170, 160, 238), r=8, fill=c["hair"])
        _r(d, k, (360, 170, 382, 238), r=8, fill=c["hair"])
        d.arc([v * k for v in (170, 80, 350, 170)], 210, 320, fill=c["hair_l"], width=int(7 * k))
    return _down(im, scale)


def body_sprite(kind, scale):
    c = PALETTE[kind]
    im, k = _canvas(CW, CH, scale)
    d = ImageDraw.Draw(im)
    x0, x1 = TORSO[kind]
    if kind == "mia":
        _e(d, k, (100, 170, 420, 540), fill=c["hair"])
        for x in (140, 200, 260, 320, 380):
            _e(d, k, (x - 42, 470, x + 42, 560), fill=c["hair"])
    _r(d, k, (222, 330, 298, 430), r=30, fill=c["skin_d"])
    _r(d, k, (x0, 396, x1, 980), r=130, fill=c["cloth"])
    if kind == "mia":  # Strickjacke offen, weißes Shirt
        _p(d, k, [(214, 400), (306, 400), (292, 980), (228, 980)], fill=c["inner"])
        _p(d, k, [(226, 398), (294, 398), (260, 470)], fill=c["skin_d"])
        _l(d, k, [(214, 400), (228, 980)], w=7, fill=c["cloth_d"])
        _l(d, k, [(306, 400), (292, 980)], w=7, fill=c["cloth_d"])
        _l(d, k, [(x0 + 60, 470), (x0 + 60, 900)], w=3, fill=c["cloth_d"])
        _l(d, k, [(x1 - 60, 470), (x1 - 60, 900)], w=3, fill=c["cloth_d"])
    else:  # Jeanshemd über weißem Shirt
        _p(d, k, [(222, 398), (298, 398), (260, 490)], fill=c["inner"])
        _p(d, k, [(188, 394), (252, 404), (232, 482)], fill=c["cloth_d"])
        _p(d, k, [(332, 394), (268, 404), (288, 482)], fill=c["cloth_d"])
        _l(d, k, [(260, 490), (260, 980)], w=5, fill=c["cloth_d"])
        for y in (560, 650, 740, 830):
            _e(d, k, (254, y - 6, 266, y + 6), fill=(230, 236, 246))
        _r(d, k, (330, 580, 404, 672), r=8, outline=c["cloth_d"], width=int(5 * k))
    return _down(im, scale)


def arm_sprite(kind, scale):
    c = PALETTE[kind]
    side = 2 * (ARM_H - ARM_PIVOT[1] + 40)
    im, k = _canvas(side, side, scale)
    d = ImageDraw.Draw(im)
    ox, oy = side / 2 - ARM_PIVOT[0], side / 2 - ARM_PIVOT[1]

    def R(b, r, **kw):
        _r(d, k, (b[0] + ox, b[1] + oy, b[2] + ox, b[3] + oy), r=r, **kw)

    if kind == "mia":
        R((8, 14, 92, 372), 40, fill=c["cloth"])
        R((6, 346, 94, 376), 12, fill=c["cloth_d"])
    else:
        R((8, 14, 92, 250), 40, fill=c["cloth"])
        R((4, 224, 96, 256), 12, fill=c["cloth_d"])
        R((16, 244, 84, 380), 30, fill=c["skin"])
    _e(d, k, (14 + ox, 358 + oy, 86 + ox, 430 + oy), fill=c["skin"])
    return _down(im, scale)


class Character:
    def __init__(self, kind, scale):
        self.kind, self.scale = kind, scale
        self.body = body_sprite(kind, scale)
        self.arm = arm_sprite(kind, scale)
        self.heads = {(m, b): head_sprite(kind, m, b, scale) for m in range(4) for b in (0, 1)}
        x0, x1 = TORSO[kind]
        self.pivots = {"L": (x0 + 38, 446), "R": (x1 - 38, 446)}
        self._arm_cache = {}

    def arm_rot(self, angle):
        a = int(round(angle / 2.0)) * 2
        im = self._arm_cache.get(a)
        if im is None:
            im = self.arm.rotate(a, resample=Image.BICUBIC)
            self._arm_cache[a] = im
        return im

    def size(self):
        return self.body.size


def paste_character(canvas, ch: Character, cx, bottom, t, mouth, blink, arm_r, arm_l, bob, lean, flash=0.0):
    """Zeichnet die Figur mit Fuß-/Unterkante bei y=bottom, horizontal um cx zentriert."""
    s = ch.scale
    w, h = ch.body.size
    ox, oy = int(cx - w / 2), int(bottom - h + bob * s)
    canvas.paste(ch.body, (ox, oy), ch.body)
    for side, ang in (("L", -arm_l), ("R", arm_r)):
        px, py = ch.pivots[side]
        im = ch.arm_rot(ang)
        canvas.paste(im, (int(ox + px * s - im.width / 2), int(oy + py * s - im.height / 2)), im)
    hd = ch.heads[(mouth, blink)]
    canvas.paste(hd, (int(ox + lean * s), int(oy + bob * 0.4 * s)), hd)


# ------------------------------------------------------------------ Hintergründe
def _grad(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, dtype=np.float32)[None, None, :]
    b = np.array(bottom, dtype=np.float32)[None, None, :]
    arr = (a * (1 - t) + b * t) * np.ones((1, w, 1), dtype=np.float32)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


class _Pen:
    def __init__(self, k=2):
        self.k = k
        self.w = int((W + 2 * BG_MARGIN) * k)
        self.h = int((H + 2 * BG_MARGIN) * k)
        self.im = None
        self.d = None

    def start(self, top, bottom):
        self.im = _grad(self.w, self.h, top, bottom)
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def X(self, v):
        return (v + BG_MARGIN) * self.k

    def rect(self, x0, y0, x1, y1, fill, r=0):
        b = [self.X(x0), self.X(y0), self.X(x1), self.X(y1)]
        if r:
            self.d.rounded_rectangle(b, radius=r * self.k, fill=fill)
        else:
            self.d.rectangle(b, fill=fill)

    def ell(self, x0, y0, x1, y1, fill):
        self.d.ellipse([self.X(x0), self.X(y0), self.X(x1), self.X(y1)], fill=fill)

    def poly(self, pts, fill):
        self.d.polygon([(self.X(x), self.X(y)) for x, y in pts], fill=fill)

    def line(self, pts, w, fill):
        self.d.line([(self.X(x), self.X(y)) for x, y in pts], width=int(w * self.k), fill=fill, joint="curve")

    def glow(self, cx, cy, r, color, alpha=90):
        pad = int(r * 1.6 * self.k)
        x0, y0 = int(self.X(cx)) - pad, int(self.X(cy)) - pad
        size = 2 * pad
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([pad - r * self.k, pad - r * self.k, pad + r * self.k, pad + r * self.k], fill=alpha)
        mask = mask.filter(ImageFilter.GaussianBlur(r * self.k * 0.35))
        sx0, sy0 = max(0, -x0), max(0, -y0)
        ex, ey = min(size, self.im.width - x0), min(size, self.im.height - y0)
        if ex <= sx0 or ey <= sy0:
            return
        mask = mask.crop((sx0, sy0, ex, ey))
        self.im.paste(color, (x0 + sx0, y0 + sy0, x0 + ex, y0 + ey), mask)
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def blur_region_people(self, seed, count, ybase, colors):
        rng = np.random.default_rng(seed)
        ov = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for _ in range(count):
            x = rng.uniform(0, W)
            s = rng.uniform(60, 110)
            col = colors[rng.integers(len(colors))]
            od.ellipse([self.X(x - s * .5), self.X(ybase - s * 3.4), self.X(x + s * .5), self.X(ybase - s * 2.4)], fill=col + (200,))
            od.rounded_rectangle([self.X(x - s * .75), self.X(ybase - s * 2.4), self.X(x + s * .75), self.X(ybase + 200)], radius=s * self.k * .5, fill=col + (200,))
        ov = ov.filter(ImageFilter.GaussianBlur(14 * self.k))
        self.im.paste(ov, (0, 0), ov)
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def finish(self):
        im = self.im.resize((W + 2 * BG_MARGIN, H + 2 * BG_MARGIN), Image.LANCZOS)
        return im


def bg_park(variant="morning", bench=True):
    p = _Pen()
    if variant == "morning":
        p.start((255, 214, 170), (255, 243, 214))
        p.glow(800, 420, 420, (255, 214, 120), 140)
        p.ell(720, 340, 880, 500, (255, 240, 190))
    else:
        p.start((120, 190, 245), (214, 238, 252))
        p.glow(850, 300, 300, (255, 255, 255), 120)
    p.ell(-300, 760, 900, 1500, (150, 205, 140) if variant == "morning" else (120, 190, 120))
    p.ell(300, 800, 1500, 1600, (120, 185, 120) if variant == "morning" else (96, 168, 100))
    p.rect(-100, 1080, 1180, 2100, (104, 172, 96) if variant == "morning" else (84, 154, 88))
    p.poly([(380, 1100), (700, 1100), (1100, 1900), (-100, 1900)], (232, 214, 176))
    # Baum links
    p.rect(120, 620, 190, 1300, (110, 78, 56), r=20)
    for cx, cy, r in ((150, 560, 230), (30, 640, 170), (300, 640, 190), (160, 430, 170), (-20, 480, 140), (280, 470, 150)):
        p.ell(cx - r, cy - r, cx + r, cy + r, (246, 180, 200))
    for cx, cy, r in ((120, 520, 90), (260, 600, 80), (40, 700, 70)):
        p.ell(cx - r, cy - r, cx + r, cy + r, (255, 205, 220))
    if bench:
        p.rect(300, 1190, 1000, 1240, (150, 100, 66), r=10)
        p.rect(300, 1250, 1000, 1300, (150, 100, 66), r=10)
        p.rect(330, 1300, 370, 1460, (90, 62, 44))
        p.rect(930, 1300, 970, 1460, (90, 62, 44))
    return p.finish()


def bg_entrance():
    p = _Pen()
    p.start((150, 205, 245), (225, 240, 252))
    p.rect(-100, 420, 1180, 1500, (96, 120, 156))
    for r in range(5):
        for c in range(4):
            x, y = 40 + c * 260, 480 + r * 190
            p.rect(x, y, x + 220, y + 150, (150, 200, 235), r=8)
            p.poly([(x + 20, y + 140), (x + 100, y + 10), (x + 140, y + 10), (x + 60, y + 140)], (255, 255, 255, 60))
    p.rect(340, 1090, 740, 1500, (60, 82, 118), r=16)
    p.rect(360, 1110, 710, 1480, (170, 215, 240), r=10)
    p.line([(535, 1110), (535, 1480)], 6, (60, 82, 118))
    p.rect(-100, 1480, 1180, 2100, (190, 192, 200))
    for cx in (110, 960):
        p.rect(cx - 50, 1330, cx + 50, 1480, (190, 110, 80), r=10)
        p.ell(cx - 90, 1130, cx + 90, 1350, (96, 168, 100))
    return p.finish()


def bg_kitchen():
    p = _Pen()
    p.start((250, 240, 226), (240, 226, 206))
    p.rect(60, 330, 500, 960, (150, 205, 240), r=20)
    p.rect(80, 350, 480, 940, (196, 232, 252), r=14)
    p.line([(280, 350), (280, 940)], 8, (250, 240, 226))
    p.line([(80, 640), (480, 640)], 8, (250, 240, 226))
    p.rect(560, 480, 1000, 520, (190, 150, 110), r=8)
    p.rect(560, 760, 1000, 800, (190, 150, 110), r=8)
    for i, col in enumerate(((237, 140, 20), (27, 54, 104), (0, 150, 136), (233, 30, 99))):
        x = 590 + i * 100
        p.rect(x, 430, x + 60, 480, col, r=10)
        p.rect(x, 710, x + 60, 760, col, r=10)
    p.rect(-100, 1080, 1180, 2100, (212, 188, 156))
    p.rect(-100, 1010, 1180, 1100, (120, 92, 72))
    p.rect(640, 840, 920, 1010, (70, 76, 92), r=18)  # Kaffeemaschine
    p.rect(680, 870, 880, 920, (200, 210, 224), r=8)
    p.ell(690, 1010, 730, 1010, (255, 255, 255))
    p.ell(60, 1060, 220, 1240, (96, 168, 100))
    return p.finish()


def bg_corridor():
    p = _Pen()
    p.start((236, 240, 248), (214, 222, 236))
    p.rect(-100, 1300, 1180, 2100, (176, 160, 140))
    p.poly([(200, 1300), (880, 1300), (1180, 2100), (-100, 2100)], (196, 180, 158))
    for i in range(4):
        x = -20 + i * 290
        p.rect(x + 40, 400, x + 230, 1180, (150, 205, 240), r=12)
        p.rect(x + 56, 416, x + 214, 1164, (206, 236, 252), r=8)
    for x, col in ((70, (237, 140, 20)), (460, (0, 150, 136)), (820, (124, 77, 255))):
        p.rect(x, 1230, x + 190, 1290, col, r=12)
    p.blur_region_people(3, 3, 1300, [(120, 150, 200), (230, 150, 90), (140, 190, 150)])
    return p.finish()


def bg_terrace():
    p = _Pen()
    p.start((255, 190, 140), (255, 236, 200))
    p.glow(300, 700, 380, (255, 220, 150), 130)
    p.ell(210, 600, 390, 780, (255, 245, 205))
    sky = (130, 108, 140)
    p.rect(-100, 1000, 1180, 1500, sky)
    p.rect(150, 760, 230, 1000, (96, 82, 112))  # Dom
    p.rect(250, 760, 330, 1000, (96, 82, 112))
    p.poly([(150, 760), (190, 560), (230, 760)], (96, 82, 112))
    p.poly([(250, 760), (290, 560), (330, 760)], (96, 82, 112))
    p.rect(160, 840, 320, 1000, (96, 82, 112))
    for x in range(380, 1100, 90):
        p.rect(x, 880 + (x * 7) % 90, x + 70, 1000, (110, 96, 124))
    p.rect(-100, 1230, 1180, 1300, (230, 232, 238))
    for x in range(-60, 1200, 90):
        p.rect(x, 1230, x + 14, 1500, (210, 214, 224))
    p.rect(-100, 1500, 1180, 2100, (200, 190, 180))
    for cx in (120, 940):
        p.ell(cx - 110, 1040, cx + 110, 1260, (96, 168, 100))
    return p.finish()


def bg_party(variant="party"):
    p = _Pen()
    p.start((118, 70, 120), (176, 98, 98))
    p.rect(-100, 1250, 1180, 2100, (96, 64, 60))
    if variant == "sofa":
        p.rect(60, 940, 1020, 1400, (74, 110, 150), r=90)
        p.rect(30, 1060, 180, 1400, (62, 96, 136), r=60)
        p.rect(900, 1060, 1050, 1400, (62, 96, 136), r=60)
        p.rect(480, 560, 540, 1000, (60, 50, 50))
        p.poly([(420, 560), (600, 560), (560, 440), (460, 440)], (255, 220, 150))
        p.glow(510, 500, 330, (255, 220, 150), 110)
    else:
        p.rect(80, 780, 420, 1250, (200, 150, 110), r=10)  # Regal
        for i, col in enumerate(((237, 140, 20), (27, 54, 104), (0, 150, 136), (233, 30, 99), (124, 77, 255))):
            p.rect(110 + i * 62, 810, 160 + i * 62, 930, col, r=6)
        p.rect(660, 1030, 1040, 1330, (230, 210, 190), r=16)  # Tisch
        p.ell(740, 960, 960, 1050, (84, 52, 38))  # Torte
        p.rect(740, 995, 960, 1050, (110, 70, 48), r=14)
        p.ell(840, 940, 860, 962, (240, 60, 70))
    p.line([(-60, 160), (270, 250), (540, 200), (810, 260), (1140, 170)], 5, (60, 40, 50))
    cols = [(255, 214, 90), (255, 120, 120), (140, 220, 255), (190, 160, 255), (150, 235, 160)]
    for i in range(14):
        t = i / 13
        x = -60 + t * 1200
        y = 160 + math.sin(t * math.pi * 4) * 40 + 70 * (1 - abs(2 * t - 1)) * 0 + 55 * math.sin(t * 3.1)
        p.glow(x, y + 24, 60, cols[i % 5], 120)
        p.ell(x - 14, y + 8, x + 14, y + 44, cols[i % 5] + (255,))
    for x, y, col in ((70, 520, (255, 90, 110)), (190, 450, (255, 214, 90)), (950, 560, (110, 200, 255)), (1020, 440, (150, 230, 140))):
        p.ell(x - 56, y - 70, x + 56, y + 70, col + (255,))
        p.line([(x, y + 70), (x, y + 340)], 3, (240, 240, 240))
    return p.finish()


def bg_balcony(variant="night"):
    p = _Pen()
    if variant == "blue":
        p.start((40, 56, 120), (232, 150, 120))
    else:
        p.start((14, 20, 56), (60, 56, 110))
    rng = np.random.default_rng(5)
    for _ in range(60):
        x, y = rng.uniform(0, W), rng.uniform(0, 700)
        p.ell(x - 2, y - 2, x + 2, y + 2, (255, 255, 240, 200))
    p.ell(760, 250, 860, 350, (255, 246, 210))
    p.glow(810, 300, 220, (255, 246, 210), 70)
    for i in range(12):
        x = -20 + i * 100
        h = 220 + (i * 137) % 340
        p.rect(x, 1120 - h, x + 96, 1500, (30, 34, 70))
        for wy in range(int(1120 - h + 20), 1480, 46):
            for wx in range(x + 12, x + 88, 28):
                if (wx * 3 + wy * 7) % 5 < 3:
                    p.rect(wx, wy, wx + 14, wy + 22, (255, 214, 120))
    p.rect(-100, 1260, 1180, 1300, (30, 28, 50))
    for x in range(-60, 1200, 80):
        p.rect(x, 1260, x + 10, 1560, (44, 42, 70))
    p.rect(-100, 1500, 1180, 2100, (46, 40, 60))
    p.line([(-60, 200), (270, 290), (540, 240), (810, 300), (1140, 210)], 4, (30, 30, 40))
    for i in range(12):
        t = i / 11
        x = -60 + t * 1200
        y = 210 + math.sin(t * 3.1) * 60 + 20
        p.glow(x, y + 20, 55, (255, 214, 120), 140)
        p.ell(x - 10, y + 6, x + 10, y + 34, (255, 230, 150))
    return p.finish()


def bg_foyer():
    p = _Pen()
    p.start((200, 224, 248), (236, 244, 252))
    p.rect(-100, 280, 1180, 1250, (176, 214, 244, 255))
    for x in range(-60, 1200, 270):
        p.rect(x, 280, x + 12, 1250, (96, 120, 156))
    p.rect(-100, 1250, 1180, 2100, (196, 198, 208))
    p.poly([(-100, 1250), (1180, 1250), (1180, 1290), (-100, 1290)], (150, 154, 170))
    p.blur_region_people(9, 9, 1280, [(60, 90, 140), (230, 140, 60), (120, 180, 160), (180, 120, 200)])
    for x, col in ((30, (27, 54, 104)), (780, (237, 140, 20))):
        p.rect(x, 520, x + 240, 1230, col, r=14)
        p.ell(x + 60, 600, x + 180, 720, (255, 255, 255, 230))
        p.rect(x + 40, 790, x + 200, 810, (255, 255, 255, 230))
        p.rect(x + 40, 840, x + 160, 860, (255, 255, 255, 180))
    p.rect(420, 1130, 660, 1160, (250, 250, 252), r=10)
    p.rect(530, 1160, 550, 1400, (150, 154, 170))
    return p.finish()


def bg_learn(variant=0):
    p = _Pen()
    tops = [((204, 228, 252), (236, 224, 252)), ((255, 236, 208), (252, 224, 236)), ((210, 244, 236), (222, 232, 252))]
    p.start(*tops[variant % 3])
    rng = np.random.default_rng(variant + 11)
    cols = [(255, 255, 255, 120), (237, 140, 20, 50), (27, 54, 104, 28), (0, 150, 136, 40), (124, 77, 255, 36)]
    for _ in range(28):
        x, y, r = rng.uniform(-100, 1180), rng.uniform(0, 1900), rng.uniform(40, 190)
        p.ell(x - r, y - r, x + r, y + r, cols[rng.integers(len(cols))])
    for gy in range(120, 1900, 120):
        for gx in range(60, 1100, 120):
            p.ell(gx - 3, gy - 3, gx + 3, gy + 3, (27, 54, 104, 28))
    p.rect(-100, 1480, 1180, 2100, (255, 255, 255, 90))
    return p.finish()


BACKGROUNDS = {
    "park_morning": lambda: bg_park("morning", True),
    "park_day": lambda: bg_park("day", False),
    "entrance": bg_entrance, "kitchen": bg_kitchen, "corridor": bg_corridor, "terrace": bg_terrace,
    "party": lambda: bg_party("party"), "sofa": lambda: bg_party("sofa"),
    "balcony": lambda: bg_balcony("blue"), "balcony_night": lambda: bg_balcony("night"),
    "foyer": bg_foyer, "learn0": lambda: bg_learn(0), "learn1": lambda: bg_learn(1), "learn2": lambda: bg_learn(2),
}
