"""Extract measurable signals from HTML — shared by public URL + Virtus local scan."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


def _find(pattern: str, html: str, flags: int = re.I | re.S) -> re.Match[str] | None:
    return re.search(pattern, html or "", flags)


def extract_signals(html: str, *, final_url: str = "", headers: dict[str, str] | None = None) -> dict[str, Any]:
    html = html or ""
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    lower = html.lower()

    title_m = _find(r"<title[^>]*>(.*?)</title>", html)
    title = re.sub(r"\s+", " ", (title_m.group(1) if title_m else "")).strip()

    desc_m = _find(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
        html,
    ) or _find(
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
        html,
    )
    description = (desc_m.group(1).strip() if desc_m else "")

    viewport = bool(_find(r'<meta[^>]+name=["\']viewport["\']', html))
    h1_count = len(re.findall(r"<h1\b", html, re.I))
    imgs = re.findall(r"<img\b[^>]*>", html, re.I)
    missing_alt = sum(1 for t in imgs if not re.search(r"\balt\s*=", t, re.I))
    lazy = bool(re.search(r'loading=["\']lazy["\']', html, re.I))
    og = bool(re.search(r'property=["\']og:', html, re.I) or "og:title" in lower)
    canonical = bool(_find(r'rel=["\']canonical["\']', html))
    https = (final_url or "").lower().startswith("https://")
    if not final_url and headers.get("x-forwarded-proto") == "https":
        https = True

    # Legal / DE
    impressum = bool(
        re.search(r"impressum", lower)
        or re.search(r'href=["\'][^"\']*impressum', lower)
    )
    datenschutz = bool(
        re.search(r"datenschutz|privacy\s*policy|datenschutzerklärung", lower)
        or re.search(r'href=["\'][^"\']*datenschutz', lower)
        or re.search(r'href=["\'][^"\']*privacy', lower)
    )
    cookie = bool(
        re.search(r"cookie", lower)
        or re.search(r"consent", lower)
        or "cookiebanner" in lower.replace(" ", "")
    )
    kontakt = bool(
        re.search(r"kontakt|contact|mailto:", lower)
        or re.search(r'href=["\'][^"\']*kontakt', lower)
        or re.search(r'href=["\']#contact', lower)
    )

    forms = bool(re.search(r"<form\b|contact-form", lower))
    cta = bool(
        re.search(
            r"\b(cta|btn|button|jetzt|anfragen|buchen|kontaktieren|call|book|order)\b",
            lower,
        )
    )
    maps = bool(
        re.search(r"google\.(com|de)/maps|maps\.google|openstreetmap|leaflet", lower)
    )
    social = bool(
        re.search(
            r"instagram\.com|facebook\.com|linkedin\.com|tiktok\.com|x\.com|twitter\.com|youtube\.com",
            lower,
        )
    )
    trust = bool(
        re.search(
            r"trusted|zertifiziert|mitglied|garantie|reviews?|bewertung|kundenstimmen|testimonial",
            lower,
        )
    )
    reviews = bool(
        re.search(r"review|bewertung|google.?rating|sterne|★★|⭐", lower)
        or re.search(r"itemprop=[\"']aggregateRating", lower)
    )

    # Accessibility / a11y heuristics
    lang_attr = bool(_find(r"<html[^>]+lang=", html))
    skip_link = bool(re.search(r"skip.?to.?content|zum.?inhalt", lower))
    aria = bool(re.search(r"\baria-|role=", lower))

    # Performance heuristics
    heavy_fonts = bool(
        re.search(r"fonts\.googleapis|fonts\.gstatic|font-awesome|typekit", lower)
    )
    heavy_js = len(re.findall(r"<script\b", html, re.I))
    inline_css_big = len(html) > 350_000

    text_only = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text_only = re.sub(r"<style[\s\S]*?</style>", " ", text_only, flags=re.I)
    text_only = re.sub(r"<[^>]+>", " ", text_only)
    text_len = len(re.sub(r"\s+", " ", text_only).strip())

    host = ""
    try:
        host = (urlparse(final_url).hostname or "").lower()
    except Exception:
        host = ""

    return {
        "title": title,
        "description": description,
        "viewport": viewport,
        "h1_count": h1_count,
        "img_count": len(imgs),
        "missing_alt": missing_alt,
        "lazy_loading": lazy,
        "open_graph": og,
        "canonical": canonical,
        "https": https,
        "impressum": impressum,
        "datenschutz": datenschutz,
        "cookie": cookie,
        "kontakt": kontakt,
        "forms": forms,
        "cta": cta,
        "maps": maps,
        "social": social,
        "trust": trust,
        "reviews": reviews,
        "lang_attr": lang_attr,
        "skip_link": skip_link,
        "aria": aria,
        "heavy_fonts": heavy_fonts,
        "script_count": heavy_js,
        "large_html": inline_css_big,
        "text_len": text_len,
        "host": host,
        "html_bytes": len(html.encode("utf-8", errors="replace")),
    }
