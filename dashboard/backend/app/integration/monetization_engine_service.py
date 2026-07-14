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
from app.integration.public_intel_miner import PublicIntelMiner
from app.integration.engine_hunter_service import EngineHunterService
from app.integration.global_spider_service import GlobalSpiderService, world_scan_regions
from app.integration.smart_gate_approval import SmartGateApprovalService
from app.integration.engine_ai_service import EngineAIService
from app.integration.stealth_http import stealth_status
from app.integration.digital_dust_service import DigitalDustService
from app.integration.engine_analytics_service import EngineAnalyticsService

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

_NETWORK_MRR_PER_ASSET_EUR = 20.0
_NETWORK_TARGET_MRR_EUR = 10_000.0
_NETWORK_BATCH_MAX = 1000

_DE_BATCH_CITIES = (
    "Berlin",
    "Hamburg",
    "München",
    "Köln",
    "Frankfurt",
    "Stuttgart",
    "Düsseldorf",
    "Leipzig",
    "Dresden",
    "Hannover",
    "Nürnberg",
    "Dortmund",
    "Essen",
    "Bremen",
    "Pirna",
    "Chemnitz",
    "Bonn",
    "Mannheim",
    "Karlsruhe",
    "Augsburg",
)

_NICHE_SCAN_QUERIES: dict[str, str] = {
    "local_service": "local service business",
    "expired_landing": "coming soon business website",
    "niche_blog": "small business blog",
}


