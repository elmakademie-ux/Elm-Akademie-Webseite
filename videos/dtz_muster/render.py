"""
DTZ-Muster-E-Mails als Lernvideos (1080x1920, 30 fps, exakt 60 s, MP4) – ELM Akademie.

    python3 render.py 1            -> ausgabe/dtz_aufgabe1_beispiel1.mp4   (Nummer 1–15)
    python3 render.py 1 4 7        -> mehrere Videos
    python3 render.py alle         -> alle 15 Videos
    python3 render.py 1 --preview  -> Vorschaubilder in vorschau/

Die E-Mails stehen in muster.py, Einstellungen oben in dieser Datei (EINSTELLUNGEN).
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import muster as M  # noqa: E402

# ================================================================ EINSTELLUNGEN
NIVEAU = "DTZ · B1"
GESAMTDAUER = 60.0
SPRECHTEMPO = 1.0
MUSIK_LAUTSTAERKE = 0.12
AUSSPRACHE = {"DTZ": "De Te Zett", "E-Mail": "Imeil", "E-Mails": "Imeils", "„": "", "“": ""}
NAVY = (27, 54, 104)
ORANGE = (237, 140, 20)          # Konnektoren
BLUE = (30, 90, 180)             # ELM-Markenfarbe (Rahmen, Beschriftungen)
BLUE_LIGHT = (236, 243, 255)     # heller Hintergrund der Aufgabenkarte
PURPLE = (124, 77, 255)          # Modalverben
BG = (244, 246, 250)
OK = (46, 160, 90)
PCOL = [(0, 150, 136), (33, 150, 243), (233, 30, 99), (255, 152, 0)]   # Farben der 4 Punkte
GREY = (120, 128, 145)
WHITE = (255, 255, 255)

W, H, FPS = 1080, 1920, 30
TOTAL = GESAMTDAUER
N_FRAMES = int(round(TOTAL * FPS))
FONT_DIR = Path("/usr/share/fonts/opentype/inter")

TASK = (60, 330, 1020, 632)
MAIL = (60, 660, 1020, 1600)
TOPBAR, FIELDS = 56, 116
BODY_TOP = MAIL[1] + TOPBAR + FIELDS + 18
BODY_BOTTOM = MAIL[3] - 26
BODY_X = MAIL[0] + 92
BODY_W = MAIL[2] - BODY_X - 36
FS, LH = 32, 44
LANDSCAPE = False
GRAM = None          # Grammatik-Feld (nur Querformat)
SPECIAL = None       # "gintro" / "goutro" fuer das Gesamtvideo


def apply_landscape():
    """Layout fuer 16:9 (1920 x 1080): erst die Aufgabe allein, dann die E-Mail allein
    (oben in der E-Mail die 4 Punkte statt An/Betreff)."""
    global W, H, TASK, MAIL, BODY_TOP, BODY_BOTTOM, BODY_X, BODY_W, LANDSCAPE, FS, LH, FIELDS
    W, H = 1920, 1080
    LANDSCAPE = True
    FS, LH = 36, 50
    FIELDS = 104                       # Zeile mit den 4 Punkten
    TASK = (230, 175, 1690, 1040)
    MAIL = (300, 182, 1620, 1056)
    BODY_TOP = MAIL[1] + TOPBAR + FIELDS + 18
    BODY_BOTTOM = MAIL[3] - 26
    BODY_X = MAIL[0] + 92
    BODY_W = MAIL[2] - BODY_X - 36

E = None   # aktuelle E-Mail
A = None   # zugehoerige Aufgabe
TL = {}
CLIPS = {}
LOGO = None


# ================================================================ Helfer
@lru_cache(None)
def font(weight, size):
    p = FONT_DIR / f"Inter-{weight}.otf"
    return ImageFont.truetype(str(p if p.exists() else FONT_DIR / "Inter-Regular.otf"), size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def back_out(t):
    t = clamp(t)
    return 1 + 2.7 * (t - 1) ** 3 + 1.7 * (t - 1) ** 2


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
        frame.alpha_composite(img.crop((l, t, r, b)) if (l, t, r, b) != (0, 0, img.width, img.height)
                              else img, (x + l, y + t))


def comp_center(frame, img, cx, cy, s=1.0, alpha=1.0):
    if abs(s - 1) > 0.003:
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)
    comp(frame, img, (cx - img.width / 2, cy - img.height / 2), alpha)


def shadow(img, blur=16, alpha=55, dy=8):
    pad = blur * 2
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    out.paste((20, 30, 60, 255), (pad, pad + dy), img.getchannel("A").point(lambda v: int(v * alpha / 255)))
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out


@lru_cache(None)
def pill(text, size, fg, bg, padx=30, pady=12, weight="Bold"):
    f = font(weight, size)
    h = int(size * 1.15) + 2 * pady
    img = Image.new("RGBA", (int(f.getlength(text)) + 2 * padx, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, h - 1), h // 2, fill=bg)
    bb = f.getbbox(text)
    d.text((padx, h / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=fg)
    return img


@lru_cache(None)
def text_img(text, weight, size, color):
    f = font(weight, size)
    img = Image.new("RGBA", (int(f.getlength(text)) + 6, int(size * 1.32)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((3, 0), text, font=f, fill=color)
    return img


def mix(c, a, bg=BG):
    return tuple(int(c[j] * a + bg[j] * (1 - a)) for j in range(3))


def check_icon(r, col, on=True):
    S = 3
    img = Image.new("RGBA", (2 * r * S, 2 * r * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if on:
        d.ellipse((0, 0, 2 * r * S - 1, 2 * r * S - 1), fill=col)
        d.line([(r * S * 0.55, r * S * 1.0), (r * S * 0.88, r * S * 1.35), (r * S * 1.5, r * S * 0.65)],
               fill=WHITE, width=int(r * S * 0.28), joint="curve")
    else:
        d.ellipse((0, 0, 2 * r * S - 1, 2 * r * S - 1), outline=col, width=int(r * S * 0.16))
    return img.resize((2 * r, 2 * r), Image.LANCZOS)


def word_kind(w):
    k = re.sub(r"[^\wäöüÄÖÜß]", "", w).lower()
    if k in M.KONNEKTOREN:
        return "k"
    if k in M.MODALVERBEN:
        return "m"
    return None


KIND_COL = {"k": ORANGE, "m": PURPLE}


# ================================================================ Inhalt aufbereiten
def setup(idx):
    global E, A
    E = M.EMAILS[idx]
    A = M.AUFGABEN[E["aufgabe"]]


def recipient():
    a = E["anrede"].rstrip(",")
    for p in ("Sehr geehrte ", "Sehr geehrter ", "Lieber ", "Liebe "):
        if a.startswith(p):
            a = a[len(p):]
    return "TV aktuell – Leserservice" if a == "Damen und Herren" else a


def intro_text():
    return f"DTZ Schreiben. Aufgabe {E['aufgabe']}: {A['thema']}."


def key_words():
    ks, ms = [], []
    for txt, _ in E["absaetze"]:
        for w in txt.split():
            k = word_kind(w)
            c = re.sub(r"[^\wäöüÄÖÜß]", "", w).lower()
            if k == "k" and c not in ks:
                ks.append(c)
            if k == "m" and c not in ms:
                ms.append(c)
    return ks[:3], ms[:2]


def outro_text():
    ks, ms = key_words()
    words = ks + ms
    return "Wichtige Wörter: " + ", ".join(words) + ". Folge der ELM Akademie!"


def parts():
    """Teile der E-Mail in Tipp-Reihenfolge: (id, text, punkt)."""
    out = [] if LANDSCAPE else [("betreff", E["betreff"], None)]   # 16:9: kein Betreff
    out.append(("anrede", E["anrede"], None))
    for k, (txt, p) in enumerate(E["absaetze"]):
        out.append((f"a{k}", txt, p))
    out.append(("gruss", E["gruss"] + "\n" + E["name"], None))
    return out


# ================================================================ Audio + Zeitplan
def spoken(display):
    s = display
    for a, b in AUSSPRACHE.items():
        s = s.replace(a, b)
    return s.replace("\n", ", ")


def synth(tempo):
    from common.audio import SR, ensure_voice, speak
    model = ensure_voice()
    tmp = HERE.parent / ".cache" / "line_dtzm.wav"
    CLIPS.clear()
    texts = [intro_text(), A["text"], outro_text()] + [t for _, t, _ in parts()]
    for text in texts:
        seg = speak(spoken(text), tmp, model, tempo)
        nz = np.nonzero(np.abs(seg) > 0.02)[0]
        s0, s1 = (nz[0] / SR, nz[-1] / SR) if len(nz) else (0, len(seg) / SR)
        CLIPS[text] = (seg, s0, s1)


def dur(text):
    return CLIPS[text][2] - CLIPS[text][1]


def build_timeline(gap):
    tl = dict(events=[], types={})
    t = 0.4
    it = intro_text()
    tl["intro"] = (t, t + dur(it))
    tl["events"].append((t, it))
    t += dur(it) + 0.5
    tl["intro_end"] = max(t, 3.6)
    t = tl["intro_end"] + 0.5
    tl["task"] = (t, t + dur(A["text"]))
    tl["events"].append((t, A["text"]))
    t += dur(A["text"]) + gap + 0.3
    tl["mail_in"] = t - 0.5
    for pid, txt, _ in parts():
        tl["events"].append((t, txt))
        tl["types"][pid] = (t, t + dur(txt))
        t += dur(txt) + gap
    tl["outro_start"] = t + 0.4
    ot = outro_text()
    tl["outro"] = (tl["outro_start"] + 0.5, tl["outro_start"] + 0.5 + dur(ot))
    tl["events"].append((tl["outro"][0], ot))
    return tl


def plan():
    gap = 0.12
    for tempo in (SPRECHTEMPO, SPRECHTEMPO * 0.94, SPRECHTEMPO * 0.88, SPRECHTEMPO * 0.82):
        synth(tempo)
        if build_timeline(gap)["outro"][1] <= TOTAL - 1.0:
            break
        print(f"  zu lang mit Tempo {tempo:.2f} – Stimme wird schneller ...")
    while gap < 2.2 and build_timeline(gap + 0.01)["outro"][1] <= TOTAL - 1.0:
        gap += 0.01
    TL.clear()
    TL.update(build_timeline(gap))
    if TL["outro"][1] > TOTAL - 0.3:
        print("  WARNUNG: Text ist sehr lang, der Abschluss ist knapp.")
    print(f"  Tempo {tempo:.2f}, Pause {gap:.2f} s, Abschluss ab {TL['outro_start']:.1f} s")


def build_audio(out_wav):
    from common.audio import SR, add, make_music
    music = make_music(TOTAL, [TL["task"][0], TL["mail_in"], TL["outro_start"]], TL["intro_end"]) * MUSIK_LAUTSTAERKE
    voice = np.zeros_like(music)
    for t, txt in TL["events"]:
        seg, s0, _ = CLIPS[txt]
        add(voice, 0.95 * seg, t - s0)
    win = int(0.2 * SR)
    env = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 6, 0, 1)
    env = np.convolve(env, np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
    mixd = music * (1 - 0.55 * env) + voice
    mixd = mixd / (np.abs(mixd).max() + 1e-9) * 0.9
    pcm = (np.stack([mixd, mixd], 1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ================================================================ Grafik
def load_logo():
    global LOGO
    logo = Image.open(HERE / "bilder" / "logo.png").convert("RGB")
    logo = logo.resize((int(logo.width * 1.4), int(logo.height * 1.4)), Image.LANCZOS)
    pad = 10
    card = Image.new("RGBA", (logo.width + 2 * pad, logo.height + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 24, fill=WHITE)
    m = Image.new("L", logo.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, logo.width - 1, logo.height - 1), 18, fill=255)
    card.paste(logo, (pad, pad), m)
    LOGO = shadow(card, 12, 40, 5)


def blob(r, color):
    img = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, 2 * r, 2 * r), fill=color)
    return img.filter(ImageFilter.GaussianBlur(30))


BLOBS = [(blob(360, (*BLUE, 20)), 0.0, (-220, 260)), (blob(320, (*NAVY, 14)), 2.0, (720, 900)),
         (blob(260, (*PURPLE, 14)), 4.0, (-60, 1450))]


def background(t):
    frame = Image.new("RGBA", (W, H), (*BG, 255))
    for b, ph, (bx, by) in BLOBS:
        comp(frame, b, (bx + 50 * math.sin(t * 0.3 + ph), by + 60 * math.cos(t * 0.25 + ph)))
    return frame


@lru_cache(None)
def legend():
    a = pill("Konnektor", 28, WHITE, ORANGE, 20, 7)
    b = pill("Modalverb", 28, WHITE, PURPLE, 20, 7)
    img = Image.new("RGBA", (a.width + b.width + 16, a.height), (0, 0, 0, 0))
    img.alpha_composite(a, (0, 0))
    img.alpha_composite(b, (a.width + 16, 0))
    return img


def draw_header(frame, show_title=True):
    comp(frame, LOGO, (36, 26 if not LANDSCAPE else 8))
    p = pill(NIVEAU, 36, WHITE, NAVY)
    comp(frame, p, (W - 64 - p.width, 78 if not LANDSCAPE else 48))
    if not show_title:
        return
    if LANDSCAPE:
        sub = text_img(f"Aufgabe {E['aufgabe']} · Beispiel {E['beispiel']}", "Bold", 30, BLUE)
        comp_center(frame, sub, W / 2, 52)
        ttl = text_img(A["thema"], "ExtraBold", 54, NAVY)
        comp_center(frame, ttl, W / 2, 104, min(1.0, 1100 / ttl.width))
        return
    sub = text_img(f"Aufgabe {E['aufgabe']} · Beispiel {E['beispiel']}", "Bold", 32, BLUE)
    comp_center(frame, sub, W / 2, 222)
    ttl = text_img(A["thema"], "ExtraBold", 54, NAVY)
    s = min(1.0, (W - 120) / ttl.width)
    comp_center(frame, ttl, W / 2, 274, s)


def wrap_words(text, f, max_w):
    lines, cur = [], []
    for w in text.split():
        test = " ".join(cur + [w])
        if cur and f.getlength(test) > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    return lines


# ---------------------------------------------------------------- Aufgabenkarte
@lru_cache(None)
def task_lines():
    x0, _, x1, _ = TASK
    return wrap_words(A["text"], font("Medium", 29), x1 - x0 - 56)


@lru_cache(None)
def task_bg():
    x0, y0, x1, y1 = TASK
    img = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), 28, fill=BLUE_LIGHT, outline=BLUE, width=4)
    d.text((28, 16), "AUFGABE", font=font("ExtraBold", 26), fill=BLUE)
    return shadow(img, 14, 35, 6)


@lru_cache(None)
def chip_img(k, cw, level):
    col = PCOL[k]
    img = Image.new("RGBA", (cw + 1, 47), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, cw, 46), 23, fill=(*col, 36 + 18 * level), outline=(*col, 255), width=3)
    num = pill(str(k + 1), 24, WHITE, col, 11, 4, "ExtraBold")
    img.alpha_composite(num, (6, int(23 - num.height / 2)))
    d.text((48, 8), A["punkte"][k], font=font("Bold", 27), fill=NAVY)
    return img


def point_done_time(k):
    for pid, _, p in parts():
        if p == k:
            return TL["types"][pid][1]
    return None


def draw_task(frame, t):
    x0, y0, x1, y1 = TASK
    comp(frame, task_bg(), (x0 - 28, y0 - 22))
    lg = legend()
    comp(frame, lg, (x1 - 22 - lg.width, y0 + 10))
    d = ImageDraw.Draw(frame, "RGBA")
    f = font("Medium", 29)
    s, e = TL["task"]
    words = [w for line in task_lines() for w in line]
    n_spoken = int(len(words) * clamp((t - s) / max(0.5, e - s) * 1.05)) if t < e + 0.1 else len(words)
    gi = 0
    for li, line in enumerate(task_lines()):
        x = x0 + 28
        for w in line:
            col = NAVY if gi < n_spoken or t >= e else mix(NAVY, 0.45, BLUE_LIGHT)
            d.text((x, y0 + 52 + li * 37), w, font=f, fill=col)
            x += f.getlength(w + " ")
            gi += 1
    cw = int((x1 - x0 - 56 - 18) / 2)
    for k in range(4):
        cx = x0 + 28 + (k % 2) * (cw + 18)
        cy = y0 + 52 + len(task_lines()) * 37 + 14 + (k // 2) * 54
        level = 0
        if s + 0.5 <= t <= e + 1.5:   # beim Vorlesen der Aufgabe nacheinander hervorheben
            level = round(8 * clamp(1 - abs(t - (s + 0.8 + 0.5 * k + (e - s) * 0.5)) / 0.5))
        comp(frame, chip_img(k, cw, level), (cx, cy))
        dt = point_done_time(k)
        if dt is not None and t >= dt:
            comp_center(frame, check_icon(16, OK, True), cx + cw - 26, cy + 23,
                        max(0.01, back_out((t - dt) / 0.35)))
        else:
            comp_center(frame, check_icon(16, GREY, False), cx + cw - 26, cy + 23)


# ---------------------------------------------------------------- E-Mail-Fenster
@lru_cache(None)
def mail_base():
    x0, y0, x1, y1 = MAIL
    w, h = x1 - x0, y1 - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, fill=WHITE)
    d.rounded_rectangle((0, 0, w - 1, TOPBAR), 30, fill=(232, 236, 243))
    d.rectangle((0, 30, w - 1, TOPBAR), fill=(232, 236, 243))
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((24 + k * 30, 19, 42 + k * 30, 37), fill=c)
    d.text((w / 2, 28), "Neue E-Mail", font=font("SemiBold", 26), fill=GREY, anchor="mm")
    d.rounded_rectangle((0, 0, w - 1, h - 1), 30, outline=BLUE, width=5)
    if LANDSCAPE:   # statt An/Betreff: Zeile fuer die 4 Punkte (wird live gezeichnet)
        d.line((30, TOPBAR + FIELDS, w - 30, TOPBAR + FIELDS), fill=(225, 229, 236), width=2)
        return shadow(img, 22, 55, 12)
    lf = font("SemiBold", 28)
    d.text((30, TOPBAR + 14), "An:", font=lf, fill=GREY)
    d.text((150, TOPBAR + 14), recipient(), font=font("Medium", 28), fill=NAVY)
    d.line((30, TOPBAR + 58, w - 30, TOPBAR + 58), fill=(225, 229, 236), width=2)
    d.text((30, TOPBAR + 70), "Betreff:", font=lf, fill=GREY)
    d.line((30, TOPBAR + FIELDS, w - 30, TOPBAR + FIELDS), fill=(225, 229, 236), width=2)
    return shadow(img, 22, 55, 12)


@lru_cache(None)
def body_layout():
    """Woerter mit Position: (teil, wort, x, y, zeichen_offset, punkt, erstes_wort_im_absatz, gewicht)."""
    out, y = [], 0
    f = font("Medium", FS)
    for pid, txt, p in [q for q in parts() if q[0] != "betreff"]:
        weight = "SemiBold" if pid in ("anrede", "gruss") else "Medium"
        off = 0
        first = True
        for para in txt.split("\n"):
            for line in wrap_words(para, f, BODY_W):
                x = 0
                for w in line:
                    out.append((pid, w, x, y, off, p, first, weight))
                    first = False
                    x += font(weight, FS).getlength(w + " ")
                    off += len(w) + 1
                y += LH
        y += 14 if pid != "anrede" else 10
    return out


def revealed(pid, t):
    if pid not in TL["types"]:
        return 0
    s, e = TL["types"][pid]
    n = len(dict((p[0], p[1]) for p in parts())[pid].replace("\n", " "))
    return int((n + 1) * clamp((t - s) / max(0.3, (e - s) * 0.95)))


def cursor_bottom(t):
    lay = body_layout()
    yb = 0
    for pid, w, x, y, off, p, first, weight in lay:
        if revealed(pid, t) > off:
            yb = y + LH
    return yb


def scroll_at(t):
    vis = BODY_BOTTOM - BODY_TOP
    vals = []
    for k in range(6):          # weich nachziehen
        tt = t - k * 0.08
        vals.append(max(0, cursor_bottom(tt) - vis + 40))
    return sum(vals) / len(vals)


def draw_mail(frame, t, slide):
    x0, y0, x1, y1 = MAIL
    dy = (1 - slide) * 260
    comp(frame, mail_base(), (x0 - 44, y0 - 44 + dy), slide)
    if slide < 0.999:
        return
    d = ImageDraw.Draw(frame, "RGBA")
    cursor = None
    if LANDSCAPE:
        draw_point_row(frame, t)
    n = revealed("betreff", t)
    if n:
        txt = E["betreff"][:n]
        bf = font("Bold", 28)
        d.text((x0 + 175, y0 + TOPBAR + 70), txt, font=bf, fill=NAVY)
        if n <= len(E["betreff"]):
            cursor = (x0 + 175 + bf.getlength(txt) + 3, y0 + TOPBAR + 72, 32)
    # Text in eigener Ebene (fuer Scrollen/Abschneiden)
    vis = BODY_BOTTOM - BODY_TOP
    layer = Image.new("RGBA", (x1 - x0, vis), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    sc = scroll_at(t)
    bx = BODY_X - x0
    for pid, w, x, y, off, p, first, weight in body_layout():
        n = revealed(pid, t) - off
        if n <= 0:
            continue
        yy = y - sc
        if yy < -LH or yy > vis:
            continue
        txt = w[:n]
        kind = word_kind(w) if n >= len(w) else None
        if kind:
            ld.text((bx + x, yy), txt, font=font("Bold", FS), fill=KIND_COL[kind])
            wd = font("Bold", FS).getlength(re.sub(r"[.,!?:]+$", "", txt))
            ld.rounded_rectangle((bx + x, yy + FS + 6, bx + x + wd, yy + FS + 10), 2, fill=KIND_COL[kind])
        else:
            ld.text((bx + x, yy), txt, font=font(weight, FS), fill=NAVY)
        if p is not None:
            ld.rectangle((bx - 18, yy + 4, bx - 13, yy + LH - 2), fill=PCOL[p])
            if first:
                num = pill(str(p + 1), 22, WHITE, PCOL[p], 10, 3, "ExtraBold")
                layer.alpha_composite(num, (int(bx - 62), int(yy + 4)))
        if n <= len(w) and revealed(pid, t) < (revealed(pid, 1e9)):
            cursor = (BODY_X + x + font(weight, FS).getlength(txt) + 2, BODY_TOP + yy + 4, 36)
    # weiche Kanten oben/unten
    if sc > 1:   # oben weich ausblenden, wenn gescrollt wird
        arr = np.asarray(layer).copy()
        fade = 34
        arr[:fade, :, 3] = (arr[:fade, :, 3] * np.linspace(0, 1, fade)[:, None]).astype(np.uint8)
        layer = Image.fromarray(arr, "RGBA")
    comp(frame, layer, (x0, BODY_TOP))
    if cursor and int(t * 3) % 2 == 0:
        cx, cy, ch = cursor
        if BODY_TOP - 40 < cy < BODY_BOTTOM:
            d.rectangle((cx, cy, cx + 3, cy + ch), fill=BLUE)


# ---------------------------------------------------------------- Untertitel
def caption(frame, text, s, e, t, y):
    if not (s - 0.1 <= t < e + 0.6):
        return
    words = text.split()
    wt = [len(w) + 1 for w in words]
    n = sum(1 for k in range(len(words)) if t >= s + (e - s) * sum(wt[:k]) / sum(wt))
    f = font("Bold", 46)
    sp = f.getlength(" ")
    widths = [f.getlength(w) for w in words]

    def lw(ws):
        return sum(ws) + sp * (len(ws) - 1)
    lines = [(0, len(words))]
    if lw(widths) > W - 200:
        k = min(range(1, len(words)), key=lambda k: max(lw(widths[:k]), lw(widths[k:])))
        lines = [(0, k), (k, len(words))]
    bw = int(max(lw(widths[a:b]) for a, b in lines)) + 64
    bh = 60 * len(lines) + 30
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), 26, fill=(*NAVY, 238))
    for li, (a, b) in enumerate(lines):
        x = (bw - lw(widths[a:b])) / 2
        for k in range(a, b):
            d.text((x, 14 + li * 60), words[k], font=f, fill=WHITE if k < n else mix(WHITE, 0.45, NAVY))
            x += widths[k] + sp
    comp(frame, img, ((W - bw) / 2, y), clamp((t - s + 0.1) / 0.15) * clamp((e + 0.6 - t) / 0.2))


# ================================================================ Szenen
def envelope():
    S = 3
    env = Image.new("RGBA", (340 * S, 236 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(env)
    d.rounded_rectangle((0, 0, 340 * S - 1, 236 * S - 1), 26 * S, fill=WHITE, outline=NAVY, width=8 * S)
    d.line([(14 * S, 22 * S), (170 * S, 140 * S), (326 * S, 22 * S)], fill=NAVY, width=8 * S, joint="curve")
    return shadow(env.resize((340, 236), Image.LANCZOS), 18, 60, 10)


def draw_intro_landscape(frame, t):
    draw_header(frame, False)
    a_out = clamp((TL["intro_end"] - t) / 0.3)
    bob = 10 * math.sin(t * 2.4)
    comp_center(frame, envelope(), 560, 470 + bob, 0.75 + 0.25 * back_out(t / 0.6), clamp(t / 0.25) * a_out)
    lab = pill(f"Aufgabe {E['aufgabe']} · Beispiel {E['beispiel']}", 44, WHITE, BLUE, 32, 12, "ExtraBold")
    comp(frame, lab, (840, 330), a_out * clamp((t - 0.3) / 0.3))
    ttl = text_img(A["thema"], "ExtraBold", 78, NAVY)
    tin = ease_out((t - 0.5) / 0.5)
    s = min(1.0, 1000 / ttl.width)
    comp(frame, scale_img(ttl, s), (840, 425 + 30 * (1 - tin)), tin * a_out)
    comp(frame, scale_img(legend(), 1.3), (845, 545), ease_out((t - 0.9) / 0.4) * a_out)
    caption(frame, intro_text(), *TL["intro"], t, 760)


def scale_img(img, s):
    if abs(s - 1) < 0.003:
        return img
    return img.resize((int(img.width * s), int(img.height * s)), Image.BICUBIC)


def draw_intro(frame, t):
    if LANDSCAPE:
        return draw_intro_landscape(frame, t)
    draw_header(frame, False)
    a_out = clamp((TL["intro_end"] - t) / 0.3)
    S = 3
    env = Image.new("RGBA", (340 * S, 236 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(env)
    d.rounded_rectangle((0, 0, 340 * S - 1, 236 * S - 1), 26 * S, fill=WHITE, outline=NAVY, width=8 * S)
    d.line([(14 * S, 22 * S), (170 * S, 140 * S), (326 * S, 22 * S)], fill=NAVY, width=8 * S, joint="curve")
    env = shadow(env.resize((340, 236), Image.LANCZOS), 18, 60, 10)
    bob = 10 * math.sin(t * 2.4)
    comp_center(frame, env, W / 2, 560 + bob, 0.7 + 0.3 * back_out(t / 0.6), clamp(t / 0.25) * a_out)
    lab = pill(f"Aufgabe {E['aufgabe']} · Beispiel {E['beispiel']}", 40, WHITE, BLUE, 30, 12, "ExtraBold")
    comp_center(frame, lab, W / 2, 790, max(0.01, back_out((t - 0.3) / 0.4)), a_out)
    ttl = text_img(A["thema"], "ExtraBold", 74, NAVY)
    s = min(1.0, (W - 100) / ttl.width)
    tin = ease_out((t - 0.5) / 0.5)
    comp_center(frame, ttl, W / 2, 900 + 30 * (1 - tin), s, tin * a_out)
    lg = legend()
    comp_center(frame, lg, W / 2, 1000, 1.3, ease_out((t - 0.9) / 0.4) * a_out)
    caption(frame, intro_text(), *TL["intro"], t, 1120)


GRAM_EVENTS = []   # (wort, art, zeit_getippt)


def build_gram_events():
    GRAM_EVENTS.clear()
    seen = set()
    for pid, w, x, y, off, p, first, weight in body_layout():
        k = word_kind(w)
        if not k:
            continue
        c = re.sub(r"[^\wäöüÄÖÜß]", "", w).lower()
        if c in seen:
            continue
        seen.add(c)
        s0, e0 = TL["types"][pid]
        n = len(dict((q[0], q[1]) for q in parts())[pid].replace("\n", " "))
        GRAM_EVENTS.append((c, k, s0 + (e0 - s0) * 0.95 * (off + len(w)) / (n + 1)))


@lru_cache(None)
def gram_bg():
    x0, y0, x1, y1 = GRAM
    img = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), 28, fill=WHITE)
    d.text((32, 24), "Grammatik in dieser E-Mail", font=font("ExtraBold", 36), fill=NAVY)
    d.text((32, 96), "Konnektoren", font=font("Bold", 30), fill=ORANGE)
    d.text((32, 296), "Modalverben", font=font("Bold", 30), fill=PURPLE)
    return shadow(img, 18, 45, 8)


def draw_gram(frame, t):
    x0, y0, x1, y1 = GRAM
    comp(frame, gram_bg(), (x0 - 36, y0 - 28))
    for kind, top in (("k", 145), ("m", 345)):
        x, y = x0 + 32, y0 + top
        for w, k, tt in GRAM_EVENTS:
            if k != kind or t < tt:
                continue
            p = pill(w, 40, WHITE, KIND_COL[k], 26, 10, "ExtraBold")
            if x + p.width > x1 - 24:
                x, y = x0 + 32, y + p.height + 14
            comp_center(frame, p, x + p.width / 2, y + p.height / 2, max(0.01, back_out((t - tt) / 0.35)))
            x += p.width + 14


# ---------------------------------------------------------------- 16:9: Aufgabe allein / Punkte-Zeile
def big_task_box():
    """Aufgabenkarte passend zum Inhalt, senkrecht mittig."""
    x0, _, x1, _ = TASK
    h = 120 + len(big_task_lines()) * 66 + 30 + 70 + 2 * 112 + 30
    y0 = int((175 + 1050 - h) / 2)
    return x0, y0, x1, y0 + h


@lru_cache(None)
def big_task_bg():
    x0, y0, x1, y1 = big_task_box()
    img = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), 40, fill=BLUE_LIGHT, outline=BLUE, width=5)
    d.text((56, 44), "AUFGABE", font=font("ExtraBold", 40), fill=BLUE)
    return shadow(img, 22, 45, 10)


@lru_cache(None)
def big_task_lines():
    return wrap_words(A["text"], font("Medium", 50), TASK[2] - TASK[0] - 112)


@lru_cache(None)
def big_chip(k, cw, level):
    col = PCOL[k]
    img = Image.new("RGBA", (cw + 1, 91), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, cw, 90), 45, fill=(*col, 36 + 22 * level), outline=(*col, 255), width=4)
    num = pill(str(k + 1), 40, WHITE, col, 18, 6, "ExtraBold")
    img.alpha_composite(num, (14, int(45 - num.height / 2)))
    d.text((90, 18), A["punkte"][k], font=font("Bold", 44), fill=NAVY)
    return img


def draw_task_alone(frame, t, a):
    x0, y0, x1, y1 = big_task_box()
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    comp(layer, big_task_bg(), (x0 - 44, y0 - 34))
    d = ImageDraw.Draw(layer)
    f = font("Medium", 50)
    s, e = TL["task"]
    lines = big_task_lines()
    words = [w for line in lines for w in line]
    n_spoken = int(len(words) * clamp((t - s) / max(0.5, e - s) * 1.05)) if t < e + 0.1 else len(words)
    gi = 0
    for li, line in enumerate(lines):
        x = x0 + 56
        for w in line:
            col = NAVY if gi < n_spoken else mix(NAVY, 0.4, BLUE_LIGHT)
            d.text((x, y0 + 120 + li * 66), w, font=f, fill=col)
            x += f.getlength(w + " ")
            gi += 1
    ytop = y0 + 120 + len(lines) * 66 + 30
    d.text((x0 + 56, ytop), "Schreiben Sie etwas zu folgenden Punkten:", font=font("SemiBold", 38), fill=GREY)
    cw = int((x1 - x0 - 112 - 30) / 2)
    for k in range(4):
        cx = x0 + 56 + (k % 2) * (cw + 30)
        cy = ytop + 70 + (k // 2) * 112
        level = round(8 * clamp(1 - abs(t - (s + 0.8 + 0.5 * k + (e - s) * 0.5)) / 0.5)) if s <= t <= e + 1.5 else 0
        comp(layer, big_chip(k, cw, level), (cx, cy))
    comp(frame, layer, (0, 0), a)


@lru_cache(None)
def row_chip(k, cw):
    col = PCOL[k]
    img = Image.new("RGBA", (cw + 1, 61), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, cw, 60), 30, fill=(*col, 40), outline=(*col, 255), width=3)
    num = pill(str(k + 1), 28, WHITE, col, 13, 5, "ExtraBold")
    img.alpha_composite(num, (9, int(30 - num.height / 2)))
    f = font("Bold", 30)
    label = A["punkte"][k]
    while f.getlength(label) > cw - 120 and f.size > 20:
        f = font("Bold", f.size - 2)
    d.text((60, 30), label, font=f, fill=NAVY, anchor="lm")
    return img


def draw_point_row(frame, t):
    x0, y0, x1, y1 = MAIL
    gap = 16
    cw = int((x1 - x0 - 60 - 3 * gap) / 4)
    y = y0 + TOPBAR + (FIELDS - 60) / 2
    for k in range(4):
        cx = x0 + 30 + k * (cw + gap)
        comp(frame, row_chip(k, cw), (cx, y))
        dt = point_done_time(k)
        on = dt is not None and t >= dt
        ic = check_icon(19, OK if on else GREY, on)
        comp_center(frame, ic, cx + cw - 32, y + 30, max(0.01, back_out((t - dt) / 0.35)) if on else 1)


def draw_main(frame, t):
    draw_header(frame)
    if LANDSCAPE:
        # Aufgabe allein, dann E-Mail allein (weiche Ueberblendung)
        k = ease_out((t - TL["mail_in"]) / 0.6)
        if k < 0.999:
            draw_task_alone(frame, t, 1 - k)
        if k > 0.01:
            draw_mail(frame, t, k)
        return
    draw_task(frame, t)
    slide = ease_out((t - TL["mail_in"]) / 0.5)
    if slide > 0.01:
        draw_mail(frame, t, slide)


def draw_outro_landscape(frame, t):
    lt = t - TL["outro_start"]
    draw_header(frame, False)
    comp_center(frame, LOGO, W / 2, 230, 1.6 * (0.8 + 0.2 * back_out(lt / 0.6)), clamp(lt / 0.3))
    ttl = text_img("Wichtige Wörter", "ExtraBold", 70, NAVY)
    comp_center(frame, ttl, W / 2, 420, 1, ease_out((lt - 0.2) / 0.4))
    ks, ms = key_words()
    chips = [shadow(pill(w, 56, WHITE, c, 38, 14, "ExtraBold"), 12, 45, 6)
             for w, c in [(w, ORANGE) for w in ks] + [(w, PURPLE) for w in ms]]
    total = sum(c.width for c in chips) - 30 * (len(chips) - 1)
    x = W / 2 - total / 2
    for k, c in enumerate(chips):
        st = 0.5 + 0.25 * k
        if lt > st:
            comp_center(frame, c, x + c.width / 2, 545, max(0.01, back_out((lt - st) / 0.4)))
        x += c.width - 30
    p = pill("Folge der ELM Akademie", 46, WHITE, NAVY, 40, 16, "ExtraBold")
    comp_center(frame, shadow(p, 14, 50, 8), W / 2, 690, max(0.01, back_out((lt - 1.6) / 0.5)),
                clamp((lt - 1.6) / 0.2))
    caption(frame, outro_text(), *TL["outro"], t, 820)


def draw_outro(frame, t):
    if LANDSCAPE:
        return draw_outro_landscape(frame, t)
    lt = t - TL["outro_start"]
    draw_header(frame, False)
    comp_center(frame, LOGO, W / 2, 470, 2.0 * (0.8 + 0.2 * back_out(lt / 0.6)), clamp(lt / 0.3))
    ttl = text_img("Wichtige Wörter", "ExtraBold", 72, NAVY)
    comp_center(frame, ttl, W / 2, 720, 1, ease_out((lt - 0.2) / 0.4))
    ks, ms = key_words()
    chips = [(w, ORANGE) for w in ks] + [(w, PURPLE) for w in ms]
    y = 850
    for k, (w, col) in enumerate(chips):
        p = shadow(pill(w, 58, WHITE, col, 40, 16, "ExtraBold"), 12, 45, 6)
        st = 0.5 + 0.25 * k
        if lt > st:
            alone = k == len(chips) - 1 and len(chips) % 2 == 1
            cx = W / 2 if alone else W / 2 + ((k % 2) * 2 - 1) * 200
            comp_center(frame, p, cx, y + (k // 2) * 140, max(0.01, back_out((lt - st) / 0.4)))
    p = pill("Folge der ELM Akademie", 48, WHITE, NAVY, 40, 18, "ExtraBold")
    comp_center(frame, shadow(p, 14, 50, 8), W / 2, 1290, max(0.01, back_out((lt - 1.6) / 0.5)),
                clamp((lt - 1.6) / 0.2))
    caption(frame, outro_text(), *TL["outro"], t, 1400)


GINTRO = dict(text="DTZ Schreiben: 15 Muster-E-Mails auf Niveau B1. Hör zu, lies mit und lerne die Satzmuster.",
              dauer=10.0)
GOUTRO = dict(text="Lerntipp: Lerne nicht alle E-Mails auswendig. Lerne die Satzmuster und benutze sie "
                   "selbst. Folge der ELM Akademie!", dauer=14.0)
GRAMMATIK = [("weil", "Ich schreibe Ihnen, weil mein Auto kaputt ist."),
             ("dass", "Ich hoffe, dass Sie gesund werden."),
             ("wenn", "Wenn du Zeit hast, komm bitte vorbei."),
             ("obwohl", "Obwohl die Wohnung klein ist, gefällt sie mir."),
             ("damit", "Ich lerne Deutsch, damit ich eine Arbeit finde."),
             ("deshalb", "Mein Auto ist kaputt. Deshalb brauche ich Hilfe."),
             ("außerdem", "Außerdem möchte ich Sie einladen."),
             ("aber", "Die Wohnung ist klein, aber schön.")]
MODAL_BSP = [("können", "Können Sie mir bitte helfen?"), ("müssen", "Ich muss am Samstag arbeiten."),
             ("möchten", "Ich möchte einen Termin machen."), ("sollen", "Sie sollen sich gut ausruhen.")]


def draw_special(frame, t):
    s, e, text = TL["say"]
    if SPECIAL == "gintro":
        comp(frame, LOGO, (36, 8))
        comp_center(frame, envelope(), W / 2, 250 + 10 * math.sin(t * 2.4), 0.8 + 0.2 * back_out(t / 0.6))
        ttl = text_img("15 Muster-E-Mails", "ExtraBold", 96, NAVY)
        comp_center(frame, ttl, W / 2, 450, 1, ease_out((t - 0.3) / 0.5))
        sub = pill("DTZ Schreiben · Niveau B1.1", 44, WHITE, BLUE, 34, 12, "ExtraBold")
        comp_center(frame, sub, W / 2, 560, max(0.01, back_out((t - 0.6) / 0.4)))
        for k, (n, a) in enumerate(M.AUFGABEN.items()):
            st = 1.2 + 0.35 * k
            if t > st:
                p = shadow(pill(f"{n}  {a['thema']}", 30, NAVY, WHITE, 26, 12, "Bold"), 10, 40, 5)
                col, row = k % 3, k // 3
                n_in_row = 3 if row == 0 else 2
                x = W / 2 + (col - (n_in_row - 1) / 2) * 590
                comp_center(frame, p, x, 680 + row * 90, max(0.01, back_out((t - st) / 0.4)))
        caption(frame, text, s, e, t, 880)
    else:
        comp(frame, LOGO, (36, 8))
        ttl = text_img("Satzmuster für den DTZ", "ExtraBold", 64, NAVY)
        comp_center(frame, ttl, W / 2, 95, 1, ease_out(t / 0.4))
        items = [(w, b, ORANGE) for w, b in GRAMMATIK] + [(w, b, PURPLE) for w, b in MODAL_BSP]
        for k, (w, bsp, col) in enumerate(items):
            st = 0.3 + 0.22 * k
            if t < st:
                continue
            a = ease_out((t - st) / 0.3)
            colx, row = (0, k) if k < 6 else (1, k - 6)
            x = 90 + colx * 900
            y = 190 + row * 88
            p = pill(w, 32, WHITE, col, 20, 8, "ExtraBold")
            comp(frame, p, (x, y), a)
            comp(frame, text_img(bsp, "Medium", 29, NAVY), (x + 222, y + 8), a)
        lt = text_img("Lerntipp", "ExtraBold", 40, OK)
        comp(frame, lt, (90, 715), ease_out((t - 3.2) / 0.4))
        caption(frame, text, s, e, t, 820)
        if t > 9.5:
            p = pill("Folge der ELM Akademie", 46, WHITE, NAVY, 40, 16, "ExtraBold")
            comp_center(frame, shadow(p, 14, 50, 8), W / 2, 1000, max(0.01, back_out((t - 9.5) / 0.5)))


def render_frame(fi):
    t = fi / FPS
    frame = background(t)
    if SPECIAL:
        draw_special(frame, t)
    elif t < TL["intro_end"]:
        draw_intro(frame, t)
    elif t < TL["outro_start"]:
        draw_main(frame, t)
    else:
        draw_outro(frame, t)
    out = frame.convert("RGB")
    a = min(clamp(t / 0.35), clamp((TOTAL - t) / 0.6))
    if a < 1:
        out = Image.blend(Image.new("RGB", (W, H), BG), out, a)
    return out.tobytes()


# ================================================================ Start
def clear_caches():
    for fn in (task_lines, task_bg, chip_img, mail_base, body_layout, gram_bg, big_task_bg, big_task_lines,
               big_chip, row_chip):
        fn.cache_clear()


def encode(out, wav, total):
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav),
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.0:LRA=9",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-t", f"{total:.3f}", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for data in pool.imap(render_frame, range(int(round(total * FPS))), chunksize=6):
            proc.stdin.write(data)
    proc.stdin.close()
    proc.wait()


def render_special(kind, out):
    """Einleitung/Abschluss des Gesamtvideos."""
    global SPECIAL, TOTAL
    from common.audio import SR, add, ensure_voice, make_music, speak
    SPECIAL = kind
    cfg = GINTRO if kind == "gintro" else GOUTRO
    TOTAL = cfg["dauer"]
    tmp = HERE.parent / ".cache" / "line_dtzm.wav"
    seg = speak(spoken(cfg["text"]), tmp, ensure_voice(), SPRECHTEMPO)
    nz = np.nonzero(np.abs(seg) > 0.02)[0]
    s0, s1 = nz[0] / SR, nz[-1] / SR
    start = 0.8 if kind == "gintro" else 3.6
    TL.clear()
    TL["say"] = (start, start + s1 - s0, cfg["text"])
    music = make_music(TOTAL, [], TOTAL + 1) * MUSIK_LAUTSTAERKE
    voice = np.zeros_like(music)
    add(voice, 0.95 * seg, start - s0)
    mixd = music * 0.6 + voice
    mixd = mixd / (np.abs(mixd).max() + 1e-9) * 0.9
    pcm = (np.stack([mixd, mixd], 1) * 32767).astype(np.int16)
    wav = HERE.parent / ".cache" / f"{kind}.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    encode(out, wav, TOTAL)
    SPECIAL = None


def render_gesamt():
    """Alle 15 E-Mails + Einleitung + Abschluss in einem 16:9-Video, mit Kapitelliste."""
    global TOTAL
    outdir = HERE / "ausgabe_16x9"
    outdir.mkdir(exist_ok=True)
    segs = [outdir / "00_einleitung.mp4"]
    if not segs[0].exists():
        print("Einleitung ...", flush=True)
        render_special("gintro", segs[0])
    for idx in range(len(M.EMAILS)):
        e = M.EMAILS[idx]
        f = outdir / f"dtz_aufgabe{e['aufgabe']}_beispiel{e['beispiel']}_16x9.mp4"
        if not f.exists():
            TOTAL = GESAMTDAUER
            render_one(idx, out=f)
        segs.append(f)
    end = outdir / "99_abschluss.mp4"
    if not end.exists():
        print("Abschluss ...", flush=True)
        render_special("goutro", end)
    segs.append(end)
    lst = outdir / "liste.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in segs))
    final = HERE / "dtz_15_muster_emails_16x9.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
    # Kapitel fuer YouTube
    t, lines = 0.0, []
    for p in segs:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  str(p)], capture_output=True, text=True).stdout)
        if p.name.startswith("00"):
            label = "Einleitung"
        elif p.name.startswith("99"):
            label = "Satzmuster & Lerntipp"
        else:
            a, b = re.findall(r"aufgabe(\d)_beispiel(\d)", p.name)[0]
            label = f"Aufgabe {a} · Beispiel {b}: {M.AUFGABEN[int(a)]['thema']}"
        lines.append(f"{int(t // 60)}:{int(t % 60):02d} {label}")
        t += d
    (HERE / "kapitel_youtube.txt").write_text("\n".join(lines) + "\n")
    print("Fertig:", final, flush=True)


def render_one(idx, preview=False, out=None):
    setup(idx)
    clear_caches()
    name = f"dtz_aufgabe{E['aufgabe']}_beispiel{E['beispiel']}"
    print(f"[{idx + 1}/15] {name}: {A['thema']}", flush=True)
    plan()
    wav = HERE.parent / ".cache" / f"{name}.wav"
    build_audio(wav)
    if preview:
        out = HERE / "vorschau"
        out.mkdir(exist_ok=True)
        ts = [2.0, TL["task"][1] - 0.5] + [TL["types"][p][1] for p in ("a1", "gruss")] + [TOTAL - 1.2]
        for x in ts:
            Image.frombytes("RGB", (W, H), render_frame(int(x * FPS))).save(out / f"{name}_t{x:05.1f}.png")
        return
    if out is None:
        outdir = HERE / ("ausgabe_16x9" if LANDSCAPE else "ausgabe")
        outdir.mkdir(exist_ok=True)
        out = outdir / f"{name}{'_16x9' if LANDSCAPE else ''}.mp4"
    encode(out, wav, TOTAL)
    print("  fertig:", out, flush=True)


def main():
    load_logo()
    if "--16x9" in sys.argv:
        apply_landscape()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    preview = "--preview" in sys.argv
    if args == ["gesamt"]:
        if not LANDSCAPE:
            apply_landscape()
        return render_gesamt()
    if args and args[0] in ("gintro", "goutro") and preview:
        global TOTAL
        out = HERE / "vorschau"
        out.mkdir(exist_ok=True)
        render_special_preview = args[0]
        return preview_special(render_special_preview, out)
    if not args or args == ["alle"]:
        nums = list(range(1, len(M.EMAILS) + 1)) if args == ["alle"] else [1]
    else:
        nums = [int(a) for a in args]
    for n in nums:
        render_one(n - 1, preview)


def preview_special(kind, outdir):
    global SPECIAL, TOTAL
    cfg = GINTRO if kind == "gintro" else GOUTRO
    SPECIAL, TOTAL = kind, cfg["dauer"]
    TL.clear()
    TL["say"] = (0.8, cfg["dauer"] - 2, cfg["text"])
    for x in (cfg["dauer"] * 0.5, cfg["dauer"] - 1.5):
        Image.frombytes("RGB", (W, H), render_frame(int(x * FPS))).save(outdir / f"{kind}_t{x:04.1f}.png")


if __name__ == "__main__":
    main()
