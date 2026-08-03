"""Opire Farm — confidence + Reward Protection (no live network in unit tests)."""

from __future__ import annotations

from pathlib import Path

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
        _sample(id="b", title="Rewrite entire C++ engine", programmingLanguages=["C++"], pendingPrice={"value": 500000, "unit": "USD_CENT"}),
    ]
    out = scan_opire(fetch_fn=lambda: rows, threshold=70)
    assert out["ok"] is True
    ids = {c["id"] for c in out["candidates"]}
    assert "a" in ids
    assert "b" not in ids


def test_approve_and_reward_protection(tmp_path: Path):
    eng = OpireFarmEngine(tmp_path)
    import swarm.opire_farm as mod

    orig = mod.fetch_opire_rewards

    def fake_fetch():
        return [_sample(id="rid-pay")]

    mod.fetch_opire_rewards = fake_fetch  # type: ignore[assignment]
    try:
        decided = eng.decide("rid-pay", "approve")
        assert decided["ok"] is True
        assert decided["task"]["status"] == "ceo_approved"
        assert decided["task"]["real_income"] is False

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
    finally:
        mod.fetch_opire_rewards = orig
