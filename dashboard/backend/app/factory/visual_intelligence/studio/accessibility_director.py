"""Accessibility Director — contrast, type size, keyboard, alt, readability."""

from __future__ import annotations

import re
from typing import Any

ENGINE_ID = "accessibility_director_v1"


def decide_accessibility(*, package_id: str) -> dict[str, Any]:
    return {
        "engine": ENGINE_ID,
        "role": "Accessibility Director",
        "choice": "Inclusive baseline",
        "reason_ru": "Контраст, размер текста, клавиатура, alt и читаемость — часть качества продукта.",
        "reason_en": "Contrast, type size, keyboard, alt and readability are product quality.",
        "apply": {
            "min_body_px": 16,
            "focus_visible": True,
            "require_alt": True,
            "skip_link": True,
        },
    }


def score_accessibility_html(html: str) -> dict[str, Any]:
    imgs = re.findall(r"<img\b([^>]*)>", html, re.I)
    missing_alt = 0
    for attrs in imgs:
        if not re.search(r"\balt=", attrs, re.I):
            missing_alt += 1
        elif re.search(r'\balt=["\']\s*["\']', attrs, re.I):
            missing_alt += 1
    has_skip = "skip-link" in html.lower() or 'href="#main"' in html.lower()
    has_lang = bool(re.search(r"<html\b[^>]*\blang=", html, re.I))
    buttons = len(re.findall(r"<button\b|<a\b[^>]*\bhref=", html, re.I))

    score = 78
    if missing_alt == 0 and imgs:
        score += 10
    elif missing_alt:
        score -= min(20, missing_alt * 4)
    if has_lang:
        score += 4
    if has_skip:
        score += 4
    if buttons:
        score += 2
    score = max(0, min(100, score))
    return {
        "engine": ENGINE_ID,
        "overall": score,
        "missing_alt": missing_alt,
        "has_skip_link": has_skip,
        "has_lang": has_lang,
        "status": "PASS" if score >= 85 else "FAIL",
    }


def accessibility_director_css() -> str:
    return """
/* Accessibility Director */
:root { --a11y-min-size: 1rem; }
body { font-size: max(16px, var(--a11y-min-size)); }
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
  outline: 3px solid #2563eb;
  outline-offset: 2px;
}
.skip-link {
  position: absolute;
  left: -999px;
  top: 0;
  background: #0f172a;
  color: #fff;
  padding: 0.5rem 0.75rem;
  z-index: 10000;
}
.skip-link:focus { left: 0.5rem; top: 0.5rem; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
"""


def apply_accessibility_html(html: str, decision: dict[str, Any] | None = None) -> str:
    apply = (decision or {}).get("apply") or {}
    out = html

    def _alt_img(m: re.Match[str]) -> str:
        tag = m.group(0)
        if re.search(r"\balt=", tag, re.I):
            return tag
        return tag[:-1] + ' alt="">'

    if apply.get("require_alt", True):
        out = re.sub(r"<img\b[^>]*>", _alt_img, out, flags=re.I)

    if apply.get("skip_link", True) and "skip-link" not in out.lower():
        skip = '<a class="skip-link" href="#top">Skip to content</a>\n'
        out = re.sub(r"<body\b[^>]*>", lambda m: m.group(0) + "\n" + skip, out, count=1, flags=re.I)

    out = re.sub(
        r"<body\b[^>]*>",
        lambda m: (
            m.group(0)
            if "data-a11y=" in m.group(0)
            else m.group(0)[:-1] + ' data-a11y="1">'
        ),
        out,
        count=1,
        flags=re.I,
    )
    return out
