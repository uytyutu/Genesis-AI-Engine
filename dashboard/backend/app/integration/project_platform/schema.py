"""Customer project schema — lifecycle, sections, timeline, versions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ProjectMode = Literal["conversation", "project"]
LifecyclePhase = Literal[
    "dialog",
    "concept",
    "collaboration",
    "approval",
    "choice",
    "handoff",
    "subscription",
]

SECTION_WEBSITE = "website"
SECTION_BUSINESS_PLAN = "business_plan"
SECTION_DOCUMENTS = "documents"
SECTION_FILES = "files"
SECTION_HISTORY = "history"
SECTION_TEAM = "team"

PROJECT_SECTIONS: tuple[str, ...] = (
    SECTION_WEBSITE,
    SECTION_BUSINESS_PLAN,
    SECTION_DOCUMENTS,
    SECTION_FILES,
    SECTION_HISTORY,
    SECTION_TEAM,
)

SECTION_LABELS: dict[str, dict[str, str]] = {
    SECTION_WEBSITE: {"ru": "Сайт", "de": "Website"},
    SECTION_BUSINESS_PLAN: {"ru": "Бизнес-план", "de": "Businessplan"},
    SECTION_DOCUMENTS: {"ru": "Документы", "de": "Dokumente"},
    SECTION_FILES: {"ru": "Файлы", "de": "Dateien"},
    SECTION_HISTORY: {"ru": "История", "de": "Verlauf"},
    SECTION_TEAM: {"ru": "Команда", "de": "Team"},
}

ArtifactKind = Literal[
    "preview",
    "zip",
    "source",
    "image",
    "pdf",
    "instructions",
    "report",
    "file",
]

TimelineEventType = Literal[
    "created",
    "analysis",
    "concept",
    "version",
    "approval",
    "generation",
    "handoff",
    "note",
]


@dataclass
class ProjectArtifact:
    id: str
    kind: ArtifactKind
    label: str
    href: str | None = None
    section: str = SECTION_FILES
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectVersion:
    version: int
    label: str
    created_at: str
    summary: str = ""
    artifacts: list[ProjectArtifact] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "label": self.label,
            "created_at": self.created_at,
            "summary": self.summary,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }


@dataclass
class TimelineEvent:
    id: str
    type: TimelineEventType
    label: str
    at: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectRecord:
    project_id: str
    workspace_id: str
    visitor_id: str
    title: str
    service_id: str | None = None
    mode: ProjectMode = "conversation"
    lifecycle_phase: LifecyclePhase = "dialog"
    active_section: str = SECTION_WEBSITE
    created_at: str = ""
    updated_at: str = ""
    next_step_hint: str = ""
    description: str = ""
    market: str = ""
    timeline: list[TimelineEvent] = field(default_factory=list)
    versions: list[ProjectVersion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "visitor_id": self.visitor_id,
            "title": self.title,
            "service_id": self.service_id,
            "mode": self.mode,
            "lifecycle_phase": self.lifecycle_phase,
            "active_section": self.active_section,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "next_step_hint": self.next_step_hint,
            "description": self.description,
            "market": self.market,
            "sections": section_summary(self),
            "timeline": [e.to_dict() for e in self.timeline],
            "versions": [v.to_dict() for v in self.versions],
        }


def section_summary(project: ProjectRecord) -> list[dict[str, Any]]:
    counts: dict[str, int] = {s: 0 for s in PROJECT_SECTIONS}
    for ver in project.versions:
        for art in ver.artifacts:
            sec = art.section if art.section in counts else SECTION_FILES
            counts[sec] = counts.get(sec, 0) + 1
    out: list[dict[str, Any]] = []
    for sid in PROJECT_SECTIONS:
        if sid == SECTION_TEAM:
            out.append({
                "id": sid,
                "label_ru": SECTION_LABELS[sid]["ru"],
                "artifact_count": counts.get(sid, 0),
                "status": "horizon",
            })
        else:
            out.append({
                "id": sid,
                "label_ru": SECTION_LABELS[sid]["ru"],
                "artifact_count": counts.get(sid, 0),
                "active": project.active_section == sid,
            })
    return out
