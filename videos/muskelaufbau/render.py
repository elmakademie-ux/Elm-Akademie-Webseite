"""
Cinematic Fitness-Reel "Muskelaufbau – Vom Anfänger zum starken Körper"
1080x1920 · 30 fps · exakt 60 s · H.264 hohe Qualitaet

Bilder:  videos/muskelaufbau/bilder/szene1.jpg ... szene6.jpg
         Mehrere Bilder pro Szene moeglich: szene2_a.jpg, szene2_b.jpg, ...
         (jpg, jpeg, png, webp). Fehlt ein Bild, wird ein Platzhalter gezeigt.

Aufruf:  python3 render.py            -> muskelaufbau.mp4
         python3 render.py --preview  -> Vorschaubilder preview_*.png
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

# ==========================================================================
# INHALT
# ==========================================================================
# Kamerafahrt pro Shot: img = Datei in bilder/, z = Zoom (von, bis),
# focus = Bildpunkt in der Mitte (x, y von 0..1) am Anfang und Ende, rot = Neigung in Grad.
SCENES = [
    dict(start=0, end=8, kicker="01", title_y=1010, title="DER ERSTE SCHRITT", sub="Jede Veränderung beginnt heute",
         voice="Jeder starke Körper beginnt mit einer Entscheidung. Heute fängst du an.",
         shots=[dict(img="pose", z=(2.1, 1.18), focus=((0.50, 0.17), (0.50, 0.42)), rot=(-1.0, 0.0))]),
    dict(start=8, end=20, kicker="02", title="HANTELTRAINING", sub="Technik vor Gewicht",
         voice="Hanteltraining. Saubere Technik vor schwerem Gewicht. "
               "Steigere dich Woche für Woche, Satz für Satz.",
         shots=[dict(img="hantel", z=(1.95, 1.60), focus=((0.80, 0.36), (0.68, 0.42)), rot=(1.0, -0.3)),
                dict(img="hantel", z=(1.70, 1.22), focus=((0.45, 0.40), (0.50, 0.48)), rot=(-0.6, 0.4))]),
    dict(start=20, end=30, kicker="03", title_y=1010, title="KNIEBEUGEN", sub="Deine Basis für echte Kraft",
         voice="Kniebeugen bauen deine Basis. Beine, Rumpf, Kraft. Alles beginnt hier.",
         shots=[dict(img="kniebeugen", z=(1.55, 1.30), focus=((0.50, 0.72), (0.58, 0.36)), rot=(0.6, -0.4))]),
    dict(start=30, end=40, kicker="04", title="ERNÄHRUNG", sub="Protein in jeder Mahlzeit",
         voice="Muskeln wachsen nicht nur im Training. Iss genug Protein, bei jeder Mahlzeit.",
         shots=[dict(img="regeneration", z=(2.2, 1.75), focus=((0.57, 0.66), (0.52, 0.58)), rot=(0.8, -0.2))]),
    dict(start=40, end=50, kicker="05", title_y=1010, title="REGENERATION", sub="Wachstum passiert in der Pause",
         voice="Und gib deinem Körper Ruhe. Im Schlaf wirst du stärker.",
         shots=[dict(img="regeneration", z=(1.28, 1.12), focus=((0.40, 0.32), (0.50, 0.45)), rot=(0.0, 0.0))]),
    dict(start=50, end=60, kicker="06", title_y=1010, title="STARK WERDEN", sub="",
         voice="Bleib dran. Aus dem Anfänger von heute wird der starke Körper von morgen.",
         shots=[dict(img="pose", z=(1.15, 1.50), focus=((0.50, 0.58), (0.50, 0.33)), rot=(0.8, 0.0))]),
]
FINAL_LINES = ["VOM ANFÄNGER", "ZUM STARKEN", "KÖRPER"]   # ab Sekunde 55
BRAND = "ELM-AKADEMIE"   # leer lassen = keine Marke im Abspann

# Look
ACCENT = (255, 168, 64)        # warmes Orange
TEXT = (250, 248, 244)
SUB_BG = (0, 0, 0, 150)

# ==========================================================================
# TECHNIK
# ==========================================================================
W, H, FPS, TOTAL = 1080, 1920, 30, 60.0
N_FRAMES = int(TOTAL * FPS)
K = 1.5            # Aufloesungsreserve der Quellbilder (fuer scharfe Zooms)
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
CUT = 0.28         # Dauer der Zoom-Punch-Uebergaenge (je Seite)


@lru_cache(None)
def font(weight, size):
    p = FONT_DIR / f"Inter-{weight}.otf"
    return ImageFont.truetype(str(p if p.exists() else FONT_DIR / "Inter-Regular.otf"), size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = clamp(t)
    return t ** 3


def speed_ramp(u):
    """Schneller Anfang, danach langsames Gleiten (Zeitlupen-Gefuehl)."""
    u = clamp(u)
    fast = 0.42 * ease_out(u / 0.12)
    slow = 0.58 * clamp((u - 0.04) / 0.96)
    return fast + slow


def comp(frame, img, pos=(0, 0)):
    """alpha_composite, das auch Positionen ausserhalb des Bildes verkraftet."""
    x, y = int(pos[0]), int(pos[1])
    l, t = max(0, -x), max(0, -y)
    r, b = min(img.width, frame.width - x), min(img.height, frame.height - y)
    if r <= l or b <= t:
        return
    if (l, t, r, b) != (0, 0, img.width, img.height):
        img = img.crop((l, t, r, b))
    frame.alpha_composite(img, (x + l, y + t))


# --------------------------------------------------------------- Bilder
def grade(img):
    """Filmischer Look: S-Kurve, Teal-Schatten, warme Lichter, leicht entsaettigt."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255
    s = a * a * (3 - 2 * a)
    a = a * 0.62 + s * 0.38
    lum = (a @ np.array([0.299, 0.587, 0.114], dtype=np.float32))[..., None]
    a += (1 - lum) ** 2 * np.array([-0.035, 0.015, 0.045], dtype=np.float32)
    a += lum ** 2 * np.array([0.055, 0.02, -0.04], dtype=np.float32)
    a = lum + (a - lum) * 0.86
    a = np.clip(a * 0.96, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


def placeholder(idx, scene):
    """Platzhalter, solange kein echtes Bild vorhanden ist."""
    w, h = int(W * K), int(H * K)
    hues = [(40, 26, 20), (20, 28, 40), (30, 30, 34), (36, 30, 18), (18, 30, 36), (40, 24, 16)]
    c = hues[idx % len(hues)]
    g = Image.linear_gradient("L").resize((w, h))
    base = Image.merge("RGB", [g.point(lambda v, k=k: int(c[k] * 2.2 * (1 - v / 255) + c[k] * 0.4))
                               for k in range(3)])
    d = ImageDraw.Draw(base)
    for k in range(14):  # Streifen fuer sichtbare Bewegung
        x = int(w * (k / 14))
        d.line((x, 0, x + w // 3, h), fill=tuple(min(255, v + 18) for v in c), width=6)
    f1, f2 = font("ExtraBold", 110), font("Medium", 56)
    for txt, f, y in (("BILD FEHLT", f1, h * 0.42), (f"bilder/szene{idx + 1}.jpg", f2, h * 0.42 + 150),
                      (scene["title"], f2, h * 0.42 + 240)):
        d.text(((w - f.getlength(txt)) / 2, y), txt, font=f, fill=(200, 200, 200))
    return base


@lru_cache(None)
def load_image(name, si):
    folder = HERE / "bilder"
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = folder / f"{name}{ext}"
        if p.exists():
            img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
            img = ImageOps.fit(img, (int(W * K), int(H * K)), Image.LANCZOS)
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
            return grade(img)
    return grade(placeholder(si, SCENES[si]))


# Shots aufbauen: (start, end, bild, bewegung, szenen-index)
SHOTS = []


def build_shots():
    for si, sc in enumerate(SCENES):
        n = len(sc["shots"])
        dur = (sc["end"] - sc["start"]) / n
        for k, mv in enumerate(sc["shots"]):
            SHOTS.append(dict(start=sc["start"] + k * dur, end=sc["start"] + (k + 1) * dur,
                              img=load_image(mv["img"], si), mv=mv, scene=si))


# --------------------------------------------------------------- Kamera
def camera(shot, t):
    """Affine Kamerafahrt: Zoom, Pan, leichte Rotation mit Speed-Ramp."""
    mv = shot["mv"]
    dur = shot["end"] - shot["start"]
    lt = t - shot["start"]
    u = speed_ramp(lt / dur)
    z = mv["z"][0] + (mv["z"][1] - mv["z"][0]) * u
    (px0, py0), (px1, py1) = mv["focus"]
    px, py = px0 + (px1 - px0) * u, py0 + (py1 - py0) * u
    rot = mv["rot"][0] + (mv["rot"][1] - mv["rot"][0]) * u
    # Punch-Zoom an Schnitten
    z *= 1 + 0.22 * ease_in((lt - (dur - CUT)) / CUT)       # raus
    z *= 1 + 0.16 * (1 - ease_out(lt / (CUT * 1.6)))          # rein
    # Handkamera-Feeling (sehr dezent)
    px += 0.004 * math.sin(t * 1.7) + 0.002 * math.sin(t * 4.1)
    py += 0.003 * math.cos(t * 1.3)
    rot += 0.25 * math.sin(t * 0.9)
    return z, px, py, rot


def render_shot(shot, t, extra_zoom=1.0):
    img = shot["img"]
    z, px, py, rot = camera(shot, t)
    z *= extra_zoom
    s = K / z
    sw, sh = img.size
    win_w, win_h = W * s, H * s
    # freier Bewegungsraum (mit Reserve fuer Rotation)
    mx, my = win_w / 2 + 40, win_h / 2 + 40
    cx = min(max(px * sw, mx), sw - mx) if sw > 2 * mx else sw / 2
    cy = min(max(py * sh, my), sh - my) if sh > 2 * my else sh / 2
    th = math.radians(rot)
    a, b = s * math.cos(th), -s * math.sin(th)
    d, e = s * math.sin(th), s * math.cos(th)
    c = cx - a * W / 2 - b * H / 2
    f = cy - d * W / 2 - e * H / 2
    return img.transform((W, H), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BILINEAR)


def zoom_blur(frame, amount):
    if amount < 0.02:
        return frame
    acc = np.asarray(frame, dtype=np.float32)
    n = 4
    for k in range(1, n):
        sc = 1 + 0.035 * amount * k
        big = frame.resize((int(W * sc), int(H * sc)), Image.BILINEAR)
        x0, y0 = (big.width - W) // 2, (big.height - H) // 2
        acc += np.asarray(big.crop((x0, y0, x0 + W, y0 + H)), dtype=np.float32)
    return Image.fromarray((acc / n).astype(np.uint8))


# --------------------------------------------------------------- Overlays
def make_vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H * 0.48) / (H * 0.6)) ** 2)
    a = np.clip((r - 0.45) * 1.5, 0, 1) ** 1.6 * 215
    v = np.zeros((H, W, 4), np.uint8)
    v[..., 3] = a.astype(np.uint8)
    # oben/unten zusaetzlich abdunkeln fuer Lesbarkeit
    grad = np.zeros(H, np.float32)
    grad[:500] = np.linspace(110, 0, 500)
    grad[-650:] = np.linspace(0, 150, 650)
    v[..., 3] = np.clip(v[..., 3].astype(np.float32) + grad[:, None], 0, 255).astype(np.uint8)
    return Image.fromarray(v, "RGBA")


