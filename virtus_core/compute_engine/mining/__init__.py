"""Workers — only VERIFIED adapters; no fake shares/payouts."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from virtus_core.compute_engine.hardware.benchmark import benchmark_sha256_cpu


@dataclass
class WorkerStatus:
    worker_id: str
    algorithm: str
    state: str  # IDLE | RUNNING | STOPPED | REJECTED
    runtime_sec: float = 0.0
    measured_ops_per_sec: float | None = None
    accepted_shares: int = 0
    rejected_shares: int = 0
    real_reward: float = 0.0
    real_reward_unit: str = "EUR"
    message: str = ""
    started_at: str | None = None
    stopped_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WorkerManager:
    def __init__(self) -> None:
        self.current: WorkerStatus | None = None

    def start_local_measure(self, seconds: float = 5.0) -> WorkerStatus:
        """Run local SHA-256 measure — REAL_REWARD stays 0."""
        started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.current = WorkerStatus(
            worker_id="local_sha256_measure",
            algorithm="sha256d_cpu",
            state="RUNNING",
            started_at=started,
            message="Measuring CPU throughput…",
        )
        bench = benchmark_sha256_cpu(seconds)
        self.current = WorkerStatus(
            worker_id="local_sha256_measure",
            algorithm="sha256d_cpu",
            state="STOPPED",
            runtime_sec=bench.duration_sec,
            measured_ops_per_sec=bench.ops_per_sec,
            accepted_shares=0,
            rejected_shares=0,
            real_reward=0.0,
            message=(
                f"Measured {bench.ops_per_sec} H/s. "
                "No external job / no payout => REAL_REVENUE=0."
            ),
            started_at=started,
            stopped_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        return self.current

    def reject_unverified(self, source_id: str, reason: str) -> WorkerStatus:
        st = WorkerStatus(
            worker_id=source_id,
            algorithm=source_id,
            state="REJECTED",
            message=reason,
        )
        self.current = st
        return st
