"""Live provider health — why Director skips employees (P0 Product Reality)."""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.integration.genesis_brain.provider_diagnostics import diagnose_workforce
from app.integration.genesis_brain.providers import build_provider_registry
from app.integration.genesis_brain.workforce_performance import WorkforcePerformance
from app.integration.genesis_brain.workforce_quotas import WorkforceQuotas

logger = logging.getLogger(__name__)

_CACHE_TTL_SEC = 120.0
_RATE_LIMIT_TTL_SEC = 3600.0
_PROBE_TIMEOUT_SEC = 8.0

_cache: dict[str, Any] = {"at": 0.0, "rows": []}


def _memory_health_path(memory_dir: Path) -> Path:
    root = memory_dir / "workforce"
    root.mkdir(parents=True, exist_ok=True)
    return root / "health.json"


def _load_persisted(memory_dir: Path) -> dict[str, Any]:
    path = _memory_health_path(memory_dir)
    if not path.is_file():
        return {"employees": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"employees": {}}


def _save_persisted(memory_dir: Path, data: dict[str, Any]) -> None:
    try:
        _memory_health_path(memory_dir).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.debug("provider health persist skip: %s", exc)


def _classify_error(exc: BaseException) -> tuple[str, str]:
    text = str(exc).lower()
    if "429" in text or "rate" in text or "too many" in text:
        return "rate_limited", "API rate limit (429) — quota exhausted or too many requests"
    if "402" in text or "payment" in text:
        return "payment_required", "Billing / credits required (402)"
    if "401" in text or "403" in text or "invalid" in text:
        return "auth_failed", "Invalid or expired API key"
    if "404" in text:
        return "model_not_found", "Model or endpoint not found (404)"
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
        return "timeout", f"Probe timed out ({_PROBE_TIMEOUT_SEC:.0f}s)"
    if isinstance(exc, (httpx.HTTPError, OSError)):
        return "network", f"{type(exc).__name__}: network or host unreachable"
    return "error", f"{type(exc).__name__}: {exc}"


