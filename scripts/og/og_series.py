#!/usr/bin/env python3
"""BollyAI OG card engine — per-series + per-season share cards.

Usage: python3 scripts/og/og_series.py <slug> [<slug>...]
Out:   site/public/img/series/<slug>/og.jpg            (series card)
       site/public/img/series/<slug>/og-s<N>.jpg       (season cards)

Design language: ink bg, Fraunces display, JetBrains Mono kickers,
amber accent, rubber-stamp verdict, 5-stop verdict ramp.
"""
import json, os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.expanduser("~/bollyai")
FONTS = os.path.join(ROOT, "scripts", "og", "fonts")
W, H = 1200, 630

INK = (13, 12, 19)
INK_DEEP = (9, 8, 14)
PAPER = (244, 239, 230)
PAPER_DIM = (200, 195, 188)
ACCENT = (232, 164, 76)       # amber
RAMP = [(178, 58, 48), (204, 110, 56), (226, 178, 88), (118, 184, 120), (66, 186, 148)]
RUNGS = ["DISASTER DROP", "SKIP", "ONE-TIME WATCH", "WORTH-IT", "MUST-WATCH"]


def F(name, size, axes=None):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    if axes:
        try: f.set_variation_by_axes(axes)
        except Exception: pass
    return f


def fraunces(size, opsz=None):
    return F("fraunces.ttf", size, [opsz if opsz else min(144, max(9, size * 0.72))])


def rough_rect(d, xy, color, width=5, jitter=2.2, seed=7):
    """Hand-drawn looking rectangle for the rubber stamp."""
    import random
    rnd = random.Random(seed)
    x0, y0, x1, y1 = xy
    pts = []
    steps = 26
    for i in range(steps + 1):  # top
        pts.append((x0 + (x1 - x0) * i / steps, y0 + rnd.uniform(-jitter, jitter)))
    for i in range(steps + 1):  # right
        pts.append((x1 + rnd.uniform(-jitter, jitter), y0 + (y1 - y0) * i / steps))
    for i in range(steps + 1):  # bottom
        pts.append((x1 - (x1 - x0) * i / steps, y1 + rnd.uniform(-jitter, jitter)))
    for i in range(steps + 1):  # left
        pts.append((x0 + rnd.uniform(-jitter, jitter), y1 - (y1 - y0) * i / steps))
    d.line(pts + [pts[0]], fill=color, width=width, joint="curve")


def stamp(verdict, angle=-7, scale=1.0):
    """Render a rotated rubber-stamp chip, returns RGBA image."""
    fs = int(44 * scale)
    f = F("jbmono-700.ttf", fs)
    pad_x, pad_y = int(34 * scale), int(22 * scale)
    tmp = Image.new("RGBA", (10, 10))
    tw = ImageDraw.Draw(tmp).textlength(verdict, font=f)
    w, h = int(tw + pad_x * 2), int(fs + pad_y * 2)
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rough_rect(d, (10, 10, w + 10, h + 10), ACCENT + (235,), width=max(4, int(5 * scale)))
    d.text((10 + pad_x, 10 + pad_y - int(fs * 0.12)), verdict, font=f, fill=ACCENT + (235,))
    # ink-bleed texture: punch tiny holes
    import random
    rnd = random.Random(3)
    px = img.load()
    for _ in range(int(w * h * 0.012)):
        x, y = rnd.randrange(img.width), rnd.randrange(img.height)
        r, g, b, a = px[x, y]
        if a > 0: px[x, y] = (r, g, b, int(a * rnd.uniform(0.2, 0.8)))
    return img.rotate(angle, expand=True, resample=Image.BICUBIC)


def ramp_bar(d, x, y, w, h, verdict):
    seg = w / 5
    for i, c in enumerate(RAMP):
        d.rectangle([x + i * seg + 2, y, x + (i + 1) * seg - 2, y + h], fill=c + (70,) if verdict is None else None)
    # active fill
    if verdict in RUNGS:
        idx = RUNGS.index(verdict)
        for i, c in enumerate(RAMP):
            alpha = 255 if i <= idx else 56
            d.rectangle([x + i * seg + 2, y, x + (i + 1) * seg - 2, y + h], fill=c + (alpha,))
        mx = x + (idx + 0.5) * seg
        d.polygon([(mx, y - 14), (mx - 9, y - 2), (mx + 9, y - 2)], fill=ACCENT)
    else:
        for i, c in enumerate(RAMP):
            d.rectangle([x + i * seg + 2, y, x + (i + 1) * seg - 2, y + h], fill=c + (56,))


def base_canvas(slug, series):
    img = Image.new("RGB", (W, H), INK)
    bd_path = os.path.join(ROOT, "site/public/img/series", slug, "backdrop.jpg")
    if os.path.exists(bd_path):
        bd = Image.open(bd_path).convert("RGB")
        s = max(W / bd.width, H / bd.height)
        bd = bd.resize((int(bd.width * s) + 1, int(bd.height * s) + 1), Image.LANCZOS)
        bd = bd.crop((bd.width - W, 0, bd.width, H))
        bd = bd.filter(ImageFilter.GaussianBlur(1.2))
        img.paste(bd, (0, 0))
        # left-to-right ink wash so type sits on quiet ground
        grad = Image.new("L", (W, 1))
        for x in range(W):
            t = x / W
            v = 255 if t < 0.42 else int(255 * (1 - min(1, (t - 0.42) / 0.5)) ** 1.4) + 38
            grad.putpixel((x, 0), min(255, v))
        grad = grad.resize((W, H))
        ink = Image.new("RGB", (W, H), INK_DEEP)
        img = Image.composite(ink, img, grad)
        # bottom shade
        bgrad = Image.new("L", (1, H))
        for y in range(H):
            bgrad.putpixel((0, y), int(120 * max(0, (y / H - 0.55) / 0.45)))
        img = Image.composite(Image.new("RGB", (W, H), INK_DEEP), img, bgrad.resize((W, H)))
    return img


