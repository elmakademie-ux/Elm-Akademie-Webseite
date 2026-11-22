"""
Rendert das Lernvideo "DTZ Schreiben – Eine E-Mail schreiben" (1080x1920, 30 fps, exakt 60 s).

    python3 render.py             -> dtz_email.mp4
    python3 render.py --preview   -> vorschau/*.png

Texte stehen in inhalt.py. Die Pausen werden automatisch so berechnet, dass das
Video genau GESAMTDAUER Sekunden lang ist.
"""
import math
import os
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
import inhalt as C  # noqa: E402

W, H, FPS = 1080, 1920, 30
TOTAL = C.GESAMTDAUER
N_FRAMES = int(round(TOTAL * FPS))
NAVY, ORANGE, BG, OK = C.FARBE_TEXT, C.FARBE_AKZENT, C.FARBE_HINTERGRUND, C.FARBE_OK
WHITE = (255, 255, 255)
GREY = (120, 128, 145)
PCOL = C.FARBEN_PUNKTE
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
NSTEP = len(C.SCHRITTE)

# Layout
HEADER_Y = 100            # unterhalb der Plattform-Leiste (oben ca. 130 px verdeckt)
DOTS_Y = 372
STEP_Y = 310
TASKB = (60, 430, 1020, 1230)     # grosse Aufgabenkarte (Schritt 1)
CHIP_Y0, CHIP_H = 408, 74         # kompakte Punkte ab Schritt 2
MAIL = (60, 604, 1020, 1345)
CAP_BOTTOM = 1530                 # Untertitel enden vor der unteren Plattform-Leiste


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


