"""
Independent discovery adapters — Counter-Liquidity Engine.

Honest catalog: many mechanisms are RESEARCH/HYPOTHESIS or CAPITAL_REQUIRED.
No fake pools. No grant applications in primary pass.
"""

from __future__ import annotations

import time
from typing import Any, Callable


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


AdapterFn = Callable[[], list[dict[str, Any]]]


def _base(**kw: Any) -> dict[str, Any]:
    d = {
        "network": "ton-testnet",
        "asset": "VCORE",
        "counterAsset": "TON",
        "sourceAddress": None,
        "contractAddress": None,
        "poolAddress": None,
        "capital_required": 0.0,
        "gas_required": 0.0,
        "sponsor": False,
        "eligibility": "UNKNOWN",
        "action": "UNKNOWN",
        "expectedAmount": None,
        "withdrawalPath": "UNKNOWN",
        "evidence": "",
        "expiry": "UNKNOWN",
        "status": "DISCOVERED",
        "registration_required": False,
        "account_required": False,
        "kyc_required": False,
        "application_required": False,
        "approval_required": False,
        "deposit_required": False,
        "stake_required": False,
        "purchase_required": False,
        "manualParticipation": False,
        "automatic_payout": None,
        "reserve": None,
        "executable_depth": None,
        "implied_price": None,
        "poolReserve": None,
        "max_executable": None,
    }
    d.update(kw)
    return d


def protocol_liquidity_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_proto_owned_liq",
            protocol="GENERIC_POL",
            source="PROTOCOL_LIQUIDITY",
            sourceType="PROTOCOL_LIQUIDITY",
            kind="PROTOCOL_OWNED_LIQUIDITY",
            eligibility="Usually governance / listing — not automatic for unknown Jetton",
            action="Request POL / listing",
            application_required=True,
            approval_required=True,
            automatic_payout=False,
            status="DISCOVERED",
            evidence="Research class: protocol treasury may seed pairs — requires eligibility check",
        )
    ]


def incentive_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_lp_mining",
            protocol="DEX_LP_MINING",
            source="LIQUIDITY_MINING",
            sourceType="LIQUIDITY_MINING",
            kind="LIQUIDITY_MINING",
            capital_required=50.0,
            gas_required=1.0,
            deposit_required=True,
            eligibility="Provide both sides of pool",
            action="deposit_lp",
            automatic_payout=False,
            evidence="https://help.dedust.io/en/liquidity/pools",
        )
    ]


def bonding_curve_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_bonding_curve",
            protocol="BONDING_CURVE_GENERIC",
            source="OTHER_DOCUMENTED_MECHANISM",
            sourceType="BONDING_CURVE",
            kind="BONDING_CURVE",
            eligibility="Curve must hold real reserve; empty curve = no counter-liquidity",
            action="buy/sell along curve",
            deposit_required=True,  # someone must seed reserve — usually deployer
            capital_required=0.0,  # if protocol seeds — research; default assume seed needed
            automatic_payout=False,
            reserve=0,
            poolReserve=0,
            executable_depth=0,
            max_executable=0,
            status="DISCOVERED",
            evidence="Without initial reserve → NO_REAL_COUNTER_LIQUIDITY",
            notes="If initial reserve absent → NO_REAL_COUNTER_LIQUIDITY",
        )
    ]


def sponsored_liquidity_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_sponsored_liq",
            protocol="SPONSORED_LIQUIDITY_RESEARCH",
            source="SPONSORED_LIQUIDITY",
            sourceType="SPONSORED_LIQUIDITY",
            kind="SPONSORED_LIQUIDITY",
            gas_required=0.0,
            sponsor=True,
            eligibility="Live sponsor campaign for pair — usually none for VCORE",
            action="claim_or_swap_via_sponsor",
            automatic_payout=None,
            evidence="Hypothesis only until documented campaign",
            status="HYPOTHESIS",
        )
    ]


def market_maker_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_mm_program",
            protocol="MARKET_MAKER_PROGRAM",
            source="MARKET_MAKER",
            sourceType="MARKET_MAKER",
            kind="MARKET_MAKER",
            application_required=True,
            account_required=True,
            eligibility="MM application + inventory",
            action="apply_mm",
            automatic_payout=False,
            evidence="External MM provides inventory — not permissionless",
        )
    ]


def grant_adapter() -> list[dict[str, Any]]:
    """Kept only to prove REJECT under strict filter — not primary search."""
    return [
        _base(
            opportunityId="cl_grant_sample",
            protocol="ECOSYSTEM_GRANT",
            source="GRANT",
            sourceType="GRANT",
            kind="GRANT",
            eligibility="Proposal + acceptance",
            action="apply_grant",
            application_required=True,
            account_required=True,
            kyc_required=True,
            automatic_payout=False,
            evidence="Out of VH-2 primary class — EXPECT REJECT",
        )
    ]


def permissionless_pool_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_perm_pool_empty",
            protocol="STON_OR_DEDUST_STYLE",
            source="PERMISSIONLESS_POOL",
            sourceType="PERMISSIONLESS_POOL",
            kind="PERMISSIONLESS_POOL",
            eligibility="Anyone can create pool — creator must deposit BOTH assets",
            action="create_pool",
            deposit_required=True,
            capital_required=1.0,
            automatic_payout=False,
            poolReserve=0,
            executable_depth=0,
            max_executable=0,
            evidence="Empty / self-seeded pool ≠ external counter-liquidity at €0",
        )
    ]


