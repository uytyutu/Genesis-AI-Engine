"""Structured Vector chat pipeline tracing — P0 diagnostics (CEO Product Reality)."""

from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("vector.pipeline")

_TRACE: ContextVar[VectorPipelineTrace | None] = ContextVar("vector_pipeline_trace", default=None)


@dataclass
class VectorPipelineTrace:
    request_id: str
    visitor_id: str
    question_preview: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    _memory_dir: Path | None = None

    def step(self, name: str, **detail: Any) -> None:
        row = {
            "at": datetime.now(timezone.utc).isoformat(),
            "step": name,
            **{k: v for k, v in detail.items() if v is not None},
        }
        self.steps.append(row)
        detail_s = " ".join(f"{k}={v!r}" for k, v in detail.items() if v is not None)
        logger.info(
            "VECTOR_PIPELINE request=%s visitor=%s step=%s %s",
            self.request_id,
            self.visitor_id[:32],
            name,
            detail_s,
        )

    def finish(self, *, ok: bool, **detail: Any) -> None:
        self.step("finish", ok=ok, **detail)
        if not self._memory_dir:
            return
        log_path = self._memory_dir / "vector_pipeline.jsonl"
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "request_id": self.request_id,
                            "visitor_id": self.visitor_id,
                            "question": self.question_preview,
                            "ok": ok,
                            "steps": self.steps,
                            **detail,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except OSError as exc:
            logger.debug("vector pipeline log skip: %s", exc)


def start_trace(
    *,
    visitor_id: str,
    question: str = "",
    memory_dir: Path | None = None,
) -> VectorPipelineTrace:
    trace = VectorPipelineTrace(
        request_id=uuid.uuid4().hex[:12],
        visitor_id=(visitor_id or "anonymous")[:64],
        question_preview=(question or "")[:160],
        _memory_dir=memory_dir,
    )
    _TRACE.set(trace)
    trace.step("api_received")
    return trace


def current_trace() -> VectorPipelineTrace | None:
    return _TRACE.get()


def trace_step(name: str, **detail: Any) -> None:
    trace = _TRACE.get()
    if trace:
        trace.step(name, **detail)
