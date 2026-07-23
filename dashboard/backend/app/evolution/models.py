"""G3.1 domain models — tickets, proposals, ledger, learning queue."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

TicketStatus = Literal["open", "analyzing", "proposed", "resolved", "closed"]
ProposalStatus = Literal[
    "pending_owner",
    "approved",
    "rejected",
    "superseded",
]
# candidate = awaiting second Owner confirm before Knowledge Ledger
LearningStatus = Literal["candidate", "promoted", "dismissed"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


@dataclass
class SupportTicket:
    ticket_id: str
    message: str
    contact: str
    status: TicketStatus
    created_at: str
    category: str = "general"
    fingerprint: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeProposal:
    proposal_id: str
    ticket_id: str
    status: ProposalStatus
    problem: str
    analysis: str
    suggested_fix: str
    diff_preview: str
    diff_summary: str
    risk: Literal["low", "medium", "high"]
    confidence_percent: int
    confidence_basis: list[str]
    business_impact: dict[str, Any]
    rollback_available: bool
    tests_planned: list[str]
    security_suite: str
    similar_case_ids: list[str]
    created_at: str
    decided_at: str | None = None
    owner_note: str = ""
    rule_candidate_pending: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeLedgerEntry:
    knowledge_id: str
    entry_type: str
    source: str
    problem: str
    solution: str
    autotest: str
    reuse: str
    created_at: str
    version: str = "g3.1"
    proposal_id: str = ""
    ticket_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearningQueueItem:
    learning_id: str
    proposal_id: str
    knowledge_id: str
    status: LearningStatus
    created_at: str
    note: str = ""
    problem: str = ""
    solution: str = ""
    autotest: str = ""
    awaits_second_confirm: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_ticket(*, message: str, contact: str = "") -> SupportTicket:
    return SupportTicket(
        ticket_id=new_id("tkt"),
        message=message.strip(),
        contact=(contact or "").strip()[:200],
        status="open",
        created_at=_utc_now(),
    )


def new_proposal(
    *,
    ticket_id: str,
    problem: str,
    analysis: str,
    suggested_fix: str,
    diff_preview: str,
    diff_summary: str,
    risk: Literal["low", "medium", "high"],
    confidence_percent: int,
    confidence_basis: list[str],
    business_impact: dict[str, Any],
    rollback_available: bool,
    tests_planned: list[str],
    similar_case_ids: list[str],
) -> ChangeProposal:
    return ChangeProposal(
        proposal_id=new_id("prp"),
        ticket_id=ticket_id,
        status="pending_owner",
        problem=problem,
        analysis=analysis,
        suggested_fix=suggested_fix,
        diff_preview=diff_preview,
        diff_summary=diff_summary,
        risk=risk,
        confidence_percent=confidence_percent,
        confidence_basis=confidence_basis,
        business_impact=business_impact,
        rollback_available=rollback_available,
        tests_planned=tests_planned,
        security_suite="scripts/s1_security_regression_suite.py",
        similar_case_ids=similar_case_ids,
        created_at=_utc_now(),
    )
