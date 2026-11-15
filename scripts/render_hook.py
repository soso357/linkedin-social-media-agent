#!/usr/bin/env python3
"""Render the single-image post visual: solid blue background, the hook only,
author name in the bottom-left corner. 1080x1080 PNG.

Usage:
  python3 scripts/render_hook.py --post-file posts/2026-11-15/post.txt --out posts/2026-11-15/visual.png
  python3 scripts/render_hook.py --hook "Your company page posts. Nobody replies." --out visual.png

With --post-file the hook is the post's first paragraph (text before the first blank line).
"""
import argparse
import hashlib
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1080
MARGIN = 96
INK = "#FFFFFF"
NAME = os.environ.get("AUTHOR_NAME", "Your Name")
PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "profile.png")
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"  # index 1 = Bold, 0 = Regular


# ---- velvet fabric background (procedural folds + sheen) ----
STOPS = [(0.00, (2, 3, 36)), (0.30, (10, 2, 72)), (0.55, (8, 4, 110)),
         (0.78, (6, 42, 190)), (0.92, (10, 95, 232)), (1.00, (60, 140, 255))]

def ramp(t):
    t = min(1, max(0, t))
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if t <= b:
            k = (t - a) / (b - a)
            return tuple(int(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
    return STOPS[-1][1]

def velvet(size=1080, seed=1, n=240):
    rnd = random.Random(seed)
    base = rnd.uniform(0.35, 1.0)
    waves = [(rnd.uniform(0.6, 1.0), rnd.uniform(1.0, 1.9), base + rnd.uniform(-0.35, 0.35), rnd.uniform(0, 6.28)) for _ in range(3)]
    waves = [(a, f, math.cos(t), math.sin(t), p) for a, f, t, p in waves]
    warp = [(rnd.uniform(0.8, 1.4), rnd.uniform(0.8, 1.8), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)) for _ in range(2)]
    def h(x, y):
        wx = sum(a * math.sin(f * y * 6.28 + p) for a, f, p, _ in warp)
        wy = sum(a * math.cos(f * x * 6.28 + q) for a, f, _, q in warp)
        return sum(a * math.sin(f * 6.28 * ((x + .1 * wx) * c + (y + .1 * wy) * s) + p) for a, f, c, s, p in waves)
    e = 1 / n
    G, H = [], []
    for j in range(n):
        for i in range(n):
            x, y = i / n, j / n
            gx = (h(x + e, y) - h(x - e, y)) / (2 * e)
            gy = (h(x, y + e) - h(x, y - e)) / (2 * e)
            G.append((gx, gy)); H.append(h(x, y))
    mags = sorted(math.hypot(*g) for g in G)
    k = 2.6 / (mags[int(len(mags) * 0.90)] + 1e-6)   # normalise: top 3% slopes -> strong sheen
    hmax = max(abs(v) for v in H) + 1e-6
    img = Image.new("RGB", (n, n)); px = img.load()
    for idx, ((gx, gy), hv) in enumerate(zip(G, H)):
        ndv = 1 / math.sqrt(1 + (k * gx) ** 2 + (k * gy) ** 2)
        sheen = (1 - ndv) ** 1.25
        lit = max(0.0, (-0.5 * gx - 0.85 * gy) * k * ndv)
        t = 0.24 + 0.85 * sheen + 0.10 * min(1, lit) - 0.06 * hv / hmax
        px[idx % n, idx // n] = ramp(t)
    img = img.resize((size, size), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2.5))
    grain = Image.effect_noise((size, size), 22).convert("RGB")
    return Image.blend(img, grain, 0.035)


def font(size, bold):
    try:
        return ImageFont.truetype(FONT, size, index=1 if bold else 0)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)


def wrap(d, text, fnt, max_w):
    lines = []
    for para in text.splitlines():
        cur = ""
        for w in para.split():
            trial = (cur + " " + w).strip()
            if d.textlength(trial, font=fnt) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def hook_from_post(path):
    text = open(path, encoding="utf-8").read().strip()
    return text.split("\n\n", 1)[0].strip()


def render(hook, out, seed=None, name=NAME):
    # Velvet fabric; seed from the hook so each post gets its own folds.
    if seed is None:
        seed = int(hashlib.md5(hook.encode()).hexdigest()[:8], 16)
    img = velvet(W, seed=seed)
    img = Image.eval(img, lambda v: int(v * 0.82))  # keep white text readable
    d = ImageDraw.Draw(img)

    # Largest font size (96 -> 44) whose wrapped hook fits the text area.
    max_w, max_h = W - 2 * MARGIN, H - 2 * MARGIN - 120
    for size in range(96, 43, -4):
        fnt = font(size, bold=True)
        lines = wrap(d, hook, fnt, max_w)
        lh = int(size * 1.18)
        if lh * len(lines) <= max_h:
            break
    block_h = lh * len(lines)
    y = (H - block_h) // 2 - 30
    for line in lines:
        d.text((MARGIN, y), line, font=fnt, fill=INK)
        y += lh

    # Round profile photo, then the name, bottom-left.
    nf = font(34, bold=False)
    x = MARGIN
    cy = H - MARGIN - 12  # vertical centre of the name text
    if os.path.exists(PHOTO):
        r = 38
        ph = Image.open(PHOTO).convert("RGB")
        pw, phh = ph.size
        s = int(min(pw, phh) * 0.80)  # head + shoulders
        cx0, cy0 = pw // 2, min(int(phh * 0.58), phh - s // 2)
        ph = ph.crop((cx0 - s // 2, cy0 - s // 2, cx0 + s // 2, cy0 + s // 2))
        ss = 4  # supersample for a smooth circle edge
        ph = ph.resize((2 * r * ss, 2 * r * ss), Image.LANCZOS)
        mask = Image.new("L", ph.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, ph.size[0] - 1, ph.size[1] - 1), fill=255)
        ph = ph.resize((2 * r, 2 * r), Image.LANCZOS)
        mask = mask.resize((2 * r, 2 * r), Image.LANCZOS)
        ring = 2
        d.ellipse((x - ring, cy - r - ring, x + 2 * r + ring, cy + r + ring), fill=INK)
        img.paste(ph, (x, cy - r), mask)
        x += 2 * r + 22
    d.text((x, cy), name, font=nf, fill=INK, anchor="lm")

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out, "PNG")
    return out


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--hook")
    src.add_argument("--post-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    hook = a.hook or hook_from_post(a.post_file)
    print(render(hook, a.out, seed=a.seed))


if __name__ == "__main__":
    main()
