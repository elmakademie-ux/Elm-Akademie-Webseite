"""
Stil 2 der Comic-Engine: Cartoon mit Nahaufnahmen und Schnitten (Lehrer mit Glatze und Brille,
Schüler mit Stachelhaaren und Rucksack), unscharfes Klassenzimmer, Wörter oben im Bild.

    python3 render_cartoon.py schlauer_schueler             -> ausgabe/schlauer_schueler_cartoon.mp4
    python3 render_cartoon.py schlauer_schueler --preview   -> vorschau/*.png

Nutzt dieselben Folgen (folgen/<name>.py), dieselbe Stimme, Musik und Untertitel-Logik wie render.py.
"""
import math
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import render as R
from render import (BLACK, EMO, FPS, H, W, WHITE, Cv, back_out, clamp, comp, comp_center, ease_out, lerp,
                    text_img)

R.CAP_NAME_Y, R.CAP_Y = 262, 395
R.OUT_SUFFIX = "_cartoon"

SKIN_T, SKIN_T2, SHIRT_T = (240, 192, 148), (228, 172, 128), (114, 158, 222)
SKIN_A, SHIRT_A = (242, 198, 156), (236, 243, 250)
LINE = 8


# ================================================================ Augen und Mund
def eye(cv, x, y, rx, ry, pr, lid, look, skin, happy=False):
    if happy:
        pts = [(x + rx * (2 * u - 1), y + 0.25 * ry - 0.9 * ry * math.sin(math.pi * u)) for u in np.linspace(0, 1, 14)]
        cv.line(pts, 11, BLACK)
        return
    cv.ellipse(x, y, rx, ry, fill=WHITE)
    px, py = x + look[0] * rx * 0.36, y + look[1] * ry * 0.30
    cv.ellipse(px, py, pr, pr, fill=(70, 48, 34))
    cv.ellipse(px, py, pr * 0.62, pr * 0.62, fill=(14, 14, 20))
    cv.ellipse(px - pr * 0.3, py - pr * 0.32, pr * 0.2, pr * 0.2, fill=WHITE)
    if lid > 0:
        ylid = y - ry + 2 * ry * lid
        xs = np.linspace(-rx, rx, 20)
        top = [(x + xx, y - ry * math.sqrt(max(0, 1 - (xx / rx) ** 2))) for xx in xs]
        bot = [(x + xx, min(ylid, y + ry * math.sqrt(max(0, 1 - (xx / rx) ** 2)))) for xx in xs[::-1]]
        cv.poly(top + bot, fill=skin)
        cv.line([(x - rx, ylid), (x + rx, ylid)], 10, BLACK)
    cv.ellipse(x, y, rx, ry, outline=BLACK, width=7)


def mouth(cv, x, y, w, shape, talk, s):
    """x, y Mitte, w halbe Breite (alles schon skaliert)."""
    if talk > 0.06 or shape in ("o", "grin", "laugh"):
        if talk > 0.06:
            rx, ry = w * (0.62 + 0.2 * talk), s * (10 + 54 * talk)
        elif shape == "o":
            rx, ry = w * 0.36, s * 44
        elif shape == "grin":
            rx, ry = w * 0.8, s * 30
        else:
            rx, ry = w * 0.85, s * 44
        cv.ellipse(x, y, rx, ry, fill=(122, 38, 52))
        cv.ellipse(x, y - ry * 0.52, rx * 0.84, ry * 0.34, fill=WHITE)
        cv.ellipse(x, y + ry * 0.5, rx * 0.55, ry * 0.36, fill=(226, 98, 112))
        cv.ellipse(x, y, rx, ry, outline=BLACK, width=LINE * s)
    elif shape == "smile":
        cv.line([(x + w * (2 * u - 1), y - 8 * s + 34 * s * math.sin(math.pi * u)) for u in np.linspace(0, 1, 12)], 9 * s, BLACK)
    else:   # flat / leichter Mundwinkel nach unten
        cv.line([(x + w * (2 * u - 1), y + 8 * s - 20 * s * math.sin(math.pi * u)) for u in np.linspace(0, 1, 12)], 9 * s, BLACK)


