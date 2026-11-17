"""
Rendert das A1-Lernvideo "Mein Tagesablauf" (1080x1920, 30 fps, 60 s, MP4).

    python3 render.py             -> tagesablauf.mp4
    python3 render.py --preview   -> vorschau/*.png (einzelne Bilder, schnell)

Texte, Zeiten und Farben stehen in inhalt.py (nicht hier).
"""
import math
import os
import re
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import inhalt as C  # noqa: E402

W, H, FPS = 1080, 1920, 30
N = len(C.SZENEN)
TOTAL = C.INTRO_DAUER + N * C.SZENEN_DAUER + C.OUTRO_DAUER
N_FRAMES = int(round(TOTAL * FPS))
FONT_DIR = Path("/usr/share/fonts/opentype/inter")

BG, NAVY, ORANGE, GREEN, GREY = (C.FARBE_HINTERGRUND, C.FARBE_TEXT, C.FARBE_VERB,
                                 C.FARBE_AKZENT, C.FARBE_GRAU)
WHITE = (255, 255, 255)

# Layout (y-Positionen) – alles Wichtige oberhalb von ~1600 px (Bedienelemente der Apps)
HEADER_Y = 48
DOTS_Y = 205
CLOCK_Y = 250
CARD = (90, 455, 990, 1220)          # x0, y0, x1, y1
SENT_Y = 1262
SUB_Y = 1440
REPEAT_Y = 1545
TRANS = 0.55                          # Dauer Szenenwechsel


# ======================================================================== Helfer
@lru_cache(None)
def font(weight, size):
    p = FONT_DIR / f"Inter-{weight}.otf"
    return ImageFont.truetype(str(p if p.exists() else FONT_DIR / "Inter-Regular.otf"), size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def back_out(t):  # leichtes Ueberschwingen ("Pop")
    t = clamp(t)
    c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


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
    if r <= l or b <= t:
        return
    if (l, t, r, b) != (0, 0, img.width, img.height):
        img = img.crop((l, t, r, b))
    frame.alpha_composite(img, (x + l, y + t))


def scaled(img, s):
    if abs(s - 1) < 0.003:
        return img
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)


def comp_center(frame, img, cx, cy, s=1.0, alpha=1.0):
    img = scaled(img, s)
    comp(frame, img, (cx - img.width / 2, cy - img.height / 2), alpha)


def shadow(img, blur=18, alpha=60, dy=10):
    pad = blur * 2
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    m = img.getchannel("A").point(lambda v: int(v * alpha / 255))
    out.paste((20, 30, 60, 255), (pad, pad + dy), m)
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out


