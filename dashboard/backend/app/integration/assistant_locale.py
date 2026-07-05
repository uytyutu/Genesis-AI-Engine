"""Localized assistant response templates (rule-based, ru/en/de)."""

from __future__ import annotations

from typing import Any


def pick(locale: str, table: dict[str, str]) -> str:
    return table.get(locale) or table["en"]


def empty_prompt(locale: str) -> str:
    return pick(
        locale,
        {
            "ru": (
                "Спросите, например:\n"
                "• Что происходит?\n"
                "• Что мне делать дальше?\n"
                "• Какой статус системы?\n"
                "• Когда будет Factory?"
            ),
            "en": (
                "Try asking:\n"
                "• What's happening?\n"
                "• What should I do next?\n"
                "• What's the system status?\n"
                "• When will Factory be ready?"
            ),
            "de": (
                "Fragen Sie zum Beispiel:\n"
                "• Was passiert gerade?\n"
                "• Was soll ich als Nächstes tun?\n"
                "• Wie ist der Systemstatus?\n"
                "• Wann ist Factory bereit?"
            ),
        },
    )


def greeting(locale: str, name: str) -> str:
    return pick(
        locale,
        {
            "ru": (
                f"Здравствуйте, {name}. Я помощник вашей цифровой компании.\n"
                "Спросите «Что происходит?» или «Что мне делать дальше?»"
            ),
            "en": (
                f"Hello, {name}. I'm your digital company assistant.\n"
                "Ask “What's happening?” or “What should I do next?”"
            ),
            "de": (
                f"Hallo, {name}. Ich bin der Assistent Ihres digitalen Unternehmens.\n"
                "Fragen Sie „Was passiert gerade?“ oder „Was soll ich als Nächstes tun?“"
            ),
        },
    )


def fallback_help(locale: str) -> str:
    return pick(
        locale,
        {
            "ru": (
                "Я отвечаю на вопросы о вашей компании: статус, задачи, продукты, следующие шаги.\n"
                "Попробуйте: «Что происходит?» или «Что мне делать дальше?»"
            ),
            "en": (
                "I answer questions about your company: status, tasks, products, next steps.\n"
                "Try: “What's happening?” or “What should I do next?”"
            ),
            "de": (
                "Ich beantworte Fragen zu Ihrem Unternehmen: Status, Aufgaben, Produkte, nächste Schritte.\n"
                "Versuchen Sie: „Was passiert gerade?“ oder „Was soll ich als Nächstes tun?“"
            ),
        },
    )


def what_happening(locale: str, dash: dict[str, Any]) -> str:
    if locale == "en":
        lines = [
            f"Today the system completed {dash['tasks_completed_today']} tasks.",
            f"Errors: {dash['errors_today']}.",
            f"Server uptime: {dash['uptime_label']}.",
            f"Last launch: {dash['last_launch_label']}.",
        ]
        lines.append(
            "All core services are running."
            if dash["all_services_ok"]
            else "Not all services respond — open Launcher or Monitoring."
        )
        lines.append("The product factory connects after you confirm the current experience.")
        return "\n".join(lines)
    if locale == "de":
        lines = [
            f"Heute hat das System {dash['tasks_completed_today']} Aufgaben erledigt.",
            f"Fehler: {dash['errors_today']}.",
            f"Server-Laufzeit: {dash['uptime_label']}.",
            f"Letzter Start: {dash['last_launch_label']}.",
        ]
        lines.append(
            "Alle Kernservices laufen."
            if dash["all_services_ok"]
            else "Nicht alle Services antworten — öffnen Sie Launcher oder Monitoring."
        )
        lines.append(
            "Die Produktfabrik wird verbunden, nachdem Sie die aktuelle Erfahrung bestätigt haben."
        )
        return "\n".join(lines)
    lines = [
        f"Сегодня система выполнила {dash['tasks_completed_today']} задач.",
        f"Ошибок: {dash['errors_today']}.",
        f"Время работы сервера: {dash['uptime_label']}.",
        f"Последний запуск: {dash['last_launch_label']}.",
    ]
    lines.append(
        "Все основные службы работают."
        if dash["all_services_ok"]
        else "Не все службы отвечают — откройте Launcher или Мониторинг."
    )
    lines.append("Отдел создания продуктов подключится после того, как вы подтвердите текущий опыт.")
    return "\n".join(lines)
