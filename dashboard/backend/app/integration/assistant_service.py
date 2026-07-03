"""Rule-based Genesis Assistant — answers from live system state, not external LLM."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.integration.context import IntegrationContext


class AssistantService:
    """Genesis-aware helper for non-programmer owners."""

    def __init__(self, ctx: IntegrationContext) -> None:
        self._ctx = ctx

    def ask(self, question: str) -> dict[str, str]:
        q = question.strip()
        if not q:
            return {
                "answer": (
                    "Спросите, например:\n"
                    "• Что происходит?\n"
                    "• Что мне делать дальше?\n"
                    "• Какой статус системы?\n"
                    "• Когда будет Factory?"
                ),
                "source": "genesis",
            }

        lower = q.lower()
        if self._matches(lower, "что происходит", "что случилось", "расскажи", "объясни"):
            return {"answer": self._what_is_happening(), "source": "genesis"}
        if self._matches(lower, "что делать", "дальше", "следующ", "рекоменд", "совет"):
            return {"answer": self._what_next(), "source": "genesis"}
        if self._matches(lower, "статус", "работает", "служб", "сервис"):
            return {"answer": self._system_status(), "source": "genesis"}
        if self._matches(lower, "factory", "фабрик", "шаблон", "продукт", "сайт"):
            return {"answer": self._factory_status(), "source": "genesis"}
        if self._matches(lower, "ошиб", "проблем", "не работ"):
            return {"answer": self._errors_help(), "source": "genesis"}
        if self._matches(lower, "задач", "демо", "очеред"):
            return {"answer": self._tasks_summary(), "source": "genesis"}
        if self._matches(lower, "прогресс", "процент", "этап", "roadmap", "план"):
            return {"answer": self._progress_summary(), "source": "genesis"}
        if self._matches(lower, "привет", "здравств", "hello", "hi"):
            name = self._ctx.owner.owner_name()
            return {
                "answer": (
                    f"Здравствуйте, {name}. Я помощник вашей цифровой компании.\n"
                    "Спросите «Что происходит?» или «Что мне делать дальше?»"
                ),
                "source": "genesis",
            }
        if self._matches(lower, "иде", "рынок", "возможност", "предлож"):
            return {"answer": self._ideas_cautious(), "source": "genesis"}

        return {
            "answer": (
                "Я отвечаю на вопросы о вашей компании: статус, задачи, продукты, следующие шаги.\n"
                "Попробуйте: «Что происходит?» или «Что мне делать дальше?»"
            ),
            "source": "genesis",
        }

    def _matches(self, text: str, *phrases: str) -> bool:
        return any(p in text for p in phrases)

    def _what_is_happening(self) -> str:
        dash = self._ctx.owner.dashboard()
        lines = [
            f"Сегодня система выполнила {dash['tasks_completed_today']} задач.",
            f"Ошибок: {dash['errors_today']}.",
            f"Время работы сервера: {dash['uptime_label']}.",
            f"Последний запуск: {dash['last_launch_label']}.",
        ]
        if dash["all_services_ok"]:
            lines.append("Все основные службы работают.")
        else:
            lines.append("Не все службы отвечают — откройте Launcher или Мониторинг.")
        lines.append("Отдел создания продуктов подключится после того, как вы подтвердите текущий опыт.")
        return "\n".join(lines)

    def _what_next(self) -> str:
        dash = self._ctx.owner.dashboard()
        steps: list[str] = []
        if not dash["system_running"]:
            steps.append("1. Откройте Genesis и нажмите «Запустить Genesis».")
        if dash["products_count"] == 0:
            steps.append("2. Нажмите «Создать продукт» — начните первый проект.")
        elif dash["products_created_today"] == 0:
            steps.append("2. Посмотрите «Проекты» или создайте ещё один продукт.")
        steps.append("3. Спросите меня об идеях — предложу варианты на основе доступных данных.")
        steps.append("4. Отдел создания продуктов готов — создайте Landing и одобрите для клиента.")
        return "Рекомендую:\n" + "\n".join(steps)

    def _ideas_cautious(self) -> str:
        return (
            "Я подготовил три возможные идеи на основе доступных данных. "
            "Выберите, какую исследовать или реализовать дальше:\n\n"
            "1. Landing Page для вашей услуги — быстрый старт, низкий риск.\n"
            "2. Telegram-бот для приёма заявок — когда будет готов соответствующий отдел.\n"
            "3. Улучшение существующего продукта — если уже есть проект в «Проектах».\n\n"
            "Это не гарантия спроса — только варианты для вашего решения. "
            "Напишите номер или «Создать продукт» на главной."
        )

    def _system_status(self) -> str:
        health = self._ctx.health.check_all()
        labels = {
            "kernel": "Kernel",
            "brain": "Brain",
            "queue": "Очередь",
            "audit": "Журнал",
        }
        lines = []
        for key, label in labels.items():
            state = health.get(key, "offline")
            icon = "✔" if state == "online" else "⚠" if state == "degraded" else "✘"
            lines.append(f"{icon} {label}: {state}")
        paused = self._ctx.adapter.is_paused
        if paused:
            lines.append("⚠ Brain на паузе — нажмите «Продолжить» в Мониторинге.")
        return "\n".join(lines)

    def _factory_status(self) -> str:
        latest = self._ctx.factory.latest_product() if hasattr(self._ctx, "factory") else None
        if latest:
            return (
                f"Отдел создания продуктов завершил: {latest['business_name']}.\n"
                "Откройте превью. Если готовы отправить клиенту — нажмите одобрение на странице продукта."
            )
        return (
            "Отдел создания продуктов готов собрать Landing Page в Sandbox.\n"
            "Нажмите «Создать продукт» и опишите задачу простыми словами."
        )

    def _errors_help(self) -> str:
        dash = self._ctx.owner.dashboard()
        if dash["errors_today"] == 0:
            return "Сегодня ошибок нет. Если что-то не работает — откройте Launcher → Журнал."
        return (
            f"Сегодня зафиксировано ошибок: {dash['errors_today']}.\n"
            "Откройте страницу «Задачи» или Launcher → Журнал для деталей."
        )

    def _tasks_summary(self) -> str:
        queue = self._ctx.tasks.queue_stats()
        dash = self._ctx.owner.dashboard()
        return (
            f"Сегодня завершено: {dash['tasks_completed_today']}.\n"
            f"Всего в очереди — ожидание: {queue.pending}, "
            f"выполняется: {queue.running}, готово: {queue.completed}, ошибки: {queue.failed}.\n"
            "Демо на главной создаёт 5 задач автоматически."
        )

    def _progress_summary(self) -> str:
        from app.integration.timeline_service import TimelineService

        snap = TimelineService().snapshot()
        lines = [f"Прогресс ({snap['label']}): {snap['progress_percent']}%"]
        for item in snap["milestones"]:
            lines.append(f"{item['symbol']} {item['label']}")
        return "\n".join(lines)
