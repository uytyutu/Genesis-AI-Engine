"""Vector Planner — Journey-first: what to do for the human before any model is chosen."""

from __future__ import annotations

from dataclasses import dataclass

from app.integration.vector_intelligence.client_life_context import ClientLifeContext
from app.integration.vector_intelligence.types import JourneyPhase, JOURNEY_PHASE_LABELS

_JOURNEY_INSTRUCTIONS: dict[JourneyPhase, tuple[str, str]] = {
    "open_dialog": (
        "ответить по сути вопроса",
        "Тепло и ясно — без проектов, услуг и «чем заняться в бизнесе», если человек не просил.",
    ),
    "accept_responsibility": (
        "взять задачу в работу",
        "С первого ответа — ощущение что работа уже началась: признать задачу, план, следующий шаг.",
    ),
    "understand_goal": (
        "понять цель и контекст",
        "Выяснить зачем нужен результат — максимум один-два уместных вопроса за ход.",
    ),
    "requirements": (
        "согласовать brief",
        "Кратко зафиксировать что делаем простым языком — без анкеты и внутреннего жаргона.",
    ),
    "materials": (
        "собрать недостающие материалы",
        "Просить только то, без чего нельзя двигаться; помнить уже переданное.",
    ),
    "creation": (
        "показать ранний черновик",
        "Дать осязаемый первый результат как можно раньше — даже с заглушками.",
    ),
    "show_progress": (
        "показать прогресс",
        "Человек видит этап, изменения и один чёткий ask если нужен.",
    ),
    "revisions": (
        "внести правки",
        "«Понял, меняем» — спокойно, сколько угодно итераций.",
    ),
    "ready": (
        "показать готовый результат",
        "Результат для просмотра — без спешки к оформлению.",
    ),
    "verification": (
        "проверить согласие с результатом",
        "Убедиться что это именно то, что хотел человек.",
    ),
    "gate": (
        "дождаться подтверждения",
        "Только после «да, это то» — следующий шаг к оформлению; не давить.",
    ),
    "launch": (
        "оформить и запустить",
        "Оплата и передача — только после подтверждённого результата.",
    ),
}


@dataclass(frozen=True)
class PlannerDecision:
    goal: str
    instruction: str
    accompany: bool = False

    def to_block(self) -> str:
        lines = [
            "## Planner (что сделать для человека)",
            f"- Цель хода: {self.goal}",
            f"- Как действовать: {self.instruction}",
        ]
        if self.accompany:
            lines.append(
                "- Сопровождать к результату — каждый ответ сдвигает задачу ближе к итогу."
            )
        return "\n".join(lines)


def plan_for_human(
    *,
    journey_phase: JourneyPhase,
    life: ClientLifeContext,
    priority: str,
    project_birth_ready: bool,
) -> PlannerDecision:
    goal, instruction = _JOURNEY_INSTRUCTIONS.get(
        journey_phase,
        ("быть полезным в текущем этапе", priority),
    )

    if journey_phase in ("show_progress", "revisions", "ready", "verification") and life.has_project:
        title = life.project_title or "проект"
        goal = f"продвинуть «{title}» — {JOURNEY_PHASE_LABELS[journey_phase].split('. ', 1)[-1]}"
        instruction = life.next_step_hint or priority

    if project_birth_ready and journey_phase == "requirements":
        instruction = (
            "Подведите итог обсуждения и одним естественным предложением "
            "предложите оформить проект — только с согласия человека."
        )
        goal = "сохранить зрелую идею, чтобы ничего не потерялось"

    if life.is_return_after_days and life.has_project and journey_phase != "open_dialog":
        stop = life.last_stop_summary or life.stage_label or priority
        goal = "мягко вернуть в работу и напомнить контекст"
        instruction = stop

    accompany = journey_phase not in ("open_dialog", "gate", "launch")

    return PlannerDecision(goal=goal, instruction=instruction, accompany=accompany)
