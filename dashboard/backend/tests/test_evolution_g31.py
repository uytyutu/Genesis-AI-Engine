"""G3.1 — AI Support & Continuous Improvement (Owner gate)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.evolution import ENGINE_ID
from app.evolution.analyzer import analyze_support_message
from app.evolution.models import KnowledgeLedgerEntry
from app.evolution.service import (
    EVOLUTION_MISSION,
    OWNER_APPROVAL_RULE,
    EvolutionSupportService,
)


def test_engine_id():
    assert ENGINE_ID == "g31_evolution_support_v1"


def test_form_ticket_creates_pending_proposal_not_applied(tmp_path: Path):
    svc = EvolutionSupportService(tmp_path)
    out = svc.submit_ticket(message="У меня не работает форма на сайте.")
    assert out["applied"] is False
    assert out["owner_approval_required"] is True
    assert out["rule"] == OWNER_APPROVAL_RULE
    assert out["mission"] == EVOLUTION_MISSION
    pr = out["proposal"]
    assert pr["status"] == "pending_owner"
    assert pr["risk"] in {"low", "medium", "high"}
    assert isinstance(pr["confidence_percent"], int)
    assert 0 <= pr["confidence_percent"] <= 100
    assert pr["confidence_basis"]
    assert "clients_affected_estimate" in pr["business_impact"]
    assert pr["rollback_available"] is True
    assert pr["diff_summary"]
    assert "form" in out["ticket"]["category"] or out["ticket"]["category"] == "form"
    assert pr["security_suite"].endswith("s1_security_regression_suite.py")


def test_approve_creates_rule_candidate_not_ledger(tmp_path: Path):
    svc = EvolutionSupportService(tmp_path)
    created = svc.submit_ticket(message="Stripe payment not confirmed")
    pid = created["proposal"]["proposal_id"]
    approved = svc.approve_proposal(pid, owner_note="OK for candidate")
    assert approved["applied"] is False
    assert approved["rule_candidate"] is True
    assert approved["awaits_second_confirm"] is True
    assert approved["knowledge"] is None
    assert approved["proposal"]["status"] == "approved"
    assert approved["proposal"]["rule_candidate_pending"] is True
    assert approved["learning"]["status"] == "candidate"
    assert approved["learning"]["awaits_second_confirm"] is True
    assert svc.list_ledger() == []
    assert len(svc.list_learning_queue()) == 1


def test_second_confirm_promotes_to_ledger(tmp_path: Path):
    svc = EvolutionSupportService(tmp_path)
    created = svc.submit_ticket(message="форма не отправляется")
    approved = svc.approve_proposal(created["proposal"]["proposal_id"])
    lid = approved["learning"]["learning_id"]
    promoted = svc.promote_rule_candidate(lid, owner_note="Confirm rule")
    assert promoted["applied"] is False
    assert promoted["knowledge"]["source"] == "G3.1"
    assert promoted["learning"]["status"] == "promoted"
    assert len(svc.list_ledger()) == 1
    assert svc.list_learning_queue()[0]["awaits_second_confirm"] is False


def test_dismiss_rule_candidate_skips_ledger(tmp_path: Path):
    svc = EvolutionSupportService(tmp_path)
    created = svc.submit_ticket(message="Login session expired too fast")
    approved = svc.approve_proposal(created["proposal"]["proposal_id"])
    lid = approved["learning"]["learning_id"]
    dismissed = svc.dismiss_rule_candidate(lid)
    assert dismissed["knowledge"] is None
    assert dismissed["learning"]["status"] == "dismissed"
    assert svc.list_ledger() == []


def test_reject_does_not_write_ledger(tmp_path: Path):
    svc = EvolutionSupportService(tmp_path)
    created = svc.submit_ticket(message="Login session expired too fast")
    pid = created["proposal"]["proposal_id"]
    rejected = svc.reject_proposal(pid, owner_note="Not now")
    assert rejected["applied"] is False
    assert rejected["proposal"]["status"] == "rejected"
    assert svc.list_ledger() == []
    assert svc.list_learning_queue() == []


def test_cannot_approve_twice(tmp_path: Path):
    svc = EvolutionSupportService(tmp_path)
    created = svc.submit_ticket(message="security XSS concern on upload")
    pid = created["proposal"]["proposal_id"]
    svc.approve_proposal(pid)
    with pytest.raises(ValueError, match="proposal_not_pending"):
        svc.approve_proposal(pid)


def test_similar_cases_from_ledger():
    ledger = [
        KnowledgeLedgerEntry(
            knowledge_id="kn-1",
            entry_type="Support",
            source="G3.1",
            problem="form validation broken",
            solution="fix endpoint wiring",
            autotest="t.py",
            reuse="forms",
            created_at="2026-07-23T00:00:00+00:00",
        )
    ]
    result = analyze_support_message("форма не отправляется", ledger=ledger)
    assert result.category == "form"
    assert "kn-1" in result.similar_case_ids
    assert result.confidence_percent >= 68
    assert result.diff_summary
    assert result.rollback_available is True
