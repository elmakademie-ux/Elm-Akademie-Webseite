"""
Erzeugt ein 60-Sekunden-Reel (1080x1920, 30 fps) mit 5 Lerntipps.

Aufruf:  python3 render.py            -> lerntipps.mp4
         python3 render.py --preview  -> nur Vorschaubilder (preview_*.png)

Texte, Farben und Zeiten lassen sich im Abschnitt INHALT anpassen.
Benoetigt: Python 3, Pillow, ffmpeg.
"""
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# INHALT
# --------------------------------------------------------------------------
HOOK = {
    "lines": ["5 Lerntipps,", "die wirklich", "funktionieren"],
    "highlight": 2,  # Index der Zeile in Akzentfarbe
    "sub": "in 60 Sekunden",
}

TIPS = [
    ("Pomodoro-Technik",
     "25 Minuten konzentriert lernen, dann 5 Minuten Pause. "
     "Nach vier Runden eine längere Pause."),
    ("Aktiv abrufen",
     "Buch zu und selbst abfragen: Was weiß ich noch? "
     "Abrufen trainiert das Gedächtnis mehr als erneutes Lesen."),
    ("Verteilt wiederholen",
     "Lieber öfter kurz als einmal lang. "
     "Wiederhole nach 1 Tag, 3 Tagen und 1 Woche."),
    ("Erklär es jemandem",
     "Wenn du es einfach erklären kannst, hast du es verstanden. "
     "Lücken fallen dabei sofort auf."),
    ("Handy aus dem Raum",
     "Schon ein sichtbares Handy lenkt ab. "
     "Leg es in einen anderen Raum, solange du lernst."),
]

CTA = {
    "question": "Welcher Tipp hilft dir am meisten?",
    "action": "Speichern & teilen",
    "brand": "ELM-AKADEMIE",
}

BRAND = "ELM-AKADEMIE"

# Sprechertexte (Zahlen ausgeschrieben, damit die Stimme sie sauber spricht).
# Reihenfolge: Einstieg, 5 Tipps, Abschluss. Leer lassen = kein Sprecher.
VOICEOVER = [
    "Fünf Lerntipps, die wirklich funktionieren. In sechzig Sekunden.",
    "Tipp eins: die Pomodoro-Technik. Fünfundzwanzig Minuten konzentriert lernen, "
    "dann fünf Minuten Pause. Nach vier Runden eine längere Pause.",
    "Tipp zwei: aktiv abrufen. Buch zu, und frag dich selbst ab. "
    "Abrufen trainiert dein Gedächtnis mehr als erneutes Lesen.",
    "Tipp drei: verteilt wiederholen. Lieber öfter kurz als einmal lang. "
    "Wiederhole nach einem Tag, drei Tagen und einer Woche.",
    "Tipp vier: Erklär es jemandem. Wenn du es einfach erklären kannst, "
    "hast du es verstanden. Lücken fallen dabei sofort auf.",
    "Tipp fünf: Handy aus dem Raum. Schon ein sichtbares Handy lenkt ab. "
    "Leg es woanders hin, solange du lernst.",
    "Welcher Tipp hilft dir am meisten? Speichern und teilen. Deine Elm-Akademie.",
]

# Zeiten in Sekunden
HOOK_DUR = 5.0
TIP_DUR = 10.0
CTA_DUR = 5.0

# Farben
BG_TOP = (24, 54, 38)
BG_BOTTOM = (12, 30, 21)
TEXT = (245, 241, 230)
MUTED = (245, 241, 230, 190)
ACCENT = (168, 214, 114)
RING_BG = (255, 255, 255, 40)

# --------------------------------------------------------------------------
# TECHNIK
# --------------------------------------------------------------------------
W, H, FPS = 1080, 1920, 30
TOTAL = HOOK_DUR + TIP_DUR * len(TIPS) + CTA_DUR
MARGIN = 100
FADE_IN = 0.55
FADE_OUT = 0.35

FONT_DIR = Path("/usr/share/fonts/opentype/inter")