def _probe_one(employee_id: str, provider: Any) -> dict[str, Any]:
    t0 = time.perf_counter()
    row: dict[str, Any] = {
        "employee_id": employee_id,
        "available": False,
        "responds": False,
        "latency_ms": None,
        "avg_latency_ms": None,
        "last_error": None,
        "excluded_reason": None,
        "model": getattr(provider, "model_name", None),
        "probed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        row["available"] = bool(provider.available())
    except Exception as exc:
        code, reason = _classify_error(exc)
        row["last_error"] = reason
        row["excluded_reason"] = code
        return row

    if not row["available"]:
        if employee_id == "ollama":
            row["excluded_reason"] = "offline"
            row["last_error"] = "Ollama offline — run ollama serve"
        else:
            row["excluded_reason"] = "no_key_or_offline"
            row["last_error"] = "Key missing or provider offline"
        return row

    if employee_id == "genesis-local":
        row["responds"] = True
        row["latency_ms"] = 0.0
        row["excluded_reason"] = None
        return row

    try:
        result = provider.chat(
            system="Reply with exactly: OK",
            messages=[{"role": "user", "content": "ping"}],
        )
        latency = (time.perf_counter() - t0) * 1000.0
        answer = (getattr(result, "answer", None) or "").strip()
        row["latency_ms"] = round(latency, 1)
        row["responds"] = bool(answer)
        if not answer:
            row["excluded_reason"] = "empty_response"
            row["last_error"] = "Provider returned empty body"
    except Exception as exc:
        latency = (time.perf_counter() - t0) * 1000.0
        row["latency_ms"] = round(latency, 1)
        code, reason = _classify_error(exc)
        row["last_error"] = reason
        row["excluded_reason"] = code
        if code == "rate_limited":
            WorkforceQuotas().exhaust(employee_id)

    return row


def probe_providers(
    *,
    memory_dir: Path,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Ping each employee — cached 120s unless force=True."""
    now = time.monotonic()
    if not force and _cache.get("rows") and now - float(_cache.get("at", 0)) < _CACHE_TTL_SEC:
        return list(_cache["rows"])

    registry = build_provider_registry([])
    persisted = _load_persisted(memory_dir)
    perf = WorkforcePerformance(memory_dir)
    perf_snap = perf.daily_snapshot()

    rows: list[dict[str, Any]] = []
    probe_ids = [eid for eid in registry if eid != "genesis-local"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_probe_one, eid, registry[eid]): eid for eid in probe_ids
        }
        try:
            done_iter = as_completed(futures, timeout=_PROBE_TIMEOUT_SEC + 2)
            for fut in done_iter:
                try:
                    rows.append(fut.result())
                except Exception as exc:
                    eid = futures[fut]
                    rows.append(
                        {
                            "employee_id": eid,
                            "available": False,
                            "responds": False,
                            "excluded_reason": "probe_failed",
                            "last_error": str(exc),
                        }
                    )
        except TimeoutError:
            for fut, eid in futures.items():
                if fut.done():
                    continue
                rows.append(
                    {
                        "employee_id": eid,
                        "available": registry[eid].available() if eid in registry else False,
                        "responds": False,
                        "excluded_reason": "probe_timeout",
                        "last_error": "Health probe timed out",
                    }
                )

    rows.append(_probe_one("genesis-local", registry["genesis-local"]))
    rows.sort(key=lambda r: r.get("employee_id", ""))

    quotas = WorkforceQuotas(memory_dir)
    diagnostics = diagnose_workforce(registry, quotas=quotas)
    diag_by_id = {d["employee_id"]: d for d in diagnostics}

    employees_persist: dict[str, Any] = dict(persisted.get("employees") or {})
    for row in rows:
        eid = row["employee_id"]
        diag = diag_by_id.get(eid, {})
        q = quotas.snapshot().get(eid, {})
        perf_row = perf_snap.get(eid, {})
        avg_sec = perf_row.get("avg_latency_sec")
        if avg_sec:
            row["avg_latency_ms"] = round(float(avg_sec) * 1000, 1)

        if not q.get("remaining", 1):
            row["excluded_reason"] = row.get("excluded_reason") or "quota_exhausted"
            row["last_error"] = row.get("last_error") or (
                f"Daily quota exhausted ({q.get('used', 0)}/{q.get('limit', 0)})"
            )
            row["responds"] = False

        if row.get("excluded_reason") in ("quota_exhausted", "rate_limited", "payment_required"):
            row["responds"] = False

        if diag.get("code") == "no_key" and eid != "ollama":
            row["available"] = False
            row["responds"] = False
            row["excluded_reason"] = "no_key"
            row["last_error"] = "No API key configured"

        prev = employees_persist.get(eid, {})
        if row.get("excluded_reason") == "rate_limited":
            employees_persist[eid] = {
                **row,
                "rate_limited_until": time.time() + _RATE_LIMIT_TTL_SEC,
            }
        elif prev.get("rate_limited_until", 0) > time.time() and not row.get("responds"):
            row["excluded_reason"] = "rate_limited"
            row["last_error"] = prev.get("last_error") or "Recently rate-limited"
        else:
            employees_persist[eid] = row

        row["director_will_use"] = bool(
            row.get("responds")
            or (eid == "genesis-local")
            or (row.get("available") and not row.get("excluded_reason"))
        )
        if eid == "genesis-local":
            row["director_will_use"] = True

    _save_persisted(memory_dir, {"employees": employees_persist, "updated_at": datetime.now(timezone.utc).isoformat()})
    _cache["at"] = now
    _cache["rows"] = rows
    return rows


def viable_cloud_employees(memory_dir: Path) -> list[str]:
    """Employees Director may try this turn (responds=True, not excluded)."""
    persisted = _load_persisted(memory_dir)
    now = time.time()
    employees = persisted.get("employees") or {}
    if employees:
        cloud = {k: v for k, v in employees.items() if k != "genesis-local"}
        if cloud:
            any_responds = any(bool(v.get("responds")) for v in cloud.values())
            all_rate_limited = all(
                float(v.get("rate_limited_until") or 0) > now
                or v.get("excluded_reason") in ("rate_limited", "quota_exhausted")
                for v in cloud.values()
            )
            if all_rate_limited and not any_responds:
                return []

        # Reuse persisted probe snapshot — avoid 1–2s network probe every chat turn.
        updated_raw = persisted.get("updated_at")
        if updated_raw:
            try:
                ts = datetime.fromisoformat(str(updated_raw).replace("Z", "+00:00"))
                age_sec = (datetime.now(timezone.utc) - ts).total_seconds()
                if age_sec < _CACHE_TTL_SEC:
                    out: list[str] = []
                    for eid, row in employees.items():
                        if eid == "genesis-local":
                            continue
                        if not row.get("responds"):
                            continue
                        if row.get("excluded_reason") in (
                            "rate_limited",
                            "quota_exhausted",
                        ):
                            continue
                        if float(row.get("rate_limited_until") or 0) > now:
                            continue
                        out.append(eid)
                    if out:
                        return out
            except (TypeError, ValueError):
                pass

    rows = probe_providers(memory_dir=memory_dir)
    out: list[str] = []
    for row in rows:
        eid = row["employee_id"]
        if eid == "genesis-local":
            continue
        if row.get("responds"):
            out.append(eid)
    return out


def workforce_health_report(*, memory_dir: Path, force_probe: bool = False) -> dict[str, Any]:
    rows = probe_providers(memory_dir=memory_dir, force=force_probe)
    registry = build_provider_registry([])
    quotas = WorkforceQuotas(memory_dir)
    diagnostics = diagnose_workforce(registry, quotas=quotas)
    viable = [r["employee_id"] for r in rows if r.get("responds")]
    excluded = [
        {
            "employee_id": r["employee_id"],
            "reason": r.get("excluded_reason") or "unknown",
            "detail": r.get("last_error"),
        }
        for r in rows
        if r["employee_id"] != "genesis-local" and not r.get("responds")
    ]
    return {
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "viable_cloud": viable,
        "fallback": "genesis-local",
        "why_fallback": (
            "All cloud employees failed probe or quota — Vector uses core brain (invisible to user)"
            if not viable
            else None
        ),
        "employees": rows,
        "diagnostics": diagnostics,
        "excluded": excluded,
        "policy": (
            "Director tries only employees with responds=true. "
            "genesis-local is always the silent safety net."
        ),
    }
