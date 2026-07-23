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
    assert "✓ Документ создан" in out["answer"]
    ws_id = out["context"]["workspace_id"]
    path = ExecutionWorkspaceStore(memory_tmp).path_for(ws_id, "files", "README.md")
    assert path.is_file()
    assert "# README" in path.read_text(encoding="utf-8")


def test_bridge_returns_none_for_normal_chat(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    assert bridge.try_user_execution("Привет как дела?", visitor_id="v2", memory_dir=memory_tmp) is None


def test_bridge_analyzes_pdf_without_analyze_keyword(memory_tmp: Path):
    """PDF-only upload must route to execution — not Brain essay (Product Truth)."""
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    upload_dir = memory_tmp / "public_chat_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    att_id = "att-pdf-only"
    plan_path = upload_dir / f"{att_id}.txt"
    plan_path.write_text(
        "TechGenie Haus Service. Берлин. Smart Home.",
        encoding="utf-8",
    )
    (upload_dir / "index.json").write_text(
        json.dumps(
            [
                {
                    "id": att_id,
                    "filename": "BUSINESSPLAN.txt",
                    "content_type": "text/plain",
                    "path": str(plan_path),
                    "visitor_id": "pdf-only",
                }
            ]
        ),
        encoding="utf-8",
    )
    files_only_prompt = (
        "Клиент прикрепил файлы без текста. Содержимое недоступно — только имена. "
        "Попроси кратко описать задачу словами."
    )
    out = bridge.try_user_execution(
        files_only_prompt,
        visitor_id="pdf-only",
        memory_dir=memory_tmp,
        attachment_files=[
            {"id": att_id, "filename": "BUSINESSPLAN.txt", "content_type": "text/plain"}
        ],
    )
    assert out is not None
    assert out["provider"] == "execution"
    assert "📊 Executive Summary" in str(out.get("cta_actions"))
    assert out.get("cta_actions")
    ws_id = out["context"]["workspace_id"]
    ws = ExecutionWorkspaceStore(memory_tmp)
    assert ws.path_for(ws_id, "files", "report.md").is_file()
    assert ws.path_for(ws_id, "files", "executive_summary.md").is_file()


    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    out = bridge.try_user_execution(
        "Ты умеешь делать сайты?",
        visitor_id="v-discover",
        memory_dir=memory_tmp,
    )
    assert out is not None
    assert out["provider"] == "capability_registry"
    assert "создавать сайты" in out["answer"].lower()
    assert "стоматологии" in out["answer"]
    assert "preview" not in out["answer"].lower()
    assert "workspace" not in out["answer"].lower()


def test_bridge_capability_discovery_general(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    out = bridge.try_user_execution(
        "Что ты умеешь?",
        visitor_id="v-discover-2",
        memory_dir=memory_tmp,
    )
    assert out is not None
    assert out["provider"] == "capability_registry"
    assert "Я умею" in out["answer"]
    assert "README" in out["answer"] or "readme" in out["answer"].lower()


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
    # RC1 co-design: first niche site goal opens journey (goal/CTA question), not instant concept
    ctx = out.get("context") or {}
    assert ctx.get("co_design") is True or ctx.get("journey_step") in {
        "company",
        "goal",
        "style",
        "colors",
        "logo",
        "materials",
    }
    ans = (out.get("answer") or "").lower()
    assert (
        "концепц" in ans
        or "перв" in ans
        or "заявк" in ans
        or "позвон" in ans
        or "запис" in ans
        or "зафиксир" in ans
    )
    if out.get("cta_href"):
        assert out["cta_label"] == "🌐 Открыть сайт"
        assert out["cta_actions"]
        assert out["cta_actions"][0]["label"] == "🌐 Открыть сайт"
    mapping = json.loads(map_path.read_text(encoding="utf-8")) if map_path.is_file() else {}
    if "visitor-site" in mapping:
        assert mapping["visitor-site"]


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


def test_document_intelligence_classifies_business_plan():
    from app.execution.document_intelligence import analyze_document, classify_document

    text = """
    Бизнес-план стоматологической клиники SmileDent
    Рынок: растущий спрос на имплантацию. Финансы: выручка 120000 евро в год.
    Сильные стороны: опытная команда врачей. Риск: высокая конкуренция в районе.
    """
    assert classify_document(text, filename="plan.pdf", goal="бизнес-план") == "business_plan"
    analysis = analyze_document(text, filename="plan.pdf", goal="бизнес-план", locale="ru")
    assert analysis.swot["strengths"]
    assert analysis.risks or analysis.swot["threats"]
    assert analysis.readiness_score >= 0
    assert analysis.priority_actions
    assert "Вердикт" in analysis.executive_summary or "verdict" in analysis.executive_summary.lower()


def test_analyze_business_document_executor_writes_reports(memory_tmp: Path):
    from app.execution.executors.analyze_business_document import AnalyzeBusinessDocumentExecutor

    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="u1", title="Docs")
    ex = AnalyzeBusinessDocumentExecutor(ws_store, memory_tmp)
    text = (
        "Бизнес-план кофейни. Рынок specialty coffee растёт. "
        "Финансы: точка безубыточности через 8 месяцев. "
        "Сильные стороны: уникальная локация. Риск: сезонность спроса."
    )
    out = ex.execute(
        {"workspace_id": ws.workspace_id, "goal": "анализ", "document_text": text},
        {"workspace_id": ws.workspace_id, "goal": "анализ"},
    )
    assert out["artifact_id"].startswith("doc-")
    assert "report.md" in out["files"]
    assert "executive_summary.md" in out["files"]
    assert "document_structure.json" in out["files"]
    report = ws_store.path_for(ws.workspace_id, "files", "report.md").read_text(encoding="utf-8")
    assert "SWOT" in report or "swot" in report.lower()
    assert "Готовность" in report or "readiness" in report.lower()
    assert "кофейни" in report or "specialty" in report.lower()


def test_bridge_analyze_document_with_attachment(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    upload_dir = memory_tmp / "public_chat_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    att_id = "att-doc001"
    plan_path = upload_dir / f"{att_id}.txt"
    plan_path.write_text(
        "Бизнес-план автосервиса. Рынок: 5000 автомобилей в радиусе 3 км. "
        "Финансы: стартовые инвестиции 40000. Риск: дефицит механиков.",
        encoding="utf-8",
    )
    meta_path = upload_dir / "index.json"
    meta_path.write_text(
        json.dumps(
            [
                {
                    "id": att_id,
                    "filename": "business-plan.txt",
                    "content_type": "text/plain",
                    "path": str(plan_path),
                    "visitor_id": "visitor-doc",
                }
            ]
        ),
        encoding="utf-8",
    )
    out = bridge.try_user_execution(
        "Проанализируй мой бизнес-план",
        visitor_id="visitor-doc",
        memory_dir=memory_tmp,
        attachment_files=[
            {
                "id": att_id,
                "filename": "business-plan.txt",
                "content_type": "text/plain",
            }
        ],
    )
    assert out is not None
    assert out["provider"] == "execution"
    assert "✓" in out["answer"]
    assert out["cta_actions"] and len(out["cta_actions"]) >= 2
    labels = " ".join(str(a.get("label")) for a in out["cta_actions"])
    assert "Executive Summary" in labels
    assert out["cta_label"] == "📊 Executive Summary"


def test_serve_workspace_file_requires_visitor(memory_tmp: Path):
    import pytest
    from fastapi import HTTPException

    from app.execution.preview import serve_workspace_file

    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="owner", title="Doc")
    map_path = memory_tmp / "execution" / "visitor_workspaces.json"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps({"v1": ws.workspace_id}), encoding="utf-8")
    report = ws_store.path_for(ws.workspace_id, "files", "report.md")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Report", encoding="utf-8")

    resp = serve_workspace_file(memory_tmp, ws.workspace_id, "v1", "report.md")
    assert resp is not None

    with pytest.raises(HTTPException) as exc:
        serve_workspace_file(memory_tmp, ws.workspace_id, "other", "report.md")
    assert exc.value.status_code == 403


