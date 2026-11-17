"""
Reel "6 Übungen für deine Lernpause" (1080x1920, 30 fps, 60 s)
mit animierter Figur, Sprecherstimme und Musik.

Aufruf:  python3 render.py            -> lernpause.mp4
         python3 render.py --preview  -> Vorschaubilder (preview_*.png)
"""
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --------------------------------------------------------------------------
# INHALT
# --------------------------------------------------------------------------
HOOK = {"lines": ["Verspannt vom", "Lernen?"], "highlight": 1,
        "sub": "6 Übungen für deine Lernpause"}

# (Name, Anleitung, Dosierung, Animation)
EXERCISES = [
    ("Schulterkreisen", "Schultern langsam in großen Kreisen bewegen.",
     "10× nach hinten · 10× nach vorne", "shoulders"),
    ("Nacken dehnen", "Kopf sanft zur Seite neigen und halten.",
     "je Seite 15 Sekunden", "neck"),
    ("Arme strecken", "Abwechselnd weit nach oben greifen.",
     "10× pro Seite", "reach"),
    ("Seitbeuge", "Arme hoch und sanft zur Seite neigen.",
     "10× im Wechsel", "sidebend"),
    ("Kniebeugen", "Langsam in die Hocke, Rücken gerade.",
     "15 Wiederholungen", "squat"),
    ("Hampelmann", "Bringt den Kreislauf in Schwung.",
     "30 Sekunden", "jumpingjack"),
]

CTA = {"question": "Speichern & in jeder Lernpause machen",
       "action": "Speichern & teilen", "brand": "ELM-AKADEMIE"}

VOICEOVER = [
    "Verspannt vom vielen Lernen? Sechs Übungen für deine Lernpause.",
    "Übung eins: Schulterkreisen. Zehnmal nach hinten, zehnmal nach vorne.",
    "Übung zwei: Nacken dehnen. Kopf langsam zur Seite neigen und jeweils fünfzehn Sekunden halten.",
    "Übung drei: Arme strecken. Abwechselnd weit nach oben greifen, zehnmal pro Seite.",
    "Übung vier: Seitbeuge. Arme nach oben und sanft zur Seite neigen.",
    "Übung fünf: Kniebeugen. Fünfzehnmal langsam in die Hocke, Rücken gerade.",
    "Übung sechs: Hampelmann. Dreißig Sekunden, für einen wachen Kopf.",
    "Speichern und in jeder Lernpause machen. Deine Elm-Akademie.",
]

BRAND = "ELM-AKADEMIE"
HOOK_DUR, EX_DUR, CTA_DUR = 4.5, 8.5, 4.5

BG_TOP, BG_BOTTOM = (24, 54, 38), (12, 30, 21)
TEXT = (245, 241, 230)
MUTED = (245, 241, 230, 190)
ACCENT = (168, 214, 114)
FIG = (245, 241, 230)

# --------------------------------------------------------------------------
# GRUNDLAGEN
# --------------------------------------------------------------------------
W, H, FPS = 1080, 1920, 30
TOTAL = HOOK_DUR + EX_DUR * len(EXERCISES) + CTA_DUR
MARGIN, FADE_IN, FADE_OUT = 100, 0.55, 0.35
FONT_DIR = Path("/usr/share/fonts/opentype/inter")


@lru_cache(None)
def font(weight, size):
    p = FONT_DIR / f"Inter-{weight}.otf"
    return ImageFont.truetype(str(p if p.exists() else FONT_DIR / "Inter-Regular.otf"), size)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def smooth(x):  # 0..1 -> 0..1 weich
    return (1 - math.cos(math.pi * max(0.0, min(1.0, x)))) / 2


def wrap(text, fnt, max_w):
    lines, cur = [], ""
    for w in text.split():
        test = f"{cur} {w}".strip()
        if fnt.getlength(test) <= max_w:
            cur = test
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


