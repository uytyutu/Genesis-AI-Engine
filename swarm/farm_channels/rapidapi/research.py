"""API opportunity research — honest candidates, no fake demand."""

from __future__ import annotations

import uuid
from typing import Any

from swarm.farm_channels.rapidapi.models import STATUS_CANDIDATE, STATUS_DISCOVERED
from swarm.farm_channels.rapidapi.scoring import score_candidate
from swarm.farm_channels.rapidapi.store import ApiFarmStore

# Seed ideas are research hypotheses with explicit evidence tags — not proven demand.
_SEED_IDEAS: list[dict[str, Any]] = [
    {
        "name": "DE Company Imprint Extractor",
        "category": "Business Data",
        "problem": "Developers need structured Impressum fields from German SME sites.",
        "target_user": "CRM / lead-enrichment tools",
        "use_case": "POST url → legal name, address, email if present on page",
        "endpoints": [{"method": "POST", "path": "/v1/imprint/extract"}],
        "upstream": "public website HTML (caller-supplied URL)",
        "demand_score": 62,
        "competition_score": 55,
        "implementation_score": 70,
        "monetization_score": 58,
        "operating_cost": 2.0,
        "suggested_price": {"BASIC": 0, "PRO": 25, "ULTRA": 75, "MEGA": 150},
        "evidence": [
            {
                "type": "hypothesis",
                "note": "Aligned with Virtus Path A DE legal pages — demand not market-proven yet",
            }
        ],
    },
    {
        "name": "Website Contact Finder",
        "category": "Business Data",
        "problem": "Find public contact emails/phones from a company homepage.",
        "target_user": "Outreach / enrichment APIs",
        "use_case": "POST url → contacts[] with source anchors",
        "endpoints": [{"method": "POST", "path": "/v1/contacts/find"}],
        "upstream": "public website HTML",
        "demand_score": 68,
        "competition_score": 72,
        "implementation_score": 75,
        "monetization_score": 60,
        "operating_cost": 1.5,
        "suggested_price": {"BASIC": 0, "PRO": 29, "ULTRA": 79, "MEGA": 149},
        "evidence": [
            {
                "type": "hypothesis",
                "note": "Crowded niche — competition_score high on purpose",
            }
        ],
    },
    {
        "name": "OpenAPI Lint Report",
        "category": "Developer Tools",
        "problem": "Validate OpenAPI 3 docs and return machine-readable issues.",
        "target_user": "API publishers / CI pipelines",
        "use_case": "POST openapi.yaml → issues[] severity",
        "endpoints": [{"method": "POST", "path": "/v1/openapi/lint"}],
        "upstream": "caller-supplied OpenAPI document",
        "demand_score": 55,
        "competition_score": 40,
        "implementation_score": 80,
        "monetization_score": 52,
        "operating_cost": 0.5,
        "suggested_price": {"BASIC": 0, "PRO": 19, "ULTRA": 49, "MEGA": 99},
        "evidence": [
            {"type": "internal_capability", "note": "Fits Farm Quality Gate tooling"},
        ],
    },
    {
        "name": "Currency FX Snapshot",
        "category": "Finance",
        "problem": "Simple EUR/USD/GBP mid rates for micro-apps (no trading).",
        "target_user": "Invoice / SaaS dashboards",
        "use_case": "GET /v1/fx?base=EUR",
        "endpoints": [{"method": "GET", "path": "/v1/fx"}],
        "upstream": "public FX feed (must be licensed before publish)",
        "demand_score": 50,
        "competition_score": 85,
        "implementation_score": 45,
        "monetization_score": 40,
        "operating_cost": 5.0,
        "suggested_price": {"BASIC": 0, "PRO": 15, "ULTRA": 45, "MEGA": 90},
        "evidence": [],  # no evidence → scoring penalty
    },
    {
        "name": "HTML Meta & OG Extractor",
        "category": "Web",
        "problem": "Extract title, description, OG image from a URL.",
        "target_user": "Link previews / content tools",
        "use_case": "POST url → meta object",
        "endpoints": [{"method": "POST", "path": "/v1/meta/extract"}],
        "upstream": "public website HTML",
        "demand_score": 64,
        "competition_score": 60,
        "implementation_score": 85,
        "monetization_score": 55,
        "operating_cost": 1.0,
        "suggested_price": {"BASIC": 0, "PRO": 22, "ULTRA": 59, "MEGA": 120},
        "evidence": [
            {"type": "hypothesis", "note": "Low complexity; good first production API"},
        ],
    },
    {
        "name": "DE PLZ City Lookup",
        "category": "Geo",
        "problem": "Map German PLZ to city/region for forms.",
        "target_user": "German checkout / CRM forms",
        "use_case": "GET /v1/de/plz/{code}",
        "endpoints": [{"method": "GET", "path": "/v1/de/plz/{plz}"}],
        "upstream": "static open PLZ dataset (bundled)",
        "demand_score": 58,
        "competition_score": 50,
        "implementation_score": 90,
        "monetization_score": 48,
        "operating_cost": 0.2,
        "suggested_price": {"BASIC": 0, "PRO": 12, "ULTRA": 35, "MEGA": 70},
        "evidence": [
            {"type": "market_fit", "note": "DE-local; Virtus Core market"},
        ],
    },
]


def discover_candidates(
    store: ApiFarmStore,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Create new candidates from research seeds; skip duplicates."""
    created: list[dict[str, Any]] = []
    for idea in _SEED_IDEAS:
        if len(created) >= limit:
            break
        dup = store.find_duplicate(idea["name"], idea.get("category") or "")
        if dup:
            continue
        row = {
            **idea,
            "id": uuid.uuid4().hex[:12],
            "status": STATUS_DISCOVERED,
            "demo": False,
        }
        scored = score_candidate(row)
        row.update(scored)
        row["status"] = STATUS_CANDIDATE
        created.append(store.upsert_candidate(row))
    return created


def research_refresh(store: ApiFarmStore, candidate_id: str) -> dict[str, Any] | None:
    row = store.get_candidate(candidate_id)
    if not row:
        return None
    scored = score_candidate(row)
    return store.update_candidate(candidate_id, **scored, status=STATUS_CANDIDATE)
