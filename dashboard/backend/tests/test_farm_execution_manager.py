"""Execution Manager — refuse gate + estimates (no live LLM required)."""

from __future__ import annotations

from swarm.farm_execution_manager import (
    capability_gate,
    estimate_execution,
    apply_file_patches,
)


def test_refuse_kernel_driver():
    gate = capability_gate(
        {
            "title": "Add Linux kernel driver for XYZ",
            "overall_confidence_pct": 90,
            "languages": ["c"],
            "blockers": [],
        }
    )
    assert gate["route"] == "refuse"
    assert gate["can_execute"] is False


def test_refuse_low_confidence():
    gate = capability_gate(
        {
            "title": "Fix typo",
            "overall_confidence_pct": 34,
            "languages": ["python"],
            "blockers": [],
        }
    )
    assert gate["route"] == "refuse"


def test_local_engineer_high_confidence_python(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    gate = capability_gate(
        {
            "title": "Fix pagination race in API",
            "overall_confidence_pct": 92,
            "languages": ["python"],
            "blockers": [],
        }
    )
    assert gate["route"] == "local_engineer"


def test_needs_external_when_no_llm_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_LLM_API_KEY", raising=False)
    gate = capability_gate(
        {
            "title": "Fix pagination race in API",
            "overall_confidence_pct": 92,
            "languages": ["python"],
            "blockers": [],
        }
    )
    assert gate["route"] == "needs_external"


def test_needs_external_medium_confidence():
    gate = capability_gate(
        {
            "title": "Improve CI matrix",
            "overall_confidence_pct": 70,
            "languages": ["python"],
            "blockers": [],
        }
    )
    assert gate["route"] == "needs_external"


def test_estimate_fields():
    est = estimate_execution(
        {
            "overall_confidence_pct": 88,
            "acceptance_pct": 80,
            "estimated_hours": 1.5,
            "competitors": 1,
            "reward_usd": 120,
        }
    )
    assert est["success_probability_pct"] >= 70
    assert est["estimated_minutes"] == 90
    assert "REAL" in est["note_ru"]


def test_apply_file_patches_rejects_traversal(tmp_path):
    bad = apply_file_patches(
        tmp_path, [{"path": "../outside.txt", "content": "x"}]
    )
    assert bad["touched"] == []
    assert bad["errors"]
