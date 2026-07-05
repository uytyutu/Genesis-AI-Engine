"""Rule-based Genesis Assistant — answers from live system state, not external LLM."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.integration import assistant_locale as L
from app.integration.locale_service import assistant_response_locale

if TYPE_CHECKING:
    from app.integration.context import IntegrationContext


class AssistantService:
    """Genesis-aware helper for non-programmer owners."""

    def __init__(self, ctx: IntegrationContext) -> None:
        self._ctx = ctx

    def ask(self, question: str, locale: str | None = None) -> dict[str, str]:
        loc = assistant_response_locale(locale, question)
        q = question.strip()
        if not q:
            return {"answer": L.empty_prompt(loc), "source": "genesis"}

        lower = q.lower()
        if self._matches(
            lower,
            "что происходит",
            "что случилось",
            "расскажи",
            "объясни",
            "what's happening",
            "what is happening",
            "was passiert",
            "was geschieht",
        ):
            return {"answer": self._what_is_happening(loc), "source": "genesis"}
        if self._matches(
            lower,
            "что делать",
            "дальше",
            "следующ",
            "рекоменд",
            "совет",
            "what should i",
            "what next",
            "next step",
            "was soll ich",
            "nächstes",
        ):
            return {"answer": self._what_next(loc), "source": "genesis"}
        if self._matches(
            lower,
            "статус",
            "работает",
            "служб",
            "сервис",
            "status",
            "service",
            "systemstatus",
            "dienst",
        ):
            return {"answer": self._system_status(loc), "source": "genesis"}
        if self._matches(lower, "factory", "фабрик", "шаблон", "продукт", "сайт", "product"):
            return {"answer": self._factory_status(loc), "source": "genesis"}
        if self._matches(
            lower,
            "ошиб",
            "проблем",
            "не работ",
            "error",
            "problem",
            "fehler",
            "funktioniert nicht",
        ):
            return {"answer": self._errors_help(loc), "source": "genesis"}
        if self._matches(lower, "задач", "демо", "очеред", "task", "queue", "aufgabe"):
            return {"answer": self._tasks_summary(loc), "source": "genesis"}
        if self._matches(
            lower,
            "прогресс",
            "процент",
            "этап",
            "roadmap",
            "план",
            "progress",
            "fortschritt",
        ):
            return {"answer": self._progress_summary(loc), "source": "genesis"}
        if self._matches(
            lower,
            "привет",
            "здравств",
            "hello",
            "hi",
            "hallo",
            "guten tag",
        ):
            name = self._ctx.owner.owner_name()
            return {"answer": L.greeting(loc, name), "source": "genesis"}
        if self._matches(
            lower,
            "иде",
            "рынок",
            "возможност",
            "предлож",
            "idea",
            "market",
            "idee",
            "markt",
        ):
            return {"answer": self._ideas_cautious(loc), "source": "genesis"}

        return {"answer": L.fallback_help(loc), "source": "genesis"}

    def _matches(self, text: str, *phrases: str) -> bool:
        return any(p in text for p in phrases)

    def _what_is_happening(self, locale: str) -> str:
        dash = self._ctx.owner.dashboard()
        return L.what_happening(locale, dash)

    def _what_next(self, locale: str) -> str:
        dash = self._ctx.owner.dashboard()
        steps: list[str] = []
        if locale == "en":
            if not dash["system_running"]:
                steps.append("1. Open Genesis and click “Start Genesis”.")
            if dash["products_count"] == 0:
                steps.append("2. Click “Create product” — start your first project.")
            elif dash["products_created_today"] == 0:
                steps.append("2. Open Projects or create another product.")
            steps.append("3. Ask me for ideas — I'll suggest options from available data.")
            steps.append("4. Product factory is ready — create a landing page and approve for client.")
            return "I recommend:\n" + "\n".join(steps)
        if locale == "de":
            if not dash["system_running"]:
                steps.append("1. Öffnen Sie Genesis und klicken Sie „Genesis starten“.")
            if dash["products_count"] == 0:
                steps.append("2. Klicken Sie „Produkt erstellen“ — starten Sie Ihr erstes Projekt.")
            elif dash["products_created_today"] == 0:
                steps.append("2. Öffnen Sie Projekte oder erstellen Sie ein weiteres Produkt.")
            steps.append("3. Fragen Sie mich nach Ideen — ich schlage Optionen vor.")
            steps.append("4. Produktfabrik ist bereit — Landing erstellen und für den Kunden freigeben.")
            return "Empfehlung:\n" + "\n".join(steps)
        if not dash["system_running"]:
            steps.append("1. Откройте Genesis и нажмите «Запустить Genesis».")
        if dash["products_count"] == 0:
            steps.append("2. Нажмите «Создать продукт» — начните первый проект.")
        elif dash["products_created_today"] == 0:
            steps.append("2. Посмотрите «Проекты» или создайте ещё один продукт.")
        steps.append("3. Спросите меня об идеях — предложу варианты на основе доступных данных.")
        steps.append("4. Отдел создания продуктов готов — создайте Landing и одобрите для клиента.")
        return "Рекомендую:\n" + "\n".join(steps)

    def _ideas_cautious(self, locale: str) -> str:
        if locale == "en":
            return (
                "Here are three possible ideas from available data. "
                "Choose which to explore:\n\n"
                "1. Landing page for your service — quick start, low risk.\n"
                "2. Telegram bot for leads — when the department is ready.\n"
                "3. Improve an existing product — if you already have a project.\n\n"
                "Not a demand guarantee — options for your decision. "
                "Reply with a number or “Create product” on Home."
            )
        if locale == "de":
            return (
                "Drei mögliche Ideen aus verfügbaren Daten:\n\n"
                "1. Landing Page für Ihre Dienstleistung — schneller Start, geringes Risiko.\n"
                "2. Telegram-Bot für Anfragen — wenn die Abteilung bereit ist.\n"
                "3. Bestehendes Produkt verbessern — wenn bereits ein Projekt existiert.\n\n"
                "Keine Nachfragegarantie — nur Optionen für Ihre Entscheidung."
            )
        return (
            "Я подготовил три возможные идеи на основе доступных данных. "
            "Выберите, какую исследовать или реализовать дальше:\n\n"
            "1. Landing Page для вашей услуги — быстрый старт, низкий риск.\n"
            "2. Telegram-бот для приёма заявок — когда будет готов соответствующий отдел.\n"
            "3. Улучшение существующего продукта — если уже есть проект в «Проектах».\n\n"
            "Это не гарантия спроса — только варианты для вашего решения. "
            "Напишите номер или «Создать продукт» на главной."
        )

    def _system_status(self, locale: str) -> str:
        health = self._ctx.health.check_all()
        labels = {
            "ru": {"kernel": "Kernel", "brain": "Brain", "queue": "Очередь", "audit": "Журнал"},
            "en": {"kernel": "Kernel", "brain": "Brain", "queue": "Queue", "audit": "Audit"},
            "de": {"kernel": "Kernel", "brain": "Brain", "queue": "Warteschlange", "audit": "Protokoll"},
        }.get(locale, {"kernel": "Kernel", "brain": "Brain", "queue": "Queue", "audit": "Audit"})
        lines = []
        for key, label in labels.items():
            state = health.get(key, "offline")
            icon = "✔" if state == "online" else "⚠" if state == "degraded" else "✘"
            lines.append(f"{icon} {label}: {state}")
        paused = self._ctx.adapter.is_paused
        if paused:
            pause_msg = {
                "ru": "⚠ Brain на паузе — нажмите «Продолжить» в Мониторинге.",
                "en": "⚠ Brain paused — click Resume in Monitoring.",
                "de": "⚠ Brain pausiert — in Monitoring auf Fortsetzen klicken.",
            }
            lines.append(pause_msg.get(locale, pause_msg["en"]))
        return "\n".join(lines)

    def _factory_status(self, locale: str) -> str:
        latest = self._ctx.factory.latest_product() if hasattr(self._ctx, "factory") else None
        if latest:
            if locale == "en":
                return (
                    f"Product factory completed: {latest['business_name']}.\n"
                    "Open preview. When ready for the client — approve on the product page."
                )
            if locale == "de":
                return (
                    f"Produktfabrik abgeschlossen: {latest['business_name']}.\n"
                    "Vorschau öffnen. Bei Bereitschaft für den Kunden — auf der Produktseite freigeben."
                )
            return (
                f"Отдел создания продуктов завершил: {latest['business_name']}.\n"
                "Откройте превью. Если готовы отправить клиенту — нажмите одобрение на странице продукта."
            )
        if locale == "en":
            return (
                "Product factory can build a landing page in Sandbox.\n"
                "Click “Create product” and describe the task in plain language."
            )
        if locale == "de":
            return (
                "Produktfabrik kann eine Landing Page in der Sandbox erstellen.\n"
                "Klicken Sie „Produkt erstellen“ und beschreiben Sie die Aufgabe."
            )
        return (
            "Отдел создания продуктов готов собрать Landing Page в Sandbox.\n"
            "Нажмите «Создать продукт» и опишите задачу простыми словами."
        )

    def _errors_help(self, locale: str) -> str:
        dash = self._ctx.owner.dashboard()
        if dash["errors_today"] == 0:
            return {
                "ru": "Сегодня ошибок нет. Если что-то не работает — откройте Launcher → Журнал.",
                "en": "No errors today. If something fails — open Launcher → Log.",
                "de": "Heute keine Fehler. Bei Problemen — Launcher → Protokoll öffnen.",
            }.get(locale, "No errors today.")
        return {
            "ru": (
                f"Сегодня зафиксировано ошибок: {dash['errors_today']}.\n"
                "Откройте страницу «Задачи» или Launcher → Журнал для деталей."
            ),
            "en": (
                f"Errors today: {dash['errors_today']}.\n"
                "Open Tasks or Launcher → Log for details."
            ),
            "de": (
                f"Fehler heute: {dash['errors_today']}.\n"
                "Öffnen Sie Aufgaben oder Launcher → Protokoll für Details."
            ),
        }.get(locale, f"Errors today: {dash['errors_today']}.")

    def _tasks_summary(self, locale: str) -> str:
        queue = self._ctx.tasks.queue_stats()
        dash = self._ctx.owner.dashboard()
        if locale == "en":
            return (
                f"Completed today: {dash['tasks_completed_today']}.\n"
                f"Queue — pending: {queue.pending}, running: {queue.running}, "
                f"done: {queue.completed}, failed: {queue.failed}.\n"
                "Demo on Home creates 5 tasks automatically."
            )
        if locale == "de":
            return (
                f"Heute erledigt: {dash['tasks_completed_today']}.\n"
                f"Warteschlange — wartend: {queue.pending}, laufend: {queue.running}, "
                f"fertig: {queue.completed}, fehlgeschlagen: {queue.failed}."
            )
        return (
            f"Сегодня завершено: {dash['tasks_completed_today']}.\n"
            f"Всего в очереди — ожидание: {queue.pending}, "
            f"выполняется: {queue.running}, готово: {queue.completed}, ошибки: {queue.failed}.\n"
            "Демо на главной создаёт 5 задач автоматически."
        )

    def _progress_summary(self, locale: str) -> str:
        from app.integration.timeline_service import TimelineService

        snap = TimelineService().snapshot()
        label = {"ru": "Прогресс", "en": "Progress", "de": "Fortschritt"}.get(locale, "Progress")
        lines = [f"{label} ({snap['label']}): {snap['progress_percent']}%"]
        for item in snap["milestones"]:
            lines.append(f"{item['symbol']} {item['label']}")
        return "\n".join(lines)
