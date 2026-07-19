"""Public pricing display — editable JSON, no hardcoded tariffs in code."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.integration.public_truth_catalog import build_truth_pricing_display

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


class PricingDisplayService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._config_path = self._memory / "pricing_display.json"
        self._analytics_path = self._memory / "pricing_analytics.jsonl"

    def get_display(self, market_code: str | None = None) -> dict:
        # Always resolve from market_registry / commerce so /services matches /order.
        code = (market_code or "DE").strip() or "DE"
        return build_truth_pricing_display(market_code=code)

    @staticmethod
    def _is_mission1_public_truth(data: dict) -> bool:
        """Mission 1: only mission1-truth catalog or CEO-published compatible JSON."""
        version = str(data.get("version") or "")
        if version.startswith("mission1-truth"):
            return True
        subs = data.get("subscriptions") or []
        for s in subs:
            if s.get("id") in ("basic", "pro", "business", "enterprise") and s.get("available"):
                return False
            if s.get("price_eur_month") in (49, 99, 199):
                return False
        for cat in data.get("service_categories") or []:
            for item in cat.get("items") or []:
                label = str(item.get("price_label") or "")
                if "450" in label or "1 800" in label or "1 800" in label.replace(" ", ""):
                    return False
        return bool(data.get("service_categories") or data.get("subscriptions"))

    def log_event(self, *, event: str, tier_id: str | None, page: str, meta: dict | None = None) -> None:
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "tier_id": tier_id,
            "page": page,
            "meta": meta or {},
        }
        self._memory.mkdir(parents=True, exist_ok=True)
        with self._analytics_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
