"""Tests — BIP39 Compute Lab dual architecture (no foreign seed income)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.bip39_compute_lab.lab import (
    evaluate_found_candidate,
    reject_foreign_seed_path,
    run_bip39_bench,
    run_dual_architecture,
)


def test_bench_runs():
    r = run_bip39_bench(workers=2, batch_per_worker=50)
    assert r["total_vectors"] > 0
    assert r["income_claimed"] is False
    assert r["telegram_required"] is False
    assert r["security"]["status"] == "SECURITY_REJECTED"


def test_foreign_seed_rejected():
    r = reject_foreign_seed_path()
    assert r["status"] == "SECURITY_REJECTED"


def test_screen_number_not_found():
    r = evaluate_found_candidate({"confirmed_balance": 1_000_000})
    assert r["found"] is False


def test_full_found_criteria():
    r = evaluate_found_candidate(
        {
            "address": "0QAdmin",
            "tx_or_blockchain_proof": "0:abc",
            "confirmed_balance": 1.5,
            "legal_source": "PROTOCOL_REWARD",
            "transferability": True,
        }
    )
    assert r["found"] is True


def test_dual_offline():
    r = run_dual_architecture(workers=2, batch=40, offline=True)
    assert r["telegram_required"] is False
    assert r["screen_number_is_not_found"]["found"] is False
    assert r["treasury_handoff"]["painted_from_hashrate"] is False
