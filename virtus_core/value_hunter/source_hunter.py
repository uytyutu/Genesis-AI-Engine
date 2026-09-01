"""
ZERO-CAPITAL SOURCE HUNTER — Virtus Autonomous Value Hunter v2 (sources layer).

VCORE is the brain that finds external value — not a magical claim on BTC.
THORChain / DEX = exit converters AFTER a real source asset exists.
Never fabricate balances. Never use foreign-protocol exploits.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

SourceKind = Literal[
    "REWARD",
    "INCENTIVE",
    "CLAIM",
    "FAUCET",
    "SPONSORED_GAS",
    "LIQUIDITY_INCENTIVE",
    "PROTOCOL_DISTRIBUTION",
    "DEVELOPER_PROGRAM",
    "TESTNET_REWARD",
    "BUG_BOUNTY",
    "EXIT_CONVERTER",
    "FORBIDDEN",
]

ZeroCapital = Literal["PASS", "FAIL", "TESTABLE", "RESEARCH", "SKIPPED"]


@dataclass
class ValueSource:
    id: str
    title: str
    kind: SourceKind
    asset: str
    eligibility: str
    capital_required_eur: float
    gas_required_eur: float
    account_required: bool
    kyc_required: bool
    automatable: str  # high|partial|low|none
    expected_value_hint: str
    expiration: str
    risk: str
    url: str
    zero_capital: ZeroCapital
    status: str  # DISCOVERED|TESTABLE|QUEUE|REJECTED|EXIT_ONLY
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _catalog() -> list[ValueSource]:
    """Curated public mechanisms — links + honest capital flags. Not promises."""
    return [
        ValueSource(
            id="src_immunefi",
            title="Immunefi / public bug bounty programs",
            kind="BUG_BOUNTY",
            asset="USDT/USDC/ETH (payout varies)",
            eligibility="In-scope finding + valid report",
            capital_required_eur=0.0,
            gas_required_eur=0.0,
            account_required=True,
            kyc_required=False,
            automatable="partial",
            expected_value_hint="Unknown — EV from program max × skill; not guaranteed",
            expiration="per program",
            risk="Competition high; invalid reports waste time",
            url="https://immunefi.com/explore/",
            zero_capital="TESTABLE",
            status="TESTABLE",
            notes="€0 entry. Account for submit. REAL only after external payout.",
        ),
        ValueSource(
            id="src_code4rena",
            title="Code4rena / audit contests",
            kind="INCENTIVE",
            asset="USDC (contest pool share)",
            eligibility="Contest registration + valid findings",
            capital_required_eur=0.0,
            gas_required_eur=0.0,
            account_required=True,
            kyc_required=False,
            automatable="partial",
            expected_value_hint="Pool-dependent; competitive",
            expiration="per contest",
            risk="High competition",
            url="https://code4rena.com/",
            zero_capital="TESTABLE",
            status="TESTABLE",
            notes="Capital €0 to enter. Skill/time is the real cost.",
        ),
        ValueSource(
            id="src_ton_testnet_faucet",
            title="TON testnet faucet",
            kind="FAUCET",
            asset="testnet TON",
            eligibility="Testnet wallet address",
            capital_required_eur=0.0,
            gas_required_eur=0.0,
            account_required=False,
            kyc_required=False,
            automatable="high",
            expected_value_hint="Testnet only — NOT mainnet BTC/TON",
            expiration="rate limits",
            risk="No REAL mainnet value",
            url="https://t.me/testgiver_ton_bot",
            zero_capital="PASS",
            status="QUEUE",
            notes="Useful for Genesis Gate. Does NOT count as Reality Ledger REAL.",
        ),
        ValueSource(
            id="src_dev_grants",
            title="Public developer / ecosystem grants",
            kind="DEVELOPER_PROGRAM",
            asset="varies (stable / native)",
            eligibility="Proposal + acceptance",
            capital_required_eur=0.0,
            gas_required_eur=0.0,
            account_required=True,
            kyc_required=True,
            automatable="low",
            expected_value_hint="Grant-sized if accepted — slow, manual",
            expiration="application windows",
            risk="KYC / approval gate; not permissionless",
            url="",
            zero_capital="FAIL",
            status="REJECTED",
            notes="Often KYC → fails strict permissionless zero-capital filter.",
        ),
        ValueSource(
            id="src_lp_incentive",
            title="DEX liquidity mining incentives",
            kind="LIQUIDITY_INCENTIVE",
            asset="TON/USDT LP rewards",
            eligibility="Provide both sides of pool",
            capital_required_eur=50.0,
            gas_required_eur=1.0,
            account_required=True,
            kyc_required=False,
            automatable="high",
            expected_value_hint="Requires depositing real assets first",
            expiration="campaign",
            risk="Impermanent loss + capital lock",
            url="https://help.dedust.io/en/liquidity/pools",
            zero_capital="FAIL",
            status="REJECTED",
            notes="DeDust/STON LP needs BOTH assets — CAPITAL_REQUIRED.",
        ),
        ValueSource(
            id="src_sponsored_gas_research",
            title="Sponsored / gasless claim research",
            kind="SPONSORED_GAS",
            asset="protocol-specific",
            eligibility="Must match live sponsored campaign rules",
            capital_required_eur=0.0,
            gas_required_eur=0.0,
            account_required=False,
            kyc_required=False,
            automatable="high",
            expected_value_hint="Only if a live gasless claim exists — usually none",
            expiration="campaign",
            risk="Phishing clones; verify official domain",
            url="",
            zero_capital="RESEARCH",
            status="DISCOVERED",
            notes="Hunter must verify official docs. No assumed free TON.",
        ),
        ValueSource(
            id="src_protocol_claim",
            title="Official permissionless claims / airdrop claim pages",
            kind="CLAIM",
            asset="varies",
            eligibility="Snapshot / on-chain eligibility",
            capital_required_eur=0.0,
            gas_required_eur=1.0,
            account_required=False,
            kyc_required=False,
            automatable="partial",
            expected_value_hint="Only if wallet is eligible — do not invent eligibility",
            expiration="claim window",
            risk="Gas may be >0; scams plentiful",
            url="",
            zero_capital="RESEARCH",
            status="DISCOVERED",
            notes="Gas >0 may still fail strict €0 gas filter depending on mode.",
        ),
        ValueSource(
            id="src_thor_exit",
            title="THORChain — exit converter (NOT a money source)",
            kind="EXIT_CONVERTER",
            asset="BTC / supported L1",
            eligibility="Hold supported inbound asset + available pool",
            capital_required_eur=0.0,
            gas_required_eur=1.0,
            account_required=False,
            kyc_required=False,
            automatable="high",
            expected_value_hint="Converts existing value only — quote needs real pools",
            expiration="n/a",
            risk="Unsupported asset (VCORE) cannot enter directly",
            url="https://dev.thorchain.org/swap-guide/quickstart-guide.html",
            zero_capital="SKIPPED",
            status="EXIT_ONLY",
            notes="SOURCE OF VALUE → supported asset → THOR → BTC. VCORE not on THOR.",
        ),
        ValueSource(
            id="src_vcore_dex_magic",
            title="Self-mint VCORE → DEX → 300 BTC with €0",
            kind="FORBIDDEN",
            asset="BTC",
            eligibility="Would require free liquidity / unsupported identity",
            capital_required_eur=0.0,
            gas_required_eur=0.0,
            account_required=False,
            kyc_required=False,
            automatable="none",
            expected_value_hint="0 — pool needs reserves; THOR needs supported assets",
            expiration="n/a",
            risk="Falsifies experiment if painted",
            url="",
            zero_capital="FAIL",
            status="REJECTED",
            notes="Rejected by Route Finder + PERMISSIONLESS_SETTLEMENT_LAW.",
        ),
        ValueSource(
            id="src_foreign_exploit",
            title="Exploit / drain foreign protocol without program",
            kind="FORBIDDEN",
            asset="any",
            eligibility="—",
            capital_required_eur=0.0,
            gas_required_eur=0.0,
            account_required=False,
            kyc_required=False,
            automatable="none",
            expected_value_hint="—",
            expiration="n/a",
            risk="Illegal / unethical",
            url="",
            zero_capital="SKIPPED",
            status="REJECTED",
            notes="Never use. Bug bounty under program only.",
        ),
    ]


def economic_filter(sources: list[ValueSource], *, max_capital_eur: float = 0.0) -> list[ValueSource]:
    out: list[ValueSource] = []
    for s in sources:
        if s.kind == "FORBIDDEN":
            s.zero_capital = "SKIPPED"
            s.status = "REJECTED"
        elif s.kind == "EXIT_CONVERTER":
            s.status = "EXIT_ONLY"
        elif s.capital_required_eur > max_capital_eur:
            s.zero_capital = "FAIL"
            s.status = "REJECTED"
        elif s.kyc_required:
            s.zero_capital = "FAIL"
            s.status = "REJECTED"
        elif s.zero_capital in ("PASS", "TESTABLE") and s.capital_required_eur <= max_capital_eur:
            if s.status not in ("REJECTED", "EXIT_ONLY"):
                s.status = "TESTABLE" if s.zero_capital == "TESTABLE" else "QUEUE"
        out.append(s)
    # Prefer TESTABLE/QUEUE first
    rank = {"QUEUE": 0, "TESTABLE": 1, "DISCOVERED": 2, "RESEARCH": 3, "EXIT_ONLY": 4, "REJECTED": 5}
    out.sort(key=lambda x: (rank.get(x.status, 9), x.capital_required_eur, x.id))
    return out


def hunt(*, max_capital_eur: float = 0.0) -> dict[str, Any]:
    sources = economic_filter(_catalog(), max_capital_eur=max_capital_eur)
    queue = [s for s in sources if s.status in ("QUEUE", "TESTABLE")]
    rejected = [s for s in sources if s.status == "REJECTED"]
    exits = [s for s in sources if s.status == "EXIT_ONLY"]
    return {
        "engine": "Virtus Autonomous Value Hunter v2",
        "module": "ZERO-CAPITAL SOURCE HUNTER",
        "version": "2.1.0",
        "note": "Catalog layer — full pipeline: virtus_core.value_hunter.pipeline.process_pipeline",
        "at": _now(),
        "target": {
            "mode": "MAXIMUM_REALIZED_BTC",
            "not": "fixed 300 BTC promise",
            "capital_eur": max_capital_eur,
            "progress_example": ["Day1: 0", "Day7: measure", "Day30: measure", "or: No viable source"],
        },
        "role_of_vcore": "Brain / orchestrator — not a claim on foreign liquidity",
        "pipeline": [
            "1 DISCOVER",
            "2 CLASSIFY",
            "3 CAPITAL FILTER",
            "4 ELIGIBILITY",
            "5 SIMULATE",
            "6 EXPECTED VALUE",
            "7 OWNER APPROVAL",
            "8 EXECUTE",
            "9 BLOCKCHAIN VERIFY",
            "10 CONVERT (DEX/THOR exit)",
            "11 TREASURY / Reality Ledger",
        ],
        "sources": [s.to_dict() for s in sources],
        "queue": [s.to_dict() for s in queue],
        "queue_count": len(queue),
        "rejected_count": len(rejected),
        "exit_converters": [s.to_dict() for s in exits],
        "law": [
            "No painted REAL",
            "No foreign exploit",
            "No VCORE→BTC magic without reserves",
            "THOR/DEX = exit after SOURCE asset exists",
            "REAL only after external confirmation",
        ],
        "promise": "System will search and measure — it does NOT promise that money will be found.",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(hunt(), indent=2, ensure_ascii=False))
