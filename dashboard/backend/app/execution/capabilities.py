"""Executable capability registry — catalog + optional executors (Phase 1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Protocol

from app.execution.models import CapabilityAvailability, PermissionKind

CapabilityExecutor = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
CapabilityRollback = Callable[[dict[str, Any], dict[str, Any]], None]

EXECUTION_LAYER_VERSION = "execution-phase2-site"


@dataclass(frozen=True)
class CapabilityDefinition:
    id: str
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    permissions: frozenset[str]
    availability: CapabilityAvailability
    timeout_sec: float
    supports_rollback: bool
    phase: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CapabilityExecutorProtocol(Protocol):
    def execute(self, inputs: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]: ...

    def rollback(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None: ...


def _schema_object(props: dict[str, str], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {k: {"type": v} for k, v in props.items()},
        "required": required or list(props.keys()),
    }


# Phase 1 catalog — metadata only; executors registered separately when Phase 2 ships.
_CATALOG: tuple[CapabilityDefinition, ...] = (
    CapabilityDefinition(
        id="analyze_pdf",
        name="Analyze PDF",
        description="Parse and analyze PDF documents",
        input_schema=_schema_object({"path": "string", "goal": "string"}),
        output_schema=_schema_object({"summary": "string", "sections": "array"}),
        permissions=frozenset({"read", "filesystem"}),
        availability="planned",
        timeout_sec=120.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="analyze_docx",
        name="Analyze DOCX",
        description="Parse Word documents",
        input_schema=_schema_object({"path": "string"}),
        output_schema=_schema_object({"text": "string"}),
        permissions=frozenset({"read", "filesystem"}),
        availability="planned",
        timeout_sec=90.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="analyze_image",
        name="Analyze Image",
        description="Vision analysis of images",
        input_schema=_schema_object({"path": "string", "prompt": "string"}),
        output_schema=_schema_object({"description": "string"}),
        permissions=frozenset({"read", "filesystem", "external_api"}),
        availability="planned",
        timeout_sec=60.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="analyze_audio",
        name="Analyze Audio",
        description="Transcribe and analyze audio",
        input_schema=_schema_object({"path": "string"}),
        output_schema=_schema_object({"transcript": "string"}),
        permissions=frozenset({"read", "filesystem", "external_api"}),
        availability="planned",
        timeout_sec=180.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="generate_site",
        name="Generate Site",
        description="Build site project from structured brief",
        input_schema=_schema_object({"brief": "string", "workspace_id": "string"}),
        output_schema=_schema_object(
            {
                "workspace_id": "string",
                "artifact_id": "string",
                "files": "array",
                "artifacts": "array",
                "preview_url": "string",
                "logs": "array",
                "status": "string",
            },
            ["workspace_id", "artifact_id", "files"],
        ),
        permissions=frozenset({"write", "filesystem", "network"}),
        availability="planned",
        timeout_sec=300.0,
        supports_rollback=True,
        phase=3,
    ),
    CapabilityDefinition(
        id="generate_app",
        name="Generate App",
        description="Scaffold application codebase",
        input_schema=_schema_object({"spec": "string", "workspace_id": "string"}),
        output_schema=_schema_object({"artifact_id": "string"}),
        permissions=frozenset({"write", "filesystem", "terminal"}),
        availability="planned",
        timeout_sec=600.0,
        supports_rollback=True,
        phase=3,
    ),
    CapabilityDefinition(
        id="generate_api",
        name="Generate API",
        description="Generate API layer from schema",
        input_schema=_schema_object({"schema": "object", "workspace_id": "string"}),
        output_schema=_schema_object({"artifact_id": "string"}),
        permissions=frozenset({"write", "filesystem"}),
        availability="planned",
        timeout_sec=300.0,
        supports_rollback=True,
        phase=3,
    ),
    CapabilityDefinition(
        id="generate_database",
        name="Generate Database",
        description="Create database schema and migrations",
        input_schema=_schema_object({"model": "object", "workspace_id": "string"}),
        output_schema=_schema_object({"artifact_id": "string"}),
        permissions=frozenset({"write", "filesystem"}),
        availability="planned",
        timeout_sec=180.0,
        supports_rollback=True,
        phase=3,
    ),
    CapabilityDefinition(
        id="generate_presentation",
        name="Generate Presentation",
        description="Build slide deck from outline",
        input_schema=_schema_object({"outline": "string"}),
        output_schema=_schema_object({"artifact_id": "string"}),
        permissions=frozenset({"write", "filesystem"}),
        availability="planned",
        timeout_sec=120.0,
        supports_rollback=False,
        phase=4,
    ),
    CapabilityDefinition(
        id="generate_excel",
        name="Generate Excel",
        description="Build spreadsheet from data model",
        input_schema=_schema_object({"model": "object"}),
        output_schema=_schema_object({"artifact_id": "string"}),
        permissions=frozenset({"write", "filesystem"}),
        availability="planned",
        timeout_sec=90.0,
        supports_rollback=False,
        phase=4,
    ),
    CapabilityDefinition(
        id="browser_search",
        name="Browser Search",
        description="Search the web via browser agent",
        input_schema=_schema_object({"query": "string"}),
        output_schema=_schema_object({"results": "array"}),
        permissions=frozenset({"network", "external_api"}),
        availability="planned",
        timeout_sec=45.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="browser_navigation",
        name="Browser Navigation",
        description="Navigate browser to URL and extract content",
        input_schema=_schema_object({"url": "string"}),
        output_schema=_schema_object({"content": "string"}),
        permissions=frozenset({"network", "external_api"}),
        availability="planned",
        timeout_sec=60.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="filesystem_read",
        name="Filesystem Read",
        description="Read file from workspace",
        input_schema=_schema_object({"path": "string", "workspace_id": "string"}),
        output_schema=_schema_object({"content": "string"}),
        permissions=frozenset({"read", "filesystem"}),
        availability="planned",
        timeout_sec=30.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="filesystem_write",
        name="Filesystem Write",
        description="Write file into workspace",
        input_schema=_schema_object({"path": "string", "content": "string", "workspace_id": "string"}),
        output_schema=_schema_object({"path": "string", "bytes": "integer"}),
        permissions=frozenset({"write", "filesystem"}),
        availability="planned",
        timeout_sec=30.0,
        supports_rollback=True,
        phase=2,
    ),
    CapabilityDefinition(
        id="git_commit",
        name="Git Commit",
        description="Commit workspace changes",
        input_schema=_schema_object({"message": "string", "workspace_id": "string"}),
        output_schema=_schema_object({"commit": "string"}),
        permissions=frozenset({"write", "filesystem", "terminal"}),
        availability="planned",
        timeout_sec=60.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="git_branch",
        name="Git Branch",
        description="Create or switch git branch",
        input_schema=_schema_object({"branch": "string", "workspace_id": "string"}),
        output_schema=_schema_object({"branch": "string"}),
        permissions=frozenset({"write", "filesystem", "terminal"}),
        availability="planned",
        timeout_sec=30.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="docker_build",
        name="Docker Build",
        description="Build container image for workspace project",
        input_schema=_schema_object({"workspace_id": "string", "tag": "string"}),
        output_schema=_schema_object({"image_id": "string"}),
        permissions=frozenset({"terminal", "filesystem", "deployment"}),
        availability="planned",
        timeout_sec=600.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="docker_run",
        name="Docker Run",
        description="Run container from workspace image",
        input_schema=_schema_object({"image_id": "string", "workspace_id": "string"}),
        output_schema=_schema_object({"container_id": "string"}),
        permissions=frozenset({"terminal", "deployment", "network"}),
        availability="planned",
        timeout_sec=120.0,
        supports_rollback=True,
        phase=2,
    ),
    CapabilityDefinition(
        id="terminal_command",
        name="Terminal Command",
        description="Run shell command in workspace sandbox",
        input_schema=_schema_object({"command": "string", "workspace_id": "string"}),
        output_schema=_schema_object({"exit_code": "integer", "stdout": "string", "stderr": "string"}),
        permissions=frozenset({"terminal", "filesystem"}),
        availability="planned",
        timeout_sec=120.0,
        supports_rollback=False,
        phase=2,
    ),
    CapabilityDefinition(
        id="deployment",
        name="Deployment",
        description="Deploy workspace artifact to target environment",
        input_schema=_schema_object({"artifact_id": "string", "target": "string"}),
        output_schema=_schema_object({"url": "string", "deployment_id": "string"}),
        permissions=frozenset({"deployment", "network", "external_api"}),
        availability="planned",
        timeout_sec=300.0,
        supports_rollback=True,
        phase=2,
    ),
    CapabilityDefinition(
        id="email_send",
        name="Send Email",
        description="Send email via configured provider",
        input_schema=_schema_object({"to": "string", "subject": "string", "body": "string"}),
        output_schema=_schema_object({"message_id": "string"}),
        permissions=frozenset({"network", "external_api"}),
        availability="planned",
        timeout_sec=30.0,
        supports_rollback=False,
        phase=4,
    ),
    CapabilityDefinition(
        id="calendar",
        name="Calendar",
        description="Create or update calendar event",
        input_schema=_schema_object({"title": "string", "start": "string", "end": "string"}),
        output_schema=_schema_object({"event_id": "string"}),
        permissions=frozenset({"network", "external_api", "write"}),
        availability="planned",
        timeout_sec=30.0,
        supports_rollback=False,
        phase=4,
    ),
    CapabilityDefinition(
        id="task_queue",
        name="Task Queue",
        description="Enqueue background task for async execution",
        input_schema=_schema_object({"task_type": "string", "payload": "object"}),
        output_schema=_schema_object({"task_id": "string"}),
        permissions=frozenset({"write"}),
        availability="planned",
        timeout_sec=15.0,
        supports_rollback=False,
        phase=1,
    ),
)


class ExecutionCapabilityRegistry:
    """Executable capability catalog — separate from Foundation F1 read-only snapshot."""

    def __init__(self) -> None:
        self._catalog: dict[str, CapabilityDefinition] = {c.id: c for c in _CATALOG}
        self._executors: dict[str, CapabilityExecutorProtocol] = {}

    def list_capabilities(self) -> list[CapabilityDefinition]:
        return list(self._catalog.values())

    def get(self, capability_id: str) -> CapabilityDefinition | None:
        return self._catalog.get(capability_id)

    def is_executable(self, capability_id: str) -> bool:
        cap = self._catalog.get(capability_id)
        return cap is not None and cap.availability == "available" and capability_id in self._executors

    def register_executor(self, capability_id: str, executor: CapabilityExecutorProtocol) -> None:
        from dataclasses import replace

        if capability_id not in self._catalog:
            raise KeyError(f"Unknown capability: {capability_id}")
        self._catalog[capability_id] = replace(
            self._catalog[capability_id], availability="available"
        )
        self._executors[capability_id] = executor

    def get_executor(self, capability_id: str) -> CapabilityExecutorProtocol | None:
        return self._executors.get(capability_id)

    def snapshot(self) -> dict[str, Any]:
        return {
            "version": EXECUTION_LAYER_VERSION,
            "capabilities": [
                {
                    **c.to_dict(),
                    "execution_status": "ready" if self.is_executable(c.id) else "not_implemented",
                }
                for c in self._catalog.values()
            ],
        }
