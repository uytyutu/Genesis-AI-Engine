"""CEO Executive Dashboard — morning screen for Mission Control.

Not a new product feature: aggregates Virtus + Farm + Launch into one view.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _farm_stub() -> dict[str, Any]:
    """Placeholder so Today Focus / Health paint without Opire panel cost."""
    return {
        "ok": True,
        "deferred": True,
        "scanned": 0,
        "high_roi": 0,
        "approved": 0,
        "executed": 0,
        "draft_pr": 0,
        "merged": 0,
        "confirmed_usd": 0.0,
        "payout_usd": 0.0,
        "paid_count": 0,
        "win_rate": None,
        "avg_hours": None,
        "avg_earn_usd": None,
        "learning_closed": 0,
        "execution_success": {},
        "avg_execution_s": None,
        "finish_line": ["Approve", "Draft PR", "Merge", "Payout Confirmed"],
        "next_unlock_ru": "Polar / Algora — после Payout Confirmed",
        "bottleneck_ru": None,
    }


def _farm_snapshot(memory_dir: Path) -> dict[str, Any]:
    """Lightweight Farm KPIs — no live Opire rescan (use cached state)."""
    try:
        from swarm.opire_farm import OpireFarmEngine

        panel = OpireFarmEngine(memory_dir).panel(force_scan=False, enrich_top=0)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc)[:200],
            "scanned": 0,
            "high_roi": 0,
            "approved": 0,
            "executed": 0,
            "draft_pr": 0,
            "merged": 0,
            "confirmed_usd": 0.0,
            "payout_usd": 0.0,
            "win_rate": None,
            "avg_hours": None,
            "avg_earn_usd": None,
        }

    funnel = panel.get("funnel") or {}
    learning = panel.get("learning_ledger") or {}
    scan = panel.get("scan") or {}
    candidates = list(scan.get("candidates") or [])
    high_roi = sum(1 for c in candidates if int(c.get("roi_stars") or 0) >= 4)

    # Also count from review_all if candidates empty (cached scan)
    if not candidates:
        for c in scan.get("review_all") or []:
            if int(c.get("roi_stars") or 0) >= 4:
                high_roi += 1

    wins = int(learning.get("wins") or 0)
    losses = int(learning.get("losses") or 0)
    closed = wins + losses
    win_rate = round(100.0 * wins / closed, 1) if closed else None
    earned = _f(learning.get("earned_usd") or funnel.get("total_confirmed_usd"))
    exec_success = (
        panel.get("execution_success")
        if isinstance(panel.get("execution_success"), dict)
        else {}
    )

    return {
        "ok": True,
        "scanned": int(funnel.get("found") or scan.get("scanned") or 0),
        "high_roi": high_roi,
        "approved": int(funnel.get("ceo_approved") or 0),
        "executed": int(funnel.get("executed") or 0),
        "draft_pr": int(funnel.get("execution_ready_for_submit") or 0),
        "merged": int(funnel.get("pr_merged") or 0),
        "confirmed_usd": round(_f(funnel.get("total_confirmed_usd")), 2),
        "payout_usd": round(earned, 2),
        "paid_count": int(funnel.get("paid") or 0),
        "win_rate": win_rate,
        "avg_hours": learning.get("avg_actual_hours_win"),
        "avg_earn_usd": (
            round(earned / wins, 2) if wins else None
        ),
        "learning_closed": int(learning.get("closed") or 0),
        "execution_success": exec_success,
        "avg_execution_s": exec_success.get("avg_execution_s"),
        "finish_line": [
            "Approve",
            "Draft PR",
            "Merge",
            "Payout Confirmed",
        ],
        "next_unlock_ru": (
            "Polar / Algora / GitHub Bounties — только после первого Payout Confirmed"
        ),
        "bottleneck_ru": funnel.get("bottleneck_hint_ru"),
    }


def _virtus_snapshot(
    memory_dir: Path,
    *,
    finance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from app.integration.launch_readiness import build_business_kpis, build_sales_focus

    sales = build_sales_focus(memory_dir)
    kpis = build_business_kpis(memory_dir)
    fin = finance or {}

    items = {str(i.get("id")): i for i in (kpis.get("items") or []) if isinstance(i, dict)}
    website_sold = items.get("first_website_sold", {}).get("status") == "done"
    store_sold = items.get("first_store_sold", {}).get("status") == "done"
    repeat = items.get("first_repeat_client", {}).get("status") == "done"

    # Count published from business KPI details / sales kinds
    websites = sum(1 for c in (sales.get("clients") or []) if c.get("kind") == "website")
    stores = sum(1 for c in (sales.get("clients") or []) if c.get("kind") == "store")
    if website_sold and websites == 0:
        websites = 1
    if store_sold and stores == 0:
        stores = 1

    revenue = _f(
        fin.get("revenue_today_eur")
        if fin.get("revenue_total_eur") is None
        else fin.get("revenue_total_eur")
    )
    if revenue == 0:
        revenue = _f(fin.get("one_time_revenue_eur")) + _f(fin.get("mrr_eur") or fin.get("subscription_mrr_eur"))

    return {
        "ok": True,
        "first_clients": {
            "count": int(sales.get("count") or 0),
            "goal": int(sales.get("goal") or 5),
            "remaining": int(sales.get("remaining") or 0),
            "pct": int(sales.get("pct") or 0),
        },
        "revenue_eur": round(revenue, 2),
        "mrr_eur": round(_f(fin.get("mrr_eur") or fin.get("subscription_mrr_eur")), 2),
        "websites_sold": websites,
        "ai_stores_sold": stores,
        "repeat_clients": 1 if repeat else 0,
        "milestones": [
            {
                "id": "first_paying_client",
                "label": "Первый платящий клиент",
                "done": int(sales.get("count") or 0) >= 1,
            },
            {
                "id": "first_website",
                "label": "Первый опубликованный сайт",
                "done": website_sold or websites >= 1,
            },
            {
                "id": "first_ai_store",
                "label": "Первый AI Store",
                "done": store_sold or stores >= 1,
            },
            {
                "id": "first_repeat",
                "label": "Первый повторный клиент",
                "done": repeat,
            },
        ],
        "finish_line_ru": "После первого повторного клиента — открывается Gen2",
        "sales_focus": sales.get("focus"),
    }


def _company_snapshot(memory_dir: Path, *, light: bool = False) -> dict[str, Any]:
    from app.integration.launch_readiness import build_launch_readiness

    launch = build_launch_readiness(memory_dir)
    items = {str(i.get("id")): i for i in (launch.get("items") or []) if isinstance(i, dict)}
    golden = launch.get("golden_website_test") if isinstance(launch.get("golden_website_test"), dict) else {}

    def pct_for(item_id: str, fallback: int | None = None) -> int:
        row = items.get(item_id) or {}
        if row.get("status") == "done":
            return 100
        if fallback is not None:
            return fallback
        return 0

    # Soft scores for pending: use launch pct for overall, heuristics for perf/docs
    launch_pct = int(launch.get("pct") or 0)
    perf = 100 if items.get("performance", {}).get("status") == "done" else max(0, launch_pct - 5)
    docs = 100 if items.get("documentation", {}).get("status") == "done" else 65
    gwt_done = sum(1 for b in (golden.get("blockers") or []) if isinstance(b, dict) and b.get("status") == "done")
    gwt_total = max(1, len(golden.get("blockers") or []))
    gwt_pct = 100 if str(golden.get("status") or "").upper() == "PASS" else round(100.0 * gwt_done / gwt_total)

    if light:
        demo_gallery = {"ok": True, "status": "deferred", "deferred": True}
        commercial_acceptance = {"ok": True, "status": "deferred", "deferred": True}
        factory_metrics = {"ok": True, "deferred": True, "avg_total_e2e_s": None}
    else:
        try:
            from app.integration.demo_gallery_audit import build_demo_gallery_snapshot

            demo_gallery = build_demo_gallery_snapshot(memory_dir)
        except Exception as exc:  # noqa: BLE001
            demo_gallery = {"ok": False, "status": "FAIL", "error": str(exc)[:160]}

        try:
            from app.integration.commercial_acceptance_gate import (
                build_commercial_acceptance_gate,
            )

            commercial_acceptance = build_commercial_acceptance_gate()
        except Exception as exc:  # noqa: BLE001
            commercial_acceptance = {
                "ok": False,
                "status": "FAIL",
                "error": str(exc)[:160],
            }

        try:
            from app.integration.factory_metrics import summary as factory_metrics_summary

            factory_metrics = factory_metrics_summary(memory_dir, limit=100)
        except Exception as exc:  # noqa: BLE001
            factory_metrics = {"ok": False, "error": str(exc)[:160]}

    return {
        "ok": True,
        "launch_readiness_pct": launch_pct,
        "performance_pct": pct_for("performance", perf if items.get("performance") else 92),
        "documentation_pct": pct_for("documentation", docs),
        "golden_website_pct": gwt_pct,
        "website_launch": golden.get("website_launch") or launch.get("website_launch"),
        "ads_allowed": bool(golden.get("ads_allowed")),
        "golden_website_test": golden,
        "demo_gallery": demo_gallery,
        "commercial_acceptance": commercial_acceptance,
        "factory_metrics": factory_metrics,
        "phase": launch.get("phase"),
        "next": launch.get("next"),
        "focus": launch.get("focus"),
    }


def _today_focus(virtus: dict[str, Any], farm: dict[str, Any], company: dict[str, Any]) -> list[dict[str, Any]]:
    focus: list[dict[str, Any]] = []
    golden = company.get("golden_website_test") if isinstance(company.get("golden_website_test"), dict) else {}
    if str(golden.get("website_launch") or "").upper() == "BLOCKED":
        reasons = golden.get("reasons") or []
        focus.append(
            {
                "id": "golden_website_blockers",
                "track": "virtus",
                "label": "Fix Golden Website blockers before ads",
                "label_ru": f"Launch Blockers: {', '.join(str(r) for r in reasons) or 'Registration, Email, Pricing, Build'}",
                "href": "/launch",
                "priority": 0,
                "done": False,
            }
        )
    clients = (virtus.get("first_clients") or {}).get("count") or 0
    if clients < 1:
        focus.append(
            {
                "id": "find_first_client",
                "track": "virtus",
                "label": "Find first client",
                "label_ru": "Найти первого платящего клиента",
                "href": "/ceo-site",
                "priority": 1,
                "done": False,
            }
        )
    elif clients < 5:
        focus.append(
            {
                "id": "next_clients",
                "track": "virtus",
                "label": f"Next paying clients ({clients}/5)",
                "label_ru": f"Следующие клиенты ({clients}/5)",
                "href": "/acquisition",
                "priority": 1,
                "done": False,
            }
        )
    else:
        focus.append(
            {
                "id": "virtus_goal_met",
                "track": "virtus",
                "label": "First 5 clients — met",
                "label_ru": "Первые 5 клиентов — достигнуто",
                "href": "/global-analytics",
                "priority": 2,
                "done": True,
            }
        )

    paid = int(farm.get("paid_count") or 0)
    approved = int(farm.get("approved") or 0)
    draft = int(farm.get("draft_pr") or 0)
    merged = int(farm.get("merged") or 0)

    if paid < 1:
        if approved < 1:
            focus.append(
                {
                    "id": "review_top_roi",
                    "track": "farm",
                    "label": "Review Top ROI bounty",
                    "label_ru": "Approve Top ROI bounty",
                    "href": "/farm-engine",
                    "priority": 1,
                    "done": False,
                }
            )
        elif draft < 1:
            focus.append(
                {
                    "id": "first_draft_pr",
                    "track": "farm",
                    "label": "First Draft PR",
                    "label_ru": "Довести Approved → Draft PR",
                    "href": "/farm-engine",
                    "priority": 1,
                    "done": False,
                }
            )
        elif merged < 1:
            focus.append(
                {
                    "id": "first_merge",
                    "track": "farm",
                    "label": "First Merge",
                    "label_ru": "Submit PR → Merge",
                    "href": "/farm-engine",
                    "priority": 1,
                    "done": False,
                }
            )
        else:
            focus.append(
                {
                    "id": "first_payout",
                    "track": "farm",
                    "label": "Confirm first payout",
                    "label_ru": "Дожать Payout Confirmed",
                    "href": "/farm-engine",
                    "priority": 1,
                    "done": False,
                }
            )
    else:
        focus.append(
            {
                "id": "farm_payout_met",
                "track": "farm",
                "label": "First payout confirmed",
                "label_ru": "Первый payout подтверждён",
                "href": "/farm-engine",
                "priority": 2,
                "done": True,
            }
        )

    docs = int(company.get("documentation_pct") or 0)
    if docs < 80 and clients < 1:
        focus.append(
            {
                "id": "docs_light",
                "track": "company",
                "label": "Docs only if blocking a sale",
                "label_ru": "Документация — только если мешает продаже",
                "href": "/launch",
                "priority": 3,
                "done": False,
            }
        )

    focus.sort(key=lambda x: (int(x.get("priority") or 9), str(x.get("id"))))
    return focus[:5]


def _first_real_euro(
    memory_dir: Path,
    *,
    finance: dict[str, Any] | None = None,
    farm: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Platform inflection: first CONFIRMED euro (or Opire payout) reached?"""
    tax_eur = 0.0
    try:
        from swarm.finance_ledger import FinanceLedger

        tax_eur = _f(FinanceLedger(memory_dir).summary().get("tax_report_confirmed_eur"))
    except Exception:
        tax_eur = 0.0

    fin = finance or {}
    tax_report = fin.get("tax_report") if isinstance(fin.get("tax_report"), dict) else {}
    if tax_report.get("confirmed_eur") is not None:
        tax_eur = max(tax_eur, _f(tax_report.get("confirmed_eur")))

    farm = farm or {}
    opire_usd = _f(farm.get("confirmed_usd") or farm.get("payout_usd"))
    # Treat confirmed Opire USD as proof of real money cycle (FX-agnostic flag).
    reached = tax_eur > 0 or opire_usd > 0 or int(farm.get("paid_count") or 0) > 0
    return {
        "id": "first_real_euro",
        "label": "First Real Euro",
        "reached": reached,
        "status": "reached" if reached else "not_reached",
        "mark": "✅" if reached else "❌",
        "ledger_confirmed_eur": round(tax_eur, 2),
        "opire_confirmed_usd": round(opire_usd, 2),
        "detail_ru": (
            f"Ledger CONFIRMED {tax_eur:.2f} € · Opire confirmed {opire_usd:.2f} $"
            if reached
            else "Ещё нет подтверждённого поступления в Ledger / Opire payout"
        ),
        "note_ru": (
            "До First Real Euro большинство модулей — инфраструктура. "
            "После — доказанный коммерческий цикл."
        ),
    }


