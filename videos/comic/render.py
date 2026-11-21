"""
Comic-Video-Engine der ELM Akademie: Strichmaennchen-Dialog im Klassenzimmer,
Wort-fuer-Wort-Untertitel (gross, handytauglich), Stimmen, Musik, Logo.

    python3 render.py schlauer_schueler             -> ausgabe/schlauer_schueler.mp4
    python3 render.py schlauer_schueler --preview   -> vorschau/*.png

Der Dialog steht in folgen/<name>.py (siehe folgen/schlauer_schueler.py).
Die Mundbewegung folgt der Lautstaerke der Stimme.
"""
import importlib
import math
import os
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "folgen"))
NAME = next((a for a in sys.argv[1:] if not a.startswith("-")), "schlauer_schueler")
C = importlib.import_module(NAME)

W, H, FPS = 1080, 1920, 30
SS = 2                                    # Supersampling fuer glatte Figuren
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
BLACK, WHITE = (20, 20, 26), (255, 255, 255)
RED, RED_D = (222, 46, 46), (176, 30, 34)
NAVY, ORANGE = (27, 54, 104), (237, 140, 20)
YELLOW = (255, 214, 64)

SPRECHER = {
    "L": dict(name="LEHRER", farbe=(40, 70, 130), text=WHITE, pitch=0.93, length=0.93),
    "A": dict(name="ALI", farbe=RED, text=YELLOW, pitch=1.13, length=1.10),
}
FLOOR_Y = 1260


