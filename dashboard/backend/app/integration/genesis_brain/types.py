"""Types for Genesis Brain provider routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ProviderKind = Literal["openai_compatible", "local_mind"]


@dataclass(frozen=True)
class ChatResult:
    answer: str
    cta_href: str | None = None
    cta_label: str | None = None
    action: dict[str, Any] | None = None
    provider_id: str = "genesis"
    trace: dict[str, Any] | None = None
    dev_route: dict[str, Any] | None = None


@dataclass(frozen=True)
class ProviderAttempt:
    provider_id: str
    available: bool
    reason: str = ""


@dataclass(frozen=True)
class CalibrationVerdict:
    passed: bool
    needs_rewrite: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "needs_rewrite": self.needs_rewrite,
            "reasons": list(self.reasons),
        }


@dataclass
class WorkforceAttemptLog:
    employee_id: str
    employee_score: float | None = None
    latency_ms: float = 0.0
    outcome: str = "skipped"  # selected | escalated | error | skipped
    calibration: CalibrationVerdict | None = None
    error: str = ""
    skip_code: str = ""
    model: str | None = None
    raw_system: str = ""
    raw_messages: list[dict[str, str]] | None = None
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "employee_id": self.employee_id,
            "employee_score": self.employee_score,
            "latency_sec": round(self.latency_ms / 1000.0, 3),
            "outcome": self.outcome,
            "calibration": self.calibration.to_dict() if self.calibration else None,
            "error": self.error or None,
            "skip_code": self.skip_code or None,
            "model": self.model,
        }
        if self.raw_response:
            out["raw_response"] = self.raw_response
        if self.raw_system:
            out["raw_system_preview"] = self.raw_system[:4000]
        if self.raw_messages:
            out["raw_messages"] = self.raw_messages
        return out


@dataclass
class WorkforceRouteLog:
    task: str
    chosen_employee: str
    chosen_score: float | None
    chosen_latency_ms: float
    why_chosen: str
    not_chosen: list[dict[str, Any]] = field(default_factory=list)
    attempts: list[WorkforceAttemptLog] = field(default_factory=list)
    second_pass: bool = False
    escalation_count: int = 0
    used_brief_speech_fallback: bool = False
    chosen_model: str | None = None
    employee_diagnostics: list[dict[str, Any]] = field(default_factory=list)
    fallback_started_at: str | None = None
    answer_source: str = ""
    cloud_llm_used: bool = False
    llm_capability: str = ""
    proof_pin: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "llm_capability": self.llm_capability or None,
            "proof_pin": self.proof_pin,
            "chosen_employee": self.chosen_employee,
            "chosen_score": self.chosen_score,
            "chosen_latency_sec": round(self.chosen_latency_ms / 1000.0, 3),
            "chosen_model": self.chosen_model,
            "why_chosen": self.why_chosen,
            "not_chosen": self.not_chosen,
            "attempts": [a.to_dict() for a in self.attempts],
            "second_pass": self.second_pass,
            "escalation_count": self.escalation_count,
            "used_brief_speech_fallback": self.used_brief_speech_fallback,
            "employee_diagnostics": self.employee_diagnostics,
            "fallback_started_at": self.fallback_started_at,
            "answer_source": self.answer_source,
            "cloud_llm_used": self.cloud_llm_used,
        }
