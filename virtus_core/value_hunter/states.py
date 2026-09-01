"""Opportunity state machine — Source Hunter v2.1."""

from __future__ import annotations

from typing import Literal

OpportunityState = Literal[
    "DISCOVERED",
    "VERIFIED",
    "ZERO_CAPITAL",
    "TESTABLE",
    "QUEUED",
    "OWNER_REQUIRED",
    "CAPITAL_REQUIRED",
    "GAS_REQUIRED",
    "KYC_REQUIRED",
    "REGISTRATION_REQUIRED",
    "UNSUPPORTED",
    "NO_SOURCE_OF_FUNDS",
    "NO_ROUTE",
    "INSUFFICIENT_LIQUIDITY",
    "SIMULATION_FAILED",
    "ECONOMIC_PROOF_FAILED",
    "SECURITY_REJECTED",
    "EXPIRED",
    "SKIPPED",
    "EXIT_ONLY",
    "REAL_SETTLEMENT_CONFIRMED",
]

POSITIVE = frozenset(
    {"DISCOVERED", "VERIFIED", "ZERO_CAPITAL", "TESTABLE", "QUEUED", "OWNER_REQUIRED", "REAL_SETTLEMENT_CONFIRMED"}
)
NEGATIVE = frozenset(
    {
        "CAPITAL_REQUIRED",
        "GAS_REQUIRED",
        "KYC_REQUIRED",
        "REGISTRATION_REQUIRED",
        "UNSUPPORTED",
        "NO_SOURCE_OF_FUNDS",
        "NO_ROUTE",
        "INSUFFICIENT_LIQUIDITY",
        "SIMULATION_FAILED",
        "ECONOMIC_PROOF_FAILED",
        "SECURITY_REJECTED",
        "EXPIRED",
        "SKIPPED",
    }
)

SECURITY_POLICY_IMMUTABLE = (
    "no_third_party_wallets",
    "no_seed_bruteforce",
    "no_production_exploit",
    "no_fake_settlement",
    "no_auto_mainnet_broadcast",
    "owner_gate_required",
    "max_capital_eur_hard",
    "ai_must_not_read_mnemonic",
)
