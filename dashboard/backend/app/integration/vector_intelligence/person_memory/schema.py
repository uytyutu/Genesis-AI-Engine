"""Person Memory v1 schema — atoms, active path, lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

MemoryCategory = Literal[
    "goals",
    "projects",
    "preferences",
    "decisions",
    "budget",
    "agreements",
]
LifecycleStatus = Literal[
    "active",
    "confirmed",
    "stale",
    "archived",
    "obsolete",
    "forgotten",
]
PathStage = Literal["idea", "concept", "registered", "operating", "paused"]

V1_CATEGORIES: frozenset[str] = frozenset(
    {"goals", "projects", "preferences", "decisions", "budget", "agreements"}
)


@dataclass
class KnowledgeAtom:
    id: str
    category: MemoryCategory
    key: str
    display: str
    confidence: float = 0.75
    status: LifecycleStatus = "active"
    updated_at: str = ""
    supersedes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "key": self.key,
            "display": self.display,
            "confidence": round(self.confidence, 3),
            "status": self.status,
            "updated_at": self.updated_at,
            "supersedes": self.supersedes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeAtom:
        return cls(
            id=str(data.get("id") or ""),
            category=data.get("category") or "goals",
            key=str(data.get("key") or ""),
            display=str(data.get("display") or ""),
            confidence=float(data.get("confidence") or 0.75),
            status=data.get("status") or "active",
            updated_at=str(data.get("updated_at") or ""),
            supersedes=data.get("supersedes"),
        )


@dataclass
class ActivePath:
    summary: str = ""
    stage: PathStage = "idea"
    confidence: float = 0.0
    updated_at: str = ""
    stage_history: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "stage": self.stage,
            "confidence": round(self.confidence, 3),
            "updated_at": self.updated_at,
            "stage_history": list(self.stage_history)[-12:],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ActivePath:
        if not data:
            return cls()
        return cls(
            summary=str(data.get("summary") or ""),
            stage=data.get("stage") or "idea",
            confidence=float(data.get("confidence") or 0.0),
            updated_at=str(data.get("updated_at") or ""),
            stage_history=list(data.get("stage_history") or []),
        )


@dataclass
class PersonProfile:
    visitor_id: str
    version: str = "person-memory-v1"
    active_path: ActivePath = field(default_factory=ActivePath)
    paths_reserved: None = None
    atoms: list[KnowledgeAtom] = field(default_factory=list)
    reflection_v2: None = None
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "visitor_id": self.visitor_id,
            "version": self.version,
            "active_path": self.active_path.to_dict(),
            "paths_reserved": self.paths_reserved,
            "atoms": [a.to_dict() for a in self.atoms],
            "reflection_v2": self.reflection_v2,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, visitor_id: str) -> PersonProfile:
        atoms = [
            KnowledgeAtom.from_dict(a)
            for a in (data.get("atoms") or [])
            if isinstance(a, dict)
        ]
        return cls(
            visitor_id=visitor_id,
            version=str(data.get("version") or "person-memory-v1"),
            active_path=ActivePath.from_dict(data.get("active_path")),
            paths_reserved=data.get("paths_reserved"),
            atoms=atoms,
            reflection_v2=data.get("reflection_v2"),
            updated_at=str(data.get("updated_at") or ""),
        )

    def active_atoms(self) -> list[KnowledgeAtom]:
        return [
            a
            for a in self.atoms
            if a.status in ("active", "confirmed", "stale")
        ]

    def atom_by_key(self, key: str) -> KnowledgeAtom | None:
        for a in reversed(self.atoms):
            if a.key == key and a.status not in ("obsolete", "forgotten", "archived"):
                return a
        return None
