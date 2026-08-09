"""CEO-gated RapidAPI publish — live OpenAPI provisioning only (no fake ACTIVE)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.farm_channels.rapidapi.models import (
    STATUS_APPROVAL_REQUIRED,
    STATUS_PUBLISHED,
    STATUS_PUBLISHING,
    STATUS_QUALITY_GATE_FAILED,
    STATUS_ACTIVE,
)
from swarm.farm_channels.rapidapi.public_base import (
    paypal_payout_confirmed,
    resolve_public_api_base,
    runtime_server_url,
)
from swarm.farm_channels.rapidapi.select import candidate_slug
from swarm.farm_channels.rapidapi.store import ApiFarmStore


def auto_publish_allowed() -> bool:
    """Marketplace auto-publish stays FALSE until CEO proves pipeline."""
    return False


def build_publish_package(candidate: dict[str, Any]) -> dict[str, Any]:
    pkg = candidate.get("publish_package") or {}
    plan = pkg.get("plan") or {}
    slug = plan.get("slug") or candidate_slug(candidate)
    server = runtime_server_url(str(slug))
    return {
        "api_name": candidate.get("name"),
        "description": candidate.get("problem"),
        "category": candidate.get("category"),
        "endpoints": candidate.get("endpoints") or [],
        "openapi": plan.get("openapi"),
        "authentication": plan.get("auth"),
        "documentation": plan.get("readme"),
        "pricing": plan.get("pricing"),
        "examples": [
            {
                "title": "Health",
                "request": "GET /health",
                "response": {"status": "ok"},
            }
        ],
        "usage_limits": plan.get("rate_limit"),
        "terms": "Caller must respect website ToS and robots for upstream URLs.",
        "support": "hello@virtuscore.com",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "public_server": server,
        "ceo_action": {
            "paypal": not paypal_payout_confirmed(),
            "hub_pricing": True,
        },
    }


def approve_candidate(
    store: ApiFarmStore,
    candidate_id: str,
    *,
    note: str = "",
) -> dict[str, Any]:
    row = store.get_candidate(candidate_id)
    if not row:
        return {"ok": False, "error": "candidate_not_found"}
    if row.get("status") == STATUS_QUALITY_GATE_FAILED:
        return {"ok": False, "error": "quality_gate_failed"}
    qg = row.get("quality_gate") or {}
    if not qg.get("ok"):
        return {
            "ok": False,
            "error": "quality_gate_required",
            "detail": "Quality Gate must PASS before approval",
        }
    updated = store.update_candidate(
        candidate_id,
        approval={
            "required": True,
            "approved": True,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "note": note or "",
        },
        status=STATUS_APPROVAL_REQUIRED,
    )
    return {"ok": True, "candidate": updated}


def publish_candidate(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    """CEO publish — live RapidAPI provision; never mark ACTIVE without apiId."""
    from swarm.farm_channels.rapidapi.provision import provision_create_api
    from swarm.farm_execution_plan import rapidapi_account_ok, rapidapi_publish_token_ok

    row = store.get_candidate(candidate_id)
    if not row:
        return {"ok": False, "error": "candidate_not_found"}

    if not (row.get("approval") or {}).get("approved"):
        return {
            "ok": False,
            "error": "approval_required",
            "requires_ceo_action": True,
            "detail": "CEO must Approve before Publish (AUTO_PUBLISH=false)",
        }

    if not (row.get("quality_gate") or {}).get("ok"):
        return {"ok": False, "error": "quality_gate_required"}

    _ = auto_publish_allowed()  # always False

    if not rapidapi_account_ok() or not rapidapi_publish_token_ok():
        return {
            "ok": False,
            "error": "missing_credentials",
            "requires_ceo_action": True,
            "blocked": True,
            "detail": (
                "Set RAPIDAPI_KEY or RAPIDAPI_PROVIDER_KEY / RAPIDAPI_PUBLISH_TOKEN "
                "in backend env. PayPal payout stays in RapidAPI provider account."
            ),
        }

    public = resolve_public_api_base()
    if not public.get("ok"):
        return {
            "ok": False,
            "error": public.get("error") or "public_api_url_missing",
            "requires_ceo_action": True,
            "blocked": True,
            "detail": public.get("detail"),
        }

    slug = candidate_slug(row)
    server = runtime_server_url(slug)
    if not server.get("ok"):
        return {
            "ok": False,
            "error": server.get("error") or "server_url_invalid",
            "requires_ceo_action": True,
            "detail": server.get("detail"),
        }

    # Ensure OpenAPI servers point at public runtime before provision
    pkg = row.get("publish_package") or {}
    plan = dict(pkg.get("plan") or {})
    openapi = dict(plan.get("openapi") or {})
    openapi["servers"] = [
        {"url": server["server_url"], "description": "Virtus Core production"}
    ]
    plan["openapi"] = openapi
    plan["public_server"] = server

    store.update_candidate(
        candidate_id,
        status=STATUS_PUBLISHING,
        publish_package={**pkg, "plan": plan},
    )

    package = build_publish_package(store.get_candidate(candidate_id) or row)
    out = store.memory_dir / "api_farm_builds" / candidate_id / "publish_package.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    provision = provision_create_api(
        openapi=openapi,
        api_name=str(row.get("name") or slug),
        category=str(row.get("category") or ""),
        artifacts_dir=Path(out.parent),
    )

    if not provision.get("ok") or not provision.get("api_id"):
        # Revert to approval-required — never fake PUBLISHED/ACTIVE
        prev_pkg = (store.get_candidate(candidate_id) or {}).get("publish_package") or {}
        store.update_candidate(
            candidate_id,
            status=STATUS_APPROVAL_REQUIRED,
            last_error=str(provision.get("detail") or provision.get("error") or "provision_failed"),
            publish_package={
                **prev_pkg,
                "listing": package,
                "provision_attempt": provision,
                "channel": "rapidapi",
            },
        )
        return {
            "ok": False,
            "error": provision.get("error") or "provision_failed",
            "requires_ceo_action": True,
            "blocked": True,
            "detail": provision.get("detail"),
            "provision": provision,
            "ceo_action": [
                "Verify RAPIDAPI_PROVISION_URL / RAPIDAPI_PLATFORM_HOST match Hub CI/CD snippet",
                "Confirm Provider account can create APIs",
                "Set GENESIS_API_PUBLIC_URL to production Virtus API",
                "Connect PayPal in Provider Dashboard when ready (RAPIDAPI_PAYPAL_CONNECTED=1)",
            ],
        }

    api_id = str(provision["api_id"])
    prev_ok = (store.get_candidate(candidate_id) or {}).get("publish_package") or {}
    store.update_candidate(
        candidate_id,
        status=STATUS_PUBLISHED,
        rapidapi_api_id=api_id,
        publish_package={
            **prev_ok,
            "listing": package,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "channel": "rapidapi",
            "provision": provision,
            "rapidapi_api_id": api_id,
        },
    )
    updated = store.update_candidate(candidate_id, status=STATUS_ACTIVE)

    # Acquisition after real Hub id
    from swarm.farm_channels.rapidapi.acquisition import enqueue_acquisition, run_acquisition

    enqueue_acquisition(store, candidate_id)
    acq = run_acquisition(store, candidate_id)

    ceo_action = [
        "Set / verify Hub pricing (BASIC/PRO/ULTRA/MEGA) if not applied by Platform API",
        "Confirm public visibility on RapidAPI Hub",
    ]
    if not paypal_payout_confirmed():
        ceo_action.append(
            "Connect PayPal in RapidAPI Provider Dashboard, then set RAPIDAPI_PAYPAL_CONNECTED=1"
        )

    return {
        "ok": True,
        "candidate": updated,
        "api_id": api_id,
        "package_path": str(out),
        "server_url": server["server_url"],
        "acquisition": acq,
        "paypal_payout_confirmed": paypal_payout_confirmed(),
        "requires_ceo_action": ceo_action,
    }