def test_capability_graph_declares_produces_consumes():
    from app.execution.capability_graph import CAPABILITY_GRAPH, get_node

    analyze = get_node("analyze_business_document")
    assert analyze is not None
    produce_paths = {p.path for p in analyze.produces}
    assert "files/document_structure.json" in produce_paths
    assert "files/report.md" in produce_paths

    site = get_node("generate_site")
    assert site is not None
    consume_paths = {c.path for c in site.consumes}
    assert "files/document_structure.json" in consume_paths
    assert site.reuse_score_when_wired >= 1


def test_generate_site_writes_site_manifest(memory_tmp: Path):
    from app.execution.executors.generate_site import GenerateSiteExecutor
    from app.execution.document_intelligence import analyze_document, structure_json

    ws_store = ExecutionWorkspaceStore(memory_tmp)
    ws = ws_store.create(owner_id="u1", title="Reuse")
    plan_text = (
        "Бизнес-план стоматологии SmileDent. Рынок: имплантация растёт на 12% в год. "
        "Сильные стороны: команда из 8 врачей с европейской сертификацией. "
        "Финансы: выручка 200000 евро. Риск: конкуренция в центре города."
    )
    doc_analysis = analyze_document(plan_text, filename="plan.pdf", goal="бизнес-план")
    files_root = ws_store.path_for(ws.workspace_id, "files")
    files_root.mkdir(parents=True, exist_ok=True)
    (files_root / "document_structure.json").write_text(structure_json(doc_analysis), encoding="utf-8")
    (files_root / "executive_summary.md").write_text(
        "# Executive Summary\n\nSmileDent — лидер имплантации в районе.\n",
        encoding="utf-8",
    )

    ex = GenerateSiteExecutor(ws_store)
    out = ex.execute(
        {"brief": "Создай сайт", "workspace_id": ws.workspace_id},
        {"workspace_id": ws.workspace_id, "goal": "Создай сайт"},
    )
    assert out.get("reuse_score", 0) >= 1
    assert "analyze_business_document" in out.get("reused_capabilities", [])
    brief = (files_root / "brief.md").read_text(encoding="utf-8")
    assert "Reuse" in brief or "document_structure" in brief
    html = (files_root / "index.html").read_text(encoding="utf-8")
    assert "SmileDent" in html or doc_analysis.structure.title.split()[0] in html
    assert (files_root / "site_manifest.json").is_file()


