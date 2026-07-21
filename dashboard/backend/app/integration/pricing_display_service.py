"""Public pricing display — editable JSON, no hardcoded tariffs in code."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


class PricingDisplayService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._config_path = self._memory / "pricing_display.json"
        self._analytics_path = self._memory / "pricing_analytics.jsonl"

    def get_display(self, market_code: str | None = None) -> dict:
        # Always resolve from market_registry / commerce so /services matches /order.
        from app.integration.public_truth_catalog import build_truth_pricing_display

        code = (market_code or "DE").strip() or "DE"
        return build_truth_pricing_display(market_code=code)

    @staticmethod
    def _is_mission1_public_truth(data: dict) -> bool:
        """Mission 1: only mission1-truth catalog or CEO-published compatible JSON."""
        version = str(data.get("version") or "")
        if version.startswith("mission1-truth"):
            return True
        subs = data.get("subscriptions") or []
        for s in subs:
            if s.get("id") in ("basic", "pro", "business", "enterprise") and s.get("available"):
                return False
            if s.get("price_eur_month") in (49, 99, 199):
                return False
        for cat in data.get("service_categories") or []:
            for item in cat.get("items") or []:
                label = str(item.get("price_label") or "")
                if "450" in label or "1 800" in label or "1 800" in label.replace(" ", ""):
                    return False
        return bool(data.get("service_categories") or data.get("subscriptions"))

    def log_event(self, *, event: str, tier_id: str | None, page: str, meta: dict | None = None) -> None:
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "tier_id": tier_id,
            "page": page,
            "meta": meta or {},
        }
        self._memory.mkdir(parents=True, exist_ok=True)
        with self._analytics_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def read_events(self, *, limit: int = 50_000) -> list[dict]:
        """Read recent pricing/path-A analytics rows (jsonl)."""
        if not self._analytics_path.is_file():
            return []
        rows: list[dict] = []
        try:
            with self._analytics_path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(row, dict):
                        rows.append(row)
                        if len(rows) >= limit:
                            # Keep last `limit` by reading all then slicing if file huge
                            pass
        except OSError:
            return []
        if len(rows) > limit:
            return rows[-limit:]
        return rows

    def path_a_funnel_summary(self) -> dict:
        """Aggregate Path A commerce funnel for CEO Money Monitor."""
        events = self.read_events()
        counts: dict[str, int] = {
            "tier_page_view": 0,
            "tier_select": 0,
            "premium_preview_view": 0,
            "upgrade_click": 0,
            "checkout_start": 0,
            "checkout_paid": 0,
            "specialization_selected": 0,
            "vxp_product_shown": 0,
            # A2.1 — Order Experience funnel
            "order_started": 0,
            "step_1_completed": 0,
            "step_2_completed": 0,
            "step_3_completed": 0,
            "step_4_completed": 0,
            "draft_restored": 0,
            "checkout_summary_viewed": 0,
            "checkout_confirmed": 0,
            "stripe_redirect_started": 0,
            "stripe_return_success": 0,
            "stripe_return_cancel": 0,
            "order_completed": 0,
        }
        niches: dict[str, int] = {}
        products: dict[str, int] = {}
        specializations: dict[str, int] = {}
        tiers: dict[str, int] = {}

        for row in events:
            ev = str(row.get("event") or "").strip()
            if ev in counts:
                counts[ev] += 1
            tier = row.get("tier_id")
            if tier and ev in ("tier_select", "tier_page_view", "premium_preview_view"):
                key = str(tier)
                tiers[key] = tiers.get(key, 0) + 1
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            niche = str(meta.get("niche") or meta.get("niche_id") or "").strip()
            if niche and ev in (
                "tier_page_view",
                "vxp_product_shown",
                "specialization_selected",
                "premium_preview_view",
                "order_started",
                "step_1_completed",
                "checkout_summary_viewed",
            ):
                niches[niche] = niches.get(niche, 0) + 1
            product = str(meta.get("product_id") or "").strip()
            if product and ev == "vxp_product_shown":
                products[product] = products.get(product, 0) + 1
            spec = str(
                meta.get("specialization_id") or meta.get("specialization") or ""
            ).strip()
            if spec and ev == "specialization_selected":
                specializations[spec] = specializations.get(spec, 0) + 1

        def _top(d: dict[str, int], n: int = 8) -> list[dict]:
            return [
                {"id": k, "count": v}
                for k, v in sorted(d.items(), key=lambda x: (-x[1], x[0]))[:n]
            ]

        steps = [
            {
                "id": "tier_page_view",
                "label_ru": "Открыли выбор тарифа",
                "count": counts["tier_page_view"],
                "icon": "👁",
            },
            {
                "id": "tier_select",
                "label_ru": "Выбрали тариф",
                "count": counts["tier_select"],
                "icon": "📦",
            },
            {
                "id": "premium_preview_view",
                "label_ru": "Premium Preview",
                "count": counts["premium_preview_view"],
                "icon": "🖼",
            },
            {
                "id": "upgrade_click",
                "label_ru": "Upgrade → Premium",
                "count": counts["upgrade_click"],
                "icon": "⬆",
            },
            {
                "id": "checkout_start",
                "label_ru": "Checkout",
                "count": counts["checkout_start"],
                "icon": "💳",
            },
            {
                "id": "checkout_paid",
                "label_ru": "Оплатили",
                "count": counts["checkout_paid"],
                "icon": "✅",
            },
        ]
        views = max(counts["tier_page_view"], 1)
        paid = counts["checkout_paid"]

        # Prefer dedicated OE events; fall back to Path A twins so older rows still count.
        oe_redirect = counts["stripe_redirect_started"] or counts["checkout_start"]
        oe_success = counts["stripe_return_success"] or counts["checkout_paid"]
        oe_completed = counts["order_completed"] or oe_success
        oe_started = max(counts["order_started"], 1)
        order_experience_funnel = {
            "title_ru": "Order Experience Funnel",
            "headline_ru": (
                f"Старт: {counts['order_started']} · оплат: {oe_success} · "
                f"отмен Stripe: {counts['stripe_return_cancel']}"
            ),
            "subtitle_ru": (
                "Где покупатель останавливается в оформлении /order — "
                "шаги → summary → Stripe → оплата."
            ),
            "steps": [
                {
                    "id": "order_started",
                    "label_ru": "Order Started",
                    "count": counts["order_started"],
                    "icon": "1",
                },
                {
                    "id": "step_1_completed",
                    "label_ru": "Step 1",
                    "count": counts["step_1_completed"],
                    "icon": "2",
                },
                {
                    "id": "step_2_completed",
                    "label_ru": "Step 2",
                    "count": counts["step_2_completed"],
                    "icon": "3",
                },
                {
                    "id": "step_3_completed",
                    "label_ru": "Step 3",
                    "count": counts["step_3_completed"],
                    "icon": "4",
                },
                {
                    "id": "step_4_completed",
                    "label_ru": "Step 4",
                    "count": counts["step_4_completed"],
                    "icon": "5",
                },
                {
                    "id": "checkout_summary_viewed",
                    "label_ru": "Checkout Summary",
                    "count": counts["checkout_summary_viewed"],
                    "icon": "📋",
                },
                {
                    "id": "checkout_confirmed",
                    "label_ru": "Confirmed",
                    "count": counts["checkout_confirmed"],
                    "icon": "☑",
                },
                {
                    "id": "stripe_redirect_started",
                    "label_ru": "Stripe Redirect",
                    "count": oe_redirect,
                    "icon": "→",
                },
                {
                    "id": "stripe_return_success",
                    "label_ru": "Payment Success",
                    "count": oe_success,
                    "icon": "€",
                },
                {
                    "id": "order_completed",
                    "label_ru": "Order Completed",
                    "count": oe_completed,
                    "icon": "✅",
                },
            ],
            "conversion_view_to_paid_pct": round(
                100.0 * oe_success / oe_started, 1
            ),
            "event_totals": {
                k: counts[k]
                for k in (
                    "order_started",
                    "step_1_completed",
                    "step_2_completed",
                    "step_3_completed",
                    "step_4_completed",
                    "draft_restored",
                    "checkout_summary_viewed",
                    "checkout_confirmed",
                    "stripe_redirect_started",
                    "stripe_return_success",
                    "stripe_return_cancel",
                    "order_completed",
                )
            },
            "next_action_href": "/order",
        }

        return {
            "title_ru": "Path A — воронка сайта",
            "headline_ru": (
                f"Оплат: {paid} · просмотров тарифа: {counts['tier_page_view']}"
            ),
            "subtitle_ru": (
                "Данные с /site, /order и Visual Experience — решения по нишам от фактов."
            ),
            "steps": steps,
            "conversion_view_to_paid_pct": round(100.0 * paid / views, 1),
            "top_niches": _top(niches),
            "top_products": _top(products),
            "top_specializations": _top(specializations),
            "tier_mix": _top(tiers),
            "event_totals": counts,
            "next_action_href": "/site",
            "order_experience_funnel": order_experience_funnel,
        }
