"""Quality gate — technical checks for owner UI (not a substitute for human approval)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ValidationResult:
    quality_percent: int
    passed: bool
    technical_checks: list[dict[str, str | bool]]
    responsive_ok: bool
    html_ok: bool
    accessibility_ok: bool


def validate_landing(html: str) -> ValidationResult:
    lower = html.lower()
    html_ok = "</html>" in lower and "<body" in lower
    responsive_ok = "@media" in html and "max-width" in html
    accessibility_ok = bool(re.search(r'lang="(?:ru|de)"', lower)) and 'name="description"' in lower and "<h1" in lower

    technical = [
        {"id": "html", "label": "HTML", "ok": html_ok and lower.strip().startswith("<!doctype html")},
        {"id": "mobile", "label": "Mobile", "ok": responsive_ok and 'name="viewport"' in lower},
        {
            "id": "accessibility",
            "label": "Accessibility",
            "ok": accessibility_ok,
        },
    ]

    score = sum(12 for c in technical if c["ok"])
    score += 10 if bool(re.search(r"<h1[^>]*>.+?</h1>", html, re.I | re.S)) else 0
    score += 10 if lower.count("<section") >= 2 else 0
    score += 8 if "service-card" in html else 0
    score += 8 if 'class="btn"' in html else 0
    score += 6 if "<footer" in lower else 0
    quality = min(98, max(72, score + 46))
    passed = all(c["ok"] for c in technical) and html_ok

    return ValidationResult(
        quality_percent=quality,
        passed=passed,
        technical_checks=technical,
        responsive_ok=responsive_ok,
        html_ok=html_ok,
        accessibility_ok=accessibility_ok,
    )


def owner_review_check(approved: bool) -> dict[str, str | bool]:
    return {
        "id": "owner_review",
        "label": "Owner Review",
        "ok": approved,
        "pending": not approved,
    }
