"""Payout notifier — UI alerts when exchange balance hits withdraw threshold."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ENV_THRESHOLD_USD = "FARM_PAYOUT_THRESHOLD_USD"
DEFAULT_THRESHOLD_USD = 10.0


class PayoutNotifier:
    """Alerts CEO to withdraw manually from Scale/Toloka to Stripe."""

    def __init__(
        self,
        memory_dir: Path,
        *,
        env_getter: Callable[[str], str] | None = None,
        threshold_usd: float | None = None,
    ) -> None:
        self._memory = Path(memory_dir)
        self._env = env_getter or (lambda k: os.getenv(k, "").strip())
        self._threshold = threshold_usd if threshold_usd is not None else self._read_threshold()

    def _read_threshold(self) -> float:
        raw = self._env(ENV_THRESHOLD_USD) or str(DEFAULT_THRESHOLD_USD)
        try:
            return max(1.0, float(raw))
        except ValueError:
            return DEFAULT_THRESHOLD_USD

    def _alerts_path(self) -> Path:
        return self._memory / "micro_farm_payout_alerts.json"

    def _load_alerts(self) -> list[dict[str, Any]]:
        path = self._alerts_path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return list(data.get("alerts") or [])
        except (json.JSONDecodeError, OSError):
            return []

    def _save_alerts(self, alerts: list[dict[str, Any]]) -> None:
        path = self._alerts_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"alerts": alerts[-50:]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def evaluate(self, monitor_snapshot: dict[str, Any]) -> dict[str, Any]:
        """Check balances vs threshold — create UI alerts, no auto-payout."""
        threshold = self._threshold
        new_alerts: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []

        for platform_key in ("scale", "toloka"):
            row = monitor_snapshot.get(platform_key) or {}
            balance = row.get("balance_usd")
            if balance is None:
                continue
            bal = float(balance)
            if bal >= threshold:
                alert = {
                    "id": f"{platform_key}-{int(bal * 100)}",
                    "platform": platform_key,
                    "balance_usd": round(bal, 2),
                    "threshold_usd": threshold,
                    "at": datetime.now(timezone.utc).isoformat(),
                    "title": f"Пора выводить с {platform_key.upper()}",
                    "message": (
                        f"Баланс ${bal:.2f} ≥ ${threshold:.2f}. "
                        f"Зайди на биржу → Withdraw → Stripe (вручную)."
                    ),
                    "severity": "success",
                    "action": "manual_withdraw",
                }
                new_alerts.append(alert)
                pending.append(alert)

        existing = self._load_alerts()
        seen = {a.get("id") for a in existing}
        merged = existing + [a for a in new_alerts if a.get("id") not in seen]
        if new_alerts:
            self._save_alerts(merged)

        return {
            "threshold_usd": threshold,
            "pending_alerts": pending,
            "recent_alerts": merged[-10:],
            "has_withdraw_ready": bool(pending),
            "stripe_note": "Stripe — конечная точка после ручного Withdraw на бирже",
            "auto_payout": False,
        }

    def snapshot(self, monitor_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        base = {
            "threshold_usd": self._threshold,
            "recent_alerts": self._load_alerts()[-10:],
            "auto_payout": False,
        }
        if monitor_snapshot:
            base.update(self.evaluate(monitor_snapshot))
        return base
