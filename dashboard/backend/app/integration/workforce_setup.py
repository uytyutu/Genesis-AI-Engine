"""Genesis Setup v2 — AI Workforce status and employee connection (not OpenAI-only)."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

from app.env_loader import load_local_env
from app.integration.genesis_brain.providers import build_provider_registry
from app.integration.secrets_env_service import SecretsEnvService

logger = logging.getLogger(__name__)

EmployeeStatus = Literal["ready", "not_connected", "offline"]

SETUP_EMPLOYEES: tuple[dict[str, Any], ...] = (
    {
        "id": "genesis-local",
        "label": "Virtus Local",
        "premium": False,
        "core": True,
        "tier": "core",
        "roles": [
            "Core Brain",
            "Memory",
            "Executive Mind",
            "Thinking Engine",
            "Offline reasoning",
        ],
    },
    {"id": "groq", "label": "Groq", "premium": False, "tier": "free"},
    {"id": "gemini", "label": "Gemini", "premium": False, "tier": "free"},
    {"id": "openrouter", "label": "OpenRouter", "premium": False, "tier": "free"},
    {"id": "ollama", "label": "Ollama", "premium": False, "tier": "local"},
    {"id": "openai", "label": "OpenAI Premium", "premium": True, "tier": "optional"},
)

CONNECTABLE = frozenset({"groq", "gemini", "openrouter", "ollama", "openai"})

_ENV_KEYS: dict[str, list[tuple[str, str | None]]] = {
    "groq": [("GENESIS_GROQ_API_KEY", None), ("GENESIS_LLM_API_KEY", None)],
    "gemini": [("GENESIS_GEMINI_API_KEY", None)],
    "openrouter": [("GENESIS_OPENROUTER_API_KEY", None)],
    "openai": [("GENESIS_LLM_API_KEY", None)],
}

_DEFAULT_MODELS: dict[str, str] = {
    "groq": "llama-3.3-70b-versatile",
    "gemini": "gemini-2.0-flash",
    "openrouter": "google/gemini-2.0-flash-001",
    "openai": "gpt-4o-mini",
}

_MODEL_ENV: dict[str, str] = {
    "groq": "GENESIS_GROQ_MODEL",
    "gemini": "GENESIS_GEMINI_MODEL",
    "openrouter": "GENESIS_OPENROUTER_MODEL",
    "openai": "GENESIS_LLM_MODEL",
}

_OPENAI_MODELS = frozenset(
    {"gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "gpt-3.5-turbo"}
)


class WorkforceSetupService:
    """Owner setup — connect AI Workforce employees."""

    def __init__(self) -> None:
        self._secrets = SecretsEnvService()

    def status(self) -> dict[str, Any]:
        load_local_env()
        employees = self._employee_rows()
        cloud_ready = [
            e for e in employees if e["status"] == "ready" and e["id"] != "genesis-local"
        ]
        free_ready = [
            e for e in cloud_ready if e.get("tier") == "free"
        ]
        tier = "full" if cloud_ready else "limited"
        from app.integration.genesis_brain.workforce_director import WorkforceDirector

        director = WorkforceDirector()
        return {
            "genesis_ready": True,
            "workforce_tier": tier,
            "cloud_employees_ready": len(cloud_ready),
            "free_employees_ready": len(free_ready),
            "owner_setup_complete": len(free_ready) >= 1,
            "employees": employees,
            "workforce_director": director.director_snapshot(),
            "setup_wizard_available": self._secrets.local_write_allowed(),
            "llm_configured": len(cloud_ready) > 0,
            "intelligence_active": True,
            "mode": "genesis",
            "env_file": self._secrets.env_file_label(),
            "allowed_models": sorted(_OPENAI_MODELS),
            "connectable": sorted(CONNECTABLE),
            "setup_once_hint": (
                "Подключите Groq, Gemini, OpenRouter один раз — Virtus Director сам переключается при лимитах."
            ),
        }

    def _employee_rows(self) -> list[dict[str, Any]]:
        from app.integration.genesis_brain.workforce_quotas import WorkforceQuotas

        registry = build_provider_registry([])
        quotas = WorkforceQuotas()
        qsnap = quotas.snapshot()
        rows: list[dict[str, Any]] = []
        for meta in SETUP_EMPLOYEES:
            eid = meta["id"]
            q = qsnap.get(eid, {})
            quota_info = {
                "quota_remaining": q.get("remaining", 0),
                "quota_limit": q.get("limit", 0),
            }
            if eid == "genesis-local":
                rows.append({**meta, "status": "ready", **quota_info})
                continue
            has_key = self._has_credentials(eid)
            provider = registry.get(eid)
            if eid == "ollama":
                if provider and provider.available():
                    status = "ready"
                else:
                    status = "offline"
            elif not has_key:
                status = "not_connected"
            elif provider and provider.available():
                status = "ready"
            else:
                status = "not_connected"
            rows.append({**meta, "status": status, **quota_info})
        return rows

    @staticmethod
    def _has_credentials(employee_id: str) -> bool:
        if employee_id == "ollama":
            return True
        if employee_id == "genesis-local":
            return True
        for key, _ in _ENV_KEYS.get(employee_id, []):
            if os.getenv(key, "").strip():
                return True
        if employee_id == "gemini" and os.getenv("GOOGLE_API_KEY", "").strip():
            return True
        return False

    def configure(
        self,
        *,
        provider: str,
        api_key: str = "",
        model: str | None = None,
    ) -> dict[str, Any]:
        if not self._secrets.local_write_allowed():
            raise PermissionError(
                "Local secrets write disabled. Set employee API keys in host environment."
            )

        pid = provider.strip().lower()
        if pid not in CONNECTABLE:
            raise ValueError(f"Unsupported employee: {provider}")

        if pid != "ollama":
            key = api_key.strip()
            if len(key) < 8:
                raise ValueError("API key is too short")
            for env_key, _ in _ENV_KEYS.get(pid, []):
                self._secrets.upsert(env_key, key)
            model_env = _MODEL_ENV.get(pid)
            if model_env:
                chosen = (model or _DEFAULT_MODELS.get(pid, "")).strip()
                if pid == "openai" and chosen not in _OPENAI_MODELS:
                    raise ValueError(f"Unsupported model: {chosen}")
                if chosen:
                    self._secrets.upsert(model_env, chosen)

        load_local_env()
        try:
            self._verify_employee(pid)
        except Exception as exc:
            logger.warning("Workforce setup verify failed %s: %s", pid, type(exc).__name__)
            raise ValueError(
                f"Ключ сохранён, но {pid} не ответил. Проверьте ключ и повторите."
            ) from exc

        st = self.status()
        label = next((e["label"] for e in SETUP_EMPLOYEES if e["id"] == pid), pid)
        logger.info("Virtus Workforce: %s connected via setup v2", pid)
        return {
            "ok": True,
            "provider": pid,
            "llm_configured": st["llm_configured"],
            "workforce_tier": st["workforce_tier"],
            "employees": st["employees"],
            "mode": "genesis",
            "model": model or _DEFAULT_MODELS.get(pid),
            "message": f"{label} подключён — Virtus Workforce может использовать этого сотрудника.",
            "env_file": self._secrets.env_file_label(),
        }

    def _verify_employee(self, provider_id: str) -> None:
        registry = build_provider_registry([])
        provider = registry.get(provider_id)
        if provider is None:
            raise RuntimeError(f"unknown employee {provider_id}")
        if not provider.available():
            if provider_id == "ollama":
                raise RuntimeError("Ollama offline — запустите ollama serve")
            raise RuntimeError(f"{provider_id} not available")
        provider.chat(
            system="Reply with exactly: OK",
            messages=[{"role": "user", "content": "ping"}],
        )
