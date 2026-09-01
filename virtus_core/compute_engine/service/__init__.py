"""Compute Engine Service — orchestrates audit / measure / report."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from virtus_core.compute_engine.ai import record_baseline
from virtus_core.compute_engine.config import (
    EXPERIMENT_PATH,
    LEDGER_PATH,
    STATE_PATH,
    ComputeConfig,
    load_config,
    save_config,
)
from virtus_core.compute_engine.discovery import default_registry, mark_benchmarked
from virtus_core.compute_engine.discovery.opportunity_scanner import scan_opportunities
from virtus_core.compute_engine.hardware import detect_hardware
from virtus_core.compute_engine.hardware.benchmark import run_default_benchmarks
from virtus_core.compute_engine.mining import WorkerManager
from virtus_core.compute_engine.treasury import load_ledger, save_empty_ledger


def run_full_audit(*, run_measure: bool = False, cfg: ComputeConfig | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    save_config(cfg)

    if not LEDGER_PATH.exists():
        save_empty_ledger(LEDGER_PATH)

    hw = detect_hardware()
    benches = run_default_benchmarks(
        cfg.benchmark_seconds,
        power_watts=hw.gpu.power_watts,
        temperature_c=hw.gpu.temperature_c,
        threads_hint=hw.cpu_threads,
    )

    registry = default_registry()
    mark_benchmarked(registry, "btc_sha256")
    mark_benchmarked(registry, "local_sha256_measure")

    opps = scan_opportunities(
        registry,
        benches,
        electricity_eur_per_kwh=cfg.electricity_eur_per_kwh,
        power_watts=hw.gpu.power_watts,
    )

    sha = next((b for b in benches if b.algorithm == "sha256d_cpu"), None)
    if sha:
        record_baseline(
            EXPERIMENT_PATH,
            algorithm="sha256d_cpu",
            baseline_ops=sha.ops_per_sec,
            hardware=hw.cpu_name or "cpu",
        )

    workers = WorkerManager()
    worker_payload: dict[str, Any] | None = None
    if run_measure:
        # Safe research worker only
        if cfg.auto_mode and "local_sha256_measure" not in cfg.enabled_workers:
            worker_payload = workers.reject_unverified(
                "local_sha256_measure",
                "AUTO_MODE on but worker not in enabled_workers — refused.",
            ).to_dict()
        else:
            worker_payload = workers.start_local_measure(min(5.0, cfg.benchmark_seconds + 2)).to_dict()
    elif cfg.auto_mode:
        # Auto mode still refuses unverified profitable miners
        profitable = [o for o in opps if o.can_run and (o.expected_net_eur_day or 0) > 0]
        if not profitable:
            worker_payload = workers.reject_unverified(
                "auto",
                "NO PROFITABLE COMPUTE FOUND — auto mode idle.",
            ).to_dict()
        else:
            worker_payload = workers.reject_unverified(
                profitable[0].source_id,
                "Candidate has positive EXPECTED net but no VERIFIED external payout adapter — not starting.",
            ).to_dict()

    treasury = load_ledger(LEDGER_PATH)

    profitable_found = any(
        o.expected_net_eur_day is not None and o.expected_net_eur_day > 0 and o.can_run for o in opps
    )

    report = {
        "engine": "Virtus Autonomous Compute / Mining Engine",
        "version": "0.1.0",
        "auto_mode": cfg.auto_mode,
        "electricity_eur_per_kwh": cfg.electricity_eur_per_kwh,
        "electricity_status": "KNOWN" if cfg.electricity_eur_per_kwh is not None else "UNKNOWN",
        "hardware": hw.to_dict(),
        "benchmarks": [b.to_dict() for b in benches],
        "registry": [e.to_dict() for e in registry],
        "opportunities": [o.to_dict() for o in opps],
        "current_worker": worker_payload,
        "treasury": treasury.to_dict(),
        "conclusion": (
            "NO PROFITABLE COMPUTE FOUND"
            if not profitable_found
            else "EXPECTED positive candidate — still needs CONFIRMED external payout before REAL"
        ),
        "blockers": _blockers(hw, cfg, opps),
        "laws": [
            "REAL COMPUTATION → REAL VERIFICATION → REAL REWARD",
            "LLM proposal ≠ VERIFIED optimization",
            "REAL revenue only with External Payout ID (CONFIRMED)",
            "AUTO_MODE default false",
        ],
    }

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _blockers(hw: Any, cfg: ComputeConfig, opps: list) -> list[str]:
    blockers = []
    if cfg.electricity_eur_per_kwh is None:
        blockers.append("Set VIRTUS_ELECTRICITY_EUR_PER_KWH or config electricity_eur_per_kwh for EUR NET.")
    if not hw.gpu.cuda_available and hw.gpu.name:
        blockers.append("GPU present but CUDA not confirmed in-process — no VERIFIED GPU miner adapter.")
    if any(o.status == "SKIPPED" and "Golem" in o.algorithm for o in opps):
        blockers.append("Golem Provider skipped: Windows host lacks supported Linux+KVM path.")
    blockers.append("No Live Earn connector with CONFIRMED payout wired for compute yet → REAL treasury = 0.")
    return blockers


def write_markdown_report(report: dict[str, Any], path: Path | None = None) -> Path:
    path = path or (STATE_PATH.parent / "VIRTUS_COMPUTE_ENGINE_REPORT.md")
    hw = report.get("hardware") or {}
    gpu = hw.get("gpu") or {}
    lines = [
        "# VIRTUS COMPUTE ENGINE REPORT",
        "",
        f"Version: `{report.get('version')}` · AUTO_MODE=`{report.get('auto_mode')}`",
        "",
        "## 1. Detected hardware",
        f"- OS: {hw.get('os')} / {hw.get('arch')}",
        f"- CPU: {hw.get('cpu_name')} · cores={hw.get('cpu_cores')} threads={hw.get('cpu_threads')}",
        f"- RAM: {hw.get('ram_gb')} GB",
        f"- GPU: {gpu.get('name')} · VRAM={gpu.get('vram_mib')} MiB · power={gpu.get('power_watts')} W · temp={gpu.get('temperature_c')} °C",
        f"- CUDA available (in-process): {gpu.get('cuda_available')}",
        "",
        "## 2–3. Benchmarks (measured)",
    ]
    for b in report.get("benchmarks") or []:
        lines.append(
            f"- `{b.get('algorithm')}` on {b.get('device')}: **{b.get('ops_per_sec')} {b.get('unit')}** "
            f"({b.get('duration_sec')}s) — {b.get('notes')}"
        )
    lines += ["", "## 4. Registry / opportunities"]
    for o in report.get("opportunities") or []:
        lines.append(
            f"- #{o.get('rank')} `{o.get('source_id')}` · status={o.get('status')} · "
            f"net/day={o.get('expected_net_eur_day')} · can_run={o.get('can_run')}"
        )
        lines.append(f"  - {o.get('detail')}")
    lines += [
        "",
        "## 5. Current worker",
        f"```json\n{json.dumps(report.get('current_worker'), indent=2, ensure_ascii=False)}\n```",
        "",
        "## 6. Treasury (REAL = CONFIRMED only)",
        f"```json\n{json.dumps(report.get('treasury'), indent=2, ensure_ascii=False)}\n```",
        "",
        f"## 7. Conclusion",
        f"**{report.get('conclusion')}**",
        "",
        "## 8. Blockers",
    ]
    for b in report.get("blockers") or []:
        lines.append(f"- {b}")
    lines += [
        "",
        "## Critical rule",
        "Do not write PROFITABLE / EARNED / MINING SUCCESS without external confirmation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
