"""Commercial Quality Gate — Hard Gate then AI Score (architecture lock).

Hard Gate FAIL → no ZIP, regardless of AI Score (Commercial Rule №1).
AI Score is a quality instrument after Hard Gate PASS.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from app.factory.analyzer import AnalysisResult
from app.factory.composers.context import QuestionnaireContext
from app.factory.content_gate import _GENERIC_HERO_BANNED, _is_generic_service_title, evaluate_analysis

ENGINE_ID = "commercial_gate_v1"
AI_SCORE_THRESHOLD = 95.0
MAX_REBUILD_ATTEMPTS = 2

_STUB_PATTERNS = (
    r"lorem\s+ipsum",
    r"coming\s+soon",
    r"sample\s+text",
    r"placeholder",
    r"your\s+company",
    r"demo\s+content",
    r"todo:",
    r"FIXME",
)

_WEAK_CTA = frozenset(
    {
        "mehr erfahren",
        "learn more",
        "click here",
        "hier klicken",
        "contact us",
        "kontakt aufnehmen",
    }
)


@dataclass(frozen=True)
class HardCheck:
    id: str
    ok: bool
    detail: str = ""


@dataclass
class AiScore:
    niche_match: float = 0.0
    content_quality: float = 0.0
    cta_quality: float = 0.0
    structure_quality: float = 0.0
    design_quality: float = 0.0
    commercial_readiness: float = 0.0

    @property
    def overall(self) -> float:
        parts = (
            self.niche_match,
            self.content_quality,
            self.cta_quality,
            self.structure_quality,
            self.design_quality,
            self.commercial_readiness,
        )
        return round(sum(parts) / len(parts), 1)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["overall"] = self.overall
        return d


@dataclass
class CommercialGateResult:
    hard_passed: bool
    score_passed: bool
    hard_checks: list[HardCheck] = field(default_factory=list)
    ai_score: AiScore = field(default_factory=AiScore)
    brand_leak: str = "PASS"
    threshold: float = AI_SCORE_THRESHOLD
    failures: list[str] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.hard_passed and self.score_passed

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": ENGINE_ID,
            "hard_passed": self.hard_passed,
            "score_passed": self.score_passed,
            "passed": self.passed,
            "brand_leak": self.brand_leak,
            "threshold": self.threshold,
            "ai_score": self.ai_score.as_dict(),
            "hard_checks": [asdict(c) for c in self.hard_checks],
            "failures": list(self.failures),
            "commercial_rule_1": "first_visitor_ready",
            **(self.extras or {}),
        }


def _blob(analysis: AnalysisResult) -> str:
    parts = [
        analysis.headline,
        analysis.subtitle,
        analysis.about_text,
        analysis.cta_label,
        " ".join(analysis.services or []),
        " ".join(analysis.benefits or ()),
        " ".join(analysis.trust_points or ()),
    ]
    return " ".join(p for p in parts if p)


def run_hard_gate(
    *,
    analysis: AnalysisResult,
    ctx: QuestionnaireContext,
    html: str | None = None,
    scenario_id: str | None = None,
) -> list[HardCheck]:
    checks: list[HardCheck] = []
    niche = (analysis.niche or ctx.niche or "generic").lower()
    headline = analysis.headline or ""
    cta = (analysis.cta_label or "").strip()
    services = list(analysis.services or [])

    # Brand leak (text-level; HTML brand leak stays in quality_gate.py)
    brand_hit = bool(
        re.search(r"virtus\s*core|genesis\.exe|mission\s*control", _blob(analysis), re.I)
    )
    checks.append(
        HardCheck("brand_leak", not brand_hit, "virtus_brand_in_copy" if brand_hit else "ok")
    )

    stub_hit = any(re.search(p, _blob(analysis), re.I) for p in _STUB_PATTERNS)
    if html:
        stub_hit = stub_hit or any(re.search(p, html, re.I) for p in _STUB_PATTERNS)
    checks.append(HardCheck("no_stubs", not stub_hit, "stub_copy" if stub_hit else "ok"))

    banned = next((b for b in _GENERIC_HERO_BANNED if b in headline.lower()), None)
    checks.append(
        HardCheck(
            "no_generic_phrases",
            banned is None,
            f"banned:{banned}" if banned else "ok",
        )
    )

    hero_ok = bool(headline.strip()) and (
        niche == "generic"
        or niche.replace("_", " ") in headline.lower()
        or any(s.lower() in headline.lower() for s in services[:2])
        or " — " in headline
    )
    # Niche voice: content_gate hero check
    cg = evaluate_analysis(analysis)
    hero_voice = next((c for c in cg.checks if c.id == "hero_niche_voice"), None)
    if hero_voice and not hero_voice.ok:
        hero_ok = False
    checks.append(
        HardCheck("hero_matches_niche", hero_ok, hero_voice.detail if hero_voice else "ok")
    )

    if ctx.services and len(ctx.services) >= 2:
        qset = {s.lower() for s in ctx.services}
        overlap = sum(1 for s in services if s.lower() in qset)
        svc_ok = overlap >= min(2, len(ctx.services))
    else:
        svc_ok = not (
            niche != "generic"
            and services
            and sum(1 for s in services if _is_generic_service_title(s)) >= 2
        )
    checks.append(
        HardCheck(
            "services_match_questionnaire",
            svc_ok,
            "mismatch" if not svc_ok else "ok",
        )
    )

    cta_ok = bool(cta) and cta.lower() not in _WEAK_CTA
    checks.append(HardCheck("cta_actionable", cta_ok, cta or "missing"))

    checks.append(
        HardCheck(
            "contacts_present",
            ctx.has_contact()
            or bool((analysis.phone or "").strip())
            or bool((analysis.email or "").strip()),
            "missing_contacts" if not ctx.has_contact() else "ok",
        )
    )

    scenario = (scenario_id or niche or "generic").lower()
    structure_ok = (analysis.niche or "").lower() == scenario or scenario == "generic"
    checks.append(
        HardCheck("structure_matches_scenario", structure_ok, f"{analysis.niche}≠{scenario}" if not structure_ok else "ok")
    )

    empty_bits = not headline.strip() or not (analysis.subtitle or "").strip() or not services
    checks.append(HardCheck("no_empty_core_sections", not empty_bits, "empty_core" if empty_bits else "ok"))

    if html is not None:
        # Linked legal / contact anchors — soft hard-check when HTML available
        linked = ("#contact" in html or "mailto:" in html or "tel:" in html)
        checks.append(HardCheck("pages_linked", linked, "ok" if linked else "no_contact_path"))

    return checks


def compute_ai_score(
    *,
    analysis: AnalysisResult,
    ctx: QuestionnaireContext,
    hard_checks: list[HardCheck],
) -> AiScore:
    niche = (analysis.niche or "generic").lower()
    services = list(analysis.services or [])

    niche_match = 70.0
    if niche != "generic":
        niche_match = 90.0
    if any(s.lower() in (analysis.headline or "").lower() for s in services[:2]):
        niche_match = min(100.0, niche_match + 8)
    if ctx.city and ctx.city.lower() in (analysis.subtitle or "").lower():
        niche_match = min(100.0, niche_match + 4)

    content = 80.0
    if len((analysis.about_text or "")) >= 40:
        content += 8
    if len(services) >= 3:
        content += 6
    if ctx.advantages:
        content += 4
    content = min(100.0, content)

    cta_q = 70.0 if (analysis.cta_label or "").lower() in _WEAK_CTA else 92.0
    if analysis.cta_label:
        cta_q = min(100.0, cta_q + 4)

    structure = 94.0 if niche != "generic" else 80.0
    if hard_checks and all(c.ok for c in hard_checks if c.id == "structure_matches_scenario"):
        structure = min(100.0, structure + 4)

    design = 92.0 if niche != "generic" else 78.0
    commercial = 95.0 if all(c.ok for c in hard_checks) else 60.0
    if ctx.has_contact():
        commercial = min(100.0, commercial + 3)

    return AiScore(
        niche_match=round(niche_match, 1),
        content_quality=round(content, 1),
        cta_quality=round(cta_q, 1),
        structure_quality=round(structure, 1),
        design_quality=round(design, 1),
        commercial_readiness=round(commercial, 1),
    )


def run_commercial_gate(
    *,
    analysis: AnalysisResult,
    ctx: QuestionnaireContext,
    html: str | None = None,
    scenario_id: str | None = None,
    threshold: float = AI_SCORE_THRESHOLD,
) -> CommercialGateResult:
    hard_checks = run_hard_gate(
        analysis=analysis, ctx=ctx, html=html, scenario_id=scenario_id
    )
    hard_passed = all(c.ok for c in hard_checks)
    brand = next((c for c in hard_checks if c.id == "brand_leak"), None)
    brand_leak = "FAIL" if brand and not brand.ok else "PASS"

    score = compute_ai_score(analysis=analysis, ctx=ctx, hard_checks=hard_checks)
    # Score only counts after Hard Gate (instrument, not sole criterion).
    score_passed = hard_passed and score.overall >= threshold

    failures = [f"{c.id}:{c.detail}" for c in hard_checks if not c.ok]
    if hard_passed and not score_passed:
        failures.append(f"ai_score_below_threshold:{score.overall}<{threshold}")

    # Commercial Rule №1: template feel → FAIL even if score high
    if hard_passed and any(
        c.id == "no_generic_phrases" and not c.ok for c in hard_checks
    ):
        score_passed = False

    return CommercialGateResult(
        hard_passed=hard_passed,
        score_passed=score_passed,
        hard_checks=hard_checks,
        ai_score=score,
        brand_leak=brand_leak,
        threshold=threshold,
        failures=failures,
    )
