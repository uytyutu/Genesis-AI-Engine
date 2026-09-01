"""Curated + fetched bounty opportunities (public programs)."""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Literal

Kind = Literal[
    "SECURITY_BOUNTY",
    "SMART_CONTRACT_BOUNTY",
    "AUDIT_COMPETITION",
    "CODE_BOUNTY",
    "COMPUTE_REWARD",
    "PROTOCOL_REWARD",
    "CLAIM_RESEARCH",
]

Status = Literal[
    "DISCOVERED",
    "RESEARCHED",
    "IN_SCOPE_OK",
    "WORTH_INVESTIGATING",
    "SKIPPED",
    "SUBMITTED",
    "PAID",
]


@dataclass
class Opportunity:
    id: str
    title: str
    kind: Kind
    platform: str
    url: str
    max_bounty_usd: float
    min_bounty_usd: float
    estimated_effort_h: float
    competition: str  # low|medium|high
    probability: float  # 0..1 subjective prior
    local_verify_possible: bool
    requires_account: bool
    status: Status
    notes: str
    expected_value_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _seed_catalog() -> list[Opportunity]:
    """Public programs — links only. Researcher must read live scope before any work."""
    return [
        Opportunity(
            id="immunefi_hub",
            title="Immunefi — Web3 bug bounty hub",
            kind="SECURITY_BOUNTY",
            platform="Immunefi",
            url="https://immunefi.com/explore/",
            max_bounty_usd=1_000_000,
            min_bounty_usd=500,
            estimated_effort_h=40,
            competition="high",
            probability=0.02,
            local_verify_possible=True,
            requires_account=True,
            status="DISCOVERED",
            notes="Official platform. PoC required for smart-contract reports. Known issues excluded.",
        ),
        Opportunity(
            id="immunefi_0x",
            title="0x Protocol (Immunefi listing)",
            kind="SMART_CONTRACT_BOUNTY",
            platform="Immunefi",
            url="https://immunefi.com/bug-bounty/0x/information/",
            max_bounty_usd=1_000_000,
            min_bounty_usd=1_000,
            estimated_effort_h=60,
            competition="high",
            probability=0.015,
            local_verify_possible=True,
            requires_account=True,
            status="RESEARCHED",
            notes="Max published $1M class. Read live scope/assets before analysis. No mainnet exploit.",
        ),
        Opportunity(
            id="immunefi_immutable",
            title="Immutable (Immunefi listing)",
            kind="SMART_CONTRACT_BOUNTY",
            platform="Immunefi",
            url="https://immunefi.com/explore/",
            max_bounty_usd=1_000_000,
            min_bounty_usd=500,
            estimated_effort_h=50,
            competition="high",
            probability=0.015,
            local_verify_possible=True,
            requires_account=True,
            status="DISCOVERED",
            notes="Verify current program page — max can change. Scope rules bind.",
        ),
        Opportunity(
            id="code4rena",
            title="Code4rena audit contests",
            kind="AUDIT_COMPETITION",
            platform="Code4rena",
            url="https://code4rena.com/",
            max_bounty_usd=100_000,
            min_bounty_usd=0,
            estimated_effort_h=30,
            competition="high",
            probability=0.05,
            local_verify_possible=True,
            requires_account=True,
            status="DISCOVERED",
            notes="Contest pools — competitive. Follow contest rules.",
        ),
        Opportunity(
            id="sherlock",
            title="Sherlock audit contests / judging",
            kind="AUDIT_COMPETITION",
            platform="Sherlock",
            url="https://audits.sherlock.xyz/",
            max_bounty_usd=80_000,
            min_bounty_usd=0,
            estimated_effort_h=30,
            competition="high",
            probability=0.04,
            local_verify_possible=True,
            requires_account=True,
            status="DISCOVERED",
            notes="Contest / judging model. Not a wallet sweep.",
        ),
        Opportunity(
            id="hackerone_web3",
            title="HackerOne (Web3 / crypto programs)",
            kind="SECURITY_BOUNTY",
            platform="HackerOne",
            url="https://hackerone.com/opportunities/all",
            max_bounty_usd=250_000,
            min_bounty_usd=100,
            estimated_effort_h=25,
            competition="high",
            probability=0.03,
            local_verify_possible=True,
            requires_account=True,
            status="DISCOVERED",
            notes="Filter to in-scope Web3. Account required → still discoverable, submit needs login.",
        ),
        Opportunity(
            id="dormant_observe",
            title="Dormant / unclaimed asset OBSERVATION only",
            kind="CLAIM_RESEARCH",
            platform="Virtus Research",
            url="",
            max_bounty_usd=0,
            min_bounty_usd=0,
            estimated_effort_h=0,
            competition="n/a",
            probability=0.0,
            local_verify_possible=False,
            requires_account=False,
            status="SKIPPED",
            notes=(
                "Foreign dormant wallets = OBSERVE ONLY. "
                "If protocol officially allows claim/recovery → reclassify to PROTOCOL_REWARD after rules check. "
                "Never auto-sweep."
            ),
        ),
        Opportunity(
            id="compute_engine",
            title="Virtus Compute Engine (measured throughput)",
            kind="COMPUTE_REWARD",
            platform="Virtus Local",
            url="/compute",
            max_bounty_usd=0,
            min_bounty_usd=0,
            estimated_effort_h=1,
            competition="n/a",
            probability=0.0,
            local_verify_possible=True,
            requires_account=False,
            status="SKIPPED",
            notes="No profitable compute found on this host yet. See /compute.",
        ),
    ]


