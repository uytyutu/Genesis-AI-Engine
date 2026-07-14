"""Person Memory facade — observe turns, load understanding."""

from __future__ import annotations

from pathlib import Path

from app.integration.vector_intelligence.person_memory.extract import extract_and_apply
from app.integration.vector_intelligence.person_memory.profile import build_planner_memory_block
from app.integration.vector_intelligence.person_memory.schema import PersonProfile
from app.integration.vector_intelligence.person_memory.store import PersonMemoryStore
from app.integration.vector_intelligence.pipeline import VectorTurnPlan


class PersonMemoryService:
    def __init__(self, memory_dir: Path) -> None:
        self._store = PersonMemoryStore(memory_dir)

    def load(self, visitor_id: str) -> PersonProfile:
        return self._store.load(visitor_id)

    def observe_turn(
        self,
        visitor_id: str,
        user_message: str,
        *,
        turn: VectorTurnPlan | None = None,
    ) -> PersonProfile:
        profile = self._store.load(visitor_id)
        profile = extract_and_apply(
            self._store,
            profile,
            user_message,
            turn=turn,
        )
        self._store.save(profile)
        return profile

    def planner_block(self, visitor_id: str, turn: VectorTurnPlan) -> str:
        return build_planner_memory_block(self.load(visitor_id), turn)

    def active_path_summary(self, visitor_id: str) -> str | None:
        summary = self.load(visitor_id).active_path.summary
        return summary or None
