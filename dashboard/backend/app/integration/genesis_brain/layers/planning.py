"""
Genesis Planning Layer — break big goals into steps (foundation stub).

Mission 4+ expands: multi-week plans, Factory handoff, milestone tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanHint:
    steps: tuple[str, ...]

    def to_prompt_hint(self) -> str:
        if not self.steps:
            return ""
        numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(self.steps, 1))
        return f"Если уместно, предложи план по шагам:\n{numbered}"


class GenesisPlanningLayer:
    """Detects when user needs a staged plan."""

    def suggest(self, topic: str) -> PlanHint:
        t = topic.lower()
        if "сайт" in t and any(w in t for w in ("салон", "кафе", "бизнес")):
            return PlanHint(
                (
                    "Уточнить цель и аудиторию",
                    "Структура страниц и запись/заказ",
                    "Контент и бренд",
                    "Сборка в Factory → превью",
                    "Запуск и первые клиенты",
                )
            )
        if "public launch" in t or "запуск" in t:
            return PlanHint(
                (
                    "Проверить витрину и чат",
                    "Подключить оплату",
                    "Первый клиент / кейс",
                    "Marketing Lab — первые каналы",
                )
            )
        return PlanHint(())
