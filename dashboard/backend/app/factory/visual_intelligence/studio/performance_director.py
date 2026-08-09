"""Performance Director — Luxury must not make the site slow."""

from __future__ import annotations

import re
from typing import Any

ENGINE_ID = "performance_director_v1"
MOBILE_FAIL = 70


def decide_performance(
    *,
    package_id: str,
    luxury_mode: bool = False,
    allow_video: bool | str | None = None,
) -> dict[str, Any]:
    pid = (package_id or "basic").strip().lower()
    # Creative may say video "if_niche_helps" — Performance may veto on mobile
    video_wanted = bool(luxury_mode) and allow_video not in (False, "false", 0)
    return {
        "engine": ENGINE_ID,
        "role": "Performance Director",
        "choice": "Speed-balanced Luxury" if luxury_mode else "Light delivery",
        "reason_ru": "Luxury и скорость балансируются автоматически.",
        "reason_en": "Luxury and speed are balanced automatically.",
        "apply": {
            "prefer_static_hero": pid == "basic" or not video_wanted,
            "lazy_images": True,
            "forbid_heavy_video_on_mobile_fail": True,
            "max_motion": "css" if pid != "basic" else "none",
        },
    }


def score_performance_html(html: str, *, luxury_mode: bool = False) -> dict[str, Any]:
    low = html.lower()
    has_video = bool(
        re.search(r"<video\b|hero-video|background-video|youtube\.com/embed", html, re.I)
    )
    img_count = len(re.findall(r"<img\b", html, re.I))
    lazy = len(re.findall(r"\bloading=['\"]lazy['\"]", html, re.I))
    has_webgl = "webgl" in low or "three.js" in low
    scripts = len(re.findall(r"<script\b", html, re.I))

    mobile = 88.0
    if has_video:
        mobile -= 27
    if has_webgl:
        mobile -= 35
    if img_count > 12:
        mobile -= 8
    if lazy < max(1, img_count // 3) and img_count > 3:
        mobile -= 6
    if scripts > 6:
        mobile -= 5
    if luxury_mode and not has_video:
        mobile += 4  # static luxury is fine
    mobile = max(0, min(100, int(round(mobile))))

    fail = mobile < MOBILE_FAIL and has_video
    action = (
        "Использовать статичный Hero + лёгкую анимацию."
        if fail
        else ("OK — баланс Luxury/скорость" if luxury_mode else "OK — лёгкая доставка")
    )
    return {
        "engine": ENGINE_ID,
        "mobile_score": mobile,
        "has_video": has_video,
        "has_webgl": has_webgl,
        "status": "FAIL" if fail else "PASS",
        "action_ru": action,
        "veto_video": fail,
    }


def performance_director_css() -> str:
    return """
/* Performance Director */
body[data-perf-hero="static"] .hero-video,
body[data-perf-hero="static"] video.hero-media {
  display: none !important;
}
img { max-width: 100%; height: auto; }
"""


def apply_performance_html(html: str, decision: dict[str, Any], score: dict[str, Any] | None = None) -> str:
    score = score or {}
    veto = bool(score.get("veto_video"))
    prefer_static = bool((decision.get("apply") or {}).get("prefer_static_hero")) or veto

    out = html
    if veto or prefer_static:
        # Strip video hero affordances
        out = re.sub(r"\bhero-video\b", "hero-still", out)
        out = re.sub(r"<video\b[^>]*>.*?</video>", "", out, flags=re.I | re.S)
        out = re.sub(
            r"<body\b([^>]*)>",
            lambda m: (
                m.group(0)
                if "data-perf-hero=" in m.group(0)
                else m.group(0)[:-1] + ' data-perf-hero="static">'
            ),
            out,
            count=1,
            flags=re.I,
        )

    # Ensure lazy on content images missing loading attr
    def _lazy_img(m: re.Match[str]) -> str:
        tag = m.group(0)
        if "loading=" in tag.lower():
            return tag
        # Self-closing <img ... /> → insert before />
        if tag.rstrip().endswith("/>"):
            return tag.rstrip()[:-2].rstrip() + ' loading="lazy" />'
        if tag.endswith(">"):
            return tag[:-1] + ' loading="lazy">'
        return tag

    out = re.sub(r"<img\b[^>]*>", _lazy_img, out, flags=re.I)
    return out