def wrap(text, f, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            test = f"{cur} {w}".strip()
            if cur and f.getlength(test) > max_w:
                lines.append(cur)
                cur = w
            else:
                cur = test
        lines.append(cur)
    return lines


def check_icon(r, col, on=True):
    S = 3
    img = Image.new("RGBA", (2 * r * S, 2 * r * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if on:
        d.ellipse((0, 0, 2 * r * S - 1, 2 * r * S - 1), fill=col)
        d.line([(r * S * 0.55, r * S * 1.0), (r * S * 0.88, r * S * 1.35), (r * S * 1.5, r * S * 0.65)],
               fill=WHITE, width=int(r * S * 0.28), joint="curve")
    else:
        d.ellipse((0, 0, 2 * r * S - 1, 2 * r * S - 1), outline=(*col, 160), width=int(r * S * 0.16))
    return img.resize((2 * r, 2 * r), Image.LANCZOS)


# ================================================================ Audio + Zeitplan
CLIPS = {}


def spoken_text(display):
    s = display
    for a, b in C.AUSSPRACHE.items():
        s = s.replace(a, b)
    return s.replace("\n", ", ")


def item_text(kind, val):
    return val if kind == "sagen" else C.EMAIL[val]


def all_items():
    seq = [("intro", k, v) for k, v in C.EINLEITUNG]
    for i, st in enumerate(C.SCHRITTE):
        seq += [(i, k, v) for k, v in st["ablauf"]]
    seq += [("outro", k, v) for k, v in C.ABSCHLUSS]
    return seq


def synth_all(tempo):
    from common.audio import SR, ensure_voice, speak
    model = ensure_voice()
    tmp = HERE.parent / ".cache" / "line_dtz.wav"
    CLIPS.clear()
    for _, k, v in all_items():
        text = item_text(k, v)
        if text in CLIPS:
            continue
        seg = speak(spoken_text(text), tmp, model, tempo)
        nz = np.nonzero(np.abs(seg) > 0.02)[0]
        s0, s1 = (nz[0] / SR, nz[-1] / SR) if len(nz) else (0, len(seg) / SR)
        CLIPS[text] = (seg, s0, s1)


def dur(text):
    return CLIPS[text][2] - CLIPS[text][1]


TL = {}


def build_timeline(gap):
    tl = dict(events=[], steps=[], says=[], types={})
    t = 0.4
    for _, k, v in all_items()[:len(C.EINLEITUNG)]:
        txt = item_text(k, v)
        tl["events"].append((t, txt))
        tl["says"].append(dict(text=txt, start=t, end=t + dur(txt)))
        t += dur(txt) + gap
    tl["intro_end"] = max(t + 0.3, 3.8)
    t = tl["intro_end"]
    for i, st in enumerate(C.SCHRITTE):
        s = dict(start=t)
        t += 0.55
        for k, v in st["ablauf"]:
            txt = item_text(k, v)
            tl["events"].append((t, txt))
            d = dur(txt)
            if k == "sagen":
                tl["says"].append(dict(text=txt, start=t, end=t + d, step=i))
            else:
                tl["types"][v] = (t, t + d)
            t += d + gap
        if i == 0:
            t += 0.8                      # Zeit, die Aufgabe anzusehen
        if i == NSTEP - 1:
            t += 1.0                      # Checkliste
        s["end"] = t + 0.2
        t = s["end"]
        tl["steps"].append(s)
    tl["outro_start"] = t
    for k, v in C.ABSCHLUSS:
        txt = item_text(k, v)
        tl["events"].append((t + 0.5, txt))
        tl["says"].append(dict(text=txt, start=t + 0.5, end=t + 0.5 + dur(txt)))
        tl["outro_speech_end"] = t + 0.5 + dur(txt)
    return tl


def plan():
    for tempo in (C.SPRECHTEMPO, C.SPRECHTEMPO * 0.95, C.SPRECHTEMPO * 0.9, C.SPRECHTEMPO * 0.85):
        synth_all(tempo)
        gap = 0.15
        if build_timeline(gap)["outro_speech_end"] <= TOTAL - 1.2:
            break
        print(f"zu lang mit Tempo {tempo:.2f}, versuche schneller ...")
    while gap < 1.2 and build_timeline(gap + 0.01)["outro_speech_end"] <= TOTAL - 1.2:
        gap += 0.01
    TL.update(build_timeline(gap))
    print(f"Tempo {tempo:.2f}, Pause zwischen Sätzen {gap:.2f} s, Abschluss ab {TL['outro_start']:.1f} s")


def build_audio(out_wav):
    from common.audio import SR, add, make_music
    music = make_music(TOTAL, [s["start"] for s in TL["steps"]], TL["intro_end"]) * C.MUSIK_LAUTSTAERKE
    voice = np.zeros_like(music)
    for t, txt in TL["events"]:
        seg, s0, _ = CLIPS[txt]
        add(voice, 0.95 * seg, t - s0)
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


# ================================================================ Grafik-Bausteine
LOGO = None


def load_logo():
    global LOGO
    logo = Image.open(HERE / "bilder" / "logo.png").convert("RGB")
    logo = logo.resize((int(logo.width * 1.6), int(logo.height * 1.6)), Image.LANCZOS)
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


BLOBS = [(blob(360, (*ORANGE, 22)), 0.0, (-220, 260)), (blob(320, (*NAVY, 14)), 2.0, (720, 900)),
         (blob(260, (*PCOL[1], 14)), 4.0, (-60, 1450))]


def background(t):
    frame = Image.new("RGBA", (W, H), (*BG, 255))
    for b, ph, (bx, by) in BLOBS:
        comp(frame, b, (bx + 50 * math.sin(t * 0.3 + ph), by + 60 * math.cos(t * 0.25 + ph)))
    return frame


def draw_header(frame, active=-1):
    comp(frame, LOGO, (36, HEADER_Y - 22))
    p = pill(C.NIVEAU, 42, WHITE, NAVY, 36, 14)
    comp(frame, p, (W - 48 - p.width, HEADER_Y + 36))
    if active < 0:
        return
    d = ImageDraw.Draw(frame, "RGBA")
    gap = 56
    x0 = W / 2 - gap * (NSTEP - 1) / 2
    for k in range(NSTEP):
        x = x0 + k * gap
        if k == active:
            d.rounded_rectangle((x - 22, DOTS_Y - 8, x + 22, DOTS_Y + 8), 8, fill=ORANGE)
        else:
            a = 0.8 if k < active else 0.25
            d.ellipse((x - 7, DOTS_Y - 7, x + 7, DOTS_Y + 7),
                      fill=tuple(int(NAVY[j] * a + BG[j] * (1 - a)) for j in range(3)))


@lru_cache(None)
def step_title(i):
    num = pill(str(i + 1), 50, WHITE, ORANGE, 24, 8, "ExtraBold")
    ttl = text_img(C.SCHRITTE[i]["titel"], "ExtraBold", 72, NAVY)
    img = Image.new("RGBA", (num.width + 20 + ttl.width, max(num.height, ttl.height)), (0, 0, 0, 0))
    img.alpha_composite(num, (0, (img.height - num.height) // 2))
    img.alpha_composite(ttl, (num.width + 20, (img.height - ttl.height) // 2 - 4))
    return img


# ---------------------------------------------------------------- Aufgabe
@lru_cache(None)
def task_big():
    """Grosse Aufgabenkarte (Schritt 1): Karte + y-Start der Punkte."""
    x0, y0, x1, y1 = TASKB
    w, h = x1 - x0, y1 - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(255, 248, 235), outline=(*ORANGE, 150), width=4)
    d.text((40, 28), "AUFGABE", font=font("ExtraBold", 38), fill=ORANGE)
    f = font("Medium", 48)
    y = 88
    for line in wrap(C.AUFGABE, f, w - 80):
        d.text((40, y), line, font=f, fill=NAVY)
        y += 64
    return img, y + 26


def chip_geom(k, big):
    if big:
        _, y0 = task_big()
        return TASKB[0] + 40, TASKB[1] + y0 + k * 100, TASKB[2] - TASKB[0] - 80, 86
    cw = (MAIL[2] - MAIL[0] - 16) // 2
    return MAIL[0] + (k % 2) * (cw + 16), CHIP_Y0 + (k // 2) * (CHIP_H + 12), cw, CHIP_H


@lru_cache(None)
def chip_bg(k, cw, ch, level):
    col = PCOL[k]
    img = Image.new("RGBA", (cw + 1, ch + 1), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, cw, ch), ch // 2, fill=(*col, int(38 + 14 * level)),
                                          outline=(*col, 255), width=4)
    return img


def draw_chips(frame, t, big, emph=None):
    d = ImageDraw.Draw(frame, "RGBA")
    for k, name in enumerate(C.PUNKTE):
        x, y, cw, ch = chip_geom(k, big)
        done_t = done_time(k)
        done = done_t is not None and t >= done_t
        pulse = clamp(1 - abs(t - (emph + 0.6 * k)) / 0.45) if emph is not None else 0
        col = PCOL[k]
        comp(frame, chip_bg(k, cw, ch, round(pulse * 8)), (x, y))
        num = pill(str(k + 1), int(ch * 0.46), WHITE, col, int(ch * 0.22), 4, "ExtraBold")
        comp(frame, num, (x + ch * 0.2, y + ch / 2 - num.height / 2))
        tf = font("Bold", int(ch * 0.47))
        d.text((x + ch * 0.2 + num.width + 18, y + ch / 2), name, font=tf, fill=NAVY, anchor="lm")
        r = int(ch * 0.32)
        if done:
            comp_center(frame, check_icon(r, OK, True), x + cw - ch * 0.5, y + ch / 2,
                        max(0.01, back_out((t - done_t) / 0.35)))
        else:
            comp_center(frame, check_icon(r, GREY, False), x + cw - ch * 0.5, y + ch / 2)


def draw_task_big(frame, t, emph):
    card, _ = task_big()
    comp(frame, shadow(card, 16, 38, 8), (TASKB[0] - 32, TASKB[1] - 32))
    draw_chips(frame, t, True, emph)


def done_time(k):
    for part, idx in C.PUNKT_ZU_TEIL.items():
        if idx == k and part in TL["types"]:
            return TL["types"][part][1]
    return None


# ---------------------------------------------------------------- E-Mail-Fenster
MF = font("Medium", 41)
LH = 55
BODY_X = 92                              # relativ zum Fenster
BODY_W = MAIL[2] - MAIL[0] - BODY_X - 36
BODY_TOP = 182                           # relativ zum Fenster
VIEW_H = MAIL[3] - MAIL[1] - BODY_TOP - 22
ORDER = ["anrede", None, "p1", "p2", "p3", "p4", None, "schluss", None, "gruss"]


@lru_cache(None)
def mail_layout():
    """Zeilen der E-Mail: (teil, zeilentext, y relativ zum Textbereich, zeichen_offset)."""
    out, y = [], 6
    for part in ORDER:
        if part is None:
            y += 20
            continue
        off = 0
        for line in wrap(C.EMAIL[part], MF, BODY_W):
            out.append((part, line, y, off))
            off += len(line) + 1
            y += LH
        y += 8
    return out


@lru_cache(None)
def mail_base():
    x0, y0, x1, y1 = MAIL
    w, h = x1 - x0, y1 - y0
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 32, fill=WHITE)
    d.rounded_rectangle((0, 0, w - 1, 58), 32, fill=(232, 236, 243))
    d.rectangle((0, 32, w - 1, 58), fill=(232, 236, 243))
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse((26 + k * 32, 20, 46 + k * 32, 40), fill=c)
    d.text((w / 2, 30), "Neue E-Mail", font=font("SemiBold", 28), fill=GREY, anchor="mm")
    lf = font("SemiBold", 32)
    d.text((32, 72), "An:", font=lf, fill=GREY)
    d.text((170, 72), C.EMAIL_AN, font=font("Medium", 32), fill=NAVY)
    d.line((32, 120, w - 32, 120), fill=(225, 229, 236), width=2)
    d.text((32, 130), "Betreff:", font=lf, fill=GREY)
    d.line((32, 178, w - 32, 178), fill=(225, 229, 236), width=2)
    return shadow(img, 22, 55, 12)


def revealed(part, t):
    if part not in TL["types"]:
        return 0
    s, e = TL["types"][part]
    total = len(C.EMAIL[part].replace("\n", " "))
    return int(total * clamp((t - s) / max(0.3, (e - s) * 0.92)))


def scroll_target(t):
    """Wie weit der Text nach oben geschoben werden muss, damit der neueste Text sichtbar bleibt."""
    bottom = 0
    for part, line, y, off in mail_layout():
        if revealed(part, t) - off > 0:
            bottom = y + LH
    return max(0, bottom - VIEW_H + 8)


def scroll(t):
    off = sum(scroll_target(t - k * 0.05) for k in range(8)) / 8     # weich
    last = TL["steps"][-1]["start"]                                  # beim Pruefen wieder nach oben
    return off * (1 - ease_out((t - last) / 0.5)) if t >= last else off


@lru_cache(None)
def mail_dim():
    x0, y0, x1, y1 = MAIL
    img = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), 32, fill=(*BG, 255))
    return img


def draw_mail(frame, t, dim=1.0):
    _draw_mail(frame, t)
    if dim < 0.999:
        comp(frame, mail_dim(), (MAIL[0], MAIL[1]), 1 - dim)


def _draw_mail(frame, t):
    comp(frame, mail_base(), (MAIL[0] - 44, MAIL[1] - 44))
    d = ImageDraw.Draw(frame, "RGBA")
    cursor = None
    n = revealed("betreff", t)
    sf = font("Bold", 34)
    if n:
        txt = C.EMAIL["betreff"][:n]
        d.text((MAIL[0] + 200, MAIL[1] + 130), txt, font=sf, fill=NAVY)
        if n < len(C.EMAIL["betreff"]):
            cursor = (MAIL[0] + 200 + sf.getlength(txt) + 3, MAIL[1] + 134, 38)
    # Text in eigener Ebene (wird nach oben geschoben und oben ausgeblendet)
    body = Image.new("RGBA", (MAIL[2] - MAIL[0], VIEW_H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    off = scroll(t)
    bcur = None
    shown = set()
    for part, line, y, o in mail_layout():
        n = revealed(part, t) - o
        if n <= 0:
            continue
        yy = y - off
        txt = line[:n]
        if part in C.PUNKT_ZU_TEIL:
            pc = PCOL[C.PUNKT_ZU_TEIL[part]]
            if part not in shown:
                shown.add(part)
                num = pill(str(C.PUNKT_ZU_TEIL[part] + 1), 26, WHITE, pc, 12, 4, "ExtraBold")
                body.alpha_composite(num, (30, int(yy + 8))) if yy > -30 else None
            bd.rectangle((BODY_X - 18, yy + 5, BODY_X - 12, yy + LH - 7), fill=(*pc, 255))
        weight = "SemiBold" if part in ("anrede", "gruss") else "Medium"
        bd.text((BODY_X, yy), txt, font=font(weight, 41), fill=NAVY)
        if n < len(line):
            bcur = (BODY_X + font(weight, 41).getlength(txt) + 3, yy + 5, 42)
    if bcur and int(t * 3) % 2 == 0:
        x, y, h = bcur
        bd.rectangle((x, y, x + 4, y + h), fill=(*ORANGE, 255))
    a = np.array(body.getchannel("A"), dtype=np.float32)
    a[:26] *= np.linspace(0, 1, 26)[:, None]          # oben weich ausblenden
    body.putalpha(Image.fromarray(a.astype(np.uint8)))
    comp(frame, body, (MAIL[0], MAIL[1] + BODY_TOP))
    if cursor and int(t * 3) % 2 == 0:
        x, y, h = cursor
        d.rectangle((x, y, x + 4, y + h), fill=(*ORANGE, 255))


@lru_cache(None)
def informal_card():
    p = pill(C.INFORMELL, 38, NAVY, (255, 243, 224), 32, 16, "SemiBold")
    return shadow(p, 10, 40, 5)


# ---------------------------------------------------------------- Untertitel (Karaoke)
def word_starts(say):
    words = say["text"].split()
    wt = [len(w) + (5 if w[-1] in ".!?:" else 2 if w[-1] == "," else 1) for w in words]
    out, t = [], say["start"]
    for k in wt:
        out.append(t)
        t += (say["end"] - say["start"]) * k / sum(wt)
    return out


def split_lines(words, widths, sp, max_w):
    """Gleichmaessig umbrechen: so wenige Zeilen wie moeglich, dann moeglichst gleich lang."""
    def lw(ws):
        return sum(ws) + sp * (len(ws) - 1)

    def greedy(limit):
        lines, cur = [], []
        for k, w_ in enumerate(widths):
            if cur and lw([widths[j] for j in cur] + [w_]) > limit:
                lines.append(cur)
                cur = []
            cur.append(k)
        return lines + [cur]
    n = len(greedy(max_w))
    lo, hi = 1, max_w
    while hi - lo > 4:
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if len(greedy(mid)) <= n else (mid, hi)
    return greedy(hi)


@lru_cache(None)
def caption_img(text, spoken):
    f = font("Bold", 56)
    words = text.split()
    widths = [f.getlength(w) for w in words]
    sp = f.getlength(" ")
    lines = split_lines(words, widths, sp, W - 150)
    lh = 74

    def lw(ix):
        return sum(widths[k] for k in ix) + sp * (len(ix) - 1)
    bw = int(max(lw(ix) for ix in lines)) + 80
    bh = lh * len(lines) + 40
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, bw - 1, bh - 1), 34, fill=(*NAVY, 244))
    for li, ix in enumerate(lines):
        x = (bw - lw(ix)) / 2
        for k in ix:
            d.text((x, 20 + li * lh), words[k], font=f, fill=WHITE if k < spoken else (255, 255, 255, 120))
            x += widths[k] + sp
    return img


def draw_caption(frame, t, bottom=None):
    for say in TL["says"]:
        if say["start"] - 0.1 <= t < say["end"] + 0.6:
            spoken = sum(1 for ws in word_starts(say) if t >= ws)
            img = caption_img(say["text"], spoken)
            a = clamp((t - say["start"] + 0.1) / 0.15) * clamp((say["end"] + 0.6 - t) / 0.2)
            comp(frame, img, ((W - img.width) / 2, (bottom or CAP_BOTTOM) - img.height), a)
            return


# ================================================================ Szenen
def draw_intro(frame, t):
    draw_header(frame)
    a_out = clamp((TL["intro_end"] - t) / 0.3)
    # Briefumschlag
    S = 3
    env = Image.new("RGBA", (360 * S, 250 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(env)
    d.rounded_rectangle((0, 0, 360 * S - 1, 250 * S - 1), 28 * S, fill=WHITE, outline=NAVY, width=8 * S)
    d.line([(14 * S, 22 * S), (180 * S, 150 * S), (346 * S, 22 * S)], fill=NAVY, width=8 * S, joint="curve")
    env = shadow(env.resize((360, 250), Image.LANCZOS), 18, 60, 10)
    bob = 10 * math.sin(t * 2.4)
    comp_center(frame, env, W / 2, 640 + bob, 0.7 + 0.3 * back_out(t / 0.6), clamp(t / 0.25) * a_out)
    badge = pill("@", 60, WHITE, ORANGE, 26, 6, "ExtraBold")
    if t > 0.5:
        comp_center(frame, badge, W / 2 + 170, 520 + bob, max(0.01, back_out((t - 0.5) / 0.4)), a_out)
    tin = ease_out((t - 0.4) / 0.5)
    ttl = text_img(C.TITEL, "ExtraBold", 108, NAVY)
    comp_center(frame, ttl, W / 2, 900 + 30 * (1 - tin), 1, tin * a_out)
    sub = text_img(C.UNTERTITEL, "SemiBold", 50, ORANGE)
    tin2 = ease_out((t - 0.7) / 0.5)
    comp_center(frame, sub, W / 2, 1010 + 20 * (1 - tin2), 1, tin2 * a_out)
    draw_caption(frame, t, 1400)


def draw_step_body(frame, t, i, lt):
    draw_chips(frame, t, False)
    dim = 1.0
    if i == NSTEP - 1:
        dim = 1 - 0.65 * ease_out((lt - 0.3) / 0.5)
    draw_mail(frame, t, dim)
    for say in TL["says"]:
        if say.get("step") == i and "Informell" in say["text"] and say["start"] - 0.2 <= t:
            a = clamp((t - say["start"] + 0.2) / 0.3)
            card = informal_card()
            layout = [l for l in mail_layout() if l[0] == "anrede"]
            y = MAIL[1] + BODY_TOP + layout[0][2] + 90 if layout else MAIL[1] + 300
            comp_center(frame, card, W / 2, y, 0.8 + 0.2 * back_out((t - say["start"] + 0.2) / 0.4), a)


def draw_step(frame, t, i):
    st = TL["steps"][i]
    lt = t - st["start"]
    draw_header(frame, i)
    stt = step_title(i)
    comp_center(frame, stt, W / 2, STEP_Y, 0.85 + 0.15 * back_out(lt / 0.45), clamp(lt / 0.2))
    if i == 0:
        draw_task_big(frame, t, st["start"] + 1.2)
    elif i == 1 and lt < 0.5:                      # Aufgabenkarte klingt aus, E-Mail blendet ein
        u = ease_out(lt / 0.5)
        old = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_task_big(old, t, None)
        comp(frame, old, (0, 0), 1 - u)
        new = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_step_body(new, t, i, lt)
        comp(frame, new, (0, 0), u)
    else:
        draw_step_body(frame, t, i, lt)
    if i == NSTEP - 1:
        draw_checklist(frame, t, lt)
    draw_caption(frame, t)


def draw_checklist(frame, t, lt):
    card = Image.new("RGBA", (860, 150 + 124 * len(C.CHECKLISTE)), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, card.width - 1, card.height - 1), 40, fill=WHITE, outline=(*OK, 170), width=5)
    d.text((card.width / 2, 74), "Checkliste", font=font("ExtraBold", 64), fill=NAVY, anchor="mm")
    a = ease_out((lt - 0.4) / 0.4)
    cy = MAIL[1] + 380
    comp_center(frame, shadow(card, 22, 70, 12), W / 2, cy, 0.9 + 0.1 * back_out((lt - 0.4) / 0.5), a)
    top = cy - card.height / 2
    say = next(s for s in TL["says"] if s.get("step") == NSTEP - 1)
    span = say["end"] - say["start"]
    for k, item in enumerate(C.CHECKLISTE):
        y = top + 160 + k * 124
        tk = say["start"] + span * (0.35 + 0.25 * k)
        on = t >= tk
        ic = check_icon(38, OK if on else GREY, on)
        comp_center(frame, ic, W / 2 - 330, y + 34, max(0.01, back_out((t - tk) / 0.35)) if on else 1, a)
        comp(frame, text_img(item, "Bold", 58, NAVY), (W / 2 - 260, y - 6), a)


def draw_outro(frame, t):
    lt = t - TL["outro_start"]
    draw_header(frame)
    comp_center(frame, LOGO, W / 2, 640, 1.9 * (0.8 + 0.2 * back_out(lt / 0.6)), clamp(lt / 0.3))
    ttl = text_img("Viel Erfolg beim DTZ!", "ExtraBold", 84, NAVY)
    comp_center(frame, ttl, W / 2, 900, 1, ease_out((lt - 0.3) / 0.5))
    p = pill("Folge der ELM Akademie", 50, WHITE, ORANGE, 44, 20, "ExtraBold")
    comp_center(frame, shadow(p, 14, 50, 8), W / 2, 1040, max(0.01, back_out((lt - 0.6) / 0.5)),
                clamp((lt - 0.6) / 0.2))


def render_frame(fi):
    t = fi / FPS
    frame = background(t)
    if t < TL["intro_end"]:
        draw_intro(frame, t)
    elif t < TL["outro_start"]:
        i = max(k for k, s in enumerate(TL["steps"]) if s["start"] <= t)
        draw_step(frame, t, i)
    else:
        draw_outro(frame, t)
    out = frame.convert("RGB")
    a = min(clamp(t / 0.35), clamp((TOTAL - t) / 0.6))
    if a < 1:
        out = Image.blend(Image.new("RGB", (W, H), BG), out, a)
    return out.tobytes()


# ================================================================ Start
def main():
    print("Erzeuge Sprache ...", flush=True)
    plan()
    load_logo()
    wav = HERE.parent / ".cache" / "dtz_email.wav"
    build_audio(wav)
    if "--preview" in sys.argv:
        out = HERE / "vorschau"
        out.mkdir(exist_ok=True)
        ts = [2.0] + [s["end"] - 0.4 for s in TL["steps"]] + [TOTAL - 1.0]
        ts.insert(4, TL["types"]["p2"][0] + 0.8)
        for x in ts:
            Image.frombytes("RGB", (W, H), render_frame(int(x * FPS))).save(out / f"t{x:05.1f}.png")
        print("Vorschau in", out)
        return
    out = HERE / "dtz_email.mp4"
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
