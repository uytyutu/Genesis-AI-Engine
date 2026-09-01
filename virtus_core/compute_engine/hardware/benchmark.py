"""Local real benchmarks — measured ops/sec, never internet-calculator truth."""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class BenchmarkResult:
    algorithm: str
    device: str
    duration_sec: float
    operations: int
    ops_per_sec: float
    unit: str
    power_watts_hint: float | None
    temperature_c_hint: float | None
    timestamp: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def benchmark_sha256_cpu(seconds: float = 3.0, threads_hint: int | None = None) -> BenchmarkResult:
    """Measure SHA-256 hashes/sec on CPU (single-process tight loop)."""
    seconds = max(0.5, min(30.0, float(seconds)))
    payload = b"virtus-compute-engine-v1" + b"\x00" * 48
    counter = 0
    t0 = time.perf_counter()
    end = t0 + seconds
    # double-SHA256-like workload (Bitcoin-style cost proxy, not a miner)
    while time.perf_counter() < end:
        h = hashlib.sha256(payload).digest()
        hashlib.sha256(h).digest()
        counter += 1
        # tiny mutate
        payload = h + payload[32:64]
    elapsed = max(1e-6, time.perf_counter() - t0)
    ops = counter / elapsed
    note = "CPU double-SHA256 throughput (research measure). NOT network hashrate / NOT earnings."
    if threads_hint:
        note += f" Logical CPUs reported: {threads_hint}."
    return BenchmarkResult(
        algorithm="sha256d_cpu",
        device="cpu",
        duration_sec=round(elapsed, 3),
        operations=counter,
        ops_per_sec=round(ops, 2),
        unit="H/s",
        power_watts_hint=None,
        temperature_c_hint=None,
        timestamp=_now(),
        notes=note,
    )


def benchmark_blake2b_cpu(seconds: float = 2.0) -> BenchmarkResult:
    seconds = max(0.5, min(30.0, float(seconds)))
    payload = b"virtus-blake2b" * 4
    counter = 0
    t0 = time.perf_counter()
    end = t0 + seconds
    while time.perf_counter() < end:
        payload = hashlib.blake2b(payload).digest()
        counter += 1
    elapsed = max(1e-6, time.perf_counter() - t0)
    return BenchmarkResult(
        algorithm="blake2b_cpu",
        device="cpu",
        duration_sec=round(elapsed, 3),
        operations=counter,
        ops_per_sec=round(counter / elapsed, 2),
        unit="H/s",
        power_watts_hint=None,
        temperature_c_hint=None,
        timestamp=_now(),
        notes="CPU blake2b throughput — research only.",
    )


def run_default_benchmarks(
    seconds: float = 3.0,
    *,
    power_watts: float | None = None,
    temperature_c: float | None = None,
    threads_hint: int | None = None,
) -> list[BenchmarkResult]:
    sha = benchmark_sha256_cpu(seconds, threads_hint=threads_hint)
    if power_watts is not None:
        sha.power_watts_hint = power_watts
    if temperature_c is not None:
        sha.temperature_c_hint = temperature_c
    blake = benchmark_blake2b_cpu(min(2.0, seconds))
    return [sha, blake]
