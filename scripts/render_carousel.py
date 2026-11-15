#!/usr/bin/env python3
"""Render a 5-slide LinkedIn carousel (1080x1080 PNGs + PDF) from a JSON brief.

Usage:
  python3 scripts/render_carousel.py --data posts/2026-09-26/carousel.json \\
      --outdir posts/2026-09-26/carousel

JSON shape:
  {"kicker": "...", "theme": "light",
   "cover": {"headline": "...", "sub": "..."},
   "slides": [{"stat": "-33%", "label": "posts published", "note": "..."}, ...],
   "takeaway": "...", "cta": "..."}
"""
import argparse
import json
import os

W = H = 1080

PALETTES = {
    "light": {"bg": (247, 244, 237), "ink": (15, 27, 45), "muted": (91, 100, 114),
              "accent": (10, 102, 194), "ember": (255, 92, 56), "card": (255, 255, 255)},
    "dark": {"bg": (13, 20, 33), "ink": (245, 247, 250), "muted": (150, 162, 179),
             "accent": (78, 161, 255), "ember": (255, 110, 80), "card": (22, 30, 46)},
    "noir": {"bg": (10, 16, 28), "ink": (245, 247, 250), "muted": (150, 162, 179),
             "accent": (80, 170, 255), "ember": (255, 110, 80), "card": (18, 26, 42)},
}


