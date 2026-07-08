"""Finance Center — display layer for payment-provider data (Genesis never holds funds)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.integration.genesis_brain.public_brand import BRAND_NAME

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_WALLET_CATALOG = [
    {"id": "bank", "label": "Банковский счёт", "icon": "🏦"},
    {"id": "stripe", "label": "Stripe", "icon": "💳"},
    {"id": "paypal", "label": "PayPal", "icon": "🟦"},
    {"id": "bitcoin", "label": "Bitcoin", "icon": "₿"},
    {"id": "usdt", "label": "USDT", "icon": "💵"},
]

_DEMO_WALLETS = [
    {"id": "bank", "label": "Банковский счёт", "icon": "🏦", "connected": True, "balance_label": "5 230 €"},
    {"id": "stripe", "label": "Stripe", "icon": "💳", "connected": True, "balance_label": "2 140 €"},
    {"id": "paypal", "label": "PayPal", "icon": "🟦", "connected": True, "balance_label": "520 €"},
    {"id": "bitcoin", "label": "Bitcoin", "icon": "₿", "connected": True, "balance_label": "0.0134 BTC"},
    {"id": "usdt", "label": "USDT", "icon": "💵", "connected": True, "balance_label": "740 USDT"},
]

_DEMO_PAYOUTS = [
    {"at": "2026-07-05", "amount_eur": 980.0, "provider": "Stripe", "status": "completed", "status_label": "Завершено"},
    {"at": "2026-06-28", "amount_eur": 230.0, "provider": "Bitcoin", "status": "confirmed", "status_label": "Подтверждено"},
    {"at": "2026-06-20", "amount_eur": 75.0, "provider": "PayPal", "status": "completed", "status_label": "Получено"},
]

_DEMO_SPARKLINE = [142.0, 198.0, 165.0, 210.0, 284.0, 312.0, 327.4]

_DEMO_FINANCE = {
    "platform_balance_eur": 2350.0,
    "available_for_withdrawal_eur": 1980.0,
    "pending_payouts_eur": 370.0,
    "revenue_today_eur": 49.0,
    "revenue_month_eur": 2847.0,
    "gross_revenue_eur": 2847.0,
    "expenses_eur": 120.0,
    "net_profit_eur": 2727.0,
    "products_sold": 12,
    "clients": 8,
    "active_subscriptions": 3,
}

_ZERO_SNAPSHOT = {
    "source": "none",
    "currency": "EUR",
    "platform_balance_eur": 0.0,
    "revenue_today_eur": 0.0,
    "revenue_month_eur": 0.0,
    "gross_revenue_eur": 0.0,
    "expenses_eur": 0.0,
    "net_profit_eur": 0.0,
    "available_for_withdrawal_eur": 0.0,
    "pending_payouts_eur": 0.0,
    "products_sold": 0,
    "clients": 0,
    "active_subscriptions": 0,
    "ai_expenses_eur": 0.0,
    "server_expenses_eur": 0.0,
}


class FinanceService:
    """Reads finance display cache synced from Payment Hub — not an internal wallet."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _load_config(self) -> dict:
        path = self._memory / "finance_config.json"
        if not path.exists():
            return {"payment_provider": None, "payment_provider_label": "Не подключено", "demo_mode": False}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if "demo_mode" not in data:
                data["demo_mode"] = False
            return data
        except (json.JSONDecodeError, OSError):
            return {"payment_provider": None, "payment_provider_label": "Не подключено", "demo_mode": False}

    def is_demo_mode(self) -> bool:
        return bool(self._load_config().get("demo_mode"))

    def set_demo_mode(self, enabled: bool) -> None:
        config = self._load_config()
        config["demo_mode"] = enabled
        path = self._memory / "finance_config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_snapshot(self) -> dict:
        path = self._memory / "finance_snapshot.json"
        if not path.exists():
            return dict(_ZERO_SNAPSHOT)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            merged = dict(_ZERO_SNAPSHOT)
            merged.update({k: data.get(k, v) for k, v in _ZERO_SNAPSHOT.items()})
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(_ZERO_SNAPSHOT)

    def _recent_transactions(self, limit: int = 8) -> list[dict[str, str | float]]:
        path = self._memory / "finance_transactions.jsonl"
        if not path.exists():
            return []
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        rows.sort(key=lambda r: str(r.get("at", "")), reverse=True)
        result = []
        for row in rows[:limit]:
            result.append(
                {
                    "at": str(row.get("at", "")),
                    "amount_eur": float(row.get("amount_eur", 0)),
                    "label": str(row.get("label", "Поступление")),
                    "category": str(row.get("category", "sale")),
                }
            )
        return result

    def _wallets(self, config: dict, connected: bool, demo: bool) -> list[dict]:
        if demo:
            return list(_DEMO_WALLETS)
        wallet_cfg = config.get("wallets") or {}
        provider = str(config.get("payment_provider") or "")
        snap = self._load_snapshot() if connected else {}
        balance = format(float(snap.get("platform_balance_eur", 0)), ",.2f").replace(",", " ") + " €"
        rows = []
        for w in _WALLET_CATALOG:
            entry = wallet_cfg.get(w["id"], {})
            is_connected = bool(entry.get("connected")) if connected else False
            if connected and w["id"] == provider:
                is_connected = True
            bal = str(entry.get("balance_label", "")) if entry.get("balance_label") else None
            if is_connected and not bal and provider == w["id"]:
                bal = balance
            rows.append(
                {
                    "id": w["id"],
                    "label": w["label"],
                    "icon": w["icon"],
                    "connected": is_connected,
                    "balance_label": bal if is_connected else None,
                }
            )
        return rows

    def _payout_history(self, limit: int = 10) -> list[dict]:
        path = self._memory / "finance_payouts.jsonl"
        if not path.exists():
            return []
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        rows.sort(key=lambda r: str(r.get("at", "")), reverse=True)
        result = []
        for row in rows[:limit]:
            result.append(
                {
                    "at": str(row.get("at", "")),
                    "amount_eur": float(row.get("amount_eur", 0)),
                    "provider": str(row.get("provider", "")),
                    "status": str(row.get("status", "pending")),
                    "status_label": str(row.get("status_label", "В обработке")),
                }
            )
        return result

    def _last_withdrawal(self, payouts: list[dict]) -> dict | None:
        if not payouts:
            return None
        p = payouts[0]
        return {
            "at": p["at"],
            "amount_eur": p["amount_eur"],
            "provider": p["provider"],
            "status_label": p["status_label"],
        }

    def _revenue_sparkline(self, connected: bool, demo: bool) -> list[float]:
        if demo:
            return list(_DEMO_SPARKLINE)
        if not connected:
            return []
        path = self._memory / "finance_sparkline.json"
        if not path.exists():
            snap = self._load_snapshot()
            today = float(snap.get("revenue_today_eur", 0))
            return [0.0] * 6 + [today] if today > 0 else []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [float(x) for x in data.get("values", [])]
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return []

    def finance_center(self, owner_name: str, greeting: str) -> dict:
        config = self._load_config()
        snap = self._load_snapshot()
        provider = config.get("payment_provider")
        connected = bool(provider)
        demo = bool(config.get("demo_mode"))
        last_sync = str(config.get("last_sync_at", "") or "")

        payouts = self._payout_history() if connected else []
        if demo:
            payouts = list(_DEMO_PAYOUTS)

        wallets = self._wallets(config, connected, demo)
        sparkline = self._revenue_sparkline(connected, demo)
        last_wd = self._last_withdrawal(payouts)

        base_note = (
            "Данные синхронизированы с платёжным провайдером. "
            f"{BRAND_NAME} не хранит средства — только отображает информацию."
            if connected
            else "Платёжная система не подключена. Суммы появятся автоматически "
            "после подключения Payment Hub."
        )
        if demo:
            base_note = (
                "Демо-режим: цифры имитируют подключённые кошельки для оценки интерфейса. "
                f"{BRAND_NAME} не хранит и не переводит средства — только отображает данные провайдеров."
            )

        result = {
            "owner_name": owner_name,
            "greeting": greeting,
            "demo_mode": demo,
            "payment_provider": provider,
            "payment_provider_label": str(
                config.get("payment_provider_label", "Не подключено")
            ),
            "payment_connected": connected and not demo,
            "last_sync_at": last_sync or None,
            "data_source_note": base_note,
            "currency": snap["currency"],
            "platform_balance_eur": float(snap["platform_balance_eur"]),
            "revenue_today_eur": float(snap["revenue_today_eur"]),
            "revenue_month_eur": float(snap["revenue_month_eur"]),
            "gross_revenue_eur": float(snap["gross_revenue_eur"]),
            "expenses_eur": float(snap["expenses_eur"]),
            "net_profit_eur": float(snap["net_profit_eur"]),
            "available_for_withdrawal_eur": float(snap["available_for_withdrawal_eur"]),
            "pending_payouts_eur": float(snap["pending_payouts_eur"]),
            "products_sold": int(snap["products_sold"]),
            "clients": int(snap["clients"]),
            "active_subscriptions": int(snap["active_subscriptions"]),
            "ai_expenses_eur": float(snap.get("ai_expenses_eur", 0.0)),
            "server_expenses_eur": float(snap.get("server_expenses_eur", 0.0)),
            "recent_transactions": self._recent_transactions(),
            "withdrawal_enabled": connected and float(snap["available_for_withdrawal_eur"]) > 0,
            "wallets": wallets,
            "payout_history": payouts,
            "last_withdrawal": last_wd,
            "revenue_sparkline": sparkline,
            "pending_payments": self._pending_payments(),
        }

        if demo:
            for key, val in _DEMO_FINANCE.items():
                result[key] = val
            result["payment_provider_label"] = "Demo (имитация)"
            result["withdrawal_enabled"] = True
            result["recent_transactions"] = [
                {"at": "2026-07-03T03:11:00Z", "amount_eur": 49.0, "label": "Landing стоматология", "category": "sale"},
                {"at": "2026-07-02T18:00:00Z", "amount_eur": 50.0, "label": "Landing Page", "category": "sale"},
            ]

        return result

    def _save_snapshot(self, snap: dict) -> None:
        path = self._memory / "finance_snapshot.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_transaction(self, row: dict) -> None:
        path = self._memory / "finance_transactions.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _touch_milestone(self, key: str, value: bool | int | str = True) -> None:
        path = self._memory / "owner_milestones.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        data[key] = value
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _pending_payments_path(self) -> Path:
        return self._memory / "finance_pending_payments.jsonl"

    def _pending_payments(self) -> list[dict]:
        path = self._pending_payments_path()
        if not path.exists():
            return []
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("status") == "pending":
                rows.append(
                    {
                        "payment_id": str(row.get("payment_id", "")),
                        "amount_eur": float(row.get("amount_eur", 0)),
                        "label": str(row.get("label", "Платёж")),
                        "provider": str(row.get("provider", "")),
                        "sender": str(row.get("sender", "Не указан")),
                        "received_at": str(row.get("received_at", "")),
                    }
                )
        rows.sort(key=lambda r: str(r.get("received_at", "")), reverse=True)
        return rows

    def _save_pending_rows(self, rows: list[dict]) -> None:
        path = self._pending_payments_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )

    def _load_pending_rows(self) -> list[dict]:
        path = self._pending_payments_path()
        if not path.exists():
            return []
        rows: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def record_provider_payment(
        self,
        amount_eur: float,
        label: str,
        *,
        provider: str = "stripe",
        product_id: str | None = None,
        sender: str | None = None,
    ) -> dict:
        """Queue payment for owner confirmation — never auto-credit the UI balance."""
        config = self._load_config()
        if not config.get("payment_provider"):
            raise ValueError("payment_not_connected")

        amount = round(float(amount_eur), 2)
        if amount <= 0:
            raise ValueError("invalid_amount")

        now = datetime.now(timezone.utc).isoformat()
        payment_id = uuid.uuid4().hex[:12]
        pending_row = {
            "payment_id": payment_id,
            "amount_eur": amount,
            "label": label,
            "provider": provider,
            "product_id": product_id,
            "sender": sender or "Не указан",
            "received_at": now,
            "status": "pending",
        }
        rows = self._load_pending_rows()
        rows.append(pending_row)
        self._save_pending_rows(rows)
        config["last_sync_at"] = now
        path = self._memory / "finance_config.json"
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": True,
            "amount_eur": amount,
            "recorded_at": now,
            "provider": provider,
            "pending": True,
            "payment_id": payment_id,
        }

    def confirm_provider_payment(self, payment_id: str) -> dict:
        rows = self._load_pending_rows()
        match = next((r for r in rows if r.get("payment_id") == payment_id), None)
        if match is None:
            raise ValueError("payment_not_found")
        if match.get("status") != "pending":
            raise ValueError("payment_already_confirmed")

        amount = round(float(match.get("amount_eur", 0)), 2)
        provider = str(match.get("provider", "stripe"))
        label = str(match.get("label", "Поступление"))
        product_id = match.get("product_id")
        now = datetime.now(timezone.utc).isoformat()

        snap = self._load_snapshot()
        snap["source"] = provider
        snap["revenue_today_eur"] = round(float(snap.get("revenue_today_eur", 0)) + amount, 2)
        snap["revenue_month_eur"] = round(float(snap.get("revenue_month_eur", 0)) + amount, 2)
        snap["gross_revenue_eur"] = round(float(snap.get("gross_revenue_eur", 0)) + amount, 2)
        snap["net_profit_eur"] = round(float(snap.get("net_profit_eur", 0)) + amount, 2)
        snap["platform_balance_eur"] = round(float(snap.get("platform_balance_eur", 0)) + amount, 2)
        snap["available_for_withdrawal_eur"] = round(
            float(snap.get("available_for_withdrawal_eur", 0)) + amount, 2
        )
        snap["products_sold"] = int(snap.get("products_sold", 0)) + 1
        self._save_snapshot(snap)

        self._append_transaction(
            {
                "at": now,
                "amount_eur": amount,
                "label": label,
                "category": "sale",
                "provider": provider,
                "product_id": product_id,
                "payment_id": payment_id,
            }
        )
        self._touch_milestone("first_payment", True)

        for row in rows:
            if row.get("payment_id") == payment_id:
                row["status"] = "confirmed"
                row["confirmed_at"] = now
        self._save_pending_rows(rows)

        config = self._load_config()
        config["last_sync_at"] = now
        path = self._memory / "finance_config.json"
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": True,
            "amount_eur": amount,
            "recorded_at": now,
            "provider": provider,
            "pending": False,
            "payment_id": payment_id,
        }

    def credit_order_payment(
        self,
        amount_eur: float,
        label: str,
        *,
        provider: str = "stripe",
        order_id: str | None = None,
        sender: str | None = None,
        external_id: str | None = None,
    ) -> dict:
        """Auto-credit verified order payment (webhook) — no owner confirm step."""
        amount = round(float(amount_eur), 2)
        if amount <= 0:
            raise ValueError("invalid_amount")

        now = datetime.now(timezone.utc).isoformat()
        payment_id = external_id or uuid.uuid4().hex[:12]

        snap = self._load_snapshot()
        snap["source"] = provider
        snap["revenue_today_eur"] = round(float(snap.get("revenue_today_eur", 0)) + amount, 2)
        snap["revenue_month_eur"] = round(float(snap.get("revenue_month_eur", 0)) + amount, 2)
        snap["gross_revenue_eur"] = round(float(snap.get("gross_revenue_eur", 0)) + amount, 2)
        snap["net_profit_eur"] = round(float(snap.get("net_profit_eur", 0)) + amount, 2)
        snap["platform_balance_eur"] = round(float(snap.get("platform_balance_eur", 0)) + amount, 2)
        snap["available_for_withdrawal_eur"] = round(
            float(snap.get("available_for_withdrawal_eur", 0)) + amount, 2
        )
        snap["products_sold"] = int(snap.get("products_sold", 0)) + 1
        self._save_snapshot(snap)

        self._append_transaction(
            {
                "at": now,
                "amount_eur": amount,
                "label": label,
                "category": "sale",
                "provider": provider,
                "order_id": order_id,
                "payment_id": payment_id,
            }
        )
        self._touch_milestone("first_payment", True)

        config = self._load_config()
        if not config.get("payment_provider"):
            config["payment_provider"] = provider
            config["payment_provider_label"] = "Stripe" if provider == "stripe" else "Sandbox"
        config["last_sync_at"] = now
        path = self._memory / "finance_config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "ok": True,
            "amount_eur": amount,
            "recorded_at": now,
            "provider": provider,
            "pending": False,
            "payment_id": payment_id,
        }

    def revenue_summary(self) -> dict[str, float]:
        snap = self._load_snapshot()
        return {
            "revenue_today_eur": float(snap["revenue_today_eur"]),
            "revenue_month_eur": float(snap["revenue_month_eur"]),
        }
