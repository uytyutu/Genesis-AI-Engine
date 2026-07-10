"""Execution Layer — Phase 1 tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.execution.capabilities import ExecutionCapabilityRegistry
from app.execution.manager import ExecutionManager
from app.execution.models import PermissionGrant
from app.execution.permissions import PermissionDenied
from app.execution.planner import TaskPlannerV2
from app.execution.log_store import ExecutionLogStore
from app.execution.workspace import ExecutionWorkspaceStore


class _EchoExecutor:
    def execute(self, inputs: dict, context: dict) -> dict:
        return {"task_id": "task-1", "echo": inputs.get("payload", {})}

    def rollback(self, inputs: dict, outputs: dict) -> None:
        pass


@pytest.fixture
def memory_tmp(tmp_path: Path) -> Path:
    mem = tmp_path / "memory"
    mem.mkdir()
    return mem


def test_capability_catalog_lists_phase2_tools():
    reg = ExecutionCapabilityRegistry()
    snap = reg.snapshot()
    ids = {c["id"] for c in snap["capabilities"]}
    assert "generate_site" in ids
    assert "analyze_pdf" in ids
    assert all(c["execution_status"] == "not_implemented" for c in snap["capabilities"])


def test_planner_site_goal_produces_three_steps(memory_tmp: Path):
    ws = ExecutionWorkspaceStore(memory_tmp).create(owner_id="u1", title="Test")
    plan = TaskPlannerV2().plan("Хочу сайт стоматологии", workspace_id=ws.workspace_id)
    assert len(plan.steps) == 3
    assert plan.steps[0].capability_id == "filesystem_write"
    assert plan.steps[1].capability_id == "generate_site"
    assert "filesystem" in plan.required_permissions


def test_execution_manager_blocks_unimplemented_capabilities(memory_tmp: Path):
    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="ceo", title="Site")
    logs = ExecutionLogStore(memory_tmp)
    mgr = ExecutionManager(workspace_store=ws_store, log_store=logs)
    plan = TaskPlannerV2().plan("Создай сайт", workspace_id=ws.workspace_id)
    grant = PermissionGrant(
        kinds=plan.required_permissions | frozenset({"read", "write", "filesystem", "network", "deployment", "external_api"}),
        workspace_id=ws.workspace_id,
        actor="ceo",
    )
    result = mgr.run(plan, grant)
    assert result.status == "blocked"
    assert result.steps[0].status == "blocked"
    assert "not implemented" in (result.steps[0].error or "")
    saved = logs.load_run(result.plan_id)
    assert saved is not None
    assert saved["status"] == "blocked"


def test_execution_manager_runs_registered_executor(memory_tmp: Path):
    reg = ExecutionCapabilityRegistry()

    class TaskQueueExecutor:
        def execute(self, inputs: dict, context: dict) -> dict:
            return {"task_id": "tq-001"}

    reg.register_executor("task_queue", TaskQueueExecutor())
    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="u1", title="General")
    logs = ExecutionLogStore(memory_tmp)
    mgr = ExecutionManager(registry=reg, workspace_store=ws_store, log_store=logs)
    plan = TaskPlannerV2(reg).plan("Расскажи анекдот", workspace_id=ws.workspace_id)
    grant = PermissionGrant(kinds=frozenset({"write", "read"}), workspace_id=ws.workspace_id)
    result = mgr.run(plan, grant)
    assert result.status == "completed"
    assert result.steps[0].verified is True
    assert result.steps[0].outputs["task_id"] == "tq-001"


def test_permission_denied_missing_grant(memory_tmp: Path):
    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="u1", title="X")
    logs = ExecutionLogStore(memory_tmp)
    mgr = ExecutionManager(workspace_store=ws_store, log_store=logs)
    plan = TaskPlannerV2().plan("Сайт", workspace_id=ws.workspace_id)
    grant = PermissionGrant(kinds=frozenset({"read"}), workspace_id=ws.workspace_id)
    with pytest.raises(PermissionDenied):
        mgr.run(plan, grant)


def test_workspace_creates_isolated_dirs(memory_tmp: Path):
    store = ExecutionWorkspaceStore(memory_tmp)
    ws = store.create(owner_id="owner", title="Project")
    for area in ("files", "logs", "tasks", "artifacts", "memory"):
        assert store.path_for(ws.workspace_id, area).is_dir()


def test_filesystem_write_executor_creates_file(memory_tmp: Path):
    from app.execution.executors.filesystem import FilesystemWriteExecutor

    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="u1", title="T")
    ex = FilesystemWriteExecutor(ws_store)
    out = ex.execute(
        {"path": "README.md", "content": "# Hi", "workspace_id": ws.workspace_id},
        {"workspace_id": ws.workspace_id},
    )
    assert out["path"] == "README.md"
    target = ws_store.path_for(ws.workspace_id, "files", "README.md")
    assert target.read_text(encoding="utf-8") == "# Hi"


def test_bridge_creates_readme_from_chat_goal(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    out = bridge.try_user_execution("Создай README", visitor_id="visitor-1", memory_dir=memory_tmp)
    assert out is not None
    assert out["provider"] == "execution"
    assert "README.md" in out["answer"]
    assert "✓ Готово" in out["answer"]
    ws_id = out["context"]["workspace_id"]
    path = ExecutionWorkspaceStore(memory_tmp).path_for(ws_id, "files", "README.md")
    assert path.is_file()
    assert "# README" in path.read_text(encoding="utf-8")


def test_bridge_returns_none_for_normal_chat(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    assert bridge.try_user_execution("Привет как дела?", visitor_id="v2", memory_dir=memory_tmp) is None


def test_generate_site_executor_creates_project(memory_tmp: Path):
    import app.execution.bridge as bridge
    from app.execution.executors.generate_site import GenerateSiteExecutor

    bridge._REGISTRY = None
    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="u1", title="Site")
    ex = GenerateSiteExecutor(ws_store)
    out = ex.execute(
        {"brief": "Создай сайт стоматологии", "workspace_id": ws.workspace_id},
        {"workspace_id": ws.workspace_id, "goal": "Создай сайт стоматологии"},
    )
    assert out["artifact_id"].startswith("site-")
    assert "index.html" in out["files"]
    assert "style.css" in out["files"]
    assert "brief.md" in out["files"]
    assert ws_store.path_for(ws.workspace_id, "files", "index.html").is_file()
    preview_index = ws_store.path_for(ws.workspace_id, "artifacts", "preview") / "index.html"
    assert preview_index.is_file()


def test_bridge_site_goal_returns_preview_cta(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    map_path = memory_tmp / "execution" / "visitor_workspaces.json"
    out = bridge.try_user_execution(
        "Создай сайт стоматологии",
        visitor_id="visitor-site",
        memory_dir=memory_tmp,
    )
    assert out is not None
    assert out["provider"] == "execution"
    assert "✓ Готово" in out["answer"]
    assert "index.html" in out["answer"]
    assert out["cta_href"]
    assert out["cta_label"] == "Открыть preview"
    ws_id = out["context"]["workspace_id"]
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    assert mapping["visitor-site"] == ws_id


def test_preview_requires_visitor_ownership(memory_tmp: Path):
    import pytest
    from fastapi import HTTPException

    from app.execution.preview import serve_preview

    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="owner", title="P")
    map_path = memory_tmp / "execution" / "visitor_workspaces.json"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps({"v1": ws.workspace_id}), encoding="utf-8")
    preview_dir = ws_store.path_for(ws.workspace_id, "artifacts", "preview")
    preview_dir.mkdir(parents=True, exist_ok=True)
    (preview_dir / "index.html").write_text("<html></html>", encoding="utf-8")

    resp = serve_preview(memory_tmp, ws.workspace_id, "v1")
    assert resp is not None

    with pytest.raises(HTTPException) as exc:
        serve_preview(memory_tmp, ws.workspace_id, "stranger")
    assert exc.value.status_code == 403

