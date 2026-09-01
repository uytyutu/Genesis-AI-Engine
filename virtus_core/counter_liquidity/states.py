"""Counter-Liquidity Discovery Engine — states & research outcomes."""

from __future__ import annotations

from typing import Literal

ResearchOutcome = Literal[
    "VERIFIED_POSSIBLE",
    "POSSIBLE_WITH_CONDITIONS",
    "NO_CAPITAL_PATH_FOUND",
    "CAPITAL_REQUIRED",
    "UNSUPPORTED",
    "RESEARCH_REQUIRED",
]

OpportunityState = Literal[
    "DISCOVERED",
    "SOURCE_VERIFIED",
    "LIQUIDITY_VERIFIED",
    "ZERO_CAPITAL",
    "SIMULATABLE",
    "TESTNET_READY",
    "OWNER_REQUIRED",
    "EXECUTABLE",
    "REALIZED",
    "HYPOTHESIS",
    "CAPITAL_REQUIRED",
    "GAS_REQUIRED",
    "NO_SOURCE",
    "NO_LIQUIDITY",
    "NO_REAL_COUNTER_LIQUIDITY",
    "NO_ROUTE",
    "UNSUPPORTED",
    "GOVERNANCE_REQUIRED",
    "KYC_REQUIRED",
    "APPLICATION_REQUIRED",
    "ACCOUNT_REQUIRED",
    "REGISTRATION_REQUIRED",
    "SECURITY_REJECTED",
    "SIMULATION_FAILED",
    "INSUFFICIENT_LIQUIDITY",
    "EXPIRED",
]

SECURITY_POLICY_IMMUTABLE = (
    "no_third_party_wallets",
    "no_seed_bruteforce",
    "no_production_exploit",
    "no_fake_settlement",
    "no_fake_liquidity",
    "no_auto_mainnet_broadcast",
    "owner_gate_required",
    "own_capital_eur_hard_zero",
    "ai_must_not_read_mnemonic",
    "no_token_impersonation",
)
