"""Quality gate — technical checks + Factory Quality Gate for client ZIP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.factory.quality_gate import QualityGateResult, run_quality_gate


@dataclass
class ValidationResult:
    quality_percent: int
    passed: bool
    technical_checks: list[dict[str, str | bool]]
    responsive_ok: bool
    html_ok: bool
    accessibility_ok: bool
    quality_gate: dict | None = None


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

    gate = run_quality_gate(html, meta=meta, assets_dir=assets_dir)
    gate_dict = gate.as_dict()

    technical: list[dict[str, str | bool]] = [
        {"id": "html", "label": "HTML", "ok": html_ok and lower.strip().startswith("<!doctype html>")},
        {"id": "mobile", "label": "Mobile", "ok": responsive_ok and 'name="viewport"' in lower},
        {"id": "accessibility", "label": "Accessibility", "ok": accessibility_ok},
        {"id": "quality_gate", "label": "Quality Gate", "ok": gate.passed},
    ]
    for failure in gate.failures[:6]:
        technical.append(
            {
                "id": f"gate:{failure.split(' — ')[0]}",
                "label": failure[:80],
                "ok": False,
            }
        )

    score = sum(12 for c in technical[:3] if c["ok"])
    score += 12 if gate.passed else 0
    score += 10 if bool(re.search(r"<h1[^>]*>.+?</h1>", html, re.I | re.S)) else 0
    score += 10 if lower.count("<section") >= 2 else 0
    score += 8 if ("svc-card" in html or "service-card" in html) else 0
    score += 8 if 'class="btn"' in html or " class=\"btn" in html else 0
    score += 6 if "<footer" in lower else 0
    quality = min(98, max(72, score + 40))
    passed = all(c["ok"] for c in technical[:4]) and html_ok and gate.passed

    return ValidationResult(
        quality_percent=quality,
        passed=passed,
        technical_checks=technical,
        responsive_ok=responsive_ok,
        html_ok=html_ok,
        accessibility_ok=accessibility_ok,
        quality_gate=gate_dict,
    )


def owner_review_check(approved: bool) -> dict[str, str | bool]:
    return {
        "id": "owner_review",
        "label": "Owner Review",
        "ok": approved,
        "pending": not approved,
    }
