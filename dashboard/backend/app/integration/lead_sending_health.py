"""Lead Sending Health Monitor — human-readable blockers for Country Desk."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _lamp(ok: bool) -> str:
    return "green" if ok else "red"


def build_lead_sending_health(
    *,
    memory_dir: Path,
    auto_send: bool,
    runner_running: bool,
    ready_now: int,
    places_ready: bool,
    gmail_send_ready: bool,
    resend_key_present: bool,
    cooldown: dict[str, Any] | None,
    domain_at_cap: bool,
    domain_remaining: int | None = None,
    hunt_ok: bool = True,
    email_providers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return CEO-facing lamps + current_blocker + next_action (no secrets)."""
    cool = cooldown if isinstance(cooldown, dict) else {}
    pool = email_providers if isinstance(email_providers, dict) else {}
    pool_ready = list(pool.get("ready_providers") or [])
    resend_available = bool(cool.get("resend_available", True))
    resend_ok = bool(resend_key_present) and resend_available and not domain_at_cap
    if "resend" in pool_ready:
        resend_ok = True
    queue_ok = int(ready_now or 0) >= 0
    queue_has_work = int(ready_now or 0) > 0
    any_mail = bool(pool_ready) or resend_ok or bool(gmail_send_ready)

    lamps = {
        "hunt": {"status": _lamp(hunt_ok), "label": "Hunt", "ok": hunt_ok},
        "queue": {
            "status": _lamp(queue_ok),
            "label": "Queue",
            "ok": queue_ok,
            "ready_now": int(ready_now or 0),
        },
        "places": {
            "status": _lamp(places_ready),
            "label": "Places",
            "ok": places_ready,
        },
        "auto_send": {
            "status": _lamp(bool(auto_send) and bool(runner_running)),
            "label": "AutoSend",
            "ok": bool(auto_send) and bool(runner_running),
            "auto_send": bool(auto_send),
            "runner_running": bool(runner_running),
        },
        "resend": {
            "status": _lamp(resend_ok),
            "label": "Resend",
            "ok": resend_ok,
            "key_present": bool(resend_key_present),
            "cooldown_active": not resend_available,
            "domain_at_cap": bool(domain_at_cap),
            "domain_remaining": domain_remaining,
            "last_reason": cool.get("last_reason"),
        },
        "gmail": {
            "status": _lamp(bool(gmail_send_ready) and "gmail" in pool_ready)
            if pool_ready
            else _lamp(bool(gmail_send_ready)),
            "label": "Gmail",
            "ok": "gmail" in pool_ready if pool else bool(gmail_send_ready),
        },
        "pool": {
            "status": _lamp(any_mail),
            "label": "Provider Pool",
            "ok": any_mail,
            "ready": pool_ready,
        },
    }

    # Enrich from pool board when present
    for p in pool.get("providers") or []:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id") or "")
        if pid in lamps and p.get("lamp"):
            lamps[pid]["status"] = (
                "green"
                if p["lamp"] == "green"
                else ("yellow" if p["lamp"] == "yellow" else "red")
            )
            lamps[pid]["ok"] = p["lamp"] == "green"
            if p.get("last_reason"):
                lamps[pid]["last_reason"] = p.get("last_reason")
            if p.get("last_detail"):
                lamps[pid]["last_detail"] = p.get("last_detail")
            if p.get("last_http_status"):
                lamps[pid]["last_http_status"] = p.get("last_http_status")

    blockers: list[dict[str, str]] = []
    next_actions: list[str] = []

    if not places_ready:
        blockers.append(
            {
                "code": "places_not_ready",
                "title": "Places",
                "detail": "GOOGLE_API_KEY не настроен — Hunt не сможет искать компании.",
            }
        )
        next_actions.append("Добавьте GOOGLE_API_KEY в .env.local и перезапустите Genesis.")

    if not auto_send:
        blockers.append(
            {
                "code": "autosend_off",
                "title": "AutoSend",
                "detail": "Тумблер автоотправки выключен.",
            }
        )
        next_actions.append("Включите Автоотправка на Country Desk.")
    elif not runner_running:
        blockers.append(
            {
                "code": "runner_stopped",
                "title": "AutoSend",
                "detail": "Автоотправка вкл., но runner остановлен — тики не идут.",
            }
        )
        next_actions.append("Нажмите ▶ Пуск на Country Desk.")

    if not any_mail:
        blockers.append(
            {
                "code": "all_providers_down",
                "title": "Provider Pool",
                "detail": (
                    pool.get("next_action_ru")
                    or "Нет доступных почтовых провайдеров (Resend/Gmail/Mailbox.org)."
                ),
            }
        )
        next_actions.append(
            "Добавьте MAILBOX_SMTP_* в .env.local или дождитесь снятия 429."
        )
    else:
        if domain_at_cap and "resend" not in pool_ready:
            blockers.append(
                {
                    "code": "domain_daily_cap",
                    "title": "Resend quota",
                    "detail": (
                        "Дневной лимит домена Resend исчерпан"
                        + (
                            f" (remaining={domain_remaining})."
                            if domain_remaining is not None
                            else "."
                        )
                        + f" Сейчас шлём через: {', '.join(pool_ready) or 'failover'}."
                    ),
                }
            )
        for p in pool.get("providers") or []:
            if not isinstance(p, dict):
                continue
            if p.get("id") == "gmail" and p.get("last_http_status") == 429:
                blockers.append(
                    {
                        "code": "gmail_429",
                        "title": "Gmail",
                        "detail": (
                            f"Gmail API 429: {str(p.get('last_detail') or '')[:180]}"
                        ),
                    }
                )

    sending_ok = bool(auto_send and runner_running and any_mail)

    if sending_ok and not blockers:
        headline_ru = "Отправка готова — Provider Pool активен."
        current_blocker_ru = ""
    elif sending_ok:
        headline_ru = (
            f"Отправка идёт через {', '.join(pool_ready)}. Есть предупреждения."
        )
        current_blocker_ru = blockers[0]["detail"] if blockers else ""
    else:
        headline_ru = "Отправка остановлена (нет доступного провайдера или AutoSend выкл.)."
        parts = [f"{b['title']}: {b['detail']}" for b in blockers[:3]]
        current_blocker_ru = " ".join(parts) if parts else "Неизвестная блокировка."

    if pool.get("next_action_ru") and pool.get("next_action_ru") not in next_actions:
        next_actions.append(str(pool["next_action_ru"]))

    return {
        "ok": True,
        "version": "lead_sending_health_v2",
        "title_ru": "Lead Sending",
        "headline_ru": headline_ru,
        "sending_ok": sending_ok,
        "lamps": lamps,
        "blockers": blockers,
        "current_blocker_ru": current_blocker_ru,
        "next_actions": next_actions[:5],
        "next_action_ru": next_actions[0] if next_actions else "Действий не требуется.",
        "email_providers": pool or None,
        "note_ru": (
            "Provider Pool: Resend → Gmail → Mailbox.org. "
            "Пока один отдыхает — используется следующий."
        ),
    }
