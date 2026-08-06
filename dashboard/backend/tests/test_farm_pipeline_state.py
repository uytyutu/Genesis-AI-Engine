"""Single Execution State Machine."""

from swarm.farm_pipeline_state import count_execution_success, derive_pipeline_state


def test_queued_after_approve_counts_as_started():
    t = {"status": "executing", "execution": {"stage": "queued"}}
    assert derive_pipeline_state(t) == "QUEUED"
    stats = count_execution_success([t])
    assert stats["approved"] == 1
    assert stats["started"] == 1
    assert stats["execution"] == 1
    assert stats["draft_pr"] == 0


def test_ceo_approved_without_execution_still_queued_if_exec_present():
    t = {"status": "ceo_approved", "execution": {"stage": "queued"}}
    assert derive_pipeline_state(t) == "QUEUED"
    assert count_execution_success([t])["started"] == 1


def test_no_contradiction_running_vs_needs_external():
    """While engine stage is active, do not treat as terminal pause."""
    t = {
        "status": "executing",
        "execution": {
            "stage": "implementation",
            "stages": {
                "repo_intelligence": {"ok": True},
                "implementation": {"mode": "needs_external", "files_touched": []},
            },
        },
    }
    # Still running → PATCHING, not SKIPPED/FAILED pause
    assert derive_pipeline_state(t) == "PATCHING"


def test_draft_pr_waiting_submit():
    t = {
        "status": "draft_pr",
        "execution": {
            "stage": "awaiting_ceo_submit",
            "patch_ready": True,
            "stages": {"implementation": {"files_touched": ["a.py"], "ok": True}},
        },
    }
    assert derive_pipeline_state(t) == "WAITING_SUBMIT"
    assert count_execution_success([t])["draft_pr"] == 1