def glass(cv, x, y, r):
    """Halbtransparentes Brillenglas (ueberblendet, ersetzt nicht)."""
    ov = Image.new("RGBA", cv.im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    px, py = cv.p(x, y)
    rr = r * 2
    d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(214, 236, 252, 70))
    d.line((px - 0.65 * rr, py - 0.45 * rr, px - 0.3 * rr, py - 0.78 * rr), fill=(255, 255, 255, 190), width=int(r * 0.16))
    cv.im.alpha_composite(ov)


# ================================================================ Lehrer
def teacher(cv, cx, cy, s, bottom, emo, talk, look, blink):
    e = EMO[emo]
    lid = max(e["lid"], 0.92 if blink else 0.0)

    def q(dx, dy):
        return (cx + dx * s, cy + dy * s)
    # Hemd + Hals
    cv.poly([q(-560, 0)[:1] + (bottom,), (cx - 560 * s, cy + 640 * s), q(-330, 420), q(-90, 330), q(90, 330),
             q(330, 420), (cx + 560 * s, cy + 640 * s), (cx + 560 * s, bottom)], fill=SHIRT_T, outline=BLACK, width=LINE)
    cv.poly([q(-90, 240), q(90, 240), q(110, 372), q(-110, 372)], fill=SKIN_T2, outline=BLACK, width=7 * s)
    cv.poly([q(-150, 330), q(-70, 322), q(-10, 420), q(-96, 450)], fill=(150, 190, 244), outline=BLACK, width=7 * s)
    cv.poly([q(150, 330), q(70, 322), q(10, 420), q(96, 450)], fill=(150, 190, 244), outline=BLACK, width=7 * s)
    cv.line([q(0, 420), q(0, 900)], 6 * s, (60, 90, 150))
    for yy in (520, 640, 760):
        cv.ellipse(*q(0, yy), 11 * s, 11 * s, fill=(236, 244, 255), outline=BLACK, width=4 * s)
    for a, b in (((-260, 560), (-180, 640)), ((250, 600), (170, 700)), ((-300, 800), (-200, 860))):
        cv.line([q(*a), q(*b)], 5 * s, (70, 104, 166))
    # Seitenhaar, Ohren
    for sx in (-1, 1):
        cv.ellipse(*q(sx * 282, -40), 58 * s, 118 * s, fill=(158, 146, 134), outline=BLACK, width=7 * s)
        cv.ellipse(*q(sx * 304, 34), 50 * s, 72 * s, fill=SKIN_T, outline=BLACK, width=7 * s)
        cv.line([q(sx * 300, 10), q(sx * 316, 36), q(sx * 300, 60)], 5 * s, BLACK)
    # Kopf
    cv.ellipse(*q(0, 0), 300 * s, 336 * s, fill=SKIN_T, outline=BLACK, width=LINE + 1)
    for dx in (-36, 8, 52):
        cv.line([q(dx, -330), q(dx + 14, -378), q(dx + 56, -372)], 5 * s, (110, 100, 92))
    for yy, ww in ((-262, 120), (-226, 90)):
        cv.line([q(-ww + 12 * k, yy + 6 * math.sin(k)) for k in range(0, 2 * ww // 12 + 1)], 5 * s, (200, 150, 110))
    # Augen und Brille
    for sx in (-1, 1):
        x, y = cx + sx * 122 * s, cy - 35 * s
        eye(cv, x, y, 74 * s, 64 * s, 27 * s, lid, look, SKIN_T, e.get("happy", False))
        cv.line([(x - 42 * s, y + 92 * s), (x, y + 100 * s), (x + 42 * s, y + 92 * s)], 5 * s, (196, 142, 108))
    for sx in (-1, 1):
        x, y = cx + sx * 122 * s, cy - 35 * s
        glass(cv, x, y, 108 * s)
        cv.ellipse(x, y, 108 * s, 108 * s, outline=BLACK, width=9 * s)
        cv.line([q(sx * 228, -50), q(sx * 292, -40)], 7 * s, BLACK)
    cv.line([q(-16, -48), q(16, -48)], 8 * s, BLACK)
    # Augenbrauen
    b = e["brow"]
    for sx in (-1, 1):
        lift = b * 34 if b > 0 else b * 10
        inner = (-b * 18) if b > 0 else (-b * 32)
        cv.line([q(sx * 36, -172 - lift + inner / 2), q(sx * 220, -150 - lift - inner / 2)], 20 * s, BLACK)
    # Nase, Mund, Falten
    cv.ellipse(*q(0, 58), 56 * s, 66 * s, fill=SKIN_T2, outline=BLACK, width=7 * s)
    cv.ellipse(*q(-20, 100), 9 * s, 6 * s, fill=(160, 100, 76))
    cv.ellipse(*q(20, 100), 9 * s, 6 * s, fill=(160, 100, 76))
    for sx in (-1, 1):
        cv.line([q(sx * 96, 60), q(sx * 112, 130), q(sx * 80, 196)], 5 * s, (200, 150, 110))
    mouth(cv, *q(0, 198), 56 * s, e["mouth"], talk, s)
    cv.line([q(-60, 262), q(0, 272), q(60, 262)], 4 * s, (205, 156, 118))


# ================================================================ Schüler
def student(cv, cx, cy, s, bottom, emo, talk, look, blink):
    e = EMO[emo]
    lid = max(e["lid"], 0.38, 0.92 if blink else 0.0)

    def q(dx, dy):
        return (cx + dx * s, cy + dy * s)
    cv.poly([(cx - 560 * s, bottom), (cx - 560 * s, cy + 620 * s), q(-300, 400), q(-80, 320), q(80, 320),
             q(300, 400), (cx + 560 * s, cy + 620 * s), (cx + 560 * s, bottom)], fill=SHIRT_A, outline=BLACK, width=LINE)
    cv.poly([q(-80, 230), q(80, 230), q(98, 360), q(-98, 360)], fill=SKIN_A, outline=BLACK, width=7 * s)
    cv.poly([q(-130, 320), q(-66, 312), q(-6, 400), q(-84, 430)], fill=WHITE, outline=BLACK, width=7 * s)
    cv.poly([q(130, 320), q(66, 312), q(6, 400), q(84, 430)], fill=WHITE, outline=BLACK, width=7 * s)
    for sx in (-1, 1):   # Rucksackgurte
        cv.poly([q(sx * 190, 330), q(sx * 270, 372), (cx + sx * 300 * s, bottom), (cx + sx * 190 * s, bottom)],
                fill=(44, 54, 78), outline=BLACK, width=6 * s)
    # Ohren + Kopf
    for sx in (-1, 1):
        cv.ellipse(*q(sx * 256, 30), 46 * s, 64 * s, fill=SKIN_A, outline=BLACK, width=7 * s)
        cv.line([q(sx * 252, 8), q(sx * 270, 32), q(sx * 252, 56)], 5 * s, (196, 140, 108))
    cv.ellipse(*q(0, 0), 258 * s, 284 * s, fill=SKIN_A, outline=BLACK, width=LINE + 1)
    # Augen
    for sx in (-1, 1):
        eye(cv, cx + sx * 98 * s, cy - 18 * s, 76 * s, 62 * s, 29 * s, lid, look, SKIN_A, e.get("happy", False))
    # Haare (Stacheln)
    hair = [(-262, -30), (-300, -150), (-246, -214), (-288, -336), (-190, -302), (-168, -424), (-88, -340), (-36, -476),
            (24, -352), (114, -458), (132, -330), (232, -404), (214, -282), (304, -302), (262, -170), (276, -30),
            (232, -70), (206, -150), (130, -182), (56, -150), (-20, -204), (-100, -142), (-182, -172), (-218, -80)]
    cv.poly([q(*p) for p in hair], fill=(18, 18, 24), outline=BLACK, width=6 * s)
    # Brauen, Nase, Mund
    b = e["brow"]
    for sx in (-1, 1):
        lift = b * 26 if b > 0 else b * 6
        inner = (-b * 14) if b > 0 else (-b * 24)
        cv.line([q(sx * 36, -118 - lift + inner / 2), q(sx * 160, -108 - lift - inner / 2)], 11 * s, BLACK)
    cv.line([q(-16, 66), q(2, 86), q(20, 70)], 7 * s, (190, 132, 100))
    mouth(cv, *q(0, 170), 58 * s, e["mouth"], talk, s)
    if e["mouth"] == "flat" and talk < 0.06:        # cooler Schmunzler statt Strich
        cv.line([q(-4, 176), q(40, 168), q(70, 150)], 8 * s, BLACK)


def char(frame, who, cx, cy, s, bottom, emo, talk, look, blink):
    cv = Cv((int(cx - 560 * s), int(cy - 520 * s), int(cx + 560 * s), int(bottom)))
    (teacher if who == "L" else student)(cv, cx, cy, s, bottom, emo, talk, look, blink)
    cv.put(frame)


# ================================================================ Klassenzimmer
@lru_cache(None)
def classroom_raw():
    img = Image.new("RGB", (W, H), (196, 224, 210))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, 0, W, 330), fill=(220, 204, 188))                       # Decke
    for x in range(0, W + 120, 120):
        d.line((x, 0, x, 330), fill=(190, 172, 156), width=3)
    for y in (110, 220):
        d.line((0, y, W, y), fill=(190, 172, 156), width=3)
    d.rectangle((120, 70, 460, 130), fill=(255, 255, 252))
    d.rectangle((640, 70, 980, 130), fill=(255, 255, 252))
    d.rectangle((0, 330, W, 352), fill=(176, 130, 96))
    d.rectangle((0, 1040, W, 1920), fill=(232, 210, 176))                   # Boden
    d.rectangle((0, 1000, W, 1040), fill=(190, 150, 112))
    for k in range(1, 14):
        yy = 1040 + 30 * k ** 1.45
        d.line((0, yy, W, yy), fill=(210, 186, 150), width=4)
    d.rectangle((40, 480, 600, 900), fill=(120, 80, 48))                    # Tafel
    d.rectangle((62, 502, 578, 878), fill=(46, 104, 84))
    d.text((160, 600), "A B C  1 2 3", fill=(220, 236, 230, 190), font=R.font("Black", 70))
    d.rectangle((640, 400, 800, 640), fill=(250, 244, 226), outline=(150, 110, 70), width=6)   # Poster
    d.ellipse((680, 440, 760, 520), fill=(250, 190, 40))
    d.rectangle((830, 470, 1030, 640), fill=(240, 246, 236), outline=(150, 110, 70), width=6)
    d.ellipse((880, 500, 980, 600), fill=(90, 150, 220))
    d.ellipse((900, 520, 950, 570), fill=(110, 180, 110))
    d.rectangle((860, 780, 1040, 830), fill=(176, 130, 96))                 # Globus
    d.ellipse((880, 650, 1020, 790), fill=(90, 150, 220))
    d.ellipse((910, 690, 970, 750), fill=(110, 180, 110))
    for x0, y0 in ((-60, 1020), (400, 1000), (840, 1030)):                  # Tische
        d.polygon([(x0, y0 + 120), (x0 + 420, y0 + 120), (x0 + 480, y0 + 40), (x0 + 60, y0 + 40)], fill=(204, 150, 92))
        d.rectangle((x0 + 20, y0 + 120, x0 + 40, y0 + 330), fill=(120, 90, 70))
        d.rectangle((x0 + 400, y0 + 120, x0 + 420, y0 + 330), fill=(120, 90, 70))
    return img


@lru_cache(None)
def bg_wide():
    return classroom_raw().filter(ImageFilter.GaussianBlur(5)).convert("RGBA")


@lru_cache(None)
def bg_close(side):
    x0 = {"L": 30, "A": 400}.get(side, 215)
    w = 620
    h = int(w * H / W)
    img = classroom_raw().crop((x0, 380, x0 + w, 380 + h)).resize((W, H), Image.BICUBIC)
    return img.filter(ImageFilter.GaussianBlur(9)).convert("RGBA")


# ================================================================ Schnitte
def build_shots():
    L = R.TL["lines"]
    shots = [(0.0, L[0]["start"] - 0.25, "wide", None)]
    for k, ln in enumerate(L):
        t0 = ln["start"] - 0.25
        t1 = (L[k + 1]["start"] - 0.25) if k + 1 < len(L) else R.TL["react"] - 0.1
        shots.append((t0, t1, "close", ln["wer"]))
    shots.append((R.TL["react"] - 0.1, R.TL["total"] + 1, "wide", None))
    R.TL["shots"] = shots


def shot_at(t):
    for s in R.TL["shots"]:
        if s[0] <= t < s[1]:
            return s
    return R.TL["shots"][-1]


def render_frame(fi):
    t = fi / FPS
    st, _, _ = R.state_at(t)
    mL, mA = R.MOUTH["L"][fi], R.MOUTH["A"][fi]
    t0, t1, kind, who = shot_at(t)
    prog = clamp((t - t0) / max(0.5, t1 - t0))
    bl, ba = R.blinking(t, 0.0), R.blinking(t, 1.0)
    lookL, lookA = (0.7, 0.35), (-0.7, -0.3)
    if kind == "wide":
        frame = bg_wide().copy()
        char(frame, "A", 800, 1230, 0.5, H, st["ae"], mA, lookA, ba)
        char(frame, "L", 290, 1010, 0.64, H, st["le"], mL, lookL, bl)
        if t >= R.TL["zzz"]:
            for k in range(3):
                lt = t - R.TL["zzz"] - 0.2 * k
                if lt > 0:
                    comp_center(frame, text_img("Z", 70 + 30 * k), 840 + 40 * k, 1010 - 90 * k - 18 * ((t * 1.2) % 1),
                                0.8 + 0.2 * back_out(lt / 0.3), clamp(lt / 0.2))
        z = 1.0 + 0.04 * prog
    else:
        frame = bg_close(who).copy()
        listener = "A" if who == "L" else "L"
        bob = 5 * math.sin(t * 13) * (mL if who == "L" else mA)
        lcx = 1000 if listener == "A" else 80
        if listener == "A":
            char(frame, "A", lcx, 1560, 0.5, H + 400, st["ae"], 0, lookA, ba)
        else:
            char(frame, "L", lcx, 1560, 0.5, H + 400, st["le"], 0, (0.8, 0.3), bl)
        if who == "L":
            char(frame, "L", 540, 1040 + bob, 1.0, H + 600, st["le"], mL, (0.5, 0.3), bl)
        else:
            char(frame, "A", 540, 1060 + bob, 1.0, H + 600, st["ae"], mA, (-0.2, -0.15), ba)
            w = R.TL["wecker"]
            if w and w[0] <= t < w[1]:
                a = clamp((t - w[0]) / 0.15) * clamp((w[1] - t) / 0.2)
                for (x, y, r) in ((760, 800, 12), (800, 750, 18)):
                    d = ImageDraw.Draw(frame, "RGBA")
                    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(255 * a)), outline=(*BLACK, int(255 * a)), width=5)
                bub = Image.new("RGBA", (330, 290), (0, 0, 0, 0))
                ImageDraw.Draw(bub).ellipse((6, 6, 323, 283), fill=WHITE, outline=BLACK, width=8)
                comp_center(frame, bub, 880, 640, 0.7 + 0.3 * back_out((t - w[0]) / 0.3), a)
                comp_center(frame, R.wecker_img(), 880, 646, 0.62, a, math.sin(t * 40) * 7)
        z = 1.0 + 0.06 * prog
    bw, bh = W / z, H / z
    cx, cy = W / 2, 1000 if kind == "close" else 1000
    frame = frame.resize((W, H), Image.BICUBIC, box=(cx - bw / 2, clamp(cy, bh / 2, H - bh / 2) - bh / 2,
                                                       cx + bw / 2, clamp(cy, bh / 2, H - bh / 2) + bh / 2)) if z > 1.001 else frame
    comp(frame, R.LOGO, (28, 22))
    R.draw_title(frame, t)
    if t < R.TL["outro"]:
        R.draw_caption(frame, t)
    return R.finish(frame, t)


R.render_frame = render_frame
_orig_build_cam = R.build_cam


def _main():
    orig_make = R.make_states

    def make():
        orig_make()
        build_shots()
    R.make_states = make
    R.main()


if __name__ == "__main__":
    _main()
