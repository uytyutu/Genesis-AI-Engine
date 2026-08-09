"""Factory Unique Visual Identity — portfolio media fingerprint index.

P0: Media Memory reuse forbidden. Each project gets Visual DNA → Media Brief →
fresh images. This module records fingerprints of generated media so near-
duplicates in the current portfolio can be rejected before export /site.

Does not store image binaries forever — only compact scene descriptors.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HISTORY_FILENAME = "MEDIA_HISTORY.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_fingerprint(
    *,
    project_id: str,
    niche: str = "",
    role: str = "hero",
    composition: str = "",
    palette: list[str] | None = None,
    scene_type: str = "",
    interior: str = "",
    style: str = "",
    angle: str = "",
) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "niche": niche,
        "role": role,
        "composition": composition,
        "palette": list(palette or []),
        "scene_type": scene_type,
        "interior": interior,
        "style": style,
        "angle": angle,
        "recorded_at": _now(),
    }


def history_path(memory_dir: Path) -> Path:
    root = Path(memory_dir) / "factory"
    root.mkdir(parents=True, exist_ok=True)
    return root / HISTORY_FILENAME


def load_history(memory_dir: Path) -> list[dict[str, Any]]:
    path = history_path(memory_dir)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = data.get("entries") if isinstance(data, dict) else None
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def save_history(memory_dir: Path, entries: list[dict[str, Any]]) -> None:
    path = history_path(memory_dir)
    path.write_text(
        json.dumps(
            {"version": 1, "updated_at": _now(), "entries": entries[-500:]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def record_fingerprint(memory_dir: Path, fingerprint: dict[str, Any]) -> dict[str, Any]:
    entries = load_history(memory_dir)
    row = dict(fingerprint)
    row.setdefault("recorded_at", _now())
    entries.append(row)
    save_history(memory_dir, entries)
    return row


def _tokens(value: str) -> set[str]:
    return {t for t in re_split(value.lower()) if len(t) > 2}


def re_split(text: str) -> list[str]:
    import re

    return re.split(r"[^a-z0-9а-яё]+", text or "", flags=re.I)


def similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Cheap descriptor overlap 0..1 — reject when too high in same niche+role."""
    score = 0.0
    weight = 0.0
    for key, w in (
        ("composition", 2.0),
        ("scene_type", 2.0),
        ("interior", 2.0),
        ("style", 1.5),
        ("angle", 1.0),
    ):
        ta, tb = _tokens(str(a.get(key) or "")), _tokens(str(b.get(key) or ""))
        if not ta and not tb:
            continue
        weight += w
        if ta and tb:
            score += w * (len(ta & tb) / max(1, len(ta | tb)))
    pa = {str(x).lower() for x in (a.get("palette") or []) if x}
    pb = {str(x).lower() for x in (b.get("palette") or []) if x}
    if pa or pb:
        weight += 1.5
        if pa and pb:
            score += 1.5 * (len(pa & pb) / max(1, len(pa | pb)))
    if weight <= 0:
        return 0.0
    return score / weight


def find_near_duplicates(
    memory_dir: Path,
    candidate: dict[str, Any],
    *,
    threshold: float = 0.72,
) -> list[dict[str, Any]]:
    """Return portfolio entries too similar to candidate (same niche+role preferred)."""
    niche = str(candidate.get("niche") or "").strip().lower()
    role = str(candidate.get("role") or "hero").strip().lower()
    hits: list[dict[str, Any]] = []
    for row in load_history(memory_dir):
        if str(row.get("project_id") or "") == str(candidate.get("project_id") or ""):
            continue
        if niche and str(row.get("niche") or "").strip().lower() != niche:
            continue
        if role and str(row.get("role") or "").strip().lower() != role:
            continue
        sim = similarity(candidate, row)
        if sim >= threshold:
            hits.append({**row, "similarity": round(sim, 3)})
    return hits


def assert_unique_visual(
    memory_dir: Path,
    candidate: dict[str, Any],
    *,
    threshold: float = 0.72,
) -> dict[str, Any]:
    """
    Gate for Factory image acceptance.
    Returns { ok, reject_reason?, near_duplicates }.
    Caller must regenerate when ok is False.
    """
    dups = find_near_duplicates(memory_dir, candidate, threshold=threshold)
    if dups:
        return {
            "ok": False,
            "reject_reason": "visual_identity_collision",
            "near_duplicates": dups,
            "law": "Unique Visual Identity — Media Memory reuse forbidden",
        }
    return {"ok": True, "near_duplicates": []}
