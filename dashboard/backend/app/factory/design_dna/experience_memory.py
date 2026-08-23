"""Experience Memory — learn from accepted Digital Experiences.

Stores best Heroes, compositions, type pairs, palettes, CTAs, transitions
that the product owner consistently accepts — then biases future principles
(never literal clones).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MEMORY_PATH = Path("dashboard/backend/data/experience_memory.json")


@dataclass
class ExperienceRecord:
    """One accepted (or strongly tasted) experience — principles, not a site dump."""

    niche_id: str
    package_id: str
    composition_id: str
    hero_layout: str
    typography_pair: str
    studio_approach: str
    palette_family: str
    why_hero_exists: str
    scene_sequence: list[str] = field(default_factory=list)
    taste_overall: float = 0.0
    owner_accepted: bool = False
    notes: str = ""
    recorded_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExperienceMemory:
    version: str = "experience_memory_v1"
    law: str = (
        "Law #1: each new project must not be worse than the previous best. "
        "Reuse principles — never copy literally."
    )
    records: list[ExperienceRecord] = field(default_factory=list)
    best_overall_by_niche: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "law": self.law,
            "records": [r.as_dict() for r in self.records],
            "best_overall_by_niche": dict(self.best_overall_by_niche),
        }


def _default_path() -> Path:
    # .../dashboard/backend/app/factory/design_dna/this.py → backend/data/
    backend = Path(__file__).resolve().parents[3]
    return backend / "data" / "experience_memory.json"


def load_memory(path: Path | None = None) -> ExperienceMemory:
    p = path or _default_path()
    if not p.is_file():
        return ExperienceMemory()
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ExperienceMemory()
    records: list[ExperienceRecord] = []
    for row in raw.get("records") or []:
        if not isinstance(row, dict):
            continue
        records.append(
            ExperienceRecord(
                niche_id=str(row.get("niche_id") or "generic"),
                package_id=str(row.get("package_id") or "business"),
                composition_id=str(row.get("composition_id") or ""),
                hero_layout=str(row.get("hero_layout") or ""),
                typography_pair=str(row.get("typography_pair") or ""),
                studio_approach=str(row.get("studio_approach") or ""),
                palette_family=str(row.get("palette_family") or ""),
                why_hero_exists=str(row.get("why_hero_exists") or ""),
                scene_sequence=list(row.get("scene_sequence") or []),
                taste_overall=float(row.get("taste_overall") or 0),
                owner_accepted=bool(row.get("owner_accepted")),
                notes=str(row.get("notes") or ""),
                recorded_at=str(row.get("recorded_at") or ""),
            )
        )
    best = {str(k): float(v) for k, v in (raw.get("best_overall_by_niche") or {}).items()}
    return ExperienceMemory(records=records, best_overall_by_niche=best)


def save_memory(memory: ExperienceMemory, path: Path | None = None) -> Path:
    p = path or _default_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(memory.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def prior_best_overall(niche_id: str, *, path: Path | None = None) -> float | None:
    """Law #1 hard bar — owner-accepted experiences only.

    Auto-taste memory may still bias principles, but must not invent a phantom
    «prior best» that freezes marketing HTML into identity-preview decks and
    breaks production / client-delivery exports (delivery_truth).
    """
    mem = load_memory(path)
    key = (niche_id or "generic").strip().lower()
    accepted = [
        float(r.taste_overall)
        for r in mem.records
        if (r.niche_id or "").strip().lower() == key
        and r.owner_accepted
        and float(r.taste_overall) > 0
    ]
    if accepted:
        return max(accepted)
    # Legacy map only if it came from an owner-accepted record for this niche
    if any(
        (r.niche_id or "").strip().lower() == key and r.owner_accepted
        for r in mem.records
    ) and key in mem.best_overall_by_niche:
        return float(mem.best_overall_by_niche[key])
    return None


def remember_experience(
    record: ExperienceRecord,
    *,
    path: Path | None = None,
) -> ExperienceMemory:
    """Append experience; ratchet niche best only on owner-accepted PASS."""
    mem = load_memory(path)
    if not record.recorded_at:
        record.recorded_at = datetime.now(timezone.utc).isoformat()
    mem.records.append(record)
    # Keep memory bounded
    if len(mem.records) > 200:
        mem.records = mem.records[-200:]
    key = record.niche_id
    if record.owner_accepted:
        prev = mem.best_overall_by_niche.get(key, 0.0)
        mem.best_overall_by_niche[key] = max(prev, record.taste_overall)
    save_memory(mem, path)
    return mem


def bias_from_memory(niche_id: str, *, path: Path | None = None) -> dict[str, Any]:
    """Return principle biases from accepted/strong memories — not clones."""
    mem = load_memory(path)
    key = (niche_id or "generic").strip().lower()
    rows = [r for r in mem.records if r.niche_id == key and (r.owner_accepted or r.taste_overall >= 70)]
    if not rows:
        rows = [r for r in mem.records if r.taste_overall >= 75][-5:]
    if not rows:
        return {"compositions": [], "approaches": [], "typography": [], "heroes": []}

    def top_counts(attr: str, n: int = 3) -> list[str]:
        counts: dict[str, int] = {}
        for r in rows:
            val = str(getattr(r, attr, "") or "")
            if not val:
                continue
            counts[val] = counts.get(val, 0) + 1
        return [k for k, _ in sorted(counts.items(), key=lambda x: -x[1])[:n]]

    return {
        "compositions": top_counts("composition_id"),
        "approaches": top_counts("studio_approach"),
        "typography": top_counts("typography_pair"),
        "heroes": top_counts("hero_layout"),
        "prior_best_overall": mem.best_overall_by_niche.get(key),
        "rule": "Bias principles from memory — never copy a prior site literally",
    }