def _growth_ladder(
    *,
    first_euro: dict[str, Any],
    virtus: dict[str, Any],
) -> dict[str, Any]:
    """Business proof milestones — not feature checklists."""
    clients = int((virtus.get("first_clients") or {}).get("count") or 0)
    revenue = _f(virtus.get("revenue_eur"))
    # Prefer Ledger CONFIRMED when available on first_euro
    booked = max(revenue, _f(first_euro.get("ledger_confirmed_eur")))

    steps = [
        {
            "id": "first_real_euro",
            "label": "First Real Euro",
            "reached": bool(first_euro.get("reached")),
        },
        {
            "id": "first_10_customers",
            "label": "First 10 Customers",
            "reached": clients >= 10,
            "progress": f"{clients}/10",
        },
        {
            "id": "first_1000_eur",
            "label": "First 1 000 €",
            "reached": booked >= 1000,
            "progress": f"{booked:.0f}/1000 €",
        },
        {
            "id": "first_10000_eur",
            "label": "First 10 000 €",
            "reached": booked >= 10_000,
            "progress": f"{booked:.0f}/10000 €",
        },
        {
            "id": "self_sustaining",
            "label": "Self-sustaining",
            "reached": booked >= 10_000 and clients >= 10,
            "progress": "операционка покрывается доходом",
        },
    ]
    current = next((s for s in steps if not s["reached"]), steps[-1])
    return {
        "title": "Growth Ladder",
        "title_ru": "Лестница доказанного бизнеса",
        "steps": steps,
        "current": current,
        "note_ru": (
            "Этапы бизнеса, не фич. Двигаемся только по CONFIRMED / реальным клиентам."
        ),
    }