@lru_cache(None)
def text_img(text, weight, size, color):
    f = font(weight, size)
    bb = f.getbbox(text)
    img = Image.new("RGBA", (int(f.getlength(text)) + 4, int(size * 1.3)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((2, 0), text, font=f, fill=color)
    return img


@lru_cache(None)
def pill(text, size, fg, bg, padx=34, pady=16, weight="Bold"):
    f = font(weight, size)
    tw = int(f.getlength(text))
    h = int(size * 1.15) + 2 * pady
    img = Image.new("RGBA", (tw + 2 * padx, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, h - 1), h // 2, fill=bg)
    bb = f.getbbox(text)
    d.text((padx, h / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=fg)
    return img


# ======================================================================== Bilder
def prepare_photo(name):
    p = HERE / "bilder" / name
    cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    img = Image.open(p).convert("RGB")
    img = ImageOps.fit(img, (int(cw * 1.6), int(ch * 1.6)), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
    return img


@lru_cache(None)
def card_mask():
    cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    m = Image.new("L", (cw * 2, ch * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, cw * 2 - 1, ch * 2 - 1), 80, fill=255)
    return m.resize((cw, ch), Image.LANCZOS)


@lru_cache(None)
def card_shadow():
    cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    base = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))
    base.putalpha(card_mask())
    return shadow(base, 26, 70, 16)


PHOTOS = []
LOGO = None


def load_assets():
    global LOGO
    for sc in C.SZENEN:
        PHOTOS.append(prepare_photo(sc["bild"]))
    logo = Image.open(HERE / "bilder" / "logo.png").convert("RGB")
    logo = logo.resize((int(logo.width * 1.45), int(logo.height * 1.45)), Image.LANCZOS)
    logo = logo.filter(ImageFilter.UnsharpMask(radius=1.5, percent=60))
    # Logo auf weisser abgerundeter Karte
    pad = 10
    card = Image.new("RGBA", (logo.width + 2 * pad, logo.height + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, card.width - 1, card.height - 1), 26, fill=WHITE)
    m = Image.new("L", logo.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, logo.width - 1, logo.height - 1), 20, fill=255)
    card.paste(logo, (pad, pad), m)
    LOGO = shadow(card, 14, 40, 6)


def render_card(i, lt):
    """Foto mit sanftem Ken-Burns-Zoom in abgerundeter Karte."""
    src = PHOTOS[i]
    cw, ch = CARD[2] - CARD[0], CARD[3] - CARD[1]
    u = clamp(lt / C.SZENEN_DAUER)
    z = 1.0 + 0.10 * ease_in_out(u)                 # langsamer Zoom
    dirx = (-1) ** i                                # Pan-Richtung wechselt je Szene
    s = 1.6 / z
    ww, wh = cw * s, ch * s
    cx = src.width / 2 + dirx * (src.width - ww) / 2 * (ease_in_out(u) - 0.5) * 0.9
    cy = src.height / 2 - (src.height - wh) / 2 * 0.25
    box = (cx - ww / 2, cy - wh / 2)
    img = src.transform((cw, ch), Image.AFFINE, (s, 0, box[0], 0, s, box[1]), Image.BICUBIC)
    img = img.convert("RGBA")
    img.putalpha(card_mask())
    return img


# ======================================================================== Hintergrund
def tod_color(minutes):
    """Hintergrund wandert von Morgen (warm) ueber Tag (hell) zu Abend (lila)."""
    keys = [(360, (255, 241, 222)), (480, (246, 247, 243)), (1020, (244, 243, 238)),
            (1110, (238, 233, 247))]
    if minutes <= keys[0][0]:
        return keys[0][1]
    for (m0, c0), (m1, c1) in zip(keys, keys[1:]):
        if minutes <= m1:
            k = (minutes - m0) / (m1 - m0)
            return tuple(int(c0[j] + (c1[j] - c0[j]) * k) for j in range(3))
    return keys[-1][1]


def blob(r, color):
    img = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, 2 * r, 2 * r), fill=color)
    return img.filter(ImageFilter.GaussianBlur(30))


BLOBS = [(blob(360, (*ORANGE, 26)), 0.0, (-200, 300)),
         (blob(300, (*NAVY, 14)), 2.0, (700, 900)),
         (blob(260, (*GREEN, 20)), 4.0, (-60, 1450))]


def background(t, minutes):
    frame = Image.new("RGBA", (W, H), (*tod_color(minutes), 255))
    for b, ph, (bx, by) in BLOBS:
        comp(frame, b, (bx + 50 * math.sin(t * 0.3 + ph), by + 60 * math.cos(t * 0.25 + ph)))
    return frame


