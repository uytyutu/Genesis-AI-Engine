"""Research Agent + Codex executor — unit tests (no live LLM)."""

from __future__ import annotations

from pathlib import Path

from swarm.farm_execution_engine import merge_execution_into_task
from swarm.farm_research_agent import (
    looks_like_research_task,
    pick_executor,
    run_research_agent,
)


def test_looks_like_research_windows():
    assert looks_like_research_task(
        {"title": "research implementation for Windows", "issue_body_preview": ""}
    )


def test_looks_like_research_rejects_plain_bug():
    assert not looks_like_research_task(
        {"title": "Fix null pointer in parser", "issue_body_preview": "crash on empty"}
    )


def test_pick_executor_codex_when_openai(monkeypatch):
    monkeypatch.setenv("FARM_EXECUTOR", "auto")
    monkeypatch.setenv("FARM_EXECUTOR_PREFER", "codex")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_GROQ_API_KEY", raising=False)
    assert pick_executor() == "codex"


def test_pick_executor_auto_prefers_groq_when_both(monkeypatch):
    monkeypatch.setenv("FARM_EXECUTOR", "auto")
    monkeypatch.delenv("FARM_EXECUTOR_PREFER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GROQ_API_KEY", "g-test")
    assert pick_executor() == "groq"


def test_pick_executor_groq_when_only_groq(monkeypatch):
    monkeypatch.setenv("FARM_EXECUTOR", "auto")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_LLM_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "g-test")
    assert pick_executor() == "groq"


def test_pick_executor_none_without_keys(monkeypatch):
    monkeypatch.setenv("FARM_EXECUTOR", "auto")
    for k in (
        "OPENAI_API_KEY",
        "GENESIS_LLM_API_KEY",
        "GROQ_API_KEY",
        "GENESIS_GROQ_API_KEY",
    ):
        monkeypatch.delenv(k, raising=False)
    assert pick_executor() == "none"


def test_research_agent_no_key_honest(tmp_path, monkeypatch):
    for k in (
        "OPENAI_API_KEY",
        "GENESIS_LLM_API_KEY",
        "GROQ_API_KEY",
        "GENESIS_GROQ_API_KEY",
    ):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("FARM_AUTO_RESEARCH", "1")
    root = tmp_path / "src"
    root.mkdir()
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    ws = tmp_path / "ws"
    ws.mkdir()
    out = run_research_agent(
        root=root,
        workspace=ws,
        task={"title": "research docs", "issue_body_preview": "document windows"},
        plan={"steps": [{"title": "read"}]},
        related=["README.md"],
        executor="none",
    )
    assert out["ok"] is False
    assert out["can_generate_patch"] is False
    assert out["files_touched"] == []


def test_merge_execution_needs_external_honest_checklist():
    task = {
        "status": "ceo_approved",
        "execution_checklist": [
            {"id": "approve", "title": "CEO Approve", "done": True},
            {"id": "repo_intel", "title": "S1", "done": False},
            {"id": "planning", "title": "S2", "done": False},
            {"id": "research", "title": "Research", "done": False},
            {"id": "implementation", "title": "S3", "done": False},
            {"id": "validation", "title": "S4", "done": False},
            {"id": "pr_intelligence", "title": "S5", "done": False},
        ],
    }
    report = {
        "ok": True,
        "stage": "awaiting_external",
        "patch_ready": False,
        "stages": {
            "implementation": {
                "ok": True,
                "mode": "needs_external",
                "files_touched": [],
            },
            "research": {"ok": True, "brief_path": "/tmp/RESEARCH_BRIEF.md"},
            "validation": {"ok": True, "skipped": True},
        },
    }
    out = merge_execution_into_task(task, report)
    assert out["status"] == "needs_external"
    by_id = {s["id"]: s["done"] for s in out["execution_checklist"]}
    assert by_id["repo_intel"] is True
    assert by_id["planning"] is True
    assert by_id["research"] is True
    assert by_id["implementation"] is False
    assert by_id["validation"] is False
    assert by_id["pr_intelligence"] is False


def test_merge_execution_research_patch_marks_implementation():
    task = {
        "status": "executing",
        "execution_checklist": [
            {"id": "repo_intel", "done": False},
            {"id": "planning", "done": False},
            {"id": "research", "done": False},
            {"id": "implementation", "done": False},
            {"id": "validation", "done": False},
            {"id": "pr_intelligence", "done": False},
        ],
    }
    report = {
        "ok": True,
        "stage": "awaiting_ceo_submit",
        "patch_ready": True,
        "stages": {
            "implementation": {
                "ok": True,
                "mode": "research_then_codex",
                "files_touched": ["docs/windows.md"],
            },
            "research": {"ok": True},
            "validation": {"ok": True, "passed": True, "skipped": False},
            "commit": {"ok": True},
        },
    }
    out = merge_execution_into_task(task, report)
    assert out["status"] == "draft_pr"
    by_id = {s["id"]: s["done"] for s in out["execution_checklist"]}
    assert by_id["implementation"] is True
    assert by_id["validation"] is True