_DEFAULT_ARBITRAGE_OFFERS: dict[str, dict[str, Any]] = {
    "local_service": {
        "offer_id": "de-local-service",
        "label": "Локальные услуги · лидогенерация DE",
        "target_url": "https://offers.virtus-core.local/local-service",
        "cpc_eur": 0.85,
        "monthly_floor_eur": 20.0,
    },
    "expired_landing": {
        "offer_id": "de-landing-arbitrage",
        "label": "Арбитраж трафика · заброшенные лендинги",
        "target_url": "https://offers.virtus-core.local/landing",
        "cpc_eur": 0.55,
        "monthly_floor_eur": 20.0,
    },
    "niche_blog": {
        "offer_id": "de-niche-portal",
        "label": "Нишевый портал · реклама + affiliate",
        "target_url": "https://offers.virtus-core.local/niche-blog",
        "cpc_eur": 0.40,
        "monthly_floor_eur": 20.0,
    },
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
        *,
        acquisition: Any | None = None,
        factory: Any | None = None,
        business_mode: Any | None = None,
    ) -> None:
        self._opportunity = opportunity
        self._finance = finance
        self._checkout = checkout
        self._scanner = scanner
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._places = GooglePlacesService()
        self._intel_miner = PublicIntelMiner(self._memory)
        self._hunter = EngineHunterService(
            opportunity, acquisition, factory, self._intel_miner, self._memory
        )
        self._global_spider = GlobalSpiderService(self._memory)
        self._smart_gate = SmartGateApprovalService(self._memory)
        self._digital_dust = DigitalDustService(self._memory)
        self._analytics = EngineAnalyticsService(self._memory)
        self._business_mode = business_mode

    def _arbitrage_offers(self) -> dict[str, dict[str, Any]]:
        path = self._memory / "engine_arbitrage_offers.json"
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    merged = dict(_DEFAULT_ARBITRAGE_OFFERS)
                    merged.update(data)
                    return merged
            except (json.JSONDecodeError, OSError):
                pass
        return dict(_DEFAULT_ARBITRAGE_OFFERS)

    def _should_assign_arbitrage(self) -> bool:
        cfg = self._intel_miner.load_pattern_config()
        policy = cfg.get("execution_policy") if isinstance(cfg.get("execution_policy"), dict) else {}
        priority = str(cfg.get("priority") or policy.get("priority") or "outreach")
        return priority != "outreach"

    def _assign_arbitrage_offer(self, meta: dict[str, Any], *, niche: str) -> dict[str, Any]:
        if not self._should_assign_arbitrage():
            meta["monetization_priority"] = "outreach"
            meta["arbitrage_skipped"] = True
            return meta
        offers = self._arbitrage_offers()
        offer = offers.get(niche) or offers.get("local_service") or {}
        if not offer:
            return meta
        meta["arbitrage_offer_id"] = offer.get("offer_id", "")
        meta["arbitrage_label"] = offer.get("label", "")
        meta["arbitrage_target_url"] = offer.get("target_url", "")
        meta["arbitrage_cpc_eur"] = float(offer.get("cpc_eur") or 0)
        meta["network_managed"] = True
        meta["projected_monthly_eur"] = float(
            offer.get("monthly_floor_eur") or _NETWORK_MRR_PER_ASSET_EUR
        )
        return meta

    def _network_portfolio(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        managed = 0
        arbitrage_routes = 0
        projected_mrr = 0.0
        for row in rows:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            if not meta.get("network_managed") and row.get("status") not in _ACTIVE_STATUSES:
                if meta.get("processing_lane") not in (_PROCESSING_LANE_HIGH, _PROCESSING_LANE_JUNK):
                    continue
            managed += 1
            if meta.get("arbitrage_target_url"):
                arbitrage_routes += 1
            projected_mrr += float(
                meta.get("projected_monthly_eur") or _NETWORK_MRR_PER_ASSET_EUR
            )
        projected_mrr = round(projected_mrr, 2)
        progress = round(min(100.0, (projected_mrr / _NETWORK_TARGET_MRR_EUR) * 100), 1)
        return {
            "mode": "network",
            "total_assets": len(rows),
            "managed_assets": managed,
            "arbitrage_routes": arbitrage_routes,
            "mrr_per_asset_eur": _NETWORK_MRR_PER_ASSET_EUR,
            "projected_mrr_eur": projected_mrr,
            "target_mrr_eur": _NETWORK_TARGET_MRR_EUR,
            "target_progress_percent": progress,
            "expired_domain_watch": "horizon",
            "batch_scan_max": _NETWORK_BATCH_MAX,
        }

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

        gate_row = self._smart_gate.auto_execute_if_qualified(
            row,
            context="junk_micro",
            opportunity_update=self._opportunity.update,
        )
        meta = dict(gate_row.get("meta") or {})
        if not meta.get("junk_smart_gate_pass"):
            return gate_row

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
        if self._business_mode and self._business_mode.is_sandbox():
            meta["potential_micro_revenue_eur"] = round(
                float(meta.get("potential_micro_revenue_eur") or 0) + micro_amount,
                2,
            )
            meta["sandbox_projected"] = True
            updated = self._opportunity.update(
                row["id"],
                {
                    "meta": meta,
                    "revenue_eur": prev_revenue,
                    "status": "reviewed",
                    "notes": (row.get("notes") or "")
                    + f"\n[Sandbox] Потенциал микро-SEO: +{micro_amount:.2f} € (не зафиксировано)",
                },
            )
            self._append_harvest_event(
                {
                    "type": "junk_micro_potential",
                    "opportunity_id": row["id"],
                    "amount_eur": micro_amount,
                    "profit_score": profit_score,
                    "lane": _PROCESSING_LANE_JUNK,
                    "sandbox": True,
                }
            )
            return updated

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
            meta = self._assign_arbitrage_offer(meta, niche=str(meta.get("niche") or "local_service"))
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
        meta = self._assign_arbitrage_offer(meta, niche=str(meta.get("niche") or "local_service"))
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
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        network = self._network_portfolio(rows)

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

        rows_all = self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        business = self._business_mode.status() if self._business_mode else {"system_mode": "live"}
        potential = (
            self._business_mode.compute_potential_revenue(rows_all)
            if self._business_mode
            else {"potential_revenue_eur": harvest.get("pipeline_potential_eur", 0)}
        )
        realized = (
            self._business_mode.realized_revenue(rows_all)
            if self._business_mode
            else {"realized_revenue_eur": harvest.get("lifetime_harvest_eur", 0)}
        )

        display_harvest = (
            float(potential.get("potential_revenue_eur") or 0)
            if business.get("system_mode") == "sandbox"
            else harvest.get("harvest_balance_eur", 0.0)
        )

        return {
            "mode": "engine",
            "system_mode": business.get("system_mode", "sandbox"),
            "mode_label": business.get("mode_label", ""),
            "financial_docs_enabled": business.get("financial_docs_enabled", True),
            "potential_revenue": potential,
            "realized_revenue": realized,
            "harvest_balance_label": (
                "Сколько можно заработать (пока не на счёте)"
                if business.get("system_mode") == "sandbox"
                else "Реальный баланс"
            ),
            "owner_name": owner_name,
            "security_law": (
                "Только публичные активы. Запрещены ключи, пароли и закрытые системы."
            ),
            "stealth_mode": stealth_status(),
            "harvest_balance_eur": display_harvest,
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
            "network": network,
            "pattern_intel_value_eur": float(harvest.get("pattern_intel_value_eur") or 0),
            "pattern_hits_total": int(harvest.get("pattern_hits_total") or 0),
            "hunter": self._hunter.hunter_dashboard(),
            "ai_brain": EngineAIService(self._memory).setup_status(),
            "global_spider": self._global_spider.spider_dashboard(),
            "places_autopilot": self._places.setup_status(),
            "smart_gate": self._smart_gate.dashboard(),
            "digital_dust": self._digital_dust.dashboard(),
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

    def live_analytics(self) -> dict[str, Any]:
        harvest = self._sync_harvest_from_assets()
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        return self._analytics.live_dashboard(
            harvest=harvest,
            hunter=self._hunter.hunter_dashboard(),
            smart_gate=self._smart_gate.dashboard(),
            global_spider=self._global_spider.spider_dashboard(),
            digital_dust=self._digital_dust.dashboard(),
            opportunities=rows,
        )

    def process_pattern_hits(self, opportunity_id: str) -> dict[str, Any]:
        """PublicIntelMiner hook — pattern hits → meta + harvest ledger (no auto-buy)."""
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")

        hits = self._intel_miner.mine_patterns_from_scan(row)
        config = self._intel_miner.load_pattern_config()
        policy = config.get("execution_policy") if isinstance(config.get("execution_policy"), dict) else {}
        priority = str(config.get("priority") or policy.get("priority") or "outreach")

        updated = self._hunter.run_hunter_scenarios(opportunity_id, hits)
        meta = dict(updated.get("meta") or {})
        hit_dicts = meta.get("pattern_hits") or []
        dust_hits = [h for h in hits if h.lane == "digital_dust"]
        if dust_hits:
            row_now = self._opportunity.get(opportunity_id) or updated
            updated = self._digital_dust.process_opportunity(
                row_now,
                hits,
                opportunity_update=self._opportunity.update,
            )
            meta = dict(updated.get("meta") or {})
            hit_dicts = meta.get("pattern_hits") or hit_dicts
            dust_value = float(meta.get("digital_dust_value_eur") or 0)
            self._append_harvest_event(
                {
                    "type": "potential_recoverable_asset",
                    "opportunity_id": opportunity_id,
                    "assets_count": meta.get("recoverable_assets_count", 0),
                    "value_eur": dust_value,
                    "company": row.get("company_name", ""),
                }
            )
            harvest = self._load_harvest()
            harvest["recoverable_assets_count"] = int(harvest.get("recoverable_assets_count") or 0) + int(
                meta.get("recoverable_assets_count") or 0
            )
            harvest["recoverable_value_eur"] = round(
                float(harvest.get("recoverable_value_eur") or 0) + dust_value,
                2,
            )
            self._save_harvest(harvest)

        data_value = round(
            sum(float(h.get("valuation_eur") or 0) for h in hit_dicts if h.get("lane") in ("dataset_row", "data_product")),
            2,
        )
        alert_hits = [h for h in hit_dicts if h.get("lane") == "arbitrage_alert"]
        pending_tx: list[dict[str, Any]] = []

        if priority != "outreach":
            for h in alert_hits:
                pending_tx.append(
                    {
                        "type": "arbitrage_buy_draft",
                        "pattern_id": h.get("pattern_id"),
                        "asset_ref": h.get("matched_value"),
                        "source_url": h.get("source_url"),
                        "estimated_value_eur": h.get("valuation_eur"),
                        "status": "pending_ceo_approval",
                        "auto_execute": False,
                    }
                )
            if alert_hits:
                meta["execution_status"] = "pending_ceo_approval"
                meta["arbitrage_alerts"] = alert_hits
            if pending_tx:
                meta["pending_transactions"] = pending_tx

        hunter_value = float(meta.get("hunter_value_eur") or 0)
        meta["pattern_value_eur"] = round(data_value + (0 if priority == "outreach" else 0), 2)
        meta["pattern_intel_at"] = datetime.now(timezone.utc).isoformat()

        potential_boost = round(float(row.get("potential_value_eur") or 0) + hunter_value, 2)
        updated = self._opportunity.update(
            opportunity_id,
            {
                "meta": meta,
                "potential_value_eur": potential_boost,
            },
        )

        if hit_dicts:
            self._append_harvest_event(
                {
                    "type": "hunter_intel",
                    "opportunity_id": opportunity_id,
                    "hits_count": len(hit_dicts),
                    "hunter_value_eur": hunter_value,
                    "scenarios": meta.get("hunter_scenarios"),
                    "execution_status": meta.get("execution_status") or "outreach_pending_approval",
                    "company": row.get("company_name", ""),
                }
            )

        harvest = self._load_harvest()
        harvest["pattern_intel_value_eur"] = round(
            float(harvest.get("pattern_intel_value_eur") or 0) + hunter_value,
            2,
        )
        harvest["pattern_hits_total"] = int(harvest.get("pattern_hits_total") or 0) + len(hit_dicts)
        harvest["hunter_value_eur"] = round(float(harvest.get("hunter_value_eur") or 0) + hunter_value, 2)
        self._save_harvest(harvest)

        context = "outreach" if priority == "outreach" else "seo_revival"
        updated = self._smart_gate.auto_execute_if_qualified(
            self._opportunity.get(opportunity_id) or updated,
            context=context,
            opportunity_update=self._opportunity.update,
        )

        return updated

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
        country = GlobalSpiderService.infer_country_code(url)
        meta["country_code"] = country
        meta["scan_region"] = country
        result = self._route_scanned_target(row, profit_score=profit_score, meta=meta, manual=manual)
        target_id = result["target"]["id"]
        enriched = self.process_pattern_hits(target_id)
        result["target"] = enriched
        result["pattern_hits"] = (enriched.get("meta") or {}).get("pattern_hits", [])
        result["pattern_hits_count"] = len(result["pattern_hits"])
        self._sync_harvest_from_assets()
        return result

    def accept_asset(self, opportunity_id: str) -> dict:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        accepted = self._scanner.accept_for_work(opportunity_id)
        meta = dict(accepted.get("meta") or {})
        niche = str(meta.get("niche") or "local_service")
        meta = self._assign_arbitrage_offer(meta, niche=niche)
        accepted = self._opportunity.update(opportunity_id, {"meta": meta})
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
        city: str = "Berlin",
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

    def run_network_scan(
        self,
        *,
        niche: str = "local_service",
        batch_limit: int = 1000,
        region: str = "WORLD",
    ) -> dict[str, Any]:
        """Scalable worldwide scan — up to 1000 public URLs per run."""
        niche_key = niche if niche in _NICHE_SCAN_QUERIES else "local_service"
        batch_limit = max(1, min(_NETWORK_BATCH_MAX, int(batch_limit)))
        world_regions = world_scan_regions()
        per_city = max(3, batch_limit // max(1, len(world_regions)))
        scanned = 0
        passed = 0
        archived = 0
        cities_hit = 0
        errors: list[str] = []
        seen: set[str] = set()

        if not self._places.configured():
            return {
                "ok": False,
                "niche": niche_key,
                "region": region,
                "batch_limit": batch_limit,
                "scanned": 0,
                "passed_gate": 0,
                "archived": 0,
                "cities_scanned": 0,
                "errors": ["places_not_configured_add_GOOGLE_PLACES_API_KEY"],
                "message": "Для авто-поиска нужен GOOGLE_PLACES_API_KEY в .env.local",
            }

        query_suffix = _NICHE_SCAN_QUERIES[niche_key]
        for region_code, city, _base in world_regions:
            if scanned >= batch_limit:
                break
            cities_hit += 1
            query = f"{query_suffix} {city}".strip()
            remaining = batch_limit - scanned
            city_limit = min(per_city, remaining, 50)
            try:
                leads = self._places.search_text(
                    query=query, limit=city_limit, region=region_code
                )
            except (ValueError, RuntimeError) as exc:
                errors.append(f"{city}: {exc}")
                continue
            for lead in leads:
                if scanned >= batch_limit:
                    break
                site = (lead.website or "").strip()
                if not site.startswith(("http://", "https://")) or site in seen:
                    continue
                seen.add(site)
                try:
                    result = self.scan_and_gate(site, niche=niche_key)
                    scanned += 1
                    if result.get("lane") == _PROCESSING_LANE_HIGH:
                        passed += 1
                    else:
                        archived += 1
                except ValueError as exc:
                    errors.append(f"{site}: {exc}")

        junk_batch = self.process_junk_archive_cycle(limit=100)
        self.sync_payment_providers()
        network = self._network_portfolio(
            self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        )
        return {
            "ok": True,
            "niche": niche_key,
            "region": region,
            "batch_limit": batch_limit,
            "scanned": scanned,
            "passed_gate": passed,
            "archived": archived,
            "cities_scanned": cities_hit,
            "junk_micro_revenue_eur": junk_batch.get("revenue_eur", 0.0),
            "network": network,
            "errors": errors[:8],
            "message": (
                f"Авто-поиск (весь мир): {scanned}/{batch_limit} сайтов · {cities_hit} городов · "
                f"в журнале {passed} · в архиве {archived}"
            ),
        }

    def run_global_spider_scan(
        self,
        *,
        niche: str = "local_service",
        batch_limit: int = 500,
        tech_pattern_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Global Spider — technology-pattern targets worldwide (public URLs only)."""
        niche_key = niche if niche in _NICHE_SCAN_QUERIES else "local_service"
        batch_limit = max(1, min(_NETWORK_BATCH_MAX, int(batch_limit)))
        candidates, discovery = self._global_spider.discover_candidate_urls(
            niche=niche_key,
            batch_limit=batch_limit,
            tech_pattern_ids=tech_pattern_ids,
        )

        if not candidates:
            spider = self._global_spider.spider_dashboard()
            return {
                "ok": False,
                "mode": "global_spider",
                "niche": niche_key,
                "batch_limit": batch_limit,
                "scanned": 0,
                "passed_gate": 0,
                "archived": 0,
                "regions_scanned": discovery.get("regions_scanned", 0),
                "discovery": discovery,
                "global_spider": spider,
                "errors": ["no_candidates_add_seed_targets_or_GOOGLE_PLACES_API_KEY"],
                "message": (
                    "Global Spider: нет кандидатов. Добавьте seed_targets в "
                    "memory/global_spider_config.json или GOOGLE_PLACES_API_KEY."
                ),
            }

        scanned = 0
        passed = 0
        archived = 0
        skipped_tech = 0
        errors: list[str] = []
        countries: dict[str, int] = {}

        for url in candidates:
            try:
                result = self.scan_and_gate(url, niche=niche_key)
                target = result.get("target") or {}
                analysis = target.get("site_analysis") if isinstance(target.get("site_analysis"), dict) else {}
                if tech_pattern_ids and not self._global_spider.matches_tech_patterns(analysis, tech_pattern_ids):
                    skipped_tech += 1
                    continue
                scanned += 1
                cc = GlobalSpiderService.infer_country_code(url)
                countries[cc] = countries.get(cc, 0) + 1
                meta = target.get("meta") if isinstance(target.get("meta"), dict) else {}
                meta["scan_mode"] = "global_spider"
                meta["country_code"] = cc
                self._opportunity.update(target["id"], {"meta": meta})
                if result.get("lane") == _PROCESSING_LANE_HIGH:
                    passed += 1
                else:
                    archived += 1
            except ValueError as exc:
                errors.append(f"{url}: {exc}")

        junk_batch = self.process_junk_archive_cycle(limit=100)
        self.sync_payment_providers()
        network = self._network_portfolio(
            self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        )
        return {
            "ok": True,
            "mode": "global_spider",
            "niche": niche_key,
            "batch_limit": batch_limit,
            "scanned": scanned,
            "passed_gate": passed,
            "archived": archived,
            "skipped_tech_filter": skipped_tech,
            "regions_scanned": discovery.get("regions_scanned", 0),
            "countries_hit": countries,
            "discovery": discovery,
            "global_spider": self._global_spider.spider_dashboard(),
            "junk_micro_revenue_eur": junk_batch.get("revenue_eur", 0.0),
            "network": network,
            "errors": errors[:8],
            "message": (
                f"Global Spider: {scanned} URL · {len(countries)} стран · "
                f"журнал {passed} · архив {archived} · tech-skip {skipped_tech}"
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
        if self._business_mode and self._business_mode.is_sandbox():
            raise ValueError("sandbox_mode_withdrawal_disabled")
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
