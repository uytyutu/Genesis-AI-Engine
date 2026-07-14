"""API cost optimizer — pick cheapest capable model per task."""

from __future__ import annotations

from typing import Any

_PROVIDER_COST_PER_1K_EUR: dict[str, float] = {
    "groq": 0.00008,
    "gemini": 0.00012,
    "ollama": 0.0,
    "openrouter": 0.00015,
    "openai": 0.00045,
    "anthropic": 0.00055,
}

_TASK_TOKEN_ESTIMATE: dict[str, int] = {
    "simple": 400,
    "conversation": 500,
    "document_analysis": 1200,
    "coding": 900,
    "reasoning": 1500,
}

_TASK_PROVIDER_CHAIN: dict[str, tuple[str, ...]] = {
    "simple": ("groq", "gemini", "ollama", "openrouter", "openai"),
    "conversation": ("groq", "gemini", "ollama", "openrouter", "openai"),
    "document_analysis": ("gemini", "groq", "ollama", "openrouter", "openai"),
    "coding": ("groq", "gemini", "ollama", "deepseek", "openai"),
    "reasoning": ("gemini", "groq", "ollama", "deepseek", "openai"),
}


class ApiCostOptimizer:
    """Maximizes net profit by routing to lowest-cost provider."""

    def provider_chain(self, router_task: str) -> tuple[str, ...]:
        return _TASK_PROVIDER_CHAIN.get(router_task, _TASK_PROVIDER_CHAIN["simple"])

    def estimate_task_cost_eur(self, *, router_task: str, provider_id: str) -> float:
        tokens = _TASK_TOKEN_ESTIMATE.get(router_task, 600)
        rate = _PROVIDER_COST_PER_1K_EUR.get(provider_id, 0.0003)
        return round(tokens / 1000.0 * rate, 6)

    def rank_providers(
        self,
        provider_chain: tuple[str, ...],
        *,
        router_task: str = "simple",
    ) -> list[dict[str, Any]]:
        ranked = sorted(
            provider_chain,
            key=lambda pid: self.estimate_task_cost_eur(router_task=router_task, provider_id=pid),
        )
        out: list[dict[str, Any]] = []
        for idx, pid in enumerate(ranked):
            cost = self.estimate_task_cost_eur(router_task=router_task, provider_id=pid)
            out.append(
                {
                    "provider_id": pid,
                    "estimated_cost_eur": cost,
                    "rank": idx + 1,
                    "tier": "flash" if pid in {"groq", "gemini", "ollama"} else "pro",
                }
            )
        return out

    def pick_cheapest(self, provider_chain: tuple[str, ...], *, router_task: str = "simple") -> dict[str, Any]:
        ranked = self.rank_providers(provider_chain, router_task=router_task)
        best = ranked[0] if ranked else {"provider_id": "groq", "estimated_cost_eur": 0.0}
        return {
            "provider_id": best["provider_id"],
            "estimated_cost_eur": best["estimated_cost_eur"],
            "router_task": router_task,
            "savings_note": "Дешевле модель → выше чистая прибыль на задачу",
            "ranking": ranked[:4],
        }

    def snapshot(self, *, router_task: str = "simple") -> dict[str, Any]:
        chain = self.provider_chain(router_task)
        pick = self.pick_cheapest(chain, router_task=router_task)
        return {
            "router_task": router_task,
            "recommended": pick,
            "cost_table_eur_per_1k": dict(_PROVIDER_COST_PER_1K_EUR),
        }
