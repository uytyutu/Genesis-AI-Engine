"""Monetization Engine — autonomous harvest mode for owner capital (Engine Mode).

SECURITY LAW: inherited from asset_scanner — public URLs only, no credential harvesting.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.integration.asset_scanner_service import AssetScannerService, assert_public_scan_allowed
from app.integration.finance_service import FinanceService
from app.integration.opportunity_service import OpportunityService
from app.integration.payment_checkout_service import PaymentCheckoutService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

# Auto-gate: engine hides low-yield targets before owner sees them
MIN_PROFIT_SCORE = 45
STRONG_PROFIT_SCORE = 70

_ACTIVE_STATUSES = frozenset({"proposed", "contacted", "qualified", "won"})
_PENDING_STATUSES = frozenset({"new", "reviewed"})


def compute_profitability_score(
    *,
    potential_eur: float,
    traffic_band: str,
    abandoned: bool,
    analysis_score: int,
    issue_count: int,
) -> int:
    score = 0
    score += min(35, int(potential_eur))
    if traffic_band == "medium":
        score += 25
    elif traffic_band == "low":
        score += 12
    if abandoned:
        score += 18
    score += min(20, max(0, analysis_score // 3))
    score -= min(15, issue_count * 2)
    return max(0, min(100, score))


class MonetizationEngineService:
    def __init__(
        self,
        opportunity: OpportunityService,
        finance: FinanceService,
        checkout: PaymentCheckoutService,
        scanner: AssetScannerService,
        memory_dir: Path | None = None,
    ) -> None:
        self._opportunity = opportunity
        self._finance = finance
        self._checkout = checkout
        self._scanner = scanner
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _harvest_path(self) -> Path:
        return self._memory / "engine_harvest.json"

    def _load_harvest(self) -> dict[str, Any]:
        path = self._harvest_path()
        if not path.is_file():
            return {
                "harvest_balance_eur": 0.0,
                "lifetime_harvest_eur": 0.0,
                "active_assets_count": 0,
                "last_sync_at": None,
            }
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"harvest_balance_eur": 0.0, "lifetime_harvest_eur": 0.0}

    def _save_harvest(self, data: dict[str, Any]) -> None:
        path = self._harvest_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _sync_harvest_from_assets(self) -> dict[str, Any]:
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        won_revenue = sum(float(r.get("revenue_eur") or 0) for r in rows if r.get("status") == "won")
        pipeline = sum(
            float(r.get("potential_value_eur") or 0)
            for r in rows
            if r.get("status") in _ACTIVE_STATUSES
        )
        active = sum(1 for r in rows if r.get("status") in _ACTIVE_STATUSES)
        harvest = self._load_harvest()
        fin_snap = self._finance._load_snapshot()  # noqa: SLF001 — engine sync layer
        harvest_balance = round(
            float(fin_snap.get("available_for_withdrawal_eur") or 0) + won_revenue,
            2,
        )
        harvest.update(
            {
                "harvest_balance_eur": harvest_balance,
                "lifetime_harvest_eur": round(
                    float(harvest.get("lifetime_harvest_eur") or 0) + won_revenue,
                    2,
                ),
                "pipeline_potential_eur": round(pipeline, 2),
                "active_assets_count": active,
                "last_sync_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save_harvest(harvest)
        return harvest

    def sync_payment_providers(self) -> dict[str, Any]:
        """Sync balances from configured payment APIs (Stripe when key present)."""
        provider = self._checkout.provider()
        result: dict[str, Any] = {
            "provider": provider,
            "configured": self._checkout.is_configured(),
            "live_mode": self._checkout.is_live_mode(),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        sk = os.getenv("STRIPE_SECRET_KEY", "").strip()
        if provider == "stripe" and sk:
            try:
                with httpx.Client(timeout=12.0) as client:
                    res = client.get(
                        "https://api.stripe.com/v1/balance",
                        headers={"Authorization": f"Bearer {sk}"},
                    )
                if res.is_success:
                    body = res.json()
                    available = body.get("available") or []
                    eur_avail = next((x for x in available if x.get("currency") == "eur"), None)
                    if eur_avail:
                        amount = round(int(eur_avail.get("amount", 0)) / 100, 2)
                        snap = self._finance._load_snapshot()  # noqa: SLF001
                        snap["platform_balance_eur"] = amount
                        snap["available_for_withdrawal_eur"] = amount
                        snap["source"] = "stripe"
                        self._finance._save_snapshot(snap)  # noqa: SLF001
                        result["stripe_available_eur"] = amount
            except httpx.HTTPError:
                result["stripe_error"] = "balance_fetch_failed"
        self._sync_harvest_from_assets()
        return result

    def engine_dashboard(self, owner_name: str = "Ramiš") -> dict[str, Any]:
        harvest = self._sync_harvest_from_assets()
        fin = self._finance.finance_center(owner_name, "")
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=100)

        pending = []
        active = []
        for row in rows:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            profit_score = int(meta.get("profit_score") or row.get("score") or 0)
            item = {
                "id": row["id"],
                "name": row.get("company_name", ""),
                "url": row.get("website_url", ""),
                "potential_eur": float(row.get("potential_value_eur") or 0),
                "profit_score": profit_score,
                "traffic_band": meta.get("traffic_band", "trace"),
                "abandoned": bool(meta.get("abandoned")),
                "status": row.get("status"),
                "status_label": row.get("status_label"),
                "income_rationale": row.get("fit_reason", ""),
                "revenue_eur": float(row.get("revenue_eur") or 0),
                "niche": meta.get("niche", "local_service"),
            }
            if row.get("status") in _ACTIVE_STATUSES:
                active.append(item)
            elif row.get("status") in _PENDING_STATUSES and profit_score >= MIN_PROFIT_SCORE:
                pending.append(item)

        pending.sort(key=lambda x: x["profit_score"], reverse=True)
        active.sort(key=lambda x: x["potential_eur"], reverse=True)

        return {
            "mode": "engine",
            "owner_name": owner_name,
            "security_law": (
                "Только публичные активы. Запрещены ключи, пароли и закрытые системы."
            ),
            "harvest_balance_eur": harvest.get("harvest_balance_eur", 0.0),
            "lifetime_harvest_eur": harvest.get("lifetime_harvest_eur", 0.0),
            "pipeline_potential_eur": harvest.get("pipeline_potential_eur", 0.0),
            "active_assets_count": harvest.get("active_assets_count", 0),
            "available_for_withdrawal_eur": fin.get("available_for_withdrawal_eur", 0.0),
            "pending_payouts_eur": fin.get("pending_payouts_eur", 0.0),
            "payment_connected": fin.get("payment_connected", False),
            "payment_provider": fin.get("payment_provider"),
            "payment_provider_label": fin.get("payment_provider_label"),
            "last_sync_at": harvest.get("last_sync_at"),
            "auto_gate_min_score": MIN_PROFIT_SCORE,
            "pending_targets": pending,
            "active_assets": active,
            "wallets": fin.get("wallets", []),
            "withdrawal_enabled": fin.get("withdrawal_enabled", False),
        }

    def scan_and_gate(self, url: str, *, niche: str = "local_service") -> dict[str, Any]:
        assert_public_scan_allowed(url)
        row = self._scanner.scan_url(url, niche=niche)
        analysis = row.get("site_analysis") or {}
        meta = dict(row.get("meta") or {})
        traffic = str(meta.get("traffic_band") or "trace")
        abandoned = bool(meta.get("abandoned"))
        profit_score = compute_profitability_score(
            potential_eur=float(row.get("potential_value_eur") or 0),
            traffic_band=traffic,
            abandoned=abandoned,
            analysis_score=int(analysis.get("improvement_score") or 0),
            issue_count=int(analysis.get("issue_count") or 0),
        )
        meta["profit_score"] = profit_score
        meta["auto_gate_pass"] = profit_score >= MIN_PROFIT_SCORE
        meta["auto_gate_reason"] = (
            "Достаточная доходность — предложено владельцу"
            if profit_score >= MIN_PROFIT_SCORE
            else "Низкая доходность — скрыто автоматическим фильтром"
        )
        updated = self._opportunity.update(row["id"], {"meta": meta, "score": profit_score})
        if profit_score < MIN_PROFIT_SCORE:
            updated = self._opportunity.update(
                row["id"],
                {"status": "lost", "notes": (row.get("notes") or "") + "\nAuto-gate: низкий потенциал."},
            )
        self._sync_harvest_from_assets()
        return {
            "target": updated,
            "profit_score": profit_score,
            "shown_to_owner": profit_score >= MIN_PROFIT_SCORE,
            "message": meta["auto_gate_reason"],
        }

    def accept_asset(self, opportunity_id: str) -> dict:
        row = self._scanner.accept_for_work(opportunity_id)
        self._sync_harvest_from_assets()
        return row

    def record_asset_revenue(self, opportunity_id: str, amount_eur: float) -> dict:
        row = self._scanner.record_income(opportunity_id, amount_eur)
        self._finance.credit_order_payment(
            amount_eur,
            f"Добыча актива: {row.get('company_name', '')}",
            provider=str(self._checkout.provider() or "stripe"),
            order_id=opportunity_id,
        )
        self._sync_harvest_from_assets()
        return row

    def connect_payout_wallet(self, wallet_id: str, account_label: str) -> dict:
        path = self._memory / "finance_config.json"
        config: dict[str, Any] = {}
        if path.is_file():
            try:
                config = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                config = {}
        wallets = dict(config.get("wallets") or {})
        wallets[wallet_id] = {
            "connected": True,
            "balance_label": account_label,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
        config["wallets"] = wallets
        if wallet_id == "stripe" and self._checkout.is_configured():
            config["payment_provider"] = "stripe"
            config["payment_provider_label"] = "Stripe"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "wallet_id": wallet_id, "label": account_label}

    def request_withdrawal(self, amount_eur: float, wallet_id: str) -> dict:
        amount = round(float(amount_eur), 2)
        if amount <= 0:
            raise ValueError("invalid_amount")
        snap = self._finance._load_snapshot()  # noqa: SLF001
        available = float(snap.get("available_for_withdrawal_eur") or 0)
        if amount > available:
            raise ValueError("insufficient_balance")

        now = datetime.now(timezone.utc).isoformat()
        snap["available_for_withdrawal_eur"] = round(available - amount, 2)
        snap["pending_payouts_eur"] = round(float(snap.get("pending_payouts_eur") or 0) + amount, 2)
        self._finance._save_snapshot(snap)  # noqa: SLF001

        payout = {
            "at": now,
            "amount_eur": amount,
            "provider": wallet_id,
            "status": "pending",
            "status_label": "В обработке",
            "destination": wallet_id,
        }
        payout_path = self._memory / "finance_payouts.jsonl"
        payout_path.parent.mkdir(parents=True, exist_ok=True)
        with payout_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payout, ensure_ascii=False) + "\n")

        sync_note = "queued_local"
        sk = os.getenv("STRIPE_SECRET_KEY", "").strip()
        if wallet_id == "stripe" and sk:
            sync_note = "stripe_payout_requires_connect_account"

        self._sync_harvest_from_assets()
        return {
            "ok": True,
            "amount_eur": amount,
            "wallet_id": wallet_id,
            "status": "pending",
            "sync": sync_note,
            "message": "Заявка на вывод поставлена в очередь. Синхронизация с провайдером — finance_config + STRIPE_SECRET_KEY.",
        }