def compute_ev(o: Opportunity) -> float:
    """Rough expected value = probability * mid bounty (not a promise)."""
    mid = (o.max_bounty_usd + o.min_bounty_usd) / 2.0
    return round(o.probability * mid, 2)


def rank_opportunities(items: list[Opportunity]) -> list[Opportunity]:
    for o in items:
        o.expected_value_usd = compute_ev(o)
        if o.status == "SKIPPED":
            continue
        # Heuristic: EV > $100 or high max with local verify → worth investigating
        if o.expected_value_usd >= 100 and o.local_verify_possible:
            o.status = "WORTH_INVESTIGATING"
    items.sort(key=lambda x: (-(0 if x.status == "SKIPPED" else 1), -x.expected_value_usd, -x.max_bounty_usd))
    return items


def try_fetch_immunefi_ping() -> dict[str, Any]:
    """Best-effort reachability check — does not scrape private data."""
    url = "https://immunefi.com/explore/"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VirtusValueHunter/0.1"})
        with urllib.request.urlopen(req, timeout=12) as r:
            code = r.status
            return {"ok": 200 <= code < 400, "http": code, "url": url, "at": _now()}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url, "at": _now()}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def discover() -> dict[str, Any]:
    from virtus_core.value_hunter.source_hunter import hunt as source_hunt

    catalog = rank_opportunities(_seed_catalog())
    ping = try_fetch_immunefi_ping()
    worth = [o for o in catalog if o.status == "WORTH_INVESTIGATING"]
    sources = source_hunt(max_capital_eur=0.0)
    return {
        "engine": "Virtus Autonomous Value Hunter v2",
        "version": "2.1.0",
        "law": "bounty/report + zero-capital sources — no foreign wallet seizure; no painted REAL",
        "immunefi_reachable": ping,
        "opportunities": [o.to_dict() for o in catalog],
        "worth_investigating": len(worth),
        "zero_capital_sources": sources,
        "target": sources.get("target"),
        "pipeline": sources.get("pipeline"),
        "forbidden": [
            "mainnet exploit without program authorization",
            "taking dormant third-party wallets",
            "fake PoC / fake payout in ledger",
            "VCORE→BTC without reserves / unsupported THOR asset",
        ],
        "next_actions": [
            "Run ZERO-CAPITAL queue (TESTABLE/QUEUE) — read live eligibility",
            "Keep Genesis + Route Finder as infrastructure (not money printers)",
            "Use THOR/DEX only as EXIT after a real source asset exists",
            "Track MAXIMUM REALIZED BTC under capital €0 — never paint 300",
            "Never mark REAL until external confirmation",
        ],
        "promise": sources.get("promise"),
        "at": _now(),
    }


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2, ensure_ascii=False))
