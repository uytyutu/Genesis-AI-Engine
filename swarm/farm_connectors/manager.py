"""Connector Manager — scan live sources into one Opportunity pool."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .base import ConnectorStatus, FarmConnector, Tier
from .normalize import dedupe_opportunities, ensure_opportunity
from .opire_connector import OpireConnector
from .registry import CONNECTOR_CATALOG
from .stubs import StubConnector

DEFAULT_THRESHOLD = 72.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_analytics(pool: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    from swarm.farm_scan_analytics import build_scan_analytics
    from swarm.opire_farm import SUPPORTED_LANGS

    return build_scan_analytics(pool, threshold=threshold, supported_langs=SUPPORTED_LANGS)


def _stub_from_catalog(entry: dict[str, Any]) -> StubConnector:
    return StubConnector(
        id=str(entry["id"]),
        display_name=str(entry["display_name"]),
        tier=Tier(entry["tier"]),
        status=ConnectorStatus(entry["status"]),
        official_docs_url=str(entry.get("official_docs_url") or ""),
        notes_ru=str(entry.get("notes_ru") or ""),
    )


class ConnectorManager:
    def __init__(self, connectors: list[FarmConnector] | None = None) -> None:
        self._connectors: dict[str, FarmConnector] = {}
        if connectors is None:
            self._register_defaults()
        else:
            for c in connectors:
                self.register(c)

    def _register_defaults(self) -> None:
        self.register(OpireConnector())
        for entry in CONNECTOR_CATALOG:
            cid = str(entry["id"])
            if cid == "opire":
                continue
            self.register(_stub_from_catalog(entry))

    def register(self, connector: FarmConnector) -> None:
        self._connectors[connector.id] = connector

    def get(self, connector_id: str) -> FarmConnector | None:
        return self._connectors.get(connector_id)

    def catalog(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for entry in CONNECTOR_CATALOG:
            live = self._connectors.get(str(entry["id"]))
            row = dict(entry)
            if live is not None:
                row["runtime_status"] = (
                    live.status.value
                    if isinstance(live.status, ConnectorStatus)
                    else str(live.status)
                )
            else:
                row["runtime_status"] = entry.get("status")
            rows.append(row)
        return rows

    def scan(
        self,
        *,
        threshold: float = DEFAULT_THRESHOLD,
        limit: int = 40,
        tiers: frozenset[Tier] | None = None,
        live_only: bool = True,
    ) -> dict[str, Any]:
        """Aggregate → normalize → dedupe → confidence filter.

        Default: Tier A + live connectors only (never auto-enable B/C).
        """
        allowed_tiers = tiers or frozenset({Tier.A})
        errors: list[dict[str, str]] = []
        per_connector: list[dict[str, Any]] = []
        normalized: list[dict[str, Any]] = []

        for cid, conn in self._connectors.items():
            tier = conn.tier if isinstance(conn.tier, Tier) else Tier(str(conn.tier))
            status = (
                conn.status
                if isinstance(conn.status, ConnectorStatus)
                else ConnectorStatus(str(conn.status))
            )
            if tier not in allowed_tiers:
                continue
            if live_only and status != ConnectorStatus.LIVE:
                per_connector.append(
                    {
                        "id": cid,
                        "status": status.value,
                        "tier": tier.value,
                        "scanned": 0,
                        "skipped": "not_live",
                    }
                )
                continue
            try:
                raw_list = conn.fetch_raw()
            except Exception as exc:  # noqa: BLE001 — isolate connector failures
                errors.append({"connector": cid, "error": str(exc)})
                per_connector.append(
                    {
                        "id": cid,
                        "status": status.value,
                        "tier": tier.value,
                        "scanned": 0,
                        "error": str(exc),
                    }
                )
                continue

            count = 0
            for raw in raw_list:
                opp = conn.normalize(raw)
                if not opp:
                    continue
                cleaned = ensure_opportunity(opp)
                if cleaned:
                    normalized.append(cleaned)
                    count += 1
            per_connector.append(
                {
                    "id": cid,
                    "status": status.value,
                    "tier": tier.value,
                    "scanned": count,
                }
            )

        from swarm.farm_roi_score import apply_roi

        pooled = [apply_roi(dict(o)) for o in dedupe_opportunities(normalized)]
        take = [
            o
            for o in pooled
            if o.get("recommendation") == "TAKE"
            and float(o.get("overall_confidence_pct") or 0) >= threshold
            and not o.get("blockers")
        ]
        # Also accept high-confidence without explicit TAKE if blockers empty
        if not take:
            take = [
                o
                for o in pooled
                if float(o.get("overall_confidence_pct") or 0) >= threshold
                and not o.get("blockers")
            ]
        take.sort(
            key=lambda x: (
                -float(x.get("roi_rank_score") or 0),
                -float(x.get("overall_confidence_pct") or 0),
                -float(x.get("reward_usd") or 0),
            )
        )

        review_pool = sorted(
            pooled,
            key=lambda x: (
                -float(x.get("roi_rank_score") or 0),
                -float(x.get("overall_confidence_pct") or 0),
                -float(x.get("reward_usd") or 0),
            ),
        )
        # Compact reject reasons for CEO Review All
        for row in review_pool:
            blockers = list(row.get("blockers") or [])
            conf = float(row.get("overall_confidence_pct") or 0)
            rec = str(row.get("recommendation") or "SKIP")
            reasons: list[str] = []
            if blockers:
                reasons.extend(str(b) for b in blockers)
            if conf < threshold and rec != "TAKE":
                reasons.append(f"below_threshold_{int(threshold)}")
            if rec == "REVIEW":
                reasons.append("review_band")
            if rec == "SKIP" and not blockers and conf < threshold:
                reasons.append("low_confidence")
            row["reject_reasons"] = reasons
            row["band"] = (
                "take"
                if rec == "TAKE" and conf >= threshold and not blockers
                else "review"
                if conf >= 40 or rec == "REVIEW"
                else "skip"
            )

        bands = {
            "80+": sum(1 for o in pooled if float(o.get("overall_confidence_pct") or 0) >= 80),
            "60+": sum(1 for o in pooled if float(o.get("overall_confidence_pct") or 0) >= 60),
            "40+": sum(1 for o in pooled if float(o.get("overall_confidence_pct") or 0) >= 40),
            "20+": sum(1 for o in pooled if float(o.get("overall_confidence_pct") or 0) >= 20),
            "all": len(pooled),
        }

        return {
            "ok": len(errors) == 0 or len(pooled) > 0,
            "errors": errors,
            "source": "farm_connector_manager",
            "architecture_ru": (
                "Connector Manager → Normalizer → Confidence → CEO Approve → "
                "Execution → Draft PR → CEO Submit → Reward Protection → REAL"
            ),
            "law_ru": (
                "Farm Engine не зависит от одной площадки. Отключили коннектор — "
                "остальные продолжают. REAL только после payout confirmed."
            ),
            "tiers_scanned": sorted(t.value for t in allowed_tiers),
            "connectors": per_connector,
            "catalog": self.catalog(),
            "scanned": len(normalized),
            "after_dedupe": len(pooled),
            "filtered_out": max(0, len(pooled) - len(take)),
            "threshold": threshold,
            "candidates": take[:limit],
            "all_preview": review_pool[:12],
            "review_all": review_pool[:80],
            "confidence_bands": bands,
            "analytics": _build_analytics(review_pool, threshold),
            "at": _now(),
            "finance_law_ru": (
                "Estimated ≠ REAL. В REAL Profit Ledger только после payout_confirmed."
            ),
            "official_flow": "platform-official → Draft PR → CEO Submit → payout",
        }


def default_manager() -> ConnectorManager:
    return ConnectorManager()


def parse_opportunity_id(opportunity_id: str) -> tuple[str | None, str]:
    """Split `platform:native` → (platform, native). Bare id → (None, id)."""
    oid = (opportunity_id or "").strip()
    if ":" in oid:
        platform, native = oid.split(":", 1)
        if platform and native:
            return platform.lower(), native
    return None, oid