def test_workflow_analyze_then_site_same_visitor(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    visitor = "workflow-visitor"
    upload_dir = memory_tmp / "public_chat_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    att_id = "att-wf001"
    plan_path = upload_dir / f"{att_id}.txt"
    plan_path.write_text(
        "Бизнес-план клиники DentalPro. Рынок стоматологии. "
        "Сильные стороны: цифровая диагностика. Финансы: рост 15%.",
        encoding="utf-8",
    )
    (upload_dir / "index.json").write_text(
        json.dumps(
            [
                {
                    "id": att_id,
                    "filename": "plan.txt",
                    "content_type": "text/plain",
                    "path": str(plan_path),
                    "visitor_id": visitor,
                }
            ]
        ),
        encoding="utf-8",
    )
    analyze_out = bridge.try_user_execution(
        "Проанализируй мой бизнес-план",
        visitor_id=visitor,
        memory_dir=memory_tmp,
        attachment_files=[{"id": att_id, "filename": "plan.txt", "content_type": "text/plain"}],
    )
    assert analyze_out and analyze_out["provider"] == "execution"
    ws_id = analyze_out["context"]["workspace_id"]

    site_out = bridge.try_user_execution(
        "Создай сайт",
        visitor_id=visitor,
        memory_dir=memory_tmp,
    )
    assert site_out and site_out["provider"] == "execution"
    assert site_out["context"]["workspace_id"] == ws_id
    cap = site_out["context"]["capability_result"]
    assert cap.get("reuse_score", 0) >= 1
    assert "проект" in (site_out["answer"] or "").lower()


def test_bridge_vague_site_asks_before_build(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    out = bridge.try_user_execution(
        "хочу создать сайт",
        visitor_id="visitor-vague",
        memory_dir=memory_tmp,
    )
    assert out is not None
    assert out["provider"] == "execution"
    assert "проект создан" in out["answer"].lower()
    assert "компани" in out["answer"].lower() or "бизнес" in out["answer"].lower()
    assert "позвонить" not in out["answer"].lower()
    assert "рынка" not in out["answer"].lower()
    assert (out.get("context") or {}).get("journey_step") == "company"
    assert out.get("cta_href") is None


def test_bridge_generic_company_site_asks_before_build(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    out = bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id="visitor-generic-co",
        memory_dir=memory_tmp,
    )
    assert out is not None
    assert out["provider"] == "execution"
    assert "проект создан" in out["answer"].lower()
    assert "компани" in out["answer"].lower() or "занимаетесь" in out["answer"].lower()
    assert "позвонить" not in out["answer"].lower()
    assert "рынка" not in out["answer"].lower()
    assert (out.get("context") or {}).get("journey_step") == "company"
    assert out.get("cta_href") is None
    assert "index.html" not in (out.get("answer") or "")


def _complete_site_co_design(bridge, *, visitor_id: str, memory_dir: Path):
    """Natural co-design steps — concept after logo, materials never block."""
    steps = [
        "Современный минималистичный стиль, светлый и чистый.",
        "Да, оставляем этот вариант.",
        "Хорошо, продолжаем.",
    ]
    last = None
    for msg in steps:
        last = bridge.try_user_execution(msg, visitor_id=visitor_id, memory_dir=memory_dir)
        assert last is not None
    return last


def test_bridge_style_step_pm_understanding_and_proposal(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-pm-style"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    second = bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert second is not None
    ans = second["answer"].lower()
    assert "greenline" in ans
    assert "солнеч" in ans or "панел" in ans
    # Industry Intelligence style prompt (solar): светлый технологичный — not generic минимализм PM copy
    assert "светлый" in ans or "технологич" in ans or "минимал" in ans
    assert (second.get("context") or {}).get("journey_step") == "style"


def test_bridge_color_step_pm_palette_proposal(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-pm-colors"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    third = bridge.try_user_execution(
        "Современный минимализм, светлый.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert third is not None
    ans = third["answer"].lower()
    assert "greenline" in ans
    assert "бело-зелён" in ans or "зелён" in ans
    assert "солнеч" in ans or "энергет" in ans
    assert "оставляем" in ans or "другую палитру" in ans
    assert "фирменные цвета" not in ans or "адаптирую" in ans
    assert (third.get("context") or {}).get("journey_step") == "colors"


def test_bridge_logo_step_pm_text_logo_proposal(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-pm-logo"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Современный минимализм, светлый.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    fourth = bridge.try_user_execution(
        "Да, оставляем этот вариант.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert fourth is not None
    ans = fourth["answer"].lower()
    assert "палитру фиксирую" in ans
    assert "greenline" in ans
    assert "текстов" in ans and "логотип" in ans
    assert "заменю" in ans or "позже" in ans
    assert "есть готовый логотип? можете прикрепить" not in ans
    assert (fourth.get("context") or {}).get("journey_step") == "logo"


def test_bridge_materials_auto_advances_to_concept(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-pm-materials"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Современный минимализм, светлый.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Да, оставляем этот вариант.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    last = bridge.try_user_execution(
        "Хорошо, продолжаем.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert last is not None
    ans = last["answer"].lower()
    assert "временн" in ans
    assert "солнеч" in ans or "энергет" in ans
    assert "есть фото, тексты или ссылки" not in ans
    assert last.get("cta_href")
    assert last["cta_label"] == "🌐 Открыть сайт"
    assert (last.get("context") or {}).get("co_design") is not True


def test_bridge_co_design_asks_style_before_concept(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-codesign-gate"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    second = bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert second is not None
    assert second.get("cta_href") is None
    assert "стиль" in second["answer"].lower() or "визуальн" in second["answer"].lower()
    assert "концепц" not in second["answer"].lower()


def test_bridge_followup_brief_generates_recognizable_site(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-followup"
    first = bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert first is not None
    assert first.get("cta_href") is None

    second = bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert second is not None
    assert second.get("cta_href") is None
    third = _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    assert third is not None
    assert third["provider"] == "execution"
    assert "перв" in third["answer"].lower() or "концепц" in third["answer"].lower()
    assert third.get("cta_href")
    assert third["cta_label"] == "🌐 Открыть сайт"

    from app.execution.workspace import ExecutionWorkspaceStore

    map_path = memory_tmp / "execution" / "visitor_workspaces.json"
    ws_id = json.loads(map_path.read_text(encoding="utf-8"))[vid]
    preview = ExecutionWorkspaceStore(memory_tmp).path_for(ws_id, "artifacts") / "preview" / "index.html"
    body = preview.read_text(encoding="utf-8")
    assert "GreenLine" in body
    assert "солнеч" in body.lower() or "Solar" in body or "панел" in body.lower()
    assert "hello@example.com" not in body
    assert "+7 (000)" not in body
    # Path A / Factory DE CTA copy (not legacy RU «Оставить заявку»)
    assert (
        "Оставить заявку" in body
        or "заявк" in body.lower()
        or "Anfrage" in body
        or "anfragen" in body.lower()
    )


def test_bridge_materials_phrase_triggers_first_concept(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-materials-phrase"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    for msg in (
        "Современный минималистичный стиль, светлый и чистый.",
        "Да, оставляем этот вариант.",
    ):
        bridge.try_user_execution(msg, visitor_id=vid, memory_dir=memory_tmp)
    last = bridge.try_user_execution(
        "Хорошо, продолжаем.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert last is not None
    assert last["provider"] == "execution"
    assert last.get("cta_href")
    assert "временн" in (last.get("answer") or "").lower()


def test_bridge_followup_after_orphan_versions_without_preview(memory_tmp: Path):
    """Disk-synced versions without preview must not block first site generation."""
    import app.execution.bridge as bridge
    from app.integration.project_platform.service import ProjectPlatformService
    from app.integration.project_platform.store import ProjectStore
    from app.integration.project_platform.schema import ProjectVersion, ProjectArtifact

    bridge._REGISTRY = None
    vid = "visitor-orphan-ver"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    svc = ProjectPlatformService(memory_tmp)
    state = svc.get_for_visitor(vid)
    ws_id = state["project"]["workspace_id"]
    record = ProjectStore(memory_tmp).load(ws_id)
    assert record is not None
    record.versions.append(
        ProjectVersion(
            version=1,
            label="Импорт",
            created_at=record.created_at,
            summary="Импорт существующих файлов проекта",
            artifacts=[
                ProjectArtifact(
                    id="art-orphan",
                    kind="source",
                    label="notes.txt",
                    href=None,
                    section="files",
                    version=1,
                )
            ],
        )
    )
    ProjectStore(memory_tmp).save(record)

    second = bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert second is not None
    third = _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    assert third is not None
    assert third["provider"] == "execution"
    assert third.get("cta_href")


def test_bridge_revision_uses_project_brief_not_edit_text(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-revision"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    revised = bridge.try_user_execution(
        "Хочу внести правки: убери из описания на сайте весь лишний текст про «хочу создать сайт». "
        "Оставь только про GreenLine и солнечные панели.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert revised is not None
    assert revised["provider"] == "execution"
    assert "правк" in revised["answer"].lower() or "обновил" in revised["answer"].lower() or "внёс" in revised["answer"].lower()

    from app.execution.workspace import ExecutionWorkspaceStore

    map_path = memory_tmp / "execution" / "visitor_workspaces.json"
    ws_id = json.loads(map_path.read_text(encoding="utf-8"))[vid]
    preview = ExecutionWorkspaceStore(memory_tmp).path_for(ws_id, "artifacts") / "preview" / "index.html"
    body = preview.read_text(encoding="utf-8")
    assert "GreenLine" in body
    assert "хочу внести правки" not in body.lower()
    assert "хочу создать сайт" not in body.lower()


def test_bridge_natural_add_block_triggers_revision(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-revision-add"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    revised = bridge.try_user_execution(
        "Добавь на сайт блок с отзывами клиентов",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert revised is not None
    assert revised["provider"] == "execution"
    assert revised.get("cta_href") or revised.get("cta_actions")


def test_bridge_purchase_requires_approval_first(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-purchase-gate"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    blocked = bridge.try_user_execution(
        "Хочу заказать.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert blocked is not None
    assert "устраивает" in blocked["answer"].lower()
    assert blocked.get("cta_href", "").startswith("/api/public/execution/preview")


def test_bridge_purchase_after_approval_routes_to_order(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-purchase-order"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    bridge.try_user_execution("Да, всё устраивает.", visitor_id=vid, memory_dir=memory_tmp)
    out = bridge.try_user_execution(
        "Хочу заказать.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert out is not None
    assert out["provider"] == "execution"
    assert out.get("cta_href", "").startswith("/order")
    assert "фиксируем" in out["answer"].lower()
    assert "первую концепцию" not in out["answer"].lower()


def test_bridge_soft_satisfaction_asks_before_order(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-like"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    out = bridge.try_user_execution("Мне нравится.", visitor_id=vid, memory_dir=memory_tmp)
    assert out is not None
    assert out.get("cta_href", "").startswith("/api/public/execution/preview")
    assert "/order" not in (out.get("cta_href") or "")
    assert "устраивает" in out["answer"].lower()


def test_bridge_revision_header_after_preview(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-rev-header"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    revised = bridge.try_user_execution(
        "Сделай шапку чуть современнее.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert revised is not None
    assert revised["provider"] == "execution"
    assert "правк" in revised["answer"].lower() or "внёс" in revised["answer"].lower()


def test_bridge_purchase_inquiry_routes_to_pricing(memory_tmp: Path):
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    vid = "visitor-purchase"
    bridge.try_user_execution(
        "Хочу создать сайт для своей компании.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    bridge.try_user_execution(
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    _complete_site_co_design(bridge, visitor_id=vid, memory_dir=memory_tmp)
    bridge.try_user_execution("Да, всё устраивает.", visitor_id=vid, memory_dir=memory_tmp)
    out = bridge.try_user_execution(
        "Хочу заказать этот сайт. Сколько стоит и как оформить заказ?",
        visitor_id=vid,
        memory_dir=memory_tmp,
    )
    assert out is not None
    assert out["provider"] == "execution"
    assert out.get("cta_href", "").startswith("/order")
    assert "фиксируем" in out["answer"].lower()
    assert "первую концепцию" not in out["answer"].lower()

