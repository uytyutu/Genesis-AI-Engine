"""Build implementation plan + publish-ready artifacts for a candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarm.farm_channels.rapidapi.models import STATUS_BUILDING, STATUS_TESTING
from swarm.farm_channels.rapidapi.store import ApiFarmStore


def _default_pricing(suggested: dict[str, Any] | None) -> dict[str, Any]:
    base = {"BASIC": 0, "PRO": 25, "ULTRA": 75, "MEGA": 150}
    if isinstance(suggested, dict) and suggested:
        for k, v in suggested.items():
            key = str(k).upper()
            if key in base:
                try:
                    base[key] = float(v)
                except (TypeError, ValueError):
                    pass
    return base


def build_implementation_plan(candidate: dict[str, Any]) -> dict[str, Any]:
    from swarm.farm_channels.rapidapi.public_base import runtime_server_url

    pricing = _default_pricing(candidate.get("suggested_price"))
    endpoints = candidate.get("endpoints") or [
        {"method": "GET", "path": "/health"},
        {"method": "POST", "path": "/v1/run"},
    ]
    name = str(candidate.get("name") or "unnamed-api")
    slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    server = runtime_server_url(slug)
    servers: list[dict[str, str]] = []
    if server.get("ok") and server.get("server_url"):
        servers = [{"url": str(server["server_url"]), "description": "Virtus Core production"}]
    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": name,
            "version": "0.1.0",
            "description": str(candidate.get("problem") or ""),
        },
        "servers": servers,
        "paths": {},
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-Api-Key"}
            }
        },
        "security": [{"ApiKeyAuth": []}],
    }
    for ep in endpoints:
        path = str(ep.get("path") or "/v1/run")
        method = str(ep.get("method") or "GET").lower()
        openapi["paths"].setdefault(path, {})[method] = {
            "summary": f"{method.upper()} {path}",
            "responses": {
                "200": {"description": "OK"},
                "400": {"description": "Validation error"},
                "401": {"description": "Unauthorized"},
                "429": {"description": "Rate limited"},
                "504": {"description": "Timeout"},
            },
        }
    openapi["paths"].setdefault("/health", {})["get"] = {
        "summary": "Health",
        "security": [],
        "responses": {"200": {"description": "OK"}},
    }
    readme = "\n".join(
        [
            f"# {name}",
            "",
            str(candidate.get("problem") or ""),
            "",
            "## Use case",
            str(candidate.get("use_case") or ""),
            "",
            "## Auth",
            "Header `X-Api-Key`.",
            "",
            "## Rate limiting",
            "Default 60 req/min (configurable).",
            "",
            "## Timeout",
            "30s request timeout.",
            "",
            "## Pricing (configurable)",
            json.dumps(pricing, indent=2),
        ]
    )
    return {
        "slug": slug,
        "openapi": openapi,
        "readme": readme,
        "pricing": pricing,
        "auth": {"type": "apiKey", "header": "X-Api-Key"},
        "rate_limit": {"requests_per_minute": 60},
        "timeout_sec": 30,
        "health_path": "/health",
        "logging": True,
        "validation": True,
        "error_handling": True,
        "tests_planned": [
            "health_ok",
            "auth_required",
            "validation_400",
            "rate_limit_header",
        ],
        "upstream": str(candidate.get("upstream") or ""),
        "public_server": server,
        "runtime_path": f"/api/farm/runtime/{slug}",
    }


def persist_build_artifacts(
    store: ApiFarmStore,
    candidate_id: str,
    plan: dict[str, Any],
) -> Path:
    out = store.memory_dir / "api_farm_builds" / candidate_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "openapi.json").write_text(
        json.dumps(plan.get("openapi") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "README.md").write_text(str(plan.get("readme") or ""), encoding="utf-8")
    (out / "pricing.json").write_text(
        json.dumps(plan.get("pricing") or {}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out


def build_candidate(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    row = store.get_candidate(candidate_id)
    if not row:
        return {"ok": False, "error": "candidate_not_found"}
    store.update_candidate(candidate_id, status=STATUS_BUILDING)
    plan = build_implementation_plan(row)
    path = persist_build_artifacts(store, candidate_id, plan)
    updated = store.update_candidate(
        candidate_id,
        status=STATUS_TESTING,
        publish_package={"plan": plan, "artifacts_dir": str(path)},
    )
    return {"ok": True, "candidate": updated, "plan": plan, "artifacts_dir": str(path)}
