"""Post-publish acquisition pack — no fake users."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.farm_channels.rapidapi.select import candidate_slug
from swarm.farm_channels.rapidapi.store import ApiFarmStore


def build_acquisition_pack(candidate: dict[str, Any]) -> dict[str, Any]:
    name = str(candidate.get("name") or "API")
    slug = candidate_slug(candidate)
    problem = str(candidate.get("problem") or "")
    use_case = str(candidate.get("use_case") or "")
    category = str(candidate.get("category") or "Other")
    pricing = ((candidate.get("publish_package") or {}).get("plan") or {}).get("pricing") or {}
    api_id = str(candidate.get("rapidapi_api_id") or "")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_id": api_id,
        "slug": slug,
        "listing_seo": {
            "name": name,
            "category": category,
            "short_description": (problem[:160] if problem else name),
            "long_description": "\n\n".join(
                p for p in (problem, f"Use case: {use_case}", "Built with Virtus Core API Farm.") if p
            ),
            "tags": [t for t in (category, "germany", "developer", "virtus-core", slug) if t],
            "search_keywords": [name, category, slug, "API", "RapidAPI"],
        },
        "developer_use_cases": [
            {
                "title": use_case or f"Call {name}",
                "steps": [
                    "Subscribe on RapidAPI Hub (BASIC free tier if enabled)",
                    "Copy X-RapidAPI-Key from your app",
                    "Call the documented endpoints with sample payloads",
                ],
            }
        ],
        "examples": [
            {
                "title": "Health",
                "request": "GET /health",
                "response": {"status": "ok"},
            }
        ],
        "docs": {
            "auth": "RapidAPI proxy headers X-RapidAPI-Key + X-RapidAPI-Host on Hub calls",
            "errors": "400 validation · 401 auth · 404 not found · 429 rate limit",
            "rate_limits": ((candidate.get("publish_package") or {}).get("plan") or {}).get(
                "rate_limit"
            ),
            "pricing_hint": pricing,
        },
        "external_discovery": {
            "automatable": [
                "listing_seo_artifact_written",
                "examples_artifact_written",
                "docs_pack_written",
            ],
            "ceo_action": [
                "Confirm Hub category + public visibility in Provider Dashboard",
                "Set / verify BASIC/PRO/ULTRA/MEGA pricing on Hub if not applied via Platform API",
                "Connect PayPal payout in RapidAPI Provider Dashboard (RAPIDAPI_PAYPAL_CONNECTED=1)",
                "Share listing URL in one developer community (manual)",
            ],
        },
        "note": "Acquisition prepares discovery assets. It does not invent users or revenue.",
    }


def run_acquisition(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    row = store.get_candidate(candidate_id)
    if not row:
        return {"ok": False, "error": "candidate_not_found"}
    api_id = str(row.get("rapidapi_api_id") or "").strip()
    if not api_id:
        return {
            "ok": False,
            "requires_ceo_action": True,
            "error": "not_published",
            "detail": "Acquisition runs only after live RapidAPI apiId exists",
        }
    pack = build_acquisition_pack(row)
    out_dir = store.memory_dir / "api_farm_builds" / candidate_id / "acquisition"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "acquisition.json").write_text(
        json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "LISTING.md").write_text(
        "\n".join(
            [
                f"# {pack['listing_seo']['name']}",
                "",
                pack["listing_seo"]["short_description"],
                "",
                pack["listing_seo"]["long_description"],
                "",
                "## Tags",
                ", ".join(pack["listing_seo"]["tags"]),
                "",
                "## CEO ACTION",
                *[f"- {x}" for x in pack["external_discovery"]["ceo_action"]],
            ]
        ),
        encoding="utf-8",
    )
    updated = store.update_candidate(
        candidate_id,
        acquisition={
            "pack_path": str(out_dir / "acquisition.json"),
            "generated_at": pack["generated_at"],
            "ceo_action": pack["external_discovery"]["ceo_action"],
        },
    )
    return {
        "ok": True,
        "candidate": updated,
        "pack": pack,
        "artifacts_dir": str(out_dir),
        "requires_ceo_action": pack["external_discovery"]["ceo_action"],
    }


def enqueue_acquisition(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    return store.enqueue_job("acquire", candidate_id=candidate_id)
