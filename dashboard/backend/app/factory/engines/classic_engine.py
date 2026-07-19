"""Classic Factory engine — wraps existing landing_builder (Path A)."""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.engines.base import EngineError, EngineRequest, EngineResult
from app.factory.landing_builder import build_landing_html
from app.factory.motion_brief import gate_motion_level, normalize_motion_level
from app.factory.package_features import (
    apply_order_contacts,
    resolve_package_features,
)


ENGINE_ID = "classic"


def generate(request: EngineRequest) -> EngineResult:
    gate = gate_motion_level(request.motion_level)
    if not gate["ok"]:
        raise EngineError(
            gate["code"],
            "3d_premium requires waitlist / paid contour — Classic CSS-motion only for free Path A.",
        )
    motion = normalize_motion_level(gate["motion_level"])
    analysis = analyze(request.description)
    analysis = apply_order_contacts(
        analysis,
        business_name=request.business_name or None,
        phone=request.phone or None,
        email=request.email or None,
    )
    features = resolve_package_features(request.package_id)
    html = build_landing_html(
        analysis,
        features=features,
        whatsapp=request.whatsapp or request.phone,
        city=request.city,
        street="",
        motion_level=motion,
        market_code=request.market_code,
    )
    return EngineResult(
        engine_id=ENGINE_ID,
        html=html,
        meta={
            "business_name": analysis.business_name,
            "niche": analysis.niche,
            "template_id": analysis.template_id,
            "package_id": request.package_id,
            "market_code": request.market_code,
            "motion_level": motion,
            "motion_assets": (
                ["assets/motion_kit.css", "assets/reveal.js"] if motion == "css" else []
            ),
        },
    )
