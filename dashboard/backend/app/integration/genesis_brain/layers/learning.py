"""
Genesis Learning Layer — improve from dialogue outcomes (foundation stub).

Mission 5+ expands: success/failure signals, prompt tuning, owner insights.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent.parent.parent / "memory"


class GenesisLearningLayer:
    """Records dialogue metadata for future self-improvement — no ML yet."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._log = (memory_dir or _DEFAULT_MEMORY) / "genesis_brain" / "learning.jsonl"
        self._candidates = (memory_dir or _DEFAULT_MEMORY) / "workforce" / "training_candidates.jsonl"
        self._log.parent.mkdir(parents=True, exist_ok=True)
        self._candidates.parent.mkdir(parents=True, exist_ok=True)

    def observe_turn(
        self,
        *,
        visitor_id: str,
        provider_id: str,
        user_len: int,
        answer_len: int,
        used_local: bool,
        workforce_task: str | None = None,
        user_message: str = "",
        answer_preview: str = "",
    ) -> None:
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "visitor_id": visitor_id[:64],
            "provider_id": provider_id,
            "user_len": user_len,
            "answer_len": answer_len,
            "used_local": used_local,
            "workforce_task": workforce_task,
        }
        try:
            with self._log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.debug("Learning log skip: %s", exc)

        if user_message and answer_preview:
            candidate = {
                **row,
                "user_message": user_message[:500],
                "answer_preview": answer_preview[:500],
                "review_status": "pending",
            }
            try:
                with self._candidates.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(candidate, ensure_ascii=False) + "\n")
            except OSError:
                pass

    def reflect_turn(
        self,
        *,
        visitor_id: str,
        user_message: str,
        answer: str,
        employee_chosen: str,
        workforce_task: str | None,
        confidence: float,
        calibration_passed: bool,
        calibration_reasons: list[str] | None = None,
        jury: dict[str, Any] | None = None,
        plan_order: list[str] | None = None,
    ) -> None:
        """Director self-review — experience for Genesis, not shown to user."""
        reflections = (self._log.parent) / "director_reflections.jsonl"
        weak = not calibration_passed or confidence < 0.55
        alt = None
        if plan_order and employee_chosen and plan_order[0] != employee_chosen:
            alt = plan_order[0]
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "visitor_id": visitor_id[:64],
            "employee_chosen": employee_chosen,
            "workforce_task": workforce_task,
            "confidence": round(confidence, 3),
            "weak_answer": weak,
            "why_weak": (
                (calibration_reasons or ["low executive confidence"])[0]
                if weak
                else None
            ),
            "misunderstood": None if calibration_passed else "calibration flagged rewrite",
            "better_employee_maybe": alt,
            "remember": user_message[:200] if user_message else "",
            "improve_next": (
                "escalate or invoke jury earlier"
                if weak and employee_chosen != "genesis-local"
                else "continue"
            ),
            "jury": jury or {"invoked": False},
            "answer_len": len(answer),
        }
        try:
            with reflections.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.debug("Director reflection skip: %s", exc)
