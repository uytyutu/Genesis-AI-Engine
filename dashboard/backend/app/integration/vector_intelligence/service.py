"""Vector Intelligence — life context, initiative, action-first planning."""

from __future__ import annotations

from pathlib import Path

from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer
from app.integration.vector_intelligence.client_life_context import (
    ClientLifeContext,
    build_client_life_context,
)
from app.integration.vector_intelligence.initiative import (
    build_action_first_hint,
    build_proactive_greeting,
    touch_last_seen,
)
from app.integration.vector_intelligence.pipeline import VectorTurnPlan, analyze_turn, compact_fast_lane_hint


class VectorIntelligenceService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory_dir = memory_dir
        self._memory = GenesisMemoryLayer(memory_dir)

    def life_context(self, visitor_id: str) -> ClientLifeContext:
        return build_client_life_context(visitor_id, memory_dir=self._memory_dir)

    def proactive_greeting(self, visitor_id: str) -> str:
        ctx = self.life_context(visitor_id)
        greeting = build_proactive_greeting(ctx)
        data = self._memory.load(visitor_id)
        touch_last_seen(data)
        self._memory.save(visitor_id, data)
        return greeting

    def plan_turn(
        self,
        visitor_id: str,
        user_message: str,
        *,
        history: list[dict[str, str]] | None = None,
        has_attachments: bool = False,
    ) -> tuple[VectorTurnPlan, str]:
        """Single pipeline pass — Planner mandate + Workforce routing metadata."""
        ctx = self.life_context(visitor_id)
        plan = analyze_turn(
            user_message,
            history=history,
            life=ctx,
            has_attachments=has_attachments,
        )
        return plan, compact_fast_lane_hint(plan)

    def action_first_hint(
        self,
        visitor_id: str,
        *,
        user_message: str = "",
        history: list[dict[str, str]] | None = None,
        has_attachments: bool = False,
    ) -> str:
        ctx = self.life_context(visitor_id)
        return build_action_first_hint(
            ctx,
            user_message=user_message,
            history=history,
            has_attachments=has_attachments,
            memory_dir=self._memory_dir,
        )

    def analyze_turn(
        self,
        user_message: str,
        *,
        visitor_id: str,
        history: list[dict[str, str]] | None = None,
        has_attachments: bool = False,
    ):
        from app.integration.vector_intelligence.pipeline import analyze_turn as _analyze

        return _analyze(
            user_message,
            history=history,
            life=self.life_context(visitor_id),
            has_attachments=has_attachments,
        )

    def observe_after_turn(
        self,
        visitor_id: str,
        user_message: str,
        *,
        turn: VectorTurnPlan,
    ) -> None:
        from app.integration.vector_intelligence.person_memory.service import PersonMemoryService

        PersonMemoryService(self._memory_dir).observe_turn(
            visitor_id,
            user_message,
            turn=turn,
        )

    def touch_session(self, visitor_id: str) -> None:
        data = self._memory.load(visitor_id)
        touch_last_seen(data)
        self._memory.save(visitor_id, data)
