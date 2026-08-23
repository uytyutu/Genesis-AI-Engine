"""Dry-run pipeline: form → scene → cost estimate → budget gate. No live jobs."""

from __future__ import annotations

from typing import Any

from app.integration.cinematic_media.budget import can_start_media_job, order_is_payment_confirmed
from app.integration.cinematic_media.cost_estimate import estimate_scene_cost
from app.integration.cinematic_media.router import MediaProviderRouter
from app.integration.cinematic_media.scene_director import build_scene_spec


def _creative_brief_from_form(form: dict[str, Any]) -> dict[str, Any]:
    """Lightweight Creative Director stub — decides experience mode from form."""
    niche = str(form.get("niche") or "").strip()
    style = str(form.get("style") or form.get("brand_style") or "premium").strip()
    product_kind = str(form.get("product_kind") or "website").strip().lower()
    cinematic = bool(form.get("cinematic_enabled") or form.get("cinematic_ai_experience"))
    return {
        "engine": "creative_director_dry_run_v0",
        "role": "AI Creative Director",
        "niche": niche,
        "style": style,
        "product_kind": product_kind,
        "cinematic_requested": cinematic,
        "hero_media": "cinematic_scroll_video" if cinematic else "photo",
        "motion_profile": "scroll_driven_film" if cinematic else "subtle_css",
        "note": "Dry-run brief only — does not call image/video APIs",
    }


def dry_run_scene_budget(
    form: dict[str, Any],
    *,
    order: dict[str, Any] | None = None,
    provider_id: str | None = None,
) -> dict[str, Any]:
    """
    Client form → Creative Director → Scene Director → cost estimate → ALLOW/BLOCK.
    Never submits a provider job. Never spends credits.
    """
    brief = _creative_brief_from_form(form)
    scene = build_scene_spec(
        niche=str(form.get("niche") or ""),
        business_name=str(form.get("business_name") or form.get("company_name") or ""),
        style=str(form.get("style") or form.get("brand_style") or "cinematic_realistic"),
        product_kind=str(form.get("product_kind") or "website"),
        city=str(form.get("city") or ""),
        description=str(form.get("description") or form.get("extra_wishes") or ""),
    )
    estimate = estimate_scene_cost(scene, provider_id=provider_id)
    providers = MediaProviderRouter().board()

    decision = "BLOCK"
    reason = "estimate_failed"
    gate: dict[str, Any] = {}

    if not estimate.get("ok") or estimate.get("estimated_cost_eur") is None:
        decision = "MANUAL_REVIEW"
        reason = str(estimate.get("error") or "unknown_cost")
        gate = {
            "allow": False,
            "error": "unknown_cost",
            "media_status": "MANUAL_REVIEW",
            "detail": "Unknown/missing estimate must never be treated as 0 €",
        }
    else:
        cost = float(estimate["estimated_cost_eur"])
        # If order provided — enforce real payment + remaining budget.
        # If form-only preview — compare against configured media_budget when cinematic.
        if order is not None:
            gate = can_start_media_job(order, estimated_cost_eur=cost)
            if gate.get("allow"):
                decision = "ALLOW"
                reason = "within_media_budget"
            else:
                decision = "BLOCK" if gate.get("error") != "unknown_cost" else "MANUAL_REVIEW"
                reason = str(gate.get("error") or "blocked")
                if gate.get("error") == "budget_exceeded":
                    decision = "MANUAL_REVIEW"
        else:
            # Preview without order: use stated internal budget from form/config default 40
            budget = form.get("media_budget_eur")
            if budget is None and brief.get("cinematic_requested"):
                from app.integration.cinematic_media.config import get_product

                product = get_product(
                    "cinematic_shop_experience"
                    if str(form.get("product_kind") or "") == "shop"
                    else "cinematic_ai_experience"
                )
                budget = float((product or {}).get("media_budget_eur") or 0)
            budget_f = float(budget or 0)
            if not brief.get("cinematic_requested"):
                decision = "BLOCK"
                reason = "cinematic_not_requested"
                gate = {"allow": False, "error": "cinematic_not_enabled"}
            elif budget_f <= 0:
                decision = "MANUAL_REVIEW"
                reason = "no_budget_configured"
                gate = {"allow": False, "error": "no_budget"}
            elif cost <= budget_f + 1e-9:
                decision = "ALLOW_IF_PAID"
                reason = "estimate_within_configured_budget"
                gate = {
                    "allow": False,
                    "preview_ok": True,
                    "error": "payment_required_before_generation",
                    "detail": "Dry-run OK vs internal budget — generation still waits for Stripe payment",
                    "budget_eur": budget_f,
                    "estimated_cost_eur": cost,
                }
            else:
                decision = "MANUAL_REVIEW"
                reason = "estimate_exceeds_configured_budget"
                gate = {
                    "allow": False,
                    "error": "budget_exceeded",
                    "budget_eur": budget_f,
                    "estimated_cost_eur": cost,
                }

    return {
        "ok": True,
        "dry_run": True,
        "network_called": False,
        "live_job_submitted": False,
        "creative_brief": brief,
        "scene": scene,
        "provider_preference": estimate.get("provider_id") or provider_id or "kie",
        "cost_estimate": estimate,
        "budget_gate": gate,
        "decision": decision,
        "reason": reason,
        "payment_confirmed": order_is_payment_confirmed(order) if order else False,
        "providers": providers,
        "client_safe_summary": {
            # Never expose internal € budget to client UIs consuming this blindly
            "cinematic": bool(brief.get("cinematic_requested")),
            "scene_type": scene.get("scene_type"),
            "shots": len(scene.get("shots") or []),
            "ready_for_generation": decision in ("ALLOW",),
            "needs_payment": decision == "ALLOW_IF_PAID",
            "needs_review": decision == "MANUAL_REVIEW",
        },
    }
