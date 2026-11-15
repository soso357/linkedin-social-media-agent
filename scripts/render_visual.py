#!/usr/bin/env python3
"""Render a minimal, modern LinkedIn visual (1200x627) as PNG + SVG.

PNG is drawn natively with Pillow (pixel-exact, no converter needed).
SVG is written alongside for editing/reuse.

Usage:
  python3 scripts/render_visual.py --headline "Short headline" --subline "supporting line" \\
      --stat "63%" --out posts/2026-09-26/visual.png --svg posts/2026-09-26/visual.svg
"""
import argparse
import html
import os

W, H = 1080, 1080

THEMES = {
    "light": {"bg": (247, 245, 240), "ink": (17, 17, 17), "muted": (85, 85, 85),
              "accent": (10, 102, 194), "card": (255, 255, 255), "line": (229, 224, 213)},
    "dark": {"bg": (14, 17, 22), "ink": (245, 245, 245), "muted": (168, 176, 187),
             "accent": (78, 161, 255), "card": (23, 28, 36), "line": (42, 51, 64)},
}


def wrap(text, per_line=26, max_lines=4):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= per_line or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def build_png(headline, subline, stat, theme, out_path, stat2=""):
    from PIL import Image, ImageDraw, ImageFont

    t = THEMES[theme]
    img = Image.new("RGB", (W, H), t["bg"])
    d = ImageDraw.Draw(img)

    def font(size, bold=False):
        idx = 1 if bold else 0
        cands = ["/System/Library/Fonts/Helvetica.ttc",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"]
        for name in cands:
            if os.path.exists(name):
                try:
                    return ImageFont.truetype(name, size,
                                              index=idx if name.endswith(".ttc") else 0)
                except Exception:
                    continue
        return ImageFont.load_default()

    def spaced(text, xy, fnt, fill, tracking=3):
        x, y = xy
        for ch in text:
            d.text((x, y), ch, font=fnt, fill=fill)
            x += d.textlength(ch, font=fnt) + tracking

    # centered target mark
    cx, cy = 540, 640
    accent = t["accent"]
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], outline=accent + (255,), width=6)
    od.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], fill=accent + (38,))
    od.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=accent + (255,))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)

    # kicker: rule + letterspaced small caps
    d.rectangle([96, 92, 170, 99], fill=accent)
    spaced((subline or "MARKETING INSIGHT").upper(), (96, 118), font(27), t["muted"])

    # headline: bold, generous leading
    y = 210
    for ln in wrap(headline, per_line=20, max_lines=3):
        d.text((94, y), ln, font=font(78, bold=True), fill=t["ink"])
        y += 94

    # accent underline under headline block
    d.rectangle([96, y + 10, 260, y + 17], fill=accent)

    # stat block pinned near bottom
    if stat:
        d.text((94, 812), stat, font=font(76, bold=True), fill=accent)
        if stat2:
            d.text((94, 896), stat2, font=font(44), fill=t["muted"])
            d.text((96, 962), "source in post caption", font=font(22), fill=t["muted"])
        else:
            d.text((96, 908), "source in post caption", font=font(22), fill=t["muted"])

    img.save(out_path)
    return out_path


def build_svg(headline, subline, stat, theme):
    hexes = {k: "#%02x%02x%02x" % v for k, v in THEMES[theme].items()}
    lines = wrap(headline, per_line=20, max_lines=3)
    y = 250
    tspans = "".join(
        f'<text x="96" y="{y + i * 94}" font-family="Helvetica,Arial,sans-serif"'
        f' font-size="78" font-weight="700" fill="{hexes["ink"]}">{html.escape(ln)}</text>\n'
        for i, ln in enumerate(lines))
    stat_block = (f'<text x="94" y="880" font-family="Helvetica,Arial,sans-serif" font-size="76"'
                  f' font-weight="800" fill="{hexes["accent"]}">{html.escape(stat)}</text>' if stat else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="{hexes["bg"]}"/>'
            f'<circle cx="540" cy="640" r="120" fill="none" stroke="{hexes["accent"]}" stroke-width="6"/>'
            f'<circle cx="540" cy="640" r="56" fill="{hexes["accent"]}" opacity="0.15"/>'
            f'<rect x="96" y="92" width="74" height="7" fill="{hexes["accent"]}"/>'
            f'<text x="96" y="140" font-family="Helvetica,Arial,sans-serif" font-size="27"'
            f' letter-spacing="3" fill="{hexes["muted"]}">{html.escape((subline or "MARKETING INSIGHT").upper())}</text>'
            f'{tspans}{stat_block}</svg>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headline", required=True)
    ap.add_argument("--subline", default="Marketing insight")
    ap.add_argument("--stat", default="")
    ap.add_argument("--stat2", default="")
    ap.add_argument("--theme", default="light", choices=list(THEMES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--svg", default="")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    build_png(args.headline, args.subline, args.stat, args.theme, args.out, args.stat2)
    svg_path = args.svg or os.path.splitext(args.out)[0] + ".svg"
    with open(svg_path, "w") as f:
        f.write(build_svg(args.headline, args.subline, args.stat, args.theme))
    print(f"PNG: {args.out} ({os.path.getsize(args.out)} bytes)")
    print(f"SVG: {svg_path}")


if __name__ == "__main__":
    main()
