"""OR3 — Baseline in-process metrics (no Prometheus required)."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any

ENGINE_ID = "operational_metrics_v1"


@dataclass
class OperationalMetrics:
    ai_latency_ms_sum: float = 0.0
    ai_latency_count: int = 0
    provider_failures: int = 0
    conversation_count: int = 0
    actions_executed: int = 0
    actions_rejected: int = 0
    draft_generation_count: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_ai_latency(self, duration_ms: float) -> None:
        with self._lock:
            self.ai_latency_ms_sum += max(0.0, duration_ms)
            self.ai_latency_count += 1

    def record_provider_failure(self) -> None:
        with self._lock:
            self.provider_failures += 1

    def record_conversation(self) -> None:
        with self._lock:
            self.conversation_count += 1

    def record_action_executed(self) -> None:
        with self._lock:
            self.actions_executed += 1

    def record_action_rejected(self) -> None:
        with self._lock:
            self.actions_rejected += 1

    def record_draft(self) -> None:
        with self._lock:
            self.draft_generation_count += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg = (
                self.ai_latency_ms_sum / self.ai_latency_count
                if self.ai_latency_count
                else 0.0
            )
            return {
                "ai_latency_avg_ms": round(avg, 2),
                "ai_latency_samples": self.ai_latency_count,
                "provider_failures": self.provider_failures,
                "conversation_count": self.conversation_count,
                "business_actions_executed": self.actions_executed,
                "business_actions_rejected": self.actions_rejected,
                "draft_generation_count": self.draft_generation_count,
                "average_response_time_ms": round(avg, 2),
            }

    def reset(self) -> None:
        with self._lock:
            self.ai_latency_ms_sum = 0.0
            self.ai_latency_count = 0
            self.provider_failures = 0
            self.conversation_count = 0
            self.actions_executed = 0
            self.actions_rejected = 0
            self.draft_generation_count = 0


_METRICS = OperationalMetrics()


def get_operational_metrics() -> OperationalMetrics:
    return _METRICS
