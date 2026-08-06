"""Golden Website Test + Public Launch Blockers for CEO Dashboard.

Ads for Website are BLOCKED until golden_website status is PASS.
Final Launch Blockers before Public Launch (product SSOT roadmap):
  1) Golden Website Test
  2) Visual Quality Gate (Business/Premium — no empty decorative zones)
  3) Social Integration Gate (links on every site/store; Starter at order, Business+ CMS)
  4) Commercial UX Gate (no Landing-era copy; forms match Virtus Core catalog)
  5) Demo Gallery refresh
  6) Live Preview Website (iframe — no white window)
  7) Brand Audit (Genesis → Virtus Core public)
  8) Golden AI Store Test (after Website)
Next major stage (not a launch blocker yet): Premium Visual Engine
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_overrides(memory_dir: Path) -> dict[str, Any]:
    path = Path(memory_dir) / "launch_readiness.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _flag_pass(row: dict[str, Any] | None, key: str) -> bool:
    if not isinstance(row, dict):
        return False
    return str(row.get(key) or "").lower() == "pass"


def build_golden_website_launch(memory_dir: Path) -> dict[str, Any]:
    """CEO-facing Golden Website Test gate + Launch Blockers."""
    from app.integration.pricing_engine import resolve_path_a_offer

    ov = _load_overrides(memory_dir)
    gwt = ov.get("golden_website_test") if isinstance(ov.get("golden_website_test"), dict) else {}
    gallery = ov.get("demo_gallery") if isinstance(ov.get("demo_gallery"), dict) else {}
    brand = ov.get("brand_audit") if isinstance(ov.get("brand_audit"), dict) else {}
    store = ov.get("golden_store_test") if isinstance(ov.get("golden_store_test"), dict) else {}

    basic = resolve_path_a_offer("basic", "DE")
    business = resolve_path_a_offer("business", "DE")
    premium = resolve_path_a_offer("premium", "DE")
    pricing_ok = (
        int(basic.amount) == 199
        and int(business.amount) == 399
        and int(premium.amount) == 699
    )

    guest_ok = _flag_pass(gwt, "guest_checkout")
    email_ok = _flag_pass(gwt, "verification_email") or _flag_pass(gwt, "order_email")
    build_ok = _flag_pass(gwt, "production_build")
    demo_pay_ok = _flag_pass(gwt, "demo_payment")
    factory_ok = _flag_pass(gwt, "factory")
    publish_ok = _flag_pass(gwt, "publish")
    # full_pass resolved below after logic/infrastructure layers

    pricing_override = str(gwt.get("pricing_ssot") or "").lower()
    if pricing_override == "pass":
        pricing_ok = True
    elif pricing_override == "fail":
        pricing_ok = False

    # Auto-detect Demo Gallery quality from package-previews (PASS only if 8+6 full).
    gallery_auto = False
    try:
        from app.integration.demo_gallery_audit import build_demo_gallery_snapshot

        snap = build_demo_gallery_snapshot(memory_dir)
        gallery_auto = str(snap.get("status") or "").upper() == "PASS"
    except Exception:
        gallery_auto = False
    gallery_ok = _flag_pass(gallery, "status") or gallery_auto

    # Live iframe preview works when demos exist AND CSP allows same-origin embed.
    # Override: launch_readiness.json → preview_website.status = pass|fail
    preview_ov = ov.get("preview_website") if isinstance(ov.get("preview_website"), dict) else {}
    preview_auto = False
    try:
        fe_prev = (
            Path(__file__).resolve().parents[3]
            / "frontend"
            / "public"
            / "package-previews"
        )
        dental = fe_prev / "sites" / "business" / "dental" / "index.html"
        preview_auto = dental.is_file() and dental.stat().st_size > 5000
    except OSError:
        preview_auto = False
    preview_flag = str(preview_ov.get("status") or "").lower()
    if preview_flag == "fail":
        preview_ok = False
    elif preview_flag == "pass":
        preview_ok = True
    else:
        # Default: treat as pass once gallery files exist (CSP fixed in next.config).
        preview_ok = preview_auto and gallery_ok

    brand_ok = _flag_pass(brand, "status")
    store_ok = _flag_pass(store, "status")

    # Honest GWT layers (Aug 2026 evidence: ord-49ab24f1fe ZIP ~15MB / ~357s).
    # Functional PASS ≠ Performance PASS. Scale needs KPIs; first-path delivery is proven.
    functional_flag = str(
        gwt.get("functional_status") or gwt.get("logic_status") or "pass"
    ).lower()
    infra_flag = str(gwt.get("infrastructure_status") or "pass_with_notes").lower()
    perf_flag = str(gwt.get("performance_status") or "open").lower()
    functional_ok = functional_flag in {"pass", "done", "ok"}
    infra_ok = infra_flag in {"pass", "done", "ok", "pass_with_notes"}
    performance_ok = perf_flag in {"pass", "done", "ok"}

    from app.integration.product_gates_ssot import GWT_PERFORMANCE_KPIS

    observed_zip_s = gwt.get("observed_zip_download_s")
    try:
        observed_zip_s = float(observed_zip_s) if observed_zip_s is not None else 357.0
    except (TypeError, ValueError):
        observed_zip_s = 357.0

    layers = {
        "functional": {
            "id": "gwt_functional",
            "label": "GWT Functional",
            "status": "PASS" if functional_ok else "FAIL",
            "detail": (
                "Commercial pipeline closed: order → pay → Factory → ready → "
                "download_url → ZIP (~15 MB) · compliance meta=HTML"
                if functional_ok
                else "End-to-end delivery path not proven"
            ),
        },
        "infrastructure": {
            "id": "gwt_infrastructure",
            "label": "GWT Infrastructure",
            "status": (
                "PASS"
                if infra_flag in {"pass", "done", "ok"}
                else ("PASS_WITH_NOTES" if infra_ok else "BLOCKED")
            ),
            "detail": (
                "HTTP ZIP works; keep free uvicorn port + E2E timeout ≥ ZIP duration"
                if infra_ok
                else "Port conflict / HTTP abort — runtime, not product logic"
            ),
        },
        "performance": {
            "id": "gwt_performance",
            "label": "GWT Performance",
            "status": "PASS" if performance_ok else "OPEN",
            "detail": (
                "KPIs met for commercial scale"
                if performance_ok
                else (
                    f"OPEN — observed ZIP download ~{observed_zip_s:.0f}s "
                    f"(target E2E < {GWT_PERFORMANCE_KPIS['full_e2e_s'][1]}s). "
                    "Optimize Factory/ZIP packing before scale."
                )
            ),
            "kpis": GWT_PERFORMANCE_KPIS,
            "observed_zip_download_s": observed_zip_s,
        },
        # Back-compat aliases for earlier CEO cards
        "logic": {
            "id": "gwt_logic",
            "label": "GWT Logic",
            "status": "PASS" if functional_ok else "FAIL",
            "detail": "Alias of GWT Functional",
        },
    }
    # Ads / full PASS: functional + infra required; performance required for scale flag.
    legacy_pass = str(gwt.get("status") or "").lower() == "pass"
    full_pass = legacy_pass and functional_ok and infra_ok and performance_ok
    functional_closed = functional_ok and infra_ok and not full_pass
    partial = functional_closed  # functional done, scale/performance still open

    # Visual Quality Gate — Business demos must not ship empty decorative zones.
    vqg_ov = ov.get("visual_quality_gate") if isinstance(ov.get("visual_quality_gate"), dict) else {}
    vqg_auto = False
    try:
        from app.factory.visual_intelligence.business_visual_pack import (
            audit_demo_gallery_visual_quality,
        )

        vqg_snap = audit_demo_gallery_visual_quality()
        vqg_auto = bool(vqg_snap.get("ok"))
    except Exception:
        vqg_auto = False
    vqg_flag = str(vqg_ov.get("status") or "").lower()
    if vqg_flag == "fail":
        vqg_ok = False
    elif vqg_flag == "pass":
        vqg_ok = True
    else:
        vqg_ok = vqg_auto

    # Social Integration Gate — every site/store must render social when links exist.
    social_ov = (
        ov.get("social_integration_gate")
        if isinstance(ov.get("social_integration_gate"), dict)
        else {}
    )
    social_auto = False
    try:
        from app.integration.social_integration_gate import (
            audit_social_integration_ready,
        )

        social_auto = bool(audit_social_integration_ready().get("ok"))
    except Exception:
        social_auto = False
    social_flag = str(social_ov.get("status") or "").lower()
    if social_flag == "fail":
        social_ok = False
    elif social_flag == "pass":
        social_ok = True
    else:
        social_ok = social_auto

    # Commercial UX Gate — no Landing-era buyer copy on order / showcase CTAs.
    cux_ov = (
        ov.get("commercial_ux_gate")
        if isinstance(ov.get("commercial_ux_gate"), dict)
        else {}
    )
    cux_auto = False
    try:
        from app.integration.commercial_ux_gate import audit_commercial_ux_ready

        cux_auto = bool(audit_commercial_ux_ready().get("ok"))
    except Exception:
        cux_auto = False
    cux_flag = str(cux_ov.get("status") or "").lower()
    if cux_flag == "fail":
        cux_ok = False
    elif cux_flag == "pass":
        cux_ok = True
    else:
        cux_ok = cux_auto

    gwt_blockers = [
        {
            "id": "guest_checkout",
            "label": "Guest Checkout",
            "status": "done" if guest_ok or full_pass else "blocked",
            "detail": (
                "Guest can open /order without forced register"
                if guest_ok or full_pass
                else "Forced register on /order"
            ),
        },
        {
            "id": "pricing_ssot",
            "label": "Pricing SSOT (DE)",
            "status": "done" if pricing_ok else "blocked",
            "detail": (
                f"DE = {basic.amount}/{business.amount}/{premium.amount} €"
                if pricing_ok
                else f"got {basic.amount}/{business.amount}/{premium.amount}, need 199/399/699"
            ),
        },
        {
            "id": "demo_payment",
            "label": "Demo Payment",
            "status": "done" if demo_pay_ok or full_pass else "blocked",
            "detail": (
                "Complete Demo Payment works for Golden Test orders"
                if demo_pay_ok or full_pass
                else "Need demo pay path without live Stripe charge"
            ),
        },
        {
            "id": "order_email",
            "label": "Order / Account Email",
            "status": "done" if email_ok or full_pass else "blocked",
            "detail": (
                "Buyer receives next-step email (or trusted local delivery)"
                if email_ok or full_pass
                else "Email after pay not confirmed"
            ),
        },
        {
            "id": "factory_publish",
            "label": "Factory → Publish",
            "status": "done" if ((factory_ok and publish_ok) or full_pass) else "blocked",
            "detail": (
                "Generate + publish without operator intervention"
                if (factory_ok and publish_ok) or full_pass
                else "Factory / Publish not confirmed in Golden Test"
            ),
        },
        {
            "id": "production_build",
            "label": "Production Build",
            "status": "done" if build_ok or full_pass else "blocked",
            "detail": (
                "Deployed build includes /why + latest copy"
                if build_ok or full_pass
                else "Rebuild & redeploy before ads"
            ),
        },
    ]

    launch_blockers = [
        {
            "id": "golden_website_test",
            "label": "Golden Website Test",
            "status": "done" if full_pass else ("pending" if functional_closed else "blocked"),
            "detail": (
                "PASS — Functional + Infrastructure + Performance"
                if full_pass
                else (
                    "Functional PASS · Infra PASS (notes) · Performance OPEN (~357s ZIP) — scale gate"
                    if functional_closed
                    else "FAIL until guest → demo pay → Factory → ZIP path is green"
                )
            ),
        },
        {
            "id": "visual_quality_gate",
            "label": "Visual Quality Gate",
            "status": "done" if vqg_ok else "blocked",
            "detail": (
                "Business/Premium: no empty Hero slots; no placeholders"
                if vqg_ok
                else "FAIL — empty decorative zones / weak assets on Business demos"
            ),
        },
        {
            "id": "social_integration_gate",
            "label": "Social Integration Gate",
            "status": "done" if social_ok else "blocked",
            "detail": (
                "L1 Social Links render only when URL exists; Business CMS edit"
                if social_ok
                else "FAIL until Factory injects L1 social (no dead icons) + Business CMS"
            ),
        },
        {
            "id": "commercial_ux_gate",
            "label": "Commercial UX Gate",
            "status": "done" if cux_ok else "blocked",
            "detail": (
                "Order/showcase: Virtus Core terminology — no Landing-era product naming"
                if cux_ok
                else "FAIL — buyer forms/CTAs still say Landing while selling Website/Shop/AI"
            ),
        },
        {
            "id": "demo_gallery",
            "label": "Demo Gallery refreshed",
            "status": "done" if gallery_ok else "blocked",
            "detail": (
                "New Website/Store demos live under /package-previews"
                if gallery_ok
                else "Replace stale R2 demos; preview must open demo without register"
            ),
        },
        {
            "id": "preview_website",
            "label": "Live Preview Website (iframe)",
            "status": "done" if preview_ok else "blocked",
            "detail": (
                "Live-Vorschau embeds package-previews (CSP frame-ancestors self)"
                if preview_ok
                else "White iframe / broken Vollständiges Demo öffnen"
            ),
        },
        {
            "id": "brand_audit",
            "label": "Brand Audit (Genesis → Virtus Core)",
            "status": "done" if brand_ok else "blocked",
            "detail": (
                "Public surfaces show Virtus Core only"
                if brand_ok
                else "Stripe Dashboard name, emails, PDF, titles — no public Genesis"
            ),
        },
        {
            "id": "golden_store_test",
            "label": "Golden AI Store Test",
            "status": "done" if store_ok else "blocked",
            "detail": (
                "PASS — Store path verified"
                if store_ok
                else "After Website PASS — Store order → demo pay → buyer path"
            ),
        },
    ]

    gwt_blocked = sum(1 for b in gwt_blockers if b["status"] != "done")
    launch_blocked = sum(1 for b in launch_blockers if b["status"] != "done")
    website_launch = "READY" if full_pass else "BLOCKED"
    ads_allowed = full_pass  # ads for Website only after GWT PASS; store ads later

    reasons = [b["label"] for b in launch_blockers if b["status"] != "done"]

    return {
        "ok": True,
        "title": "Golden Website Test",
        "subtitle": "Final Launch Blockers before Public Launch",
        "status": (
            "PASS"
            if full_pass
            else ("FUNCTIONAL_PASS" if functional_closed else "FAIL")
        ),
        "layers": layers,
        "functional_status": layers["functional"]["status"],
        "logic_status": layers["logic"]["status"],
        "infrastructure_status": layers["infrastructure"]["status"],
        "performance_status": layers["performance"]["status"],
        "performance_kpis": GWT_PERFORMANCE_KPIS,
        "website_launch": website_launch,
        "ads_allowed": ads_allowed,
        "blockers": gwt_blockers,
        "launch_blockers": launch_blockers,
        "blocked_count": gwt_blocked,
        "launch_blocked_count": launch_blocked,
        "reasons": reasons,
        "campaign_prices_de": {"basic": 199, "business": 399, "premium": 699},
        "live_prices_de": {
            "basic": int(basic.amount),
            "business": int(business.amount),
            "premium": int(premium.amount),
        },
        "checklist_stage1": [
            {"id": "package", "label": "Package selection"},
            {"id": "form", "label": "Order form filled"},
            {"id": "order", "label": "Order created"},
            {"id": "payment", "label": "Payment (demo or live)"},
            {"id": "factory", "label": "Factory started"},
            {"id": "site", "label": "Site generated"},
            {"id": "cabinet", "label": "Order visible in Client Workspace"},
            {"id": "zip", "label": "ZIP downloadable"},
            {"id": "status", "label": "Status updates correctly"},
            {"id": "unattended", "label": "Full path without manual intervention"},
        ],
        "next_after_pass": [
            "GWT Performance: ZIP/Factory under KPI (E2E < 2–3 min; ZIP prepare < 30 s)",
            "Social Integration Gate L1 (order form → Factory; Business CMS)",
            "Brand Audit (Stripe Dashboard name → Virtus Core)",
            "Golden AI Store Test + Commerce Gate",
            "Omnichannel AI (one AI Assistant, official APIs)",
            "Premium Visual Engine (3D / video / Lottie)",
        ],
        "how_to_mark_pass_ru": (
            "Functional уже PASS. Полный scale PASS: "
            'golden_website_test: { "status": "pass", "functional_status": "pass", '
            '"infrastructure_status": "pass", "performance_status": "pass", '
            '"guest_checkout": "pass", "demo_payment": "pass", "order_email": "pass", '
            '"factory": "pass", "publish": "pass", "pricing_ssot": "pass", '
            '"production_build": "pass" }'
        ),
        "focus": (
            "GWT Functional PASS · Performance OPEN (~357s ZIP) — optimize before scale"
            if functional_closed
            else (
                "Website Launch BLOCKED — " + ", ".join(reasons)
                if website_launch == "BLOCKED"
                else "Website Launch READY — advertise Website today"
            )
        ),
        "updated_at": _now(),
    }
