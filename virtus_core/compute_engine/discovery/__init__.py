"""Protocol / algorithm registry — statuses gate auto-start."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Status = Literal[
    "DISCOVERED",
    "RESEARCHED",
    "BENCHMARKED",
    "VERIFIED",
    "ENABLED",
    "DISABLED",
    "SKIPPED",
]


@dataclass
class AlgorithmEntry:
    id: str
    name: str
    protocol: str
    network: str
    reward_unit: str
    hardware_requirement: str
    wallet_requirement: str
    status: Status
    reason: str
    notes: str = ""
    pool_or_api: str = ""
    min_payout: str = "unknown"
    fees: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_registry() -> list[AlgorithmEntry]:
    """Static researched catalog — auto-run ONLY VERIFIED+ENABLED."""
    return [
        AlgorithmEntry(
            id="btc_sha256",
            name="Bitcoin SHA-256",
            protocol="PoW",
            network="bitcoin-mainnet",
            reward_unit="BTC",
            hardware_requirement="ASIC preferred; GPU/CPU uneconomic",
            wallet_requirement="BTC address",
            status="RESEARCHED",
            reason="Consumer GPU (GTX 1650 class) cannot compete with ASIC — expect NEGATIVE net.",
            pool_or_api="stratum (not auto-wired in V1)",
            notes="Benchmark CPU sha256d for measurement only. Worker DISABLED.",
        ),
        AlgorithmEntry(
            id="golem_provider",
            name="Golem Network Provider",
            protocol="distributed-compute",
            network="golem",
            reward_unit="GLM",
            hardware_requirement="x86-64 Linux + KVM (Windows/WSL unsupported by Golem support)",
            wallet_requirement="Yagna local wallet / GLM",
            status="SKIPPED",
            reason="REQUIRES MANUAL SETUP · Linux+KVM · not zero-setup on this Windows host.",
            pool_or_api="https://docs.golem.network/",
            notes="NO ACCOUNT=NO BLOCKER → skip, continue discovery.",
        ),
        AlgorithmEntry(
            id="flux_pouw",
            name="Flux PoUW / compute",
            protocol="PoUW",
            network="flux",
            reward_unit="FLUX",
            hardware_requirement="Kubernetes / FluxEdge node participation",
            wallet_requirement="Flux wallet",
            status="DISCOVERED",
            reason="Infrastructure-heavy — not VERIFIED for auto worker on desktop Windows.",
            pool_or_api="https://runonflux.com/",
            notes="Research only until adapter passes VERIFIED gate.",
        ),
        AlgorithmEntry(
            id="local_sha256_measure",
            name="Local SHA-256 measure worker",
            protocol="research-benchmark",
            network="local",
            reward_unit="NONE",
            hardware_requirement="CPU",
            wallet_requirement="none",
            status="VERIFIED",
            reason="Measures real throughput; reward ALWAYS 0 (no external payout).",
            notes="Safe to run for research. REAL_REVENUE remains 0.",
        ),
        AlgorithmEntry(
            id="gpu_pow_generic",
            name="Generic GPU PoW networks",
            protocol="PoW",
            network="various",
            reward_unit="token",
            hardware_requirement="CUDA miner binary + pool",
            wallet_requirement="coin address",
            status="DISCOVERED",
            reason="No VERIFIED adapter yet — do not auto-start unknown miners from LLM suggestions.",
        ),
    ]


def mark_benchmarked(registry: list[AlgorithmEntry], algo_id: str) -> None:
    for e in registry:
        if e.id == algo_id and e.status in {"DISCOVERED", "RESEARCHED", "VERIFIED"}:
            if e.status != "VERIFIED":
                e.status = "BENCHMARKED"
            e.notes = (e.notes + " | local benchmark recorded").strip(" |")
