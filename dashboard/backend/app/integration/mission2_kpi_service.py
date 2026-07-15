"""Mission 2 — операционная панель: KPI, конверсия, следующее действие."""

from __future__ import annotations

from typing import Any


def _meta(row: dict[str, Any]) -> dict[str, Any]:
    m = row.get("meta")
    return m if isinstance(m, dict) else {}


def _qualification_passed(row: dict[str, Any]) -> bool:
    qual = _meta(row).get("qualification")
    if isinstance(qual, dict) and qual.get("passed") is True:
        return True
    return row.get("qualification_passed") is True


def _audit_prepared(row: dict[str, Any]) -> bool:
    meta = _meta(row)
    if meta.get("audit_report_md"):
        return True
    return bool(str(row.get("audit_report_md") or "").strip())


def _letter_ready(row: dict[str, Any]) -> bool:
    if str(row.get("proposed_message") or "").strip():
        return True
    return str(row.get("outreach_status") or "") in (
        "pending_approval",
        "approved",
        "sent",
        "rejected",
        "draft",
    )


def _was_sent(row: dict[str, Any]) -> bool:
    if str(row.get("outreach_status") or "") == "sent":
        return True
    return str(row.get("status") or "") in ("contacted", "replied", "qualified", "won", "lost")


def _has_reply(row: dict[str, Any]) -> bool:
    return str(row.get("status") or "") in ("replied", "qualified", "won")


def _call_done(row: dict[str, Any]) -> bool:
    meta = _meta(row)
    if meta.get("call_done") is True or meta.get("call_scheduled") is True:
        return True
    if str(meta.get("stage") or "") == "call":
        return True
    return str(row.get("status") or "") in ("qualified", "won") and _has_reply(row)


def _kp_sent(row: dict[str, Any]) -> bool:
    if not _was_sent(row):
        return False
    return str(row.get("status") or "") in ("proposed", "qualified", "won", "replied")


def _pct(num: int, denom: int) -> int:
    if denom <= 0:
        return 0
    return min(100, round(100 * num / denom))


def _format_eur(amount: float) -> str:
    return f"{amount:,.2f} €".replace(",", " ").replace(".", ",")


def _bottleneck_ru(
    *,
    found: int,
    qualified: int,
    letters: int,
    sent: int,
    replies: int,
    won: int,
) -> str:
    if found >= 50 and qualified >= found * 0.8 and letters >= qualified * 0.5 and sent >= 20 and replies == 0:
        return (
            f"{found} лидов → {qualified} квалифицированы → {sent} писем → 0 ответов. "
            "Проблема не в Spider — проблема в письмах или оффере."
        )
    if sent >= 30 and replies >= 10 and won == 0:
        return (
            f"{sent} писем → {replies} ответов → 0 продаж. "
            "Проблема в оффере или цене — не в Brain и не в поиске."
        )
    if found > 0 and qualified < found * 0.2:
        return "Мало проходит квалификацию — проверьте Discovery и фильтры сайта/email."
    if qualified > 0 and letters < qualified * 0.3:
        return "Квалификация есть — тормоз на подготовке аудитов и писем (Outbox / prepare)."
    if letters > 0 and sent < letters * 0.3:
        return "Письма готовы — нужен Approve CEO и отправка."
    if sent > 0 and replies == 0:
        return "Письма ушли — ждём ответов или меняем текст/канал."
    if replies > 0 and won == 0:
        return "Есть диалог — дожимайте КП и цену до первой оплаты."
    if found == 0:
        return "Нет лидов в журнале — запустите ферму или Spider."
    return "Воронка движется — следующий шаг ниже."


