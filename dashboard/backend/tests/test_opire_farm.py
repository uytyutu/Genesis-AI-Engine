"""Opire Farm — confidence + Reward Protection (no live network in unit tests)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from swarm.farm_execution_engine import (
    FarmExecutionEngine,
    build_plan,
    build_pr_body,
    detect_stack,
)
from swarm.opire_farm import (
    OpireFarmEngine,
    score_reward,
    scan_opire,
)


def _sample(**over: object) -> dict:
    base = {
        "id": "rid-1",
        "title": "Fix pagination race in API",
        "url": "https://github.com/acme/demo/issues/42",
        "platform": "GitHub",
        "claimerUsers": [],
        "tryingUsers": [],
        "programmingLanguages": ["Python"],
        "pendingPrice": {"value": 8000, "unit": "USD_CENT"},
        "project": {
            "url": "https://github.com/acme/demo",
            "name": "demo",
            "isPublic": True,
            "isBotInstalled": True,
        },
        "organization": {"name": "acme"},
    }
    base.update(over)
    return base


def test_score_prefers_python_fix_low_competition():
    s = score_reward(_sample())
    assert s["recommendation"] == "TAKE"
    assert s["overall_confidence_pct"] >= 72
    assert s["reward_usd"] == 80.0
    assert s["issue_id"] == "42"


def test_score_rejects_captcha():
    s = score_reward(_sample(title="Auto Solve hcaptcha 500"))
    assert s["recommendation"] == "SKIP"
    assert "forbidden_captcha_or_tos_evasion" in s["blockers"]


def test_scan_filters_with_stub_fetch():
    rows = [
        _sample(id="a"),
        _sample(
            id="b",
            title="Rewrite entire C++ engine",
            programmingLanguages=["C++"],
            pendingPrice={"value": 500000, "unit": "USD_CENT"},
        ),
    ]
    out = scan_opire(fetch_fn=lambda: rows, threshold=70)
    assert out["ok"] is True
    ids = {c["id"] for c in out["candidates"]}
    assert "opire:a" in ids
    assert "opire:b" not in ids
    assert "b" not in ids


def _mock_sniper_ok(intel, monkeypatch):
    monkeypatch.setattr(
        intel,
        "apply_sniper_to_candidate",
        lambda cand, timeout=10.0: {
            **cand,
            "repo_status": "ok",
            "recommendation": cand.get("recommendation") or "TAKE",
            "blockers": [
                b
                for b in (cand.get("blockers") or [])
                if b
                not in (
                    "repo_unreachable",
                    "repo_auth_required",
                    "missing_repo",
                )
            ],
        },
    )


def test_approve_and_reward_protection(tmp_path: Path, monkeypatch):
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod
    import swarm.opire_issue_intel as intel

    monkeypatch.setenv("FARM_AUTO_EXECUTE_ON_APPROVE", "0")
    monkeypatch.setattr(mod, "fetch_opire_rewards", lambda: [_sample(id="rid-pay")])
    monkeypatch.setattr(
        intel,
        "fetch_issue_from_url",
        lambda *a, **k: {
            "ok": True,
            "body": "Fix pagination race. Must add test.",
            "title": "Fix pagination",
        },
    )
    _mock_sniper_ok(intel, monkeypatch)
    decided = eng.decide("rid-pay", "approve")
    assert decided["ok"] is True
    assert decided["task"]["status"] == "ceo_approved"
    assert decided["task"]["real_income"] is False
    assert decided["next_action"] == "start_execution"
    assert decided.get("auto_started_execution") is False
    assert decided["task"].get("ceo_action_links", {}).get("try_comment_text") == "/try"

    denied = eng.start_execution("missing", clone=False)
    assert denied["ok"] is False

    bad = eng.advance("rid-pay", "payout_confirmed")
    assert bad["ok"] is False

    ok = eng.advance(
        "rid-pay",
        "payout_confirmed",
        payment_confirmation_id="opire-pay-99",
        payout_usd=80.0,
    )
    assert ok["ok"] is True
    assert ok["task"]["real_income"] is True
    assert ok["task"]["payout_confirmed_usd"] == 80.0

    panel = eng.panel(force_scan=False)
    assert panel["ledger"]["real_confirmed_usd"] == 80.0
    assert panel["funnel"]["paid"] == 1
    assert panel["funnel"]["total_confirmed_usd"] == 80.0
    assert panel["funnel"]["ceo_approved"] >= 1


def test_approve_auto_starts_execution_engine(tmp_path: Path, monkeypatch):
    """Blocker №1: Approve must call start_execution — not leave Execution paused."""
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod
    import swarm.opire_issue_intel as intel

    monkeypatch.setenv("FARM_AUTO_EXECUTE_ON_APPROVE", "1")
    monkeypatch.setenv("FARM_AUTO_ADVANCE", "0")
    calls: list[tuple[str, bool]] = []

    def _fake_start(reward_id: str, *, clone: bool = True, _auto_depth: int = 0):
        calls.append((reward_id, clone))
        state = eng._load()
        task = (state.get("tasks") or {}).get(reward_id) or {}
        task = {
            **task,
            "status": "executing",
            "execution": {
                "ok": True,
                "stage": "running",
                "stages": {
                    "clone": {"ok": True},
                    "analysis": {"ok": True},
                },
            },
        }
        state.setdefault("tasks", {})[reward_id] = task
        eng._save(state)
        return {
            "ok": True,
            "task": task,
            "message_ru": "Clone → Analysis started (test)",
        }

    monkeypatch.setattr(eng, "start_execution", _fake_start)
    monkeypatch.setattr(mod, "fetch_opire_rewards", lambda: [_sample(id="rid-auto")])
    monkeypatch.setattr(
        intel,
        "fetch_issue_from_url",
        lambda *a, **k: {"ok": True, "body": "Fix pagination", "title": "Fix"},
    )
    _mock_sniper_ok(intel, monkeypatch)

    decided = eng.decide("rid-auto", "approve")
    assert decided["ok"] is True
    assert decided.get("auto_started_execution") is True
    assert calls, "start_execution must be called after Approve"
    assert "rid-auto" in str(calls[0][0])
    assert decided["task"]["status"] == "executing"
    assert decided["next_action"] == "monitor_execution"
    assert "Execution" in (decided.get("message_ru") or "") or "Approve" in (
        decided.get("message_ru") or ""
    )


def test_detect_stack_and_pr_body(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "pagination.py").write_text("x=1\n", encoding="utf-8")
    stack = detect_stack(tmp_path)
    assert "python" in stack["languages"]
    assert stack["has_tests_guess"] is True
    plan = build_plan(
        issue_title="Fix pagination race",
        issue_url="https://github.com/acme/demo/issues/42",
        stack=stack,
        related=["pagination.py"],
    )
    body = build_pr_body(
        issue_url="https://github.com/acme/demo/issues/42",
        issue_id="42",
        plan=plan,
        title="Fix pagination race",
    )
    assert "/claim #42" in body
    assert "CEO Submit required" in body


def test_execution_pipeline_scaffold_no_clone(tmp_path: Path, monkeypatch):
    """Without LLM: Impossible → auto Skip (no Cursor handoff)."""
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod
    import swarm.opire_issue_intel as intel

    monkeypatch.setenv("FARM_AUTO_ADVANCE", "0")
    monkeypatch.setenv("FARM_AUTO_RESEARCH", "0")
    monkeypatch.setenv("FARM_AUTO_EXECUTE_ON_APPROVE", "0")
    monkeypatch.setattr(
        "swarm.farm_execution_manager._has_engineer_llm", lambda: False
    )
    monkeypatch.setattr(
        "swarm.farm_research_agent.auto_research_enabled", lambda: False
    )
    monkeypatch.setattr("swarm.farm_research_agent.pick_executor", lambda: "none")

    monkeypatch.setattr(mod, "fetch_opire_rewards", lambda: [_sample(id="rid-ex")])
    monkeypatch.setattr(
        intel,
        "fetch_issue_from_url",
        lambda *a, **k: {"ok": True, "body": "Fix pagination", "title": "Fix"},
    )
    _mock_sniper_ok(intel, monkeypatch)
    decided = eng.decide("rid-ex", "approve")
    assert decided["ok"] is True

    ee = FarmExecutionEngine(tmp_path)
    task_id = str(decided["task"]["id"])
    ws_src = ee.workspace_for(task_id) / "src"
    ws_src.mkdir(parents=True)
    (ws_src / "requirements.txt").write_text("x\n", encoding="utf-8")
    (ws_src / "README.md").write_text("# demo\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=ws_src, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t"],
        cwd=ws_src,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "t"],
        cwd=ws_src,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=ws_src, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=ws_src,
        check=True,
        capture_output=True,
    )

    out = eng.start_execution(task_id, clone=False)
    assert out.get("auto_skipped") is True
    assert out["task"]["status"] == "skipped"
    assert out["task"].get("skip_reason") == "not_auto_executable"
    assert task_id in (eng._load().get("skipped_forever") or [])
    # Permanent skip — decide skip again is fine; scan exclude includes skipped
    assert out["ok"] is False


def test_ceo_skip_removes_from_active_forever(tmp_path: Path, monkeypatch):
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod
    import swarm.opire_issue_intel as intel

    monkeypatch.setenv("FARM_AUTO_EXECUTE_ON_APPROVE", "0")
    monkeypatch.setattr(mod, "fetch_opire_rewards", lambda: [_sample(id="rid-skip")])
    monkeypatch.setattr(
        intel,
        "fetch_issue_from_url",
        lambda *a, **k: {"ok": True, "body": "x", "title": "Fix"},
    )
    _mock_sniper_ok(intel, monkeypatch)
    approved = eng.decide("rid-skip", "approve")
    assert approved["ok"] is True
    tid = str(approved["task"]["id"])
    skipped = eng.decide(tid, "skip")
    assert skipped["ok"] is True
    assert skipped["task"]["status"] == "skipped"
    panel = eng.panel(force_scan=False)
    assert all(t.get("id") != tid for t in panel["active_tasks"])
    forever = eng._load().get("skipped_forever") or []
    assert tid in forever or any(tid.endswith(str(x)) for x in forever)

def test_analyze_issue_rejects_captcha_body():
    from swarm.opire_issue_intel import analyze_issue_text

    a = analyze_issue_text("Fix login", "Please auto solve hcaptcha for users")
    assert "forbidden_captcha_or_tos_evasion" in a["blockers"]


def test_resolve_git_binary_or_message():
    from swarm.farm_execution_engine import resolve_git_binary

    # On CEO machine Git is installed; in CI may still find it
    git = resolve_git_binary()
    assert git is None or "git" in git.lower()


def test_score_with_issue_intel_body():
    raw = _sample()
    intel = {
        "ok": True,
        "body": "Acceptance criteria:\n- Fix race\n- Add test\nMust pass CI",
        "title": raw["title"],
    }
    s = score_reward(raw, issue_intel=intel)
    assert s["ceo_action_links"]["try_comment_text"] == "/try"
    assert "claim" in s["ceo_action_links"]["claim_pr_text"]
    assert s["issue_analysis"]["body_chars"] > 10


def test_proof_pending_until_real(tmp_path: Path, monkeypatch):
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod
    import swarm.opire_issue_intel as intel

    monkeypatch.setenv("FARM_AUTO_EXECUTE_ON_APPROVE", "0")
    monkeypatch.setattr(mod, "fetch_opire_rewards", lambda: [_sample(id="rid-proof")])
    monkeypatch.setattr(
        intel,
        "fetch_issue_from_url",
        lambda *a, **k: {"ok": True, "body": "Fix bug", "title": "Fix"},
    )
    _mock_sniper_ok(intel, monkeypatch)
    eng.decide("rid-proof", "approve")
    panel = eng.panel(force_scan=False)
    assert panel["proof"]["proof_status"] == "PENDING_FIRST_REAL"
    assert panel["proof"]["payout_confirmed"] == 0

    eng.advance(
        "rid-proof",
        "payout_confirmed",
        payment_confirmation_id="virtus_auto:test:opire:rid-proof",
        payout_usd=80.0,
    )
    panel2 = eng.panel(force_scan=False)
    assert panel2["proof"]["proof_status"] == "VERIFIED"
    assert panel2["proof"]["payout_confirmed"] == 1
    assert panel2["proof"]["real_confirmed_usd"] == 80.0


def test_ceo_submit_blocked_before_draft(tmp_path: Path, monkeypatch):
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod
    import swarm.opire_issue_intel as intel

    monkeypatch.setenv("FARM_AUTO_EXECUTE_ON_APPROVE", "0")
    monkeypatch.setattr(mod, "fetch_opire_rewards", lambda: [_sample(id="rid-block")])
    monkeypatch.setattr(
        intel,
        "fetch_issue_from_url",
        lambda *a, **k: {"ok": True, "body": "Fix the bug with tests", "title": "x"},
    )
    _mock_sniper_ok(intel, monkeypatch)
    eng.decide("rid-block", "approve")
    blocked = eng.ceo_submit_pr("rid-block")
    assert blocked["ok"] is False
    assert blocked["error"] == "draft_required"


def test_skip_from_scan_is_instant_no_fetch(tmp_path: Path, monkeypatch):
    """Skip must not hang on Opire rescan — forever-register by id."""
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod

    def _boom():
        raise AssertionError("skip must not fetch Opire")

    monkeypatch.setattr(mod, "fetch_opire_rewards", _boom)
    monkeypatch.setattr(
        mod,
        "scan_opire",
        lambda **k: (_ for _ in ()).throw(AssertionError("no scan")),
    )
    out = eng.decide("opire:never-seen", "skip")
    assert out["ok"] is True
    assert out["task"]["status"] == "skipped"
    forever = eng._load().get("skipped_forever") or []
    assert "opire:never-seen" in forever or "never-seen" in forever


def test_money_mode_filters_low_confidence():
    from swarm.opire_farm import apply_money_mode_to_scan, is_money_mode_candidate

    good = {
        "id": "g",
        "title": "Fix pagination",
        "url": "https://github.com/acme/demo/issues/1",
        "issue_id": "1",
        "repository": "acme/demo",
        "overall_confidence_pct": 88,
        "success_probability_pct": 88,
        "blockers": [],
        "reject_reasons": [],
        "recommendation": "TAKE",
        "repo_status": "ok",
        "estimated_hours": 1.5,
        "competitors": 0,
        "supported_languages": ["python"],
        "languages": ["python"],
        "tests_available": "likely",
        "roi_label": "A",
        "roi_usd_per_hour": 40,
        "task_type": "bug_fix",
    }
    bad = {
        "id": "b",
        "title": "Rewrite everything",
        "url": "https://github.com/acme/demo/issues/2",
        "overall_confidence_pct": 65,
        "blockers": ["high_competition"],
        "recommendation": "REVIEW",
        "repo_status": "ok",
        "estimated_hours": 2,
        "competitors": 9,
        "languages": ["python"],
    }
    assert is_money_mode_candidate(good) is True
    assert is_money_mode_candidate(bad) is False
    out = apply_money_mode_to_scan({"candidates": [good, bad]})
    assert [c["id"] for c in out["candidates"]] == ["g"]
    assert out["money_mode"]["threshold"] == 80
    assert out["candidates"][0]["preflight"]["verdict"] == "GO"
    assert out["candidates"][0]["success_checklist"]
