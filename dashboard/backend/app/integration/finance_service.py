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
    "paid_by_client_eur": 0.0,
    "pending_settlement_eur": 0.0,
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

    def _settlements(self):
        from app.integration.payment_settlement_service import PaymentSettlementService

        return PaymentSettlementService(self._memory)

    def _sync_settlement_snapshot(self, snap: dict | None = None) -> dict:
        snap = dict(snap if snap is not None else self._load_snapshot())
        return self._settlements().apply_to_snapshot(snap)

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

    def _load_tax_settings(self) -> dict:
        path = self._memory / "engine_tax_config.json"
        defaults = {
            "vat_rate_percent": 19.0,
            "stripe_fee_percent": 1.4,
            "stripe_fee_fixed_eur": 0.25,
        }
        if not path.is_file():
            return dict(defaults)
        try:
            merged = dict(defaults)
            merged.update(json.loads(path.read_text(encoding="utf-8")))
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(defaults)

    def _stripe_fee(self, gross: float, settings: dict) -> float:
        if gross <= 0:
            return 0.0
        pct = float(settings.get("stripe_fee_percent") or 0) / 100.0
        fixed = float(settings.get("stripe_fee_fixed_eur") or 0)
        return round(gross * pct + fixed, 2)

    def financial_view(
        self,
        *,
        business_mode=None,
        opportunities: list[dict] | None = None,
        demo: bool = False,
        connected: bool = False,
    ) -> dict:
        """Wallet-like display synced from payment providers — Genesis never holds funds."""
        snap = self._load_snapshot()
        config = self._load_config()
        settings = self._load_tax_settings()
        last_sync = str(config.get("last_sync_at", "") or "")

        custody_note = (
            "Деньги никогда не хранятся в Genesis. "
            "Клиент платит → Stripe/PayPal/банк → ваш личный счёт. "
            "Genesis только фиксирует: «счёт оплачен, средства поступили»."
        )
        money_route = "Клиент → платёжный шлюз → ваш банковский счёт"

        sandbox = business_mode.is_sandbox() if business_mode else False
        if sandbox:
            potential = (
                business_mode.compute_potential_revenue(opportunities or [])
                if business_mode
                else {"potential_revenue_eur": 0.0, "disclaimer": ""}
            )
            return {
                "system_mode": "sandbox",
                "funds_held_by_genesis_eur": 0.0,
                "money_never_stored": True,
                "money_route": money_route,
                "custody_note": custody_note,
                "gross_synced_eur": 0.0,
                "tax_reserve_eur": 0.0,
                "net_clean_eur": 0.0,
                "safe_to_withdraw_eur": 0.0,
                "safe_to_withdraw_status": "sandbox",
                "safe_to_withdraw_label": "Sandbox — только Potential Revenue",
                "pending_at_provider_eur": 0.0,
                "potential_revenue": potential,
                "potential_revenue_eur": float(potential.get("potential_revenue_eur") or 0),
                "reconcile_enabled": True,
                "withdraw_enabled": False,
                "last_reconcile_at": last_sync or None,
                "disclaimer": str(
                    potential.get("disclaimer")
                    or "В Sandbox нет реальных выплат — только оценка потенциала."
                ),
            }

        if demo:
            gross = float(_DEMO_FINANCE["gross_revenue_eur"])
            available = float(_DEMO_FINANCE["available_for_withdrawal_eur"])
            pending = float(_DEMO_FINANCE["pending_payouts_eur"])
        else:
            gross = float(snap.get("paid_by_client_eur") or snap.get("gross_revenue_eur") or 0)
            available = float(snap.get("available_for_withdrawal_eur") or 0)
            pending = float(snap.get("pending_settlement_eur") or snap.get("pending_payouts_eur") or 0)

        commission = self._stripe_fee(gross, settings)
        net_after_fees = round(max(0.0, gross - commission), 2)
        vat_rate = float(settings.get("vat_rate_percent") or 19) / 100.0
        tax_reserve = round(net_after_fees * vat_rate, 2)
        net_clean = round(net_after_fees - tax_reserve, 2)
        provider_available = round(max(0.0, available), 2)
        safe = round(max(0.0, min(provider_available, net_clean)), 2)

        if safe > 0:
            status = "green"
            label = "Доступно к выводу (settlement пройден)"
        elif gross > 0 and pending > 0:
            status = "amber"
            label = f"Оплачено клиентом — удержание Stripe DE (~{3} раб. дня)"
        elif gross > 0:
            status = "amber"
            label = "Резерв под налоги или ожидание выплаты"
        else:
            status = "amber"
            label = "Ожидание первой оплаты"

        can_withdraw = (connected or demo) and safe > 0
        paid_by_client = float(snap.get("paid_by_client_eur") or 0)
        pending_settlement = float(snap.get("pending_settlement_eur") or 0)
        return {
            "system_mode": "live",
            "funds_held_by_genesis_eur": 0.0,
            "money_never_stored": True,
            "money_route": money_route,
            "custody_note": custody_note,
            "gross_synced_eur": round(gross, 2),
            "paid_by_client_eur": round(paid_by_client, 2),
            "pending_settlement_eur": round(pending_settlement, 2),
            "available_for_withdrawal_eur": round(available, 2),
            "commission_eur": commission,
            "net_after_fees_eur": net_after_fees,
            "tax_reserve_eur": tax_reserve,
            "net_clean_eur": net_clean,
            "safe_to_withdraw_eur": safe,
            "safe_to_withdraw_status": status,
            "safe_to_withdraw_label": label,
            "pending_at_provider_eur": pending,
            "potential_revenue_eur": 0.0,
            "reconcile_enabled": connected or demo,
            "withdraw_enabled": can_withdraw,
            "last_reconcile_at": last_sync or None,
            "disclaimer": (
                "Цифровой сейф: учёт до копейки. Деньги на вашем банковском счёте — "
                "Genesis только синхронизирует и показывает Safe to Withdraw."
            ),
        }

    def reconcile(self, *, business_mode=None, opportunities: list[dict] | None = None) -> dict:
        config = self._load_config()
        now = datetime.now(timezone.utc).isoformat()
        config["last_sync_at"] = now
        path = self._memory / "finance_config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        connected = bool(config.get("payment_provider"))
        demo = bool(config.get("demo_mode"))
        snap = self._sync_settlement_snapshot()
        self._save_snapshot(snap)
        view = self.financial_view(
            business_mode=business_mode,
            opportunities=opportunities,
            demo=demo,
            connected=connected,
        )
        return {"ok": True, "synced_at": now, "financial_view": view}

    def finance_center(
        self,
        owner_name: str,
        greeting: str,
        *,
        business_mode=None,
        opportunities: list[dict] | None = None,
    ) -> dict:
        config = self._load_config()
        snap = self._sync_settlement_snapshot(self._load_snapshot())
        self._save_snapshot(snap)
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
            "paid_by_client_eur": float(snap.get("paid_by_client_eur") or 0),
            "pending_settlement_eur": float(snap.get("pending_settlement_eur") or 0),
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
            "settlements": self._settlements().list_settlements(),
            "settlement_note_ru": (
                "DE: Stripe удерживает ~3 рабочих дня. «Оплачено клиентом» — после webhook; "
                "«Доступно к выводу» — после settlement."
            ),
        }

        if demo:
            for key, val in _DEMO_FINANCE.items():
                result[key] = val
            result["payment_provider_label"] = "Demo (имитация)"
            result["recent_transactions"] = [
                {"at": "2026-07-03T03:11:00Z", "amount_eur": 49.0, "label": "Landing стоматология", "category": "sale"},
                {"at": "2026-07-02T18:00:00Z", "amount_eur": 50.0, "label": "Landing Page", "category": "sale"},
            ]

        view = self.financial_view(
            business_mode=business_mode,
            opportunities=opportunities,
            demo=demo,
            connected=connected,
        )
        result["financial_view"] = view
        result["system_mode"] = view["system_mode"]
        result["withdrawal_enabled"] = bool(view.get("withdraw_enabled"))

        return result

    def global_revenue_report(self, opportunities: list[dict]) -> dict:
        revenue_by: dict[str, float] = {}
        pipeline_by: dict[str, float] = {}
        leads_by: dict[str, int] = {}
        for row in opportunities:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            cc = str(meta.get("country_code") or meta.get("scan_region") or "GLOBAL")
            rev = float(row.get("revenue_eur") or 0)
            pot = float(row.get("potential_value_eur") or 0)
            if rev > 0:
                revenue_by[cc] = round(revenue_by.get(cc, 0) + rev, 2)
            if pot > 0 and row.get("status") not in ("won", "lost"):
                pipeline_by[cc] = round(pipeline_by.get(cc, 0) + pot, 2)
            leads_by[cc] = leads_by.get(cc, 0) + 1

        countries = sorted(set(revenue_by) | set(pipeline_by) | set(leads_by))
        rows = []
        for cc in countries:
            rows.append(
                {
                    "country_code": cc,
                    "revenue_eur": revenue_by.get(cc, 0.0),
                    "pipeline_eur": pipeline_by.get(cc, 0.0),
                    "leads": leads_by.get(cc, 0),
                }
            )
        rows.sort(key=lambda r: r["revenue_eur"], reverse=True)
        return {
            "currency": "EUR",
            "countries_active": len([r for r in rows if r["revenue_eur"] > 0]),
            "total_revenue_eur": round(sum(revenue_by.values()), 2),
            "total_pipeline_eur": round(sum(pipeline_by.values()), 2),
            "by_country": rows,
            "note": "Global Revenue — доход и воронка по странам (из meta.country_code).",
        }

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
        snap["products_sold"] = int(snap.get("products_sold", 0)) + 1

        self._settlements().record_payment(
            amount_eur=amount,
            payment_id=payment_id,
            provider=provider,
            label=label,
            immediate_available=provider == "sandbox",
        )
        snap = self._sync_settlement_snapshot(snap)
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
                "settlement_status": "pending_settlement",
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
        snap["products_sold"] = int(snap.get("products_sold", 0)) + 1

        self._settlements().record_payment(
            amount_eur=amount,
            payment_id=payment_id,
            provider=provider,
            label=label,
            order_id=order_id,
            sender=sender,
            immediate_available=provider == "sandbox",
        )
        snap = self._sync_settlement_snapshot(snap)
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
                "external_id": external_id,
                "settlement_status": "pending_settlement",
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

    def _load_all_transactions(self) -> list[dict]:
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
        return rows

    def payment_connected(self) -> bool:
        config = self._load_config()
        return bool(config.get("payment_provider")) and not bool(config.get("demo_mode"))

    def real_money_inputs(self) -> dict:
        """Raw inputs for real-money tiers — no ledger mixing."""
        config = self._load_config()
        snap = self._sync_settlement_snapshot(self._load_snapshot())
        self._save_snapshot(snap)
        return {
            "finance_snapshot": snap,
            "transactions": self._load_all_transactions(),
            "pending_payments": self._pending_payments(),
            "payout_history": self._payout_history(limit=50),
            "settlements": self._settlements().list_settlements(limit=100),
            "payment_connected": self.payment_connected(),
            "demo_mode": bool(config.get("demo_mode")),
        }
