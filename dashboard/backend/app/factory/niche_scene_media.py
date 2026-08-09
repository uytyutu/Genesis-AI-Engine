"""Niche-character stills — as if a DE client filled the purchase form.

Offline Pillow scenes (no external AI). Each niche has its own silhouette,
palette and mood so Basic / Business / Premium share character, not a flat
gradient plate. Used by store_media + site media fallback.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

Role = Literal["hero", "product", "banner", "gallery"]

# German craft + commerce niches → (bg, accent, light)
_PALETTES: dict[str, tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]] = {
    # Visual language: each niche = distinct brand atmosphere (Studio Portfolio)
    "dachreinigung": ((14, 20, 32), (120, 170, 210), (40, 52, 70)),  # cool height / air
    "roof": ((14, 20, 32), (120, 170, 210), (40, 52, 70)),
    "zaunbau": ((28, 20, 12), (180, 120, 50), (58, 44, 28)),  # timber / material
    "fence": ((28, 20, 12), (180, 120, 50), (58, 44, 28)),
    "gartenpflege": ((8, 32, 18), (70, 175, 95), (28, 70, 42)),  # deep garden green
    "green": ((8, 32, 18), (70, 175, 95), (28, 70, 42)),
    "garden": ((8, 32, 18), (70, 175, 95), (28, 70, 42)),
    "handwerk": ((22, 14, 6), (250, 160, 20), (55, 40, 18)),  # workshop amber
    "maler": ((32, 26, 24), (210, 70, 50), (70, 48, 42)),
    "sanitaer": ((12, 26, 34), (60, 160, 200), (32, 58, 72)),
    "elektro": ((8, 12, 28), (255, 210, 40), (36, 44, 72)),
    "auto": ((8, 10, 14), (230, 40, 40), (32, 36, 44)),  # contrast / speed
    "auto_detailing": ((6, 8, 12), (200, 170, 70), (28, 32, 40)),  # gloss / night studio
    "auto_parts": ((16, 18, 22), (180, 50, 40), (40, 44, 52)),
    "car_dealership": ((20, 24, 32), (40, 90, 160), (48, 56, 72)),
    "orthodontics": ((248, 252, 254), (50, 170, 180), (226, 240, 244)),
    "family_psychology": ((246, 240, 232), (150, 110, 90), (228, 220, 210)),
    "cleaning": ((230, 240, 248), (40, 140, 200), (210, 224, 236)),
    "office_cleaning": ((224, 232, 240), (50, 120, 170), (200, 214, 228)),
    "photography": ((12, 12, 16), (220, 80, 60), (36, 36, 44)),
    "it_support": ((10, 16, 28), (40, 200, 180), (28, 40, 56)),
    "landschaft": ((12, 36, 24), (90, 160, 80), (32, 64, 44)),
    "dental": ((245, 250, 252), (40, 150, 190), (220, 232, 240)),  # sterile light
    "beauty": ((28, 14, 24), (210, 90, 150), (60, 28, 48)),
    "restaurant": ((18, 10, 8), (200, 90, 40), (48, 28, 20)),  # warm evening
    "food": ((18, 10, 8), (200, 90, 40), (48, 28, 20)),
    "fashion": ((18, 14, 12), (190, 90, 50), (48, 36, 32)),
    "clothing": ((18, 14, 12), (190, 90, 50), (48, 36, 32)),
    "electronics": ((6, 10, 22), (50, 120, 255), (24, 36, 64)),
    "computer": ((6, 10, 22), (50, 120, 255), (24, 36, 64)),
    "furniture": ((22, 16, 10), (170, 100, 45), (52, 40, 28)),
    "realestate": ((20, 24, 36), (100, 130, 190), (44, 52, 70)),
    "psychology": ((240, 236, 228), (100, 125, 115), (220, 214, 202)),  # calm editorial
    "law": ((248, 246, 240), (70, 70, 78), (220, 216, 208)),  # strict geometry / ink
    "fitness": ((6, 8, 12), (255, 60, 40), (28, 32, 40)),  # dynamic contrast
    "energy": ((6, 22, 30), (255, 190, 30), (28, 52, 60)),
    "accessories": ((14, 12, 10), (210, 170, 40), (42, 36, 28)),
    "jewelry": ((10, 8, 14), (230, 190, 70), (36, 30, 42)),
    "pets": ((26, 20, 14), (190, 130, 70), (56, 44, 34)),
    "coffee": ((22, 12, 8), (170, 95, 40), (52, 32, 22)),
    "sports": ((6, 8, 12), (255, 60, 40), (28, 32, 40)),
    "other": ((14, 16, 18), (52, 180, 140), (36, 42, 48)),
    "generic": ((14, 16, 18), (52, 180, 140), (36, 42, 48)),
}

_ALIASES: dict[str, str] = {
    "dach": "dachreinigung",
    "dachreinigung": "dachreinigung",
    "roof": "dachreinigung",
    "roofcleaning": "dachreinigung",
    "zaun": "zaunbau",
    "zaunbau": "zaunbau",
    "fence": "zaunbau",
    "fencing": "zaunbau",
    "garten": "gartenpflege",
    "gartenpflege": "gartenpflege",
    "garden": "gartenpflege",
    "green": "gartenpflege",
    "malerarbeiten": "maler",
    "painter": "maler",
    "plumbing": "sanitaer",
    "sanitär": "sanitaer",
    "electric": "elektro",
    "electrician": "elektro",
    "jewelry": "jewelry",
    "jewellery": "jewelry",
    "pets": "pets",
    "pet": "pets",
    "coffee": "coffee",
    "cafe": "coffee",
    "sports": "sports",
    "sport": "sports",
    "fitness": "fitness",
    "detailing": "auto_detailing",
    "autodetailing": "auto_detailing",
    "auto_detailing": "auto_detailing",
    "orthodontics": "orthodontics",
    "ortho": "orthodontics",
    "cleaning": "cleaning",
    "office_cleaning": "office_cleaning",
    "photography": "photography",
    "it_support": "it_support",
    "itsupport": "it_support",
    "landschaft": "landschaft",
    "landscape": "landschaft",
    "family_psychology": "family_psychology",
    "cardealership": "car_dealership",
    "car_dealership": "car_dealership",
    "familypsychology": "family_psychology",
}


def normalize_niche(niche_id: str | None) -> str:
    raw = (niche_id or "generic").strip().lower().replace(" ", "_")
    compact = raw.replace("_", "")
    if raw in _PALETTES:
        return raw
    mapped = _ALIASES.get(raw) or _ALIASES.get(compact)
    if mapped:
        return mapped
    for k in _PALETTES:
        if k.replace("_", "") == compact:
            return k
    return "generic"

def _palette(niche: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    n = normalize_niche(niche)
    return _PALETTES.get(n) or _PALETTES["generic"]


def _digest(*parts: str) -> bytes:
    return hashlib.sha256("|".join(parts).encode("utf-8")).digest()


def write_niche_scene(
    dest: Path,
    *,
    niche_id: str,
    seed: str = "",
    label: str = "",
    role: Role = "hero",
    size: tuple[int, int] | None = None,
    metaphor: str = "",
    accent_hex: str | None = None,
) -> Path:
    """Write a niche-character JPEG. Same niche → same family across tiers.

    Brand Book may pass metaphor (e.g. fresh rain after storm) to bias the scene.
    Never draws café / salon / SaaS plates.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    niche = normalize_niche(niche_id)
    bg, accent, light = _palette(niche)
    if accent_hex and accent_hex.startswith("#") and len(accent_hex) >= 7:
        try:
            accent = (
                int(accent_hex[1:3], 16),
                int(accent_hex[3:5], 16),
                int(accent_hex[5:7], 16),
            )
        except ValueError:
            pass
    dig = _digest(niche, seed, label, role, metaphor)
    if size is None:
        size = (1600, 900) if role in ("hero", "banner") else (900, 1120)
    w, h = size
    dest.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Sky wash — for roof niches lean cooler / higher (height + air)
    sky_bias = niche == "dachreinigung" or "rain" in (metaphor or "").lower() or "regen" in (metaphor or "").lower()
    for i in range(5):
        ox = int(dig[i] / 255 * w)
        oy = int(dig[i + 5] / 255 * (h * (0.45 if sky_bias else 1)))
        r = int(min(w, h) * (0.22 + dig[i + 10] / 255 * 0.32))
        wash = accent if i % 2 == 0 else light
        if sky_bias and i < 2:
            wash = (min(255, accent[0] + 40), min(255, accent[1] + 50), min(255, accent[2] + 70))
        overlay = Image.new("RGB", (w, h), wash)
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).ellipse((ox - r, oy - r, ox + r, oy + r), fill=35 + (i * 14) % 70)
        mask = mask.filter(ImageFilter.GaussianBlur(72))
        img = Image.composite(overlay, img, mask)
        draw = ImageDraw.Draw(img)

    # Horizon / ground plane
    ground_y = int(h * (0.58 if sky_bias else (0.62 if role in ("hero", "banner") else 0.72)))
    draw.rectangle((0, ground_y, w, h), fill=tuple(max(0, c - 8) for c in bg))

    _draw_niche_silhouette(
        draw,
        niche=niche,
        w=w,
        h=h,
        ground_y=ground_y,
        bg=bg,
        accent=accent,
        light=light,
        dig=dig,
        role=role,
        metaphor=metaphor,
        img=img,
    )

    if role in ("hero", "banner") and niche not in (
        "psychology",
        "family_psychology",
        "law",
        "dental",
    ):
        # Soft left veil for craft/commerce heroes; skip calm niches (fonts stay readable)
        veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        vdraw = ImageDraw.Draw(veil)
        for y in range(h):
            a = int(110 * (1 - y / h) ** 1.35)
            vdraw.line([(0, y), (int(w * 0.55), y)], fill=(8, 6, 4, a))
        img = Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
        draw = ImageDraw.Draw(img)
    elif niche in ("psychology", "family_psychology", "dental") and role in ("hero", "banner"):
        # Soft right wash so light interiors stay readable under copy panels
        veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        vdraw = ImageDraw.Draw(veil)
        for x in range(int(w * 0.55), w):
            t = (x - w * 0.55) / (w * 0.45)
            a = int(40 + 70 * t)
            col = (248, 246, 240, a) if niche != "dental" else (248, 250, 252, a)
            vdraw.line([(x, 0), (x, h)], fill=col)
        img = Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
        draw = ImageDraw.Draw(img)
    elif label:
        try:
            font = ImageFont.truetype("arial.ttf", 26)
        except OSError:
            font = ImageFont.load_default()
        text = (label or "")[:30]
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) / 2, h * 0.86), text, fill=(250, 250, 249), font=font)

    img = img.filter(ImageFilter.SMOOTH_MORE)
    img.save(dest, "JPEG", quality=92, optimize=True, progressive=True)
    return dest