def make_font(bold=False):
    from PIL import ImageFont
    idx = 1 if bold else 0
    for name in ("/System/Library/Fonts/Helvetica.ttc",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(name):
            try:
                return lambda s: ImageFont.truetype(
                    name, s, index=idx if name.endswith(".ttc") else 0)
            except Exception:
                continue
    from PIL import ImageFont as F
    return lambda s: F.load_default()


def wrap(d, text, fnt, max_w, max_lines=4):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def base(theme):
    from PIL import Image
    return Image.new("RGB", (W, H), PALETTES[theme]["bg"])


def frame(theme, num, total=5):
    from PIL import ImageDraw
    t = PALETTES[theme]
    img = base(theme)
    d = ImageDraw.Draw(img)
    # top-left page tag
    d.rectangle([72, 64, 170, 72], fill=t["ember"])
    fnt = make_font() (26)
    d.text((72, 84), f"{num:02d} / {total:02d}", font=fnt, fill=t["muted"])
    # bottom dots
    gap, r, y = 26, 7, 1006
    x0 = (W - ((total - 1) * gap)) / 2
    for i in range(total):
        c = t["ember"] if i + 1 == num else (210, 205, 192) if theme == "light" else (60, 72, 92)
        d.ellipse([x0 + i * gap - r, y - r, x0 + i * gap + r, y + r], fill=c)
    # cinematic finish: soft glow, vignette, film grain
    from PIL import Image as _I
    glow = _I.new("RGBA", (W, H), (0, 0, 0, 0))
    _gd = ImageDraw.Draw(glow)
    _gd.ellipse([W / 2 - 700, -500, W / 2 + 700, 700],
                fill=t["accent"] + (26 if theme != "light" else 18,))
    img = _I.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    mask = _I.radial_gradient("L").resize((W, H))
    img = _I.composite(img, _I.new("RGB", (W, H), (0, 0, 0)), mask)
    grain = _I.effect_noise((W, H), 28).convert("RGB")
    img = _I.blend(img, grain, 0.05)
    d = ImageDraw.Draw(img)
    return img, d


def slide_cover(data, theme, total):
    from PIL import ImageDraw
    img, d = frame(theme, 1, total)
    t = PALETTES[theme]
    fb, fr = make_font(True), make_font()
    # giant ghost numeral behind content
    ghost = fb(420)
    d.text((600, 560), "01", font=ghost,
           fill=(231, 226, 211) if theme == "light" else (30, 40, 58))
    # kicker
    d.rectangle([96, 220, 196, 228], fill=t["ember"])
    f26 = fr(30)
    kx = 96
    for ch in data["kicker"].upper():
        d.text((kx, 246), ch, font=f26, fill=t["muted"])
        kx += d.textlength(ch, font=f26) + 3
    y = 330
    for ln in wrap(d, data["cover"]["headline"], fb(104), 888, 3):
        d.text((92, y), ln, font=fb(104), fill=t["ink"])
        y += 122
    d.rectangle([96, y + 14, 300, y + 22], fill=t["accent"])
    y += 70
    for ln in wrap(d, data["cover"].get("sub", ""), fr(40), 888, 3):
        d.text((94, y), ln, font=fr(40), fill=t["muted"])
        y += 54
    return img


def slide_stat(s, theme, num, total):
    from PIL import ImageDraw
    img, d = frame(theme, num, total)
    t = PALETTES[theme]
    fb, fr = make_font(True), make_font()
    f30 = fr(32)
    kx = 96
    for ch in s.get("kicker", "THE PROOF").upper():
        d.text((kx, 200), ch, font=f30, fill=t["muted"])
        kx += d.textlength(ch, font=f30) + 3
    d.text((92, 270), s["stat"], font=fb(230), fill=t["accent"])
    y = 560
    for ln in wrap(d, s.get("label", ""), fb(64), 888, 2):
        d.text((94, y), ln, font=fb(64), fill=t["ink"])
        y += 78
    y += 20
    for ln in wrap(d, s.get("note", ""), fr(38), 888, 3):
        d.text((94, y), ln, font=fr(38), fill=t["muted"])
        y += 52
    return img


def slide_lines(title, lines, theme, num, total):
    from PIL import ImageDraw
    img, d = frame(theme, num, total)
    t = PALETTES[theme]
    fb, fr = make_font(True), make_font()
    y = 220
    for ln in wrap(d, title, fb(72), 888, 3):
        d.text((92, y), ln, font=fb(72), fill=t["ink"])
        y += 88
    d.rectangle([96, y + 12, 260, y + 20], fill=t["ember"])
    y += 70
    for i, line in enumerate(lines):
        ls = wrap(d, line, fr(44), 800, 3)
        d.text((94, y), f"0{i + 1}", font=fb(44), fill=t["accent"])
        ly = y
        for ln in ls:
            d.text((200, ly), ln, font=fr(44), fill=t["ink"])
            ly += 58
        y = ly + 34
    return img


def slide_cta(data, theme, num, total):
    from PIL import ImageDraw
    img, d = frame(theme, num, total)
    t = PALETTES[theme]
    fb, fr = make_font(True), make_font()
    y = 300
    for ln in wrap(d, data["cta"], fb(84), 888, 4):
        d.text((92, y), ln, font=fb(84), fill=t["ink"])
        y += 100
    d.rectangle([96, y + 16, 300, y + 24], fill=t["ember"])
    f = fr(36)
    d.text((96, y + 60), "New case every morning.", font=f, fill=t["muted"])
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    data = json.load(open(args.data))
    theme = data.get("theme", "light")
    os.makedirs(args.outdir, exist_ok=True)

    middle = data.get("slides", [])
    total = 1 + len(middle) + (1 if data.get("takeaway") else 0) + 1
    slides = [slide_cover(data, theme, total)]
    for i, s in enumerate(middle):
        if "stat" in s:
            slides.append(slide_stat(s, theme, i + 2, total))
        else:
            slides.append(slide_lines(s.get("title", ""), s.get("lines", []), theme, i + 2, total))
    if data.get("takeaway"):
        slides.append(slide_lines("Do this next week",
                                  [data["takeaway"]], theme, len(slides) + 1, total))
    slides.append(slide_cta(data, theme, len(slides) + 1, total))

    paths = []
    for i, im in enumerate(slides):
        p = os.path.join(args.outdir, f"slide-{i + 1:02d}.png")
        im.save(p)
        paths.append(p)
    pdf = os.path.join(args.outdir, "carousel.pdf")
    slides[0].save(pdf, save_all=True, append_images=slides[1:])
    print(f"{len(slides)} slides -> {args.outdir} + carousel.pdf")


if __name__ == "__main__":
    main()