def _constraint_card(
    *,
    id: str,
    constraint: str,
    impact: str,
    action: str,
    href: str,
    priority: int,
    owner: str = "CEO",
    metric: str | None = None,
    answer_ru: str | None = None,
) -> dict[str, Any]:
    """THIS WEEK card — one bottleneck only (Phase D Proof)."""
    return {
        "phase": "D",
        "label": "THIS WEEK",
        "question_ru": "Какой один показатель сейчас сильнее всего ограничивает рост?",
        "id": id,
        "constraint": constraint,
        "metric": metric or constraint,
        "owner": owner,
        "impact": impact,
        "action": action,
        "answer_ru": answer_ru or impact,
        "href": href,
        "priority": priority,
        "rule_ru": "Нельзя одновременно бороться более чем с одним главным ограничителем.",
    }


def _weekly_constraint(
    *,
    first_euro: dict[str, Any],
    virtus: dict[str, Any],
    farm: dict[str, Any],
    company: dict[str, Any],
    health: dict[str, Any],
) -> dict[str, Any]:
    """One question: which single metric most limits growth this week?"""
    clients = int((virtus.get("first_clients") or {}).get("count") or 0)
    fm = company.get("factory_metrics") if isinstance(company.get("factory_metrics"), dict) else {}
    avg_e2e = fm.get("avg_total_e2e_s")
    es = farm.get("execution_success") if isinstance(farm.get("execution_success"), dict) else {}
    approved = int(es.get("approved") or farm.get("approved") or 0)
    started = int(es.get("started") or farm.get("executed") or 0)
    reds = [
        i
        for i in (health.get("items") or [])
        if isinstance(i, dict) and i.get("status") == "red"
    ]

    if reds:
        top = reds[0]
        label = str(top.get("label") or "System health")
        detail = str(top.get("detail_ru") or "")
        return _constraint_card(
            id=f"health_{top.get('id')}",
            constraint=label,
            impact=detail or f"{label} в red — блокирует рост.",
            action=f"Сначала починить {label}.",
            href=str(top.get("href") or "/executive"),
            priority=0,
            metric=label,
            answer_ru=detail,
        )
    if not first_euro.get("reached") and clients < 1:
        return _constraint_card(
            id="no_first_client",
            constraint="No paying customers",
            impact="Blocks First Real Euro",
            action="Acquire first customer.",
            href="/ceo-site",
            priority=1,
            metric="First paying client",
            answer_ru="Нет первого клиента — коммерческий цикл ещё не доказан.",
        )
    if not first_euro.get("reached"):
        return _constraint_card(
            id="first_real_euro",
            constraint="No confirmed payment",
            impact="Blocks First Real Euro",
            action="Get first Ledger CONFIRMED / Opire payout.",
            href="/finance",
            priority=1,
            metric="First Real Euro",
            answer_ru="Есть активность, но нет CONFIRMED поступления в Ledger.",
        )
    if approved > 0 and started == 0:
        return _constraint_card(
            id="opire_execution_gap",
            constraint="Approve without Execution",
            impact="Farm cycle unproven — no path to payout.",
            action="Start Execution on approved Opire items.",
            href="/farm-engine",
            priority=2,
            metric="Opire Start Rate",
            answer_ru="Approve без Execution — Farm не зарабатывает.",
        )
    if avg_e2e is not None and float(avg_e2e) > 120:
        return _constraint_card(
            id="factory_slow",
            constraint="Factory too slow",
            impact="Poor delivery experience.",
            action="Optimize slowest Factory stage (often Render).",
            href="/executive",
            priority=3,
            metric="Factory Avg Build",
            answer_ru=f"Avg E2E {avg_e2e}s выше целевых 120s — тормозит доставку.",
        )
    if clients < 10:
        return _constraint_card(
            id="customers_to_10",
            constraint=f"Only {clients}/10 customers",
            impact="Repeatability not yet proven.",
            action="Acquire next paying customer (sites / API / AI).",
            href="/ceo-site",
            priority=4,
            metric="Customers",
            answer_ru=f"Клиентов {clients}/10 — следующий этап Growth Ladder.",
        )
    return _constraint_card(
        id="scale_next",
        constraint="Conversion / retention",
        impact="Growth limited by funnel quality, not product gaps.",
        action="Improve site conversion and repeat customers.",
        href="/global-analytics",
        priority=5,
        metric="Conversion / retention",
        answer_ru=(
            "Базовые доказательства есть — смотри конверсию сайта и повторных клиентов."
        ),
    )


