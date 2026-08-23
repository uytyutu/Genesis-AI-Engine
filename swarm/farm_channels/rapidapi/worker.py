"""Durable API Farm job stepper — one step per AUTO-RUN tick."""

from __future__ import annotations

from typing import Any

from swarm.farm_channels.rapidapi.builder import build_candidate
from swarm.farm_channels.rapidapi.monitor import monitor_candidate, portfolio_metrics
from swarm.farm_channels.rapidapi.publisher import approve_candidate, publish_candidate
from swarm.farm_channels.rapidapi.quality_gate import run_quality_gate
from swarm.farm_channels.rapidapi.research import discover_candidates, research_refresh
from swarm.farm_channels.rapidapi.scoring import score_candidate
from swarm.farm_channels.rapidapi.select import select_best_candidate
from swarm.farm_channels.rapidapi.store import ApiFarmStore


def status_payload(store: ApiFarmStore | None = None) -> dict[str, Any]:
    store = store or ApiFarmStore()
    from swarm.farm_channels.rapidapi.public_base import (
        paypal_payout_confirmed,
        resolve_public_api_base,
    )
    from swarm.farm_channels.rapidapi.publisher import auto_publish_allowed
    from swarm.farm_channels.rapidapi.revenue import revenue_summary
    from swarm.farm_execution_plan import rapidapi_account_ok, rapidapi_publish_token_ok

    port = portfolio_metrics(store)
    rev = revenue_summary(store)
    jobs = store.list_jobs(limit=20)
    queued = sum(1 for j in jobs if j.get("status") == "queued")
    running = sum(1 for j in jobs if j.get("status") == "running")
    public = resolve_public_api_base()
    best = select_best_candidate(store)
    ceo_action: list[str] = []
    if not public.get("ok"):
        ceo_action.append(str(public.get("detail") or "Set GENESIS_API_PUBLIC_URL"))
    if not rapidapi_account_ok() or not rapidapi_publish_token_ok():
        ceo_action.append("Set RAPIDAPI_KEY / RAPIDAPI_PUBLISH_TOKEN")
    if not paypal_payout_confirmed():
        ceo_action.append(
            "Connect PayPal in RapidAPI Provider Dashboard → RAPIDAPI_PAYPAL_CONNECTED=1"
        )
    from swarm.farm_channels.rapidapi.markets import (
        coverage_summary,
        market_capabilities_matrix,
        products_catalog,
    )

    markets = coverage_summary()
    return {
        "channel": "rapidapi",
        "title": "API Farm",
        "auto_publish": auto_publish_allowed(),
        "credentials": {
            "rapidapi_account": rapidapi_account_ok(),
            "publish_token": rapidapi_publish_token_ok(),
        },
        "public_api": public,
        "paypal_payout_confirmed": paypal_payout_confirmed(),
        "best_candidate": (
            {
                "id": best.get("id"),
                "name": best.get("name"),
                "status": best.get("status"),
                "total_score": best.get("total_score"),
            }
            if best
            else None
        ),
        "ceo_action": ceo_action,
        "requires_ceo_action": bool(ceo_action),
        "portfolio": port,
        "revenue": rev,
        "markets": markets,
        "market_matrix": market_capabilities_matrix(wave_only=True),
        "api_products": products_catalog(),
        "jobs": {"queued": queued, "running": running, "recent": jobs[:10]},
        "payout_path_ru": "RapidAPI → PayPal (не Stripe)",
        "money_rule_ru": "Actual = только подтверждённый PAID_OUT",
    }


def enqueue_pipeline(
    store: ApiFarmStore,
    *,
    discover: bool = True,
    candidate_id: str = "",
    through_quality_gate: bool = True,
) -> list[dict[str, Any]]:
    """Enqueue durable jobs for AUTO-RUN / manual run."""
    jobs: list[dict[str, Any]] = []
    if discover:
        jobs.append(store.enqueue_job("discover"))
    if candidate_id:
        jobs.append(store.enqueue_job("score", candidate_id=candidate_id))
        jobs.append(store.enqueue_job("build", candidate_id=candidate_id))
        jobs.append(store.enqueue_job("test", candidate_id=candidate_id))
        if through_quality_gate:
            jobs.append(store.enqueue_job("quality_gate", candidate_id=candidate_id))
    return jobs


