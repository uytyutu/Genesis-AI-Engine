"""G3.1 service — Owner gate for all changes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.evolution.analyzer import analyze_support_message
from app.evolution.models import (
    ChangeProposal,
    KnowledgeLedgerEntry,
    LearningQueueItem,
    _utc_now,
    new_id,
    new_proposal,
    new_ticket,
)
from app.evolution.store import EvolutionStore

ENGINE_ID = "g31_evolution_support_service_v1"
OWNER_APPROVAL_RULE = "AI may recommend changes. Only the Owner approves changes."
EVOLUTION_MISSION = (
    "Evolution Center не создаёт новые функции. Он делает существующую платформу "
    "безопаснее, стабильнее, полезнее и умнее на основе подтверждённого опыта."
)


class EvolutionSupportService:
    def __init__(self, memory_dir: Path) -> None:
        self._store = EvolutionStore(memory_dir)

    def submit_ticket(self, *, message: str, contact: str = "") -> dict[str, Any]:
        if not (message or "").strip():
            raise ValueError("message_required")
        ticket = new_ticket(message=message, contact=contact)
        analysis = analyze_support_message(
            message, ledger=self._store.list_ledger()
        )
        ticket.category = analysis.category
        ticket.fingerprint = analysis.fingerprint
        ticket.status = "proposed"
        self._store.append_ticket(ticket)

        proposal = new_proposal(
            ticket_id=ticket.ticket_id,
            problem=analysis.problem,
            analysis=analysis.analysis,
            suggested_fix=analysis.suggested_fix,
            diff_preview=analysis.diff_preview,
            diff_summary=analysis.diff_summary,
            risk=analysis.risk,
            confidence_percent=analysis.confidence_percent,
            confidence_basis=analysis.confidence_basis,
            business_impact=analysis.business_impact,
            rollback_available=analysis.rollback_available,
            tests_planned=analysis.tests_planned,
            similar_case_ids=analysis.similar_case_ids,
        )
        self._store.append_proposal(proposal)
        return {
            "ticket": ticket.as_dict(),
            "proposal": proposal.as_dict(),
            "owner_approval_required": True,
            "rule": OWNER_APPROVAL_RULE,
            "mission": EVOLUTION_MISSION,
            "applied": False,
        }

    def list_proposals(self, *, status: str | None = None) -> list[dict[str, Any]]:
        rows = self._store.list_proposals()
        if status:
            rows = [r for r in rows if r.status == status]
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return [r.as_dict() for r in rows]

    def get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        row = self._store.get_proposal(proposal_id)
        return row.as_dict() if row else None

    def list_ledger(self) -> list[dict[str, Any]]:
        return [r.as_dict() for r in self._store.list_ledger()]

    def list_learning_queue(self) -> list[dict[str, Any]]:
        return [r.as_dict() for r in self._store.list_learning()]

    def approve_proposal(
        self, proposal_id: str, *, owner_note: str = ""
    ) -> dict[str, Any]:
        """First Owner confirm — creates Rule Candidate only (not ledger yet)."""
        proposal = self._require_pending(proposal_id)
        proposal.status = "approved"
        proposal.decided_at = _utc_now()
        proposal.owner_note = (owner_note or "").strip()[:500]
        proposal.rule_candidate_pending = True
        self._save_proposal(proposal)
        self._store.update_ticket_status(proposal.ticket_id, "resolved")

        learning = LearningQueueItem(
            learning_id=new_id("lrn"),
            proposal_id=proposal.proposal_id,
            knowledge_id="",
            status="candidate",
            created_at=_utc_now(),
            note="Rule Candidate — awaits second Owner confirmation before Knowledge Ledger",
            problem=proposal.problem,
            solution=proposal.suggested_fix,
            autotest="; ".join(proposal.tests_planned) or "pending",
            awaits_second_confirm=True,
        )
        self._store.append_learning(learning)
        return {
            "proposal": proposal.as_dict(),
            "learning": learning.as_dict(),
            "knowledge": None,
            "rule_candidate": True,
            "awaits_second_confirm": True,
            "applied": False,
            "rule": OWNER_APPROVAL_RULE,
        }

    def promote_rule_candidate(
        self, learning_id: str, *, owner_note: str = ""
    ) -> dict[str, Any]:
        """Second Owner confirm — promote candidate into Knowledge Ledger."""
        item = self._require_learning(learning_id, want="candidate")
        knowledge = KnowledgeLedgerEntry(
            knowledge_id=new_id("kn"),
            entry_type="Support",
            source="G3.1",
            problem=item.problem,
            solution=item.solution,
            autotest=item.autotest or "pending",
            reuse="Confirmed rule — reuse on similar cases; still not auto-applied to code",
            created_at=_utc_now(),
            proposal_id=item.proposal_id,
        )
        self._store.append_ledger(knowledge)
        item.status = "promoted"
        item.knowledge_id = knowledge.knowledge_id
        item.awaits_second_confirm = False
        item.note = (owner_note or "Promoted to Knowledge Ledger").strip()[:500]
        self._save_learning(item)
        # clear pending flag on proposal if present
        proposal = self._store.get_proposal(item.proposal_id)
        if proposal is not None:
            proposal.rule_candidate_pending = False
            self._save_proposal(proposal)
        return {
            "learning": item.as_dict(),
            "knowledge": knowledge.as_dict(),
            "applied": False,
            "rule": OWNER_APPROVAL_RULE,
        }

    def dismiss_rule_candidate(
        self, learning_id: str, *, owner_note: str = ""
    ) -> dict[str, Any]:
        item = self._require_learning(learning_id, want="candidate")
        item.status = "dismissed"
        item.awaits_second_confirm = False
        item.note = (owner_note or "Dismissed — not added to Knowledge Ledger").strip()[
            :500
        ]
        self._save_learning(item)
        proposal = self._store.get_proposal(item.proposal_id)
        if proposal is not None:
            proposal.rule_candidate_pending = False
            self._save_proposal(proposal)
        return {
            "learning": item.as_dict(),
            "knowledge": None,
            "applied": False,
            "rule": OWNER_APPROVAL_RULE,
        }

    def reject_proposal(
        self, proposal_id: str, *, owner_note: str = ""
    ) -> dict[str, Any]:
        proposal = self._require_pending(proposal_id)
        proposal.status = "rejected"
        proposal.decided_at = _utc_now()
        proposal.owner_note = (owner_note or "").strip()[:500]
        proposal.rule_candidate_pending = False
        self._save_proposal(proposal)
        self._store.update_ticket_status(proposal.ticket_id, "closed")
        return {
            "proposal": proposal.as_dict(),
            "applied": False,
            "rule": OWNER_APPROVAL_RULE,
        }

    def _require_pending(self, proposal_id: str) -> ChangeProposal:
        proposal = self._store.get_proposal(proposal_id)
        if proposal is None:
            raise ValueError("proposal_not_found")
        if proposal.status != "pending_owner":
            raise ValueError("proposal_not_pending")
        return proposal

    def _require_learning(
        self, learning_id: str, *, want: str
    ) -> LearningQueueItem:
        for item in self._store.list_learning():
            if item.learning_id == learning_id:
                if item.status != want:
                    raise ValueError("learning_not_candidate")
                return item
        raise ValueError("learning_not_found")

    def _save_proposal(self, updated: ChangeProposal) -> None:
        rows = self._store.list_proposals()
        out: list[ChangeProposal] = []
        for row in rows:
            out.append(updated if row.proposal_id == updated.proposal_id else row)
        self._store.rewrite_proposals(out)

    def _save_learning(self, updated: LearningQueueItem) -> None:
        rows = self._store.list_learning()
        out: list[LearningQueueItem] = []
        for row in rows:
            out.append(updated if row.learning_id == updated.learning_id else row)
        self._store.rewrite_learning(out)
