"""Mission Proof — доказанные этапы до первого €."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def _meta(row: dict[str, Any]) -> dict[str, Any]:
    m = row.get("meta")
    return m if isinstance(m, dict) else {}


def _letter_sent(row: dict[str, Any]) -> bool:
    return str(row.get("outreach_status") or "") == "sent" or str(row.get("status") or "") in (
        "contacted",
        "replied",
        "qualified",
        "won",
    )


def build_mission_proof(
    opportunities: list[dict[str, Any]] | None,
    *,
    settlements: list[dict[str, Any]] | None = None,
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    rows = opportunities or []
    settles = settlements or []

    milestones: dict[str, Any] = {}
    if memory_dir:
        path = memory_dir / "owner_milestones.json"
        if path.is_file():
            try:
                milestones = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                milestones = {}

    stripe_paid = any(
        str(s.get("provider") or "") == "stripe" and float(s.get("amount_eur") or 0) > 0 for s in settles
    )
    any_paid = stripe_paid or bool(milestones.get("first_payment"))
    won_count = sum(1 for r in rows if str(r.get("status") or "") == "won")
    repeat_won = won_count > 1 or bool(milestones.get("repeat_client"))

    checks: list[tuple[str, str, Callable[[], bool]]] = [
        ("first_lead", "Первый лид", lambda: len(rows) >= 1),
        ("first_letter", "Первое письмо", lambda: any(_letter_sent(r) for r in rows)),
        ("first_reply", "Первый ответ", lambda: any(str(r.get("status") or "") in ("replied", "qualified", "won") for r in rows)),
        (
            "first_call",
            "Первый созвон",
            lambda: any(
                _meta(r).get("call_done")
                or str(r.get("status") or "") in ("qualified", "won")
                for r in rows
            ),
        ),
        ("first_client", "Первый клиент", lambda: won_count >= 1),
        ("first_payment", "Первая оплата", lambda: any_paid),
        ("repeat_client", "Повторный клиент", lambda: repeat_won),
    ]

    steps = []
    done_count = 0
    for step_id, label, fn in checks:
        done = bool(fn())
        if done:
            done_count += 1
        steps.append({"id": step_id, "label_ru": label, "done": done, "icon": "✅" if done else "⬜"})

    total = len(checks)
    progress_pct = round(100 * done_count / total) if total else 0

    return {
        "title_ru": "Mission Proof",
        "subtitle_ru": "Доказанные этапы — не ощущения",
        "progress_pct": progress_pct,
        "progress_label_ru": f"{done_count}/{total}",
        "steps": steps,
        "next_unproven_ru": next((s["label_ru"] for s in steps if not s["done"]), "Все этапы доказаны"),
    }
