"""Factory performance telemetry — full build-stage trace for Mission Control.

Canonical stages (SSOT):
  queue → template → content → assets → render → gates → zip → total

Legacy aliases (zip_pack, compliance_check, total_e2e) remain for older rows.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_ID = "factory_metrics_v1"
MAX_HISTORY = 1000

# Primary stage ladder (CEO table / optimization focus).
BUILD_STAGE_IDS: tuple[str, ...] = (
    "queue",
    "template",
    "content",
    "assets",
    "render",
    "gates",
    "zip",
)

STAGE_IDS = BUILD_STAGE_IDS + (
    "total",
    "total_e2e",
    "zip_pack",
    "compliance_check",
    "order_to_queue",
    "queue_to_build",
    "build_to_assets",
    "assets_to_zip",
    "zip_to_ready",
    "ready_to_download",
)

# Map legacy keys → canonical for aggregation.
_STAGE_ALIASES: dict[str, str] = {
    "zip_pack": "zip",
    "compliance_check": "gates",
    "total_e2e": "total",
    "build_to_assets": "assets",
    "assets_to_zip": "zip",
}


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path(memory_dir: Path) -> Path:
    return Path(memory_dir) / "factory_metrics.jsonl"


def normalize_stages(stages: dict[str, Any] | None) -> dict[str, float]:
    """Collapse aliases into canonical BUILD_STAGE_IDS + total."""
    raw = {str(k): float(v) for k, v in (stages or {}).items() if v is not None}
    out: dict[str, float] = {}
    for key, val in raw.items():
        canon = _STAGE_ALIASES.get(key, key)
        # Prefer first write; sum only if both present for same canon from distinct keys
        if canon in out and key != canon:
            continue
        out[canon] = round(val, 4)
    if "total" not in out and "total_e2e" in raw:
        out["total"] = round(float(raw["total_e2e"]), 4)
    return out


class StageTimer:
    """Wall-clock stage timer; call ``mark(name)`` between stages."""

    def __init__(self) -> None:
        self._t0 = time.perf_counter()
        self._last = self._t0
        self.stages: dict[str, float] = {}

    def mark(self, name: str) -> float:
        now = time.perf_counter()
        dt = round(now - self._last, 4)
        self.stages[name] = dt
        self._last = now
        return dt

    def total(self) -> float:
        return round(time.perf_counter() - self._t0, 4)

    def as_dict(self) -> dict[str, float]:
        out = dict(self.stages)
        tot = self.total()
        out["total"] = tot
        out["total_e2e"] = tot  # back-compat
        return out


def record_build(
    memory_dir: Path,
    *,
    order_id: str | None = None,
    product_id: str | None = None,
    stages: dict[str, float] | None = None,
    zip_bytes: int | None = None,
    cached_zip: bool | None = None,
    kind: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    norm = normalize_stages(stages)
    row: dict[str, Any] = {
        "engine_id": ENGINE_ID,
        "at": _utc(),
        "order_id": order_id,
        "product_id": product_id,
        "kind": kind or ("zip_cache" if cached_zip else "build"),
        "stages": norm,
        "zip_bytes": zip_bytes,
        "cached_zip": cached_zip,
    }
    if extra:
        row.update(extra)
    path = _path(memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def load_recent(memory_dir: Path, *, limit: int = 100) -> list[dict[str, Any]]:
    path = _path(memory_dir)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, Any]] = []
    for line in lines[-max(1, min(limit, MAX_HISTORY)) :]:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            if isinstance(data.get("stages"), dict):
                data = {**data, "stages": normalize_stages(data["stages"])}
            rows.append(data)
    return rows


def summary(memory_dir: Path, *, limit: int = 100) -> dict[str, Any]:
    rows = load_recent(memory_dir, limit=limit)
    # Prefer full builds for stage averages (exclude pure cache hits).
    build_rows = [r for r in rows if not r.get("cached_zip")]
    if not build_rows:
        build_rows = rows

    def _vals(stage: str, source: list[dict[str, Any]]) -> list[float]:
        out: list[float] = []
        for r in source:
            st = r.get("stages") if isinstance(r.get("stages"), dict) else {}
            v = st.get(stage)
            if v is not None and float(v) > 0:
                out.append(float(v))
        return out

    def _avg(xs: list[float]) -> float | None:
        return round(sum(xs) / len(xs), 3) if xs else None

    def _p50(xs: list[float]) -> float | None:
        if not xs:
            return None
        s = sorted(xs)
        return round(s[len(s) // 2], 3)

    totals = _vals("total", rows)
    zip_packs = _vals("zip", rows)
    cached = sum(1 for r in rows if r.get("cached_zip") is True)

    avg_stages: dict[str, float | None] = {}
    stage_table: list[dict[str, Any]] = []
    for sid in BUILD_STAGE_IDS:
        xs = _vals(sid, build_rows)
        avg = _avg(xs)
        avg_stages[sid] = avg
        stage_table.append(
            {
                "id": sid,
                "label": sid.replace("_", " ").title(),
                "avg_s": avg,
                "p50_s": _p50(xs),
                "samples": len(xs),
                "status": "ok" if avg is not None else "no_data",
            }
        )
    total_avg = _avg(totals) or _avg(_vals("total", build_rows))
    stage_table.append(
        {
            "id": "total",
            "label": "Total",
            "avg_s": total_avg,
            "p50_s": _p50(totals),
            "samples": len(totals),
            "status": "ok" if total_avg is not None else "no_data",
        }
    )

    return {
        "ok": True,
        "engine_id": ENGINE_ID,
        "title": "Factory Metrics",
        "count": len(rows),
        "build_count": len(build_rows),
        "cached_zip_hits": cached,
        "avg_total_e2e_s": total_avg,
        "avg_zip_pack_s": _avg(zip_packs),
        "p50_total_e2e_s": _p50(totals),
        "avg_stages": avg_stages,
        "stage_table": stage_table,
        "stage_ids": list(BUILD_STAGE_IDS),
        "targets_s": {
            "stage1": 180,
            "stage2": 120,
            "stage3": 90,
        },
        "recent": rows[-20:],
    }