def ensure_tier_media_floor(
    assets_dir: Path,
    *,
    niche_id: str,
    business_name: str = "",
    package_id: str = "business",
    metaphor: str = "",
    accent_hex: str | None = None,
) -> list[str]:
    """Business: hero + bg + gallery×3. Premium: Studio Renderer 2.0 full media floor."""
    pkg = (package_id or "basic").strip().lower()
    if pkg not in ("business", "premium", "connected"):
        # Basic still needs a hero plate
        dest = assets_dir / "hero.jpg"
        write_niche_scene(
            dest,
            niche_id=niche_id,
            seed=f"floor-hero|{business_name}|{pkg}",
            role="hero",
            size=(1600, 900),
            metaphor=metaphor,
            accent_hex=accent_hex,
        )
        return ["hero.jpg"]

    if pkg in ("premium", "connected"):
        try:
            from app.factory.studio_renderer_v2 import ensure_studio_media_floor

            return ensure_studio_media_floor(
                assets_dir,
                niche_id=niche_id,
                business_name=business_name,
                package_id=pkg,
                metaphor=metaphor,
                accent_hex=accent_hex,
            )
        except Exception:
            pass

    written: list[str] = []
    slots: list[tuple[str, Role, tuple[int, int]]] = [
        ("hero.jpg", "hero", (1600, 900)),
        ("background.jpg", "banner", (1920, 1080)),
        ("gallery_1.jpg", "gallery", (1200, 800)),
        ("gallery_2.jpg", "gallery", (1200, 800)),
        ("gallery_3.jpg", "gallery", (1200, 800)),
        ("illustration.jpg", "product", (1000, 1000)),
        ("gallery.jpg", "gallery", (1200, 800)),
    ]
    for name, role, size in slots:
        dest = assets_dir / name
        if dest.is_file() and dest.stat().st_size >= 4_000:
            written.append(name)
            continue
        write_niche_scene(
            dest,
            niche_id=niche_id,
            seed=f"floor|{name}|{business_name}|{pkg}",
            role=role,
            size=size,
            metaphor=metaphor,
            accent_hex=accent_hex,
        )
        written.append(name)
    return written


