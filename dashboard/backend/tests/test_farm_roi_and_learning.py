"""ROI Score + Bounty Learning Ledger."""

from pathlib import Path

from swarm.farm_bounty_ledger import FarmBountyLearningLedger
from swarm.farm_roi_score import compute_roi, stars_from_usd_per_hour


def test_roi_docs_vs_long_react():
    docs = compute_roi({"reward_usd": 20, "estimated_hours": 0.25, "overall_confidence_pct": 90})
    react = compute_roi({"reward_usd": 60, "estimated_hours": 8, "overall_confidence_pct": 80})
    ci = compute_roi({"reward_usd": 40, "estimated_hours": 0.75, "overall_confidence_pct": 85})
    assert docs["roi_stars"] >= 5
    assert react["roi_stars"] <= 2
    assert ci["roi_stars"] >= 4
    assert docs["roi_rank_score"] > react["roi_rank_score"]


def test_stars_thresholds():
    assert stars_from_usd_per_hour(80) == 5
    assert stars_from_usd_per_hour(40) == 4
    assert stars_from_usd_per_hour(10) == 2
    assert stars_from_usd_per_hour(5) == 1


def test_bounty_ledger_win_and_summary(tmp_path: Path):
    ledger = FarmBountyLearningLedger(tmp_path)
    win = {
        "id": "opire:1",
        "title": "Fix docs typo",
        "languages": ["python", "markdown"],
        "reward_usd": 20,
        "estimated_hours": 0.25,
        "overall_confidence_pct": 90,
        "approved_at": "2026-08-01T10:00:00+00:00",
        "updated_at": "2026-08-01T10:20:00+00:00",
        "payout_confirmed_usd": 20,
        "bot_installed": True,
        "competitors": 0,
        "status": "payout_confirmed",
    }
    lose = {
        "id": "opire:2",
        "title": "Big react refactor",
        "languages": ["react"],
        "reward_usd": 60,
        "estimated_hours": 8,
        "skip_reason": "ceo_skip",
        "ceo_note": "too slow",
        "status": "skipped",
    }
    ledger.append_from_task(win, outcome="win")
    ledger.append_from_task(lose, outcome="skip")
    summary = ledger.summary()
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["earned_usd"] == 20
    assert summary["closed"] == 2
    assert any(r["reason"].startswith("langs:") for r in summary["why_won"])
    assert summary["stats_ready"] is False
