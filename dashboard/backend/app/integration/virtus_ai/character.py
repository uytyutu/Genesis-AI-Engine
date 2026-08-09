"""Virtus AI character — calm digital project director."""

from __future__ import annotations

from typing import Any


def welcome_message(ctx: dict[str, Any] | None = None) -> str:
    c = ctx or {}
    name = str(c.get("client_name") or c.get("name") or "").strip() or "коллега"
    project = str(c.get("project_name") or c.get("business_name") or "ваш проект").strip()
    niche = str(c.get("niche") or "").strip()
    last = c.get("last_session") or {}
    leads = c.get("pending_leads")
    published = bool(c.get("published", True))

    lines = [
        f"Добро пожаловать, {name}.",
        "",
        "Рад снова видеть вас.",
        "",
        f"Последний раз мы работали над проектом «{project}»"
        + (f" ({niche})." if niche else "."),
        "",
    ]
    bullets: list[str] = []
    if published:
        bullets.append("сайт опубликован")
    if last.get("summary"):
        bullets.append(str(last["summary"]))
    if isinstance(leads, int) and leads > 0:
        bullets.append(f"ожидают проверки {leads} заявки")
    if not bullets and last.get("done"):
        for d in list(last.get("done") or [])[:3]:
            bullets.append(str(d))
    if bullets:
        lines.append("После нашей последней сессии:")
        lines.append("")
        for b in bullets:
            lines.append(f"• {b}")
        lines.append("")
    lines.append("Что будем делать сегодня?")
    return "\n".join(lines)


def redirect_to_project(user_text: str) -> str | None:
    """Soft redirect when the user drifts into small-talk / off-topic."""
    t = (user_text or "").strip().lower()
    if not t:
        return None

    # Off-topic universal AI asks
    banned = (
        "диплом",
        "физик",
        "новост",
        "напиши код на python для",
        "рецепт",
        "гороскоп",
    )
    if any(b in t for b in banned):
        return (
            "Я Virtus AI — цифровой директор вашего проекта в Virtus Core.\n\n"
            "Универсальные темы вне цифрового бизнеса я не веду.\n"
            "Чем займёмся в вашем проекте: сайт, магазин, заявки или запуск?"
        )

    greetings = ("привет", "как дела", "как настроение", "hello", "hi ")
    if any(t.startswith(g) or t == g.strip() for g in greetings) and len(t) < 40:
        return (
            "Привет!\n\n"
            "Всё готово к работе.\n"
            "Проект синхронизирован.\n\n"
            "Продолжим работу над сайтом или хотите заняться чем-то новым?"
        )

    if "где мы остановились" in t or "где остановились" in t:
        return "__RESUME__"

    return None
