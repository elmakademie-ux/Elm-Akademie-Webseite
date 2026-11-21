#!/usr/bin/env python3
"""Kostenloser 2D-Renderer: Drehbuch + Piper-Audio -> 9:16-MP4 (1080x1920, 30 fps).

  python3 scripts/render2d.py A1 A2 B1 B2        alle Videos (parallel, je Video ein Prozess)
  python3 scripts/render2d.py A1 --still 5,20    nur Standbilder (output/stills/) zur Kontrolle

Voraussetzungen: scripts/make_audio.py und scripts/build.py wurden ausgeführt (Audio + durations.json),
ffmpeg ist installiert. Es werden keine externen Dienste verwendet.
Ausgabe: videos/<N>/<N>_9x16.mp4 und videos/<N>/<N>_9x16.srt (gleiche Zeiten wie im Video).
"""
from __future__ import annotations

import math
import re
import subprocess
import sys
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from anim_art import BACKGROUNDS, BG_MARGIN, H, W, Character, paste_character
from lib import *  # noqa: F401,F403

FPS = 30
SR = 44100
ELM_BLUE = (27, 54, 104)
ORANGE = (237, 140, 20)
GREEN = (46, 160, 90)
INK = (27, 54, 104)
SPEAKER_COLOR = {"mia": (233, 74, 120), "jonas": (0, 150, 136), "narrator": (124, 77, 255)}
SHEET_TOP = 1480
ENDCARD_SEC = 4.0
LOGO = ROOT.parent / "videos" / "dtz_email" / "bilder" / "logo.png"

SCENE_BG = {
    "A1": {"S01": "park_morning", "S02": "learn0", "S03": "park_morning", "S04": "park_morning", "S05": "park_morning",
           "S06": "park_day", "S10": "park_day"},
    "A2": {"S01": "entrance", "S03": "kitchen", "S04": "kitchen", "S05": "kitchen", "S06": "kitchen",
           "S07": "corridor", "S11": "terrace"},
    "B1": {"S01": "party", "S03": "party", "S04": "sofa", "S05": "sofa", "S06": "balcony", "S10": "balcony_night"},
    "B2": {"S01": "foyer", "S03": "foyer", "S04": "foyer", "S05": "foyer", "S06": "foyer", "S10": "foyer"},
}
LEARN_TYPES = ("intro", "vocab", "grammar", "exercise")
GREETING = re.compile(r"\b(Hallo|Tschüss|Guten Morgen|Auf Wiedersehen|Bis bald|Bis zum nächsten)\b")

_fonts: dict = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in _fonts:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        _fonts[key] = ImageFont.truetype(name, size)
    return _fonts[key]


def text_w(txt, f):
    return f.getlength(txt)


