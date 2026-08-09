"""Launch Readiness + Success Path KPIs — Gen1 Feature Freeze → Beta → Public Launch.

Primary KPI: how many successful clients completed the full real path.
Not: how many features are ready.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_overrides(memory_dir: Path) -> dict[str, Any]:
    path = Path(memory_dir) / "launch_readiness.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _status(done: bool, *, detail: str, pending_detail: str | None = None) -> dict[str, Any]:
    return {
        "status": "done" if done else "pending",
        "detail": detail if done else (pending_detail or detail),
    }


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_demo_shop_order(order: dict[str, Any]) -> bool:
    mode = str(order.get("payment_mode") or order.get("checkout_mode") or "").lower()
    if mode in {"demo", "sandbox"}:
        return True
    if order.get("demo") is True:
        return True
    note = str(order.get("note") or "").lower()
    if "demo payment" in note or "payment_mode=demo" in note:
        return True
    if order.get("live_charge") is False and str(order.get("checkout_phase") or "") == "demo":
        return True
    return False


def _is_store_sales_order(order: dict[str, Any]) -> bool:
    kind = str(order.get("product_kind") or order.get("kind") or "").lower()
    if kind in {"store", "ai_store", "shop"}:
        return True
    pid = str(order.get("product_id") or order.get("package_id") or "").lower()
    name = str(
        order.get("product_name") or order.get("title") or order.get("package_name") or ""
    ).lower()
    blob = f"{pid} {name}"
    return any(x in blob for x in ("store", "shop", "aistore", "ai store", "ai-store"))


def _iter_sales_orders(memory_dir: Path) -> list[dict[str, Any]]:
    sales_root = Path(memory_dir) / "sales_orders"
    if not sales_root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sales_root.glob("*.json"):
        try:
            order = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(order, dict):
            rows.append(order)
    return rows


def build_launch_readiness(memory_dir: Path) -> dict[str, Any]:
    """Mission Control — gate before Public Launch (after Gen1 Feature Freeze)."""
    from app.factory.visual_intelligence import visual_intelligence_ready
    from app.integration.platform_global_analytics import (
        _email_test_success,
        _scan_commerce_files,
        _stripe_oauth_connected_count,
    )
    from app.integration.store_admin.invoice_pdf_service import count_issued_invoices
    from app.integration.store_admin.shipping_api_service import shipping_api_ready

    rows = _scan_commerce_files(memory_dir)
    overrides = _load_overrides(memory_dir)
    vie = visual_intelligence_ready(memory_dir)
    commerce_ok = (
        _stripe_oauth_connected_count(rows) > 0
        or _email_test_success(rows)
        or count_issued_invoices(memory_dir) > 0
        or shipping_api_ready(memory_dir)
    )
    core = [
        {"id": "architecture", "label": "Architecture", **_status(True, detail="Mission Control · Worlds")},
        {
            "id": "website_factory",
            "label": "Website Factory",
            **_status(True, detail="Path A · Composer · Compliance"),
        },
        {
            "id": "store_factory",
            "label": "Store Factory",
            **_status(True, detail="Premium Generation · Store Admin"),
        },
        {"id": "vector", "label": "Vector", **_status(True, detail="Setup guidance · Business Ready")},
        {
            "id": "commerce",
            "label": "Commerce",
            **_status(True, detail="Stripe · SMTP · PDF · Shipping (Gen1)"),
        },
        {
            "id": "visual_engine",
            "label": "Visual Engine",
            **_status(
                vie,
                detail="Style · Asset · Motion · Gate ≥ 90",
                pending_detail="Visual Intelligence Engine must pass Quality Gate",
            ),
        },
    ]

    perf_override = overrides.get("performance") if isinstance(overrides.get("performance"), dict) else {}
    beta_override = overrides.get("beta_feedback") if isinstance(overrides.get("beta_feedback"), dict) else {}
    docs_override = overrides.get("documentation") if isinstance(overrides.get("documentation"), dict) else {}
    client_card_override = (
        overrides.get("client_card") if isinstance(overrides.get("client_card"), dict) else {}
    )

    beta_clients = int(beta_override.get("beta_clients") or overrides.get("beta_clients") or 0)
    perf_done = str(perf_override.get("status") or "").lower() == "done"
    beta_done = str(beta_override.get("status") or "").lower() == "done" or beta_clients >= 5
    docs_done = str(docs_override.get("status") or "").lower() == "done"

    client_card_done = str(client_card_override.get("status") or "").lower() == "done"
    if not client_card_done:
        try:
            from app.integration.customer_identity.support_center import SupportCenterService

            # Green when Support Center module is importable and Business ID format works.
            from app.integration.customer_identity.business_id import generate_business_id

            bid = generate_business_id()
            client_card_done = bid.startswith("VC-") and len(bid) >= 10
            _ = SupportCenterService
        except Exception:
            client_card_done = False

    launch_items = [
        *core,
        {
            "id": "client_card",
            "label": "Client Card · Business ID",
            **_status(
                client_card_done,
                detail=str(
                    client_card_override.get("detail")
                    or "Support Center · Business ID · timeline · notes"
                ),
                pending_detail="Support Client Card + public Business ID for first clients",
            ),
        },
        {
            "id": "performance",
            "label": "Performance",
            **_status(
                perf_done,
                detail=str(perf_override.get("detail") or "Lighthouse / CWV / mobile OK"),
                pending_detail="Generation speed · load · Lighthouse · Core Web Vitals · mobile",
            ),
        },
        {
            "id": "beta_feedback",
            "label": "Beta Feedback",
            **_status(
                beta_done,
                detail=str(
                    beta_override.get("detail")
                    or f"{beta_clients} beta client(s) · feedback loop active"
                ),
                pending_detail="5–10 real clients using the platform + UX fixes from drop-offs",
            ),
        },
        {
            "id": "documentation",
            "label": "Documentation",
            **_status(
                docs_done,
                detail=str(docs_override.get("detail") or "Owner + merchant launch docs ready"),
                pending_detail="Order · Stripe · SMTP · Website · Store · FAQ",
            ),
        },
    ]

    from app.integration.golden_website_launch import build_golden_website_launch

    golden = build_golden_website_launch(memory_dir)
    golden_pass = str(golden.get("status") or "").upper() == "PASS"

    # Ads gate: Golden Website Test sits above Performance/Docs vanity greens.
    launch_items.append(
        {
            "id": "golden_website_test",
            "label": "Golden Website Test",
            **_status(
                golden_pass,
                detail=str(golden.get("focus") or "PASS — ads unlocked"),
                pending_detail=(
                    "BLOCKED: "
                    + ", ".join(golden.get("reasons") or ["Registration", "Email", "Pricing", "Build"])
                ),
            ),
        }
    )
    all_pre = all(i.get("status") == "done" for i in launch_items)
    launch_items.append(
        {
            "id": "launch_ready",
            "label": "Website Launch",
            **_status(
                all_pre and golden_pass,
                detail="Public Launch unlocked — advertise Website",
                pending_detail=(
                    f"Website Launch BLOCKED — {', '.join(golden.get('reasons') or [])}"
                    if not golden_pass
                    else "All Launch Readiness items must be green first"
                ),
            ),
        }
    )

    done = sum(1 for i in launch_items if i.get("status") == "done")
    total = len(launch_items)
    next_item = next((i for i in launch_items if i.get("status") != "done"), None)
    ads_blocked = not golden_pass
    return {
        "ok": True,
        "title": "Launch Readiness",
        "phase": "feature_freeze",
        "done": done,
        "total": total,
        "pct": round(100.0 * done / total) if total else 0,
        "next": next_item,
        "items": launch_items,
        "commerce_signals": commerce_ok,
        "beta_clients": beta_clients,
        "golden_website_test": golden,
        "website_launch": golden.get("website_launch"),
        "ads_allowed": bool(golden.get("ads_allowed")),
        "focus": (
            f"Website Launch BLOCKED — {', '.join(golden.get('reasons') or [])}. No ads until PASS."
            if ads_blocked
            else (
                "Public Launch only when every item is green. "
                "Until then: Sales → Real Beta → UX → Performance → Polish — no Gen2."
            )
        ),
        "note": (
            "Override Golden Website PASS via memory/launch_readiness.json → golden_website_test. "
            "Also: performance / beta_feedback / documentation."
        ),
        "updated_at": _now(),
    }


# Moments that count as "first real value" for the merchant (earliest wins).
_FIRST_VALUE_FIELDS: tuple[tuple[str, str], ...] = (
    ("first_value_at", "client_said_value"),
    ("value_confirmed_at", "client_said_value"),
    ("published_at", "published"),
    ("first_shop_order_at", "first_shop_order"),
    ("first_order_at", "first_shop_order"),
    ("first_email_at", "first_email"),
    ("first_lead_at", "first_lead"),
    ("first_inquiry_at", "first_lead"),
    ("commerce_connected_at", "commerce_connected"),
)


def _first_value_event(order: dict[str, Any]) -> tuple[datetime, str] | None:
    best: tuple[datetime, str] | None = None
    for key, kind in _FIRST_VALUE_FIELDS:
        ts = _parse_iso(order.get(key))
        if not ts:
            continue
        if best is None or ts < best[0]:
            best = (ts, kind)
    return best


def build_sales_focus(memory_dir: Path) -> dict[str, Any]:
    """Priority #1: first 5 real paying clients (each auto-joins Beta)."""
    overrides = _load_overrides(memory_dir)
    ov = overrides.get("sales_focus") if isinstance(overrides.get("sales_focus"), dict) else {}
    goal = int(ov.get("goal") or 5)

    clients: list[dict[str, Any]] = []
    seen: set[str] = set()
    for order in _iter_sales_orders(memory_dir):
        if order.get("payment_mode") == "demo" or order.get("demo") is True:
            continue
        status = str(order.get("status") or "").lower()
        paid_like = bool(order.get("paid_at")) or status in {
            "paid",
            "completed",
            "delivered",
            "published",
            "in_production",
        }
        if not paid_like:
            continue
        key = str(
            order.get("client_id")
            or order.get("customer_email")
            or order.get("email")
            or order.get("order_id")
            or order.get("id")
            or ""
        ).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        niche = str(order.get("niche") or order.get("industry") or order.get("segment") or "").strip()
        clients.append(
            {
                "id": key,
                "order_id": order.get("order_id") or order.get("id"),
                "niche": niche or None,
                "kind": "store" if _is_store_sales_order(order) else "website",
                "paid_at": order.get("paid_at") or order.get("created_at"),
                "beta": True,
            }
        )

    if isinstance(ov.get("clients"), list):
        for row in ov["clients"]:
            if not isinstance(row, dict):
                continue
            key = str(row.get("id") or row.get("email") or row.get("name") or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            clients.append(
                {
                    "id": key,
                    "order_id": row.get("order_id"),
                    "niche": row.get("niche") or row.get("industry"),
                    "kind": row.get("kind") or "website",
                    "paid_at": row.get("paid_at"),
                    "beta": True,
                }
            )

    count = len(clients)
    niches_target = [
        {"id": "restaurant", "label": "Ресторан / кафе"},
        {"id": "beauty", "label": "Салон красоты"},
        {"id": "auto", "label": "Автосервис"},
        {"id": "handwerk", "label": "Handwerk / мастер"},
        {"id": "professional", "label": "Стоматология или юрист"},
    ]
    return {
        "ok": True,
        "title": "First 5 Clients",
        "subtitle": "Главный приоритет: продажи. Каждый клиент = реальная Beta.",
        "priority": 1,
        "goal": goal,
        "count": count,
        "remaining": max(0, goal - count),
        "pct": min(100, round(100.0 * count / goal)) if goal else 0,
        "on_goal": count >= goal,
        "clients": clients[:20],
        "target_niches": niches_target,
        "path": [
            "Sales",
            "Real Beta",
            "UX fixes",
            "Performance",
            "Polish",
            "Public Launch",
        ],
        "after_each_sale": [
            "Где клиент запутался?",
            "Сколько заняла настройка? (Time To Launch / First Value Time)",
            "Где попросил помощь?",
        ],
        "focus": (
            f"Найти первых {goal} клиентов — не тысячи. "
            "Ресторан · салон · автосервис · Handwerk · стоматология/юрист."
        ),
        "updated_at": _now(),
    }


def build_first_value_time(memory_dir: Path) -> dict[str, Any]:
    """Minutes from purchase → first real value (publish, order, email, lead, or client said so)."""
    overrides = _load_overrides(memory_dir)
    fvt_ov = (
        overrides.get("first_value_time")
        if isinstance(overrides.get("first_value_time"), dict)
        else {}
    )
    goal_min = float(fvt_ov.get("goal_min") or 60)

    minutes: list[float] = []
    by_kind: dict[str, int] = {}
    samples: list[dict[str, Any]] = []

    for order in _iter_sales_orders(memory_dir):
        if order.get("payment_mode") == "demo" or order.get("demo") is True:
            continue
        start = _parse_iso(order.get("paid_at")) or _parse_iso(order.get("created_at"))
        if not start:
            continue
        event = _first_value_event(order)
        if not event:
            continue
        value_at, kind = event
        delta_min = (value_at - start).total_seconds() / 60.0
        if delta_min < 0 or delta_min > 60 * 24 * 30:
            continue
        minutes.append(delta_min)
        by_kind[kind] = by_kind.get(kind, 0) + 1
        samples.append(
            {
                "order_id": order.get("order_id") or order.get("id"),
                "kind": kind,
                "minutes": round(delta_min, 1),
            }
        )

    if not minutes:
        median = None
        avg = None
        on_goal = None
        status = "pending"
        detail = (
            f"Цель < {int(goal_min)} мин до первой пользы — пока нет измерений. "
            "Фиксируйте published_at / first_order / first_email / first_lead / first_value_at."
        )
    else:
        ordered = sorted(minutes)
        median = round(ordered[len(ordered) // 2], 1)
        avg = round(sum(minutes) / len(minutes), 1)
        on_goal = median <= goal_min
        status = "done" if on_goal else "watch"
        detail = (
            f"Медиана {median:.0f} мин до первой пользы (цель < {int(goal_min)})"
            if on_goal
            else f"Медиана {median:.0f} мин — выше цели < {int(goal_min)} мин"
        )

    if str(fvt_ov.get("status") or "").lower() == "done":
        status = "done"
        on_goal = True
        detail = str(fvt_ov.get("detail") or detail)

    return {
        "ok": True,
        "title": "First Value Time",
        "subtitle": (
            "От покупки до момента, когда клиент впервые получает реальную пользу "
            "(сайт опубликован, магазин запущен, заказ, письмо, заявка)."
        ),
        "median_min": median,
        "avg_min": avg,
        "goal_min": goal_min,
        "on_goal": on_goal,
        "status": status,
        "samples": len(minutes),
        "by_kind": by_kind,
        "recent": samples[-20:],
        "detail": detail,
        "focus": (
            "Чем быстрее первая польза — тем выше шанс, что клиент останется. "
            f"Цель < {int(goal_min)} мин."
        ),
        "updated_at": _now(),
    }


def build_time_to_launch(memory_dir: Path) -> dict[str, Any]:
    """Time from purchase/paid → published. Goals: website < 30m · store < 60m."""
    overrides = _load_overrides(memory_dir)
    ttl_ov = overrides.get("time_to_launch") if isinstance(overrides.get("time_to_launch"), dict) else {}

    website_minutes: list[float] = []
    store_minutes: list[float] = []
    samples: list[dict[str, Any]] = []

    for order in _iter_sales_orders(memory_dir):
        if order.get("payment_mode") == "demo" or order.get("demo") is True:
            continue
        published_at = _parse_iso(order.get("published_at"))
        if not published_at:
            continue
        start = _parse_iso(order.get("paid_at")) or _parse_iso(order.get("created_at"))
        if not start:
            continue
        delta_min = (published_at - start).total_seconds() / 60.0
        if delta_min < 0 or delta_min > 60 * 24 * 14:
            continue
        is_store = _is_store_sales_order(order)
        (store_minutes if is_store else website_minutes).append(delta_min)
        samples.append(
            {
                "order_id": order.get("order_id") or order.get("id"),
                "kind": "store" if is_store else "website",
                "minutes": round(delta_min, 1),
            }
        )

    def _summary(vals: list[float], goal: float) -> dict[str, Any]:
        if not vals:
            return {
                "samples": 0,
                "median_min": None,
                "avg_min": None,
                "goal_min": goal,
                "on_goal": None,
                "status": "pending",
                "detail": f"Цель < {int(goal)} мин — пока нет измерений",
            }
        ordered = sorted(vals)
        mid = ordered[len(ordered) // 2]
        avg = sum(vals) / len(vals)
        on_goal = mid <= goal
        return {
            "samples": len(vals),
            "median_min": round(mid, 1),
            "avg_min": round(avg, 1),
            "goal_min": goal,
            "on_goal": on_goal,
            "status": "done" if on_goal else "watch",
            "detail": (
                f"Медиана {mid:.0f} мин (цель < {int(goal)})"
                if on_goal
                else f"Медиана {mid:.0f} мин — выше цели < {int(goal)} мин"
            ),
        }

    website = _summary(website_minutes, float(ttl_ov.get("website_goal_min") or 30))
    store = _summary(store_minutes, float(ttl_ov.get("store_goal_min") or 60))
    if str(ttl_ov.get("website_status") or "").lower() == "done":
        website.update({"status": "done", "on_goal": True})
        website["detail"] = str(ttl_ov.get("website_detail") or website["detail"])
    if str(ttl_ov.get("store_status") or "").lower() == "done":
        store.update({"status": "done", "on_goal": True})
        store["detail"] = str(ttl_ov.get("store_detail") or store["detail"])

    return {
        "ok": True,
        "title": "Time To Launch",
        "subtitle": "От покупки до публикации готового сайта / магазина",
        "website": website,
        "store": store,
        "goals": {"website_min": 30, "store_min": 60},
        "samples": samples[-20:],
        "focus": "Конкурентное преимущество: сайт < 30 мин · магазин < 60 мин.",
        "updated_at": _now(),
    }


def build_business_kpis(memory_dir: Path) -> dict[str, Any]:
    """7-stage success path — real clients, not feature count."""
    from app.integration.platform_global_analytics import (
        _email_test_success,
        _scan_commerce_files,
        _stripe_oauth_connected_count,
    )
    from app.integration.store_admin.shipping_api_service import count_shipping_api_activity

    root = Path(memory_dir)
    overrides = _load_overrides(root)
    kpi_ov = overrides.get("business_kpis") if isinstance(overrides.get("business_kpis"), dict) else {}
    rows = _scan_commerce_files(root)

    email_ok = _email_test_success(rows)
    ship = count_shipping_api_activity(root)
    shipments = int(ship.get("shipments_created") or 0)
    delivered = int(ship.get("delivered") or 0)

    paid_website = 0
    paid_store = 0
    for order in _iter_sales_orders(root):
        if order.get("payment_mode") == "demo" or order.get("demo") is True:
            continue
        status = str(order.get("status") or "").lower()
        paid_like = bool(order.get("paid_at")) or status in {
            "paid",
            "completed",
            "delivered",
            "published",
            "in_production",
        }
        if not paid_like:
            continue
        if _is_store_sales_order(order):
            paid_store += 1
        else:
            paid_website += 1

    real_shop_orders = 0
    buyers_with_multi = 0
    admin = root / "store_admin"
    if admin.is_dir():
        for op in admin.glob("*/orders.json"):
            try:
                data = json.loads(op.read_text(encoding="utf-8"))
                orders = data.get("orders") if isinstance(data, dict) else []
                if not isinstance(orders, list):
                    continue
                for o in orders:
                    if isinstance(o, dict) and not _is_demo_shop_order(o):
                        real_shop_orders += 1
            except (OSError, json.JSONDecodeError):
                pass
        for cp in admin.glob("*/customers/index.json"):
            try:
                data = json.loads(cp.read_text(encoding="utf-8"))
                buyers = (
                    data
                    if isinstance(data, list)
                    else data.get("buyers") or data.get("customers") or []
                )
                for b in buyers or []:
                    if not isinstance(b, dict):
                        continue
                    real_orders = [
                        o
                        for o in (b.get("orders") or [])
                        if isinstance(o, dict) and not _is_demo_shop_order(o)
                    ]
                    if len(real_orders) >= 2:
                        buyers_with_multi += 1
            except (OSError, json.JSONDecodeError):
                pass

    def kpi(
        kid: str,
        stage: int,
        label: str,
        hit: bool,
        detail: str,
        pending: str,
    ) -> dict[str, Any]:
        ov = kpi_ov.get(kid) if isinstance(kpi_ov.get(kid), dict) else {}
        if str(ov.get("status") or "").lower() == "done":
            return {
                "id": kid,
                "stage": stage,
                "label": label,
                "status": "done",
                "detail": str(ov.get("detail") or detail),
            }
        if str(ov.get("status") or "").lower() == "pending":
            hit = False
        return {
            "id": kid,
            "stage": stage,
            "label": label,
            "status": "done" if hit else "pending",
            "detail": detail if hit else pending,
        }

    items = [
        kpi(
            "first_website_sold",
            1,
            "Этап 1 · Первый проданный сайт",
            paid_website > 0,
            f"{paid_website} реальн. заказ(ов) Website",
            "Не тестовый — реальный клиент купил сайт",
        ),
        kpi(
            "first_store_sold",
            2,
            "Этап 2 · Первый AI Store",
            paid_store > 0,
            f"{paid_store} реальн. заказ(ов) AI Store",
            "Первая реальная продажа AI Store",
        ),
        kpi(
            "first_shop_order",
            3,
            "Этап 3 · Первый заказ в магазине клиента",
            real_shop_orders > 0,
            f"{real_shop_orders} заказ(ов) у клиентов (не demo)",
            "Реальный заказ через магазин клиента — не Demo",
        ),
        kpi(
            "first_email_sent",
            4,
            "Этап 4 · Первое успешное письмо",
            email_ok,
            "SMTP / Test Email success",
            "Успешная отправка письма клиенту магазина",
        ),
        kpi(
            "first_shipment",
            5,
            "Этап 5 · Первая реальная доставка",
            shipments > 0 or delivered > 0,
            f"{shipments} отправлений · {delivered} delivered",
            "Create Shipment + tracking у реального заказа",
        ),
        kpi(
            "first_positive_review",
            6,
            "Этап 6 · Первый положительный отзыв",
            bool(kpi_ov.get("first_positive_review", {}).get("status") == "done")
            or bool(kpi_ov.get("first_reviews", {}).get("status") == "done"),
            str(
                (kpi_ov.get("first_positive_review") or kpi_ov.get("first_reviews") or {}).get(
                    "detail"
                )
                or "Положительный отзыв получен"
            ),
            "Первый положительный отзыв реального клиента",
        ),
        kpi(
            "first_repeat_client",
            7,
            "Этап 7 · Первый повторный клиент",
            buyers_with_multi > 0,
            f"{buyers_with_multi} покупатель(ей) с 2+ заказами",
            "Повторный заказ — модель начинает работать",
        ),
    ]

    done = sum(1 for i in items if i["status"] == "done")
    next_stage = next((i for i in items if i["status"] != "done"), None)
    return {
        "ok": True,
        "title": "Success Path",
        "subtitle": "Сколько успешных клиентов прошло полный путь — не сколько функций готово",
        "primary_kpi": "successful_full_path_clients",
        "done": done,
        "total": len(items),
        "items": items,
        "next": next_stage,
        "shop_orders_real": real_shop_orders,
        "stripe_connected_stores": _stripe_oauth_connected_count(rows),
        "focus": (
            "Сейчас приоритет — продажи (первые 5 клиентов). "
            "Каждый клиент = Beta. Полный путь остаётся главным KPI успеха продукта."
        ),
        "updated_at": _now(),
    }
