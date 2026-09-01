"""Opportunity scanner — expected net from measured + public params (honest)."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any

from virtus_core.compute_engine.discovery import AlgorithmEntry
from virtus_core.compute_engine.economics.profitability import ProfitEstimate, estimate_profit
from virtus_core.compute_engine.hardware.benchmark import BenchmarkResult


@dataclass
class Opportunity:
    rank: int
    source_id: str
    algorithm: str
    measured_ops_per_sec: float | None
    measured_unit: str | None
    expected_gross_eur_day: float | None
    expected_cost_eur_day: float | None
    expected_net_eur_day: float | None
    confidence: float
    status: str
    can_run: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _fetch_btc_network() -> dict[str, Any] | None:
    """Public blockchain.info / mempool stats — optional, timeout short."""
    urls = [
        "https://mempool.space/api/v1/mining/hashrate/3d",
        "https://blockchain.info/q/getdifficulty",
    ]
    out: dict[str, Any] = {}
    try:
        req = urllib.request.Request(
            "https://mempool.space/api/blocks/tip/height",
            headers={"User-Agent": "VirtusComputeEngine/0.1"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            out["tip_height"] = int(r.read().decode().strip())
    except Exception as e:
        out["tip_error"] = str(e)
    try:
        req = urllib.request.Request(
            "https://mempool.space/api/v1/difficulty-adjustment",
            headers={"User-Agent": "VirtusComputeEngine/0.1"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            out["difficulty"] = json.loads(r.read().decode())
    except Exception as e:
        out["difficulty_error"] = str(e)
    return out or None


def scan_opportunities(
    registry: list[AlgorithmEntry],
    benchmarks: list[BenchmarkResult],
    *,
    electricity_eur_per_kwh: float | None,
    power_watts: float | None,
) -> list[Opportunity]:
    bench_map = {b.algorithm: b for b in benchmarks}
    sha = bench_map.get("sha256d_cpu")
    network = _fetch_btc_network()

    opps: list[Opportunity] = []

    for entry in registry:
        measured = None
        unit = None
        if entry.id in {"btc_sha256", "local_sha256_measure"} and sha:
            measured = sha.ops_per_sec
            unit = sha.unit

        if entry.id == "btc_sha256":
            # Honest: consumer CPU H/s vs network ~EH/s → expected reward ≈ 0
            # Use tiny expected gross to show math, then costs dominate.
            # Network hashrate ~600 EH/s = 6e20 H/s. Share = ours/network ≈ 0.
            gross = 0.0
            detail = (
                f"Measured {measured} {unit}. BTC network tip={network.get('tip_height') if network else '?'}."
                " Share of network hashrate ≈ 0 → EXPECTED GROSS ≈ €0/day."
            )
            if electricity_eur_per_kwh is None:
                profit = ProfitEstimate(
                    source_id=entry.id,
                    gross_eur_day=gross,
                    electricity_eur_day=None,
                    fees_eur_day=0.0,
                    net_eur_day=None,
                    net_per_hour=None,
                    confidence=0.95,
                    electricity_status="UNKNOWN",
                    note="Electricity price not set — cannot claim NET profit/loss in EUR.",
                )
            else:
                watts = power_watts or 65.0  # idle/active CPU guess if no telemetry
                profit = estimate_profit(
                    source_id=entry.id,
                    gross_eur_day=gross,
                    power_watts=watts,
                    electricity_eur_per_kwh=electricity_eur_per_kwh,
                    fees_eur_day=0.0,
                    confidence=0.9,
                )
            can = False
            opps.append(
                Opportunity(
                    rank=0,
                    source_id=entry.id,
                    algorithm=entry.name,
                    measured_ops_per_sec=measured,
                    measured_unit=unit,
                    expected_gross_eur_day=profit.gross_eur_day,
                    expected_cost_eur_day=profit.electricity_eur_day,
                    expected_net_eur_day=profit.net_eur_day,
                    confidence=profit.confidence,
                    status=entry.status,
                    can_run=can,
                    detail=detail + " " + profit.note,
                )
            )
        elif entry.id == "local_sha256_measure":
            opps.append(
                Opportunity(
                    rank=0,
                    source_id=entry.id,
                    algorithm=entry.name,
                    measured_ops_per_sec=measured,
                    measured_unit=unit,
                    expected_gross_eur_day=0.0,
                    expected_cost_eur_day=None if electricity_eur_per_kwh is None else None,
                    expected_net_eur_day=0.0,
                    confidence=1.0,
                    status=entry.status,
                    can_run=True,  # research worker only — reward 0
                    detail="VERIFIED research worker. REAL_REVENUE always 0. Useful for throughput experiments.",
                )
            )
        elif entry.status == "SKIPPED":
            opps.append(
                Opportunity(
                    rank=0,
                    source_id=entry.id,
                    algorithm=entry.name,
                    measured_ops_per_sec=None,
                    measured_unit=None,
                    expected_gross_eur_day=None,
                    expected_cost_eur_day=None,
                    expected_net_eur_day=None,
                    confidence=0.0,
                    status="SKIPPED",
                    can_run=False,
                    detail=entry.reason,
                )
            )
        else:
            opps.append(
                Opportunity(
                    rank=0,
                    source_id=entry.id,
                    algorithm=entry.name,
                    measured_ops_per_sec=None,
                    measured_unit=None,
                    expected_gross_eur_day=None,
                    expected_cost_eur_day=None,
                    expected_net_eur_day=None,
                    confidence=0.2,
                    status=entry.status,
                    can_run=False,
                    detail=entry.reason,
                )
            )

    # Rank by expected net (None last), then confidence
    def sort_key(o: Opportunity) -> tuple:
        net = o.expected_net_eur_day
        return (
            0 if o.can_run else 1,
            -(net if net is not None else -1e9),
            -o.confidence,
        )

    opps.sort(key=sort_key)
    for i, o in enumerate(opps, 1):
        o.rank = i
    return opps
