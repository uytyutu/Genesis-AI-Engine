"""Immutable laws of Virtus Core Studio Era.

Law #1: each new project must not be worse than the previous best.
Law #2: Reality Over Architecture — client-visible first, or unfinished.

Violations → REBUILD / work continues. No compromises. Agent never auto-PASS.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


LAW_1 = (
    "Каждый новый проект обязан быть не хуже предыдущего лучшего проекта. "
    "Если генерация ухудшила качество — REBUILD. "
    "Если она повторила шаблон — REBUILD. "
    "Если сайт выглядит как конструктор — REBUILD. "
    "Если сайт уступает современным digital-студиям — REBUILD."
)

LAW_1_EN = (
    "Every new project must not be worse than the previous best. "
    "Quality regression → REBUILD. "
    "Template repeat → REBUILD. "
    "Constructor look → REBUILD. "
    "Below modern digital studios → REBUILD."
)

LAW_2 = (
    "Любая новая идея должна сначала стать заметной клиенту. "
    "Если появляется Director, Engine, Rule или Memory — "
    "ответь: «Что изменится в первом впечатлении клиента?» "
    "Если ответ: «Пока ничего, но архитектура стала лучше» — "
    "работа ещё не закончена."
)

LAW_2_EN = (
    "Reality Over Architecture. "
    "Any new idea must first become visible to the client. "
    "For every Director, Engine, Rule, or Memory ask: "
    "What changes in the client's first impression? "
    "If the answer is only better architecture — the work is unfinished."
)

LAW_2_NAME = "Reality Over Architecture"

# What the client actually sees — everything else is invisible
CLIENT_SEES = (
    "first_screen",
    "time_to_result",
    "quality_of_result",
)

ERA_NAME = "Virtus Core Studio Era"
ERA_GOAL = (
    "Stop competing with website constructors. "
    "Compete with professional digital studios on result quality."
)
ERA_PRODUCT_NAME = "Digital Experience Generation"  # not Website Builder
ERA_ALT_NAME = "Business Experience Generation"
ERA_NEXT_PROGRAM = "Studio Intelligence"  # after Goal B — not Goal C
ERA_PRODUCT_AIM = "digital brands"  # not websites


@dataclass(frozen=True)
class LawVerdict:
    law: str
    ok: bool
    action: str  # CONTINUE | REBUILD
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def enforce_law_1(
    *,
    taste_overall: float,
    prior_best_overall: float | None,
    template_like: bool,
    constructor_like: bool,
    below_studio_bar: bool,
    margin: float = 2.0,
) -> LawVerdict:
    """Immutable quality ratchet. Never returns PASS."""
    reasons: list[str] = []
    if template_like:
        reasons.append("Template repeat")
    if constructor_like:
        reasons.append("Constructor look")
    if below_studio_bar:
        reasons.append("Below modern digital-studio bar")
    if prior_best_overall is not None and taste_overall + margin < prior_best_overall:
        reasons.append(
            f"Worse than prior best ({taste_overall:.0f} < {prior_best_overall:.0f})"
        )
    if reasons:
        return LawVerdict(law=LAW_1_EN, ok=False, action="REBUILD", reasons=tuple(reasons))
    return LawVerdict(law=LAW_1_EN, ok=True, action="CONTINUE", reasons=())


def check_law_2_client_visible(*, first_impression_change: str) -> LawVerdict:
    """Law #2 gate: unfinished if only architecture improved.

    Pass a short answer to: what changes in the client's first impression?
    Empty / architecture-only → work continues (not DONE).
    """
    text = (first_impression_change or "").strip().lower()
    architecture_only = (
        not text
        or text in {"nothing", "n/a", "none", "пока ничего", "-"}
        or ("architect" in text and "impression" not in text and "screen" not in text)
        or ("архитектур" in text and "впечатл" not in text and "экран" not in text)
    )
    if architecture_only:
        return LawVerdict(
            law=LAW_2_EN,
            ok=False,
            action="CONTINUE_WORK",
            reasons=("No client-visible first-impression change yet",),
        )
    return LawVerdict(law=LAW_2_EN, ok=True, action="CLIENT_VISIBLE", reasons=())