# ================================================================ Helfer
@lru_cache(None)
def font(weight, size):
    p = FONT_DIR / f"Inter-{weight}.otf"
    return ImageFont.truetype(str(p if p.exists() else FONT_DIR / "Inter-Bold.otf"), size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def back_out(t):
    t = clamp(t)
    return 1 + 2.7 * (t - 1) ** 3 + 1.7 * (t - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def with_alpha(img, a):
    if a >= 0.999:
        return img
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return out


def comp(frame, img, pos=(0, 0), alpha=1.0):
    if alpha <= 0.01:
        return
    img = with_alpha(img, alpha)
    x, y = int(pos[0]), int(pos[1])
    l, t = max(0, -x), max(0, -y)
    r, b = min(img.width, frame.width - x), min(img.height, frame.height - y)
    if r > l and b > t:
        frame.alpha_composite(img.crop((l, t, r, b)), (x + l, y + t))


def comp_center(frame, img, cx, cy, s=1.0, alpha=1.0, rot=0.0):
    if abs(s - 1) > 0.003:
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)
    if rot:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
    comp(frame, img, (cx - img.width / 2, cy - img.height / 2), alpha)


class Cv:
    """Zeichenflaeche in Szenen-Koordinaten, intern 2x aufgeloest."""

    def __init__(self, box):
        self.x0, self.y0 = box[0], box[1]
        self.w, self.h = box[2] - box[0], box[3] - box[1]
        self.im = Image.new("RGBA", (self.w * SS, self.h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def p(self, x, y):
        return ((x - self.x0) * SS, (y - self.y0) * SS)

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=0):
        a, b = self.p(cx - rx, cy - ry), self.p(cx + rx, cy + ry)
        self.d.ellipse((*a, *b), fill=fill, outline=outline, width=max(1, int(width * SS)) if outline else 0)

    def line(self, pts, width, fill):
        q = [self.p(*pt) for pt in pts]
        self.d.line(q, fill=fill, width=int(width * SS), joint="curve")
        r = width * SS / 2
        for x, y in q:
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def poly(self, pts, fill=None, outline=None, width=0):
        if fill:
            self.d.polygon([self.p(*pt) for pt in pts], fill=fill)
        if outline:
            self.line(list(pts) + [pts[0]], width, outline)

    def out(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)

    def put(self, frame):
        comp(frame, self.out(), (self.x0, self.y0))


# ================================================================ Gesichter
EMO = {
    "neutral":    dict(lid=0.0, brow=0.0, mouth="flat"),
    "annoyed":    dict(lid=0.35, brow=-1.0, mouth="flat"),
    "puzzled":    dict(lid=0.0, brow=0.8, mouth="flat"),
    "innocent":   dict(lid=0.0, brow=0.9, mouth="smile"),
    "smug":       dict(lid=0.45, brow=-0.3, mouth="smile"),
    "suspicious": dict(lid=0.5, brow=-0.7, mouth="flat"),
    "shocked":    dict(lid=0.0, brow=1.0, mouth="o"),
    "grin":       dict(lid=0.1, brow=0.2, mouth="grin"),
    "tired":      dict(lid=0.6, brow=0.2, mouth="flat"),
    "laugh":      dict(lid=0.0, brow=0.5, mouth="laugh", happy=True),
}


def face(cv, cx, cy, r, emo, talk, look, blink):
    k = r / 90
    e = EMO[emo]
    lid = max(e["lid"], 0.9 if blink else 0.0)
    ex, ey, rx, ry = 34 * k, -10 * k, 17 * k, 21 * k
    for sx in (-1, 1):
        x, y = cx + sx * ex, cy + ey
        if e.get("happy"):
            pts = [(x + rx * (2 * u - 1), y + 4 * k - 12 * k * math.sin(math.pi * u)) for u in np.linspace(0, 1, 10)]
            cv.line(pts, 6 * k, BLACK)
        else:
            cv.ellipse(x, y, rx, ry, fill=WHITE)
            cv.ellipse(x + look[0] * 7 * k, y + look[1] * 8 * k, 7.5 * k, 7.5 * k, fill=BLACK)
            if lid > 0:
                ylid = y - ry + 2 * ry * lid
                xs = np.linspace(-rx, rx, 18)
                top = [(x + xx, y - ry * math.sqrt(max(0, 1 - (xx / rx) ** 2))) for xx in xs]
                bot = [(x + xx, min(ylid, y + ry * math.sqrt(max(0, 1 - (xx / rx) ** 2)))) for xx in xs[::-1]]
                cv.poly(top + bot, fill=WHITE)
                cv.line([(x - rx, ylid), (x + rx, ylid)], 5 * k, BLACK)
            cv.ellipse(x, y, rx, ry, outline=BLACK, width=4.5 * k)
        # Augenbrauen
        b = e["brow"]
        yc = y - ry - 15 * k - (b * 12 * k if b > 0 else b * 5 * k)
        inner = (-b * 6 * k) if b > 0 else (-b * 10 * k)
        cv.line([(cx + sx * (ex - 18 * k), yc + inner / 2), (cx + sx * (ex + 20 * k), yc - inner / 2)], 7 * k, BLACK)
    my = cy + r * 0.52
    shape = e["mouth"]
    if talk > 0.06:
        cv.ellipse(cx, my, 15 * k + 7 * k * talk, 3 * k + 21 * k * talk, fill=BLACK)
    elif shape == "flat":
        cv.line([(cx - 17 * k, my), (cx + 17 * k, my + 1 * k)], 6 * k, BLACK)
    elif shape == "smile":
        cv.line([(cx + 24 * k * (2 * u - 1), my - 4 * k + 11 * k * math.sin(math.pi * u)) for u in np.linspace(0, 1, 10)],
                6 * k, BLACK)
    elif shape == "o":
        cv.ellipse(cx, my + 4 * k, 13 * k, 17 * k, fill=BLACK)
    elif shape in ("grin", "laugh"):
        wd, ht = (26, 14) if shape == "grin" else (32, 18 + 14 * talk)
        if shape == "laugh":
            ht = 22 + 12 * (0.5 + 0.5 * math.sin(talk * 6.28))
        pts = [(cx + wd * k * math.cos(a), my - 6 * k + ht * k * math.sin(a)) for a in np.linspace(0, math.pi, 14)]
        cv.poly(pts, fill=BLACK, outline=BLACK, width=3 * k)
        cv.ellipse(cx, my + ht * k * 0.55, wd * 0.5 * k, ht * 0.28 * k, fill=(214, 84, 96))


# ================================================================ Posen
# (Ellenbogen x, y, Hand x, y, Handbewegung) relativ zur Schulter, fuer den Arm rechts (+x); links wird gespiegelt
TPOSE = {
    "hips":     (80, 140, 32, 268, 0.0),
    "point":    (84, 50, 175, -35, 1.0),
    "palm":     (92, 115, 165, 70, 1.0),
    "shrug":    (84, 95, 135, 62, 0.6),
    "facepalm": (60, 30, -40, -138, 0.0),
}
APOSE = {
    "rest":    (62, 100, -22, 182, 0.0),
    "explain": (96, 84, 128, -12, 1.0),
    "shrug":   (112, 92, 150, 44, 0.7),
    "scratch": (74, 10, 36, -112, 0.5),
    "chin":    (20, 70, -28, -92, 0.0),
}


def pose_vec(table, a, b, u):
    u = ease_out(u)
    return tuple(lerp(a_, b_, u) for a_, b_ in zip(table[a], table[b]))


def draw_arm(cv, shoulder, side, vec, wig, t, sleeve, hand_r, phase):
    ex, ey, hx, hy, wf = vec
    wx = math.sin(t * 9 + phase) * 11 * wig * wf
    wy = math.sin(t * 7 + phase) * 7 * wig * wf
    sx, sy = shoulder
    pts = [(sx, sy), (sx + side * (ex + wx * 0.4), sy + ey + wy * 0.4), (sx + side * (hx + wx), sy + hy + wy)]
    if sleeve:
        cv.line(pts, 50, BLACK)
        cv.line(pts, 38, sleeve)
    else:
        cv.line(pts, 21, BLACK)
        cv.line(pts, 9, WHITE)
    cv.ellipse(pts[2][0], pts[2][1], hand_r, hand_r, fill=WHITE, outline=BLACK, width=6)


def blinking(t, seed):
    return ((t + seed * 1.37) % 3.6) < 0.12


# ================================================================ Figuren
T_X, A_X = 815, 290


def draw_teacher(frame, t, emo, arms_a, arms_b, u, talk, bob):
    cx = T_X
    cv = Cv((560, 590, 1080, 1660))
    cv.ellipse(cx, 1580, 115, 22, fill=(0, 0, 0, 38))
    for sx in (-1, 1):
        pts = [(cx + sx * 19, 1170), (cx + sx * 25, 1556)]
        cv.line(pts, 38, BLACK)
        cv.line(pts, 29, (74, 78, 96))
        cv.ellipse(cx + sx * 25 + sx * 14, 1574, 40, 16, fill=BLACK)
    cv.poly([(cx - 42, 868), (cx + 42, 868), (cx + 35, 1196), (cx - 35, 1196)], fill=WHITE, outline=BLACK, width=8)
    cv.line([(cx - 34, 1184), (cx + 34, 1184)], 12, (44, 46, 60))
    cv.poly([(cx - 10, 884), (cx + 10, 884), (cx + 15, 990), (cx, 1024), (cx - 15, 990)], fill=(52, 84, 150), outline=BLACK, width=4)
    for side, ia in ((-1, 0), (1, 1)):
        vec = pose_vec(TPOSE, arms_a[ia], arms_b[ia], u)
        draw_arm(cv, (cx + side * 40, 892), side, vec, talk, t, None, 21, ia * 2.0)
    hy = 764 + bob
    cv.ellipse(cx, hy, 90, 90, fill=WHITE, outline=BLACK, width=8)
    face(cv, cx, hy, 90, emo, talk, (-0.85, 0.35), blinking(t, 0.0))
    cv.put(frame)


def draw_ali(frame, t, emo, arms_a, arms_b, u, talk, bob, hand_scratch=False):
    cx = A_X
    cv = Cv((10, 800, 680, 1660))
    cv.ellipse(cx + 20, 1610, 270, 24, fill=(0, 0, 0, 34))
    # Beine + Turnschuhe unter dem Tisch
    for sx in (-1, 1):
        x = cx + sx * 52
        cv.line([(x, 1380), (x, 1560)], 46, BLACK)
        cv.line([(x, 1380), (x, 1560)], 36, (66, 78, 112))
        cv.ellipse(x - 6, 1590, 54, 24, fill=WHITE, outline=BLACK, width=6)
        cv.ellipse(x - 28, 1592, 24, 18, fill=RED)
        cv.ellipse(x - 6, 1590, 54, 24, outline=BLACK, width=6)
    # Stuhllehne
    cv.poly([(cx - 118, 1110), (cx + 118, 1110), (cx + 118, 1350), (cx - 118, 1350)], fill=(120, 124, 134), outline=BLACK, width=7)
    # Oberkoerper (Hoodie)
    cv.poly([(cx - 94, 1120), (cx + 94, 1120), (cx + 108, 1350), (cx - 108, 1350)], fill=RED, outline=BLACK, width=8)
    cv.ellipse(cx, 1118, 76, 36, fill=RED_D, outline=BLACK, width=7)
    for sx in (-1, 1):
        cv.line([(cx + sx * 22, 1146), (cx + sx * 30, 1230)], 6, WHITE)
        cv.ellipse(cx + sx * 30, 1236, 8, 8, fill=WHITE, outline=BLACK, width=3)
    # Tisch
    cv.poly([(40, 1352), (620, 1352), (666, 1296), (96, 1296)], fill=(196, 200, 208), outline=BLACK, width=7)
    cv.poly([(330, 1334), (460, 1334), (490, 1304), (358, 1304)], fill=WHITE, outline=(110, 114, 124), width=3)
    cv.poly([(40, 1352), (620, 1352), (620, 1396), (40, 1396)], fill=(140, 144, 154), outline=BLACK, width=7)
    for x in (82, 580):
        cv.line([(x, 1396), (x, 1600)], 12, (96, 100, 110))
    # Arme
    for side, ia in ((-1, 0), (1, 1)):
        vec = pose_vec(APOSE, arms_a[ia], arms_b[ia], u)
        draw_arm(cv, (cx + side * 82, 1146), side, vec, talk, t, RED, 23, ia * 2.5)
    # Kopf mit Kappe
    hy = 1010 + bob
    cv.ellipse(cx, hy, 92, 92, fill=WHITE, outline=BLACK, width=8)
    face(cv, cx, hy, 92, emo, talk, (0.85, -0.1), blinking(t, 1.0))
    r = 96
    a0 = math.asin(66 / r)
    arc = [(cx + r * math.cos(th), hy + r * math.sin(th)) for th in np.linspace(math.pi + a0, 2 * math.pi - a0, 22)]
    cv.poly(arc + [(cx, hy - 66 + 12)], fill=RED, outline=BLACK, width=7)
    cv.poly([(cx - 88, hy - 56), (cx - 140, hy - 42), (cx - 136, hy - 26), (cx - 80, hy - 40)], fill=RED, outline=BLACK, width=6)
    cv.ellipse(cx, hy - 96, 8, 8, fill=RED_D, outline=BLACK, width=4)
    cv.put(frame)


def draw_mates(frame, t, spk, laugh_t):
    cv = Cv((540, 960, 860, 1330))
    for (mx, my), seed in (((606, 1118), 2.0), ((700, 1086), 3.0), ((790, 1108), 4.0)):
        cv.poly([(mx - 30, my + 40), (mx + 30, my + 40), (mx + 36, my + 190), (mx - 36, my + 190)], fill=(238, 240, 244), outline=BLACK, width=7)
        cv.ellipse(mx, my, 56, 56, fill=(244, 246, 250), outline=BLACK, width=7)
        if laugh_t is not None and t >= laugh_t:
            lt = t - laugh_t
            face(cv, mx, my + 2 * math.sin(lt * 16 + seed), 56, "laugh", (lt * 3 + seed) % 1.0, (0, 0), False)
        else:
            look = (-0.9, 0.2) if spk == "A" else (0.9, 0.2) if spk == "L" else (0, 0.3)
            face(cv, mx, my, 56, "neutral", 0, look, blinking(t, seed))
    cv.poly([(560, 1268), (850, 1268), (872, 1236), (582, 1236)], fill=(190, 194, 202), outline=BLACK, width=6)
    cv.poly([(560, 1268), (850, 1268), (850, 1296), (560, 1296)], fill=(150, 154, 164), outline=BLACK, width=6)
    cv.put(frame)


# ================================================================ Requisiten
@lru_cache(None)
def wecker_img():
    cv = Cv((0, 0, 320, 300))
    cx, cy = 160, 160
    cv.ellipse(cx - 70, cy - 82, 36, 30, fill=(150, 154, 164), outline=BLACK, width=6)
    cv.ellipse(cx + 70, cy - 82, 36, 30, fill=(150, 154, 164), outline=BLACK, width=6)
    cv.line([(cx - 70, cy + 86), (cx - 94, cy + 124)], 12, BLACK)
    cv.line([(cx + 70, cy + 86), (cx + 94, cy + 124)], 12, BLACK)
    cv.ellipse(cx, cy, 98, 98, fill=RED, outline=BLACK, width=8)
    cv.ellipse(cx, cy, 74, 74, fill=WHITE, outline=BLACK, width=5)
    for k in range(12):
        a = k * math.pi / 6
        cv.line([(cx + 62 * math.sin(a), cy - 62 * math.cos(a)), (cx + 70 * math.sin(a), cy - 70 * math.cos(a))], 4, BLACK)
    cv.line([(cx, cy), (cx, cy - 50)], 7, BLACK)
    cv.line([(cx, cy), (cx + 34, cy + 14)], 7, BLACK)
    cv.ellipse(cx, cy, 8, 8, fill=BLACK)
    return cv.out()


def ring_lines(frame, cx, cy, t):
    d = ImageDraw.Draw(frame, "RGBA")
    ph = int(t * 14) % 2
    for sx in (-1, 1):
        for k in range(3):
            a = (-0.55 + 0.55 * k + (0.08 if ph else -0.08)) * 1.0
            x1, y1 = cx + sx * 150, cy - 40 + k * 0 - 70 + k * 56
            d.line([(x1, y1), (x1 + sx * (26 + 8 * ph), y1 + a * 40)], fill=(*BLACK, 255), width=9)


def draw_wecker(frame, t, t0, t1):
    a = clamp((t - t0) / 0.15) * clamp((t1 - t) / 0.2)
    if a <= 0:
        return
    s = 0.7 + 0.3 * back_out((t - t0) / 0.3)
    bx, by = 520, 800
    d = ImageDraw.Draw(frame, "RGBA")
    for (x, y, r) in ((398, 940, 13), (432, 898, 20), (468, 856, 28)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(255 * a)), outline=(*BLACK, int(255 * a)), width=5)
    bub = Image.new("RGBA", (420, 360), (0, 0, 0, 0))
    ImageDraw.Draw(bub).ellipse((6, 6, 413, 353), fill=WHITE, outline=BLACK, width=8)
    comp_center(frame, bub, bx, by, s, a)
    shake = math.sin(t * 40) * 7
    comp_center(frame, wecker_img(), bx, by + 6, 0.74 * s, a, shake)
    if a > 0.5:
        ring_lines(frame, bx, by, t)


def draw_zzz(frame, t, t0):
    if t < t0:
        return
    for k, (x, y, sz) in enumerate(((415, 860, 74), (470, 780, 100), (540, 690, 130))):
        lt = t - t0 - k * 0.28
        a = clamp(lt / 0.2)
        if a <= 0:
            continue
        img = text_img("Z", sz)
        comp_center(frame, img, x + 12 * math.sin(t * 2 + k), y - 14 * ((t - t0) % 1.6) + 12, 0.8 + 0.2 * back_out(lt / 0.3), a)


def draw_haha(frame, t, t0):
    if t < t0:
        return
    for k, (x, y) in enumerate(((560, 935), (650, 860), (720, 950))):
        lt = t - t0 - k * 0.18
        if lt < 0:
            continue
        txt = "HA" if (int(t * 6) + k) % 2 == 0 else "HA!"
        comp_center(frame, text_img(txt, 70), x, y + 5 * math.sin(t * 14 + k), 0.7 + 0.3 * back_out(lt / 0.25),
                    clamp(lt / 0.1), 8 * math.sin(t * 9 + k))


@lru_cache(None)
def text_img(text, size, color=WHITE, weight="Black", stroke=None):
    f = font(weight, size)
    sw = stroke if stroke is not None else max(6, size // 10)
    bb = f.getbbox(text, stroke_width=sw)
    pad = 6
    img = Image.new("RGBA", (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - bb[0], pad - bb[1]), text, font=f, fill=color, stroke_width=sw, stroke_fill=BLACK)
    return img


# ================================================================ Hintergrund
@lru_cache(None)
def background():
    y = np.arange(H, dtype=np.float32)[:, None]
    wall = 226 - 36 * np.clip(y / FLOOR_Y, 0, 1)
    floor = 168 - 54 * np.clip((y - FLOOR_Y) / (H - FLOOR_Y), 0, 1)
    g = np.where(y < FLOOR_Y, wall, floor)
    arr = np.repeat(g, W, axis=1)
    img = Image.fromarray(np.stack([arr * 0.985, arr * 0.99, arr], axis=2).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    # Decke und Lampen
    d.rectangle((0, 0, W, 84), fill=(176, 181, 191))
    d.line((0, 84, W, 84), fill=BLACK, width=6)
    for x in (70, 470, 870):
        d.rounded_rectangle((x, 16, x + 190, 60), 8, fill=WHITE, outline=(120, 124, 134), width=4)
    # Schild: Unterricht 8:00 Uhr
    d.rounded_rectangle((400, 130, 800, 300), 18, fill=WHITE, outline=BLACK, width=8)
    d.text((600, 178), "Unterricht", font=font("ExtraBold", 54), fill=(60, 64, 78), anchor="mm")
    d.text((600, 245), "8:00 Uhr", font=font("Black", 60), fill=RED, anchor="mm")
    # Wanduhr: 8:45
    cx, cy, r = 940, 215, 80
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE, outline=BLACK, width=9)
    for k in range(12):
        a = k * math.pi / 6
        d.line((cx + 64 * math.sin(a), cy - 64 * math.cos(a), cx + 73 * math.sin(a), cy - 73 * math.cos(a)), fill=BLACK, width=5)
    ah, am = math.radians(8.75 * 30), math.radians(45 * 6)
    d.line((cx, cy, cx + 38 * math.sin(ah), cy - 38 * math.cos(ah)), fill=BLACK, width=9)
    d.line((cx, cy, cx + 58 * math.sin(am), cy - 58 * math.cos(am)), fill=BLACK, width=6)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=BLACK)
    # Poster / Tafel links
    d.rounded_rectangle((40, 360, 200, 540), 8, fill=(250, 250, 252), outline=BLACK, width=6)
    for k in range(5):
        d.line((62, 394 + k * 28, 178 - (k % 2) * 30, 394 + k * 28), fill=(150, 154, 166), width=6)
    # Boden: Fluchtlinien
    d.line((0, FLOOR_Y, W, FLOOR_Y), fill=BLACK, width=8)
    d.rectangle((0, FLOOR_Y - 22, W, FLOOR_Y), fill=(120, 126, 138))
    for n in range(1, 9):
        yy = FLOOR_Y + 12 * n ** 1.55
        d.line((0, yy, W, yy), fill=(255, 255, 255, 22), width=3)
    for x in range(-1400, 2500, 230):
        d.line((540 + (x - 540) * 0.18, FLOOR_Y, x, H), fill=(255, 255, 255, 22), width=3)
    return img


LOGO = None


def load_logo():
    global LOGO
    src = Image.open(HERE.parent / "dtz_email" / "bilder" / "logo.png").convert("RGB")
    src = src.resize((int(src.width * 1.4), int(src.height * 1.4)), Image.LANCZOS)
    pad = 10
    card = Image.new("RGBA", (src.width + 2 * pad, src.height + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 24, fill=WHITE)
    m = Image.new("L", src.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, src.width - 1, src.height - 1), 18, fill=255)
    card.paste(src, (pad, pad), m)
    LOGO = card


# ================================================================ Sprache + Zeitplan
CLIPS = {}
TL = {}
MOUTH = {"L": None, "A": None}


def spoken_text(display):
    s = display
    for a, b in getattr(C, "AUSSPRACHE", {}).items():
        s = s.replace(a, b)
    return s


def synth_all():
    from common.audio import SR, ensure_voice, speak
    model = ensure_voice()
    tmp = HERE.parent / ".cache" / "line_comic.wav"
    for ln in C.ZEILEN:
        key = (ln["wer"], ln["text"])
        if key in CLIPS:
            continue
        sp = SPRECHER[ln["wer"]]
        seg = speak(spoken_text(ln["text"]), tmp, model, sp["length"])
        f = sp["pitch"]                       # Tonhoehe ueber Resampling
        seg = np.interp(np.arange(int(len(seg) / f)) * f, np.arange(len(seg)), seg).astype(np.float32)
        nz = np.nonzero(np.abs(seg) > 0.02)[0]
        s0, s1 = (nz[0] / SR, nz[-1] / SR) if len(nz) else (0, len(seg) / SR)
        CLIPS[key] = (seg, s0, s1)


def plan():
    synth_all()
    t = C.START
    lines = []
    for i, ln in enumerate(C.ZEILEN):
        seg, s0, s1 = CLIPS[(ln["wer"], ln["text"])]
        d = s1 - s0
        t += ln.get("pause_davor", 0.0)
        lines.append(dict(ln, start=t, end=t + d, i=i))
        t += d + C.PAUSE
    last = lines[-1]["end"]
    TL["lines"] = lines
    TL["react"] = last + 0.12
    TL["outro"] = last + C.REAKTION_DAUER
    TL["total"] = round((TL["outro"] + C.OUTRO_DAUER) * FPS) / FPS
    TL["n"] = int(round(TL["total"] * FPS))
    print(f"Dauer {TL['total']:.1f} s, {len(lines)} Zeilen")


def build_audio(out_wav):
    from common.audio import SR, add, make_music, tone
    total = TL["total"]
    music = make_music(total, [], 9999) * 0.11
    voice = np.zeros_like(music)
    n = TL["n"]
    MOUTH["L"], MOUTH["A"] = np.zeros(n), np.zeros(n)
    blk = SR // FPS
    for ln in TL["lines"]:
        seg, s0, _ = CLIPS[(ln["wer"], ln["text"])]
        add(voice, 0.95 * seg, ln["start"] - s0)
        rms = np.sqrt(np.convolve(seg ** 2, np.ones(blk) / blk, mode="same"))
        ref = np.percentile(rms[rms > 0.01], 85) if (rms > 0.01).any() else 1
        for fi in range(int(ln["start"] * FPS), min(n, int(ln["end"] * FPS) + 1)):
            si = int((fi / FPS - (ln["start"] - s0)) * SR)
            if 0 <= si < len(rms):
                MOUTH[ln["wer"]][fi] = clamp(rms[si] / ref * 0.95)
    for k in ("L", "A"):                       # Mund glaetten
        MOUTH[k] = np.convolve(MOUTH[k], [0.25, 0.5, 0.25], mode="same")
    # Effekte
    sfx = np.zeros_like(music)
    w = TL["wecker"]
    if w:
        for rep in range(2):
            for kk in range(4):
                at = w[0] + rep * 0.62 + kk * 0.1
                bn = int(0.055 * SR)
                env = np.sin(np.pi * np.arange(bn) / bn)
                add(sfx, 0.16 * env * tone(2350, 0.055, (1, 0.3)), at)
    tr = TL["react"] + 0.05                    # Ba-dum-tss
    for dt, f in ((0, 120), (0.17, 96)):
        kn = int(0.3 * SR)
        kt = np.arange(kn) / SR
        add(sfx, 0.5 * np.sin(2 * np.pi * np.cumsum(f * (1 + 1.4 * np.exp(-kt * 22))) / SR) * np.exp(-kt * 10), tr + dt)
    rng = np.random.default_rng(3)
    for dt, ln_, dec, amp in ((0.34, 0.9, 3.0, 0.20),):
        cn = int(ln_ * SR)
        noise = np.diff(rng.standard_normal(cn), prepend=0)
        add(sfx, amp * noise * np.exp(-np.arange(cn) / SR * dec), tr + dt)
    win = int(0.2 * SR)
    env = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 6, 0, 1)
    env = np.convolve(env, np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
    mix = music * (1 - 0.55 * env) + voice + sfx
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.9
    pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wv:
        wv.setnchannels(2)
        wv.setsampwidth(2)
        wv.setframerate(SR)
        wv.writeframes(pcm.tobytes())


# ================================================================ Zustaende
def make_states():
    cur = dict(le="neutral", la=("hips", "hips"), ae="neutral", aa=("rest", "rest"))
    out = [(0.0, dict(cur))]
    for ln in TL["lines"]:
        cur = dict(cur)
        for k in ("le", "la", "ae", "aa"):
            if k in ln:
                cur[k] = ln[k]
        out.append((ln["start"] - 0.12, dict(cur)))
    cur = dict(cur)
    cur.update(C.REAKTION)
    out.append((TL["react"], dict(cur)))
    TL["states"] = out


def state_at(t):
    S = TL["states"]
    k = max(i for i, (ts, _) in enumerate(S) if ts <= t)
    prev = S[max(0, k - 1)][1]
    u = clamp((t - S[k][0]) / 0.3) if k > 0 else 1.0
    return S[k][1], prev, u


def speaker_at(t):
    for ln in TL["lines"]:
        if ln["start"] - 0.05 <= t <= ln["end"] + 0.15:
            return ln["wer"]
    return None


# ================================================================ Untertitel
def chunks(text):
    toks, out, i = text.split(), [], 0
    while i < len(toks):
        c = toks[i]
        if len(c.strip(".,!?")) <= 3 and i + 1 < len(toks) and c[-1] not in ".,!?":
            c += " " + toks[i + 1]
            i += 1
        out.append(c)
        i += 1
    return out


@lru_cache(None)
def cap_img(text, color):
    for size in range(150, 70, -6):
        img = text_img(text, size, color)
        if img.width <= W - 110:
            return img
    return img


@lru_cache(None)
def name_pill(wer):
    sp = SPRECHER[wer]
    f = font("ExtraBold", 44)
    wd = int(f.getlength(sp["name"])) + 70
    img = Image.new("RGBA", (wd, 78), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, wd - 1, 77), 39, fill=sp["farbe"], outline=BLACK, width=5)
    d.text((wd / 2, 40), sp["name"], font=f, fill=WHITE, anchor="mm")
    return img


