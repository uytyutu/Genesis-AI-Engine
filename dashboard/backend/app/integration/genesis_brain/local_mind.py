"""Genesis Local Mind — brief-driven offline fallback when cloud LLM unavailable."""

from __future__ import annotations

from typing import Any

from app.integration.genesis_brain.brief_speech import (
    BriefSpeechSynthesizer,
    clean_user_messages,
    extract_clean_user_text,
)
from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.executive_brain import ExecutiveDecision
from app.integration.genesis_brain.layers.knowledge import GenesisKnowledgeLayer
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief
from app.integration.genesis_brain.layers.thinking_engine import ThinkingEngine
from app.integration.genesis_brain.layers.executive_brain import GenesisExecutiveBrain
from app.integration.genesis_brain.types import ChatResult


class LocalMindProvider:
    """v3 — speech from Thinking Brief, not keyword templates."""

    provider_id = "genesis-local"

    @property
    def model_name(self) -> str:
        return "brief_speech"

    def __init__(self, packages: list[dict[str, Any]] | None = None) -> None:
        self._knowledge = GenesisKnowledgeLayer(packages)
        self._thinking = ThinkingEngine()
        self._executive = GenesisExecutiveBrain()
        self._synth = BriefSpeechSynthesizer()

    def available(self) -> bool:
        return True

    def chat(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        conversation_state: ConversationState | None = None,
        visitor_id: str = "local",
        turn_index: int = 0,
        thinking_brief: ThinkingBrief | None = None,
        executive_decision: ExecutiveDecision | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        clean_messages = clean_user_messages(messages)
        state = conversation_state or ConversationState.from_messages(clean_messages)
        if turn_index <= 0:
            turn_index = sum(1 for m in clean_messages if m.get("role") == "user")
        last_user = ""
        if clean_messages:
            for msg in reversed(clean_messages):
                if msg.get("role") == "user":
                    last_user = (msg.get("content") or "").strip()
                    break
        if not last_user and messages:
            last_user = extract_clean_user_text(messages[-1].get("content", ""))

        if thinking_brief is None or executive_decision is None:
            thinking_brief = self._thinking.think(
                last_user=last_user,
                messages=clean_messages,
                state=state,
                emotional=None,
                memory_inferences=None,
            )
            executive_decision = self._executive.decide_from_thinking(
                thinking_brief,
                state=state,
                messages=clean_messages,
                last_user=last_user,
            )

        draft = self._synth.speak(
            thinking_brief,
            executive_decision,
            state=state,
            visitor_id=visitor_id,
            turn_index=turn_index,
            last_user=last_user,
            messages=clean_messages,
        )
        return ChatResult(answer=draft, provider_id=self.provider_id)
