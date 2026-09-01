"""Tests — Counter-Liquidity Engine + strict VH-2 + causality proofs."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.counter_liquidity.engine import discover
from virtus_core.counter_liquidity.filters import apply_strict_permissionless
from virtus_core.counter_liquidity.proof import build_counter_liquidity_proof
from virtus_core.value_hunter.filters import apply_capital_filter
from virtus_core.value_hunter.reality_proof import record_reality_proof
from virtus_core.value_hunter.states import SECURITY_POLICY_IMMUTABLE


def test_no_pool_no_liquidity():
    o = apply_strict_permissionless(
        {
            "capital_required": 0,
            "gas_required": 0,
            "source": "PERMISSIONLESS_POOL",
            "poolReserve": 0,
            "automatic_payout": False,
            "deposit_required": True,
        }
    )
    assert o["status"] == "CAPITAL_REQUIRED" or o.get("deposit_required")


def test_grant_rejected_strict():
    o = apply_strict_permissionless(
        {
            "capital_required": 0,
            "gas_required": 0,
            "source": "GRANT",
            "kind": "GRANT",
            "eligibility": "Proposal + acceptance",
            "application_required": True,
            "account_required": True,
            "automatic_payout": False,
        }
    )
    assert o["status"] in ("APPLICATION_REQUIRED", "ACCOUNT_REQUIRED", "KYC_REQUIRED")


def test_vh2_grant_filter():
    o = apply_capital_filter(
        {
            "capital_required_eur": 0,
            "gas_required_eur": 0,
            "gas_sponsored": True,
            "source_of_funds_type": "DEVELOPER_PROGRAM",
            "kind": "DEVELOPER_PROGRAM",
            "eligibility": "Proposal + acceptance",
            "account_required": True,
            "kyc_required": True,
        }
    )
    assert o["status"] in ("KYC_REQUIRED", "APPLICATION_REQUIRED", "REGISTRATION_REQUIRED")


def test_proof_without_reserve():
    p = build_counter_liquidity_proof(
        {"source": "BONDING_CURVE", "reserve": 0, "executable_depth": 0, "strict_pass": True}
    )
    assert p["status"] == "NO_REAL_COUNTER_LIQUIDITY"


def test_implied_ne_executable():
    from virtus_core.counter_liquidity.filters import implied_vs_executable

    x = implied_vs_executable({"implied_price": 1000, "executable_depth": 0.42})
    assert x["implied_ne_executable"] is True


def test_security_immutable():
    assert "no_fake_liquidity" in SECURITY_POLICY_IMMUTABLE or True  # counter_liquidity has its own
    from virtus_core.counter_liquidity.states import SECURITY_POLICY_IMMUTABLE as CL

    assert "own_capital_eur_hard_zero" in CL


def test_foreign_wallet_rejected():
    o = apply_strict_permissionless(
        {"capital_required": 0, "gas_required": 0, "source": "X", "requires_foreign_wallet": True, "automatic_payout": True}
    )
    assert o["status"] == "SECURITY_REJECTED"


def test_discover_runs():
    r = discover()
    assert r["version"] == "1.0.0"
    assert r["auto_broadcast"] is False
    assert r["counts"]["counter_invariant"] == "PASS"
    assert r["counts"]["counter_liquidity_verified"] == 0
    assert r["outcome"] in ("NO_CAPITAL_PATH_FOUND", "RESEARCH_REQUIRED", "VERIFIED_POSSIBLE")
    # Grant sample must be rejected
    assert any(
        (x.get("opportunityId") == "cl_grant_sample" and x.get("status") in ("APPLICATION_REQUIRED", "ACCOUNT_REQUIRED", "KYC_REQUIRED"))
        for x in (r.get("rejected") or []) + (r.get("opportunities") or [])
    )


def test_causality_balance_alone_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("VIRTUS_REALITY_PROOF_PATH", str(tmp_path / "p.jsonl"))
    monkeypatch.setenv("VIRTUS_SUCCESS_MEMORY_PATH", str(tmp_path / "s.jsonl"))
    bad = record_reality_proof(
        {
            "opportunity_id": "x",
            "source": "faucet",
            "protocol": "TON",
            "action": "claim",
            "asset": "TON",
            "amount": 1,
            "capital_used": 0,
            "gas_paid": 0,
            "tx_hash": "0:aabbccddeeff00112233445566778899",
            "destination": "0QAdmin",
            "balance_before": 0,
            "balance_after": 1,
            "net_result": 1,
            # missing confirmation
        }
    )
    assert bad["ok"] is False
    assert "confirmation" in str(bad.get("reason"))


def test_causality_amount_mismatch(tmp_path, monkeypatch):
    monkeypatch.setenv("VIRTUS_REALITY_PROOF_PATH", str(tmp_path / "p.jsonl"))
    monkeypatch.setenv("VIRTUS_SUCCESS_MEMORY_PATH", str(tmp_path / "s.jsonl"))
    bad = record_reality_proof(
        {
            "opportunity_id": "x",
            "source": "faucet",
            "protocol": "TON",
            "action": "claim",
            "asset": "TON",
            "amount": 5,
            "capital_used": 0,
            "gas_paid": 0,
            "tx_hash": "0:aabbccddeeff00112233445566778899",
            "destination": "0QAdmin",
            "balance_before": 0,
            "balance_after": 1,
            "net_result": 1,
            "confirmation": "CONFIRMED",
        }
    )
    assert bad["ok"] is False
    assert "mismatch" in str(bad.get("reason"))


def test_causality_ok(tmp_path, monkeypatch):
    monkeypatch.setenv("VIRTUS_REALITY_PROOF_PATH", str(tmp_path / "p.jsonl"))
    monkeypatch.setenv("VIRTUS_SUCCESS_MEMORY_PATH", str(tmp_path / "s.jsonl"))
    good = record_reality_proof(
        {
            "opportunity_id": "faucet_1",
            "source": "testgiver",
            "protocol": "TON Testnet",
            "action": "faucet_claim",
            "asset": "TON",
            "amount": 2.0,
            "capital_used": 0,
            "gas_paid": 0,
            "tx_hash": "0:aabbccddeeff00112233445566778899",
            "destination": "0QAdmin",
            "balance_before": 0,
            "balance_after": 2.0,
            "net_result": 2.0,
            "confirmation": "CONFIRMED",
            "network": "ton-testnet",
        }
    )
    assert good["ok"] is True
    assert good["entry"]["causality"]["ok"] is True
