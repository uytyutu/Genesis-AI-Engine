"""Growth Center — business growth metrics (not production metrics)."""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_ZERO = {
    "users_growth_percent": 0.0,
    "subscriptions_growth_percent": 0.0,
    "revenue_growth_percent": 0.0,
    "conversion_growth_percent": 0.0,
    "cac_change_percent": 0.0,
    "retention_growth_percent": 0.0,
    "users_total": 0,
    "subscriptions_total": 0,
    "conversion_percent": 0.0,
    "cac_eur": 0.0,
    "retention_percent": 0.0,
}

_DEMO = {
    "users_growth_percent": 12.0,
    "subscriptions_growth_percent": 7.0,
    "revenue_growth_percent": 18.0,
    "conversion_growth_percent": 2.0,
    "cac_change_percent": -9.0,
    "retention_growth_percent": 4.5,
    "users_total": 842,
    "subscriptions_total": 391,
    "conversion_percent": 14.8,
    "cac_eur": 12.40,
    "retention_percent": 68.0,
}


class GrowthService:
    """Growth metrics from analytics / Payment Hub — business autonomy is not guaranteed by AI."""

    def __init__(self, memory_dir: Path | None = None, finance: object | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._finance = finance

    def _demo(self) -> bool:
        if self._finance is None:
            return False
        return bool(getattr(self._finance, "is_demo_mode", lambda: False)())

    def _load(self) -> dict:
        path = self._memory / "growth_snapshot.json"
        if not path.exists():
            return dict(_ZERO)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {**_ZERO, **data}
        except (json.JSONDecodeError, OSError):
            return dict(_ZERO)

    def center(self) -> dict:
        snap = _DEMO if self._demo() else self._load()
        return {
            "demo_mode": self._demo(),
            "data_source_note": (
                "Демо-режим: показатели роста для оценки интерфейса."
                if self._demo()
                else "Рост появится после первых пользователей, оплат и аналитики. "
                "ИИ ускоряет производство — рост бизнеса зависит от ценности продукта."
            ),
            "users_total": int(snap["users_total"]),
            "users_growth_percent": float(snap["users_growth_percent"]),
            "subscriptions_total": int(snap["subscriptions_total"]),
            "subscriptions_growth_percent": float(snap["subscriptions_growth_percent"]),
            "revenue_growth_percent": float(snap["revenue_growth_percent"]),
            "conversion_percent": float(snap["conversion_percent"]),
            "conversion_growth_percent": float(snap["conversion_growth_percent"]),
            "cac_eur": float(snap["cac_eur"]),
            "cac_change_percent": float(snap["cac_change_percent"]),
            "retention_percent": float(snap["retention_percent"]),
            "retention_growth_percent": float(snap["retention_growth_percent"]),
        }
