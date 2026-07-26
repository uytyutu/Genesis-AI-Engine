"""Official TikTok Developer API adapter — Stage 1: interface only, no publish."""

from __future__ import annotations

from typing import Any

from modules.tiktok_horizon.adapters.base import AdapterResult, ExternalAdapter
from modules.tiktok_horizon.models import TrendObservation


class TikTokOfficialAdapter(ExternalAdapter):
    """Placeholder for OAuth + Content Posting / Research endpoints.

    Stage 1 does not call TikTok. When credentials exist later, implement
    fetch_trend_signals / publish_video using only official APIs.
    """

    provider_id = "tiktok_official"

    def __init__(self, *, connected: bool = False) -> None:
        self._connected = connected

    def health(self) -> AdapterResult:
        return AdapterResult(
            ok=True,
            provider=self.provider_id,
            data={"connected": self._connected, "publish_enabled": False},
            stage1_disabled=True,
            meta={"note": "Stage 1: account connect + publish not wired."},
        )

    def fetch_trend_signals(self) -> AdapterResult:
        """Return public-pattern signals when official research endpoints are wired."""
        if not self._connected:
            return AdapterResult(
                ok=True,
                provider=self.provider_id,
                data=[],
                stage1_disabled=True,
                error="tiktok_not_connected",
                meta={"note": "No live scrape. Ingest observations or connect official API later."},
            )
        return AdapterResult(
            ok=True,
            provider=self.provider_id,
            data=[],
            stage1_disabled=True,
            meta={"note": "Connected stub — no endpoint calls in Stage 1."},
        )

    def publish_video(self, _payload: dict[str, Any]) -> AdapterResult:
        return AdapterResult(
            ok=False,
            provider=self.provider_id,
            stage1_disabled=True,
            error="publish_disabled_stage1",
        )

    @staticmethod
    def observation_from_dict(raw: dict[str, Any]) -> TrendObservation:
        tokens = raw.get("topic_tokens") or []
        if isinstance(tokens, str):
            tokens = [t.strip() for t in tokens.replace(",", " ").split() if t.strip()]
        tags = raw.get("hashtag_pattern") or []
        if isinstance(tags, str):
            tags = [t.strip().lstrip("#") for t in tags.replace(",", " ").split() if t.strip()]
        return TrendObservation(
            signal_id=str(raw.get("signal_id") or ""),
            observed_at=str(raw.get("observed_at") or ""),
            topic_tokens=[str(t).lower()[:40] for t in tokens][:12],
            duration_sec=float(raw.get("duration_sec") or 0),
            hook_style=str(raw.get("hook_style") or "unknown")[:60],
            editing_style=str(raw.get("editing_style") or "unknown")[:60],
            caption_style=str(raw.get("caption_style") or "unknown")[:60],
            hashtag_pattern=[str(t)[:40] for t in tags][:10],
            engagement_proxy=float(raw.get("engagement_proxy") or 0),
            language=str(raw.get("language") or "de")[:8],
            source=str(raw.get("source") or "manual_ingest")[:40],
        )
