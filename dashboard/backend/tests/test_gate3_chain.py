"""Gate 3 RC1 — full PDF → execution → artifacts chain audit tests."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.execution.workspace import ExecutionWorkspaceStore
from app.integration.knowledge_intake_service import KnowledgeIntakeService
from app.integration.public_chat_attachments import PublicChatAttachmentService


def _write_blank_pdf(path: Path, *, pages: int = 1) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        writer.write(fh)


def _seed_attachment(
    memory_tmp: Path,
    *,
    att_id: str,
    filename: str,
    content_type: str,
    body: str,
    visitor_id: str = "gate3-visitor",
) -> str:
    upload_dir = memory_tmp / "public_chat_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    if content_type == "application/pdf":
        file_path = upload_dir / f"{att_id}.pdf"
        _write_blank_pdf(file_path)
        store_path = upload_dir / f"{att_id}.txt"
        store_path.write_text(body, encoding="utf-8")
        store_name = f"{Path(filename).stem}.txt"
        store_type = "text/plain"
        disk_path = store_path
    else:
        file_path = upload_dir / f"{att_id}{Path(filename).suffix or '.txt'}"
        file_path.write_text(body, encoding="utf-8")
        store_name = filename
        store_type = content_type
        disk_path = file_path
    index = upload_dir / "index.json"
    rows: list[dict] = []
    if index.is_file():
        rows = json.loads(index.read_text(encoding="utf-8"))
    rows.append(
        {
            "id": att_id,
            "filename": store_name,
            "content_type": store_type,
            "path": str(disk_path),
            "visitor_id": visitor_id,
        }
    )
    index.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return att_id


@pytest.fixture
def memory_tmp(tmp_path: Path) -> Path:
    mem = tmp_path / "memory"
    mem.mkdir()
    return mem


@pytest.mark.parametrize(
    ("question", "att_id"),
    [
        ("Проверь мой бизнес-план", "att-g3-ru"),
        ("Проанализируй бизнес-план", "att-g3-ru2"),
        ("Analyze my business plan", "att-g3-en"),
        ("Review this document", "att-g3-en2"),
    ],
)
def test_gate3_routing_questions(memory_tmp: Path, question: str, att_id: str) -> None:
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    _seed_attachment(
        memory_tmp,
        att_id=att_id,
        filename="BUSINESSPLAN.pdf",
        content_type="application/pdf",
        body="TechGenie Haus Service Berlin Smart Home dental market analysis.",
    )
    out = bridge.try_user_execution(
        question,
        visitor_id="gate3-visitor",
        memory_dir=memory_tmp,
        attachment_files=[
            {"id": att_id, "filename": "BUSINESSPLAN.txt", "content_type": "text/plain"}
        ],
    )
    assert out is not None, f"routing failed for: {question}"
    assert out["provider"] == "execution"
    assert "Не удалось" not in out["answer"]
    assert out.get("cta_actions")


def test_gate3_resolve_for_execution_finds_meta_without_parse(memory_tmp: Path) -> None:
    att_id = "att-resolve"
    _seed_attachment(
        memory_tmp,
        att_id=att_id,
        filename="plan.pdf",
        content_type="application/pdf",
        body="AutoService Berlin revenue growth 2026.",
    )
    svc = KnowledgeIntakeService(memory_tmp)
    rows = svc.resolve_for_execution(
        attachment_ids=[att_id],
        visitor_id="gate3-visitor",
        session_id=None,
    )
    assert len(rows) == 1
    assert rows[0]["id"] == att_id


def test_gate3_routing_blocks_brain_path(memory_tmp: Path) -> None:
    """When analyzable doc resolved, bridge returns execution (Brain not needed)."""
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    att_id = "att-brain-block"
    _seed_attachment(
        memory_tmp,
        att_id=att_id,
        filename="business-plan.txt",
        content_type="text/plain",
        body="Coffee shop Berlin Mitte. Revenue 120k. Risk: rent increase.",
    )
    out = bridge.try_user_execution(
        "Проверь мой бизнес-план",
        visitor_id="gate3-visitor",
        memory_dir=memory_tmp,
        attachment_files=[{"id": att_id, "filename": "business-plan.txt", "content_type": "text/plain"}],
    )
    assert out["provider"] == "execution"
    assert "✓ Отчёты созданы" in out["answer"]


def test_gate3_artifacts_created(memory_tmp: Path) -> None:
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    att_id = "att-artifacts"
    _seed_attachment(
        memory_tmp,
        att_id=att_id,
        filename="plan.txt",
        content_type="text/plain",
        body="Clinic SmileDent. Market: dentistry. SWOT strengths: digital X-ray.",
    )
    out = bridge.try_user_execution(
        "Проверь документ",
        visitor_id="gate3-visitor",
        memory_dir=memory_tmp,
        attachment_files=[{"id": att_id, "filename": "plan.txt", "content_type": "text/plain"}],
    )
    assert out and out["provider"] == "execution"
    ws_id = out["context"]["workspace_id"]
    ws = ExecutionWorkspaceStore(memory_tmp)
    assert ws.path_for(ws_id, "files", "report.md").is_file()
    assert ws.path_for(ws_id, "files", "executive_summary.md").is_file()
    assert ws.path_for(ws_id, "files", "document_structure.json").is_file()


def test_gate3_missing_attachment_ids_via_resolve(memory_tmp: Path) -> None:
    svc = KnowledgeIntakeService(memory_tmp)
    rows = svc.resolve_for_execution(
        attachment_ids=["att-missing-404"],
        visitor_id="gate3-visitor",
        session_id=None,
    )
    assert rows == []


def test_gate3_russian_english_german_content(memory_tmp: Path) -> None:
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    cases = [
        ("ru", "Стартап в Берлине. Рынок умного дома. Риск: конкуренция."),
        ("en", "Berlin startup. Smart home market. Risk: competition."),
        ("de", "Berlin Startup. Smart-Home-Markt. Risiko: Wettbewerb."),
    ]
    for lang, body in cases:
        att_id = f"att-{lang}"
        _seed_attachment(
            memory_tmp,
            att_id=att_id,
            filename=f"plan-{lang}.txt",
            content_type="text/plain",
            body=body,
        )
        out = bridge.try_user_execution(
            "Проверь бизнес-план",
            visitor_id=f"visitor-{lang}",
            memory_dir=memory_tmp,
            attachment_files=[{"id": att_id, "filename": f"plan-{lang}.txt", "content_type": "text/plain"}],
        )
        assert out and out["provider"] == "execution", lang


def test_gate3_large_text_document(memory_tmp: Path) -> None:
    import app.execution.bridge as bridge

    bridge._REGISTRY = None
    att_id = "att-large"
    body = "Paragraph about market. " * 800
    _seed_attachment(
        memory_tmp,
        att_id=att_id,
        filename="large-plan.txt",
        content_type="text/plain",
        body=body,
    )
    out = bridge.try_user_execution(
        "Проверь",
        visitor_id="gate3-large",
        memory_dir=memory_tmp,
        attachment_files=[{"id": att_id, "filename": "large-plan.txt", "content_type": "text/plain"}],
    )
    assert out and out["provider"] == "execution"


def test_gate3_upload_save_roundtrip(memory_tmp: Path) -> None:
    """Frontend upload → index.json → resolve_for_execution."""
    from starlette.datastructures import Headers, UploadFile

    svc = PublicChatAttachmentService(memory_tmp)
    payload = b"%PDF-1.4 business plan content placeholder"
    upload = UploadFile(
        filename="BUSINESSPLAN.pdf",
        file=BytesIO(payload),
        headers=Headers({"content-type": "application/pdf"}),
    )
    row = svc.save(upload, visitor_id="upload-visitor")
    assert row["id"]
    intake = KnowledgeIntakeService(memory_tmp)
    files = intake.resolve_for_execution(
        attachment_ids=[row["id"]],
        visitor_id="upload-visitor",
        session_id=None,
    )
    assert len(files) == 1
    assert files[0]["id"] == row["id"]


def test_gate3_check_business_plan_phrase_matches_analyze_goal() -> None:
    import app.execution.bridge as bridge

    assert bridge._ANALYZE_GOAL.search("Проверь мой бизнес-план")
    assert bridge._DOC_HINT.search("Проверь мой бизнес-план")