@lru_cache(None)
def font(weight: str, size: int):
    for name in (f"Inter-{weight}.otf", "Inter-Regular.otf"):
        p = FONT_DIR / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.truetype("DejaVuSans-Bold.ttf", size)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def wrap(text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if fnt.getlength(test) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


@lru_cache(None)
def text_block(text, weight, size, color, max_w=W - 2 * MARGIN, spacing=1.25, align="center"):
    """Rendert (umbrochenen) Text einmal als transparentes Bild."""
    fnt = font(weight, size)
    lines = wrap(text, fnt, max_w)
    lh = int(size * spacing)
    img = Image.new("RGBA", (W, lh * len(lines) + size // 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        lw = fnt.getlength(line)
        x = (W - lw) / 2 if align == "center" else MARGIN
        d.text((x, i * lh), line, font=fnt, fill=color)
    return img


def place(frame, img, y, t_local, delay, scene_dur, dy=50):
    """Blendet ein Element mit Slide-up ein und am Szenenende aus."""
    a_in = ease_out((t_local - delay) / FADE_IN)
    a_out = min(1.0, max(0.0, (scene_dur - t_local) / FADE_OUT))
    a = a_in * a_out
    if a <= 0.01:
        return
    off = int((1 - a_in) * dy)
    layer = img
    if a < 0.999:
        layer = img.copy()
        layer.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    frame.alpha_composite(layer, (0, int(y + off)))


def make_background():
    bg = Image.new("RGBA", (W, H))
    px = bg.load()
    for y in range(H):
        k = y / (H - 1)
        c = tuple(int(BG_TOP[i] * (1 - k) + BG_BOTTOM[i] * k) for i in range(3))
        for x in range(W):
            px[x, y] = (*c, 255)
    return bg


def make_blob(r, color):
    img = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, 2 * r, 2 * r), fill=color)
    return img


BG = make_background()
BLOBS = [
    (make_blob(380, (168, 214, 114, 18)), 0.0),
    (make_blob(260, (245, 241, 230, 12)), 2.1),
    (make_blob(200, (168, 214, 114, 14)), 4.2),
]


def draw_background(t):
    frame = BG.copy()
    positions = [(-120, 180), (650, 1150), (120, 1500)]
    for (blob, phase), (bx, by) in zip(BLOBS, positions):
        x = bx + int(40 * math.sin(t * 0.35 + phase))
        y = by + int(50 * math.cos(t * 0.28 + phase))
        frame.alpha_composite(blob, (x, y)) if 0 <= x and 0 <= y else frame.paste(
            blob, (x, y), blob)
    return frame


def draw_chrome(frame, t):
    layer = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # Fortschrittsbalken oben
    y = 90
    d.rounded_rectangle((MARGIN, y, W - MARGIN, y + 8), 4, fill=(255, 255, 255, 45))
    p = t / TOTAL
    d.rounded_rectangle((MARGIN, y, MARGIN + int((W - 2 * MARGIN) * p), y + 8), 4, fill=ACCENT)
    # Marke
    f = font("SemiBold", 34)
    lw = f.getlength(BRAND)
    d.text(((W - lw) / 2, 130), BRAND, font=f, fill=(245, 241, 230, 170))
    frame.alpha_composite(layer)


def draw_hook(frame, t):
    y = 620
    for i, line in enumerate(HOOK["lines"]):
        col = ACCENT if i == HOOK["highlight"] else TEXT
        img = text_block(line, "ExtraBold", 118, col)
        place(frame, img, y, t, 0.15 + i * 0.22, HOOK_DUR)
        y += 140
    sub = text_block(HOOK["sub"], "Medium", 52, MUTED)
    place(frame, sub, y + 60, t, 1.0, HOOK_DUR)


def draw_ring(frame, cx, cy, r, progress, alpha, label):
    layer = Image.new("RGBA", (W, 2 * r + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    box = (cx - r, 20, cx + r, 20 + 2 * r)
    d.ellipse(box, outline=RING_BG, width=14)
    if progress > 0:
        d.arc(box, -90, -90 + 360 * progress, fill=ACCENT, width=14)
    f = font("ExtraBold", 150)
    tw = f.getlength(label)
    bb = f.getbbox(label)
    d.text((cx - tw / 2, 20 + r - (bb[1] + bb[3]) / 2), label, font=f, fill=TEXT)
    if alpha < 0.999:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(layer, (0, cy - r - 20))


def draw_tip(frame, t, idx):
    title, body = TIPS[idx]
    a_in = ease_out(t / FADE_IN)
    a_out = min(1.0, max(0.0, (TIP_DUR - t) / FADE_OUT))
    progress = ease_out(min(1.0, t / (TIP_DUR - 0.6)))
    draw_ring(frame, W // 2, 560, 165, progress, a_in * a_out, str(idx + 1))

    lbl = text_block(f"TIPP {idx + 1} VON {len(TIPS)}", "SemiBold", 36, ACCENT)
    place(frame, lbl, 800, t, 0.2, TIP_DUR)
    ttl = text_block(title, "ExtraBold", 88, TEXT)
    place(frame, ttl, 870, t, 0.35, TIP_DUR)
    ttl_h = ttl.height
    bdy = text_block(body, "Medium", 50, MUTED, spacing=1.4)
    place(frame, bdy, 870 + ttl_h + 40, t, 0.8, TIP_DUR)


def draw_cta(frame, t):
    q = text_block(CTA["question"], "ExtraBold", 92, TEXT)
    place(frame, q, 640, t, 0.1, CTA_DUR + 1)
    y = 640 + q.height + 70
    # Button
    f = font("Bold", 56)
    label = CTA["action"]
    bw = int(f.getlength(label)) + 120
    btn = Image.new("RGBA", (W, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(btn)
    x0 = (W - bw) // 2
    d.rounded_rectangle((x0, 0, x0 + bw, 120), 60, fill=ACCENT)
    bb = f.getbbox(label)
    d.text(((W - f.getlength(label)) / 2, 60 - (bb[1] + bb[3]) / 2), label, font=f, fill=BG_BOTTOM)
    place(frame, btn, y, t, 0.5, CTA_DUR + 1)
    br = text_block(CTA["brand"], "Bold", 60, ACCENT)
    place(frame, br, y + 220, t, 0.9, CTA_DUR + 1)


def render_frame(t):
    frame = draw_background(t)
    draw_chrome(frame, t)
    if t < HOOK_DUR:
        draw_hook(frame, t)
    elif t < HOOK_DUR + TIP_DUR * len(TIPS):
        k = t - HOOK_DUR
        idx = int(k // TIP_DUR)
        draw_tip(frame, k - idx * TIP_DUR, idx)
    else:
        draw_cta(frame, t - HOOK_DUR - TIP_DUR * len(TIPS))
    return frame.convert("RGB")


def main():
    out_dir = Path(__file__).parent
    if "--preview" in sys.argv:
        for name, ts in [("hook", 3), ("tipp1", 8), ("tipp3", 31), ("cta", 58)]:
            render_frame(ts).save(out_dir / f"preview_{name}.png")
        return
    out = out_dir / "lerntipps.mp4"
    n = int(TOTAL * FPS)

    # Tonspur
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from common.audio import build_audio
    tip_starts = [HOOK_DUR + i * TIP_DUR for i in range(len(TIPS))]
    starts = [0.4] + [s + 0.3 for s in tip_starts] + [tip_starts[-1] + TIP_DUR + 0.2]
    lines = [(s, txt) for s, txt in zip(starts, VOICEOVER) if txt.strip()]
    print("Erzeuge Tonspur ...", flush=True)
    wav = build_audio(TOTAL, lines, tip_starts, HOOK_DUR, out_dir.parent / ".cache" / "audio.wav")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(wav),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart", str(out),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(render_frame(i / FPS).tobytes())
        if i % (FPS * 5) == 0:
            print(f"{i / FPS:5.1f}s / {TOTAL:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("Fertig:", out)


if __name__ == "__main__":
    main()
