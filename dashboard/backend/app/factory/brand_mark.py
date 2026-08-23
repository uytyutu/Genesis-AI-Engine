"""Short individual brand marks — monogram + display name (never long legal wordmarks)."""

from __future__ import annotations

import hashlib
import html as html_lib
import re


def short_brand_name(full_name: str, *, max_words: int = 2, max_chars: int = 18) -> str:
    """Display name for logos — short, human, not a legal paragraph."""
    raw = re.sub(r"\s+", " ", (full_name or "").strip())
    if not raw:
        return "Studio"
    # Drop common legal suffixes
    cleaned = re.sub(
        r"\b(gmbh|ug|ag|ltd|llc|inc|co\.?|sarl|s\.?r\.?l\.?|kg|ohg|e\.?k\.?)\b\.?",
        "",
        raw,
        flags=re.I,
    ).strip(" -|,.")
    words = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß0-9&']+", cleaned or raw) if w]
    if not words:
        return raw[:max_chars]
    pick = " ".join(words[:max_words])
    if len(pick) > max_chars and words:
        pick = words[0][:max_chars]
    return pick or raw[:max_chars]


def brand_initials(full_name: str) -> str:
    words = re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", full_name or "")
    if not words:
        return "VC"
    if len(words) == 1:
        w = words[0]
        return (w[:2] if len(w) >= 2 else w[:1]).upper()
    return (words[0][0] + words[1][0]).upper()


def _hue_from_name(name: str, niche: str = "") -> tuple[int, int, int]:
    seed = f"{niche}|{name}".encode("utf-8")
    h = int(hashlib.sha256(seed).hexdigest()[:6], 16)
    # Niche-biased palettes (avoid generic purple)
    niche_bias = {
        "restaurant": (28, 72, 48),
        "beauty": (330, 55, 42),
        "auto": (210, 35, 28),
        "fashion": (20, 40, 22),
        "food": (140, 45, 32),
        "psychology": (150, 28, 30),
        "handwerk": (35, 55, 38),
    }.get((niche or "").lower(), (None, None, None))
    if niche_bias[0] is not None:
        hue = (niche_bias[0] + (h % 40) - 20) % 360
        sat = niche_bias[1]
        lit = niche_bias[2]
    else:
        hue = h % 360
        sat = 35 + (h % 25)
        lit = 28 + (h % 18)
    return _hsl_to_rgb(hue / 360, sat / 100, lit / 100)


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    def hue2rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        v = int(round(l * 255))
        return v, v, v
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = hue2rgb(p, q, h + 1 / 3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1 / 3)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def brand_mark_svg(
    full_name: str,
    *,
    niche: str = "",
    size: int = 40,
    accent: str | None = None,
) -> str:
    """Inline SVG monogram — unique per brand, compact."""
    initials = brand_initials(full_name)
    r, g, b = _hue_from_name(full_name, niche)
    if accent and accent.startswith("#") and len(accent) in (4, 7):
        fill = accent
    else:
        fill = f"rgb({r},{g},{b})"
    # Shape variety from hash
    variant = int(hashlib.md5(f"{full_name}|{niche}".encode()).hexdigest()[:2], 16) % 4
    if variant == 0:
        shape = f'<rect x="2" y="2" width="{size-4}" height="{size-4}" rx="10" fill="{fill}"/>'
    elif variant == 1:
        shape = f'<circle cx="{size/2}" cy="{size/2}" r="{size/2-2}" fill="{fill}"/>'
    elif variant == 2:
        shape = (
            f'<path d="M{size/2} 2 L{size-2} {size*0.78} L2 {size*0.78} Z" fill="{fill}"/>'
        )
    else:
        shape = (
            f'<rect x="2" y="2" width="{size-4}" height="{size-4}" rx="4" fill="{fill}"/>'
            f'<rect x="8" y="8" width="{size-16}" height="{size-16}" rx="2" fill="rgba(255,255,255,0.18)"/>'
        )
    safe_i = html_lib.escape(initials[:2])
    return (
        f'<svg class="brand-mark" width="{size}" height="{size}" viewBox="0 0 {size} {size}" '
        f'aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        f"{shape}"
        f'<text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle" '
        f'fill="#fafaf9" font-family="Georgia,serif" font-size="{max(12, size // 2.4)}" '
        f'font-weight="700">{safe_i}</text></svg>'
    )


def site_logo_html(
    business_name: str,
    *,
    niche: str = "",
    src: str = "assets/logo.png",
    accent: str | None = None,
    use_img: bool = True,
) -> str:
    display = short_brand_name(business_name)
    safe_full = html_lib.escape(business_name)
    safe_disp = html_lib.escape(display)
    mark = brand_mark_svg(business_name, niche=niche, accent=accent)
    img = ""
    if use_img:
        logo = html_lib.escape(src or "assets/logo.png")
        img = (
            f'<img class="brand-logo-img" src="{logo}" alt="{safe_full}" '
            f'onerror="this.style.display=\'none\';var m=this.nextElementSibling;'
            f'if(m)m.style.display=\'inline-flex\'">'
        )
    return (
        f'<span class="brand-lockup" title="{safe_full}">'
        f"{img}"
        f'<span class="brand-mark-wrap" style="{"display:none" if use_img else "display:inline-flex"}">{mark}</span>'
        f'<strong class="brand-word">{safe_disp}</strong>'
        f"</span>"
    )


def store_logo_html(
    store_name: str,
    *,
    niche: str = "",
    accent: str | None = None,
    href: str = "index.html",
) -> str:
    display = short_brand_name(store_name)
    safe_full = html_lib.escape(store_name)
    safe_disp = html_lib.escape(display)
    mark = brand_mark_svg(store_name, niche=niche, size=36, accent=accent)
    return (
        f'<a class="brand brand-lockup" href="{html_lib.escape(href)}" title="{safe_full}">'
        f'<span class="brand-mark-wrap">{mark}</span>'
        f'<strong class="brand-word">{safe_disp}</strong>'
        f"</a>"
    )
