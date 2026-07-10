"""Wire Execution Layer to public chat — one capability at a time (top-down)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.execution.capabilities import ExecutionCapabilityRegistry
from app.execution.executors.filesystem import FilesystemReadExecutor, FilesystemWriteExecutor
from app.execution.log_store import ExecutionLogStore
from app.execution.manager import ExecutionManager
from app.execution.models import ExecutionPlan, ExecutionStep, PermissionGrant, VerificationRule
from app.execution.workspace import ExecutionWorkspaceStore

_REGISTRY: ExecutionCapabilityRegistry | None = None

_README_GOAL = re.compile(
    r"(?:создай|создать|напиши|create|write)\s+(?:файл\s+)?readme\b",
    re.IGNORECASE,
)
_FILE_GOAL = re.compile(
    r"(?:создай|создать|напиши|create|write)\s+(?:файл\s+)?(?P<name>[\w.\-]+\.[a-zA-Z0-9]+)",
    re.IGNORECASE,
)
_CONTENT_AFTER = re.compile(r"(?:с\s+текстом|с\s+содержимым|content|:)\s*(.+)$", re.IGNORECASE | re.DOTALL)


def get_execution_registry(memory_dir: Path) -> ExecutionCapabilityRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        reg = ExecutionCapabilityRegistry()
        ws = ExecutionWorkspaceStore(memory_dir)
        reg.register_executor("filesystem_write", FilesystemWriteExecutor(ws))
        reg.register_executor("filesystem_read", FilesystemReadExecutor(ws))
        _REGISTRY = reg
    return _REGISTRY


def _visitor_map_path(memory_dir: Path) -> Path:
    return memory_dir / "execution" / "visitor_workspaces.json"


def _workspace_for_visitor(memory_dir: Path, visitor_id: str) -> str:
    path = _visitor_map_path(memory_dir)
    mapping: dict[str, str] = {}
    if path.is_file():
        try:
            mapping = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            mapping = {}
    if visitor_id in mapping and ExecutionWorkspaceStore(memory_dir).get(mapping[visitor_id]):
        return mapping[visitor_id]
    ws = ExecutionWorkspaceStore(memory_dir).create(
        owner_id=visitor_id[:64] or "anonymous",
        title="Vector Workspace",
    )
    mapping[visitor_id] = ws.workspace_id
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws.workspace_id


def _parse_file_request(goal: str) -> tuple[str, str] | None:
    g = goal.strip()
    if _README_GOAL.search(g):
        content = _default_readme(g)
        m = _CONTENT_AFTER.search(g)
        if m:
            content = m.group(1).strip()
        return "README.md", content
    m = _FILE_GOAL.search(g)
    if m:
        name = m.group("name")
        content = ""
        cm = _CONTENT_AFTER.search(g)
        if cm:
            content = cm.group(1).strip()
        return name, content
    return None


def _default_readme(goal: str) -> str:
    return f"""# README

Создано Vector (Virtus Core).

## Запрос
{goal.strip()}

## Дальше
- Добавьте описание проекта
- Уточните структуру сайта или продукта в чате
"""


def try_user_execution(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    """
  Run a single real capability when the user goal matches.
  Returns public chat dict or None (fall through to Brain).
    """
    parsed = _parse_file_request(goal)
    if not parsed:
        return None

    filename, content = parsed
    workspace_id = _workspace_for_visitor(memory_dir, visitor_id)
    registry = get_execution_registry(memory_dir)
    ws_store = ExecutionWorkspaceStore(memory_dir)
    logs = ExecutionLogStore(memory_dir)
    mgr = ExecutionManager(registry=registry, workspace_store=ws_store, log_store=logs)

    plan = ExecutionPlan(
        plan_id="",
        goal=goal.strip(),
        workspace_id=workspace_id,
        steps=(
            ExecutionStep(
                id="step-write",
                capability_id="filesystem_write",
                title=f"Write {filename}",
                inputs={"path": filename, "content": content, "workspace_id": workspace_id},
                verification=VerificationRule(
                    id="vr-write",
                    description="file written",
                    required_output_keys=("path", "bytes"),
                ),
            ),
        ),
        required_permissions=frozenset({"write", "filesystem"}),
    )

    grant = PermissionGrant(
        kinds=frozenset({"read", "write", "filesystem"}),
        workspace_id=workspace_id,
        actor=visitor_id,
    )
    result = mgr.run(plan, grant)
    if result.status != "completed":
        err = result.error or (result.steps[0].error if result.steps else "execution failed")
        return {
            "answer": f"Не удалось создать файл: {err}",
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": None,
            "cta_label": None,
            "context": {"execution": result.to_dict()},
        }

    step = result.steps[0]
    rel = step.outputs.get("path", filename)
    nbytes = step.outputs.get("bytes", 0)
    answer = (
        "✓ Создаю файл в Workspace...\n"
        "✓ Готово.\n\n"
        f"**{rel}** создан ({nbytes} байт).\n\n"
        f"Путь в workspace: `files/{rel}`"
    )
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": None,
        "cta_label": None,
        "context": {
            "execution": result.to_dict(),
            "workspace_id": workspace_id,
            "artifact_path": f"files/{rel}",
        },
    }


def list_user_capabilities(memory_dir: Path) -> list[dict[str, str]]:
    """Product KPI — what Vector can actually do today."""
    reg = get_execution_registry(memory_dir)
    ready = [c for c in reg.list_capabilities() if reg.is_executable(c.id)]
    labels = {
        "filesystem_write": "создавать файлы в Workspace",
        "filesystem_read": "читать файлы из Workspace",
    }
    return [{"id": c.id, "label": labels.get(c.id, c.name)} for c in ready]