def run_first_api(store: ApiFarmStore, *, max_steps: int = 12) -> dict[str, Any]:
    """Discover if needed → pick best → build+gate only that candidate → APPROVAL_REQUIRED."""
    if not store.list_candidates():
        discover_candidates(store, limit=10)
    best = select_best_candidate(store)
    if not best:
        return {"ok": False, "error": "no_candidates", "requires_ceo_action": True}
    cid = str(best["id"])
    # Clear competing queued jobs for other candidates (keep history, don't enqueue spam)
    enqueue_pipeline(store, discover=False, candidate_id=cid, through_quality_gate=True)
    burst = run_burst(store, max_steps=max_steps)
    row = store.get_candidate(cid)
    return {
        "ok": True,
        "action": "first_api",
        "candidate_id": cid,
        "candidate": row,
        "burst": burst,
        "status": status_payload(store),
        "next": "CEO Approve → Publish (live RapidAPI provision)",
    }


def step(store: ApiFarmStore | None = None) -> dict[str, Any]:
    """Claim one queued job and advance it. Safe to call from farm tick."""
    store = store or ApiFarmStore()
    job = store.claim_next_job()
    if not job:
        return {"ok": True, "idle": True, "job": None}

    kind = str(job.get("kind") or "")
    cid = str(job.get("candidate_id") or "")
    try:
        result = _run_kind(store, kind, cid)
        ok = bool(result.get("ok", True))
        store.finish_job(job["id"], ok=ok, result=result, error=str(result.get("error") or ""))
        return {"ok": ok, "idle": False, "job": job, "result": result}
    except Exception as exc:
        store.finish_job(job["id"], ok=False, error=str(exc))
        return {"ok": False, "idle": False, "job": job, "error": str(exc)}


def _run_kind(store: ApiFarmStore, kind: str, candidate_id: str) -> dict[str, Any]:
    if kind == "discover":
        created = discover_candidates(store, limit=10)
        # Prefer single-track: queue only best candidate
        best = select_best_candidate(store)
        if best:
            enqueue_pipeline(
                store,
                discover=False,
                candidate_id=str(best["id"]),
                through_quality_gate=True,
            )
        elif created:
            enqueue_pipeline(
                store,
                discover=False,
                candidate_id=str(created[0]["id"]),
                through_quality_gate=True,
            )
        return {
            "ok": True,
            "created": len(created),
            "ids": [c["id"] for c in created],
            "queued_best": (best or (created[0] if created else {})).get("id"),
        }

    if kind == "first_api":
        return run_first_api(store)

    if kind == "research":
        row = research_refresh(store, candidate_id)
        return {"ok": bool(row), "candidate": row}

    if kind == "score":
        row = store.get_candidate(candidate_id)
        if not row:
            return {"ok": False, "error": "candidate_not_found"}
        scored = score_candidate(row)
        updated = store.update_candidate(candidate_id, **scored)
        return {"ok": True, "candidate": updated}

    if kind in ("build", "test"):
        return build_candidate(store, candidate_id)

    if kind == "quality_gate":
        return run_quality_gate(store, candidate_id)

    if kind == "prepare_publish":
        from swarm.farm_channels.rapidapi.publisher import build_publish_package

        row = store.get_candidate(candidate_id)
        if not row:
            return {"ok": False, "error": "candidate_not_found"}
        package = build_publish_package(row)
        store.update_candidate(
            candidate_id,
            publish_package={**(row.get("publish_package") or {}), "listing": package},
        )
        return {"ok": True, "package": package}

    if kind == "publish":
        return publish_candidate(store, candidate_id)

    if kind == "monitor":
        return monitor_candidate(store, candidate_id)

    if kind == "approve":
        return approve_candidate(store, candidate_id)

    if kind == "acquire":
        from swarm.farm_channels.rapidapi.acquisition import run_acquisition

        return run_acquisition(store, candidate_id)

    return {"ok": False, "error": f"unknown_kind:{kind}"}


def run_burst(store: ApiFarmStore | None = None, *, max_steps: int = 8) -> dict[str, Any]:
    store = store or ApiFarmStore()
    results = []
    for _ in range(max(1, int(max_steps))):
        out = step(store)
        results.append(out)
        if out.get("idle"):
            break
    return {"ok": True, "steps": results, "status": status_payload(store)}
