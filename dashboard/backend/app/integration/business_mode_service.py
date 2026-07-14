"""Business Sandbox Mode — Incubator (Sandbox) vs Gewerbe-ready Live."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_CONFIRM_PHRASE = "ACTIVATE BUSINESS"

_DEFAULT_MODE: dict[str, Any] = {
    "system_mode": "sandbox",
    "label_sandbox": "Искатель · аналитика рынка",
    "label_live": "Бизнес · Gewerbe / Finanzamt",
    "activated_at": None,
    "activated_by": None,
    "note": (
        "Sandbox: только Potential Revenue — без Rechnungen, DATEV и налоговых событий. "
        "Live: после Gewerbeanmeldung — инвойсы и экспорт для Steuerberater."
    ),
}


class BusinessModeService:
    """system_mode: sandbox (default) | live — gates all official financial ops."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _path(self) -> Path:
        return self._memory / "business_mode.json"

    def load(self) -> dict[str, Any]:
        path = self._path()
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(_DEFAULT_MODE, ensure_ascii=False, indent=2), encoding="utf-8")
            return dict(_DEFAULT_MODE)
        try:
            merged = dict(_DEFAULT_MODE)
            merged.update(json.loads(path.read_text(encoding="utf-8")))
            mode = str(merged.get("system_mode") or "sandbox").lower()
            merged["system_mode"] = "live" if mode == "live" else "sandbox"
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT_MODE)

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def is_sandbox(self) -> bool:
        return self.load()["system_mode"] != "live"

    def is_live(self) -> bool:
        return self.load()["system_mode"] == "live"

    def financial_docs_enabled(self) -> bool:
        return self.is_live()

    def require_live(self) -> None:
        if self.is_sandbox():
            raise ValueError("sandbox_mode_financial_docs_disabled")

    def status(self) -> dict[str, Any]:
        cfg = self.load()
        sandbox = self.is_sandbox()
        return {
            "system_mode": cfg["system_mode"],
            "mode_label": cfg["label_sandbox"] if sandbox else cfg["label_live"],
            "financial_docs_enabled": not sandbox,
            "invoices_enabled": not sandbox,
            "datev_export_enabled": not sandbox,
            "tax_events_enabled": not sandbox,
            "activated_at": cfg.get("activated_at"),
            "note": cfg.get("note"),
            "confirm_phrase_required": _CONFIRM_PHRASE,
        }

    def activate_business(
        self,
        *,
        confirmed: bool,
        phrase: str,
        owner_name: str = "CEO",
    ) -> dict[str, Any]:
        if not confirmed:
            raise ValueError("confirmation_required")
        if (phrase or "").strip().upper() != _CONFIRM_PHRASE:
            raise ValueError("invalid_confirm_phrase")
        cfg = self.load()
        if cfg["system_mode"] == "live":
            return self.status()
        cfg["system_mode"] = "live"
        cfg["activated_at"] = datetime.now(timezone.utc).isoformat()
        cfg["activated_by"] = owner_name
        self.save(cfg)
        return self.status()

    def compute_potential_revenue(self, opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        """Projected earnings from leads — NOT realized profit (Sandbox display)."""
        pipeline = 0.0
        hunter = 0.0
        micro = 0.0
        dust = 0.0
        leads = 0
        high_score = 0

        for row in opportunities:
            if row.get("source_id") != "asset_scan":
                continue
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if row.get("status") in ("won", "lost"):
                continue
            leads += 1
            pipeline += float(row.get("potential_value_eur") or 0)
            hunter += float(meta.get("hunter_value_eur") or 0)
            micro += float(meta.get("potential_micro_revenue_eur") or meta.get("junk_micro_revenue_eur") or 0)
            dust += float(meta.get("digital_dust_value_eur") or 0)
            if int(meta.get("profit_score") or row.get("score") or 0) >= 45:
                high_score += 1

        total = round(pipeline + hunter + micro + dust, 2)
        return {
            "potential_revenue_eur": total,
            "pipeline_potential_eur": round(pipeline, 2),
            "hunter_potential_eur": round(hunter, 2),
            "micro_potential_eur": round(micro, 2),
            "dust_potential_eur": round(dust, 2),
            "active_leads": leads,
            "high_score_leads": high_score,
            "revenue_quality": "projected",
            "disclaimer": (
                "Potential Revenue — оценка по лидам и scoring. "
                "Не является реальным доходом до Live Mode и оплаты клиента."
            ),
        }

    def realized_revenue(self, opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        won = [r for r in opportunities if r.get("status") == "won"]
        gross = round(sum(float(r.get("revenue_eur") or 0) for r in won), 2)
        return {
            "realized_revenue_eur": gross,
            "won_assets": len(won),
            "revenue_quality": "realized" if self.is_live() else "sandbox_blocked",
        }
