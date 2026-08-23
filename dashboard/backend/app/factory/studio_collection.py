"""Virtus Core Studio Collection — internal quality etalons (not client templates).

Before export, ask: is this better than our best work — or worse?
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ENGINE_ID = "studio_collection_v1"

# Targets (fill over time by promoting Reality Sprint PASS sites)
COLLECTION_TARGETS: dict[str, int] = {
    "websites": 100,
    "stores": 50,
    "clinics": 20,
    "restaurants": 20,
    "handwerk": 20,
    "lawyers": 20,
}

NICHE_TO_BUCKET: dict[str, str] = {
    "dental": "clinics",
    "psychology": "clinics",
    "beauty": "clinics",
    "restaurant": "restaurants",
    "handwerk": "handwerk",
    "dachreinigung": "handwerk",
    "gartenpflege": "handwerk",
    "cleaning": "handwerk",
    "zaunbau": "handwerk",
    "law": "lawyers",
    "accounting": "lawyers",
    "fashion": "stores",
    "furniture": "stores",
    "computer": "stores",
}


@dataclass(frozen=True)
class CollectionEntry:
    id: str
    bucket: str
    niche_id: str
    fingerprint: str
    overall_score: int
    notes: str = ""
    product_ref: str = ""
    at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _default_path(memory_dir: Path | None = None) -> Path:
    if memory_dir is not None:
        return Path(memory_dir) / "studio_collection.json"
    return (
        Path(__file__).resolve().parents[2] / ".tmp_studio_collection" / "studio_collection.json"
    )


def load_collection(path: Path | None = None) -> dict[str, Any]:
    p = path or _default_path()
    if not p.is_file():
        return {
            "engine": ENGINE_ID,
            "targets": dict(COLLECTION_TARGETS),
            "entries": [],
        }
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("targets", dict(COLLECTION_TARGETS))
            data.setdefault("entries", [])
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"engine": ENGINE_ID, "targets": dict(COLLECTION_TARGETS), "entries": []}


def save_collection(data: dict[str, Any], path: Path | None = None) -> Path:
    p = path or _default_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "engine": ENGINE_ID,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "targets": data.get("targets") or dict(COLLECTION_TARGETS),
        "entries": list(data.get("entries") or [])[-400:],
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def bucket_for_niche(niche_id: str, *, is_store: bool = False) -> str:
    if is_store:
        return "stores"
    return NICHE_TO_BUCKET.get((niche_id or "").lower(), "websites")


def promote_to_collection(
    *,
    niche_id: str,
    fingerprint: str,
    overall_score: int,
    notes: str = "",
    product_ref: str = "",
    is_store: bool = False,
    memory_dir: Path | None = None,
    min_score: int = 80,
) -> dict[str, Any]:
    """Promote only strong Reality PASS candidates into the Studio Collection."""
    if overall_score < min_score:
        return {"ok": False, "reason": "score_below_collection_bar", "min_score": min_score}
    path = _default_path(memory_dir)
    data = load_collection(path)
    bucket = bucket_for_niche(niche_id, is_store=is_store)
    entry = CollectionEntry(
        id=f"{bucket}-{fingerprint[:12]}",
        bucket=bucket,
        niche_id=(niche_id or "").lower(),
        fingerprint=fingerprint,
        overall_score=int(overall_score),
        notes=notes[:400],
        product_ref=product_ref,
        at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    # Replace weaker same-fingerprint
    entries = [
        e
        for e in (data.get("entries") or [])
        if not (isinstance(e, dict) and e.get("fingerprint") == fingerprint)
    ]
    entries.append(entry.as_dict())
    data["entries"] = entries
    save_collection(data, path)
    return {"ok": True, "entry": entry.as_dict(), "path": str(path)}


def compare_to_collection(
    *,
    niche_id: str,
    fingerprint: str,
    overall_score: int,
    is_store: bool = False,
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    """Ask: better than our best — or worse?

    Empty collection → advisory only (cannot block first works).
    """
    from app.factory.visual_intelligence.ai_design_director import similarity_pct

    data = load_collection(_default_path(memory_dir))
    bucket = bucket_for_niche(niche_id, is_store=is_store)
    peers = [
        e
        for e in (data.get("entries") or [])
        if isinstance(e, dict) and e.get("bucket") == bucket
    ]
    if not peers:
        return {
            "engine": ENGINE_ID,
            "bucket": bucket,
            "peers": 0,
            "verdict": "no_etalon_yet",
            "export_allowed": True,
            "message": "Studio Collection empty for this bucket — build etalons via Reality PASS.",
            "law": "Better than our best — or do not export",
        }

    best = max(int(e.get("overall_score") or 0) for e in peers)
    # Also flag near-clones of etalons (Law №4 vs collection)
    clone_hit = None
    clone_score = 0
    for e in peers:
        sc = similarity_pct(fingerprint, str(e.get("fp") or e.get("fingerprint") or ""))
        if sc > clone_score:
            clone_score = sc
            clone_hit = e

    better = int(overall_score) >= best
    clone_block = clone_score >= 90
    export_ok = better and not clone_block

    if clone_block:
        verdict = "worse_clone_of_etalon"
    elif better:
        verdict = "meets_or_beats_best"
    else:
        verdict = "worse_than_best"

    return {
        "engine": ENGINE_ID,
        "bucket": bucket,
        "peers": len(peers),
        "best_score": best,
        "this_score": int(overall_score),
        "clone_similarity_pct": clone_score,
        "clone_hit": clone_hit,
        "verdict": verdict,
        "export_allowed": export_ok,
        "message": (
            "Clone of Studio Collection etalon — REBUILD"
            if clone_block
            else (
                "Meets or beats Studio Collection best"
                if better
                else f"Worse than Studio Collection best ({best}) — do not export"
            )
        ),
        "law": "Better than our best — or do not export",
    }


def collection_status(memory_dir: Path | None = None) -> dict[str, Any]:
    data = load_collection(_default_path(memory_dir))
    counts: dict[str, int] = {k: 0 for k in COLLECTION_TARGETS}
    for e in data.get("entries") or []:
        if isinstance(e, dict):
            b = str(e.get("bucket") or "")
            if b in counts:
                counts[b] += 1
    return {
        "engine": ENGINE_ID,
        "targets": dict(COLLECTION_TARGETS),
        "counts": counts,
        "total": sum(counts.values()),
        "entries": len(data.get("entries") or []),
    }


__all__ = [
    "COLLECTION_TARGETS",
    "CollectionEntry",
    "bucket_for_niche",
    "collection_status",
    "compare_to_collection",
    "load_collection",
    "promote_to_collection",
    "save_collection",
]