def _next_action(
    rows: list[dict[str, Any]],
    *,
    outbox_pending: int,
    received_eur: float,
) -> dict[str, Any]:
    if outbox_pending > 0:
        return {
            "title_ru": "Следующее действие",
            "text_ru": f"Одобрить {outbox_pending} письм{'о' if outbox_pending == 1 else 'а' if outbox_pending < 5 else ''}",
            "detail_ru": "CEO Outbox — одна кнопка до отправки клиентам.",
            "href": "/acquisition",
            "priority": "high",
            "action_id": "approve_letters",
        }

    unqualified = [r for r in rows if not _qualification_passed(r)]
    if len(rows) < 5:
        need = max(5 - len(rows), 3)
        return {
            "title_ru": "Следующее действие",
            "text_ru": f"Подготовить {need} новых лидов",
            "detail_ru": "Запустите ферму или «Подготовить лиды» на /business.",
            "href": "/business",
            "priority": "high",
            "action_id": "prepare_leads",
        }

    qualified_no_letter = [r for r in rows if _qualification_passed(r) and not _letter_ready(r)]
    if qualified_no_letter:
        n = min(len(qualified_no_letter), 5)
        return {
            "title_ru": "Следующее действие",
            "text_ru": f"Подготовить аудит и письмо для {n} лидов",
            "detail_ru": "Qualification пройдена — нужен audit + КП.",
            "href": "/business",
            "priority": "medium",
            "action_id": "prepare_letters",
        }

    waiting = [
        r
        for r in rows
        if _was_sent(r) and not _has_reply(r) and str(r.get("status") or "") not in ("won", "lost")
    ]
    if waiting:
        name = str(waiting[0].get("company_name") or "клиента").strip()[:40]
        return {
            "title_ru": "Следующее действие",
            "text_ru": f"Ожидается ответ: {name}",
            "detail_ru": f"В очереди {len(waiting)} без ответа — follow-up или звонок.",
            "href": "/journal",
            "priority": "medium",
            "action_id": "await_reply",
        }

    if received_eur <= 0 and any(str(r.get("status") or "") == "won" for r in rows):
        return {
            "title_ru": "Следующее действие",
            "text_ru": "Подключить Stripe и выставить счёт Won-сделке",
            "detail_ru": "Won в журнале без «Получено» — нужна оплата через Stripe Live.",
            "href": "/finance",
            "priority": "high",
            "action_id": "stripe_invoice",
        }

    return {
        "title_ru": "Следующее действие",
        "text_ru": "Подготовить 5 новых лидов",
        "detail_ru": "Расширяйте воронку — первый € ближе при объёме и Approve.",
        "href": "/business",
        "priority": "low",
        "action_id": "grow_pipeline",
    }


