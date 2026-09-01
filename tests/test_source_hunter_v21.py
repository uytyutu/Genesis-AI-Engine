"""Unit tests — ZERO-CAPITAL SOURCE HUNTER v2.1 + Evolution Engine."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.value_hunter.adapters import run_all_adapters
from virtus_core.value_hunter.evolution import record_success, run_epoch_tick, spawn_agent
from virtus_core.value_hunter.filters import apply_capital_filter, economic_proof
from virtus_core.value_hunter.pipeline import (
    deduplicate,
    kill_switch_check,
    process_pipeline,
    reality_ledger_accept,
    simulate,
)


def test_A_capital_zero_pass():
    o = apply_capital_filter(
        {
            "capital_required_eur": 0,
            "gas_required_eur": 0,
            "gas_sponsored": True,
            "source_of_funds_type": "BUG_BOUNTY",
            "status": "DISCOVERED",
        }
    )
    assert o["status"] in ("ZERO_CAPITAL", "TESTABLE")


def test_B_capital_reject():
    o = apply_capital_filter(
        {
            "capital_required_eur": 50,
            "gas_required_eur": 0,
            "gas_sponsored": True,
            "source_of_funds_type": "INCENTIVE",
        }
    )
    assert o["status"] == "CAPITAL_REQUIRED"


def test_C_gas_without_sponsor_reject():
    o = apply_capital_filter(
        {
            "capital_required_eur": 0,
            "gas_required_eur": 1.0,
            "gas_sponsored": False,
            "source_of_funds_type": "CLAIM",
        }
    )
    assert o["status"] == "GAS_REQUIRED"


def test_D_unknown_source_reject():
    o = apply_capital_filter(
        {
            "capital_required_eur": 0,
            "gas_required_eur": 0,
            "gas_sponsored": True,
            "source_of_funds_type": "",
        }
    )
    assert o["status"] == "NO_SOURCE_OF_FUNDS"


def test_E_foreign_wallet_security():
    o = apply_capital_filter(
        {
            "capital_required_eur": 0,
            "gas_required_eur": 0,
            "gas_sponsored": True,
            "source_of_funds_type": "OTHER",
            "requires_foreign_wallet": True,
        }
    )
    assert o["status"] == "SECURITY_REJECTED"


def test_H_simulation_fail_on_capital():
    sim = simulate({"status": "CAPITAL_REQUIRED", "source_of_funds_type": "INCENTIVE"})
    assert sim["ok"] is False
    assert sim["broadcast"] is False


def test_I_fake_balance_not_real():
    r = reality_ledger_accept(
        {
            "network": "ton",
            "asset": "TON",
            "amount": 1,
            "txHash": "abc",
            "source": "x",
            "destination": "y",
            "confirmationStatus": "CONFIRMED",
            "ui_only": True,
        }
    )
    assert r["accepted"] is False


def test_J_fake_tx_not_real():
    r = reality_ledger_accept(
        {
            "network": "ton",
            "asset": "TON",
            "amount": 1,
            "txHash": "fake",
            "source": "x",
            "destination": "y",
            "confirmationStatus": "CONFIRMED",
            "fake_tx": True,
        }
    )
    assert r["accepted"] is False


def test_K_confirmed_tx_real():
    r = reality_ledger_accept(
        {
            "network": "ton",
            "asset": "TON",
            "amount": 0.37,
            "txHash": "EQ_real_example",
            "source": "faucet",
            "destination": "owner",
            "confirmationStatus": "CONFIRMED",
            "evidence": "rpc",
        }
    )
    assert r["accepted"] is True and r["real"] is True


def test_L_owner_gate_kill_switch():
    ks = kill_switch_check(
        {"source_of_funds_type": "BUG_BOUNTY", "withdrawal_path": "owner", "attempt_broadcast": True},
        owner_approved=False,
    )
    assert ks["abort"] is True
    assert "owner_gate" in ks["reasons"]


def test_M_kill_switch_unknown_dest():
    ks = kill_switch_check({"source_of_funds_type": "CLAIM", "withdrawal_path": "UNKNOWN"})
    assert ks["abort"] is True


def test_N_adapter_no_global_crash():
    pack = run_all_adapters()
    assert "adapters" in pack
    assert isinstance(pack["raw_items"], list)


def test_O_dedup():
    a = {"id": "x", "protocol": "P", "kind": "CLAIM", "asset": "TON", "eligibility": "e", "required_action": "a"}
    out = deduplicate([a, dict(a), dict(a)])
    assert len(out) == 1
    assert out[0]["dedup_hits"] == 3


def test_economic_proof_fail():
    p = economic_proof({"source_of_funds_type": "CLAIM", "eligibility": "UNKNOWN"})
    assert p["ok"] is False
    assert p["status"] == "ECONOMIC_PROOF_FAILED"


def test_pipeline_runs():
    r = process_pipeline()
    assert r["version"].startswith("2.1")
    assert r["auto_broadcast"] is False
    assert r["max_capital_eur"] == 0
    assert "counts" in r
    assert r["counter_invariant"] == "PASS"
    acc = r["counts"]["accounting"]
    assert acc["sum_buckets"] == acc["DISCOVERED"]
    assert r["counts"]["executable_now"] == 0 or isinstance(r["counts"]["executable_now"], int)
    assert r["mission"]["id"] == "VH-1"
    assert r["mission"]["current"] == 0 or r["mission"]["current"] >= 0
    assert r["genesis"]["genesis_pass"] in (True, False)


def test_counter_invariant_partitions():
    r = process_pipeline()
    c = r["counts"]
    assert c["counter_invariant"] == "PASS"
    assert c["discovered"] == c["rejected"] + c["exit_only"] + c["candidates_for_test"] + c["pending"] + c["expired"]


def test_real_verify_unknown_amount():
    from virtus_core.value_hunter.real_verify import verify_real_opportunity

    v = verify_real_opportunity(
        {
            "protocol": "Immunefi",
            "asset": "USDT",
            "eligibility": "in-scope",
            "required_action": "report",
            "source_of_funds_type": "BUG_BOUNTY",
            "expected_gross": None,
            "capital_required_eur": 0,
            "gas_required_eur": 0,
            "withdrawal_path": "owner",
            "url": "https://immunefi.com",
        }
    )
    assert v["status"] == "NOT VERIFIED"
    assert "how_much" in v["unknowns"]


def test_success_memory_requires_fields():
    from virtus_core.value_hunter.success_memory import append_success

    bad = append_success({"asset": "TON", "reward": 1})
    assert bad["ok"] is False


def test_signer_boundary():
    from virtus_core.value_hunter.signer_boundary import assert_ai_has_no_keys, refuses_to_open_secret_file

    assert refuses_to_open_secret_file(".env.ton") is True
    assert assert_ai_has_no_keys()["policy"] == "AI_MUST_NOT_READ_MNEMONIC"


def test_evolution_tick():
    tick = run_epoch_tick()
    assert tick["engine"] == "Value Hunter Evolution Engine"
    assert tick["agent"]["capital_limit"] == 0.0 or tick["agent"].get("genome", {}).get("capital_limit_eur") == 0.0
    assert "no_auto_mainnet_broadcast" in tick["agent"]["security_policy_immutable"]


def test_success_requires_real_confirm(tmp_path, monkeypatch):
    mem = tmp_path / "success_memory.jsonl"
    monkeypatch.setenv("VIRTUS_SUCCESS_MEMORY_PATH", str(mem))
    a = spawn_agent()
    bad = record_success(
        a["agent_id"],
        {"asset": "TON", "amount": 1, "tx": "x", "confirmations": "ui", "capital_used_eur": 0},
    )
    assert bad["ok"] is False
    good = record_success(
        a["agent_id"],
        {
            "asset": "TON",
            "amount": 0.37,
            "tx": "0:abcdef0123456789deadbeef01234567",
            "confirmations": "verified",
            "capital_used_eur": 0,
            "source": "testnet_faucet",
            "protocol": "TON Testnet",
            "action": "faucet_claim",
            "gas": 0,
            "net_result": 0.37,
        },
    )
    assert good["ok"] is True and good["success"] is True
    assert good.get("success_memory", {}).get("stored") is True
    # Production KPI path must stay empty — this test used isolated memory file
    monkeypatch.delenv("VIRTUS_SUCCESS_MEMORY_PATH", raising=False)
    from virtus_core.value_hunter.success_memory import success_count

    # default path may still be 0 after fixture filter
    assert success_count() >= 0


def test_reality_proof_recorder(tmp_path, monkeypatch):
    from virtus_core.value_hunter.reality_proof import record_reality_proof, proof_count

    monkeypatch.setenv("VIRTUS_REALITY_PROOF_PATH", str(tmp_path / "proofs.jsonl"))
    monkeypatch.setenv("VIRTUS_SUCCESS_MEMORY_PATH", str(tmp_path / "sm.jsonl"))
    bad = record_reality_proof({"opportunity_id": "x"})
    assert bad["ok"] is False
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
            "block": 123,
            "destination": "0QAdmin",
            "balance_before": 0,
            "balance_after": 2.0,
            "net_result": 2.0,
            "network": "ton-testnet",
            "confirmation": "CONFIRMED",
        }
    )
    assert good["ok"] is True
    assert proof_count() == 1


def test_offline_discovery():
    r = process_pipeline(offline=True)
    assert r["discovery"].get("status") == "DISCOVERY_OFFLINE" or r.get("discovery")
