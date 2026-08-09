"""Monitor published API Farm products — honest zeros until live keys/usage."""

from __future__ import annotations

from typing import Any

from swarm.farm_channels.rapidapi.models import STATUS_ACTIVE, STATUS_PAUSED, STATUS_PUBLISHED
from swarm.farm_channels.rapidapi.store import ApiFarmStore


def monitor_candidate(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    row = store.get_candidate(candidate_id)
    if not row:
        return {"ok": False, "error": "candidate_not_found"}
    metrics = row.get("metrics") or {}
    health: dict[str, Any] = {"probed": False}
    try:
        from swarm.farm_channels.rapidapi.public_base import runtime_server_url
        from swarm.farm_channels.rapidapi.select import candidate_slug
        from urllib.request import urlopen

        srv = runtime_server_url(candidate_slug(row))
        if srv.get("ok") and srv.get("server_url"):
            url = f"{srv['server_url'].rstrip('/')}/health"
            with urlopen(url, timeout=5) as resp:
                health = {
                    "probed": True,
                    "url": url,
                    "http_status": getattr(resp, "status", 200),
                    "ok": 200 <= (getattr(resp, "status", 200) or 200) < 300,
                }
        else:
            health = {
                "probed": False,
                "requires_ceo_action": True,
                "detail": srv.get("detail") or "public URL missing",
            }
    except Exception as exc:
        health = {"probed": True, "ok": False, "error": str(exc)}
    # No fake usage: leave zeros unless previously recorded from real events
    snapshot = {
        "candidate_id": candidate_id,
        "status": row.get("status"),
        "rapidapi_api_id": row.get("rapidapi_api_id") or "",
        "requests": int(metrics.get("requests") or 0),
        "successful_requests": int(metrics.get("successful_requests") or 0),
        "errors": int(metrics.get("errors") or 0),
        "latency_ms": metrics.get("latency_ms"),
        "subscribers": int(metrics.get("subscribers") or 0),
        "last_activity": row.get("updated_at"),
        "public_health": health,
        "simulated": False,
    }
    return {"ok": True, "monitor": snapshot}


def pause_candidate(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    row = store.update_candidate(candidate_id, status=STATUS_PAUSED)
    return {"ok": bool(row), "candidate": row}


def resume_candidate(store: ApiFarmStore, candidate_id: str) -> dict[str, Any]:
    row = store.get_candidate(candidate_id)
    if not row:
        return {"ok": False, "error": "candidate_not_found"}
    target = STATUS_ACTIVE if row.get("publish_package") else STATUS_PUBLISHED
    updated = store.update_candidate(candidate_id, status=target)
    return {"ok": True, "candidate": updated}


def portfolio_metrics(store: ApiFarmStore) -> dict[str, Any]:
    from swarm.farm_channels.rapidapi.lifecycle import (
        portfolio_lifecycle_summary,
        reconcile_candidate_status,
    )

    # Demote dishonest ACTIVE/PUBLISHED without Hub evidence (no fake LIVE).
    for r in list(store.list_candidates()):
        fix = reconcile_candidate_status(r)
        if fix and fix != r.get("status"):
            store.update_candidate(str(r.get("id")), status=fix)

    rows = store.list_candidates()
    by_status: dict[str, int] = {}
    requests = subscribers = external_subscribers = paid_subscribers = 0
    for r in rows:
        st = str(r.get("status") or "")
        by_status[st] = by_status.get(st, 0) + 1
        m = r.get("metrics") or {}
        if m.get("self_test_only") or m.get("provider_self_test"):
            continue
        requests += int(m.get("external_requests") or m.get("requests") or 0)
        subscribers += int(m.get("subscribers") or 0)
        external_subscribers += int(
            m.get("external_subscribers") or m.get("subscribers") or 0
        )
        paid_subscribers += int(m.get("paid_subscribers") or 0)

    life = portfolio_lifecycle_summary(rows)
    return {
        "counts": by_status,
        "candidates": by_status.get("CANDIDATE", 0)
        + by_status.get("DISCOVERED", 0)
        + by_status.get("RESEARCHING", 0),
        "building": by_status.get("BUILDING", 0),
        "testing": by_status.get("TESTING", 0) + by_status.get("QUALITY_GATE", 0),
        # Ready = CEO approve queue — NOT Live
        "ready": by_status.get("APPROVAL_REQUIRED", 0) + by_status.get("READY", 0),
        "ready_to_publish": life["ready_to_publish"],
        # Published/Live from Hub evidence, not raw ACTIVE count alone
        "published": life["published_apis"],
        "active": life["live_apis"],
        "live_apis": life["live_apis"],
        "published_apis": life["published_apis"],
        "by_lifecycle": life["by_lifecycle"],
        "failed": by_status.get("FAILED", 0) + by_status.get("QUALITY_GATE_FAILED", 0),
        "paused": by_status.get("PAUSED", 0),
        "total_apis": len(rows),
        "api_calls": requests,
        "external_requests": requests,
        "subscribers": subscribers,
        "external_subscribers": external_subscribers,
        "paid_subscribers": paid_subscribers,
        "lifecycle_rule_ru": life["rule_ru"],
    }
