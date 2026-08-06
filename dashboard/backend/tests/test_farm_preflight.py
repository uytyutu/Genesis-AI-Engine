"""Pre-flight + capability matrix for Opire Farm."""

from swarm.farm_preflight import run_preflight
from swarm.farm_virtus_capabilities import (
    capability_snapshot,
    detect_task_type,
    task_type_auto_ok,
)


def test_detect_readme_task():
    assert detect_task_type("Update README with install steps") == "readme"
    assert task_type_auto_ok("readme")["ok"] is True
    assert task_type_auto_ok("human_interview")["ok"] is False


def test_preflight_go_on_healthy_candidate():
    cand = {
        "title": "Fix pagination race",
        "url": "https://github.com/acme/demo/issues/1",
        "issue_id": "1",
        "repository": "acme/demo",
        "overall_confidence_pct": 88,
        "blockers": [],
        "reject_reasons": [],
        "repo_status": "ok",
        "estimated_hours": 1.5,
        "competitors": 0,
        "languages": ["python"],
        "supported_languages": ["python"],
        "task_type": "bug_fix",
    }
    pf = run_preflight(cand, deep=False, min_confidence=80)
    assert pf["verdict"] == "GO"
    assert pf["approve_allowed"] is True
    assert pf["go"] is True


def test_preflight_skip_dead_repo():
    cand = {
        "title": "Fix bug",
        "url": "https://github.com/acme/demo/issues/1",
        "overall_confidence_pct": 90,
        "blockers": ["repo_unreachable"],
        "repo_status": "unreachable",
        "estimated_hours": 1,
        "competitors": 0,
        "languages": ["python"],
        "supported_languages": ["python"],
    }
    pf = run_preflight(cand, deep=False)
    assert pf["verdict"] == "SKIP"
    assert pf["approve_allowed"] is False


def test_capability_matrix_has_docs_and_contours():
    snap = capability_snapshot()
    ids = {r["id"] for r in snap["matrix"]}
    assert "documentation" in ids
    assert "bug_fix" in ids
    assert "opire_farm" in snap["contours_ru"]