# ======================================================================== Uhr
def to_min(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def draw_clock(frame, cx, cy, r, minutes, alpha=1.0):
    S = 3
    size = 2 * r + 40
    img = Image.new("RGBA", (size * S, size * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size * S / 2
    R = r * S
    d.ellipse((c - R, c - R, c + R, c + R), fill=WHITE, outline=NAVY, width=9 * S)
    for k in range(12):
        a = math.radians(k * 30)
        r0 = R * (0.78 if k % 3 == 0 else 0.84)
        d.line((c + r0 * math.sin(a), c - r0 * math.cos(a), c + R * 0.9 * math.sin(a),
                c - R * 0.9 * math.cos(a)), fill=NAVY, width=(5 if k % 3 == 0 else 3) * S)
    h_ang = math.radians(((minutes / 60) % 12) * 30)
    m_ang = math.radians((minutes % 60) * 6)
    d.line((c, c, c + R * 0.5 * math.sin(h_ang), c - R * 0.5 * math.cos(h_ang)), fill=NAVY, width=11 * S)
    d.line((c, c, c + R * 0.74 * math.sin(m_ang), c - R * 0.74 * math.cos(m_ang)), fill=ORANGE, width=7 * S)
    d.ellipse((c - 9 * S, c - 9 * S, c + 9 * S, c + 9 * S), fill=NAVY)
    img = img.resize((size, size), Image.LANCZOS)
    comp(frame, shadow(img, 12, 40, 6), (cx - size / 2 - 24, cy - size / 2 - 24), alpha)


def scene_minutes(i, lt):
    """Uhrzeit fuer die Zeiger: dreht beim Szenenwechsel zur neuen Zeit."""
    target = to_min(C.SZENEN[i]["zeit"])
    prev = to_min(C.SZENEN[i - 1]["zeit"]) if i > 0 else target - 30
    return prev + (target - prev) * ease_in_out(lt / 0.9)


def draw_time_block(frame, i, lt, a_scene):
    sc = C.SZENEN[i]
    draw_clock(frame, 205, CLOCK_Y + 95, 88, scene_minutes(i, lt), a_scene)
    tin = ease_out((lt - 0.15) / 0.5)
    a = tin * a_scene
    big = text_img(sc["zeit"], "ExtraBold", 132, NAVY)
    uhr = text_img("Uhr", "Bold", 60, NAVY)
    x0 = 345
    comp(frame, big, (x0, CLOCK_Y - 8 + 30 * (1 - tin)), a)
    comp(frame, uhr, (x0 + big.width + 14, CLOCK_Y + 58 + 30 * (1 - tin)), a)
    hint = text_img(f"= {sc['sprechweise']}", "SemiBold", 44, ORANGE)
    comp(frame, hint, (x0 + 4, CLOCK_Y + 150 + 20 * (1 - ease_out((lt - 0.45) / 0.5))),
         ease_out((lt - 0.45) / 0.5) * a_scene)


# ======================================================================== Text
def parse_marked(text):
    """'Ich *stehe* um ... *auf*.' -> Liste von Woertern mit Teilen (text, hervorgehoben)."""
    words = []
    for w in text.split():
        parts = []
        pos = 0
        for m in re.finditer(r"\*([^*]+)\*", w):
            if m.start() > pos:
                parts.append((w[pos:m.start()], False))
            parts.append((m.group(1), True))
            pos = m.end()
        if pos < len(w):
            parts.append((w[pos:], False))
        words.append(parts)
    return words


@lru_cache(None)
def sentence_img(text, size=70, spoken=999, max_w=W - 140):
    f = font("ExtraBold", size)
    words = parse_marked(text)
    space = f.getlength(" ")
    widths = [sum(f.getlength(t) for t, _ in parts) for parts in words]

    def line_w(ws):
        return sum(ws) + space * (len(ws) - 1)

    if line_w(widths) <= max_w:
        lines = [(words, line_w(widths))]
    else:  # zwei moeglichst gleich lange Zeilen
        k = min(range(1, len(words)), key=lambda k: max(line_w(widths[:k]), line_w(widths[k:])))
        lines = [(words[:k], line_w(widths[:k])), (words[k:], line_w(widths[k:]))]
    lh = int(size * 1.3)
    img = Image.new("RGBA", (W, lh * len(lines) + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gi = 0
    for li, (line, lw) in enumerate(lines):
        x = (W - lw) / 2
        y = li * lh
        for wi, parts in enumerate(line):
            if wi:
                x += space
            a = 255 if gi < spoken else 85      # noch nicht gesprochene Woerter blass
            for t, hl in parts:
                tw = f.getlength(t)
                if hl:
                    d.rounded_rectangle((x - 4, y + size * 0.98, x + tw + 4, y + size * 0.98 + 9), 4,
                                        fill=(*ORANGE, int(110 * a / 255)))
                d.text((x, y), t, font=f, fill=(*(ORANGE if hl else NAVY), a))
                x += tw
            gi += 1
    return img


@lru_cache(None)
def fitted_sentence(text, spoken=999):
    """Groesste Schrift, bei der der Satz in eine Zeile passt (sonst Umbruch ab 56 px)."""
    plain = text.replace("*", "")
    for size in range(70, 55, -2):
        if font("ExtraBold", size).getlength(plain) <= W - 150:
            return sentence_img(text, size, spoken)
    return sentence_img(text, 56, spoken)


SUBS = []        # Untertitel fuer Einleitung und Abschluss
WORD_TIMES = {}  # szene -> Startzeit jedes Wortes (lokal), fuer die Karaoke-Hervorhebung


def word_weight(w):
    return len(w) + (5 if w[-1] in ".!?" else 2 if w[-1] == "," else 1)


def build_word_times(timings):
    for start, dur, text, scene in timings:
        words = text.split()
        total = sum(word_weight(w) for w in words)
        t = start - (C.INTRO_DAUER + scene * C.SZENEN_DAUER)
        times = []
        for w in words:
            times.append(t)
            t += dur * word_weight(w) / total
        WORD_TIMES[scene] = times


def build_subs(timings):
    for start, dur, text in timings:
        words = text.split()
        # in Bloecke mit hoechstens ~26 Zeichen teilen
        chunks, cur = [], []
        for w in words:
            if cur and len(" ".join(cur + [w])) > 32:
                chunks.append(cur)
                cur = []
            cur.append(w)
        chunks.append(cur)
        weight = lambda w: len(w) + (5 if w[-1] in ".!?" else 2 if w[-1] == "," else 1)
        total = sum(weight(w) for c in chunks for w in c)
        t = start
        for c in chunks:
            ws = []
            for w in c:
                d = dur * weight(w) / total
                ws.append((w, t, t + d))
                t += d
            SUBS.append((ws[0][1], ws[-1][2], ws))


def draw_subs(frame, t):
    for s, e, ws in SUBS:
        if s - 0.05 <= t < e + 0.35:
            f = font("Bold", 48)
            text = " ".join(w for w, _, _ in ws)
            tw = f.getlength(text)
            bw, bh = int(tw + 64), 92
            img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle((0, 0, bw - 1, bh - 1), 24, fill=(*NAVY, 235))
            x = 32
            bb = f.getbbox(text)
            y = bh / 2 - (bb[1] + bb[3]) / 2
            for w, ws_, we in ws:
                spoken = t >= ws_
                d.text((x, y), w, font=f, fill=WHITE if spoken else (255, 255, 255, 120))
                x += f.getlength(w + " ")
            a = clamp((t - s + 0.05) / 0.12) * clamp((e + 0.35 - t) / 0.15)
            comp(frame, img, ((W - bw) / 2, SUB_Y), a)
            return


# ======================================================================== Szenen
def scene_alpha(lt):
    return ease_out(lt / TRANS) * clamp((C.SZENEN_DAUER - lt) / 0.35)


def draw_header(frame, t, show_dots=True, active=-1):
    comp(frame, LOGO, (40, HEADER_Y - 20))
    p = pill(C.NIVEAU, 38, WHITE, NAVY)
    comp(frame, p, (W - 70 - p.width, HEADER_Y + 38))
    if not show_dots:
        return
    d = ImageDraw.Draw(frame, "RGBA")
    gap = 54
    x0 = W / 2 - gap * (N - 1) / 2
    for k in range(N):
        x = x0 + k * gap
        if k == active:
            d.rounded_rectangle((x - 22, DOTS_Y - 9, x + 22, DOTS_Y + 9), 9, fill=ORANGE)
        else:
            r = 8
            d.ellipse((x - r, DOTS_Y - r, x + r, DOTS_Y + r), fill=NAVY if k < active else (*GREY, 90))


def draw_card_layer(frame, i, lt, enter=True):
    """Karte faehrt von rechts herein und nach links hinaus."""
    cw = CARD[2] - CARD[0]
    tin = ease_out(lt / TRANS)
    tout = ease_in_out((lt - (C.SZENEN_DAUER - 0.4)) / 0.4)
    dx = (1 - tin) * (W * 0.9) - tout * (W * 0.9)
    rot_a = (1 - tin) * 0.0
    a = min(tin, 1 - tout * 0.8)
    card = render_card(i, lt)
    sh = card_shadow()
    pad = (sh.width - cw) // 2
    comp(frame, sh, (CARD[0] - pad + dx, CARD[1] - pad + 10), a)
    comp(frame, card, (CARD[0] + dx, CARD[1]), a)
    # Verb-Etikett unten links an der Karte
    lab = pill(C.SZENEN[i]["verb"], 46, WHITE, ORANGE, 36, 18)
    lin = back_out((lt - 0.55) / 0.45)
    if lt > 0.55:
        comp_center(frame, shadow(lab, 10, 50, 6), CARD[0] + 40 + lab.width / 2 + dx, CARD[3] - 8,
                    max(0.01, lin), a)


def draw_scene(frame, t, i, lt):
    sc = C.SZENEN[i]
    a = scene_alpha(lt)
    draw_header(frame, t, True, i)
    draw_time_block(frame, i, lt, clamp((C.SZENEN_DAUER - lt) / 0.35))
    draw_card_layer(frame, i, lt)
    # Lernsatz
    # Karaoke: gesprochene Woerter werden kraeftig, die anderen bleiben blass
    spoken = sum(1 for ws in WORD_TIMES.get(i, []) if lt >= ws)
    s_img = fitted_sentence(sc["satz"], spoken)
    sin_ = back_out((lt - 0.35) / 0.5)
    if lt > 0.35:
        comp_center(frame, s_img, W / 2, SENT_Y + s_img.height / 2, 0.85 + 0.15 * max(0.01, sin_),
                    clamp((lt - 0.35) / 0.25) * clamp((C.SZENEN_DAUER - lt) / 0.3))
    draw_repeat(frame, i, lt)


VOICE_END = {}  # szene -> lokale Zeit, zu der die Stimme fertig ist


def draw_repeat(frame, i, lt):
    start = VOICE_END.get(i, 3.5) + 0.25
    end = C.SZENEN_DAUER - 0.35
    if not (start <= lt < end):
        return
    k = (lt - start) / (end - start)
    a = clamp((lt - start) / 0.2) * clamp((end - lt) / 0.2)
    pulse = 1 + 0.04 * math.sin((lt - start) * 7)
    p = pill(C.NACHSPRECHEN, 44, WHITE, GREEN, 40, 18)
    # kleines Mikrofon-Symbol links im Pill
    icon = Image.new("RGBA", (p.width + 56, p.height), (0, 0, 0, 0))
    icon.alpha_composite(p, (56, 0))
    d = ImageDraw.Draw(icon)
    cy = p.height / 2
    d.ellipse((0, 0, p.height - 1, p.height - 1), fill=GREEN)
    d.rounded_rectangle((p.height / 2 - 9, cy - 22, p.height / 2 + 9, cy + 8), 9, fill=WHITE)
    d.arc((p.height / 2 - 17, cy - 12, p.height / 2 + 17, cy + 18), 0, 180, fill=WHITE, width=4)
    d.line((p.height / 2, cy + 18, p.height / 2, cy + 26), fill=WHITE, width=4)
    comp_center(frame, icon, W / 2, REPEAT_Y + icon.height / 2, pulse, a)
    # Fortschrittsbalken (Zeit zum Nachsprechen)
    bw = 300
    x0 = (W - bw) / 2
    y = REPEAT_Y + icon.height + 18
    dd = ImageDraw.Draw(frame, "RGBA")
    dd.rounded_rectangle((x0, y, x0 + bw, y + 8), 4, fill=(*GREEN, int(60 * a)))
    dd.rounded_rectangle((x0, y, x0 + bw * (1 - k), y + 8), 4, fill=(*GREEN, int(255 * a)))


def draw_intro(frame, t):
    draw_header(frame, t, False)
    a_out = clamp((C.INTRO_DAUER - t) / 0.4)
    # Mini-Vorschau der 7 Bilder als Faecher
    for k in range(N):
        tin = back_out((t - 0.15 - 0.09 * k) / 0.5)
        if t < 0.15 + 0.09 * k:
            continue
        th = PHOTO_THUMBS[k]
        ang = (k - 3) * 7
        img = th.rotate(-ang, expand=True, resample=Image.BICUBIC)
        cx = W / 2 + (k - 3) * 105
        cy = 640 + abs(k - 3) ** 1.6 * 14
        comp_center(frame, img, cx, cy, max(0.01, tin), a_out)
    tin = ease_out((t - 0.6) / 0.6)
    ttl = text_img(C.TITEL, "ExtraBold", 104, NAVY)
    comp(frame, ttl, ((W - ttl.width) / 2, 960 + 40 * (1 - tin)), tin * a_out)
    sub = text_img(C.UNTERTITEL, "SemiBold", 52, ORANGE)
    tin2 = ease_out((t - 0.9) / 0.6)
    comp(frame, sub, ((W - sub.width) / 2, 1110 + 30 * (1 - tin2)), tin2 * a_out)
    # kleine Uhr zum Thema Zeit
    if t > 1.2:
        draw_clock(frame, W / 2, 1290, 62, 360 + (t - 1.2) * 40, ease_out((t - 1.2) / 0.5) * a_out)


def draw_outro(frame, t, lt):
    draw_header(frame, t, False)
    tin = back_out(lt / 0.5)
    ttl = text_img(C.OUTRO_TITEL, "ExtraBold", 80, NAVY)
    comp_center(frame, ttl, W / 2, 330, max(0.01, tin), clamp(lt / 0.2))
    # Wiederholung aller Verben
    box = Image.new("RGBA", (900, 92 * N + 60), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), 40, fill=(*WHITE, 235))
    comp(frame, shadow(box, 22, 50, 12), ((W - 900) / 2 - 44, 430 - 44), ease_out((lt - 0.2) / 0.4))
    for k, sc in enumerate(C.SZENEN):
        rt = ease_out((lt - 0.35 - 0.16 * k) / 0.35)
        if rt <= 0.01:
            continue
        y = 430 + 30 + k * 92
        tm = text_img(sc["zeit"], "Bold", 46, GREY)
        vb = text_img(sc["verb"], "ExtraBold", 54, ORANGE if k % 2 == 0 else NAVY)
        comp(frame, tm, (150 + 30 * (1 - rt), y + 6), rt)
        comp(frame, vb, (340 + 30 * (1 - rt), y), rt)
    cta = pill(C.OUTRO_AUFRUF, 50, WHITE, NAVY, 46, 22)
    ct = back_out((lt - 1.8) / 0.5)
    if lt > 1.8:
        comp_center(frame, shadow(cta, 14, 60, 8), W / 2, 1210, max(0.01, ct))
    if lt > 2.1:
        comp_center(frame, LOGO, W / 2, 1400, 1.25, ease_out((lt - 2.1) / 0.5))


PHOTO_THUMBS = []


def make_thumbs():
    for ph in PHOTOS:
        th = ImageOps.fit(ph, (220, 280), Image.LANCZOS).convert("RGBA")
        frame = Image.new("RGBA", (236, 296), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rounded_rectangle((0, 0, 235, 295), 24, fill=WHITE)
        m = Image.new("L", th.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, 219, 279), 18, fill=255)
        frame.paste(th, (8, 8), m)
        PHOTO_THUMBS.append(shadow(frame, 14, 60, 8))


# ======================================================================== Frame
def minutes_at(t):
    if t < C.INTRO_DAUER:
        return 330
    i = min(N - 1, int((t - C.INTRO_DAUER) // C.SZENEN_DAUER))
    if t >= C.INTRO_DAUER + N * C.SZENEN_DAUER:
        return to_min(C.SZENEN[-1]["zeit"]) + 60
    return scene_minutes(i, t - C.INTRO_DAUER - i * C.SZENEN_DAUER)


def render_frame(fi):
    t = fi / FPS
    frame = background(t, minutes_at(t))
    end_scenes = C.INTRO_DAUER + N * C.SZENEN_DAUER
    if t < C.INTRO_DAUER:
        draw_intro(frame, t)
    elif t < end_scenes:
        k = t - C.INTRO_DAUER
        i = int(k // C.SZENEN_DAUER)
        draw_scene(frame, t, i, k - i * C.SZENEN_DAUER)
    else:
        draw_outro(frame, t, t - end_scenes)
    draw_subs(frame, t)
    a = min(clamp(t / 0.4), clamp((TOTAL - t) / 0.6))
    out = frame.convert("RGB")
    if a < 1:
        out = Image.blend(Image.new("RGB", (W, H), BG), out, a)
    return out.tobytes()


# ======================================================================== Audio
def build_audio(out_wav):
    from common.audio import SR, add, ensure_voice, make_music, speak
    starts = [C.INTRO_DAUER + k * C.SZENEN_DAUER for k in range(N)]
    music = make_music(TOTAL, starts, C.INTRO_DAUER) * C.MUSIK_LAUTSTAERKE
    voice = np.zeros_like(music)
    model = ensure_voice()
    tmp = HERE.parent / ".cache" / "line_ta.wav"
    lines = [(0.5, C.INTRO_SPRECHER, None)]
    lines += [(s + 0.65, sc["satz"].replace("*", ""), k) for k, (s, sc) in enumerate(zip(starts, C.SZENEN))]
    lines += [(starts[-1] + C.SZENEN_DAUER + 0.35, C.OUTRO_SPRECHER, None)]
    timings = []
    for start, text, scene in lines:
        seg = speak(text, tmp, model, C.SPRECHTEMPO)
        nz = np.nonzero(np.abs(seg) > 0.02)[0]
        lead = nz[0] / SR if len(nz) else 0
        end = nz[-1] / SR if len(nz) else len(seg) / SR
        add(voice, 0.95 * seg, start)
        timings.append((start + lead, end - lead, text, scene))
        if scene is not None:
            VOICE_END[scene] = start + end - starts[scene]
            if VOICE_END[scene] > C.SZENEN_DAUER - 1.5:
                print(f"Hinweis: Szene {scene + 1}: wenig Zeit zum Nachsprechen.")
    win = int(0.2 * SR)
    env = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 6, 0, 1)
    env = np.convolve(env, np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
    mix = music * (1 - 0.5 * env) + voice
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.9
    pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return timings


# ======================================================================== Start
def main():
    load_assets()
    make_thumbs()
    cache = HERE.parent / ".cache"
    cache.mkdir(exist_ok=True)
    wav = cache / "tagesablauf.wav"
    print("Erzeuge Tonspur ...", flush=True)
    timings = build_audio(wav)
    build_subs([x[:3] for x in timings if x[3] is None])
    build_word_times([x for x in timings if x[3] is not None])

    if "--preview" in sys.argv:
        out = HERE / "vorschau"
        out.mkdir(exist_ok=True)
        times = [2.5, 6.0, 9.6, 15.5, 31.0, 50.5, 57.5]
        for ts in times:
            Image.frombytes("RGB", (W, H), render_frame(int(ts * FPS))).save(out / f"t{ts:05.1f}.png")
        print("Vorschau in", out)
        return

    out = HERE / "tagesablauf.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav),
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.0:LRA=9",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for k, data in enumerate(pool.imap(render_frame, range(N_FRAMES), chunksize=6)):
            proc.stdin.write(data)
            if k % (FPS * 10) == 0:
                print(f"{k / FPS:5.1f}s / {TOTAL:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("Fertig:", out)


if __name__ == "__main__":
    main()
