"""Premium Site QA — owner verdict for Design Spec builds.

Outcomes (honest):
  REJECT — cannot show to client
  IMPROVE — visible issues, rebuild or edit
  READY_FOR_REVIEW — passes automated premium bar; owner eye still required
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_FAKE_TRUST = re.compile(
    r"500\s*\+|98\s*%|100\s*%\s*zufriedenheit|zufriedenheit\s*98",
    re.IGNORECASE,
)


def run_premium_site_qa(
    *,
    html: str,
    meta: dict[str, Any] | None = None,
    niche_id: str = "",
    design_spec: dict[str, Any] | None = None,
    assets_dir: Path | None = None,
) -> dict[str, Any]:
    meta = meta if isinstance(meta, dict) else {}
    spec = design_spec if isinstance(design_spec, dict) else meta.get("website_design_spec")
    if not isinstance(spec, dict):
        spec = {}

    niche = str(niche_id or meta.get("niche") or spec.get("niche_id") or "").strip().lower()
    family = str(spec.get("industry_family") or "").strip().lower()
    hard: list[str] = []
    improve: list[str] = []

    if not html or len(html) < 400:
        hard.append("html:empty_or_too_short")
    if not spec.get("schema"):
        hard.append("design_spec:missing")
    if not spec.get("version_id"):
        improve.append("design_spec:no_version_id")

    # Spec-as-Contract: Premium QA is independent of LLM opinion.
    # Invalid Spec is always REJECT — Engine must not "fix somehow".
    if spec:
        from app.factory.website_design_spec import validate_website_design_spec

        _gate = validate_website_design_spec(spec)
        if not _gate["ok"]:
            for err in _gate["errors"][:16]:
                hard.append(f"design_spec:{err}")
        elif not spec.get("version_id"):
            improve.append("design_spec:no_version_id")

    visible = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    visible = re.sub(r"<style[^>]*>.*?</style>", " ", visible, flags=re.S | re.I)
    if _FAKE_TRUST.search(visible):
        hard.append("trust:fake_stats_in_html")

    if "viewport" not in html.lower():
        improve.append("mobile:viewport_meta_missing")

    from app.factory.quality_gate import run_quality_gate

    qg = run_quality_gate(html, meta=meta, assets_dir=assets_dir)
    if not qg.passed:
        for f in qg.failures[:12]:
            hard.append(f"quality:{f}")

    from app.factory.product_intelligence import run_website_product_intelligence

    pi = run_website_product_intelligence(
        html=html,
        niche_id=niche or "generic",
        city=str((spec.get("business") or {}).get("city") or meta.get("city") or ""),
    )
    contamination = pi.get("cross_contamination") or {}
    if contamination.get("status") == "FAIL":
        hard.append(f"niche:contamination:{contamination.get('detail') or 'fail'}")
    geo = pi.get("geo_consistency") or {}
    if geo.get("status") == "FAIL":
        improve.append("geo:inconsistent_cities")

    if family == "automotive" or niche in ("auto", "autohaus", "car_dealership"):
        markers = ("werkstatt", "inspektion", "service", "fahrzeug", "reifen", "öl")
        low = visible.lower()
        if not any(m in low for m in markers):
            improve.append("automotive:weak_service_vocabulary")
        if "data-dna-" not in html:
            improve.append("automotive:design_dna_attrs_missing")

    if family == "hospitality" or niche in ("restaurant", "food", "cafe", "café"):
        markers = (
            "speisekarte",
            "menü",
            "menu",
            "küche",
            "reserv",
            "gericht",
            "gast",
            "wein",
        )
        auto_leak = ("werkstatt", "inspektion", "bremsen", "fahrzeug", "ölwechsel")
        low = visible.lower()
        if not any(m in low for m in markers):
            improve.append("hospitality:weak_menu_vocabulary")
        if any(m in low for m in auto_leak):
            hard.append("hospitality:automotive_contamination")
        if "data-renderer=\"restaurant\"" not in html and "data-renderer='restaurant'" not in html:
            improve.append("hospitality:restaurant_renderer_missing")
        if spec.get("renderer_strategy") != "restaurant":
            improve.append("hospitality:renderer_strategy_mismatch")

    if hard:
        verdict = "REJECT"
    elif improve:
        verdict = "IMPROVE"
    else:
        verdict = "READY_FOR_REVIEW"

    return {
        "verdict": verdict,
        "hard_failures": hard,
        "improvements": improve,
        "quality_gate_passed": qg.passed,
        "product_intelligence": {
            "niche_id": niche,
            "family": family,
            "geo": geo.get("status"),
            "contamination": contamination.get("status"),
        },
        "design_spec_version": spec.get("version_id"),
        "owner_approve_allowed": verdict == "READY_FOR_REVIEW",
    }
