"""Commercial Readiness Score — master KPI above Overall / Feeling / Motion.

Commercial Ready only when CRS ≥ threshold.
"""

from __future__ import annotations

from typing import Any

from app.factory.visual_intelligence.ai_design_director import score_html
from app.factory.visual_intelligence.studio.accessibility_director import (
    score_accessibility_html,
)
from app.factory.visual_intelligence.studio.conversion_director import (
    score_conversion_html,
)
from app.factory.visual_intelligence.studio.performance_director import (
    score_performance_html,
)

ENGINE_ID = "commercial_readiness_v1"
COMMERCIAL_READY_THRESHOLD = 90
PRODUCT_LABEL = "Commercial Ready"


def _clip(n: float) -> int:
    return max(0, min(100, int(round(n))))


def score_commercial_readiness(
    html: str,
    *,
    package_id: str = "business",
    niche: str | None = None,
    market_code: str = "DE",
    luxury_mode: bool | None = None,
) -> dict[str, Any]:
    """Master score: Visual · Trust · Conversion · Performance · Mobile · Accessibility."""
    pid = (package_id or "business").strip().lower()
    design = score_html(
        html,
        package_id=pid,
        niche=niche,
        luxury_mode=luxury_mode,
    )
    scores_d = design.get("scores") or {}
    conv = score_conversion_html(html)
    conv_s = conv.get("scores") or {}
    perf = score_performance_html(html, luxury_mode=bool(luxury_mode or pid == "premium"))
    a11y = score_accessibility_html(html)

    visual = int(scores_d.get("visual") or design.get("overall") or 0)
    trust = int(scores_d.get("trust") or conv_s.get("trust") or 0)
    conversion = int(conv.get("overall") or 0)
    performance = int(perf.get("mobile_score") or 0)
    # Performance dimension: invert penalty — high mobile = high performance
    performance = _clip(performance)
    mobile = int(scores_d.get("mobile_experience") or performance)
    accessibility = int(a11y.get("overall") or 0)

    # Soft boost when market legal markers present (DE)
    market = (market_code or "DE").upper()
    low = html.lower()
    if market in ("DE", "AT", "CH") and (
        "impressum" in low or "datenschutz" in low or 'data-locale-legal="impressum' in low
    ):
        trust = _clip(trust + 2)

    overall = _clip(
        visual * 0.18
        + trust * 0.20
        + conversion * 0.22
        + performance * 0.15
        + mobile * 0.15
        + accessibility * 0.10
    )
    ready = overall >= COMMERCIAL_READY_THRESHOLD and perf.get("status") != "FAIL"

    return {
        "engine": ENGINE_ID,
        "threshold": COMMERCIAL_READY_THRESHOLD,
        "scores": {
            "visual": visual,
            "trust": trust,
            "conversion": conversion,
            "performance": performance,
            "mobile": mobile,
            "accessibility": accessibility,
        },
        "overall_commercial": overall,
        "commercial_ready": ready,
        "label": PRODUCT_LABEL if ready else "Not Commercial Ready",
        "status": "PASS" if ready else "FAIL",
        "conversion_detail": conv,
        "performance_detail": perf,
        "accessibility_detail": a11y,
        "design_director_overall": design.get("overall"),
        "ssot_ru": (
            "Главный KPI — Commercial Readiness Score. "
            f"Только при ≥ {COMMERCIAL_READY_THRESHOLD} Factory ставит Commercial Ready."
        ),
    }
