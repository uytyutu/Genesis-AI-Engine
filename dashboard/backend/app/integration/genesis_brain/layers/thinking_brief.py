"""ThinkingBrief — internal Genesis Mind state (never exposed to client)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.integration.genesis_brain.layers.goal_analysis import ThreadContext


@dataclass(frozen=True)
class ThinkingBrief:
    """Internal state of Genesis — not a response template."""

    conversation_goal: str = ""
    real_goal: str = ""
    implicit_need: str = ""
    known_facts: tuple[str, ...] = ()
    missing_facts: tuple[str, ...] = ()
    emotional_state: str = "нейтральное"
    confidence: float = 0.5
    possible_actions: tuple[str, ...] = ()
    recommended_action: str = "answer"
    why: str = ""
    risks: tuple[str, ...] = ()
    best_response_strategy: str = ""
    optional_question: str | None = None
    thread: ThreadContext = field(default_factory=ThreadContext)
    avoid: tuple[str, ...] = (
        "шаблоны",
        "продажа без запроса",
        "factory",
        "studio",
        "6 страниц",
        "650–850",
    )

    def to_llm_block(self) -> str:
        """For system prompt only — never user-visible."""
        lines = [
            "[Thinking Brief — внутренний контекст. Не цитируй дословно.]",
            f"conversation_goal: {self.conversation_goal}",
            f"real_goal: {self.real_goal}",
            f"implicit_need: {self.implicit_need}",
            f"emotional_state: {self.emotional_state}",
            f"confidence: {self.confidence:.2f}",
            f"recommended_action: {self.recommended_action}",
            f"why: {self.why}",
            f"journey_context: {self.best_response_strategy}",
        ]
        if self.known_facts:
            lines.append("known_facts: " + "; ".join(self.known_facts))
        if self.missing_facts:
            lines.append("missing_facts: " + "; ".join(self.missing_facts))
        if self.risks:
            lines.append("risks: " + "; ".join(self.risks))
        if self.possible_actions:
            lines.append("possible_actions: " + ", ".join(self.possible_actions))
        if self.optional_question:
            lines.append(f"optional_one_question: {self.optional_question}")
        if self.avoid:
            lines.append("avoid: " + ", ".join(self.avoid))
        if self.confidence < 0.55:
            lines.append(
                "uncertainty_rule: не притворяйся всезнайкой — "
                "«Не могу утверждать наверняка» или «Есть несколько точек зрения» уместны."
            )
        return "\n".join(lines)

    def to_llm_mandate(
        self,
        *,
        executive_action: str,
        executive_confidence: float,
        memory_inferences: dict[str, Any] | None = None,
        conv_state: Any = None,
        personality: str = "Genesis",
    ) -> str:
        """
        Structured mandate for LLM — internal Journey context only.
        Never user-visible; injected into LLM turn only.
        """
        inf = memory_inferences or {}
        known: list[str] = list(self.known_facts)
        if conv_state is not None:
            age = getattr(conv_state, "user_age", None)
            if age:
                known.append(f"Age: {age}")
            city = getattr(conv_state, "city", None) or getattr(conv_state, "country", None)
            if city:
                known.append(f"Location: {city}")
            biz = getattr(conv_state, "business_type", None)
            if biz:
                known.append(f"Business context: {biz}")
        for key, label in (
            ("long_term_goals", "Long goals"),
            ("core_values", "Values"),
            ("communication_style", "Preferred style"),
            ("preferred_depth", "Depth"),
            ("risk_profile", "Risk profile"),
        ):
            val = inf.get(key)
            if val:
                if isinstance(val, list):
                    known.append(f"{label}: {', '.join(str(v) for v in val[:5])}")
                else:
                    known.append(f"{label}: {val}")

        lines = [
            "THINKING BRIEF",
            "",
            "Known Facts:",
        ]
        if known:
            lines.extend(f"  - {f}" for f in known)
        else:
            lines.append("  - (building from dialogue)")
        lines.extend(
            [
                "",
                f"Long Goal: {self.conversation_goal or self.real_goal or '—'}",
                f"Implicit Need: {self.implicit_need or '—'}",
                f"Emotion: {self.emotional_state}",
                f"Real Goal: {self.real_goal or '—'}",
                "",
                "Executive Decision:",
                f"  action: {executive_action}",
                f"  confidence: {executive_confidence:.2f}",
            ]
        )
        if self.optional_question:
            lines.append(f"  optional_question: {self.optional_question}")
        lines.extend(
            [
                "",
                f"Journey context: {self.best_response_strategy or '—'}",
                f"Reasoning: {self.why or '—'}",
            ]
        )
        if self.avoid:
            lines.append(f"Avoid: {', '.join(self.avoid)}")
        if self.confidence < 0.55:
            lines.append(
                "Uncertainty: do not fake expertise — honest limits are allowed."
            )
        return "\n".join(lines)

    def to_debug_dict(self) -> dict[str, object]:
        """Developer Mode only — never in production API without dev gate."""
        return {
            "conversation_goal": self.conversation_goal,
            "real_goal": self.real_goal,
            "implicit_need": self.implicit_need,
            "known_facts": list(self.known_facts),
            "missing_facts": list(self.missing_facts),
            "emotional_state": self.emotional_state,
            "confidence": self.confidence,
            "possible_actions": list(self.possible_actions),
            "recommended_action": self.recommended_action,
            "why": self.why,
            "risks": list(self.risks),
            "best_response_strategy": self.best_response_strategy,
            "optional_question": self.optional_question,
            "avoid": list(self.avoid),
            "thread": {
                "mentioned_doubt": self.thread.mentioned_doubt,
                "mentioned_wealth": self.thread.mentioned_wealth,
                "mentioned_success": self.thread.mentioned_success,
                "mentioned_age": self.thread.mentioned_age,
                "mentioned_business": self.thread.mentioned_business,
                "prior_topics": list(self.thread.prior_topics),
            },
        }