def make_leak(size=1500):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    r = np.sqrt((x - size / 2) ** 2 + (y - size / 2) ** 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** 2.2 * 120
    img = np.zeros((size, size, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = 255, 140, 50
    img[..., 3] = a.astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def make_bokeh(r):
    img = Image.new("RGBA", (2 * r + 8, 2 * r + 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((4, 4, 4 + 2 * r, 4 + 2 * r), fill=(255, 210, 150, 255))
    return img.filter(ImageFilter.GaussianBlur(max(1, r // 3)))


VIGNETTE = make_vignette()
LEAK = make_leak()
RNG = np.random.default_rng(7)
PARTICLES = [dict(x=RNG.uniform(0, W), y=RNG.uniform(0, H), depth=RNG.uniform(0.2, 1.0),
                  r=int(RNG.uniform(3, 22)), a=RNG.uniform(0.12, 0.45), ph=RNG.uniform(0, 6.28))
             for _ in range(38)]
BOKEH = {}
GRAIN = [RNG.normal(0, 7, (H // 2, W // 2)).astype(np.int16) for _ in range(6)]


def draw_particles(frame, t, pan_x, pan_y):
    """Parallax-Ebene: Staub/Lichtpartikel bewegen sich je nach Tiefe schneller als das Bild."""
    for p in PARTICLES:
        sp = 0.4 + 1.8 * p["depth"]
        x = (p["x"] - pan_x * 900 * sp + 12 * math.sin(t * 0.6 + p["ph"])) % (W + 100) - 50
        y = (p["y"] - t * 22 * sp - pan_y * 900 * sp) % (H + 100) - 50
        r = max(2, int(p["r"] * (0.5 + p["depth"])))
        if r not in BOKEH:
            BOKEH[r] = make_bokeh(r)
        spr = BOKEH[r]
        a = p["a"] * (0.6 + 0.4 * math.sin(t * 1.3 + p["ph"]))
        layer = spr.copy()
        layer.putalpha(spr.getchannel("A").point(lambda v, a=a: int(v * a)))
        comp(frame, layer, (int(x), int(y)))


# --------------------------------------------------------------- Text
@lru_cache(None)
def tracked_text(text, weight, size, color, tracking=0.06):
    f = font(weight, size)
    sp = size * tracking
    widths = [f.getlength(ch) for ch in text]
    tw = int(sum(widths) + sp * (len(text) - 1)) + 4
    img = Image.new("RGBA", (tw, int(size * 1.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 0
    for ch, w in zip(text, widths):
        d.text((x, 0), ch, font=f, fill=color)
        x += w + sp
    return img


def fit_title(text, weight="ExtraBold", max_w=W - 160, size=118):
    while size > 50:
        img = tracked_text(text, weight, size, TEXT)
        if img.width <= max_w:
            return img
        size -= 4
    return tracked_text(text, weight, size, TEXT)


def with_alpha(img, a):
    if a >= 0.999:
        return img
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return out


def shadowed(img, blur=14, alpha=170):
    pad = blur * 3
    sh = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    mask = img.getchannel("A").point(lambda v: int(v * alpha / 255))
    sh.paste((0, 0, 0, 255), (pad, pad + 4), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(img, (pad, pad))
    return sh, pad


def draw_scene_title(frame, si, lt, dur):
    sc = SCENES[si]
    a_out = clamp((dur - lt - 0.15) / 0.35)
    if si == len(SCENES) - 1 and lt > 4.6:
        a_out = clamp((5.2 - lt) / 0.4)
    y = sc.get("title_y", 300)
    # Kicker "02 / 06" + wachsende Linie
    kick = tracked_text(f"{sc['kicker']} / {len(SCENES):02d}", "Bold", 38, ACCENT, 0.18)
    a = ease_out((lt - 0.25) / 0.4) * a_out
    if a > 0.01:
        comp(frame, with_alpha(kick, a), ((W - kick.width) // 2, y))
        lw = int(140 * ease_out((lt - 0.3) / 0.6))
        ImageDraw.Draw(frame).rectangle(((W - lw) // 2, y + 62, (W + lw) // 2, y + 67),
                                        fill=(*ACCENT, int(255 * a)))
    # Titel: von unten hereingleiten, leicht "atmend" skaliert
    ttl = fit_title(sc["title"])
    tin = ease_out((lt - 0.4) / 0.55)
    a = tin * a_out
    if a > 0.01:
        sh, pad = shadowed(ttl)
        scale = 1.0 + 0.04 * (1 - tin) + 0.012 * lt / dur
        if abs(scale - 1) > 0.002:
            sh = sh.resize((int(sh.width * scale), int(sh.height * scale)), Image.BILINEAR)
        comp(frame, with_alpha(sh, a),
                              ((W - sh.width) // 2, int(y + 95 - pad * scale + 50 * (1 - tin))))
    if sc["sub"]:
        sub = tracked_text(sc["sub"], "Medium", 46, (235, 230, 222), 0.02)
        a = ease_out((lt - 0.8) / 0.5) * a_out
        if a > 0.01:
            sh, pad = shadowed(sub, 10, 200)
            comp(frame, with_alpha(sh, a), ((W - sh.width) // 2, y + 250 - pad))


def draw_final(frame, lt):
    """Abschluss-Statement ab Sekunde 55 der letzten Szene."""
    start = 5.0
    if lt < start:
        return
    dim = ease_out((lt - start + 0.2) / 0.6)
    comp(frame, Image.new("RGBA", (W, H), (0, 0, 0, int(110 * dim))))
    y = 640
    for k, line in enumerate(FINAL_LINES):
        col = ACCENT if k == len(FINAL_LINES) - 1 else TEXT
        img = fit_title(line, size=124) if col == TEXT else tracked_text(line, "ExtraBold", 124, col)
        tin = ease_out((lt - start - 0.15 * k) / 0.45)
        if tin <= 0.01:
            continue
        sh, pad = shadowed(img, 16, 190)
        sc = 1 + 0.25 * (1 - tin)
        sh = sh.resize((int(sh.width * sc), int(sh.height * sc)), Image.BILINEAR)
        comp(frame, with_alpha(sh, tin), ((W - sh.width) // 2, int(y - pad * sc)))
        y += 150
    if BRAND:
        a = ease_out((lt - start - 1.0) / 0.6)
        if a > 0.01:
            b = tracked_text(BRAND, "Bold", 44, TEXT, 0.3)
            comp(frame, with_alpha(b, a * 0.9), ((W - b.width) // 2, y + 40))


# --------------------------------------------------------------- Untertitel
SUBS = []  # (start, end, text) - wird nach der Tonspur gefuellt


def chunk_text(text, max_chars=24):
    words, chunks, cur = text.split(), [], ""
    for w in words:
        if cur and (len(cur) + 1 + len(w) > max_chars or cur.endswith((".", ",", "?", "!"))):
            chunks.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return chunks + ([cur] if cur else [])


def build_subs(lines_with_timing):
    for start, dur, text in lines_with_timing:
        chunks = chunk_text(text)
        weights = [len(c) + (6 if c.endswith((".", "?", "!")) else 3 if c.endswith(",") else 0)
                   for c in chunks]
        tot, t = sum(weights), start
        for c, w in zip(chunks, weights):
            d = dur * w / tot
            SUBS.append((t, t + d, c))
            t += d


@lru_cache(None)
def sub_img(text):
    f = font("Bold", 54)
    tw = int(f.getlength(text))
    img = Image.new("RGBA", (tw + 60, 92), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, tw + 60, 92), 18, fill=SUB_BG)
    bb = f.getbbox(text)
    d.text((30, 46 - (bb[1] + bb[3]) / 2), text, font=f, fill=TEXT)
    return img


def draw_subs(frame, t):
    for s, e, txt in SUBS:
        if s <= t < e:
            img = sub_img(txt)
            a = clamp((t - s) / 0.08) * clamp((e - t) / 0.08 + 0.3)
            pop = 1 + 0.06 * (1 - ease_out((t - s) / 0.15))
            if pop > 1.001:
                img = img.resize((int(img.width * pop), int(img.height * pop)), Image.BILINEAR)
            comp(frame, with_alpha(img, a), ((W - img.width) // 2, 1400 - img.height // 2))
            break


# --------------------------------------------------------------- Frame
def shot_at(t):
    for k, sh in enumerate(SHOTS):
        if sh["start"] <= t < sh["end"]:
            return k, sh
    return len(SHOTS) - 1, SHOTS[-1]


def render_frame(i):
    t = i / FPS
    k, shot = shot_at(t)
    frame = render_shot(shot, t).convert("RGBA")
    lt = t - shot["start"]
    dur = shot["end"] - shot["start"]
    # Zoom-Blur an den Schnitten
    blur = max(ease_in((lt - (dur - CUT)) / CUT), 1 - ease_out(lt / CUT)) if 0 < k or lt > CUT else 0
    if t > TOTAL - 1.0:
        blur = 0
    if blur > 0.02:
        frame = zoom_blur(frame.convert("RGB"), blur).convert("RGBA")

    _, px, py, _ = camera(shot, t)
    draw_particles(frame, t, px * 0.6, py * 0.6)

    # Light Leak: warmes Licht wandert beim Szenenwechsel durchs Bild
    scene = SCENES[shot["scene"]]
    st = t - scene["start"]
    if st < 1.2 or shot["scene"] in (0, 5):
        sweep = st / 1.2 if st < 1.2 else 0.5 + 0.1 * math.sin(t * 0.5)
        lx = int(-700 + (W + 200) * sweep)
        a = (1 - clamp(st / 1.2)) * 0.9 if st < 1.2 else 0.35
        comp(frame, with_alpha(LEAK, a), (lx, 250 + int(200 * math.sin(t * 0.3))))

    comp(frame, VIGNETTE)
    draw_scene_title(frame, shot["scene"], st, scene["end"] - scene["start"])
    if shot["scene"] == len(SCENES) - 1:
        draw_final(frame, st)
    draw_subs(frame, t)

    # Weisser Blitz am Szenenanfang
    if 0 < scene["start"] and st < 0.25:
        flash = Image.new("RGBA", (W, H), (255, 245, 235, int(150 * (1 - st / 0.25))))
        comp(frame, flash)
    # Ein-/Ausblenden
    fade_a = min(clamp(t / 0.6), clamp((TOTAL - t) / 0.8))

    arr = np.asarray(frame.convert("RGB"), dtype=np.int16)
    g = GRAIN[i % len(GRAIN)]
    arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    if fade_a < 1:
        arr = (arr * fade_a).astype(np.int16)
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


# ==========================================================================
# AUDIO: motivierende Musik (selbst erzeugt) + Sprecher
# ==========================================================================
SR = 44100
BPM = 120  # 1 Takt = 2 s -> alle Szenenwechsel liegen auf Taktanfaengen


def band_noise(n, lo, hi, seed=0):
    x = np.random.default_rng(seed).standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (fr / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def mtof(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def make_music():
    from common.audio import add
    n_total = int(TOTAL * SR) + SR * 3
    buf = np.zeros(n_total)
    drums = np.zeros(n_total)
    beat = 60 / BPM
    bar = 4 * beat
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G

    def env(n, a, d):
        t = np.arange(n) / SR
        return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t * d)

    def kick(amp=1.0):
        n = int(0.5 * SR)
        t = np.arange(n) / SR
        f = 45 + 110 * np.exp(-t * 30)
        return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)

    snare_n = band_noise(int(0.3 * SR), 1200, 7000, 3)
    hat_n = band_noise(int(0.08 * SR), 7000, 15000, 4)

    def snare(amp=1.0):
        n = len(snare_n)
        t = np.arange(n) / SR
        return amp * (0.7 * snare_n * np.exp(-t * 16) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 22))

    def hat(amp=1.0):
        return amp * hat_n * np.exp(-np.arange(len(hat_n)) / SR * 55)

    def section(t):
        if t < 8:
            return "intro"
        if t < 40:
            return "drive"
        if t < 50:
            return "calm"
        return "final"

    t = 0.0
    bi = 0
    while t < TOTAL:
        ch = chords[bi % 4]
        sec = section(t)
        # Flaechen (Pad)
        n = int((bar + 1.5) * SR)
        tt = np.arange(n) / SR
        penv = np.minimum(1, tt / 0.6) * np.minimum(1, (n / SR - tt) / 1.2)
        for note in ch:
            for det in (-0.004, 0.004):
                f0 = mtof(note) * (1 + det)
                sig = sum(np.sin(2 * np.pi * f0 * h * tt) / h ** 1.6 for h in range(1, 5))
                add(buf, 0.035 * penv * sig, t)
        # Bass
        root = mtof(ch[0] - 24)
        if sec in ("drive", "final"):
            for k in range(8):  # Achtel-Puls
                nn = int(beat / 2 * SR)
                tt = np.arange(nn) / SR
                sig = sum(np.sin(2 * np.pi * root * h * tt) / h for h in range(1, 7))
                add(buf, 0.10 * sig * env(nn, 0.005, 7), t + k * beat / 2)
        else:
            nn = int(bar * SR)
            tt = np.arange(nn) / SR
            sig = sum(np.sin(2 * np.pi * root * h * tt) / h ** 2 for h in range(1, 4))
            add(buf, 0.12 * sig * env(nn, 0.3, 0.6), t)
        # Arpeggio / Ostinato
        if sec in ("drive", "final", "calm"):
            step = beat / 4 if sec != "calm" else beat / 2
            notes = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24]
            k = 0
            while k * step < bar - 1e-6:
                nn = int(0.35 * SR)
                tt = np.arange(nn) / SR
                f0 = mtof(notes[k % 4])
                sig = np.sin(2 * np.pi * f0 * tt) + 0.3 * np.sin(4 * np.pi * f0 * tt)
                amp = 0.022 if sec != "calm" else 0.04
                add(buf, amp * sig * env(nn, 0.003, 11), t + k * step)
                k += 1
        # Schlagzeug
        for b in range(4):
            bt = t + b * beat
            if sec == "intro":
                if b in (0, 2) and t >= 2:  # Herzschlag
                    add(drums, kick(0.8), bt)
                    add(drums, kick(0.45), bt + 0.22)
            elif sec == "calm":
                if b == 0:
                    add(drums, kick(0.5), bt)
            else:
                add(drums, kick(1.0), bt)
                if b in (1, 3):
                    add(drums, snare(0.55), bt)
                for hh in range(2 if sec == "drive" else 4):
                    add(drums, hat(0.12 if hh % 2 else 0.2), bt + hh * beat / (2 if sec == "drive" else 4))
        t += bar
        bi += 1

    # Riser vor grossen Wechseln, Whoosh vor allen Szenenwechseln, Impact auf dem Wechsel
    def riser(at, length, amp):
        n = int(length * SR)
        tt = np.arange(n) / SR
        nz = band_noise(n, 800, 9000, int(at))
        swell = (tt / length) ** 2.2
        f = 200 + 1000 * (tt / length) ** 2
        tone_ = np.sin(2 * np.pi * np.cumsum(f) / SR)
        add(buf, amp * swell * (0.6 * nz + 0.25 * tone_), at - length)

    def impact(at, amp):
        n = int(3.0 * SR)
        tt = np.arange(n) / SR
        f = 32 + 50 * np.exp(-tt * 6)
        boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.6)
        nz = lowpass(band_noise(n, 30, 5000, int(at) + 99), 1800) * np.exp(-tt * 5)
        add(buf, amp * (boom + 0.5 * nz), at)

    for sc in SCENES[1:]:
        big = sc["start"] in (8, 50)
        riser(sc["start"], 2.0 if big else 0.7, 0.35 if big else 0.18)
        impact(sc["start"], 0.7 if big else 0.45)
    impact(55.0, 0.5)  # Akzent zum Schluss-Statement

    mix = buf + 0.9 * drums
    mix = mix[: int(TOTAL * SR)]
    fi, fo = int(0.5 * SR), int(1.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.4)
    return mix / (np.abs(mix).max() + 1e-9)


def build_audio(out_wav):
    import wave
    from common.audio import add, ensure_voice, speak
    music = make_music() * 0.32
    voice = np.zeros_like(music)
    model = ensure_voice()
    timings = []
    tmp = HERE.parent / ".cache" / "line_mk.wav"
    for si, sc in enumerate(SCENES):
        start = sc["start"] + (0.7 if si == 0 else 0.45)
        seg = speak(sc["voice"], tmp, model)
        # Stimme etwas voller: leichte Bassanhebung
        seg = seg + 0.25 * lowpass(seg, 220)
        seg /= np.abs(seg).max() + 1e-9
        d = len(seg) / SR
        if start + d > sc["end"] - 0.15:
            print(f"Warnung: Szene {si + 1}: Sprechtext {d:.1f}s ist zu lang fuer die Szene.")
        add(voice, 0.95 * seg, start)
        # Untertitel-Timing ohne Stille am Ende
        nz = np.nonzero(np.abs(seg) > 0.02)[0]
        speech_end = (nz[-1] / SR) if len(nz) else d
        timings.append((start, speech_end, sc["voice"]))

    win = int(0.2 * SR)
    envv = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
    envv = np.clip(envv / (envv.max() + 1e-9) * 6, 0, 1)
    envv = np.convolve(envv, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
    mix = music * (1 - 0.5 * envv) + voice
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.9
    pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return timings


# ==========================================================================
def main():
    build_shots()
    cache = HERE.parent / ".cache"
    cache.mkdir(exist_ok=True)
    wav = cache / "muskelaufbau.wav"
    print("Erzeuge Tonspur ...", flush=True)
    build_subs(build_audio(wav))

    if "--preview" in sys.argv:
        for k, ts in enumerate([1.5, 4.0, 9.0, 16.0, 24.0, 33.0, 44.0, 52.0, 57.5]):
            Image.frombytes("RGB", (W, H), render_frame(int(ts * FPS))).save(HERE / f"preview_{k}.png")
        return

    out = HERE / "muskelaufbau.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav),
           "-c:v", "libx264", "-preset", "slow", "-b:v", "11M", "-maxrate", "14M", "-bufsize", "22M",
           "-profile:v", "high", "-tune", "grain",
           "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
           "-t", str(TOTAL), "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, data in enumerate(pool.imap(render_frame, range(N_FRAMES), chunksize=8)):
            proc.stdin.write(data)
            if i % (FPS * 10) == 0:
                print(f"{i / FPS:5.1f}s / {TOTAL:.0f}s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("Fertig:", out)


if __name__ == "__main__":
    main()
