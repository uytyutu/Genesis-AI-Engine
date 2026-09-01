"""AI experiment ledger — proposals need BASELINE→VERIFY before VERIFIED."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Experiment:
    id: str
    algorithm: str
    baseline_ops: float
    candidate_ops: float | None
    hardware: str
    speedup: float | None
    status: str  # PROPOSED | RUNNING | PASS | FAIL | VERIFIED
    note: str
    at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_experiments(path: Path) -> list[Experiment]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    out = []
    for r in raw.get("experiments") or []:
        out.append(
            Experiment(
                id=str(r["id"]),
                algorithm=str(r.get("algorithm")),
                baseline_ops=float(r.get("baseline_ops") or 0),
                candidate_ops=r.get("candidate_ops"),
                hardware=str(r.get("hardware") or ""),
                speedup=r.get("speedup"),
                status=str(r.get("status") or "PROPOSED"),
                note=str(r.get("note") or ""),
                at=str(r.get("at") or ""),
            )
        )
    return out


def record_baseline(path: Path, algorithm: str, baseline_ops: float, hardware: str) -> Experiment:
    path.parent.mkdir(parents=True, exist_ok=True)
    experiments = load_experiments(path)
    exp = Experiment(
        id=f"EXP-{uuid.uuid4().hex[:6].upper()}",
        algorithm=algorithm,
        baseline_ops=baseline_ops,
        candidate_ops=None,
        hardware=hardware,
        speedup=None,
        status="PROPOSED",
        note="LLM/optimizer may propose candidate later — NOT VERIFIED until same-output + faster measured.",
        at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    experiments.append(exp)
    path.write_text(
        json.dumps({"experiments": [e.to_dict() for e in experiments]}, indent=2),
        encoding="utf-8",
    )
    return exp
