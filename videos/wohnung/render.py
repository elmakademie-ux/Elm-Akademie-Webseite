"""
Rendert das A1-Lernvideo "Meine Wohnung" (1080x1920, 30 fps, exakt 60 s, MP4).

    python3 render.py             -> meine_wohnung.mp4
    python3 render.py --preview   -> vorschau/*.png

Texte, Wörter und Farben stehen in inhalt.py.
Die Pausen zum Nachsprechen werden automatisch so berechnet, dass das Video genau
GESAMTDAUER Sekunden lang ist.
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import illustrationen  # noqa: E402
import inhalt as C  # noqa: E402

W, H, FPS = 1080, 1920, 30
TOTAL = C.GESAMTDAUER
N_FRAMES = int(round(TOTAL * FPS))
NS = len(C.SZENEN)
FONT_DIR = Path("/usr/share/fonts/opentype/inter")

NAVY, BG = C.FARBE_TEXT, C.FARBE_HINTERGRUND
GREEN_REP = C.FARBE_NACHSPRECHEN
WHITE = (255, 255, 255)
ART_COL = {"der": C.FARBE_DER, "die": C.FARBE_DIE, "das": C.FARBE_DAS}

# Layout
HEADER_Y = 48
DOTS_Y = 208
TITLE_Y = 286
CARD = (90, 355, 990, 1125)          # 900 x 770
SENT_Y = 1160
WORD_Y = 1335
REP_Y = 1478


# =================================================================== Helfer
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
    if r <= l or b <= t:
        return
    if (l, t, r, b) != (0, 0, img.width, img.height):
        img = img.crop((l, t, r, b))
    frame.alpha_composite(img, (x + l, y + t))


def comp_center(frame, img, cx, cy, s=1.0, alpha=1.0):
    if abs(s - 1) > 0.003:
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BICUBIC)
    comp(frame, img, (cx - img.width / 2, cy - img.height / 2), alpha)


def shadow(img, blur=16, alpha=55, dy=8):
    pad = blur * 2
    out = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    m = img.getchannel("A").point(lambda v: int(v * alpha / 255))
    out.paste((20, 30, 60, 255), (pad, pad + dy), m)
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(img, (pad, pad))
    return out


@lru_cache(None)
def pill(text, size, fg, bg, padx=32, pady=14, weight="Bold"):
    f = font(weight, size)
    h = int(size * 1.15) + 2 * pady
    img = Image.new("RGBA", (int(f.getlength(text)) + 2 * padx, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, h - 1), h // 2, fill=bg)
    bb = f.getbbox(text)
    d.text((padx, h / 2 - (bb[1] + bb[3]) / 2), text, font=f, fill=fg)
    return img


# =================================================================== Woerter / Farben
NOUNS = {}
for v in C.VOKABELN:
    art, noun = v.split(" ", 1)
    NOUNS[noun] = ART_COL[art]


def strip_punct(w):
    return w.strip(".,!?;:…")


def token_colors(words):
    cols = [None] * len(words)
    for k, w in enumerate(words):
        c = NOUNS.get(strip_punct(w))
        if c:
            cols[k] = c
            if k and words[k - 1].lower() in ART_COL:
                cols[k - 1] = c
    return cols


def word_color(phrase):
    art = phrase.split(" ")[0].lower()
    return ART_COL.get(art, NAVY)


@lru_cache(None)
def sentence_img(text, spoken, size):
    """Satz mit farbigen Nomen; noch nicht gesprochene Woerter blass (Karaoke)."""
    f = font("ExtraBold", size)
    words = text.split()
    cols = token_colors(words)
    space = f.getlength(" ")
    widths = [f.getlength(w) for w in words]
    max_w = W - 140

    def lw(ws):
        return sum(ws) + space * (len(ws) - 1)

    # in moeglichst gleich lange Zeilen teilen (1-3 Zeilen)
    if lw(widths) <= max_w:
        splits = [0, len(words)]
    else:
        best = None
        for k in range(1, len(words)):
            m = max(lw(widths[:k]), lw(widths[k:]))
            if best is None or m < best[0]:
                best = (m, [0, k, len(words)])
        splits = best[1]
    lh = int(size * 1.28)
    img = Image.new("RGBA", (W, lh * (len(splits) - 1) + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gi = 0
    for li in range(len(splits) - 1):
        seg = list(range(splits[li], splits[li + 1]))
        x = (W - lw([widths[k] for k in seg])) / 2
        for k in seg:
            a = 255 if gi < spoken else 80
            col = cols[k] or NAVY
            d.text((x, li * lh), words[k], font=f, fill=(*col, a))
            if cols[k]:
                d.rounded_rectangle((x, li * lh + size * 1.02, x + widths[k], li * lh + size * 1.02 + 6), 3,
                                    fill=(*col, int(a * 0.5)))
            x += widths[k] + space
            gi += 1
    return img


def fit_size(text):
    for size in range(64, 47, -2):
        f = font("ExtraBold", size)
        if f.getlength(text) <= 2 * (W - 160):
            return size
    return 48


@lru_cache(None)
def colored_phrase(phrase, size, weight="ExtraBold"):
    col = word_color(phrase)
    f = font(weight, size)
    img = Image.new("RGBA", (int(f.getlength(phrase)) + 8, int(size * 1.3)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4, 0), phrase, font=f, fill=col)
    return img


@lru_cache(None)
def big_word(phrase):
    col = word_color(phrase)
    t = colored_phrase(phrase, 86)
    w, h = t.width + 90, 150
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 40, fill=WHITE)
    d.rounded_rectangle((0, h - 12, w - 1, h - 1), 6, fill=col)
    img.alpha_composite(t, (45, 20))
    return shadow(img, 18, 60, 10)


@lru_cache(None)
def pin_label(phrase):
    col = word_color(phrase)
    t = colored_phrase(phrase, 40, "Bold")
    w, h = t.width + 36, 66
    img = Image.new("RGBA", (w, h + 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 20, fill=WHITE, outline=col, width=4)
    d.polygon([(w / 2 - 14, h - 2), (w / 2 + 14, h - 2), (w / 2, h + 16)], fill=col)
    img.alpha_composite(t, (18, 8))
    return shadow(img, 10, 60, 5)


# =================================================================== Audio + Zeitplan
CLIPS = {}   # text -> (samples, speech_start, speech_end) in Sekunden


def synth_all():
    from common.audio import SR, ensure_voice, speak
    model = ensure_voice()
    tmp = HERE.parent / ".cache" / "line_wo.wav"
    texts = [C.INTRO_SATZ, C.OUTRO_FRAGE]
    for sc in C.SZENEN:
        texts += sc["saetze"] + sc["woerter"]
    for t in texts:
        if t in CLIPS:
            continue
        seg = speak(t, tmp, model, C.SPRECHTEMPO)
        nz = np.nonzero(np.abs(seg) > 0.02)[0]
        s0, s1 = (nz[0] / SR, nz[-1] / SR) if len(nz) else (0, len(seg) / SR)
        CLIPS[t] = (seg, s0, s1)


def speech_dur(t):
    _, s0, s1 = CLIPS[t]
    return s1 - s0


TL = {}  # Zeitplan


def build_timeline(pause):
    tl = dict(events=[], scenes=[])
    t = 0.45
    tl["events"].append((t, C.INTRO_SATZ))
    tl["intro_words"] = word_times(C.INTRO_SATZ, t)
    tl["intro_end"] = max(4.2, t + speech_dur(C.INTRO_SATZ) + 0.7)
    cur = tl["intro_end"]
    for sc in C.SZENEN:
        s = dict(start=cur, sent_words=[], words=[])
        t = cur + 0.65
        for sent in sc["saetze"]:
            tl["events"].append((t, sent))
            s["sent_words"] += word_times(sent, t)
            t += speech_dur(sent) + 0.3
        t += 0.1
        for w in sc["woerter"]:
            tl["events"].append((t, w))
            d = speech_dur(w)
            s["words"].append(dict(word=w, start=t, end=t + d, next=t + d + pause))
            t += d + pause
        s["end"] = max(t + (0.15 if sc["woerter"] else 0.9), cur + 3.8)
        tl["scenes"].append(s)
        cur = s["end"]
    tl["outro_start"] = cur
    tl["events"].append((cur + 0.6, C.OUTRO_FRAGE))
    return tl


def word_times(sentence, start):
    """Startzeit jedes Wortes (gewichtete Verteilung ueber die Sprechdauer)."""
    words = sentence.split()
    wt = [len(w) + (5 if w[-1] in ".!?" else 2 if w[-1] == "," else 1) for w in words]
    d = speech_dur(sentence)
    out, t = [], start
    for w, k in zip(words, wt):
        out.append(t)
        t += d * k / sum(wt)
    return out


def plan():
    n_words = sum(len(sc["woerter"]) for sc in C.SZENEN)
    base = build_timeline(0.0)["outro_start"]
    outro_min = 6.0
    pause = max(0.7, min(2.2, (TOTAL - outro_min - base) / max(1, n_words)))
    # feinjustieren, bis der Abschluss genau outro_min Sekunden hat
    while pause < 2.2 and build_timeline(pause + 0.02)["outro_start"] <= TOTAL - outro_min:
        pause += 0.02
    tl = build_timeline(pause)
    if tl["outro_start"] > TOTAL - 4.5:
        print("WARNUNG: Texte sind fuer die Gesamtdauer zu lang – SPRECHTEMPO verkleinern oder Saetze kuerzen.")
    print(f"Pause zum Nachsprechen: {pause:.2f} s, Abschluss ab {tl['outro_start']:.1f} s")
    TL.update(tl)
    # letzte Szene endet genau bei Outro-Start; Dauer Outro = Rest bis TOTAL


def build_audio(out_wav):
    from common.audio import SR, add, make_music
    starts = [s["start"] for s in TL["scenes"]]
    music = make_music(TOTAL, starts, TL["intro_end"]) * C.MUSIK_LAUTSTAERKE
    voice = np.zeros_like(music)
    for t, text in TL["events"]:
        seg, s0, _ = CLIPS[text]
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


# =================================================================== Bilder
SRC_SCALE = 1.6
CW, CH = CARD[2] - CARD[0], CARD[3] - CARD[1]
SOURCES = []
LOGO = None
THUMB = None


def load_assets():
    global LOGO, THUMB
    for sc in C.SZENEN:
        img = None
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            p = HERE / "bilder" / f"{sc['bild']}{ext}"
            if p.exists():
                img = ImageOps.fit(ImageOps.exif_transpose(Image.open(p)).convert("RGB"),
                                   (int(CW * SRC_SCALE), int(CH * SRC_SCALE)), Image.LANCZOS)
                break
        if img is None:
            img = illustrationen.render(sc["bild"], int(CW * SRC_SCALE))
        SOURCES.append(img)
    logo = Image.open(HERE / "bilder" / "logo.png").convert("RGB")
    logo = logo.resize((int(logo.width * 1.4), int(logo.height * 1.4)), Image.LANCZOS)
    pad = 10
    card = Image.new("RGBA", (logo.width + 2 * pad, logo.height + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 24, fill=WHITE)
    m = Image.new("L", logo.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, logo.width - 1, logo.height - 1), 18, fill=255)
    card.paste(logo, (pad, pad), m)
    LOGO = shadow(card, 12, 40, 5)
    th = SOURCES[0].resize((420, 359), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", th.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, th.width - 1, th.height - 1), 40, fill=255)
    th.putalpha(m)
    THUMB = shadow(th, 20, 70, 12)


@lru_cache(None)
def card_mask():
    m = Image.new("L", (CW * 2, CH * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, CW * 2 - 1, CH * 2 - 1), 76, fill=255)
    return m.resize((CW, CH), Image.LANCZOS)


@lru_cache(None)
def card_shadow():
    b = Image.new("RGBA", (CW, CH), WHITE)
    b.putalpha(card_mask())
    return shadow(b, 26, 70, 16)


def render_card(i, u):
    """Ken-Burns-Zoom; liefert Bild und Funktion zur Umrechnung von Bildpunkten."""
    src = SOURCES[i]
    last = C.SZENEN[i]["bild"] == "gesamt"           # Uebersicht: kaum Zoom, nichts abschneiden
    z = 1.0 + (0.03 if last else 0.09) * ease_io(u)
    s = SRC_SCALE / z
    ww, wh = CW * s, CH * s
    dirx = 0 if last else (-1) ** i
    cx = src.width / 2 + dirx * (src.width - ww) / 2 * (ease_io(u) - 0.5) * 0.9
    cy = src.height / 2
    bx, by = cx - ww / 2, cy - wh / 2
    img = src.transform((CW, CH), Image.AFFINE, (s, 0, bx, 0, s, by), Image.BICUBIC).convert("RGBA")
    img.putalpha(card_mask())
    k = src.width / illustrationen.BW

    def to_card(x, y):
        return (x * k - bx) / s, (y * k - by) / s
    return img, to_card


# =================================================================== Hintergrund
def blob(r, color):
    img = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, 2 * r, 2 * r), fill=color)
    return img.filter(ImageFilter.GaussianBlur(30))


BLOBS = [(blob(360, (*C.FARBE_DAS, 20)), 0.0, (-220, 260)),
         (blob(300, (*C.FARBE_DER, 16)), 2.0, (720, 880)),
         (blob(260, (*C.FARBE_DIE, 14)), 4.0, (-60, 1450))]


def background(t):
    frame = Image.new("RGBA", (W, H), (*BG, 255))
    for b, ph, (bx, by) in BLOBS:
        comp(frame, b, (bx + 50 * math.sin(t * 0.3 + ph), by + 60 * math.cos(t * 0.25 + ph)))
    return frame


@lru_cache(None)
def legend():
    parts = [pill(a, 32, WHITE, ART_COL[a], 22, 8) for a in ("der", "die", "das")]
    w = sum(p.width for p in parts) + 16 * 2
    img = Image.new("RGBA", (w, parts[0].height), (0, 0, 0, 0))
    x = 0
    for p in parts:
        img.alpha_composite(p, (x, 0))
        x += p.width + 16
    return img


def draw_header(frame, active=-1):
    comp(frame, LOGO, (36, HEADER_Y - 22))
    p = pill(C.NIVEAU, 36, WHITE, NAVY)
    comp(frame, p, (W - 64 - p.width, HEADER_Y + 30))
    lg = legend()
    left, right = 36 + LOGO.width - 20, W - 64 - p.width
    comp(frame, lg, ((left + right) / 2 - lg.width / 2, HEADER_Y + 36))
    if active < 0:
        return
    d = ImageDraw.Draw(frame, "RGBA")
    gap = 50
    x0 = W / 2 - gap * (NS - 1) / 2
    for k in range(NS):
        x = x0 + k * gap
        if k == active:
            d.rounded_rectangle((x - 20, DOTS_Y - 8, x + 20, DOTS_Y + 8), 8, fill=NAVY)
        else:
            d.ellipse((x - 7, DOTS_Y - 7, x + 7, DOTS_Y + 7), fill=(*NAVY, 200 if k < active else 60))


# =================================================================== Szenen
def draw_sentence(frame, text, times, t, appear, fade_end):
    spoken = sum(1 for ws in times if t >= ws)
    img = sentence_img(text, spoken, fit_size(text))
    a = clamp((t - appear) / 0.3) * clamp((fade_end - t) / 0.3)
    s = 0.92 + 0.08 * back_out((t - appear) / 0.45)
    comp_center(frame, img, W / 2, SENT_Y + img.height / 2, s, a)


def draw_scene(frame, t, i):
    sc, sp = C.SZENEN[i], TL["scenes"][i]
    lt, dur = t - sp["start"], sp["end"] - sp["start"]
    tin = ease_out(lt / 0.5)
    tout = ease_io((lt - (dur - 0.35)) / 0.35)
    draw_header(frame, i)
    # Ueberschrift
    ttl = colored_phrase(sc["titel"], 76)
    comp_center(frame, ttl, W / 2, TITLE_Y, 0.9 + 0.1 * back_out((lt - 0.1) / 0.45),
                clamp((lt - 0.1) / 0.25) * (1 - tout))
    # Bildkarte (faehrt rein / raus)
    dx = (1 - tin) * W * 0.85 - tout * W * 0.85
    a = min(tin, 1 - tout * 0.8)
    card, to_card = render_card(i, clamp(lt / dur))
    sh = card_shadow()
    pad = (sh.width - CW) // 2
    comp(frame, sh, (CARD[0] - pad + dx, CARD[1] - pad + 10), a)
    comp(frame, card, (CARD[0] + dx, CARD[1]), a)
    # Pins
    for w in sp["words"]:
        if w["word"] in sc["pins"] and t >= w["start"]:
            px, py = to_card(*sc["pins"][w["word"]])
            x, y = CARD[0] + px + dx, CARD[1] + py
            pa = back_out((t - w["start"]) / 0.4)
            d = ImageDraw.Draw(frame, "RGBA")
            r = 13 * max(0.01, pa)
            d.ellipse((x - r - 5, y - r - 5, x + r + 5, y + r + 5), fill=(*WHITE, int(255 * a)))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(*word_color(w["word"]), int(255 * a)))
            lab = pin_label(w["word"])
            comp_center(frame, lab, x, y - 22 - lab.height / 2 + 10, max(0.01, pa), a)
    # Satz (Karaoke)
    text = " ".join(sc["saetze"])
    draw_sentence(frame, text, sp["sent_words"], t, sp["start"] + 0.35, sp["end"] - 0.05)
    # Neues Wort gross + Sprich nach
    cur = None
    for w in sp["words"]:
        if t >= w["start"] - 0.05:
            cur = w
    if cur is not None:
        bw = big_word(cur["word"])
        pa = back_out((t - cur["start"] + 0.05) / 0.35)
        a2 = clamp((t - cur["start"] + 0.05) / 0.15) * clamp((sp["end"] - t) / 0.25)
        comp_center(frame, bw, W / 2, WORD_Y + 70, 0.6 + 0.4 * max(0.01, pa), a2)
        if cur["end"] + 0.1 <= t < cur["next"]:
            draw_repeat(frame, (t - cur["end"] - 0.1) / max(0.1, cur["next"] - cur["end"] - 0.1),
                        clamp((t - cur["end"] - 0.1) / 0.2) * clamp((cur["next"] - t) / 0.15))


@lru_cache(None)
def repeat_badge():
    p = pill(C.NACHSPRECHEN, 40, WHITE, GREEN_REP, 34, 14)
    h = p.height
    img = Image.new("RGBA", (p.width + h + 10, h), (0, 0, 0, 0))
    img.alpha_composite(p, (h + 10, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, h - 1, h - 1), fill=GREEN_REP)
    c = h / 2
    d.rounded_rectangle((c - 8, c - 20, c + 8, c + 6), 8, fill=WHITE)
    d.arc((c - 15, c - 10, c + 15, c + 16), 0, 180, fill=WHITE, width=4)
    d.line((c, c + 16, c, c + 23), fill=WHITE, width=4)
    return img


def draw_repeat(frame, k, a):
    b = repeat_badge()
    comp_center(frame, b, W / 2, REP_Y + b.height / 2, 1 + 0.04 * math.sin(k * 12), a)
    d = ImageDraw.Draw(frame, "RGBA")
    bw, x0, y = 280, W / 2 - 140, REP_Y + b.height + 16
    d.rounded_rectangle((x0, y, x0 + bw, y + 8), 4, fill=(*GREEN_REP, int(60 * a)))
    d.rounded_rectangle((x0, y, x0 + bw * (1 - clamp(k)), y + 8), 4, fill=(*GREEN_REP, int(255 * a)))


def draw_intro(frame, t):
    end = TL["intro_end"]
    a_out = clamp((end - t) / 0.35)
    draw_header(frame)
    comp_center(frame, THUMB, W / 2, 620, 0.85 + 0.15 * back_out((t - 0.1) / 0.6), clamp(t / 0.3) * a_out)
    ttl = pill(C.TITEL, 100, NAVY, (0, 0, 0, 0), 0, 0, "ExtraBold")
    tin = ease_out((t - 0.5) / 0.5)
    comp_center(frame, ttl, W / 2, 905 + 30 * (1 - tin), 1, tin * a_out)
    # Artikel-Farben erklaeren
    y = 1030
    for k, art in enumerate(("der", "die", "das")):
        p = pill(art, 52, WHITE, ART_COL[art], 36, 14)
        pa = back_out((t - 1.0 - 0.18 * k) / 0.4)
        if t > 1.0 + 0.18 * k:
            comp_center(frame, p, W / 2 + (k - 1) * 210, y + 45, max(0.01, pa), a_out)
    draw_sentence(frame, C.INTRO_SATZ, TL["intro_words"], t, 0.3, end)


def draw_outro(frame, t):
    lt = t - TL["outro_start"]
    draw_header(frame)
    q = pill(C.OUTRO_FRAGE, 78, NAVY, (0, 0, 0, 0), 0, 0, "ExtraBold")
    comp_center(frame, q, W / 2, 420, 0.85 + 0.15 * back_out(lt / 0.5), clamp(lt / 0.25))
    s = pill(C.OUTRO_SATZ_ANFANG, 58, NAVY, (0, 0, 0, 0), 0, 0, "Bold")
    comp_center(frame, s, W / 2, 580, 1, clamp((lt - 0.6) / 0.3))
    hl = int(max(0, lt - 1.8) / 0.7) % len(C.OUTRO_ADJEKTIVE)
    for k, adj in enumerate(C.OUTRO_ADJEKTIVE):
        on = lt > 1.8 and k == hl
        p = pill(adj, 56, WHITE if on else NAVY, (237, 140, 20) if on else WHITE, 44, 18, "ExtraBold")
        p = shadow(p, 12, 45, 6)
        x = W / 2 + (-1 if k % 2 == 0 else 1) * 215
        y = 720 + (k // 2) * 140
        st = 0.9 + 0.15 * k
        if lt > st:
            comp_center(frame, p, x, y, max(0.01, back_out((lt - st) / 0.4)) * (1.06 if on else 1.0))
    if lt > 2.0:
        a = ease_out((lt - 2.0) / 0.5)
        comp_center(frame, LOGO, W / 2, 1110, 1.35, a)
        m = pill(C.OUTRO_MARKE, 46, NAVY, (0, 0, 0, 0), 0, 0, "Bold")
        comp_center(frame, m, W / 2, 1265, 1, a)


def render_frame(fi):
    t = fi / FPS
    frame = background(t)
    if t < TL["intro_end"]:
        draw_intro(frame, t)
    elif t < TL["outro_start"]:
        i = max(k for k, s in enumerate(TL["scenes"]) if s["start"] <= t)
        draw_scene(frame, t, i)
    else:
        draw_outro(frame, t)
    out = frame.convert("RGB")
    a = min(clamp(t / 0.35), clamp((TOTAL - t) / 0.6))
    if a < 1:
        out = Image.blend(Image.new("RGB", (W, H), BG), out, a)
    return out.tobytes()


# =================================================================== Start
def main():
    print("Erzeuge Sprache ...", flush=True)
    synth_all()
    plan()
    load_assets()
    cache = HERE.parent / ".cache"
    wav = cache / "wohnung.wav"
    build_audio(wav)

    if "--preview" in sys.argv:
        out = HERE / "vorschau"
        out.mkdir(exist_ok=True)
        times = [2.5]
        for s, sc in zip(TL["scenes"], C.SZENEN):
            times.append(s["words"][-1]["end"] + 0.4 if s["words"] else s["end"] - 0.6)
        times.append(TOTAL - 1.5)
        for ts in times:
            Image.frombytes("RGB", (W, H), render_frame(int(ts * FPS))).save(out / f"t{ts:05.1f}.png")
        print("Vorschau in", out)
        return

    out = HERE / "meine_wohnung.mp4"
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
