"""Farm scan analytics aggregates."""

from swarm.farm_scan_analytics import build_scan_analytics


def test_scan_analytics_languages_and_rejects():
    pool = [
        {
            "languages": ["python", "fastapi"],
            "overall_confidence_pct": 80,
            "reward_usd": 50,
            "recommendation": "TAKE",
            "blockers": [],
        },
        {
            "languages": ["rust"],
            "overall_confidence_pct": 70,
            "reward_usd": 100,
            "recommendation": "SKIP",
            "blockers": ["unsupported_language"],
            "reject_reasons": ["unsupported_language"],
        },
        {
            "languages": ["react", "typescript"],
            "overall_confidence_pct": 35,
            "reward_usd": 80,
            "recommendation": "SKIP",
            "blockers": [],
            "reject_reasons": ["below_threshold_60"],
        },
        {
            "languages": ["python"],
            "overall_confidence_pct": 55,
            "reward_usd": 40,
            "recommendation": "REVIEW",
            "blockers": ["repo_unreachable"],
        },
    ]
    out = build_scan_analytics(pool, threshold=60.0, supported_langs=frozenset({"python", "fastapi", "typescript", "react"}))
    assert out["pool_size"] == 4
    langs = {r["name"]: r["count"] for r in out["languages"]}
    assert langs.get("python") == 2
    reasons = {r["reason"]: r["count"] for r in out["reject_reasons"]}
    assert reasons.get("capability_missing") == 1
    assert reasons.get("dead_repo") == 1
    assert reasons.get("confidence_low") >= 1
    assert out["potential_reward"]["high"]["count"] == 1
    assert out["potential_reward"]["high"]["usd"] == 50
    assert out["capability_coverage"]["coverage_pct"] >= 50
