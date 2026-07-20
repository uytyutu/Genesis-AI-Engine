#!/usr/bin/env python3
"""CEO pulse — answers daily owner questions from Cursor (no PowerShell required for CEO).

Usage (repo root):
  py -3.12 scripts/ceo_pulse.py
  py -3.12 scripts/ceo_pulse.py pulse
  py -3.12 scripts/ceo_pulse.py caps
  py -3.12 scripts/ceo_pulse.py pending
  py -3.12 scripts/ceo_pulse.py money
  py -3.12 scripts/ceo_pulse.py health

Does not start uvicorn. Reads local memory + services directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _ctx():
    from app.env_loader import load_local_env

    load_local_env()
    from app.integration.context import get_integration

    return get_integration()


def cmd_pulse() -> int:
    ctx = _ctx()
    lines: list[str] = []
    lines.append("=== CEO Pulse (Cursor) ===")

    # 1 Critical problems / health
    try:
        check = ctx.system_check.run()
        ok = bool(check.get("ok", check.get("healthy", True)))
        issues = check.get("issues") or check.get("failures") or []
        if isinstance(issues, list) and issues:
            lines.append(f"1. Критические проблемы: ДА ({len(issues)})")
            for row in issues[:5]:
                lines.append(f"   - {row if isinstance(row, str) else json.dumps(row, ensure_ascii=False)[:120]}")
        else:
            lines.append(f"1. Критические проблемы: {'НЕТ' if ok else 'СМОТРИ /check'}")
    except Exception as exc:
        lines.append(f"1. Критические проблемы: не удалось проверить ({exc})")

    # 2 New money
    try:
        mon = ctx.micro_farm.money_monitor_panel(lite=True)
        rm = (mon or {}).get("real_money") or {}
        paid = ((rm.get("paid_by_client") or {}).get("amount_label_ru")) or (
            (mon or {}).get("actual_revenue") or {}
        ).get("paid_by_client_label_ru")
        avail = ((rm.get("available") or rm.get("received") or {}).get("amount_label_ru")) or (
            (mon or {}).get("actual_revenue") or {}
        ).get("withdrawable_label_ru")
        lines.append(f"2. Деньги: оплачено клиентом {paid or '—'} · к выводу {avail or '—'}")
        funnel = (mon or {}).get("path_a_funnel") or {}
        if funnel.get("headline_ru"):
            lines.append(f"   Path A: {funnel['headline_ru']}")
    except Exception as exc:
        lines.append(f"2. Деньги: ошибка ({exc})")

    # 3 Leads needing decision
    try:
        queue = ctx.acquisition.approval_queue(limit=10)
        lines.append(f"3. Лиды на решение: {len(queue)}")
        for row in queue[:5]:
            name = row.get("company_name") or row.get("name") or row.get("id")
            lines.append(f"   - {name} [{row.get('id') or row.get('opportunity_id')}]")
    except Exception as exc:
        lines.append(f"3. Лиды: ошибка ({exc})")

    # 4 Pending approvals (orders awaiting payment / reviews)
    try:
        pending_orders = ctx.sales.list_pending()
        reviews = ctx.reviews.list_pending()
        lines.append(
            f"4. Подтверждения: заказы awaiting={len(pending_orders)} · отзывы={len(reviews)}"
        )
        for o in pending_orders[:5]:
            lines.append(
                f"   - order {o.get('order_id')} {o.get('business_name')} "
                f"{o.get('price_label') or o.get('price_eur')} €"
            )
    except Exception as exc:
        lines.append(f"4. Подтверждения: ошибка ({exc})")

    # 5 System / workers
    try:
        farm = ctx.micro_farm.dashboard_lite() if hasattr(ctx.micro_farm, "dashboard_lite") else {}
        if not farm and hasattr(ctx.micro_farm, "dashboard"):
            farm = ctx.micro_farm.dashboard()
        workers = farm.get("workers") or farm.get("status") or farm.get("state")
        lines.append(f"5. Работает: farm={workers if workers is not None else 'см. Genesis.exe / farm'}")
    except Exception as exc:
        lines.append(f"5. Работает: ошибка ({exc})")

    # External caps summary
    try:
        from app.integration.external_capabilities import snapshot

        snap = snapshot()
        lines.append(
            f"External caps: enabled={snap['summary']['enabled']}/"
            f"{snap['summary']['total']} (Mission1 ready={snap['summary']['ready_adapters']})"
        )
    except Exception:
        pass

    lines.append("")
    lines.append("Cursor actions:")
    lines.append("  py -3.12 scripts/ceo_pulse.py pending")
    lines.append("  py -3.12 scripts/ceo_pulse.py money")
    lines.append("  py -3.12 scripts/ceo_pulse.py caps")
    lines.append("  py -3.12 scripts/ceo_pulse.py health")
    print("\n".join(lines))
    return 0


def cmd_pending() -> int:
    ctx = _ctx()
    queue = ctx.acquisition.approval_queue(limit=30)
    orders = ctx.sales.list_pending()
    print(f"Approval queue: {len(queue)}")
    for row in queue:
        print(
            json.dumps(
                {
                    "id": row.get("id") or row.get("opportunity_id"),
                    "company": row.get("company_name") or row.get("name"),
                    "status": row.get("outreach_status"),
                },
                ensure_ascii=False,
            )
        )
    print(f"Pending orders: {len(orders)}")
    for o in orders:
        print(
            json.dumps(
                {
                    "order_id": o.get("order_id"),
                    "business": o.get("business_name"),
                    "status": o.get("status"),
                    "price": o.get("price_label") or o.get("price_eur"),
                },
                ensure_ascii=False,
            )
        )
    return 0


def cmd_money() -> int:
    ctx = _ctx()
    mon = ctx.micro_farm.money_monitor_panel(lite=False)
    print(json.dumps(mon, ensure_ascii=False, indent=2, default=str)[:8000])
    return 0


def cmd_caps() -> int:
    from app.integration.external_capabilities import snapshot

    print(json.dumps(snapshot(), ensure_ascii=False, indent=2))
    return 0


def cmd_health() -> int:
    ctx = _ctx()
    check = ctx.system_check.run()
    print(json.dumps(check, ensure_ascii=False, indent=2, default=str)[:8000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="CEO pulse for Cursor")
    p.add_argument(
        "command",
        nargs="?",
        default="pulse",
        choices=("pulse", "pending", "money", "caps", "health"),
    )
    args = p.parse_args()
    return {
        "pulse": cmd_pulse,
        "pending": cmd_pending,
        "money": cmd_money,
        "caps": cmd_caps,
        "health": cmd_health,
    }[args.command]()


if __name__ == "__main__":
    raise SystemExit(main())