def aggregator_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_aggregator",
            protocol="AGGREGATOR_GENERIC",
            source="AGGREGATOR",
            sourceType="AGGREGATOR",
            kind="AGGREGATOR",
            eligibility="Token must be listed with underlying liquidity",
            action="route_swap",
            automatic_payout=False,
            evidence="Aggregator without pool → UNSUPPORTED for VCORE until listed",
            status="DISCOVERED",
        )
    ]


def compute_reward_adapter() -> list[dict[str, Any]]:
    """Primary VH-2 class: permissionless compute → automatic reward."""
    return [
        _base(
            opportunityId="cl_perm_compute_research",
            protocol="PUBLIC_VERIFIABLE_COMPUTE",
            source="COMPUTE_REWARD",
            sourceType="COMPUTE_REWARD",
            counterAsset="varies",
            asset="REWARD_TOKEN",
            kind="PERMISSIONLESS_COMPUTE",
            eligibility="Public work + on-chain/oracle verify — no account if true permissionless",
            action="execute_public_work",
            automatic_payout=True,
            registration_required=False,
            account_required=False,
            application_required=False,
            evidence="RESEARCH: live instances rare; must verify concrete protocol docs + contract",
            status="HYPOTHESIS",
            expectedAmount=None,
            withdrawalPath="protocol_reward → owner_wallet",
        ),
        _base(
            opportunityId="cl_open_protocol_reward",
            protocol="OPEN_PROTOCOL_REWARDS",
            source="PROTOCOL_REWARD",
            sourceType="PROTOCOL_REWARD",
            counterAsset="TON/USDT",
            asset="PROTOCOL_REWARD",
            kind="OPEN_PROTOCOL_REWARDS",
            eligibility="Permissionless call / claim without registration",
            action="call_reward_entrypoint",
            automatic_payout=True,
            evidence="Hypothesis: most 'rewards' still need gas or deposit — verify per protocol",
            status="HYPOTHESIS",
            gas_required=0.05,
            sponsor=False,
        ),
    ]


def cross_chain_adapter() -> list[dict[str, Any]]:
    return [
        _base(
            opportunityId="cl_xchain",
            protocol="CROSS_CHAIN_BRIDGE_RFQ",
            source="CROSS_CHAIN_LIQUIDITY",
            sourceType="CROSS_CHAIN_LIQUIDITY",
            kind="CROSS_CHAIN",
            eligibility="Supported assets only — VCORE not native on THOR/etc.",
            action="swap_via_bridge",
            automatic_payout=False,
            evidence="VCORE unsupported on major bridges → UNSUPPORTED until mapped",
        )
    ]


def unusual_liquidity_seeds() -> list[dict[str, Any]]:
    """UnusualLiquidityDetector seeds — hypotheses, not opportunities."""
    return [
        _base(
            opportunityId="cl_unusual_solver",
            protocol="INTENT_SOLVER_NETWORK",
            source="OTHER_DOCUMENTED_MECHANISM",
            sourceType="SOLVER_LIQUIDITY",
            kind="UNUSUAL",
            status="HYPOTHESIS",
            eligibility="Solver inventories — usually need supported token + RFQ",
            action="submit_intent",
            automatic_payout=False,
            application_required=False,
            evidence="Why liquidity exists: solvers hold inventory for supported pairs. VCORE access: unknown.",
        ),
        _base(
            opportunityId="cl_unusual_bootstrap",
            protocol="LBP_AUCTION",
            source="LIQUIDITY_BOOTSTRAP",
            sourceType="LIQUIDITY_BOOTSTRAP",
            kind="UNUSUAL",
            status="HYPOTHESIS",
            eligibility="Auction / LBP — usually needs capital to buy",
            action="participate_auction",
            purchase_required=True,
            capital_required=10.0,
            automatic_payout=False,
            evidence="Bootstrap ≠ free counter-liquidity",
        ),
    ]


ALL_ADAPTERS: list[tuple[str, AdapterFn]] = [
    ("permissionless_compute", compute_reward_adapter),
    ("bonding_curve", bonding_curve_adapter),
    ("permissionless_pool", permissionless_pool_adapter),
    ("protocol_liquidity", protocol_liquidity_adapter),
    ("sponsored_liquidity", sponsored_liquidity_adapter),
    ("incentive", incentive_adapter),
    ("market_maker", market_maker_adapter),
    ("aggregator", aggregator_adapter),
    ("cross_chain", cross_chain_adapter),
    ("unusual", unusual_liquidity_seeds),
    ("grant_reject_sample", grant_adapter),
]


def run_adapters() -> dict[str, Any]:
    results = []
    items: list[dict[str, Any]] = []
    for name, fn in ALL_ADAPTERS:
        t0 = time.time()
        try:
            batch = fn()
            results.append({"adapter": name, "ok": True, "count": len(batch), "ms": int((time.time() - t0) * 1000)})
            items.extend(batch)
        except Exception as e:
            results.append({"adapter": name, "ok": False, "count": 0, "error": str(e), "status": "SKIPPED"})
    return {"at": _now(), "adapters": results, "raw": items}