def wrap_px(txt, f, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rr_sprite(w, h, r, fill, shadow=True):
    ss = 3
    pad = 24 if shadow else 0
    im = Image.new("RGBA", ((w + 2 * pad) * ss, (h + 2 * pad) * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.rounded_rectangle([pad * ss, (pad + 8) * ss, (pad + w) * ss, (pad + h + 8) * ss], radius=r * ss, fill=(0, 20, 60, 50))
    d.rounded_rectangle([pad * ss, pad * ss, (pad + w) * ss, (pad + h) * ss], radius=r * ss, fill=fill)
    return im.resize((w + 2 * pad, h + 2 * pad), Image.LANCZOS), pad


# ------------------------------------------------------------------ Audio
def read_wav(path):
    with wave.open(str(path)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    if sr != SR:
        xn = np.arange(int(len(x) * SR / sr)) / SR
        x = np.interp(xn, np.arange(len(x)) / sr, x)
    return x


def build_audio(script, timeline, total, out_wav):
    from common.audio import make_music  # vorhandener, selbst erzeugter Musikgenerator (keine Lizenzfragen)
    n = int(total * SR)
    per = {sp: np.zeros(n, dtype=np.float32) for sp in ("mia", "jonas", "narrator")}
    for e in timeline:
        wav = ROOT / "audio" / script["level"] / f"{e['line_id']}_{e['speaker']}.wav"
        x = read_wav(wav)
        i = int(e["start"] * SR)
        x = x[: max(0, n - i)]
        per[e["speaker"]][i:i + len(x)] += x
    voice = sum(per.values())
    music = make_music(total, [], 10 ** 6).astype(np.float32)[:n] * 0.16
    if len(music) < n:
        music = np.pad(music, (0, n - len(music)))
    win = int(0.3 * SR)
    env = np.convolve(np.abs(voice), np.ones(win) / win, mode="same")
    env = np.clip(env / (env.max() + 1e-9) * 8, 0, 1)
    env = np.convolve(env, np.ones(int(0.4 * SR)) / int(0.4 * SR), mode="same")
    mix = music * (1 - 0.6 * env) + voice * 0.95
    mix = np.tanh(mix * 1.1)
    mix *= 0.9 / (np.abs(mix).max() + 1e-9)
    pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    # Mund-Hüllkurven je Sprecher (pro Videobild)
    nf = int(total * FPS) + 1
    envs = {}
    for sp, arr in per.items():
        w_ = SR // FPS
        c = np.abs(arr)
        pad = np.pad(c, (w_, w_ + SR))
        cs = np.cumsum(pad)
        idx = (np.arange(nf) * SR / FPS).astype(int) + w_
        rms = (cs[idx + w_ // 2] - cs[idx - w_ // 2]) / w_
        envs[sp] = np.clip(rms / (np.percentile(rms[rms > 0], 90) * 1.1 + 1e-9), 0, 1) if (rms > 0).any() else rms
    return envs


# ------------------------------------------------------------------ Szenenplan
def plan_scenes(script, timeline):
    lv = script["level"]
    scenes = []
    learn_i = 0
    for s in script["scenes"]:
        key = s["id"].split("-")[1]
        if s["type"] in LEARN_TYPES:
            bg = f"learn{learn_i % 3}"
            if s["type"] == "intro":
                bg = "learn0"
            learn_i += 1 if s["type"] != "intro" else 0
        else:
            bg = SCENE_BG[lv][key]
        lines = [e for e in timeline if e["scene"] == s["id"]]
        sc = {"id": s["id"], "type": s["type"], "title": s["title"], "bg": bg, "chars": [c for c in s["characters"] if c in ("mia", "jonas")],
              "start": s["_start"], "end": s["_end"], "lines": lines, "items": s.get("on_screen", []), "idx": len(scenes)}
        sc["reveal"] = schedule_items(sc)
        scenes.append(sc)
    return scenes


def schedule_items(sc):
    items, lines = sc["items"], sc["lines"]
    m, n = len(items), len(lines)
    if not m:
        return []
    if sc["type"] == "exercise":
        q = [i for i, l in enumerate(lines) if re.match(r"^(Eins|Zwei|Drei|Vier|Fünf)\b", l["text"])]
        a = [i for i, l in enumerate(lines) if re.match(r"^(Richtig|Lösung|Zum Beispiel)", l["text"])]
        out = []
        for k, it in enumerate(items):
            left, right = (it.split("→", 1) + [None])[:2] if "→" in it else (it, None)
            t_show = lines[q[k]]["start"] if k < len(q) else sc["start"]
            t_ans = lines[a[k]]["start"] if (right and k < len(a)) else None
            out.append({"t": t_show, "left": left.strip(), "right": right.strip() if right else None, "t_ans": t_ans})
        return out
    off = 1 if sc["type"] == "vocab" and n > 1 else 0
    span = n - off
    out = []
    for k, it in enumerate(items):
        li = min(n - 1, off + int(k * span / m))
        out.append({"t": lines[li]["start"], "left": it, "right": None, "t_ans": None})
    return out


# ------------------------------------------------------------------ Overlays
class Overlays:
    def __init__(self, script):
        self.lv = script["level"]
        self.sheet = self._sheet()
        self.cache = {}
        self.logo = self._logo(112)

    def _sheet(self):
        im = Image.new("RGBA", (W, H - SHEET_TOP + 40), (0, 0, 0, 0))
        ss = 2
        big = Image.new("RGBA", (im.width * ss, im.height * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        d.rounded_rectangle([0, 0, big.width, big.height + 200], radius=60 * ss, fill=ELM_BLUE)
        d.rounded_rectangle([0, 0, big.width, 14 * ss], radius=7 * ss, fill=ORANGE)
        return big.resize(im.size, Image.LANCZOS)

    def _logo(self, w):
        if not LOGO.exists():
            return None
        lg = Image.open(LOGO).convert("RGB")
        h = int(lg.height * w / lg.width)
        lg = lg.resize((w, h), Image.LANCZOS)
        mask = Image.new("L", lg.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=14, fill=255)
        out = lg.convert("RGBA")
        out.putalpha(mask)
        return out

    def header(self, sc):
        key = ("hdr", sc["id"])
        if key not in self.cache:
            f = font(34)
            title = sc["title"]
            tw = int(text_w(title, f)) + 40
            w = min(W - 40 - 112 - 70 - 70, tw + 90)
            sp, pad = rr_sprite(w + 90, 64, 32, ELM_BLUE + (235,), shadow=True)
            d = ImageDraw.Draw(sp)
            d.rounded_rectangle([pad + 6, pad + 6, pad + 84, pad + 58], radius=26, fill=ORANGE)
            d.text((pad + 45, pad + 32), self.lv, font=font(32), fill=(255, 255, 255), anchor="mm")
            fit = font(34)
            while text_w(title, fit) > w - 30 and fit.size > 22:
                fit = font(fit.size - 2)
            d.text((pad + 100, pad + 32), title, font=fit, fill=(255, 255, 255), anchor="lm")
            self.cache[key] = sp
        return self.cache[key]

    def card(self, text):
        key = ("card", text)
        if key not in self.cache:
            maxw = 880
            size = 72
            while True:
                f = font(size)
                lines = []
                for part in text.split("\n"):
                    lines += wrap_px(part, f, maxw)
                if len(lines) <= 3 or size <= 44:
                    break
                size -= 4
            lh = int(size * 1.25)
            h = lh * len(lines) + 70
            w = int(min(960, max(text_w(l, f) for l in lines) + 120))
            sp, pad = rr_sprite(w, h, 40, (255, 255, 255, 245))
            d = ImageDraw.Draw(sp)
            d.rounded_rectangle([pad, pad + 30, pad + 14, pad + h - 30], radius=7, fill=ORANGE)
            for i, l in enumerate(lines):
                d.text((pad + w / 2 + 6, pad + 35 + i * lh + lh / 2), l, font=f, fill=INK, anchor="mm")
            self.cache[key] = sp
        return self.cache[key]

    def board(self, state):
        """state: Liste (left, right, ans_shown) + Index des neuesten Eintrags."""
        items, newest = state
        key = ("board", tuple(items), newest)
        if key in self.cache:
            return self.cache[key]
        maxh = 700
        size = 54
        maxw = 840
        while True:
            f = font(size)
            fa = font(size)
            layout, total = [], 0
            gap = int(size * 0.5)
            for left, right, shown in items:
                ls = wrap_px(left, f, maxw)
                rs = wrap_px("→ " + right, fa, maxw) if right else []
                hh = int((len(ls) + len(rs)) * size * 1.22)
                layout.append((ls, rs, shown, hh))
                total += hh + gap
            if total + 60 <= maxh or size <= 30:
                break
            size -= 2
        h = total + 50
        sp, pad = rr_sprite(960, h, 44, (255, 255, 255, 240))
        d = ImageDraw.Draw(sp)
        y = pad + 30
        for i, (ls, rs, shown, hh) in enumerate(layout):
            if i == newest:
                d.rounded_rectangle([pad + 16, y - 10, pad + 944, y + hh + 6], radius=20, fill=(255, 238, 210))
            d.ellipse([pad + 36, y + size * 0.3, pad + 36 + size * 0.38, y + size * 0.3 + size * 0.38], fill=ORANGE)
            ty = y
            for l in ls:
                d.text((pad + 36 + size * 0.38 + 24, ty), l, font=f, fill=INK)
                ty += int(size * 1.22)
            for l in rs:
                if shown:
                    d.text((pad + 36 + size * 0.38 + 24, ty), l, font=fa, fill=GREEN)
                ty += int(size * 1.22)
            y += hh + gap
        self.cache[key] = sp
        return sp

    def subtitle(self, cue):
        key = ("sub", cue["start"], cue["text"])
        if key not in self.cache:
            lines = cue["text"].split("\n")
            size = 56
            while size > 34 and max(text_w(l, font(size)) for l in lines) > 960:
                size -= 2
            f = font(size)
            lh = int(size * 1.3)
            im = Image.new("RGBA", (W, lh * len(lines) + 10), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            for i, l in enumerate(lines):
                d.text((W / 2, i * lh + lh / 2 + 4), l, font=f, fill=(255, 255, 255), anchor="mm")
            self.cache[key] = im
        return self.cache[key]

    def chip(self, speaker):
        key = ("chip", speaker)
        if key not in self.cache:
            names = {"mia": "Mia", "jonas": "Jonas", "narrator": "Erzähler"}
            f = font(34)
            name = names[speaker]
            w = int(text_w(name, f)) + 60
            sp, pad = rr_sprite(w, 56, 28, SPEAKER_COLOR[speaker] + (255,), shadow=False)
            ImageDraw.Draw(sp).text((pad + w / 2, pad + 29), name, font=f, fill=(255, 255, 255), anchor="mm")
            self.cache[key] = sp
        return self.cache[key]

    def endcard_bg(self):
        key = ("end",)
        if key not in self.cache:
            top, bot = np.array((27, 54, 104)), np.array((12, 28, 66))
            t = np.linspace(0, 1, H)[:, None, None]
            arr = (top * (1 - t) + bot * t) * np.ones((1, W, 1))
            im = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
            d = ImageDraw.Draw(im)
            if LOGO.exists():
                lg = self._logo(520)
                card, pad = rr_sprite(lg.width + 80, lg.height + 80, 50, (255, 255, 255, 255))
                im.alpha_composite(card, (W // 2 - card.width // 2, 330))
                im.alpha_composite(lg, (W // 2 - lg.width // 2, 330 + pad + 40))
            d.text((W / 2, 780), "Folge der ELM Akademie", font=font(62), fill=(255, 255, 255), anchor="mm")
            d.rounded_rectangle([W / 2 - 330, 850, W / 2 + 330, 950], radius=50, fill=ORANGE)
            d.text((W / 2, 900), "Abonnieren & mitmachen!", font=font(44), fill=(255, 255, 255), anchor="mm")
            self.cache[key] = im.convert("RGB")
        return self.cache[key]


# ------------------------------------------------------------------ Renderer
class Renderer:
    def __init__(self, level):
        self.level = level
        self.script = load_script(level)
        dur = load_json(ROOT / "audio" / level / "durations.json")
        self.timeline = build_timeline(self.script, dur)
        self.cues = build_cues(self.timeline)
        self.scenes = plan_scenes(self.script, self.timeline)
        self.content_end = self.scenes[-1]["end"]
        self.total = self.content_end + ENDCARD_SEC
        self.nframes = int(math.ceil(self.total * FPS))
        self.ov = Overlays(self.script)
        self.bgs, self.chars = {}, {}
        self.arm = {"mia": 0.0, "jonas": 0.0}
        self.mouth_prev = {"mia": 0.0, "jonas": 0.0}
        self.phase = {"mia": 0.0, "jonas": 1.7}
        self.envs = None

    def bg(self, key):
        if key not in self.bgs:
            self.bgs[key] = BACKGROUNDS[key]()
        return self.bgs[key]

    def char(self, kind, scale):
        k = (kind, scale)
        if k not in self.chars:
            self.chars[k] = Character(kind, scale)
        return self.chars[k]

    def scene_at(self, t):
        for sc in self.scenes:
            if t < sc["end"]:
                return sc
        return self.scenes[-1]

    def line_at(self, t):
        for e in self.timeline:
            if e["start"] <= t < e["end"]:
                return e
        return None

    def cue_at(self, t):
        for c in self.cues:
            if c["start"] <= t < c["end"]:
                return c
        return None

    def bg_frame(self, sc, t):
        im = self.bg(sc["bg"])
        p = min(1.0, max(0.0, (t - sc["start"]) / max(1e-6, sc["end"] - sc["start"])))
        q = p if sc["idx"] % 2 == 0 else 1 - p
        ww = W * (1 + 0.05 * q)
        hh = ww * H / W
        cx, cy = BG_MARGIN + W / 2, BG_MARGIN + H / 2
        box = (cx - ww / 2, cy - hh / 2, cx + ww / 2, cy + hh / 2)
        return im.resize((W, H), Image.BILINEAR, box=box)

    def characters(self, canvas, sc, t, f, endcard):
        kinds = sc["chars"]
        if endcard:
            kinds = ["mia", "jonas"]
        if not kinds:
            return
        learn = sc["type"] in LEARN_TYPES and not endcard
        if learn:
            scale, bottom = 0.72, 1500
            xs = {2: [270, 810], 1: [800]}[len(kinds)]
        elif len(kinds) == 2:
            scale, bottom, xs = 0.95, 1500, [290, 790]
        else:
            scale, bottom, xs = 1.1, 1500, [540]
        if endcard:
            scale, bottom, xs = 0.95, 1700, [290, 790]
        e = self.line_at(t)
        for kind, cx in zip(kinds, xs):
            ch = self.char(kind, scale)
            ph = self.phase[kind]
            active = e is not None and e["speaker"] == kind
            env = float(self.envs[kind][min(f, len(self.envs[kind]) - 1)]) if active else 0.0
            prev = self.mouth_prev[kind]
            es = 0.6 * env + 0.4 * prev
            self.mouth_prev[kind] = es
            mouth = 0 if es < 0.12 else 1 if es < 0.3 else 2 if es < 0.58 else 3
            blink = 1 if ((t + ph * 1.3) % (3.7 + ph * 0.3)) < 0.13 else 0
            # Arm-Ziel
            wave = False
            if sc["type"] == "hook" and t - sc["start"] < 3.6:
                wave = True
            if sc["type"] == "outro" and (t > sc["end"] - 3.2 or endcard):
                wave = True
            if active and GREETING.search(e["text"]):
                wave = True
            if wave:
                target = 152 + 20 * math.sin(2 * math.pi * 2.4 * t + ph)
            elif active:
                target = 6 + 26 * es + 4 * math.sin(2 * math.pi * 1.3 * t)
            else:
                target = 2 * math.sin(2 * math.pi * 0.5 * t + ph)
            self.arm[kind] += (target - self.arm[kind]) * 0.28
            bob = 5 * math.sin(2 * math.pi * t / 2.8 + ph) + (es * 7 if active else 0)
            lean = 4 * math.sin(2 * math.pi * t / 4.1 + ph)
            paste_character(canvas, ch, cx, bottom, t, mouth, blink, self.arm[kind], 3 * math.sin(2 * math.pi * 0.6 * t + ph), bob, lean)

    def top_content(self, canvas, sc, t):
        ov = self.ov
        shown = [r for r in sc["reveal"] if r["t"] <= t]
        if not shown:
            return
        if sc["type"] in LEARN_TYPES:
            items = []
            newest = len(shown) - 1
            for r in shown:
                ans_shown = r["t_ans"] is not None and r["t_ans"] <= t
                items.append((r["left"], r["right"], bool(ans_shown)))
            # Exercise: zuletzt freigeschalteter Eintrag (Frage oder Lösung) hervorheben
            if sc["type"] == "exercise":
                newest = max(range(len(shown)), key=lambda i: max(shown[i]["t"], shown[i]["t_ans"] or -1)
                             if (shown[i]["t_ans"] is None or shown[i]["t_ans"] <= t) else shown[i]["t"])
            board = ov.board((items, newest))
            canvas.paste(board, (W // 2 - board.width // 2, 150), board)
        else:
            r = shown[-1]
            card = ov.card(r["left"])
            age = t - r["t"]
            if age < 0.25:
                s = 0.8 + 0.2 * (1 - (1 - age / 0.25) ** 3)
                card = card.resize((int(card.width * s), int(card.height * s)), Image.BILINEAR)
            canvas.paste(card, (W // 2 - card.width // 2, 175), card)

    def frame(self, f):
        t = f / FPS
        endcard = t >= self.content_end
        sc = self.scene_at(min(t, self.content_end - 1e-3))
        if endcard:
            canvas = self.ov.endcard_bg().copy()
        else:
            canvas = self.bg_frame(sc, t)
        self.characters(canvas, sc, t, f, endcard)
        if not endcard:
            canvas.paste(self.ov.sheet, (0, SHEET_TOP), self.ov.sheet)
            h = self.ov.header(sc)
            canvas.paste(h, (24, 30), h)
            if self.ov.logo:
                canvas.paste(self.ov.logo, (W - 24 - self.ov.logo.width, 40), self.ov.logo)
            self.top_content(canvas, sc, t)
            c = self.cue_at(t)
            if c:
                chip = self.ov.chip(c["speaker"])
                canvas.paste(chip, (40, SHEET_TOP + 34), chip)
                sub = self.ov.subtitle(c)
                canvas.paste(sub, (0, SHEET_TOP + 130 + (3 - len(c["text"].split("\n"))) * 20), sub)
        return canvas

    def render(self, out_mp4, seconds=None):
        out_wav = ROOT / ".cache" / f"{self.level}_mix.wav"
        self.envs = build_audio(self.script, self.timeline, self.total, out_wav)
        nf = self.nframes if not seconds else min(self.nframes, int(seconds * FPS))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-i", str(out_wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-t", f"{nf / FPS:.3f}", "-movflags", "+faststart", str(out_mp4)]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(nf):
            pr.stdin.write(self.frame(f).convert("RGB").tobytes())
            if f % 600 == 0:
                print(f"{self.level}: {f}/{nf}", flush=True)
        pr.stdin.close()
        pr.wait()
        # SRT passend zum Video (Hochformat-Umbruch, identische Zeiten)
        srt = []
        for i, c in enumerate(self.cues, 1):
            srt.append(f"{i}\n{fmt_ts(c['start'])} --> {fmt_ts(c['end'])}\n{c['text']}\n")
        (out_mp4.with_suffix(".srt")).write_text("\n".join(srt), encoding="utf-8")
        print(f"{self.level}: fertig -> {out_mp4} ({nf / FPS:.0f} s)", flush=True)

    def stills(self, times):
        self.envs = build_audio(self.script, self.timeline, self.total, ROOT / ".cache" / f"{self.level}_mix.wav")
        outd = ROOT / "output" / "stills"
        outd.mkdir(parents=True, exist_ok=True)
        # vorherige Bilder durchlaufen lassen, damit Glättung (Arm/Mund) eingeschwungen ist
        for tt in times:
            f0 = int(tt * FPS)
            for f in range(max(0, f0 - 12), f0):
                self.frame(f)
            self.frame(f0).save(outd / f"{self.level}_{tt:06.1f}.png")


def run(args):
    level, seconds = args
    r = Renderer(level)
    out = ROOT / "videos" / level / f"{level}_9x16.mp4"
    r.render(out, seconds)


def main():
    argv = sys.argv[1:]
    seconds = None
    still = None
    if "--seconds" in argv:
        i = argv.index("--seconds"); seconds = float(argv[i + 1]); del argv[i:i + 2]
    if "--still" in argv:
        i = argv.index("--still"); still = [float(x) for x in argv[i + 1].split(",")]; del argv[i:i + 2]
    levels = argv or LEVELS
    (ROOT / ".cache").mkdir(exist_ok=True)
    if still:
        for lv in levels:
            Renderer(lv).stills(still)
        return
    with ProcessPoolExecutor(max_workers=min(4, len(levels))) as ex:
        list(ex.map(run, [(lv, seconds) for lv in levels]))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT.parent / "videos"))
    main()
