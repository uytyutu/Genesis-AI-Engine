"""
Genesis Mind v3 — Thinking Engine.

Internal thinking cycle before every response.
ThinkingBrief is NEVER shown, logged, persisted, or sent to the client.
"""

from __future__ import annotations

from typing import Any

from app.config import cloud_proof_mode
from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalBrief
from app.integration.genesis_brain.layers.goal_analysis import GoalAnalysisLayer
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief
from app.integration.genesis_brain.semantic_briefs import enrich_thinking_brief


class ThinkingEngine:
    """Inference layer — conclusions, not keyword tags."""

    def __init__(self) -> None:
        self._goal = GoalAnalysisLayer()

    def think(
        self,
        *,
        last_user: str,
        messages: list[dict[str, str]],
        state: ConversationState,
        emotional: EmotionalBrief | None = None,
        memory_inferences: dict[str, Any] | None = None,
    ) -> ThinkingBrief:
        goal = self._goal.analyze(last_user, messages, state, emotional)
        base = self._from_goal(goal, state, messages)
        if cloud_proof_mode():
            return base
        return enrich_thinking_brief(
            base, goal, state, last_user, messages, memory_inferences
        )

    def _from_goal(
        self,
        goal: Any,
        state: ConversationState,
        messages: list[dict[str, str]],
    ) -> ThinkingBrief:
        known = list(goal.known_facts)
        if state.budget_display():
            known.append(f"бюджет: {state.budget_display()}")
        if state.city:
            known.append(f"город: {state.city}")
        if state.business_type:
            known.append(f"ниша: {state.business_type}")

        missing: list[str] = []
        for gap in state.missing_critical(messages):
            if gap == "country":
                missing.append("страна")
            elif gap == "budget":
                missing.append("бюджет")
            elif gap == "niche":
                missing.append("формат (офлайн/онлайн)")

        emotion_ru = {
            "hopeful": "надежда",
            "anxious": "тревога",
            "heavy": "тяжесть",
            "neutral": "нейтральное",
            "excited": "воодушевление",
            "frustrated": "раздражение",
            "grateful": "благодарность",
        }.get(goal.emotion, "нейтральное")

        action_map = {
            "comfort": "comfort",
            "answer": "answer",
            "advise": "advise",
            "challenge": "challenge",
            "acknowledge": "answer",
            "one_question": "ask_one_question",
            "close": "wait",
        }
        recommended = action_map.get(goal.helpful_action, "answer")

        return ThinkingBrief(
            conversation_goal=goal.surface_topic or "диалог",
            real_goal=goal.implicit_need,
            implicit_need=goal.implicit_need,
            known_facts=tuple(known),
            missing_facts=tuple(missing),
            emotional_state=emotion_ru,
            confidence=min(0.95, max(0.35, goal.reasoning_chain.count(".") * 0.15 + 0.5)),
            possible_actions=("answer", "advise", "comfort", "explore", "ask_one_question"),
            recommended_action=recommended,
            why=goal.reasoning_chain,
            risks=(),
            best_response_strategy="этап Journey: по контексту хода; ситуация: уточняется goal layer",
            optional_question=goal.optional_question,
            thread=goal.thread,
        )