@lru_cache(None)
def text_block(text, weight, size, color, spacing=1.25):
    fnt = font(weight, size)
    lines = wrap(text, fnt, W - 2 * MARGIN)
    lh = int(size * spacing)
    img = Image.new("RGBA", (W, lh * len(lines) + size // 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text(((W - fnt.getlength(line)) / 2, i * lh), line, font=fnt, fill=color)
    return img


@lru_cache(None)
def pill(text, outline=True):
    f = font("SemiBold", 40)
    bw = int(f.getlength(text)) + 80
    img = Image.new("RGBA", (W, 84), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0 = (W - bw) // 2
    if outline:
        d.rounded_rectangle((x0, 2, x0 + bw, 80), 40, outline=ACCENT, width=4)
        col = ACCENT
    else:
        d.rounded_rectangle((x0, 2, x0 + bw, 80), 40, fill=ACCENT)
        col = BG_BOTTOM
    bb = f.getbbox(text)
    d.text(((W - f.getlength(text)) / 2, 41 - (bb[1] + bb[3]) / 2), text, font=f, fill=col)
    return img


def fade(img, a):
    if a >= 0.999:
        return img
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return out


def place(frame, img, y, t, delay, dur, dy=50):
    a_in = ease_out((t - delay) / FADE_IN)
    a = a_in * min(1.0, max(0.0, (dur - t) / FADE_OUT))
    if a > 0.01:
        frame.alpha_composite(fade(img, a), (0, int(y + (1 - a_in) * dy)))


def make_background():
    col = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1)
        col.putpixel((0, y), tuple(int(BG_TOP[i] * (1 - k) + BG_BOTTOM[i] * k) for i in range(3)))
    return col.resize((W, H)).convert("RGBA")


BG = make_background()


def blob(r, color):
    img = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, 2 * r, 2 * r), fill=color)
    return img


BLOBS = [(blob(380, (168, 214, 114, 18)), 0.0, (-120, 180)),
         (blob(260, (245, 241, 230, 12)), 2.1, (650, 1150)),
         (blob(200, (168, 214, 114, 14)), 4.2, (120, 1500))]


def draw_background(t):
    frame = BG.copy()
    for b, ph, (bx, by) in BLOBS:
        x = bx + int(40 * math.sin(t * 0.35 + ph))
        y = by + int(50 * math.cos(t * 0.28 + ph))
        frame.paste(b, (x, y), b)
    layer = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((MARGIN, 90, W - MARGIN, 98), 4, fill=(255, 255, 255, 45))
    d.rounded_rectangle((MARGIN, 90, MARGIN + int((W - 2 * MARGIN) * t / TOTAL), 98), 4, fill=ACCENT)
    f = font("SemiBold", 34)
    d.text(((W - f.getlength(BRAND)) / 2, 130), BRAND, font=f, fill=(245, 241, 230, 170))
    frame.alpha_composite(layer)
    return frame


# --------------------------------------------------------------------------
# FIGUR
# --------------------------------------------------------------------------
S = 2                      # Supersampling fuer glatte Linien
FIG_TOP, FIG_H = 200, 900  # Bereich der Figur im Bild
GROUND = 830               # Bodenlinie innerhalb des Figurbereichs
TORSO, NECK, HEAD_R = 230, 30, 62
UPPER, FORE, THIGH, SHIN = 135, 125, 165, 165
SH_W, HIP_W = 88, 48


def rot(vx, vy, deg):
    a = math.radians(deg)
    return vx * math.cos(a) - vy * math.sin(a), vx * math.sin(a) + vy * math.cos(a)


def pose_for(kind, t):
    """Liefert die Gelenkparameter fuer eine Animation zum Zeitpunkt t."""
    p = dict(lean=0, head=0, sh_dx=0, sh_dy=0, arm_l=(12, 8), arm_r=(12, 8),
             feet=75, squat=0, hop=0, focus=None, breathe=math.sin(t * 2.2) * 4)
    if kind == "shoulders":
        w = 2 * math.pi * t / 2.0
        p.update(sh_dx=8 * math.cos(w), sh_dy=-22 * (1 + math.sin(w)) / 2 - 4 * math.cos(w),
                 focus="shoulders")
    elif kind == "neck":
        ph = (t % 5.0) / 5.0  # rechts halten, links halten
        s = smooth(ph * 4) if ph < 0.5 else 1 - smooth((ph - 0.5) * 4)
        side = 1 if t % 10 < 5 else -1
        p.update(head=30 * s * side, focus="neck")
    elif kind == "reach":
        s = (1 - math.cos(2 * math.pi * t / 2.6)) / 2
        p.update(arm_l=(15 + 160 * s, 10 * (1 - s)), arm_r=(15 + 160 * (1 - s), 10 * s),
                 lean=6 * (s - 0.5) * -2, focus="arms")
    elif kind == "sidebend":
        lean = 16 * math.sin(2 * math.pi * t / 3.6)
        p.update(arm_l=(168, 0), arm_r=(168, 0), lean=lean, focus="waist")
    elif kind == "squat":
        s = (1 - math.cos(2 * math.pi * t / 3.0)) / 2
        p.update(squat=s, arm_l=(35 + 50 * s, 150), arm_r=(35 + 50 * s, 150),
                 feet=95, focus="legs")
    elif kind == "jumpingjack":
        ph = (t % 1.1) / 1.1
        s = (1 - math.cos(2 * math.pi * ph)) / 2
        p.update(arm_l=(20 + 150 * s, 0), arm_r=(20 + 150 * s, 0), feet=60 + 95 * s,
                 hop=28 * abs(math.sin(2 * math.pi * ph)), focus="all")
    elif kind == "cheer":
        p.update(arm_l=(145, 0), arm_r=(145, 0), hop=10 * abs(math.sin(t * 4)))
    return p