def draw_caption(frame, t):
    for ln in TL["lines"]:
        if ln["start"] - 0.05 <= t < ln["end"] + 0.3:
            ch = chunks(ln["text"])
            wts = [len(c) + (7 if c[-1] in ".?!" else 3 if c[-1] == "," else 0) for c in ch]
            tot, acc, starts = sum(wts), 0.0, []
            for wgt in wts:
                starts.append(ln["start"] + (ln["end"] - ln["start"]) * acc / tot)
                acc += wgt
            k = max(i for i, s in enumerate(starts) if t >= s - 0.04) if t >= starts[0] - 0.04 else 0
            col = SPRECHER[ln["wer"]]["text"]
            pop = back_out((t - starts[k] + 0.04) / 0.16)
            fade = clamp((ln["end"] + 0.3 - t) / 0.2)
            comp_center(frame, name_pill(ln["wer"]), W / 2, 420, 1, fade)
            comp_center(frame, cap_img(ch[k], col), W / 2, 545, 0.78 + 0.22 * pop, fade)
            return


def draw_title(frame, t):
    if t > C.START - 0.1:
        return
    a = clamp(t / 0.25) * clamp((C.START - 0.1 - t) / 0.25)
    s = 0.8 + 0.2 * back_out(t / 0.45)
    comp_center(frame, text_img(C.TITEL[0], 118, WHITE), W / 2, 470, s, a)
    comp_center(frame, text_img(C.TITEL[1], 150, YELLOW), W / 2, 625, s, a)
    pill = Image.new("RGBA", (770, 84), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    d.rounded_rectangle((0, 0, 769, 83), 42, fill=ORANGE, outline=BLACK, width=5)
    d.text((385, 43), C.UNTERTITEL, font=font("ExtraBold", 42), fill=WHITE, anchor="mm")
    comp_center(frame, pill, W / 2, 770, 1, a * clamp((t - 0.3) / 0.25))


# ================================================================ Bild
def zoom_params(t):
    z = 1.0 + 0.09 * ease_out((t - C.START + 0.2) / 0.8)
    if t >= TL["react"]:
        z += 0.03 * ease_out((t - TL["react"]) / 0.5)
    return z


def render_frame(fi):
    t = fi / FPS
    total = TL["total"]
    frame = background().copy()
    st, prev, u = state_at(t)
    spk = speaker_at(t)
    mL, mA = MOUTH["L"][fi], MOUTH["A"][fi]
    reacting = t >= TL["react"]
    draw_mates(frame, t, spk, TL["react"] + 0.08)
    bobA = 5 * math.sin(t * 13) * mA + 2 * math.sin(t * 2)
    bobL = 5 * math.sin(t * 13) * mL + 2 * math.sin(t * 2 + 1)
    draw_ali(frame, t, st["ae"], prev["aa"], st["aa"], u, mA, bobA)
    draw_teacher(frame, t, st["le"], prev["la"], st["la"], u, mL, bobL)
    if TL["wecker"]:
        draw_wecker(frame, t, *TL["wecker"])
    draw_zzz(frame, t, TL["zzz"])
    if reacting:
        draw_haha(frame, t, TL["react"] + 0.15)
    # Kamera: leichter Zoom Richtung Sprecher
    z = zoom_params(t)
    cam = TL["cam"][fi]
    bw, bh = W / z, H / z
    cxz = clamp(cam, bw / 2, W - bw / 2)
    cyz = clamp(1010, bh / 2, H - bh / 2)
    box = (cxz - bw / 2, cyz - bh / 2, cxz + bw / 2, cyz + bh / 2)
    frame = frame.resize((W, H), Image.BICUBIC, box=box) if z > 1.001 else frame
    # Logo, Titel, Untertitel
    comp(frame, LOGO, (28, 22 + 70 - 70), 1.0)
    draw_title(frame, t)
    if t < TL["outro"]:
        draw_caption(frame, t)
    else:
        lt = t - TL["outro"]
        veil = Image.new("RGBA", (W, H), (255, 255, 255, int(235 * ease_out(lt / 0.4))))
        frame.alpha_composite(veil)
        comp_center(frame, LOGO, W / 2, 780, 2.5 * (0.85 + 0.15 * back_out(lt / 0.6)), clamp(lt / 0.3))
        pill = Image.new("RGBA", (800, 118), (0, 0, 0, 0))
        d = ImageDraw.Draw(pill)
        d.rounded_rectangle((0, 0, 799, 117), 59, fill=ORANGE)
        d.text((400, 61), "Folge der ELM Akademie", font=font("ExtraBold", 54), fill=WHITE, anchor="mm")
        comp_center(frame, pill, W / 2, 1130, max(0.01, back_out((lt - 0.5) / 0.5)), clamp((lt - 0.5) / 0.2))
    out = frame.convert("RGB")
    a = min(clamp(t / 0.3), clamp((total - t) / 0.6))
    if a < 1:
        out = Image.blend(Image.new("RGB", (W, H), (255, 255, 255)), out, a)
    return out.tobytes()


def build_cam():
    n = TL["n"]
    cam, cur = np.zeros(n), 540.0
    for fi in range(n):
        spk = speaker_at(fi / FPS)
        tgt = {"A": 500, "L": 590}.get(spk, 540) if fi / FPS < TL["react"] else 540
        cur += (tgt - cur) * 0.10
        cam[fi] = cur
    TL["cam"] = cam


def main():
    print("Erzeuge Sprache ...", flush=True)
    plan()
    w = next((ln for ln in TL["lines"] if ln.get("prop") == "wecker"), None)
    TL["wecker"] = (w["start"] + 0.3, w["end"] + 0.25) if w else None
    z = next((ln for ln in TL["lines"] if ln.get("prop") == "zzz"), None)
    TL["zzz"] = (z["end"] - 0.6) if z else 1e9
    load_logo()
    make_states()
    wav = HERE.parent / ".cache" / f"{NAME}.wav"
    build_audio(wav)
    build_cam()
    if "--preview" in sys.argv:
        out = HERE / "vorschau"
        out.mkdir(exist_ok=True)
        ts = [1.0] + [ln["start"] + 0.5 for ln in TL["lines"]] + [TL["react"] + 1.0, TL["outro"] + 1.5]
        for x in ts:
            Image.frombytes("RGB", (W, H), render_frame(int(x * FPS))).save(out / f"t{x:05.1f}.png")
        print("Vorschau in", out)
        return
    outdir = HERE / "ausgabe"
    outdir.mkdir(exist_ok=True)
    out = outdir / f"{NAME}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.0:LRA=9",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", f"{TL['total']:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, data in enumerate(pool.imap(render_frame, range(TL["n"]), chunksize=6)):
            proc.stdin.write(data)
            if k % (FPS * 5) == 0:
                print(f"{k / FPS:5.1f}s / {TL['total']:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("Fertig:", out)


if __name__ == "__main__":
    main()
