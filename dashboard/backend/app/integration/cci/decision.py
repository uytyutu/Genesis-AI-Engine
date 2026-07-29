"""Canonical CCI Decision contract — compatible across future CCI versions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

DecisionKind = Literal["auto_send", "HOLD", "never"]


@dataclass(frozen=True)
class RejectedCandidate:
    email: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Decision:
    """Canonical contract. Future CCI versions must keep these fields."""

    chosen: str | None
    decision: DecisionKind
    contact_confidence: int
    company_fit: int | None
    reasons_selected: tuple[str, ...]
    rejected: tuple[RejectedCandidate, ...]
    cci_version: str
    ruleset: str
    trace_id: str
    # Extra audit (optional for callers; always present for golden/debug)
    raw_score: int = 0
    candidates_scored: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.reasons_selected and self.decision == "auto_send":
            raise ValueError("CCI: no explanation → no auto_send decision")
        if self.decision == "auto_send" and not self.chosen:
            raise ValueError("CCI: auto_send requires chosen email")
        if self.contact_confidence < 0 or self.contact_confidence > 100:
            raise ValueError("CCI: contact_confidence must be 0..100")


def decision_to_dict(d: Decision) -> dict[str, Any]:
    payload = asdict(d)
    return payload
