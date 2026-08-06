"""Opire — first live Tier A connector (official api.opire.dev only)."""

from __future__ import annotations

from typing import Any, Callable

from .base import ConnectorStatus, Tier


class OpireConnector:
    id = "opire"
    display_name = "Opire"
    tier = Tier.A
    status = ConnectorStatus.LIVE
    official_docs_url = "https://docs.opire.dev"

    def __init__(
        self,
        fetch_fn: Callable[[], list[dict[str, Any]]] | None = None,
        *,
        enrich_issues: bool = False,
    ) -> None:
        self._fetch_fn = fetch_fn
        self._enrich_issues = enrich_issues

    def fetch_raw(self) -> list[dict[str, Any]]:
        if self._fetch_fn is not None:
            return list(self._fetch_fn())
        from swarm.opire_farm import fetch_opire_rewards

        return list(fetch_opire_rewards())

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        from swarm.opire_farm import score_reward
        from swarm.opire_issue_intel import fetch_issue_from_url

        intel = None
        if self._enrich_issues:
            url = str(raw.get("url") or "")
            if url:
                intel = fetch_issue_from_url(url, timeout=12.0)

        scored = score_reward(raw, issue_intel=intel)
        native = str(scored.get("id") or raw.get("id") or "")
        if not native:
            return None
        return {
            **scored,
            "id": f"opire:{native}",
            "native_id": native,
            "platform": "opire",
            "tier": Tier.A.value,
            "connector_id": self.id,
            "official_flow": "/try → PR /claim → merge → Opire payout",
        }
