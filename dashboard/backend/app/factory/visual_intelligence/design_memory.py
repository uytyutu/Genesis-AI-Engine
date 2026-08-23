"""Design Memory — Law №4: Factory must not repeat a company.

Anonymized composition fingerprints. If Similarity ≥ threshold → REBUILD.
Also flags cross-niche “confusable” twins (same bones, different niche label).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.factory.visual_intelligence.ai_design_director import (
    SIMILARITY_REBUILD_THRESHOLD,
    similarity_pct,
)

ENGINE_ID = "design_memory_v1"
MAX_ENTRIES = 500
# Law №4 — stricter than soft creativity nudge
LAW4_SAME_NICHE_THRESHOLD = min(SIMILARITY_REBUILD_THRESHOLD, 88)
LAW4_CROSS_NICHE_THRESHOLD = 94  # almost identical structure across niches = FAIL


def _default_path(memory_dir: Path | None = None) -> Path:
    if memory_dir is not None:
        return Path(memory_dir) / "design_memory.json"
    return Path(__file__).resolve().parents[3] / ".tmp_design_memory" / "design_memory.json"


def load_memory(path: Path | None = None) -> dict[str, Any]:
    p = path or _default_path()
    if not p.is_file():
        return {"engine": ENGINE_ID, "entries": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"engine": ENGINE_ID, "entries": []}


def save_memory(data: dict[str, Any], path: Path | None = None) -> Path:
    p = path or _default_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    entries = list(data.get("entries") or [])[-MAX_ENTRIES:]
    payload = {
        "engine": ENGINE_ID,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": entries,
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def record_composition(
    *,
    fingerprint: str,
    package_id: str,
    niche: str,
    layout_profile: str | None = None,
    hero_layout: str | None = None,
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    """Store anonymized composition (no business name, no copy, no contacts)."""
    path = _default_path(memory_dir)
    data = load_memory(path)
    entry = {
        "fp": fingerprint,
        "package_id": (package_id or "").lower(),
        "niche": (niche or "").lower(),
        "layout_profile": layout_profile,
        "hero_layout": hero_layout,
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    data.setdefault("entries", []).append(entry)
    save_memory(data, path)
    return {"ok": True, "path": str(path), "entry": entry, "count": len(data["entries"])}


def check_similarity(
    fingerprint: str,
    *,
    niche: str | None = None,
    package_id: str | None = None,
    memory_dir: Path | None = None,
    threshold: int | None = None,
) -> dict[str, Any]:
    """Law №4 check — same niche clones + cross-niche confusable twins."""
    thr = int(threshold if threshold is not None else LAW4_SAME_NICHE_THRESHOLD)
    data = load_memory(_default_path(memory_dir))
    best_same = 0
    best_cross = 0
    best_hit: dict[str, Any] | None = None
    cross_hit: dict[str, Any] | None = None
    niche_key = (niche or "").lower()
    pid = (package_id or "").lower()

    for e in data.get("entries") or []:
        if not isinstance(e, dict):
            continue
        if pid and e.get("package_id") == pid and e.get("fp") == fingerprint:
            continue
        score = similarity_pct(fingerprint, str(e.get("fp") or ""))
        e_niche = str(e.get("niche") or "").lower()
        if niche_key and e_niche == niche_key:
            if score > best_same:
                best_same = score
                best_hit = e
        else:
            if score > best_cross:
                best_cross = score
                cross_hit = e

    same_fail = best_same >= thr
    cross_fail = best_cross >= LAW4_CROSS_NICHE_THRESHOLD
    rebuild = same_fail or cross_fail

    return {
        "engine": ENGINE_ID,
        "law": "Law №4 — No Repeated Companies",
        "similarity_pct": best_same,
        "cross_niche_similarity_pct": best_cross,
        "threshold": thr,
        "cross_threshold": LAW4_CROSS_NICHE_THRESHOLD,
        "rebuild_needed": rebuild,
        "law4_violation": rebuild,
        "match": best_hit,
        "cross_match": cross_hit if cross_fail else None,
        "action_ru": (
            "Law №4: перестроить композицию / Hero / типографику / ритм / медиа — "
            "сайты не должны быть взаимозаменяемы"
            if rebuild
            else "OK — достаточно уникально (Law №4)"
        ),
    }


__all__ = [
    "ENGINE_ID",
    "LAW4_CROSS_NICHE_THRESHOLD",
    "LAW4_SAME_NICHE_THRESHOLD",
    "MAX_ENTRIES",
    "check_similarity",
    "load_memory",
    "record_composition",
    "save_memory",
]