def build_mission2_kpi(
    opportunities: list[dict[str, Any]] | None,
    *,
    received_eur: float = 0.0,
    training_eur: float = 0.0,
    outbox_pending: int = 0,
) -> dict[str, Any]:
    rows = opportunities or []

    found = len(rows)
    qualified = sum(1 for r in rows if _qualification_passed(r))
    audits = sum(1 for r in rows if _audit_prepared(r))
    letters = sum(1 for r in rows if _letter_ready(r))
    sent = sum(1 for r in rows if _was_sent(r))
    replies = sum(1 for r in rows if _has_reply(r))
    calls = sum(1 for r in rows if _call_done(r))
    kp_sent = sum(1 for r in rows if _kp_sent(r))
    won = sum(1 for r in rows if str(r.get("status") or "") == "won")
    received = round(float(received_eur or 0), 2)

    metrics = [
        {"id": "companies_found", "label_ru": "Компаний найдено", "value": found, "format": "count"},
        {"id": "after_qualification", "label_ru": "После квалификации", "value": qualified, "format": "count"},
        {"id": "audits_prepared", "label_ru": "Аудитов подготовлено", "value": audits, "format": "count"},
        {"id": "letters_ready", "label_ru": "Писем готово", "value": letters, "format": "count"},
        {"id": "sent", "label_ru": "Отправлено", "value": sent, "format": "count"},
        {"id": "replies", "label_ru": "Ответов", "value": replies, "format": "count"},
        {"id": "calls", "label_ru": "Созвонов", "value": calls, "format": "count"},
        {"id": "kp_sent", "label_ru": "КП отправлено", "value": kp_sent, "format": "count"},
        {"id": "won", "label_ru": "Won", "value": won, "format": "count"},
        {"id": "received", "label_ru": "Оплачено клиентом", "value": received, "format": "eur", "display": _format_eur(received)},
    ]

    conversions = [
        {
            "id": "discovery_qualified",
            "label_ru": "Discovery → Qualified",
            "from_label_ru": "найдено",
            "to_label_ru": "квалиф.",
            "percent": _pct(qualified, found),
            "from_count": found,
            "to_count": qualified,
        },
        {
            "id": "qualified_email",
            "label_ru": "Qualified → Email",
            "from_label_ru": "квалиф.",
            "to_label_ru": "письма",
            "percent": _pct(letters, qualified),
            "from_count": qualified,
            "to_count": letters,
        },
        {
            "id": "email_reply",
            "label_ru": "Email → Reply",
            "from_label_ru": "отправлено",
            "to_label_ru": "ответы",
            "percent": _pct(replies, sent),
            "from_count": sent,
            "to_count": replies,
        },
        {
            "id": "reply_sale",
            "label_ru": "Reply → Sale",
            "from_label_ru": "ответы",
            "to_label_ru": "Won",
            "percent": _pct(won, replies),
            "from_count": replies,
            "to_count": won,
        },
    ]

    bottleneck = _bottleneck_ru(
        found=found,
        qualified=qualified,
        letters=letters,
        sent=sent,
        replies=replies,
        won=won,
    )
    next_action = _next_action(rows, outbox_pending=outbox_pending, received_eur=received)

    nav_sections = [
        {"href": "/business/kpi", "label_ru": "Полная воронка", "hint_ru": "Все этапы KPI"},
        {"href": "/growth", "label_ru": "Конверсия", "hint_ru": "Где тормозит"},
        {"href": "/acquisition", "label_ru": "Outbox", "hint_ru": "Approve · отправка"},
        {"href": "/finance", "label_ru": "Получено", "hint_ru": "Stripe · банк"},
        {"href": "/journal", "label_ru": "Журнал", "hint_ru": "Все лиды"},
    ]

    return {
        "title_ru": "MISSION 2 — KPI",
        "subtitle_ru": "Операционная панель — не учебный журнал фермы",
        "metrics": metrics,
        "conversions": conversions,
        "bottleneck_ru": bottleneck,
        "next_action": next_action,
        "nav_sections": nav_sections,
        "training_eur": round(float(training_eur or 0), 2),
        "training_note_ru": (
            f"Учебный журнал фермы: {_format_eur(training_eur)} — симуляция, не смешивается с «Получено»."
        ),
    }


def build_sales_funnel_progress(
    opportunities: list[dict[str, Any]] | None,
    *,
    received_eur: float = 0.0,
    training_eur: float = 0.0,
    outbox_pending: int = 0,
) -> dict[str, Any]:
    """Compact funnel for money monitor — full KPI on /business/kpi."""
    kpi = build_mission2_kpi(
        opportunities,
        received_eur=received_eur,
        training_eur=training_eur,
        outbox_pending=outbox_pending,
    )
    by_id = {m["id"]: m for m in kpi["metrics"]}

    steps = [
        {"id": "leads_found", "label_ru": "Лидов найдено", "count": by_id["companies_found"]["value"], "icon": "🔍"},
        {
            "id": "qualification_passed",
            "label_ru": "Прошли квалификацию",
            "count": by_id["after_qualification"]["value"],
            "icon": "✓",
        },
        {"id": "letters_prepared", "label_ru": "Писем подготовлено", "count": by_id["letters_ready"]["value"], "icon": "✉️"},
        {"id": "sent", "label_ru": "Отправлено", "count": by_id["sent"]["value"], "icon": "📤"},
        {"id": "replies", "label_ru": "Ответов", "count": by_id["replies"]["value"], "icon": "💬"},
        {"id": "won", "label_ru": "Won", "count": by_id["won"]["value"], "icon": "🏆"},
        {
            "id": "received",
            "label_ru": "Получено",
            "count": None,
            "amount_eur": by_id["received"]["value"],
            "amount_label_ru": by_id["received"]["display"],
            "icon": "✅",
        },
    ]

    received = float(by_id["received"]["value"])
    return {
        "title_ru": "Настоящий прогресс",
        "headline_ru": kpi["next_action"]["text_ru"],
        "subtitle_ru": kpi["next_action"]["detail_ru"],
        "steps": steps,
        "training_note_ru": kpi["training_note_ru"],
        "next_action_href": kpi["next_action"]["href"],
    }
