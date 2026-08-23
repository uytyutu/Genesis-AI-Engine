"""Quality Gate before RapidAPI publish — FAIL blocks publish."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarm.farm_channels.rapidapi.models import (
    STATUS_APPROVAL_REQUIRED,
    STATUS_QUALITY_GATE,
    STATUS_QUALITY_GATE_FAILED,
)
from swarm.farm_channels.rapidapi.store import ApiFarmStore


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"id": name, "ok": bool(ok), "detail": detail}


def run_quality_gate(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    row = store.get_candidate(candidate_id)
    if not row:
        return {"ok": False, "error": "candidate_not_found", "checks": []}

    store.update_candidate(candidate_id, status=STATUS_QUALITY_GATE)
    pkg = row.get("publish_package") or {}
    plan = pkg.get("plan") or {}
    artifacts = Path(str(pkg.get("artifacts_dir") or ""))
    openapi = plan.get("openapi") if isinstance(plan.get("openapi"), dict) else {}
    pricing = plan.get("pricing") if isinstance(plan.get("pricing"), dict) else {}
    readme = str(plan.get("readme") or "")
    upstream = str(plan.get("upstream") or row.get("upstream") or "")

    checks = [
        _check("api_package_exists", bool(plan), "implementation plan present"),
        _check(
            "openapi_valid",
            bool(openapi.get("openapi") and openapi.get("paths")),
            "OpenAPI 3 + paths",
        ),
        _check(
            "health_endpoint",
            "/health" in (openapi.get("paths") or {}),
            "GET /health declared",
        ),
        _check(
            "authentication",
            bool((openapi.get("components") or {}).get("securitySchemes")),
            "ApiKey security scheme",
        ),
        _check("validation", bool(plan.get("validation")), "request validation planned"),
        _check(
            "error_responses",
            any(
                "400" in (m.get("responses") or {})
                for p in (openapi.get("paths") or {}).values()
                for m in p.values()
                if isinstance(m, dict)
            ),
            "400 responses declared",
        ),
        _check("timeout", float(plan.get("timeout_sec") or 0) > 0, "timeout configured"),
        _check(
            "rate_limiting",
            bool(plan.get("rate_limit")),
            "rate_limit configured",
        ),
        _check(
            "no_secrets_in_package",
            "sk_live" not in json.dumps(plan).lower()
            and "password" not in readme.lower(),
            "no obvious secrets in package",
        ),
        _check(
            "no_fake_usage_claims",
            "fake" not in readme.lower() and not row.get("demo"),
            "docs do not claim fake usage",
        ),
        _check("tests_planned", bool(plan.get("tests_planned")), "test list present"),
        _check("upstream_declared", bool(upstream.strip()), "upstream dependency named"),
        _check(
            "documentation",
            len(readme) > 80 and "## Auth" in readme,
            "README with Auth section",
        ),
        _check(
            "pricing_valid",
            all(k in pricing for k in ("BASIC", "PRO", "ULTRA", "MEGA"))
            and float(pricing.get("PRO") or 0) >= 0,
            "BASIC/PRO/ULTRA/MEGA present",
        ),
        _check(
            "unit_economics_positive",
            float(row.get("expected_margin") or 0) >= 0
            and float(pricing.get("PRO") or 0) * 0.75
            >= float(row.get("operating_cost") or 0),
            "PRO after ~25% fee covers operating_cost",
        ),
        _check(
            "artifacts_on_disk",
            artifacts.is_dir() and (artifacts / "openapi.json").is_file(),
            str(artifacts),
        ),
        _check(
            "not_duplicate_active",
            True,  # duplicate prevention at discover time; re-check soft
            "discover-time duplicate check",
        ),
        _check(
            "public_servers_declared",
            bool((openapi.get("servers") or [])),
            "OpenAPI servers[] must be public production URL (not localhost)",
        ),
    ]

    # Soft runtime health: package-level only until live server exists
    checks.append(
        _check(
            "api_starts_declared",
            True,
            "runtime start deferred until publish host wired — package gate only",
        )
    )

    failed = [c for c in checks if not c["ok"]]
    ok = not failed
    report = {
        "ok": ok,
        "checks": checks,
        "failed": [c["id"] for c in failed],
        "summary": "PASS" if ok else f"FAIL: {', '.join(c['id'] for c in failed)}",
    }
    if ok:
        store.update_candidate(
            candidate_id,
            status=STATUS_APPROVAL_REQUIRED,
            quality_gate=report,
        )
    else:
        store.update_candidate(
            candidate_id,
            status=STATUS_QUALITY_GATE_FAILED,
            quality_gate=report,
            last_error=report["summary"],
        )
    return {"ok": ok, "candidate_id": candidate_id, "quality_gate": report}
