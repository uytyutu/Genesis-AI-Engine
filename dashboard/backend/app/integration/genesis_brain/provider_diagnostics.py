"""Why each Workforce employee is or is not callable — runtime diagnostics (dev only)."""

from __future__ import annotations

import os
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME
from app.integration.genesis_brain.workforce_quotas import WorkforceQuotas

_ENV_KEYS: dict[str, tuple[str, ...]] = {
    "groq": ("GENESIS_GROQ_API_KEY", "GROQ_API_KEY", "GENESIS_LLM_API_KEY"),
    "gemini": ("GENESIS_GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "openrouter": ("GENESIS_OPENROUTER_API_KEY",),
    "ollama": (),
    "openai": ("GENESIS_LLM_API_KEY", "OPENAI_API_KEY"),
    "anthropic": ("GENESIS_ANTHROPIC_API_KEY",),
    "deepseek": ("GENESIS_DEEPSEEK_API_KEY",),
    "kimi": ("GENESIS_KIMI_API_KEY", "MOONSHOT_API_KEY"),
}

_CLOUD_ORDER = (
    "groq",
    "gemini",
    "openrouter",
    "ollama",
    "openai",
    "anthropic",
    "deepseek",
    "kimi",
)


def _has_key(employee_id: str) -> bool:
    if employee_id == "ollama":
        return True
    for key in _ENV_KEYS.get(employee_id, ()):
        if os.getenv(key, "").strip():
            return True
    return False


def diagnose_employee(
    employee_id: str,
    provider: Any | None,
    quotas: WorkforceQuotas,
    *,
    in_workforce_plan: bool = True,
    premium_blocked: bool = False,
) -> dict[str, Any]:
    if employee_id == "genesis-local":
        return {
            "employee_id": employee_id,
            "callable": True,
            "code": "core",
            "reason": f"{ASSISTANT_NAME} Local — core brain, always active",
            "has_key": True,
            "quota_ok": True,
        }

    has_key = _has_key(employee_id)
    quota_ok = quotas.has_budget(employee_id)
    quota = quotas.snapshot().get(employee_id, {})

    if premium_blocked:
        return {
            "employee_id": employee_id,
            "callable": False,
            "code": "premium_blocked",
            "reason": "Premium employee — not enabled for this task",
            "has_key": has_key,
            "quota_ok": quota_ok,
            "quota": quota,
        }

    if not in_workforce_plan:
        return {
            "employee_id": employee_id,
            "callable": False,
            "code": "not_in_plan",
            "reason": "Not in workforce plan for this turn",
            "has_key": has_key,
            "quota_ok": quota_ok,
        }

    if employee_id != "ollama" and not has_key:
        return {
            "employee_id": employee_id,
            "callable": False,
            "code": "no_key",
            "reason": "No API key in environment",
            "has_key": False,
            "quota_ok": quota_ok,
            "env_vars": list(_ENV_KEYS.get(employee_id, ())),
        }

    if not quota_ok:
        return {
            "employee_id": employee_id,
            "callable": False,
            "code": "quota",
            "reason": f"Daily quota exhausted ({quota.get('used', 0)}/{quota.get('limit', 0)})",
            "has_key": has_key,
            "quota_ok": False,
            "quota": quota,
        }

    if provider is None:
        return {
            "employee_id": employee_id,
            "callable": False,
            "code": "disabled",
            "reason": "Provider not registered",
            "has_key": has_key,
            "quota_ok": quota_ok,
        }

    try:
        available = provider.available()
    except Exception as exc:
        return {
            "employee_id": employee_id,
            "callable": False,
            "code": "network",
            "reason": f"availability check failed: {type(exc).__name__}",
            "has_key": has_key,
            "quota_ok": quota_ok,
        }

    if not available:
        if employee_id == "ollama":
            reason = "Ollama offline — run ollama serve"
            code = "offline"
        else:
            reason = "Key present but provider unavailable (network, invalid key, or API down)"
            code = "network"
        return {
            "employee_id": employee_id,
            "callable": False,
            "code": code,
            "reason": reason,
            "has_key": has_key,
            "quota_ok": quota_ok,
        }

    model = getattr(provider, "model_name", None) or getattr(provider, "_model", None)
    return {
        "employee_id": employee_id,
        "callable": True,
        "code": "ready",
        "reason": "Ready",
        "has_key": has_key,
        "quota_ok": quota_ok,
        "model": model,
    }


def diagnose_workforce(
    registry: dict[str, Any],
    *,
    plan_order: list[str] | None = None,
    premium_ids: frozenset[str] | None = None,
    quotas: WorkforceQuotas | None = None,
) -> list[dict[str, Any]]:
    q = quotas or WorkforceQuotas()
    plan_set = set(plan_order or _CLOUD_ORDER)
    premium = premium_ids or frozenset({"openai", "anthropic"})
    out: list[dict[str, Any]] = []
    for eid in _CLOUD_ORDER:
        blocked = eid in premium and eid not in plan_set
        out.append(
            diagnose_employee(
                eid,
                registry.get(eid),
                q,
                in_workforce_plan=eid in plan_set or not blocked,
                premium_blocked=blocked,
            )
        )
    out.append(diagnose_employee("genesis-local", registry.get("genesis-local"), q))
    return out
