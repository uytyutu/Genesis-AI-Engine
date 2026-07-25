"""Live Activity Monitor — facts only (Reality over Simulation).

Shows what Country Desk / revenue path did recently — not capability cards.
Unknown delivery / commissions stay 0 or status=unknown — never invented.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _in_window(dt: datetime | None, start: datetime) -> bool:
    return bool(dt and dt >= start)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _step(
    *,
    id: str,
    label_ru: str,
    count: int,
    last_at: datetime | None,
    status: str,
    detail_ru: str = "",
) -> dict[str, Any]:
    return {
        "id": id,
        "label_ru": label_ru,
        "count": int(count),
        "last_at": _iso(last_at),
        "status": status,  # success | error | idle | unknown
        "detail_ru": detail_ru,
    }


def _row_times(row: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    found = _parse_dt(str(row.get("found_at") or row.get("created_at") or ""))
    updated = _parse_dt(str(row.get("updated_at") or "")) or found
    return found, updated


def _is_reply(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").lower()
    outreach = str(row.get("outreach_status") or "").lower()
    if status in ("replied", "qualified", "negotiation") or outreach == "replied":
        return True
    for ev in row.get("interactions") or []:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("event") or "").lower() in (
            "replied",
            "reply",
            "positive_reply",
            "ответил",
            "answer",
        ):
            return True
    return False


def _reply_at(row: dict[str, Any]) -> datetime | None:
    best: datetime | None = None
    for ev in row.get("interactions") or []:
        if not isinstance(ev, dict):
            continue
        if str(ev.get("event") or "").lower() not in (
            "replied",
            "reply",
            "positive_reply",
            "ответил",
            "answer",
        ):
            continue
        at = _parse_dt(str(ev.get("at") or ev.get("created_at") or ""))
        if at and (best is None or at > best):
            best = at
    if best:
        return best
    if _is_reply(row):
        _, updated = _row_times(row)
        return updated
    return None


def build_live_monitor(
    *,
    memory_dir: Path | None,
    opportunity_rows: list[dict[str, Any]],
    runner: dict[str, Any],
    quota_health: dict[str, Any] | None = None,
    stripe_settlements: list[dict[str, Any]] | None = None,
    stripe_paid_eur: float = 0.0,
    digistore_commission_eur: float = 0.0,
    window_minutes: int = 10,
) -> dict[str, Any]:
    """Aggregate live funnel facts for CEO pulse (10 min + today)."""
    now = _utc_now()
    window_start = now - timedelta(minutes=max(1, int(window_minutes)))
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    quota_health = quota_health or {}
    settlements = stripe_settlements or []

    def bucket(start: datetime) -> dict[str, Any]:
        found = 0
        found_last: datetime | None = None
        passed = 0
        passed_last: datetime | None = None
        audited = 0
        audited_last: datetime | None = None
        sent = 0
        sent_last: datetime | None = None
        delivered = 0
        delivered_last: datetime | None = None
        delivered_known = False
        replies = 0
        replies_last: datetime | None = None
        focus_company = ""
        focus_market = ""
        focus_status = ""

        for row in opportunity_rows:
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            found_at, updated_at = _row_times(row)
            company = str(row.get("company_name") or meta.get("company") or "").strip()
            market = str(meta.get("market") or row.get("market") or "").upper()

            if _in_window(found_at, start):
                found += 1
                if found_at and (found_last is None or found_at > found_last):
                    found_last = found_at
                    if company:
                        focus_company = company
                        focus_market = market
                        focus_status = "hunt"

            archived = bool(meta.get("quality_archive"))
            if not archived and _in_window(found_at or updated_at, start):
                # Passed filter = ingested and not quality-archived in window
                if found_at and _in_window(found_at, start):
                    passed += 1
                    if found_at and (passed_last is None or found_at > passed_last):
                        passed_last = found_at

            has_audit = bool(
                meta.get("premium_score") is not None
                or meta.get("analysis")
                or meta.get("website_audit")
                or meta.get("audit_at")
                or row.get("recommended_price_label")
            )
            audit_at = _parse_dt(str(meta.get("audit_at") or "")) or (
                updated_at if has_audit else None
            )
            if has_audit and _in_window(audit_at, start):
                audited += 1
                if audit_at and (audited_last is None or audit_at > audited_last):
                    audited_last = audit_at
                    if company:
                        focus_company = company
                        focus_market = market
                        focus_status = "audit"

            outreach = str(row.get("outreach_status") or "")
            if outreach == "sent" and _in_window(updated_at, start):
                sent += 1
                if updated_at and (sent_last is None or updated_at > sent_last):
                    sent_last = updated_at
                    if company:
                        focus_company = company
                        focus_market = market
                        focus_status = "send"

            if meta.get("email_delivered") is True:
                delivered_known = True
                del_at = _parse_dt(str(meta.get("email_delivered_at") or "")) or updated_at
                if _in_window(del_at, start):
                    delivered += 1
                    if del_at and (delivered_last is None or del_at > delivered_last):
                        delivered_last = del_at

            reply_at = _reply_at(row)
            if reply_at and _in_window(reply_at, start):
                replies += 1
                if replies_last is None or reply_at > replies_last:
                    replies_last = reply_at

        stripe_orders = 0
        stripe_paid = 0.0
        stripe_last: datetime | None = None
        for s in settlements:
            paid_at = _parse_dt(str(s.get("paid_at") or ""))
            if not _in_window(paid_at, start):
                continue
            stripe_orders += 1
            stripe_paid += float(s.get("amount_eur") or 0)
            if paid_at and (stripe_last is None or paid_at > stripe_last):
                stripe_last = paid_at

        # Digistore: only CONFIRMED commissions (caller passes total for today/all)
        digi = float(digistore_commission_eur or 0) if start <= today_start else 0.0
        # For 10-min window we don't invent — keep 0 unless caller scopes it
        if start > today_start:
            digi = 0.0

        return {
            "companies_found": found,
            "after_filter": passed,
            "audits_done": audited,
            "kp_sent": sent,
            "email_delivered": delivered,
            "email_delivered_tracked": delivered_known,
            "replies": replies,
            "stripe_orders": stripe_orders,
            "stripe_paid_eur": round(stripe_paid, 2),
            "digistore_commission_eur": round(digi, 2),
            "focus": {
                "company": focus_company,
                "market": focus_market,
                "stage": focus_status,
            },
            "last": {
                "found_at": _iso(found_last),
                "filter_at": _iso(passed_last),
                "audit_at": _iso(audited_last),
                "sent_at": _iso(sent_last),
                "delivered_at": _iso(delivered_last),
                "reply_at": _iso(replies_last),
                "stripe_at": _iso(stripe_last),
            },
        }

    last_10 = bucket(window_start)
    today = bucket(today_start)

    # Prefer quota sent_today when opportunity timestamps lag
    quota_sent = int(quota_health.get("sent_today_total") or 0)
    if quota_sent > int(today["kp_sent"]):
        today["kp_sent"] = quota_sent
        today["kp_sent_source"] = "outreach_quota"
    else:
        today["kp_sent_source"] = "opportunities"

    runner_running = bool(runner.get("running"))
    last_tick = _parse_dt(str(runner.get("last_tick_at") or ""))
    last_action = str(runner.get("last_action") or "")
    last_msg = str(runner.get("last_message_ru") or "")
    tick_age = (now - last_tick).total_seconds() if last_tick else None
    interval = int(runner.get("interval_sec") or 10)

    if not runner_running:
        now_status = "idle"
        now_detail = "Раннер остановлен — нажмите ▶ Пуск на Country Desk."
    elif tick_age is not None and tick_age > max(90, interval * 6):
        now_status = "error"
        now_detail = f"Тик завис: последний {int(tick_age)}с назад (ожидали ~{interval}с)."
    elif last_action in ("send_skip", "error"):
        now_status = "idle" if last_action == "send_skip" else "error"
        now_detail = last_msg or last_action
    else:
        now_status = "success"
        now_detail = last_msg or f"Тик: {last_action or '—'}"

    # Current focus from runner message or today funnel
    current_company = today["focus"].get("company") or last_10["focus"].get("company") or ""
    if ":" in last_msg and last_action == "send":
        # "Отправлено [DE]: Company"
        parts = last_msg.split(":", 1)
        if len(parts) == 2 and parts[1].strip():
            current_company = parts[1].strip()

    def status_for(count: int, last_at: str | None, *, unknown: bool = False) -> str:
        if unknown:
            return "unknown"
        if count > 0:
            return "success"
        if last_at:
            return "idle"
        return "idle"

    steps_10m = [
        _step(
            id="found",
            label_ru="Найдено компаний",
            count=last_10["companies_found"],
            last_at=_parse_dt(last_10["last"]["found_at"]),
            status=status_for(last_10["companies_found"], last_10["last"]["found_at"]),
        ),
        _step(
            id="filter",
            label_ru="После фильтра",
            count=last_10["after_filter"],
            last_at=_parse_dt(last_10["last"]["filter_at"]),
            status=status_for(last_10["after_filter"], last_10["last"]["filter_at"]),
        ),
        _step(
            id="audit",
            label_ru="Аудитов выполнено",
            count=last_10["audits_done"],
            last_at=_parse_dt(last_10["last"]["audit_at"]),
            status=status_for(last_10["audits_done"], last_10["last"]["audit_at"]),
        ),
        _step(
            id="kp_sent",
            label_ru="КП отправлено",
            count=last_10["kp_sent"],
            last_at=_parse_dt(last_10["last"]["sent_at"]),
            status=status_for(last_10["kp_sent"], last_10["last"]["sent_at"]),
        ),
        _step(
            id="delivered",
            label_ru="Email доставлено",
            count=last_10["email_delivered"],
            last_at=_parse_dt(last_10["last"]["delivered_at"]),
            status=(
                "unknown"
                if not last_10["email_delivered_tracked"]
                else status_for(last_10["email_delivered"], last_10["last"]["delivered_at"])
            ),
            detail_ru=(
                "Нет webhook доставки Resend — не считаем доставку без факта."
                if not last_10["email_delivered_tracked"]
                else ""
            ),
        ),
        _step(
            id="replies",
            label_ru="Ответов",
            count=last_10["replies"],
            last_at=_parse_dt(last_10["last"]["reply_at"]),
            status=status_for(last_10["replies"], last_10["last"]["reply_at"]),
        ),
        _step(
            id="stripe_orders",
            label_ru="Создан заказ Stripe",
            count=last_10["stripe_orders"],
            last_at=_parse_dt(last_10["last"]["stripe_at"]),
            status=status_for(last_10["stripe_orders"], last_10["last"]["stripe_at"]),
        ),
        _step(
            id="paid",
            label_ru="Оплачено €",
            count=int(round(float(last_10["stripe_paid_eur"]) * 100)),  # cents for count slot
            last_at=_parse_dt(last_10["last"]["stripe_at"]),
            status=status_for(
                1 if last_10["stripe_paid_eur"] > 0 else 0,
                last_10["last"]["stripe_at"],
            ),
            detail_ru=f"{last_10['stripe_paid_eur']:.2f} € CONFIRMED",
        ),
    ]
    # Fix paid step to show euros as display_value
    steps_10m[-1]["display_value"] = f"{last_10['stripe_paid_eur']:.2f} €"
    steps_10m[-1]["count"] = last_10["stripe_orders"]  # keep count = orders; euros in display

    steps_today = []
    for s in steps_10m:
        key_map = {
            "found": "companies_found",
            "filter": "after_filter",
            "audit": "audits_done",
            "kp_sent": "kp_sent",
            "delivered": "email_delivered",
            "replies": "replies",
            "stripe_orders": "stripe_orders",
            "paid": "stripe_orders",
        }
        k = key_map[s["id"]]
        count = int(today[k])
        last_key = {
            "found": "found_at",
            "filter": "filter_at",
            "audit": "audit_at",
            "kp_sent": "sent_at",
            "delivered": "delivered_at",
            "replies": "reply_at",
            "stripe_orders": "stripe_at",
            "paid": "stripe_at",
        }[s["id"]]
        last_at = _parse_dt(today["last"][last_key])
        unknown = s["id"] == "delivered" and not today["email_delivered_tracked"]
        row = _step(
            id=s["id"],
            label_ru=s["label_ru"],
            count=count,
            last_at=last_at,
            status=status_for(count, _iso(last_at), unknown=unknown),
            detail_ru=s.get("detail_ru") or "",
        )
        if s["id"] == "paid":
            row["display_value"] = f"{today['stripe_paid_eur']:.2f} €"
            row["detail_ru"] = f"{today['stripe_paid_eur']:.2f} € CONFIRMED"
        if s["id"] == "delivered" and unknown:
            row["detail_ru"] = "Нет webhook доставки Resend — не считаем доставку без факта."
        steps_today.append(row)

    # Digistore step (today only — commissions are day/ledger scoped)
    digi_today = float(digistore_commission_eur or 0)
    steps_today.append(
        _step(
            id="digistore",
            label_ru="Комиссии Digistore",
            count=1 if digi_today > 0 else 0,
            last_at=None,
            status="success" if digi_today > 0 else "idle",
            detail_ru=f"{digi_today:.2f} € CONFIRMED (ключ ≠ комиссия)",
        )
    )
    steps_today[-1]["display_value"] = f"{digi_today:.2f} €"

    events = []
    for entry in list(runner.get("log") or [])[-12:]:
        if not isinstance(entry, dict):
            continue
        action = str(entry.get("action") or "")
        ok = action not in ("error", "send_error")
        events.append(
            {
                "at": entry.get("at"),
                "action": action,
                "message_ru": entry.get("message_ru") or "",
                "status": "success" if ok else "error",
            }
        )

    alive = runner_running and now_status in ("success", "idle")

    return {
        "ok": True,
        "generated_at": now.isoformat(),
        "window_minutes": int(window_minutes),
        "alive": alive,
        "headline_ru": (
            "Машина работает"
            if alive and (last_10["companies_found"] or last_10["kp_sent"] or runner_running)
            else "Нет живой активности — смотрите шаги ниже"
        ),
        "now": {
            "runner_running": runner_running,
            "last_action": last_action or None,
            "last_message_ru": last_msg or None,
            "last_tick_at": _iso(last_tick),
            "next_tick_at": runner.get("next_tick_at"),
            "interval_sec": interval,
            "ticks": int(runner.get("ticks") or 0),
            "session_leads": int(runner.get("session_leads") or 0),
            "session_drafts": int(runner.get("session_drafts") or 0),
            "session_sends": int(runner.get("session_sends") or 0),
            "session_skipped": int(runner.get("session_skipped") or 0),
            "current_company": current_company or None,
            "current_market": today["focus"].get("market") or last_10["focus"].get("market") or None,
            "status": now_status,
            "detail_ru": now_detail,
        },
        "last_10_min": {
            **{k: last_10[k] for k in (
                "companies_found",
                "after_filter",
                "audits_done",
                "kp_sent",
                "email_delivered",
                "replies",
                "stripe_orders",
                "stripe_paid_eur",
            )},
            "steps": steps_10m,
        },
        "today": {
            **{k: today[k] for k in (
                "companies_found",
                "after_filter",
                "audits_done",
                "kp_sent",
                "email_delivered",
                "replies",
                "stripe_orders",
                "stripe_paid_eur",
            )},
            "digistore_commission_eur": digi_today,
            "kp_sent_source": today.get("kp_sent_source"),
            "steps": steps_today,
            "ready_now_note_ru": "Ready/Waiting — на Country Desk; здесь только факты времени.",
        },
        "reality": {
            "stripe_paid_total_eur": round(float(stripe_paid_eur or 0), 2),
            "digistore_commission_eur": digi_today,
            "rule_ru": "Ключ ≠ деньги. В Ledger только CONFIRMED оплата / комиссия.",
        },
        "recent_events": list(reversed(events)),
        "memory_dir": str(memory_dir) if memory_dir else None,
    }
