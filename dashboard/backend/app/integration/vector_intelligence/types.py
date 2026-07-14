"""Vector Intelligence — shared types."""

from __future__ import annotations

from typing import Literal

VectorIntent = Literal[
    "free_talk",
    "learn",
    "explore_idea",
    "build_result",
    "continue_work",
    "support",
]
# Legacy routing codes — compatibility only; Journey Phase drives behavior.
VectorNeed = Literal["companion", "expert", "advisor", "helper", "employee"]
VectorAction = Literal[
    "answer_naturally",
    "explore_together",
    "suggest_save_project",
    "manage_project",
    "execute",
]

JourneyPhase = Literal[
    "open_dialog",
    "accept_responsibility",
    "understand_goal",
    "requirements",
    "materials",
    "creation",
    "show_progress",
    "revisions",
    "ready",
    "verification",
    "gate",
    "launch",
]

JOURNEY_PHASE_LABELS: dict[JourneyPhase, str] = {
    "open_dialog": "Открытый диалог",
    "accept_responsibility": "1. Принятие ответственности",
    "understand_goal": "2. Понимание цели",
    "requirements": "3. Формулирование требований",
    "materials": "4. Сбор материалов",
    "creation": "5. Постепенное создание",
    "show_progress": "6. Показ прогресса",
    "revisions": "7. Правки и изменения",
    "ready": "8. Готово",
    "verification": "9. Проверка результата",
    "gate": "10. Gate — подтверждение результата",
    "launch": "11. Оформление и запуск",
}

JOURNEY_PHASE_PRIORITY: dict[JourneyPhase, str] = {
    "open_dialog": "ответить по сути — без продаж, проектов и «режима консультации»",
    "accept_responsibility": "взять задачу в работу — «моей задачей уже занимаются»",
    "understand_goal": "понять цель человека — уточнить только необходимое",
    "requirements": "зафиксировать согласованный brief простым языком",
    "materials": "собрать недостающие материалы — не блокировать без полного пакета",
    "creation": "дать ранний черновик — работа уже видна",
    "show_progress": "показать где проект сейчас и что изменилось",
    "revisions": "спокойно внести правки — без упрёков и спешки к оформлению",
    "ready": "показать готовый результат для просмотра",
    "verification": "убедиться что это именно тот результат, который хотел человек",
    "gate": "дождаться явного «да, это то» — без давления к оплате",
    "launch": "оформить и запустить только после подтверждения результата",
}

VECTOR_JOURNEY_OS = """## Vector — Project Execution Journey (internal)

Один Vector. Меняется только этап совместной работы — не роль.

**Вопрос каждого хода:** на каком этапе Project Execution Journey находится человек?

Пайплайн: Conversation → Journey Phase → Memory → Context → Planner → Workforce → Response

Workforce — последний шаг, за кулисами. Пользователь знает только Vector."""

# Legacy aliases — imports unchanged across codebase.
VECTOR_PERSONALITY_OS = VECTOR_JOURNEY_OS
UNIFIED_VECTOR_PRINCIPLE = VECTOR_JOURNEY_OS
