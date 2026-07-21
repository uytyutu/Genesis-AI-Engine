"""R3 — Compliance Engine: single checkpoint before client ZIP.

Wraps Factory Quality Gate. Does not add new site features.
Public surface for Factory / ZIP Builder — bricks stay under Quality Gate.

Domains (CEO map):
  Design · Brand · Performance · SEO · Accessibility · Authenticity · Market Rules

Authenticity ← media honesty + no platform chrome / fabricated trust signals
Market Rules ← localization / market chrome
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.factory.quality_gate import (
    GateCheck,
    QualityGateResult,
    assert_quality_gate,
    run_quality_gate,
)

ENGINE_ID = "compliance_v1"

_CATEGORY_MAP: dict[str, str] = {
    "design": "design",
    "brand": "brand",
    "performance": "performance",
    "seo": "seo",
    "accessibility": "accessibility",
    "media": "authenticity",
    "localization": "market_rules",
}

COMPLIANCE_DOMAINS = (
    "design",
    "brand",
    "performance",
    "seo",
    "accessibility",
    "authenticity",
    "market_rules",
)


@dataclass(frozen=True)
class ComplianceCheck:
    id: str
    domain: str
    ok: bool
    detail: str = ""


@dataclass
class ComplianceResult:
    passed: bool
    engine_id: str = ENGINE_ID
    checks: list[ComplianceCheck] = field(default_factory=list)
    quality_gate: QualityGateResult | None = None

    @property
    def failures(self) -> list[str]:
        return [f"{c.domain}:{c.id} — {c.detail}" for c in self.checks if not c.ok]

    def domain_summary(self) -> dict[str, bool]:
        summary = {d: True for d in COMPLIANCE_DOMAINS}
        for c in self.checks:
            if c.domain in summary and not c.ok:
                summary[c.domain] = False
        return summary

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "passed": self.passed,
            "domains": self.domain_summary(),
            "failures": self.failures,
            "checks": [
                {
                    "id": c.id,
                    "domain": c.domain,
                    "ok": c.ok,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
            "quality_gate": self.quality_gate.as_dict() if self.quality_gate else None,
        }


class ComplianceError(ValueError):
    """Raised when ZIP is blocked by Compliance Engine."""

    def __init__(self, result: ComplianceResult):
        self.result = result
        msg = "compliance_failed: " + "; ".join(result.failures[:8])
        super().__init__(msg)


def _map_check(gate_check: GateCheck) -> ComplianceCheck:
    domain = _CATEGORY_MAP.get(gate_check.category, gate_check.category)
    return ComplianceCheck(
        id=gate_check.id,
        domain=domain,
        ok=gate_check.ok,
        detail=gate_check.detail,
    )


def run_compliance(
    html: str,
    *,
    meta: dict | None = None,
    assets_dir: Path | None = None,
) -> ComplianceResult:
    """Evaluate deliverable against all Compliance domains."""
    gate = run_quality_gate(html, meta=meta, assets_dir=assets_dir)
    checks = [_map_check(c) for c in gate.checks]
    return ComplianceResult(
        passed=gate.passed,
        checks=checks,
        quality_gate=gate,
    )


def assert_compliance(
    html: str,
    *,
    meta: dict | None = None,
    assets_dir: Path | None = None,
) -> ComplianceResult:
    """Block ZIP when any mandatory Compliance domain fails."""
    result = run_compliance(html, meta=meta, assets_dir=assets_dir)
    if not result.passed:
        raise ComplianceError(result)
    return result


def assert_release_ready(
    html: str,
    *,
    meta: dict | None = None,
    assets_dir: Path | None = None,
) -> ComplianceResult:
    """ZIP Builder entry — Compliance first; QualityGateError for legacy catch."""
    result = run_compliance(html, meta=meta, assets_dir=assets_dir)
    if result.passed:
        return result
    try:
        assert_quality_gate(html, meta=meta, assets_dir=assets_dir)
    except Exception:
        pass
    raise ComplianceError(result)
