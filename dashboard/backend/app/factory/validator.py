"""Validation — technical checks + Compliance Engine (Quality Gate inside)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.factory.compliance_engine import run_compliance


@dataclass
class ValidationResult:
    quality_percent: int
    passed: bool
    technical_checks: list[dict[str, str | bool]]
    responsive_ok: bool
    html_ok: bool
    accessibility_ok: bool
    quality_gate: dict | None = None
    compliance: dict | None = None


def validate_landing(
    html: str,
    *,
    meta: dict | None = None,
    assets_dir: Path | None = None,
) -> ValidationResult:
    lower = html.lower()
    html_ok = "</html>" in lower and "<body" in lower
    responsive_ok = "@media" in html and "max-width" in html
    accessibility_ok = bool(
        re.search(r'lang="(?:ru|uk|en|de|fr|es|nl|cs)"', lower)
    ) and 'name="description"' in lower and "<h1" in lower

    compliance = run_compliance(html, meta=meta, assets_dir=assets_dir)
    gate_dict = (
        compliance.quality_gate.as_dict() if compliance.quality_gate else None
    )
    compliance_dict = compliance.as_dict()

    technical: list[dict[str, str | bool]] = [
        {"id": "html", "label": "HTML", "ok": html_ok and lower.strip().startswith("<!doctype html>")},
        {"id": "mobile", "label": "Mobile", "ok": responsive_ok and 'name="viewport"' in lower},
        {"id": "accessibility", "label": "Accessibility", "ok": accessibility_ok},
        {"id": "compliance", "label": "Compliance Engine", "ok": compliance.passed},
        {"id": "quality_gate", "label": "Quality Gate", "ok": compliance.passed},
    ]
    for failure in compliance.failures[:6]:
        technical.append(
            {
                "id": f"compliance:{failure.split(' — ')[0]}",
                "label": failure[:80],
                "ok": False,
            }
        )

    score = sum(12 for c in technical[:3] if c["ok"])
    score += 12 if compliance.passed else 0
    score += 10 if bool(re.search(r"<h1[^>]*>.+?</h1>", html, re.I | re.S)) else 0
    score += 10 if lower.count("<section") >= 2 else 0
    score += 8 if ("svc-card" in html or "service-card" in html or "svc-row" in html) else 0
    score += 8 if 'class="btn"' in html or " class=\"btn" in html else 0
    score += 6 if "<footer" in lower else 0
    quality = min(98, max(72, score + 40))
    # First four core checks + gate (index 3 is compliance; 4 is legacy alias)
    passed = (
        all(c["ok"] for c in technical[:4])
        and html_ok
        and compliance.passed
    )

    return ValidationResult(
        quality_percent=quality,
        passed=passed,
        technical_checks=technical,
        responsive_ok=responsive_ok,
        html_ok=html_ok,
        accessibility_ok=accessibility_ok,
        quality_gate=gate_dict,
        compliance=compliance_dict,
    )


def owner_review_check(approved: bool) -> dict[str, str | bool]:
    return {
        "id": "owner_review",
        "label": "Owner Review",
        "ok": approved,
        "pending": not approved,
    }
