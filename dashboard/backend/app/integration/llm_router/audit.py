"""Full LLM infrastructure audit — per-provider dev/release report."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.genesis_brain.provider_diagnostics import _has_key, diagnose_workforce
from app.integration.genesis_brain.providers import build_provider_registry
from app.integration.genesis_brain.workforce_performance import WorkforcePerformance
from app.integration.genesis_brain.workforce_quotas import WorkforceQuotas
from app.integration.llm_router.circuit_breaker import CircuitBreaker
from app.integration.llm_router.policies import CLOUD_EMPLOYEES, FREE_TIER_EMPLOYEES
from app.integration.provider_health_service import probe_providers

_PROVIDER_LABELS = {
    "groq": "Groq",
    "gemini": "Gemini",
    "openai": "OpenAI",
    "openrouter": "OpenRouter",
    "ollama": "Ollama",
    "anthropic": "Anthropic",
    "deepseek": "DeepSeek",
    "genesis-local": "genesis-local (emergency)",
}


def _status_label(row: dict[str, Any], *, circuit: dict[str, Any]) -> str:
    eid = row.get("employee_id", "")
    if circuit.get(eid, {}).get("is_open"):
        return "Circuit Open"
    if not row.get("available"):
        if eid == "ollama":
            return "Offline"
        if not _has_key(eid) and eid != "genesis-local":
            return "No Key"
        return "Unavailable"
    if row.get("responds"):
        return "OK"
    reason = row.get("excluded_reason") or ""
    if reason == "rate_limited":
        return "Rate Limit"
    if reason == "payment_required":
        return "Payment Required"
    if reason == "quota_exhausted":
        return "Quota Exhausted"
    if reason == "auth_failed":
        return "Auth Failed"
    if reason == "timeout":
        return "Timeout"
    if reason == "no_key":
        return "No Key"
    return "Error"


def audit_infrastructure(
    *,
    memory_dir: Path | None = None,
    force_probe: bool = True,
) -> dict[str, Any]:
    """Probe every provider and build infrastructure readiness report."""
    mem = memory_dir or Path(__file__).resolve().parents[3] / "memory"
    registry = build_provider_registry([])
    quotas = WorkforceQuotas(mem)
    perf = WorkforcePerformance(mem)
    breaker = CircuitBreaker(mem)
    circuit = breaker.snapshot()

    rows = probe_providers(memory_dir=mem, force=force_probe)
    diagnostics = diagnose_workforce(registry, quotas=quotas)
    diag_by_id = {d["employee_id"]: d for d in diagnostics}
    perf_snap = perf.daily_snapshot()

    by_id = {r["employee_id"]: r for r in rows}
    providers: list[dict[str, Any]] = []

    order = (
        "groq",
        "gemini",
        "openai",
        "openrouter",
        "ollama",
        "anthropic",
        "deepseek",
        "genesis-local",
    )
    viable = [eid for eid in order if eid in CLOUD_EMPLOYEES and by_id.get(eid, {}).get("responds")]

    for eid in order:
        row = by_id.get(eid, {"employee_id": eid})
        diag = diag_by_id.get(eid, {})
        q = quotas.snapshot().get(eid, {})
        perf_row = perf_snap.get(eid, {})
        if q.get("remaining", 1) == 0 and eid != "genesis-local":
            status = "Quota Exhausted"
        else:
            status = _status_label(row, circuit=circuit)
        avg_ms = row.get("avg_latency_ms") or row.get("latency_ms")
        if perf_row.get("avg_latency_sec") and not avg_ms:
            avg_ms = round(float(perf_row["avg_latency_sec"]) * 1000, 1)

        providers.append(
            {
                "provider_id": eid,
                "label": _PROVIDER_LABELS.get(eid, eid),
                "status": status,
                "avg_latency_ms": avg_ms,
                "avg_latency_sec": round(avg_ms / 1000, 2) if avg_ms else None,
                "error": row.get("last_error") or circuit.get(eid, {}).get("last_error"),
                "model": row.get("model") or diag.get("model"),
                "key_configured": diag.get("has_key", _has_key(eid)),
                "quota_remaining": q.get("remaining"),
                "quota_limit": q.get("limit"),
                "responds": bool(row.get("responds")),
                "llm_ready": status == "OK",
                "production_ready": status == "OK",
                "is_free_tier": eid in FREE_TIER_EMPLOYEES,
                "in_use": eid in viable[:3] if eid in CLOUD_EMPLOYEES and status == "OK" else False,
                "circuit_open": bool(circuit.get(eid, {}).get("is_open")),
                "callable": diag.get("callable"),
            }
        )

    cloud_ok = [p for p in providers if p["provider_id"] in CLOUD_EMPLOYEES and p["llm_ready"]]
    free_ok = [p for p in cloud_ok if p.get("is_free_tier")]

    return {
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "stage": "development",
        "policy": (
            "Rule #0: Router + Capability — never a specific vendor. "
            "Architecture Proof: set GENESIS_LLM_PROOF_PROVIDER=groq|gemini|ollama (dev, no code change)."
        ),
        "viable_cloud_count": len(cloud_ok),
        "viable_cloud": [p["provider_id"] for p in cloud_ok],
        "viable_free_tier": [p["provider_id"] for p in free_ok],
        "providers": providers,
        "circuit_breaker": circuit,
        "ready_for_architecture_proof": len(cloud_ok) >= 1,
        "ready_for_product_review": len(cloud_ok) >= 1,
        "production_prep": "after release milestone — OpenAI, Claude, cost intelligence",
    }


def infrastructure_report_table(report: dict[str, Any]) -> str:
    """Markdown table for CEO report."""
    lines = [
        "| Provider | Status | Avg time | Error | In use |",
        "|----------|--------|----------|-------|--------|",
    ]
    for p in report.get("providers") or []:
        if p["provider_id"] == "genesis-local":
            continue
        latency = (
            f"{p['avg_latency_sec']} s"
            if p.get("avg_latency_sec")
            else "—"
        )
        err = (p.get("error") or "—").replace("|", "/")[:60]
        used = "Da" if p.get("in_use") else "Net"
        lines.append(
            f"| {p['label']} | {p['status']} | {latency} | {err} | {used} |"
        )
    lines.append("")
    lines.append(
        f"**Viable cloud:** {report.get('viable_cloud_count', 0)} — "
        f"{', '.join(report.get('viable_cloud') or []) or 'none'}"
    )
    lines.append(
        f"**Viable free tier:** {len(report.get('viable_free_tier') or [])} — "
        f"{', '.join(report.get('viable_free_tier') or []) or 'none'}"
    )
    lines.append(
        f"**Architecture proof ready:** "
        f"{'yes' if report.get('ready_for_architecture_proof') else 'no (need >=1 responding LLM)'}"
    )
    lines.append(
        f"**Production prep:** {report.get('production_prep', 'after release')}"
    )
    return "\n".join(lines)
