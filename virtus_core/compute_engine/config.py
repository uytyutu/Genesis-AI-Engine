"""Compute Engine configuration — AUTO_MODE=false by default."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "virtus_core" / "compute_engine" / ".runtime"
CONFIG_PATH = DATA_DIR / "config.json"
LEDGER_PATH = DATA_DIR / "reward_ledger.json"
EXPERIMENT_PATH = DATA_DIR / "experiments.json"
STATE_PATH = DATA_DIR / "engine_state.json"


@dataclass
class ComputeConfig:
    auto_mode: bool = False
    electricity_eur_per_kwh: float | None = None  # None = UNKNOWN → no REAL profit claim
    min_switch_advantage: float = 0.10
    benchmark_seconds: float = 3.0
    enabled_workers: list[str] = field(default_factory=list)  # only explicitly enabled
    currency: str = "EUR"


def load_config() -> ComputeConfig:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        try:
            raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return ComputeConfig(
                auto_mode=bool(raw.get("auto_mode", False)),
                electricity_eur_per_kwh=raw.get("electricity_eur_per_kwh"),
                min_switch_advantage=float(raw.get("min_switch_advantage", 0.10)),
                benchmark_seconds=float(raw.get("benchmark_seconds", 3.0)),
                enabled_workers=list(raw.get("enabled_workers") or []),
                currency=str(raw.get("currency") or "EUR"),
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    # env override for electricity only
    cfg = ComputeConfig()
    env_kwh = os.environ.get("VIRTUS_ELECTRICITY_EUR_PER_KWH", "").strip()
    if env_kwh:
        try:
            cfg.electricity_eur_per_kwh = float(env_kwh)
        except ValueError:
            pass
    if os.environ.get("VIRTUS_COMPUTE_AUTO_MODE", "").strip().lower() in {"1", "true", "yes"}:
        cfg.auto_mode = True
    save_config(cfg)
    return cfg


def save_config(cfg: ComputeConfig) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