def _health_item(
    *,
    id: str,
    label: str,
    status: str,
    detail_ru: str,
    href: str,
) -> dict[str, Any]:
    mark = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(status, "⚪")
    return {
        "id": id,
        "label": label,
        "status": status,
        "mark": mark,
        "detail_ru": detail_ru,
        "href": href,
    }


def _dashboard_health(
    memory_dir: Path,
    *,
    virtus: dict[str, Any],
    farm: dict[str, Any],
    company: dict[str, Any],
    finance: dict[str, Any] | None,
    first_euro: dict[str, Any],
) -> dict[str, Any]:
    """5-second CEO strip — where is the real problem."""
    items: list[dict[str, Any]] = []

    # Finance
    tax = 0.0
    demo = bool((finance or {}).get("demo_mode"))
    try:
        tr = (finance or {}).get("tax_report") if isinstance((finance or {}).get("tax_report"), dict) else {}
        tax = _f(tr.get("confirmed_eur"))
        if tax == 0:
            from swarm.finance_ledger import FinanceLedger

            tax = _f(FinanceLedger(memory_dir).summary().get("tax_report_confirmed_eur"))
    except Exception:
        pass
    if demo:
        items.append(
            _health_item(
                id="finance",
                label="Finance",
                status="yellow",
                detail_ru="Demo mode — налоговые цифры не из Ledger REAL",
                href="/finance",
            )
        )
    elif tax > 0:
        items.append(
            _health_item(
                id="finance",
                label="Finance",
                status="green",
                detail_ru=f"Ledger CONFIRMED {tax:.2f} €",
                href="/finance",
            )
        )
    else:
        items.append(
            _health_item(
                id="finance",
                label="Finance",
                status="green",
                detail_ru="Контур чистый · 0 € CONFIRMED (ожидаемо до первой оплаты)",
                href="/finance",
            )
        )

    # Factory
    fm = company.get("factory_metrics") if isinstance(company.get("factory_metrics"), dict) else {}
    avg_e2e = fm.get("avg_total_e2e_s")
    if fm.get("ok") is False:
        items.append(
            _health_item(
                id="factory",
                label="Factory",
                status="yellow",
                detail_ru=str(fm.get("error") or "Нет метрик"),
                href="/executive",
            )
        )
    elif avg_e2e is not None and float(avg_e2e) > 180:
        items.append(
            _health_item(
                id="factory",
                label="Factory",
                status="yellow",
                detail_ru=f"Avg E2E {avg_e2e}s > 180s KPI",
                href="/executive",
            )
        )
    else:
        items.append(
            _health_item(
                id="factory",
                label="Factory",
                status="green",
                detail_ru=(
                    f"Metrics ok · avg E2E {avg_e2e}s"
                    if avg_e2e is not None
                    else "Telemetry ready · ждём живые сборки"
                ),
                href="/executive",
            )
        )

    # Country Desk
    places_active = False
    places_detail = "Country Desk без активного Places-блока"
    try:
        from app.integration.places_quota_cooldown import places_quota_status

        pq = places_quota_status(memory_dir)
        places_active = bool(pq.get("active"))
        if places_active:
            places_detail = str(pq.get("blocker_ru") or "Google Places quota exceeded")
    except Exception:
        places_detail = "Places quota status unavailable"
    items.append(
        _health_item(
            id="country_desk",
            label="Country Desk",
            status="yellow" if places_active else "green",
            detail_ru=places_detail,
            href="/acquisition",
        )
    )

    # Revenue Lab
    items.append(
        _health_item(
            id="revenue_lab",
            label="Revenue Lab",
            status="green" if first_euro.get("reached") else "yellow",
            detail_ru=(
                "First Real Euro reached"
                if first_euro.get("reached")
                else "Источники прозрачны · ждём First Real Euro"
            ),
            href="/revenue",
        )
    )

    # Opire
    es = farm.get("execution_success") if isinstance(farm.get("execution_success"), dict) else {}
    approved = int(es.get("approved") or farm.get("approved") or 0)
    started = int(es.get("started") or farm.get("executed") or 0)
    if not farm.get("ok", True):
        items.append(
            _health_item(
                id="opire",
                label="Opire",
                status="red",
                detail_ru=str(farm.get("error") or "Farm panel error"),
                href="/farm-engine",
            )
        )
    elif approved > 0 and started == 0:
        items.append(
            _health_item(
                id="opire",
                label="Opire",
                status="red",
                detail_ru="Approve без Execution — конвейер не стартовал",
                href="/farm-engine",
            )
        )
    elif farm.get("bottleneck_ru"):
        items.append(
            _health_item(
                id="opire",
                label="Opire",
                status="yellow",
                detail_ru=str(farm.get("bottleneck_ru")),
                href="/farm-engine",
            )
        )
    else:
        items.append(
            _health_item(
                id="opire",
                label="Opire",
                status="green",
                detail_ru=(
                    f"Approved {approved} · Started {started} · Draft {farm.get('draft_pr') or 0}"
                ),
                href="/farm-engine",
            )
        )

    # Awin
    awin_ok = False
    try:
        import os

        awin_ok = bool(os.getenv("AWIN_API_TOKEN", "").strip()) and bool(
            os.getenv("AWIN_PUBLISHER_ID", "").strip()
        )
    except Exception:
        awin_ok = False
    items.append(
        _health_item(
            id="awin",
            label="Awin",
            status="green" if awin_ok else "red",
            detail_ru=(
                "Ключи на месте · ждём первую комиссию в Ledger"
                if awin_ok
                else "Нет AWIN_API_TOKEN / AWIN_PUBLISHER_ID"
            ),
            href="/revenue",
        )
    )

    reds = sum(1 for i in items if i["status"] == "red")
    yellows = sum(1 for i in items if i["status"] == "yellow")
    return {
        "title": "CEO Dashboard Health",
        "items": items,
        "summary": {
            "green": sum(1 for i in items if i["status"] == "green"),
            "yellow": yellows,
            "red": reds,
        },
        "headline_ru": (
            f"{reds} red · {yellows} yellow — сначала red"
            if reds
            else (
                f"{yellows} yellow — смотри узкие места"
                if yellows
                else "Все контуры зелёные или в ожидаемом нуле"
            )
        ),
    }


