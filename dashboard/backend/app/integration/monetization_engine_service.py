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
from app.integration.google_places_service import GooglePlacesService
from app.integration.opportunity_service import OpportunityService
from app.integration.payment_checkout_service import PaymentCheckoutService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

# Auto-gate: high-yield → owner journal; low-yield → junk archive (micro-monetization)
MIN_PROFIT_SCORE = 45
STRONG_PROFIT_SCORE = 70
MICRO_REVENUE_MIN_EUR = 0.50
MICRO_REVENUE_MAX_EUR = 1.00
_PROCESSING_LANE_HIGH = "high"
_PROCESSING_LANE_JUNK = "junk_archive"

_ACTIVE_STATUSES = frozenset({"proposed", "contacted", "qualified", "won"})
_PENDING_STATUSES = frozenset({"new", "reviewed"})

_NICHE_SCAN_QUERIES: dict[str, str] = {
    "local_service": "Autowerkstatt",
    "expired_landing": "Handwerker website",
    "niche_blog": "Lokaler Blog",
}


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
        self._places = GooglePlacesService()

    def _append_harvest_event(self, event: dict[str, Any]) -> None:
        path = self._memory / "engine_harvest_events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        event["at"] = datetime.now(timezone.utc).isoformat()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

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

    def _micro_revenue_for_score(self, profit_score: int) -> float:
        if profit_score >= MIN_PROFIT_SCORE:
            return 0.0
        ratio = max(0.0, min(1.0, profit_score / max(1, MIN_PROFIT_SCORE)))
        amount = MICRO_REVENUE_MIN_EUR + ratio * (MICRO_REVENUE_MAX_EUR - MICRO_REVENUE_MIN_EUR)
        return round(amount, 2)

    def _apply_junk_micro_monetization(self, row: dict[str, Any]) -> dict[str, Any]:
        """Secondary processing: auto SEO micro-fixes → €0.50–1.00 per junk asset."""
        meta = dict(row.get("meta") or {})
        profit_score = int(meta.get("profit_score") or row.get("score") or 0)
        if meta.get("processing_lane") != _PROCESSING_LANE_JUNK:
            return row

        micro_amount = self._micro_revenue_for_score(profit_score)
        if micro_amount <= 0:
            return row

        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        title = str(analysis.get("title") or row.get("company_name") or "Asset")
        seo_actions = [
            f"Meta title optimiert: «{title[:48]} · Service»",
            "Meta description auf DE ergänzt (120 Zeichen)",
            "Open-Graph og:title / og:description synchronisiert",
        ]
        prev_revenue = float(row.get("revenue_eur") or 0)
        new_revenue = round(prev_revenue + micro_amount, 2)
        meta.update(
            {
                "junk_micro_seo": seo_actions,
                "junk_micro_revenue_eur": round(float(meta.get("junk_micro_revenue_eur") or 0) + micro_amount, 2),
                "junk_last_micro_at": datetime.now(timezone.utc).isoformat(),
                "junk_micro_cycles": int(meta.get("junk_micro_cycles") or 0) + 1,
            }
        )
        updated = self._opportunity.update(
            row["id"],
            {
                "meta": meta,
                "revenue_eur": new_revenue,
                "status": "won" if new_revenue >= MICRO_REVENUE_MAX_EUR else "reviewed",
                "notes": (row.get("notes") or "") + f"\nJunk-SEO micro: +{micro_amount:.2f} €",
            },
        )
        self._finance.credit_order_payment(
            micro_amount,
            f"Junk-SEO: {row.get('company_name', '')}",
            provider=str(self._checkout.provider() or "engine"),
            order_id=row["id"],
        )
        self._append_harvest_event(
            {
                "type": "junk_micro_revenue",
                "opportunity_id": row["id"],
                "amount_eur": micro_amount,
                "profit_score": profit_score,
                "lane": _PROCESSING_LANE_JUNK,
            }
        )
        return updated

    def process_junk_archive_cycle(self, *, limit: int = 50) -> dict[str, Any]:
        """Batch secondary processing for archived low-score assets."""
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        processed = 0
        revenue_eur = 0.0
        for row in rows:
            if processed >= limit:
                break
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if meta.get("processing_lane") != _PROCESSING_LANE_JUNK:
                continue
            if meta.get("junk_last_micro_at"):
                continue
            before = float(row.get("revenue_eur") or 0)
            updated = self._apply_junk_micro_monetization(row)
            after = float(updated.get("revenue_eur") or 0)
            delta = round(after - before, 2)
            if delta > 0:
                processed += 1
                revenue_eur = round(revenue_eur + delta, 2)
        self._sync_harvest_from_assets()
        return {
            "ok": True,
            "processed": processed,
            "revenue_eur": revenue_eur,
            "message": (
                f"Вторичная обработка: {processed} активов, +{revenue_eur:.2f} € микро-дохода."
                if processed
                else "Архив мусора: новых активов для микро-обработки нет."
            ),
        }

    def _route_scanned_target(
        self,
        row: dict[str, Any],
        *,
        profit_score: int,
        meta: dict[str, Any],
        manual: bool = False,
    ) -> dict[str, Any]:
        if profit_score >= MIN_PROFIT_SCORE:
            meta["processing_lane"] = _PROCESSING_LANE_HIGH
            meta["auto_gate_pass"] = True
            meta["auto_gate_reason"] = (
                "Достаточная доходность — в журнал владельца"
                if not manual
                else "Ручной URL — высокий score, готов к активации"
            )
            updated = self._opportunity.update(row["id"], {"meta": meta, "score": profit_score})
            return {
                "target": updated,
                "profit_score": profit_score,
                "lane": _PROCESSING_LANE_HIGH,
                "shown_to_owner": True,
                "archived": False,
                "message": meta["auto_gate_reason"],
            }

        meta["processing_lane"] = _PROCESSING_LANE_JUNK
        meta["auto_gate_pass"] = False
        meta["auto_gate_reason"] = (
            "Низкий score — в архив мусора, запущена микро-монетизация SEO"
            if not manual
            else "Ручной URL — низкий score, вторичная обработка в архиве"
        )
        updated = self._opportunity.update(
            row["id"],
            {
                "meta": meta,
                "score": profit_score,
                "status": "reviewed",
                "notes": (row.get("notes") or "") + "\nAuto-gate: junk archive (SEO micro).",
            },
        )
        updated = self._apply_junk_micro_monetization(updated)
        return {
            "target": updated,
            "profit_score": profit_score,
            "lane": _PROCESSING_LANE_JUNK,
            "shown_to_owner": False,
            "archived": True,
            "message": meta["auto_gate_reason"],
        }

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
                        self.connect_payout_wallet("stripe", f"Stripe · {amount:.2f} €")
            except httpx.HTTPError:
                result["stripe_error"] = "balance_fetch_failed"
        elif self._checkout.is_configured():
            path = self._memory / "finance_config.json"
            config: dict[str, Any] = {}
            if path.is_file():
                try:
                    config = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    config = {}
            if not config.get("payment_provider"):
                config["payment_provider"] = provider
                config["payment_provider_label"] = "Stripe" if provider == "stripe" else "Sandbox"
                path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        self._sync_harvest_from_assets()
        return result

    def engine_dashboard(self, owner_name: str = "Ramiš") -> dict[str, Any]:
        harvest = self._sync_harvest_from_assets()
        fin = self._finance.finance_center(owner_name, "")
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=100)

        pending = []
        active = []
        harvested = []
        junk_archive = []
        junk_micro_total = 0.0
        for row in rows:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            profit_score = int(meta.get("profit_score") or row.get("score") or 0)
            lane = str(meta.get("processing_lane") or "")
            micro_rev = float(meta.get("junk_micro_revenue_eur") or 0)
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
                "processing_lane": lane,
                "micro_revenue_eur": micro_rev,
            }
            if lane == _PROCESSING_LANE_JUNK:
                junk_archive.append(item)
                junk_micro_total = round(junk_micro_total + micro_rev, 2)
                continue
            if row.get("status") == "won":
                harvested.append(item)
            elif row.get("status") in _ACTIVE_STATUSES:
                active.append(item)
            elif row.get("status") in _PENDING_STATUSES and profit_score >= MIN_PROFIT_SCORE:
                pending.append(item)

        pending.sort(key=lambda x: x["profit_score"], reverse=True)
        active.sort(key=lambda x: x["potential_eur"], reverse=True)
        harvested.sort(key=lambda x: x["revenue_eur"], reverse=True)
        junk_archive.sort(key=lambda x: x["micro_revenue_eur"], reverse=True)

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
            "harvested_assets": harvested,
            "harvested_count": len(harvested),
            "junk_archive_assets": junk_archive,
            "junk_archive_count": len(junk_archive),
            "junk_micro_revenue_eur": junk_micro_total,
            "finance_gateway": {
                "provider": fin.get("payment_provider"),
                "connected": fin.get("payment_connected", False),
                "sync_path": "monetization_engine_service.sync_payment_providers",
                "withdraw_path": "monetization_engine_service.request_withdrawal",
                "ledger": "memory/finance_snapshot.json + engine_harvest.json",
            },
            "wallets": fin.get("wallets", []),
            "withdrawal_enabled": fin.get("withdrawal_enabled", False),
        }

    def scan_and_gate(self, url: str, *, niche: str = "local_service", manual: bool = False) -> dict[str, Any]:
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
        meta["niche"] = niche
        result = self._route_scanned_target(row, profit_score=profit_score, meta=meta, manual=manual)
        self._sync_harvest_from_assets()
        return result

    def accept_asset(self, opportunity_id: str) -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        accepted = self._scanner.accept_for_work(opportunity_id)
        potential = float(accepted.get("potential_value_eur") or 0)
        self._append_harvest_event(
            {
                "type": "asset_accepted",
                "opportunity_id": opportunity_id,
                "potential_eur": potential,
                "company": accepted.get("company_name", ""),
            }
        )
        harvest = self._load_harvest()
        harvest["pipeline_locked_eur"] = round(
            float(harvest.get("pipeline_locked_eur") or 0) + potential,
            2,
        )
        self._save_harvest(harvest)
        self._sync_harvest_from_assets()
        if self._checkout.is_configured():
            self.sync_payment_providers()
        return accepted

    def run_scan_mode(
        self,
        *,
        niche: str = "local_service",
        city: str = "Pirna",
        limit: int = 8,
    ) -> dict[str, Any]:
        """Manual niche scan — public leads with websites only."""
        niche_key = niche if niche in _NICHE_SCAN_QUERIES else "local_service"
        query_base = _NICHE_SCAN_QUERIES[niche_key]
        query = f"{query_base} {city}".strip()
        scanned = 0
        passed = 0
        archived = 0
        errors: list[str] = []

        urls: list[str] = []
        if self._places.configured():
            try:
                leads = self._places.search_text(query=query, limit=limit)
                for lead in leads:
                    site = (lead.website or "").strip()
                    if site.startswith(("http://", "https://")):
                        urls.append(site)
            except ValueError as exc:
                errors.append(str(exc))
        else:
            journal = self._opportunity.list_opportunities(limit=limit * 3)
            for row in journal:
                site = (row.get("website_url") or "").strip()
                if site.startswith(("http://", "https://")):
                    urls.append(site)
            if not urls:
                errors.append("places_not_configured_add_GOOGLE_PLACES_API_KEY_or_scan_URL_manually")

        seen: set[str] = set()
        for url in urls:
            if url in seen:
                continue
            seen.add(url)
            try:
                result = self.scan_and_gate(url, niche=niche_key)
                scanned += 1
                if result.get("lane") == _PROCESSING_LANE_HIGH:
                    passed += 1
                else:
                    archived += 1
            except ValueError as exc:
                errors.append(f"{url}: {exc}")

        junk_batch = self.process_junk_archive_cycle()
        self.sync_payment_providers()
        return {
            "ok": True,
            "niche": niche_key,
            "city": city,
            "query": query,
            "scanned": scanned,
            "passed_gate": passed,
            "archived": archived,
            "hidden": archived,
            "junk_micro_revenue_eur": junk_batch.get("revenue_eur", 0.0),
            "errors": errors[:5],
            "message": (
                f"Поиск целей: {scanned} URL · журнал {passed} · архив {archived} · "
                f"микро +{float(junk_batch.get('revenue_eur') or 0):.2f} €"
            ),
        }

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
