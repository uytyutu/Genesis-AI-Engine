"""Provider router — budget check then disabled providers (no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.cinematic_media.budget import can_start_media_job
from app.integration.cinematic_media.providers.base import MediaJobRequest, MediaJobResult
from app.integration.cinematic_media.providers.kie import KieMediaProvider
from app.integration.cinematic_media.providers.kling import KlingMediaProvider


class MediaProviderRouter:
    def __init__(self) -> None:
        self._providers = {
            "kling": KlingMediaProvider(),
            "kie": KieMediaProvider(),
        }

    def board(self) -> dict[str, Any]:
        return {
            "providers": {pid: p.status() for pid, p in self._providers.items()},
            "live_generation": False,
            "rule": "No auto-spend without paid media budget + enabled provider",
        }

    def submit(
        self,
        order: dict[str, Any],
        *,
        provider_id: str,
        capability: str,
        prompt: str = "",
        estimated_cost_eur: float | None = None,
        memory_dir: Path | None = None,
    ) -> dict[str, Any]:
        del memory_dir  # charge applied only by future live path after CEO enable
        gate = can_start_media_job(order, estimated_cost_eur=estimated_cost_eur)
        if not gate.get("allow"):
            return {"ok": False, "gate": gate, "network_called": False}

        provider = self._providers.get(provider_id)
        if provider is None:
            return {"ok": False, "error": "unknown_provider", "network_called": False}
        if not provider.enabled():
            result = provider.submit(
                MediaJobRequest(
                    order_id=str(order.get("order_id") or ""),
                    capability=capability,
                    prompt=prompt,
                    estimated_cost_eur=estimated_cost_eur,
                )
            )
            return {
                "ok": False,
                "error": "provider_disabled",
                "result": result.as_dict(),
                "network_called": False,
                "provider_status": provider.status(),
            }
        # Live path reserved for later CEO approval — still blocked here for safety
        return {
            "ok": False,
            "error": "live_path_not_authorized",
            "network_called": False,
            "detail": "Even if enabled in config, live calls require a separate CEO release",
        }
