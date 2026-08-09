"""Asset Manager — library · licensed free · AI slots · cache · quality filter."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

AssetSource = Literal["virtus_library", "licensed_free", "ai_generated", "client_upload", "placeholder"]

# Minimum quality score (0–100) to accept an asset into a deliverable
ASSET_QUALITY_FLOOR = 70


@dataclass(frozen=True)
class AssetPick:
    id: str
    role: str  # hero | gallery | product | background | logo
    source: AssetSource
    path: str
    license: str
    quality_score: float
    niche_fit: float
    cached: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "source": self.source,
            "path": self.path,
            "license": self.license,
            "quality_score": self.quality_score,
            "niche_fit": self.niche_fit,
            "cached": self.cached,
            "meta": dict(self.meta),
        }


# Curated Virtus library stubs — real files can land under factory/assets/library later
_VIRTUS_LIBRARY: list[dict[str, Any]] = [
    {
        "id": "vl_law_hero_01",
        "roles": ["hero", "background"],
        "niches": ["law", "accounting"],
        "path": "assets/library/law_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 92,
        "tags": ["corporate", "minimal", "trust"],
    },
    {
        "id": "vl_restaurant_hero_01",
        "roles": ["hero", "gallery"],
        "niches": ["restaurant"],
        "path": "assets/library/restaurant_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 94,
        "tags": ["warm", "atmosphere", "food"],
    },
    {
        "id": "vl_beauty_hero_01",
        "roles": ["hero", "gallery"],
        "niches": ["beauty"],
        "path": "assets/library/beauty_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 93,
        "tags": ["elegant", "soft", "light"],
    },
    {
        "id": "vl_auto_hero_01",
        "roles": ["hero", "background"],
        "niches": ["auto", "auto_ankauf"],
        "path": "assets/library/auto_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 91,
        "tags": ["dark", "tech", "workshop"],
    },
    {
        "id": "vl_dental_hero_01",
        "roles": ["hero"],
        "niches": ["dental"],
        "path": "assets/library/dental_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 92,
        "tags": ["clean", "trust", "clinic"],
    },
    {
        "id": "vl_fashion_hero_01",
        "roles": ["hero", "banner"],
        "niches": ["fashion"],
        "path": "assets/library/fashion_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 95,
        "tags": ["editorial", "banner"],
    },
    {
        "id": "vl_tech_hero_01",
        "roles": ["hero", "background"],
        "niches": ["computer", "energy"],
        "path": "assets/library/tech_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 93,
        "tags": ["modern", "tech"],
    },
    {
        "id": "vl_generic_hero_01",
        "roles": ["hero", "background"],
        "niches": ["generic", "handwerk", "cleaning"],
        "path": "assets/library/generic_hero_01.jpg",
        "license": "Virtus Core proprietary",
        "quality": 88,
        "tags": ["professional", "neutral"],
    },
]

# Licensed-free catalog (metadata only — URLs resolved at compose when network allowed)
_LICENSED_FREE: list[dict[str, Any]] = [
    {
        "id": "lf_unsplash_architecture",
        "roles": ["hero", "background"],
        "niches": ["realestate", "law"],
        "path": "assets/licensed/architecture.jpg",
        "license": "Unsplash License",
        "quality": 86,
        "tags": ["architecture", "space"],
    },
    {
        "id": "lf_pexels_workshop",
        "roles": ["hero", "gallery"],
        "niches": ["handwerk", "auto"],
        "path": "assets/licensed/workshop.jpg",
        "license": "Pexels License",
        "quality": 84,
        "tags": ["craft", "tools"],
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def score_asset_candidate(
    *,
    role: str,
    niche_id: str,
    width: int | None = None,
    height: int | None = None,
    file_bytes: int | None = None,
    source: AssetSource = "virtus_library",
    base_quality: float = 80.0,
    tags: list[str] | None = None,
) -> float:
    """Heuristic quality — not random. Rewards fit, resolution, sane size."""
    score = float(base_quality)
    # Role aspect expectations
    if width and height and width > 0 and height > 0:
        ratio = width / height
        if role == "hero" and 1.2 <= ratio <= 2.4:
            score += 6
        elif role == "product" and 0.7 <= ratio <= 1.3:
            score += 5
        elif role in {"gallery", "banner"} and 1.0 <= ratio <= 2.0:
            score += 4
        else:
            score -= 8
        if width >= 1600:
            score += 4
        elif width < 800:
            score -= 12
    if file_bytes is not None:
        if file_bytes > 2_500_000:
            score -= 15
        elif file_bytes < 8_000 and source != "placeholder":
            score -= 20
        elif 40_000 <= file_bytes <= 900_000:
            score += 3
    # Source honesty
    if source == "placeholder":
        score = min(score, 55)
    if source == "ai_generated":
        score -= 2  # require slightly higher bar elsewhere
    return max(0.0, min(100.0, round(score, 1)))


class AssetManager:
    """Select / cache / reuse visual materials with a quality floor."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = Path(memory_dir) if memory_dir else None
        self._cache_dir = (
            (self._memory / "visual_intelligence" / "asset_cache")
            if self._memory
            else None
        )
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_index(self) -> Path | None:
        if not self._cache_dir:
            return None
        return self._cache_dir / "index.json"

    def _load_cache(self) -> dict[str, Any]:
        path = self._cache_index()
        if not path or not path.is_file():
            return {"version": 1, "entries": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"version": 1, "entries": {}}
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "entries": {}}

    def _save_cache(self, data: dict[str, Any]) -> None:
        path = self._cache_index()
        if not path:
            return
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def pick(
        self,
        *,
        role: str,
        niche_id: str,
        prefer_ai: bool = False,
        client_path: str | None = None,
        min_quality: float = ASSET_QUALITY_FLOOR,
    ) -> AssetPick:
        """Choose best asset — client upload > cache > Virtus library > licensed free > placeholder."""
        from app.factory.visual_intelligence.style_engine import normalize_niche

        niche = normalize_niche(niche_id)
        role_l = (role or "hero").strip().lower()

        if client_path:
            q = score_asset_candidate(
                role=role_l,
                niche_id=niche,
                source="client_upload",
                base_quality=90,
                width=1800,
                height=1200,
                file_bytes=200_000,
            )
            pick = AssetPick(
                id=f"client-{hashlib.sha1(client_path.encode()).hexdigest()[:8]}",
                role=role_l,
                source="client_upload",
                path=client_path,
                license="Client provided",
                quality_score=q,
                niche_fit=1.0,
                cached=False,
            )
            if q >= min_quality:
                self._remember(pick, niche)
                return pick

        cached = self._from_cache(role_l, niche, min_quality)
        if cached:
            return cached

        candidates: list[AssetPick] = []
        for row in _VIRTUS_LIBRARY:
            roles = set(row.get("roles") or [])
            if role_l not in roles and not (role_l == "background" and "background" in roles):
                if role_l not in roles:
                    continue
            niche_fit = 1.0 if niche in row["niches"] or "generic" in row["niches"] else 0.35
            if niche not in row["niches"] and "generic" not in row["niches"]:
                continue
            q = score_asset_candidate(
                role=role_l,
                niche_id=niche,
                source="virtus_library",
                base_quality=float(row["quality"]),
                width=1920,
                height=1080,
                file_bytes=180_000,
                tags=list(row.get("tags") or []),
            )
            q = round(q * (0.85 + 0.15 * niche_fit), 1)
            candidates.append(
                AssetPick(
                    id=str(row["id"]),
                    role=role_l,
                    source="virtus_library",
                    path=str(row["path"]),
                    license=str(row["license"]),
                    quality_score=q,
                    niche_fit=niche_fit,
                )
            )
        for row in _LICENSED_FREE:
            if role_l not in row["roles"]:
                continue
            niche_fit = 1.0 if niche in row["niches"] else 0.4
            if niche_fit < 0.5:
                continue
            q = score_asset_candidate(
                role=role_l,
                niche_id=niche,
                source="licensed_free",
                base_quality=float(row["quality"]),
                width=1600,
                height=1000,
                file_bytes=220_000,
            )
            candidates.append(
                AssetPick(
                    id=str(row["id"]),
                    role=role_l,
                    source="licensed_free",
                    path=str(row["path"]),
                    license=str(row["license"]),
                    quality_score=q,
                    niche_fit=niche_fit,
                )
            )

        if prefer_ai:
            ai_q = score_asset_candidate(
                role=role_l,
                niche_id=niche,
                source="ai_generated",
                base_quality=82,
                width=1600,
                height=1000,
                file_bytes=160_000,
            )
            candidates.append(
                AssetPick(
                    id=f"ai-{niche}-{role_l}",
                    role=role_l,
                    source="ai_generated",
                    path=f"assets/ai/{niche}_{role_l}.jpg",
                    license="AI-generated under Virtus terms",
                    quality_score=ai_q,
                    niche_fit=0.9,
                    meta={"enabled": False, "note": "Slot ready — generation opt-in"},
                )
            )

        candidates = [c for c in candidates if c.quality_score >= min_quality]
        candidates.sort(key=lambda c: (c.niche_fit, c.quality_score), reverse=True)
        if candidates:
            best = candidates[0]
            self._remember(best, niche)
            return best

        # Controlled placeholder — fails quality floor intentionally for gate visibility
        return AssetPick(
            id=f"ph-{niche}-{role_l}",
            role=role_l,
            source="placeholder",
            path=f"assets/images/{role_l}.jpg",
            license="placeholder",
            quality_score=score_asset_candidate(
                role=role_l, niche_id=niche, source="placeholder", base_quality=50
            ),
            niche_fit=0.2,
            meta={"needs_replacement": True},
        )

    def _cache_key(self, role: str, niche: str) -> str:
        return f"{niche}:{role}"

    def _from_cache(self, role: str, niche: str, min_quality: float) -> AssetPick | None:
        data = self._load_cache()
        entries = data.get("entries") if isinstance(data.get("entries"), dict) else {}
        row = entries.get(self._cache_key(role, niche))
        if not isinstance(row, dict):
            return None
        if float(row.get("quality_score") or 0) < min_quality:
            return None
        return AssetPick(
            id=str(row.get("id") or "cached"),
            role=role,
            source=str(row.get("source") or "virtus_library"),  # type: ignore[arg-type]
            path=str(row.get("path") or ""),
            license=str(row.get("license") or ""),
            quality_score=float(row.get("quality_score") or 0),
            niche_fit=float(row.get("niche_fit") or 0),
            cached=True,
            meta=dict(row.get("meta") or {}),
        )

    def _remember(self, pick: AssetPick, niche: str) -> None:
        if pick.source == "placeholder":
            return
        data = self._load_cache()
        entries = data.setdefault("entries", {})
        if not isinstance(entries, dict):
            entries = {}
            data["entries"] = entries
        entries[self._cache_key(pick.role, niche)] = {
            **pick.as_dict(),
            "cached_at": _now(),
        }
        data["updated_at"] = _now()
        self._save_cache(data)

    def evaluate_html_images(self, html: str) -> list[dict[str, Any]]:
        """Scan img tags for lazy-load + alt — feeds Visual Quality Gate."""
        imgs = re.findall(r"<img\b[^>]*>", html or "", flags=re.I)
        rows = []
        for tag in imgs[:40]:
            has_alt = bool(re.search(r'\balt\s*=\s*("[^"]*"|\'[^\']*\')', tag, re.I))
            lazy = "loading=" in tag.lower() and "lazy" in tag.lower()
            src_m = re.search(r'\bsrc\s*=\s*("([^"]*)"|\'([^\']*)\')', tag, re.I)
            src = (src_m.group(2) or src_m.group(3) or "") if src_m else ""
            rows.append({"src": src, "has_alt": has_alt, "lazy": lazy})
        return rows
