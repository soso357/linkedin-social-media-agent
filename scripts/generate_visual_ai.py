#!/usr/bin/env python3
"""Generate a LinkedIn visual with a FREE AI image provider (no key needed).

Default provider: Pollinations.ai (FLUX model) — free, no signup.
Paid option: OpenAI image models via --provider openai (needs OPENAI_API_KEY).

Usage:
  python3 scripts/generate_visual_ai.py --headline "Post less, grow faster" \\
      --subline "Inter Milan case" --stat "-33% posts / +43% reach" \\
      --out posts/2026-09-26/visual-ai.png

Fallback: scripts/render_visual.py (coded card, always works offline).

Note: AI models often garble small text. The daily workflow must READ the
generated PNG back and fall back to the coded card if text is unreadable.
"""
import argparse
import base64
import json
import os
import random
import sys
import urllib.parse
import urllib.request

HOUSE_STYLE = (
    "Style: minimal, professional, modern LinkedIn banner, clean flat design, "
    "soft warm off-white background (#F7F5F0), one deep-blue accent (#0A66C2), "
    "large clean sans-serif headline typography, strong visual hierarchy, "
    "very few words, generous whitespace, subtle abstract geometric shapes only, "
    "no photos of people, no stock-photo look, no clutter, no watermark."
)


def load_env():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headline", default="")
    ap.add_argument("--subline", default="")
    ap.add_argument("--stat", default="")
    ap.add_argument("--prompt", default="", help="free-form prompt (overrides headline parts)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1024x1024",
                    help="use standard sizes only (provider rejects custom ones)")
    ap.add_argument("--provider", default="free", choices=["free", "openai"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--hybrid", action="store_true",
                    help="free AI abstract background + crisp coded text overlay (recommended)")
    args = ap.parse_args()

    load_env()

    if args.prompt:
        prompt = args.prompt + " " + HOUSE_STYLE
    else:
        prompt = (f"LinkedIn post banner. Headline text: '{args.headline}'. "
                  f"Secondary text: '{args.subline}'. Highlight stat: '{args.stat}'. "
                  + HOUSE_STYLE)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)

    if args.provider == "free":
        code = generate_free(prompt, args)
        if code == 0 and args.hybrid:
            code = apply_text_overlay(args)
        return code

    key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.5-flare")
    if not key:
        print("OPENAI_API_KEY not set — use --provider free or render_visual.py.")
        return 2
    body = json.dumps({"model": model, "prompt": prompt, "size": args.size}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations",
                                 data=body, method="POST")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        detail = ""
        try:
            detail = e.read().decode()  # type: ignore
        except Exception:
            pass
        print(f"OpenAI image error: {e}\n{detail}", file=sys.stderr)
        return 1

    b64 = data["data"][0]["b64_json"]
    with open(args.out, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"AI visual saved: {args.out} ({os.path.getsize(args.out)} bytes, model={model})")
    return 0


def generate_free(prompt, args):
    """Pollinations.ai — free, no key. Returns 0 on success."""
    if args.hybrid:
        # abstract background only: no text, the overlay adds typography later
        prompt = ("Abstract minimal background, soft warm off-white with one deep-blue "
                  "geometric shape on the right side, flat modern design, generous "
                  "whitespace, no text, no words, no letters, no people, no watermark.")
    w, h = (args.size.split("x") + ["1024"])[:2]
    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    params = urllib.parse.urlencode({
        "width": w, "height": h, "seed": seed,
        "model": "flux", "nologo": "true",
    })
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?{params}"
    try:
        import certifi
        import ssl
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = None
    try:
        with urllib.request.urlopen(url, timeout=300, context=ctx) as resp:
            blob = resp.read()
    except Exception as e:
        print(f"Free provider error: {e}", file=sys.stderr)
        return 1
    if len(blob) < 10_000:
        print(f"Free provider returned suspiciously small file ({len(blob)} bytes).", file=sys.stderr)
        return 1
    with open(args.out, "wb") as f:
        f.write(blob)
    print(f"AI visual saved: {args.out} ({len(blob)} bytes, free/pollinations-flux, seed={seed})")
    return 0


def apply_text_overlay(args):
    """Draw crisp headline/stat over the AI background (left text panel)."""
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1080, 1080
    bg = Image.open(args.out).convert("RGB")
    # cover-crop to exact size, shaving the bottom (frees watermarks there)
    CUT = 80
    scale = max(W / bg.width, (H + CUT) / bg.height)
    bg = bg.resize((int(bg.width * scale) + 1, int(bg.height * scale) + 1)).crop((0, 0, W, H))

    d = ImageDraw.Draw(bg)
    ink, muted, accent = (17, 17, 17), (85, 85, 85), (10, 102, 194)
    # bottom text band keeps the AI art visible up top, text always crisp
    d.rectangle([0, 560, W, H], fill=(247, 245, 240))

    def font(size):
        for name in ("/System/Library/Fonts/Helvetica.ttc",
                     "/System/Library/Fonts/Supplemental/Arial.ttf"):
            if os.path.exists(name):
                try:
                    return ImageFont.truetype(name, size, index=1)
                except Exception:
                    continue
        return ImageFont.load_default()

    def wrap(text, per_line=22, max_lines=3):
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

    d.rectangle([96, 610, 170, 617], fill=accent)
    d.text((96, 632), (args.subline or "MARKETING INSIGHT").upper(), font=font(27), fill=muted)
    y = 700
    for ln in wrap(args.headline):
        d.text((94, y), ln, font=font(72), fill=ink)
        y += 86
    d.rectangle([96, y + 8, 260, y + 15], fill=accent)
    if args.stat:
        d.text((94, 906), args.stat, font=font(64), fill=accent)
        d.text((96, 992), "source in post caption", font=font(22), fill=muted)
    bg.save(args.out)
    print(f"Hybrid visual saved: {args.out} ({os.path.getsize(args.out)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
