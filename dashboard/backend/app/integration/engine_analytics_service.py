"""Engine live analytics — developer-oriented real-time signals."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.digital_dust_service import DigitalDustService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


class EngineAnalyticsService:
    """Real-time harvest/hunter/dust metrics for developer dashboard."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _events_last_minutes(self, minutes: int = 60) -> list[dict[str, Any]]:
        path = self._memory / "engine_harvest_events.jsonl"
        if not path.is_file():
            return []
        cutoff = datetime.now(timezone.utc).timestamp() - minutes * 60
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            at = ev.get("at") or ""
            try:
                ts = datetime.fromisoformat(at.replace("Z", "+00:00")).timestamp()
            except ValueError:
                ts = 0
            if ts >= cutoff:
                rows.append(ev)
        return rows

    def market_signals(self, opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        """Task-focused market view — outreach vs dust vs junk micro."""
        outreach = 0
        dust = 0
        junk = 0
        by_country: dict[str, int] = {}
        for row in opportunities:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            cc = str(meta.get("country_code") or "GLOBAL")
            by_country[cc] = by_country.get(cc, 0) + 1
            if meta.get("recoverable_assets_count"):
                dust += int(meta.get("recoverable_assets_count") or 0)
            if meta.get("hunter_scenarios"):
                outreach += int((meta.get("hunter_scenarios") or {}).get("outreach") or 0)
            if meta.get("processing_lane") == "junk_archive":
                junk += 1
        top_countries = sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:6]
        return {
            "outreach_leads": outreach,
            "recoverable_assets": dust,
            "junk_archive_targets": junk,
            "top_countries": [{"code": c, "leads": n} for c, n in top_countries],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def live_dashboard(
        self,
        *,
        harvest: dict[str, Any],
        hunter: dict[str, Any],
        smart_gate: dict[str, Any],
        global_spider: dict[str, Any],
        digital_dust: dict[str, Any],
        opportunities: list[dict[str, Any]],
    ) -> dict[str, Any]:
        events = self._events_last_minutes(60)
        event_types: dict[str, int] = {}
        for ev in events:
            t = str(ev.get("type") or "other")
            event_types[t] = event_types.get(t, 0) + 1

        return {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "events_last_hour": len(events),
            "event_breakdown": event_types,
            "harvest_balance_eur": harvest.get("harvest_balance_eur", 0),
            "hunter_value_eur": harvest.get("hunter_value_eur", 0),
            "pattern_hits_total": harvest.get("pattern_hits_total", 0),
            "hunter": hunter,
            "smart_gate": smart_gate,
            "global_spider": global_spider,
            "digital_dust": digital_dust,
            "market": self.market_signals(opportunities),
            "logic_chain": DigitalDustService.logic_chain(),
            "developer_note": (
                "Режим разработчика: зелёный = авто безопасно · жёлтый = CEO Approve · "
                "красный = заблокировано Security Law"
            ),
        }