def build_ceo_executive_dashboard(
    memory_dir: Path,
    *,
    finance: dict[str, Any] | None = None,
    include_deployment: bool = False,
    stage: str = "core",
) -> dict[str, Any]:
    """
    stage=core  — Today Focus + Health + Virtus fast path (≤2s target)
    stage=full  — includes live Farm panel + heavy company audits
    """
    root = Path(memory_dir)
    light = str(stage or "core").strip().lower() != "full"
    virtus = _virtus_snapshot(root, finance=finance)
    farm = _farm_stub() if light else _farm_snapshot(root)
    company = _company_snapshot(root, light=light)
    today = _today_focus(virtus, farm, company)
    first_euro = _first_real_euro(root, finance=finance, farm=farm)
    health = _dashboard_health(
        root,
        virtus=virtus,
        farm=farm,
        company=company,
        finance=finance,
        first_euro=first_euro,
    )
    growth = _growth_ladder(first_euro=first_euro, virtus=virtus)
    weekly = _weekly_constraint(
        first_euro=first_euro,
        virtus=virtus,
        farm=farm,
        company=company,
        health=health,
    )

    # RC1: SSH/DNS/HTTP deployment probes must NOT block morning CEO open.
    # Live probe: GET /api/owner/deployment-manager (lazy from UI).
    if include_deployment:
        try:
            from app.integration.deployment_manager import build_deployment_manager

            deployment_manager = build_deployment_manager()
            deployment_inspector = deployment_manager.get("inspector") or {}
            frontend_deployment = deployment_inspector.get("legacy_card") or {
                "id": "frontend_deployment",
                "title": "Frontend Deployment",
                "status": deployment_manager.get("status") or "unknown",
                "mark": deployment_manager.get("mark") or "🟡",
                "detail_ru": deployment_manager.get("explanation_ru") or "",
                "deploy": "UNKNOWN",
            }
            if isinstance(frontend_deployment, dict):
                frontend_deployment = {
                    **frontend_deployment,
                    "inspector_status": deployment_inspector.get("status"),
                    "manager_status": deployment_manager.get("status"),
                    "explanation_ru": deployment_manager.get("explanation_ru"),
                    "actions": deployment_manager.get("actions") or [],
                }
        except Exception as exc:  # noqa: BLE001
            deployment_manager = {
                "id": "deployment_manager",
                "title": "Deployment Manager",
                "status": "unknown",
                "mark": "🟡",
                "explanation_ru": f"manager failed: {type(exc).__name__}",
                "actions": [],
                "policy": {"production": "ovh", "preview": "vercel"},
            }
            try:
                from app.integration.deployment_inspector import build_deployment_inspector

                deployment_inspector = build_deployment_inspector()
                frontend_deployment = deployment_inspector.get("legacy_card") or {
                    "id": "frontend_deployment",
                    "status": "unknown",
                    "mark": "🟡",
                    "detail_ru": str(exc),
                    "deploy": "UNKNOWN",
                }
            except Exception as exc2:  # noqa: BLE001
                deployment_inspector = {
                    "id": "deployment_inspector",
                    "status": "unknown",
                    "mark": "🟡",
                    "explanation_ru": f"inspector failed: {type(exc2).__name__}",
                    "actions": [],
                }
                frontend_deployment = {
                    "id": "frontend_deployment",
                    "title": "Frontend Deployment",
                    "status": "unknown",
                    "mark": "🟡",
                    "detail_ru": f"deploy check failed: {type(exc).__name__}",
                    "deploy": "UNKNOWN",
                }
    else:
        deployment_manager = {
            "id": "deployment_manager",
            "title": "Deployment Manager",
            "status": "deferred",
            "mark": "🟡",
            "explanation_ru": (
                "Live OVH/SSH probe загружается отдельно — не блокирует утренний пульт. "
                "Откройте карточку или GET /api/owner/deployment-manager."
            ),
            "actions": [
                {
                    "id": "load_live",
                    "label_ru": "Проверить production (live)",
                    "href": "/api/owner/deployment-manager",
                }
            ],
            "policy": {
                "production": "ovh",
                "preview": "vercel",
                "chain_ru": "Local → Vercel Preview → OVH Production",
            },
            "deferred": True,
        }
        deployment_inspector = {
            "id": "deployment_inspector",
            "title": "Deployment Inspector",
            "status": "deferred",
            "mark": "🟡",
            "explanation_ru": "Deferred — see Deployment Manager live endpoint.",
            "actions": [],
            "deferred": True,
        }
        frontend_deployment = {
            "id": "frontend_deployment",
            "title": "Frontend Deployment",
            "status": "deferred",
            "mark": "🟡",
            "detail_ru": "Deferred for CEO Dashboard speed.",
            "deploy": "DEFERRED",
            "deferred": True,
        }

    return {
        "ok": True,
        "title": "CEO Dashboard",
        "subtitle": "Утром открываешь — сразу понятно, чем заниматься сегодня",
        "phase": {
            "id": "D",
            "name": "Proof",
            "name_ru": "Доказательство",
            "goal_ru": "Доказать, что Virtus Core умеет стабильно зарабатывать реальные деньги.",
            "mode": "evidence_driven",
            "rule_ru": "Нельзя одновременно бороться более чем с одним главным ограничителем.",
            "frozen_ru": "Новые функции — только если они снимают текущий weekly constraint.",
            "kpis": [
                "First Real Euro",
                "First 10 Customers",
                "Factory Stability",
                "Country Desk funnel → Paid",
                "Opire cycle → Payout",
            ],
        },
        "deployment_manager": deployment_manager,
        "deployment_inspector": deployment_inspector,
        "frontend_deployment": frontend_deployment,
        "virtus": virtus,
        "farm": farm,
        "company": company,
        "today_focus": today,
        "first_real_euro": first_euro,
        "growth_ladder": growth,
        "weekly_constraint": weekly,
        "dashboard_health": health,
        "kpi_law_ru": (
            "Один вопрос в неделю: какой показатель сильнее всего ограничивает рост? "
            "Решения — по живой статистике. Новые SSOT-правила не добавляем."
        ),
        "tracks": {
            "virtus": "Доказать коммерческую модель → Gen2 после повторного клиента",
            "farm": "Доказать цикл заработка → Polar/Algora после Payout Confirmed",
        },
        "income_contours": {
            "title_ru": "Три независимых контура дохода",
            "farms": [
                {
                    "id": "opire_farm",
                    "label": "Opire Farm",
                    "role_ru": "Исполняет bounty → Draft PR → Merge → Payout",
                    "href": "/farm-engine",
                },
                {
                    "id": "alpha_hunter",
                    "label": "Alpha Hunter",
                    "role_ru": "Ищет новые рынки (не выполняет Opire)",
                    "href": "/alpha-hunter",
                },
                {
                    "id": "sales_farm",
                    "label": "Sales Farm",
                    "role_ru": "Country Desk → Stripe → Factory → REAL €",
                    "href": "/acquisition",
                },
            ],
            "sink_ru": "Все подтверждённые деньги → REAL Ledger (Financial Truth).",
        },
        "stage": "core" if light else "full",
        "updated_at": _now(),
    }


def build_ceo_farm_section(memory_dir: Path) -> dict[str, Any]:
    """Lazy Farm KPIs for CEO Dashboard after first paint."""
    farm = _farm_snapshot(Path(memory_dir))
    return {"ok": True, "farm": farm, "updated_at": _now()}
