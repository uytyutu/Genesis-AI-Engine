"""Composable capability results — outputs other capabilities can chain on."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.execution.models import ExecutionStatus


@dataclass
class CapabilityArtifact:
    """Single produced artifact (file, bundle, or URL)."""

    id: str
    kind: Literal["file", "bundle", "url"]
    path: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityResult:
    """
    Standard composable output for execution capabilities.

    Future agents chain on workspace_id + artifact_id without rewriting upstream logic.
    """

    workspace_id: str
    artifact_id: str
    files: list[str] = field(default_factory=list)
    artifacts: list[CapabilityArtifact] = field(default_factory=list)
    preview_url: str | None = None
    logs: list[str] = field(default_factory=list)
    status: ExecutionStatus = "completed"
    capability_id: str = ""
    reused_capabilities: list[str] = field(default_factory=list)
    reuse_score: int = 0
    source_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "artifact_id": self.artifact_id,
            "files": list(self.files),
            "artifacts": [a.to_dict() for a in self.artifacts],
            "preview_url": self.preview_url,
            "logs": list(self.logs),
            "status": self.status,
            "capability_id": self.capability_id,
            "reused_capabilities": list(self.reused_capabilities),
            "reuse_score": self.reuse_score,
            "source_files": list(self.source_files),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityResult:
        artifacts = [
            CapabilityArtifact(**a) if isinstance(a, dict) else a
            for a in data.get("artifacts") or []
        ]
        return cls(
            workspace_id=str(data.get("workspace_id") or ""),
            artifact_id=str(data.get("artifact_id") or ""),
            files=list(data.get("files") or []),
            artifacts=artifacts,
            preview_url=data.get("preview_url"),
            logs=list(data.get("logs") or []),
            status=data.get("status") or "completed",
            capability_id=str(data.get("capability_id") or ""),
        )