def compose(slug, series, season=None):
    img = base_canvas(slug, series).convert("RGBA")
    d = ImageDraw.Draw(img)
    M = 64

    # poster
    pp = os.path.join(ROOT, "site/public/img/series", slug, "poster.jpg")
    px = None
    if os.path.exists(pp):
        poster = Image.open(pp).convert("RGB").resize((300, 450), Image.LANCZOS)
        frame = Image.new("RGB", (310, 460), PAPER)
        frame.paste(poster, (5, 5))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([W - 310 - M + 10, (H - 460) // 2 + 14, W - M + 10, (H - 460) // 2 + 474], fill=(0, 0, 0, 140))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        img = Image.alpha_composite(img, sh)
        img.paste(frame, (W - 310 - M, (H - 460) // 2))
        d = ImageDraw.Draw(img)
        px = W - 310 - M

    text_right = (px - 40) if px else (W - M)

    # season source: explicit season card, else PEAK season (best scored with a verdict)
    if season:
        src = season
    else:
        # peak = best-scored season that HAS a verdict (matches site peakSeason logic)
        verdicted = [s for s in series["seasons"] if s.get("bollymeter") and s.get("verdict")]
        scored = [s for s in series["seasons"] if s.get("bollymeter")]
        pool = verdicted or scored
        src = max(pool, key=lambda s: s["bollymeter"]["score"]) if pool else (series["seasons"][-1] if series["seasons"] else None)

    # ── fixed layout slots ──
    # kicker @78 · title @128 · meta @~300 · score 360-505 · ramp @528 · wordmark @H-66
    kick = "WHAT BOLLYAI THINKS" if not season else f"SEASON {season['number']} VERDICT"
    kf = F("jbmono-700.ttf", 26)
    d.text((M, 78), kick, font=kf, fill=ACCENT)
    d.line([(M, 118), (M + d.textlength(kick, font=kf), 118)], fill=ACCENT + (120,), width=2)

    title = series["title"]["value"].upper()
    tsize = 150 if len(title) <= 8 else (104 if len(title) <= 16 else 72)
    tf = fraunces(tsize, opsz=144)
    d.text((M - 6, 128 + (150 - tsize) // 2), title, font=tf, fill=PAPER)

    meta = f"{series['origin']}  ·  {series['platform']['value']}  ·  {len(series['seasons'])} seasons"
    if season:
        meta = f"{season['year']}  ·  {season['episodes']} episodes  ·  {series['platform']['value']}"
    d.text((M, 308), meta, font=F("hanken-400.ttf", 30), fill=PAPER_DIM)

    bm = (src or {}).get("bollymeter")
    if bm:
        score = f"{bm['score']:.1f}"
        sf = fraunces(132, opsz=144)
        d.text((M - 4, 362), score, font=sf, fill=ACCENT)
        sw = d.textlength(score, font=sf)
        d.text((M + sw + 14, 398), "BOLLYMETER", font=F("jbmono-700.ttf", 22), fill=PAPER_DIM)
        d.text((M + sw + 14, 432), "/10", font=F("hanken-700.ttf", 40), fill=PAPER_DIM)

    verdict = (src or {}).get("verdict")
    ramp_w = min(460, text_right - M)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ramp_bar(ImageDraw.Draw(overlay), M, 532, ramp_w, 14, verdict)
    img = Image.alpha_composite(img, overlay)

    # verdict stamp: over the open middle, tilted like it was pressed on
    chip = stamp(verdict) if verdict else (stamp("STILL DROPPING", angle=-5) if season else None)
    if chip:
        sx = int(max(M + 470, text_right - chip.width - 20))
        img.alpha_composite(chip, (sx, 330))

    # wordmark
    d = ImageDraw.Draw(img)
    wm = "bollyai.in"
    wf = F("hanken-700.ttf", 32)
    d.text((M, H - 66), wm, font=wf, fill=PAPER)
    wx = M + d.textlength(wm, font=wf)
    d.ellipse([wx + 14, H - 52, wx + 26, H - 40], fill=ACCENT)

    return img.convert("RGB")


def main():
    for slug in sys.argv[1:]:
        series = json.load(open(os.path.join(ROOT, "data/series", f"{slug}.json")))
        out_dir = os.path.join(ROOT, "site/public/img/series", slug)
        os.makedirs(out_dir, exist_ok=True)
        compose(slug, series).save(os.path.join(out_dir, "og.jpg"), "JPEG", quality=88, optimize=True)
        print(f"OK {slug} og.jpg")
        for s in series["seasons"]:
            compose(slug, series, s).save(os.path.join(out_dir, f"og-s{s['number']}.jpg"), "JPEG", quality=88, optimize=True)
            print(f"OK {slug} og-s{s['number']}.jpg")


if __name__ == "__main__":
    main()