def _draw_niche_silhouette(
    draw,
    *,
    niche: str,
    w: int,
    h: int,
    ground_y: int,
    bg: tuple[int, int, int],
    accent: tuple[int, int, int],
    light: tuple[int, int, int],
    dig: bytes,
    role: Role,
    metaphor: str = "",
    img=None,
) -> None:
    """Readable craft silhouettes — form-like, not abstract blobs."""
    mid_x = w // 2
    shift = int((dig[0] - 128) / 128 * w * 0.06)

    if niche == "dachreinigung":
        # Fresh rain after storm — height, sky, wet tiles, mist (Brand Book metaphor)
        eaves_l, eaves_r = int(w * 0.10) + shift, int(w * 0.90) + shift
        ridge = mid_x + shift
        apex_y = int(h * 0.22)
        # Soft cloud bands in sky
        for i in range(4):
            cx = int(w * (0.15 + i * 0.22))
            cy = int(h * (0.08 + (dig[i] % 40) / 400))
            draw.ellipse(
                (cx - 90, cy - 28, cx + 110, cy + 36),
                fill=(70, 90, 110),
            )
        # Sun glow (post-storm)
        sx, sy = int(w * 0.78), int(h * 0.12)
        draw.ellipse((sx - 50, sy - 50, sx + 50, sy + 50), fill=(255, 210, 140))
        draw.ellipse((sx - 28, sy - 28, sx + 28, sy + 28), fill=(255, 236, 190))
        # Roof body
        tile = (max(20, light[0] - 10), max(24, light[1] - 5), min(255, light[2] + 15))
        draw.polygon(
            [(eaves_l, ground_y - 16), (ridge, apex_y), (eaves_r, ground_y - 16)],
            fill=tile,
        )
        # Wet tile lines + specular glints
        for i in range(9):
            y = apex_y + int((ground_y - 36 - apex_y) * (i + 1) / 10)
            t = (i + 1) / 10
            x0 = int(ridge + (eaves_l - ridge) * t)
            x1 = int(ridge + (eaves_r - ridge) * t)
            draw.line([(x0, y), (x1, y)], fill=tuple(min(255, c + 35) for c in tile), width=2)
            # water glint
            gx = x0 + int((x1 - x0) * ((dig[i % 16]) / 255))
            draw.ellipse((gx - 3, y - 2, gx + 8, y + 3), fill=(220, 235, 245))
        chim = [
            ridge + int(w * 0.08),
            apex_y + 18,
            ridge + int(w * 0.13),
            ground_y - int(h * 0.24),
        ]
        draw.rectangle(chim, fill=accent)
        # Pressure-wash mist / rain droplets
        for i in range(14):
            sx = eaves_l + int(w * 0.06) + i * int(w * 0.035)
            sy = apex_y + 30 + (i % 4) * 16
            draw.ellipse((sx, sy, sx + 22, sy + 14), fill=(180, 210, 230))
        for i in range(20):
            dx = int(dig[i % 16] / 255 * w)
            dy = int(h * 0.15) + int(dig[(i + 3) % 16] / 255 * h * 0.35)
            draw.ellipse((dx, dy, dx + 3, dy + 7), fill=(186, 230, 253))
        # Ladder + safety line hint
        lx = eaves_r - int(w * 0.1)
        draw.line([(lx, ground_y), (lx - 40, apex_y + 50)], fill=accent, width=6)
        draw.line([(lx + 28, ground_y), (lx - 12, apex_y + 50)], fill=accent, width=6)
        draw.line(
            [(lx - 20, apex_y + 80), (ridge + 20, apex_y + 40)],
            fill=(234, 88, 12),
            width=3,
        )
        # Worker silhouette on roof (guardian)
        wx, wy = ridge - int(w * 0.05), apex_y + int(h * 0.12)
        draw.ellipse((wx - 8, wy - 22, wx + 8, wy - 6), fill=(30, 35, 40))
        draw.rectangle((wx - 10, wy - 6, wx + 10, wy + 28), fill=(40, 48, 55))
        # Before/After demo bias — moss vs clean wash
        meta_l = (metaphor or "").lower()
        if "before" in meta_l or "moos" in meta_l or "dirty" in meta_l:
            for i in range(18):
                mx = eaves_l + int((eaves_r - eaves_l) * ((dig[i % 16]) / 255))
                my = apex_y + 40 + int((ground_y - apex_y - 80) * ((dig[(i + 5) % 16]) / 255))
                draw.ellipse(
                    (mx - 10, my - 6, mx + 14, my + 10),
                    fill=(48, 72, 42),
                )
        elif "after" in meta_l or "clean" in meta_l:
            for i in range(10):
                y = apex_y + int((ground_y - 40 - apex_y) * (i + 1) / 11)
                t = (i + 1) / 11
                x0 = int(ridge + (eaves_l - ridge) * t)
                x1 = int(ridge + (eaves_r - ridge) * t)
                draw.line(
                    [(x0, y), (x1, y)],
                    fill=(200, 220, 230),
                    width=1,
                )

    elif niche == "zaunbau":
        # Fence posts + rails + gate gap
        post_w = max(10, w // 55)
        n_posts = 9 if role != "product" else 5
        span = int(w * 0.78)
        start = int(w * 0.11) + shift
        top = int(h * 0.34)
        for i in range(n_posts):
            x = start + int(span * i / max(1, n_posts - 1))
            draw.rectangle((x, top, x + post_w, ground_y), fill=accent)
            # Cap
            draw.polygon(
                [(x - 4, top), (x + post_w // 2, top - 18), (x + post_w + 4, top)],
                fill=light,
            )
        rail_y1, rail_y2 = int(h * 0.48), int(h * 0.58)
        draw.rectangle((start, rail_y1, start + span + post_w, rail_y1 + 10), fill=light)
        draw.rectangle((start, rail_y2, start + span + post_w, rail_y2 + 10), fill=light)
        # Hedge silhouette behind
        for i in range(12):
            hx = start + i * (span // 11)
            hh = 40 + (dig[i % 16] % 50)
            draw.ellipse((hx, ground_y - hh, hx + 70, ground_y + 10), fill=(40, 70, 45))

    elif niche == "gartenpflege":
        # Path + bushes + tree + lawn stripes
        draw.polygon(
            [
                (mid_x - 40 + shift, ground_y),
                (mid_x + 40 + shift, ground_y),
                (int(w * 0.72) + shift, int(h * 0.95)),
                (int(w * 0.28) + shift, int(h * 0.95)),
            ],
            fill=(70, 60, 45),
        )
        # Tree
        trunk_x = int(w * 0.72) + shift
        draw.rectangle((trunk_x, int(h * 0.38), trunk_x + 28, ground_y), fill=(90, 60, 35))
        draw.ellipse(
            (trunk_x - 70, int(h * 0.18), trunk_x + 100, int(h * 0.52)),
            fill=accent,
        )
        # Bushes
        for i, bx in enumerate((0.18, 0.32, 0.48)):
            x = int(w * bx) + shift
            draw.ellipse((x, ground_y - 70 - i * 8, x + 110, ground_y + 8), fill=light)
        # Lawn mower hint
        mx = int(w * 0.22) + shift
        draw.rounded_rectangle((mx, ground_y - 36, mx + 90, ground_y - 8), radius=8, fill=accent)
        draw.ellipse((mx - 8, ground_y - 20, mx + 18, ground_y + 6), fill=light)
        draw.ellipse((mx + 70, ground_y - 20, mx + 96, ground_y + 6), fill=light)

    elif niche == "handwerk":
        # Site materials · amber work light · tools · dust — role shifts camera
        var = dig[3] % 3
        left, right = int(w * 0.18) + shift, int(w * 0.82) + shift
        top = int(h * (0.28 if role == "hero" else 0.34))
        # Scaffold / timber frame
        draw.rectangle((left, top, right, ground_y), fill=light)
        ridge_y = int(h * 0.16) + (dig[4] % 20)
        draw.polygon(
            [(left - 24, top), ((left + right) // 2, ridge_y), (right + 24, top)],
            fill=accent,
        )
        # Studs
        for i in range(4):
            x = left + int((right - left) * (0.15 + i * 0.2))
            draw.rectangle((x, top + 8, x + 14, ground_y - 8), fill=tuple(max(0, c - 20) for c in light))
        # Dust motes
        for i in range(18):
            mx = int(dig[i % 16] / 255 * w)
            my = int(dig[(i + 3) % 16] / 255 * h * 0.7)
            draw.ellipse((mx, my, mx + 3, my + 3), fill=(255, 210, 140))
        # Tools on ground
        hx = int(w * (0.62 if var else 0.28)) + shift
        hy = ground_y - 40
        draw.rectangle((hx, hy, hx + 110, hy + 16), fill=accent)
        draw.rectangle((hx + 88, hy - 32, hx + 120, hy + 48), fill=(40, 28, 14))
        if role == "gallery":
            # Close materials stack
            bx = int(w * 0.12) + shift
            for i in range(4):
                draw.rectangle(
                    (bx, ground_y - 28 - i * 18, bx + 160 + i * 10, ground_y - 12 - i * 18),
                    fill=accent if i % 2 == 0 else light,
                )

    elif niche == "car_dealership":
        # Wet asphalt · headlights · reflections · metal — cinematic night
        var = dig[2] % 3
        # Rain streaks
        for i in range(40):
            rx = int((dig[i % 16] / 255) * w)
            ry = int((dig[(i + 5) % 16] / 255) * h * 0.55)
            draw.line((rx, ry, rx + 2, ry + 28 + (i % 12)), fill=(70, 90, 120), width=1)
        # Wet road reflections
        for i in range(8):
            y = ground_y + i * 8
            draw.rectangle(
                (0, y, w, y + 4),
                fill=(30 + i * 4, 40 + i * 3, 55 + i * 2),
            )
        # Car body silhouette — different camera per role
        cx = mid_x + shift + (var - 1) * int(w * 0.08)
        body_y = int(h * (0.46 if role == "hero" else 0.5))
        draw.rounded_rectangle(
            (cx - int(w * 0.32), body_y, cx + int(w * 0.32), ground_y - 12),
            radius=28,
            fill=light,
        )
        draw.polygon(
            [
                (cx - int(w * 0.18), body_y),
                (cx - int(w * 0.08), int(h * 0.32)),
                (cx + int(w * 0.12), int(h * 0.32)),
                (cx + int(w * 0.24), body_y),
            ],
            fill=accent,
        )
        # Headlights glow
        for side in (-1, 1):
            hx = cx + side * int(w * 0.26)
            draw.ellipse(
                (hx - 55, body_y, hx + 55, body_y + 95),
                fill=(90, 70, 40),
            )
            draw.ellipse(
                (hx - 28, body_y + 20, hx + 28, body_y + 70),
                fill=(255, 240, 200),
            )
            draw.ellipse(
                (hx - 12, body_y + 32, hx + 12, body_y + 56),
                fill=(255, 255, 255),
            )
        # Wheels
        for wx in (cx - int(w * 0.2), cx + int(w * 0.16)):
            draw.ellipse((wx, ground_y - 55, wx + 70, ground_y + 5), fill=bg)
            draw.ellipse((wx + 18, ground_y - 38, wx + 52, ground_y - 10), fill=accent)

    elif niche == "maler":
        wall_l = int(w * 0.2) + shift
        draw.rectangle((wall_l, int(h * 0.25), wall_l + int(w * 0.45), ground_y), fill=light)
        # Paint roller streak
        for i in range(5):
            y = int(h * 0.32) + i * 28
            draw.rectangle((wall_l + 20, y, wall_l + int(w * 0.38), y + 16), fill=accent)
        # Bucket
        bx = int(w * 0.68) + shift
        draw.ellipse((bx, ground_y - 50, bx + 70, ground_y - 10), fill=accent)
        draw.rectangle((bx + 8, ground_y - 90, bx + 62, ground_y - 30), fill=light)

    elif niche == "sanitaer":
        # Vanity + faucet silhouette
        vanity = [int(w * 0.25) + shift, int(h * 0.52), int(w * 0.75) + shift, ground_y - 10]
        draw.rounded_rectangle(vanity, radius=16, fill=light)
        cx = mid_x + shift
        draw.ellipse((cx - 55, int(h * 0.42), cx + 55, int(h * 0.58)), fill=bg)
        draw.rectangle((cx - 8, int(h * 0.28), cx + 8, int(h * 0.45)), fill=accent)
        draw.rectangle((cx - 35, int(h * 0.28), cx + 8, int(h * 0.34)), fill=accent)

    elif niche == "elektro":
        # Panel + cable arcs + bolt
        panel = [int(w * 0.35) + shift, int(h * 0.28), int(w * 0.65) + shift, ground_y - 20]
        draw.rounded_rectangle(panel, radius=12, fill=light)
        for i in range(4):
            y = int(h * 0.36) + i * 40
            draw.rectangle((panel[0] + 30, y, panel[2] - 30, y + 18), fill=accent)
        # Bolt
        bx, by = int(w * 0.72) + shift, int(h * 0.4)
        draw.polygon(
            [(bx, by), (bx + 35, by + 40), (bx + 12, by + 40), (bx + 40, by + 95), (bx - 5, by + 50), (bx + 18, by + 50)],
            fill=accent,
        )

    elif niche in ("restaurant", "food"):
        # Fire · ember · steam · close food light — warm night
        var = dig[1] % 3
        # Ember base
        for i in range(12):
            ex = mid_x + shift + int((dig[i % 16] - 128) / 128 * w * 0.25)
            ey = ground_y - 20 - (i % 4) * 12
            r = 18 + (i % 5) * 6
            draw.ellipse(
                (ex - r, ey - r, ex + r, ey + r),
                fill=(220 - i * 8, 60 + i * 4, 20),
            )
        # Flame tongues
        cx = mid_x + shift
        for i in range(5):
            fx = cx - 40 + i * 20
            draw.polygon(
                [
                    (fx, ground_y - 40),
                    (fx + 18, int(h * (0.28 + (dig[i] % 20) / 200))),
                    (fx + 36, ground_y - 40),
                ],
                fill=accent if i % 2 == 0 else (255, 160, 60),
            )
        # Plate / knife close-up for gallery
        if role in ("gallery", "product") or var == 2:
            draw.ellipse(
                (cx - 140, int(h * 0.42), cx + 140, int(h * 0.72)),
                fill=light,
            )
            draw.ellipse(
                (cx - 90, int(h * 0.48), cx + 90, int(h * 0.66)),
                fill=(40, 22, 14),
            )
            draw.ellipse((cx - 35, int(h * 0.52), cx + 35, int(h * 0.6)), fill=accent)
        # Steam
        for i in range(4):
            sx = cx - 40 + i * 28
            draw.arc(
                (sx, int(h * 0.22), sx + 30, int(h * 0.42)),
                200,
                340,
                fill=(230, 220, 210),
                width=3,
            )

    elif niche in ("beauty", "fashion", "clothing", "accessories"):
        # Soft oval + bottle / garment
        cx = mid_x + shift
        draw.ellipse((cx - 140, int(h * 0.28), cx + 140, int(h * 0.78)), fill=light)
        draw.rounded_rectangle(
            (cx - 35, int(h * 0.36), cx + 35, int(h * 0.68)),
            radius=18,
            fill=accent,
        )
        draw.ellipse((cx - 22, int(h * 0.3), cx + 22, int(h * 0.38)), fill=accent)

    elif niche == "jewelry":
        # Ring / gem plate — not a salon interior
        cx = mid_x + shift
        draw.ellipse((cx - 90, int(h * 0.34), cx + 90, int(h * 0.62)), outline=accent, width=10)
        draw.polygon(
            [
                (cx, int(h * 0.28)),
                (cx + 38, int(h * 0.42)),
                (cx, int(h * 0.52)),
                (cx - 38, int(h * 0.42)),
            ],
            fill=accent,
        )
        draw.ellipse((cx - 18, int(h * 0.40), cx + 18, int(h * 0.48)), fill=light)

    elif niche == "pets":
        # Soft pet silhouette (ears + body)
        cx = mid_x + shift
        draw.ellipse((cx - 110, int(h * 0.42), cx + 110, int(h * 0.72)), fill=light)
        draw.ellipse((cx - 55, int(h * 0.28), cx - 5, int(h * 0.48)), fill=accent)
        draw.ellipse((cx + 5, int(h * 0.28), cx + 55, int(h * 0.48)), fill=accent)
        draw.ellipse((cx - 70, int(h * 0.34), cx + 70, int(h * 0.58)), fill=light)

    elif niche == "coffee":
        # Cup + steam
        cx = mid_x + shift
        draw.rounded_rectangle(
            (cx - 70, int(h * 0.40), cx + 70, int(h * 0.68)),
            radius=16,
            fill=light,
        )
        draw.arc((cx + 55, int(h * 0.46), cx + 105, int(h * 0.62)), 270, 90, fill=accent, width=8)
        for sx in (-18, 0, 18):
            draw.arc(
                (cx + sx - 8, int(h * 0.26), cx + sx + 8, int(h * 0.40)),
                200,
                340,
                fill=accent,
                width=3,
            )

    elif niche == "auto":
        # Workshop lift + vehicle body (not gym weights)
        body = [int(w * 0.18) + shift, int(h * 0.48), int(w * 0.82) + shift, int(h * 0.68)]
        draw.rounded_rectangle(body, radius=20, fill=light)
        draw.polygon(
            [
                (int(w * 0.32) + shift, int(h * 0.48)),
                (int(w * 0.42) + shift, int(h * 0.34)),
                (int(w * 0.62) + shift, int(h * 0.34)),
                (int(w * 0.72) + shift, int(h * 0.48)),
            ],
            fill=accent,
        )
        for wx in (0.3, 0.68):
            x = int(w * wx) + shift
            draw.ellipse((x, int(h * 0.62), x + 70, int(h * 0.78)), fill=bg)
        # Lift posts
        for px in (0.22, 0.75):
            x = int(w * px) + shift
            draw.rectangle((x, int(h * 0.28), x + 18, int(h * 0.72)), fill=accent)

    elif niche == "auto_detailing":
        # Gloss car + polish glow
        cx = mid_x + shift
        draw.ellipse((cx - 220, int(h * 0.42), cx + 220, int(h * 0.78)), fill=light)
        draw.polygon(
            [
                (cx - 160, int(h * 0.52)),
                (cx - 80, int(h * 0.34)),
                (cx + 90, int(h * 0.34)),
                (cx + 170, int(h * 0.52)),
                (cx + 160, int(h * 0.68)),
                (cx - 150, int(h * 0.68)),
            ],
            fill=accent,
        )
        draw.ellipse((cx - 40, int(h * 0.22), cx + 40, int(h * 0.34)), fill=(255, 240, 180))

    elif niche in ("fitness", "sports"):
        # Weight plate + bar
        cx = mid_x + shift
        draw.rectangle((cx - 200, int(h * 0.48), cx + 200, int(h * 0.54)), fill=light)
        for side in (-1, 1):
            x = cx + side * 170
            draw.ellipse((x - 55, int(h * 0.38), x + 55, int(h * 0.64)), fill=accent)
            draw.ellipse((x - 28, int(h * 0.44), x + 28, int(h * 0.58)), fill=bg)

    elif niche in ("cleaning", "office_cleaning"):
        # Window facade + mop silhouette
        for i in range(3):
            x = int(w * 0.28) + i * int(w * 0.16) + shift
            draw.rectangle((x, int(h * 0.28), x + int(w * 0.12), int(h * 0.68)), outline=light, width=6)
            draw.rectangle((x + 8, int(h * 0.34), x + int(w * 0.12) - 8, int(h * 0.48)), fill=accent)
        draw.line(
            (int(w * 0.2) + shift, int(h * 0.72), int(w * 0.55) + shift, int(h * 0.42)),
            fill=accent,
            width=8,
        )

    elif niche == "photography":
        # Softbox + camera body
        cx = mid_x + shift
        draw.ellipse((cx - 120, int(h * 0.22), cx + 120, int(h * 0.48)), fill=light)
        draw.rounded_rectangle(
            (cx - 70, int(h * 0.48), cx + 70, int(h * 0.68)),
            radius=12,
            fill=accent,
        )
        draw.ellipse((cx - 28, int(h * 0.52), cx + 28, int(h * 0.64)), fill=bg)

    elif niche == "orthodontics":
        # Smile arc + aligner tray
        cx = mid_x + shift
        draw.arc((cx - 110, int(h * 0.36), cx + 110, int(h * 0.7)), 20, 160, fill=accent, width=14)
        draw.rounded_rectangle(
            (cx - 90, int(h * 0.55), cx + 90, int(h * 0.68)),
            radius=20,
            fill=light,
        )

    elif niche in ("computer", "it_support"):
        draw.rounded_rectangle(
            (int(w * 0.22) + shift, int(h * 0.28), int(w * 0.78) + shift, int(h * 0.62)),
            radius=18,
            fill=light,
        )
        draw.rectangle(
            (int(w * 0.28) + shift, int(h * 0.34), int(w * 0.72) + shift, int(h * 0.56)),
            fill=accent,
        )
        draw.rectangle(
            (mid_x - 40 + shift, int(h * 0.62), mid_x + 40 + shift, int(h * 0.68)),
            fill=light,
        )
        # Circuit dots
        for i in range(5):
            x = int(w * 0.3) + i * 70 + shift
            draw.ellipse((x, int(h * 0.72), x + 12, int(h * 0.76)), fill=accent)

    elif niche == "dental":
        # Glass · soft clinical light · clean depth — not empty white blob
        var = dig[0] % 3
        # Soft window light from left
        for i in range(6):
            x0 = int(w * 0.08) + i * 18
            draw.rectangle(
                (x0, int(h * 0.12), x0 + 10, int(h * 0.55)),
                fill=(255, 255, 255),
            )
        # Glass panel
        gx = int(w * 0.42) + shift
        draw.rounded_rectangle(
            (gx, int(h * 0.22), gx + int(w * 0.38), ground_y - 20),
            radius=8,
            fill=light,
        )
        draw.rectangle(
            (gx + 24, int(h * 0.3), gx + int(w * 0.32), int(h * 0.55)),
            fill=(230, 245, 250),
        )
        # Soft reflection streak
        draw.polygon(
            [
                (gx + 40, int(h * 0.28)),
                (gx + 70, int(h * 0.28)),
                (gx + 50, int(h * 0.7)),
                (gx + 20, int(h * 0.7)),
            ],
            fill=(255, 255, 255),
        )
        # Chair / treatment hint
        if role != "product":
            cx = int(w * 0.28) + shift
            draw.ellipse((cx, int(h * 0.48), cx + 120, ground_y - 8), fill=accent)
            draw.rounded_rectangle(
                (cx + 30, int(h * 0.38), cx + 90, int(h * 0.52)),
                radius=20,
                fill=light,
            )
        if var == 1:
            # Smile arc detail for gallery variety
            sx = mid_x + shift
            draw.arc((sx - 80, int(h * 0.4), sx + 80, int(h * 0.7)), 30, 150, fill=accent, width=10)

    elif niche == "psychology" or niche == "family_psychology":
        # Morning light · wood · book · tea · quiet chamber
        var = dig[5] % 3
        # Wood floor planks
        for i in range(8):
            y = ground_y + i * 6
            draw.rectangle(
                (0, y, w, y + 4),
                fill=(210 - i * 4, 190 - i * 3, 160 - i * 2),
            )
        # Window light pool
        draw.polygon(
            [
                (int(w * 0.55) + shift, int(h * 0.1)),
                (int(w * 0.95) + shift, int(h * 0.1)),
                (int(w * 0.78) + shift, ground_y),
                (int(w * 0.35) + shift, ground_y),
            ],
            fill=(255, 248, 230),
        )
        # Soft chairs — spacing varies by role
        gap = 0.22 if niche == "family_psychology" else 0.26
        for i, bx in enumerate((0.22, 0.22 + gap)):
            x = int(w * bx) + shift
            seat_y = int(h * (0.48 if role == "hero" else 0.5))
            draw.rounded_rectangle(
                (x, seat_y, x + int(w * 0.18), ground_y - 8),
                radius=22,
                fill=light,
            )
            draw.ellipse(
                (x + 20, seat_y - 50, x + int(w * 0.14), seat_y + 10),
                fill=accent if i == 0 else (200, 185, 165),
            )
        # Side table + book + tea
        tx = int(w * 0.72) + shift
        table_top = min(int(h * 0.58), ground_y - 40)
        draw.rectangle((tx, table_top, tx + 90, max(table_top + 1, ground_y - 10)), fill=(120, 90, 60))
        draw.rectangle((tx + 15, max(8, table_top - 20), tx + 75, table_top), fill=accent)
        cup_y = max(8, table_top - 40)
        draw.ellipse((tx + 30, cup_y, tx + 58, cup_y + 24), fill=(240, 230, 210))
        if var == 2 or role == "gallery":
            # Plant silhouette
            px = int(w * 0.12) + shift
            plant_top = min(int(h * 0.5), ground_y - 20)
            draw.rectangle((px + 28, plant_top, px + 42, max(plant_top + 1, ground_y)), fill=(90, 70, 50))
            leaf_y = max(8, plant_top - int(h * 0.18))
            draw.ellipse((px, leaf_y, px + 70, plant_top + 10), fill=(100, 130, 105))

    elif niche == "energy" or niche == "landschaft":
        # House + sun / panels (energy) or path (landscape via panels as beds)
        left = int(w * 0.3) + shift
        draw.rectangle((left, int(h * 0.42), left + int(w * 0.28), ground_y), fill=light)
        draw.polygon(
            [
                (left - 15, int(h * 0.42)),
                (left + int(w * 0.14), int(h * 0.26)),
                (left + int(w * 0.28) + 15, int(h * 0.42)),
            ],
            fill=accent,
        )
        px = left + int(w * 0.32)
        for i in range(3):
            draw.rectangle(
                (px, int(h * 0.48) + i * 28, px + 100, int(h * 0.48) + i * 28 + 20),
                fill=(30, 60, 90) if niche == "energy" else accent,
            )
        sx, sy = int(w * 0.78) + shift, int(h * 0.22)
        draw.ellipse((sx, sy, sx + 70, sy + 70), fill=accent)

    elif niche in ("electronics",):
        draw.rounded_rectangle(
            (int(w * 0.22) + shift, int(h * 0.28), int(w * 0.78) + shift, int(h * 0.62)),
            radius=18,
            fill=light,
        )
        draw.rectangle(
            (int(w * 0.28) + shift, int(h * 0.34), int(w * 0.72) + shift, int(h * 0.56)),
            fill=accent,
        )
        draw.rectangle(
            (mid_x - 40 + shift, int(h * 0.62), mid_x + 40 + shift, int(h * 0.68)),
            fill=light,
        )

    elif niche in ("law", "realestate", "furniture"):
        # Columns / facade
        for i in range(4):
            x = int(w * 0.25) + i * int(w * 0.14) + shift
            draw.rectangle((x, int(h * 0.3), x + 36, ground_y), fill=light)
        draw.rectangle(
            (int(w * 0.22) + shift, int(h * 0.28), int(w * 0.78) + shift, int(h * 0.34)),
            fill=accent,
        )

    else:
        # Generic storefront
        left = int(w * 0.28) + shift
        draw.rectangle((left, int(h * 0.35), left + int(w * 0.44), ground_y), fill=light)
        draw.rectangle((left + 30, int(h * 0.45), left + int(w * 0.38), int(h * 0.62)), fill=accent)


def ensure_niche_hero(
    dest: Path,
    *,
    niche_id: str,
    business_name: str = "",
    package_id: str = "business",
) -> Path:
    """Site hero fallback — same niche character for every package tier."""
    return write_niche_scene(
        dest,
        niche_id=niche_id,
        seed=f"{business_name}|{package_id}|hero",
        label="",
        role="hero",
        size=(1600, 900),
    )


__all__ = [
    "ensure_niche_hero",
    "ensure_tier_media_floor",
    "normalize_niche",
    "write_niche_scene",
]
