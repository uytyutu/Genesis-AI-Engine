"""Mission 2 — воронка продаж: реальный прогресс CEO, не учебный ledger."""

from __future__ import annotations

from typing import Any


def _qualification_passed(row: dict[str, Any]) -> bool:
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    qual = meta.get("qualification")
    if isinstance(qual, dict) and qual.get("passed") is True:
        return True
    if row.get("qualification_passed") is True:
        return True
    return False


def _letters_prepared(row: dict[str, Any]) -> bool:
    if str(row.get("proposed_message") or "").strip():
        return True
    status = str(row.get("outreach_status") or "")
    return status in ("pending_approval", "approved", "sent", "rejected", "draft")


def _was_sent(row: dict[str, Any]) -> bool:
    if str(row.get("outreach_status") or "") == "sent":
        return True
    return str(row.get("status") or "") in ("contacted", "replied", "qualified", "won", "lost")


def _has_reply(row: dict[str, Any]) -> bool:
    return str(row.get("status") or "") in ("replied", "qualified", "won")


def build_sales_funnel_progress(
    opportunities: list[dict[str, Any]] | None,
    *,
    received_eur: float = 0.0,
    training_eur: float = 0.0,
) -> dict[str, Any]:
    """CEO progress board — counts from journal, received from external payments only."""
    rows = opportunities or []

    leads_found = len(rows)
    qualification_passed = sum(1 for r in rows if _qualification_passed(r))
    letters_prepared = sum(1 for r in rows if _letters_prepared(r))
    sent = sum(1 for r in rows if _was_sent(r))
    replies = sum(1 for r in rows if _has_reply(r))
    won = sum(1 for r in rows if str(r.get("status") or "") == "won")
    received = round(float(received_eur or 0), 2)

    steps = [
        {
            "id": "leads_found",
            "label_ru": "Лидов найдено",
            "count": leads_found,
            "icon": "🔍",
        },
        {
            "id": "qualification_passed",
            "label_ru": "Прошли квалификацию",
            "count": qualification_passed,
            "icon": "✓",
        },
        {
            "id": "letters_prepared",
            "label_ru": "Писем подготовлено",
            "count": letters_prepared,
            "icon": "✉️",
        },
        {
            "id": "sent",
            "label_ru": "Отправлено",
            "count": sent,
            "icon": "📤",
        },
        {
            "id": "replies",
            "label_ru": "Ответов",
            "count": replies,
            "icon": "💬",
        },
        {
            "id": "won",
            "label_ru": "Won",
            "count": won,
            "icon": "🏆",
        },
        {
            "id": "received",
            "label_ru": "Получено",
            "count": None,
            "amount_eur": received,
            "amount_label_ru": f"{received:,.2f} €".replace(",", " ").replace(".", ","),
            "icon": "✅",
        },
    ]

    headline_ru = (
        f"Получено: {received:,.2f} € — модель доказана".replace(",", " ").replace(".", ",")
        if received > 0
        else "Прогресс к первому € — воронка B2B"
    )

    return {
        "title_ru": "Настоящий прогресс",
        "headline_ru": headline_ru,
        "subtitle_ru": "Считаем лиды и сделки — не учебный журнал фермы",
        "steps": steps,
        "training_note_ru": (
            f"{training_eur:,.2f} € в учебном журнале фермы — симуляция конвейера, не ваш доход. "
            "Здесь — путь к реальному €."
        ).replace(",", " ").replace(".", ","),
    }
