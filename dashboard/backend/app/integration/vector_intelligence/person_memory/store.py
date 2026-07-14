"""Person Memory persistence — file-backed person knowledge."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.integration.vector_intelligence.person_memory.schema import (
    ActivePath,
    KnowledgeAtom,
    LifecycleStatus,
    PersonProfile,
)

_STALE_DAYS = 60


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"kn-{uuid.uuid4().hex[:10]}"


class PersonMemoryStore:
    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "person_knowledge"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, visitor_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", visitor_id)[:64] or "anonymous"
        return self._root / f"{safe}.json"

    def load(self, visitor_id: str) -> PersonProfile:
        path = self._path(visitor_id)
        if not path.is_file():
            return PersonProfile(visitor_id=visitor_id)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                profile = PersonProfile.from_dict(data, visitor_id=visitor_id)
                return self._apply_stale_decay(profile)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass
        return PersonProfile(visitor_id=visitor_id)

    def save(self, profile: PersonProfile) -> None:
        profile.updated_at = _utc_now()
        path = self._path(profile.visitor_id)
        path.write_text(
            json.dumps(profile.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _apply_stale_decay(self, profile: PersonProfile) -> PersonProfile:
        now = datetime.now(timezone.utc)
        changed = False
        for atom in profile.atoms:
            if atom.status not in ("active", "confirmed"):
                continue
            if not atom.updated_at:
                continue
            try:
                updated = datetime.fromisoformat(atom.updated_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            days = (now - updated).total_seconds() / 86400.0
            if days >= _STALE_DAYS:
                atom.status = "stale"
                changed = True
        if changed:
            self.save(profile)
        return profile

    def upsert_atom(
        self,
        profile: PersonProfile,
        *,
        category: str,
        key: str,
        display: str,
        confidence: float,
        status: LifecycleStatus = "active",
    ) -> PersonProfile:
        existing = profile.atom_by_key(key)
        now = _utc_now()
        if existing and existing.display.strip().lower() == display.strip().lower():
            existing.confidence = min(0.98, max(existing.confidence, confidence) + 0.05)
            existing.status = "confirmed" if existing.confidence >= 0.7 else existing.status
            existing.updated_at = now
            return profile

        if existing:
            existing.status = "obsolete"
            existing.updated_at = now

        profile.atoms.append(
            KnowledgeAtom(
                id=_new_id(),
                category=category,  # type: ignore[arg-type]
                key=key,
                display=display,
                confidence=confidence,
                status=status,
                updated_at=now,
                supersedes=existing.id if existing else None,
            )
        )
        profile.atoms = profile.atoms[-80:]
        return profile

    def set_active_path(
        self,
        profile: PersonProfile,
        *,
        summary: str,
        stage: str = "idea",
        confidence: float,
    ) -> PersonProfile:
        now = _utc_now()
        prev = profile.active_path
        if prev.summary and prev.stage != stage:
            profile.active_path.stage_history.append(
                {"from": prev.stage, "to": stage, "at": now}
            )
        profile.active_path = ActivePath(
            summary=summary,
            stage=stage,  # type: ignore[arg-type]
            confidence=confidence,
            updated_at=now,
            stage_history=prev.stage_history,
        )
        return profile

    def archive_path(self, profile: PersonProfile) -> PersonProfile:
        if profile.active_path.summary:
            profile.active_path.stage = "paused"
            profile.active_path.confidence = max(0.3, profile.active_path.confidence - 0.2)
            profile.active_path.updated_at = _utc_now()
        for atom in profile.atoms:
            if atom.status in ("active", "confirmed", "stale") and atom.category in (
                "projects",
                "budget",
                "agreements",
            ):
                atom.status = "archived"
                atom.updated_at = _utc_now()
        return profile

    def forget_key(self, profile: PersonProfile, key: str) -> PersonProfile:
        for atom in profile.atoms:
            if atom.key == key:
                atom.status = "forgotten"
                atom.updated_at = _utc_now()
        return profile