def leg(hip, foot, side):
    hx, hy = hip
    fx, fy = foot
    dx, dy = fx - hx, fy - hy
    d = min(math.hypot(dx, dy), THIGH + SHIN - 0.5)
    a = math.acos(max(-1, min(1, (THIGH ** 2 + d ** 2 - SHIN ** 2) / (2 * THIGH * d))))
    base = math.atan2(dy, dx)
    ang = base - a * side  # Knie nach aussen
    kx, ky = hx + THIGH * math.cos(ang), hy + THIGH * math.sin(ang)
    return (kx, ky)


def draw_figure(p, alpha=1.0):
    img = Image.new("RGBA", (W * S, FIG_H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W / 2
    lift = p["hop"]
    # Becken: Hoehe aus Beinlaenge, Kniebeuge und Fussabstand
    stand = THIGH + SHIN - 12
    h = stand - 150 * p["squat"]
    spread = p["feet"] - HIP_W
    h = min(h, math.sqrt(max(1, (THIGH + SHIN - 2) ** 2 - spread ** 2)))
    pelvis = (cx, GROUND - h - lift)

    def P(x, y):
        return (x * S, y * S)

    # Schatten
    sw = 150 - lift * 1.5
    d.ellipse((*P(cx - sw, GROUND + 6), *P(cx + sw, GROUND + 26)), fill=(0, 0, 0, 60))

    lw = int(26 * S)
    col = (*FIG, int(255 * alpha))
    acc = (*ACCENT, int(255 * alpha))

    def seg(a, b, c=col, w=lw):
        d.line((*P(*a), *P(*b)), fill=c, width=w)
        r = w / 2
        for q in (a, b):
            x, y = P(*q)
            d.ellipse((x - r, y - r, x + r, y + r), fill=c)

    f = p["focus"]
    # Beine
    for side in (-1, 1):
        hip = (pelvis[0] + side * HIP_W, pelvis[1])
        foot = (cx + side * p["feet"], GROUND - lift)
        knee = leg(hip, foot, side)
        c = acc if f in ("legs", "all") else col
        seg(hip, knee, c)
        seg(knee, foot, c)
        seg(foot, (foot[0] + side * 28, foot[1]), c)

    # Oberkoerper um Becken drehen
    def up(vx, vy):
        rx, ry = rot(vx, vy, p["lean"])
        return (pelvis[0] + rx, pelvis[1] + ry)

    neck_base = up(0, -TORSO - p["breathe"] * 0.3)
    shs = [up(side * SH_W + side * p["sh_dx"], -TORSO + 18 + p["sh_dy"] - p["breathe"] * 0.3)
           for side in (-1, 1)]
    hips = [(pelvis[0] - HIP_W, pelvis[1]), (pelvis[0] + HIP_W, pelvis[1])]
    torso_c = acc if f in ("waist", "all") else col
    seg(pelvis, neck_base, torso_c, int(34 * S))
    seg(hips[0], hips[1], col)
    seg(shs[0], shs[1], acc if f in ("shoulders", "all") else col)

    # Arme
    for side, sh, (a, b) in ((-1, shs[0], p["arm_l"]), (1, shs[1], p["arm_r"])):
        ang = a + p["lean"] * 0  # Winkel ab senkrecht nach unten, nach aussen
        ux, uy = side * math.sin(math.radians(ang)), math.cos(math.radians(ang))
        ux, uy = rot(ux, uy, p["lean"])
        elbow = (sh[0] + ux * UPPER, sh[1] + uy * UPPER)
        ang2 = ang - b
        vx, vy = side * math.sin(math.radians(ang2)), math.cos(math.radians(ang2))
        vx, vy = rot(vx, vy, p["lean"])
        hand = (elbow[0] + vx * FORE, elbow[1] + vy * FORE)
        c = acc if f in ("arms", "all") else col
        seg(sh, elbow, c)
        seg(elbow, hand, c)

    # Kopf
    hv = rot(0, -(NECK + HEAD_R), p["lean"] + p["head"])
    head = (neck_base[0] + hv[0], neck_base[1] + hv[1])
    seg(neck_base, (neck_base[0] + hv[0] * 0.45, neck_base[1] + hv[1] * 0.45),
        acc if f == "neck" else col, int(22 * S))
    hx, hy = P(*head)
    r = HEAD_R * S
    d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=col)
    # Gesicht
    face = (*BG_BOTTOM, int(255 * alpha))
    for ex in (-22, 22):
        ox, oy = rot(ex, -8, p["lean"] + p["head"])
        x, y = P(head[0] + ox, head[1] + oy)
        er = 7 * S
        d.ellipse((x - er, y - er, x + er, y + er), fill=face)
    mx, my = rot(0, 14, p["lean"] + p["head"])
    x, y = P(head[0] + mx, head[1] + my)
    mr = 20 * S
    tilt = p["lean"] + p["head"]
    d.arc((x - mr, y - mr, x + mr, y + mr), 30 + tilt, 150 + tilt, fill=face, width=int(6 * S))

    return img.resize((W, FIG_H), Image.LANCZOS)


def place_figure(frame, kind, t, dur, delay=0.0):
    a = ease_out((t - delay) / 0.5) * min(1.0, max(0.0, (dur - t) / FADE_OUT))
    if a <= 0.01:
        return
    fig = draw_figure(pose_for(kind, t))
    frame.alpha_composite(fade(fig, a), (0, FIG_TOP + int((1 - a) * 30)))


# --------------------------------------------------------------------------
# SZENEN
# --------------------------------------------------------------------------
TEXT_Y = FIG_TOP + FIG_H + 10


def draw_hook(frame, t):
    place_figure(frame, "idle", t, HOOK_DUR)
    y = TEXT_Y - 40
    for i, line in enumerate(HOOK["lines"]):
        img = text_block(line, "ExtraBold", 104, ACCENT if i == HOOK["highlight"] else TEXT)
        place(frame, img, y, t, 0.15 + i * 0.25, HOOK_DUR)
        y += 120
    place(frame, text_block(HOOK["sub"], "Medium", 50, MUTED), y + 30, t, 0.9, HOOK_DUR)


def draw_exercise(frame, t, i):
    name, how, dose, kind = EXERCISES[i]
    place_figure(frame, kind, t, EX_DUR)
    place(frame, text_block(f"ÜBUNG {i + 1} VON {len(EXERCISES)}", "SemiBold", 36, ACCENT),
          TEXT_Y, t, 0.15, EX_DUR)
    ttl = text_block(name, "ExtraBold", 92, TEXT)
    place(frame, ttl, TEXT_Y + 60, t, 0.3, EX_DUR)
    body = text_block(how, "Medium", 48, MUTED, 1.35)
    y = TEXT_Y + 60 + ttl.height + 20
    place(frame, body, y, t, 0.6, EX_DUR)
    place(frame, pill(dose), y + body.height + 40, t, 0.9, EX_DUR)


def draw_cta(frame, t):
    place_figure(frame, "cheer", t, CTA_DUR + 1)
    q = text_block(CTA["question"], "ExtraBold", 80, TEXT)
    place(frame, q, TEXT_Y - 20, t, 0.1, CTA_DUR + 1)
    y = TEXT_Y - 20 + q.height + 40
    place(frame, pill(CTA["action"], outline=False), y, t, 0.4, CTA_DUR + 1)
    place(frame, text_block(CTA["brand"], "Bold", 56, ACCENT), y + 130, t, 0.7, CTA_DUR + 1)


def render_frame(t):
    frame = draw_background(t)
    ex_end = HOOK_DUR + EX_DUR * len(EXERCISES)
    if t < HOOK_DUR:
        draw_hook(frame, t)
    elif t < ex_end:
        k = t - HOOK_DUR
        i = int(k // EX_DUR)
        draw_exercise(frame, k - i * EX_DUR, i)
    else:
        draw_cta(frame, t - ex_end)
    return frame.convert("RGB")


def main():
    out_dir = Path(__file__).parent
    if "--preview" in sys.argv:
        times = [2.5] + [HOOK_DUR + i * EX_DUR + 3.0 for i in range(len(EXERCISES))] + [TOTAL - 2]
        for k, ts in enumerate(times):
            render_frame(ts).save(out_dir / f"preview_{k}.png")
        return

    from common.audio import build_audio
    starts_ex = [HOOK_DUR + i * EX_DUR for i in range(len(EXERCISES))]
    starts = [0.3] + [s + 0.3 for s in starts_ex] + [starts_ex[-1] + EX_DUR + 0.15]
    lines = [(s, txt) for s, txt in zip(starts, VOICEOVER) if txt.strip()]
    print("Erzeuge Tonspur ...", flush=True)
    wav = build_audio(TOTAL, lines, starts_ex, HOOK_DUR, out_dir.parent / ".cache" / "lernpause.wav")

    out = out_dir / "lernpause.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
           "-shortest", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for i in range(n):
        proc.stdin.write(render_frame(i / FPS).tobytes())
        if i % (FPS * 10) == 0:
            print(f"{i / FPS:5.1f}s / {TOTAL:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("Fertig:", out)


if __name__ == "__main__":
    main()
