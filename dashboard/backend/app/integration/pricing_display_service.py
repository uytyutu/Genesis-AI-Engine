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

    def get_display(self) -> dict:
        if not self._config_path.is_file():
            return build_truth_pricing_display()
        try:
            data = json.loads(self._config_path.read_text(encoding="utf-8"))
            if not (data.get("service_categories") or data.get("subscriptions")):
                return build_truth_pricing_display()
            return data
        except (json.JSONDecodeError, OSError):
            return build_truth_pricing_display()

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
