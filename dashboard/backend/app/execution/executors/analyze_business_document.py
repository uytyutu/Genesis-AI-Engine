"""Analyze business documents — PDF/DOCX → structured artifacts (Commit 3)."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.execution.artifact_result import CapabilityArtifact, CapabilityResult
from app.execution.document_intelligence import (
    analyze_document,
    render_executive_summary_md,
    render_report_md,
    structure_json,
)
from app.execution.workspace import ExecutionWorkspaceStore
from app.integration.knowledge_intake_pdf import extract_pdf_text
from app.integration.public_chat_attachments import PublicChatAttachmentService

_MAX_ANALYSIS_PAGES = 50


def _extract_text_from_path(path: Path, content_type: str) -> tuple[str, int, int]:
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime == "application/pdf" or path.suffix.lower() == ".pdf":
        return extract_pdf_text(path, max_pages=_MAX_ANALYSIS_PAGES)
    if path.suffix.lower() in (".txt", ".md"):
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        return text, 1, 1
    raise ValueError(f"unsupported document type: {content_type or path.suffix}")


class AnalyzeBusinessDocumentExecutor:
    """Universal business document analysis → composable artifacts."""

    def __init__(self, workspace_store: ExecutionWorkspaceStore, memory_dir: Path) -> None:
        self._workspaces = workspace_store
        self._memory_dir = memory_dir

    def execute(self, inputs: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        workspace_id = str(inputs.get("workspace_id") or context.get("workspace_id") or "")
        if not workspace_id:
            raise ValueError("workspace_id required")

        goal = str(inputs.get("goal") or context.get("goal") or "").strip()
        attachment_id = str(inputs.get("attachment_id") or "").strip()
        inline_text = str(inputs.get("document_text") or "").strip()

        source_path: Path | None = None
        filename = "document.pdf"
        content_type = "application/pdf"
        page_count = 0
        pages_included = 0

        if attachment_id:
            meta = PublicChatAttachmentService(self._memory_dir).get_meta(attachment_id)
            if not meta:
                raise ValueError("attachment not found")
            source_path = Path(str(meta.get("path") or ""))
            filename = str(meta.get("filename") or filename)
            content_type = str(meta.get("content_type") or content_type)
            if not source_path.is_file():
                raise ValueError("attachment file missing on disk")

        if source_path:
            text, page_count, pages_included = _extract_text_from_path(source_path, content_type)
        elif inline_text:
            text = inline_text
        else:
            raise ValueError("document required: attach PDF or provide document_text")

        if not text.strip():
            raise ValueError("no extractable text in document")

        analysis = analyze_document(
            text,
            filename=filename,
            goal=goal,
            page_count=page_count if source_path else 0,
            pages_analyzed=pages_included if source_path else 0,
            locale=str(inputs.get("report_locale") or context.get("report_locale") or "") or None,
        )

        artifact_id = f"doc-{uuid.uuid4().hex[:8]}"
        files_root = self._workspaces.path_for(workspace_id, "files")
        uploads_dir = files_root / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        if source_path:
            stored_source = uploads_dir / Path(filename).name
            shutil.copy2(source_path, stored_source)
            source_rel = f"uploads/{stored_source.name}"
        else:
            source_rel = ""

        written = [
            "executive_summary.md",
            "report.md",
            "document_structure.json",
        ]
        if source_rel:
            written.insert(0, source_rel)

        (files_root / "executive_summary.md").write_text(
            render_executive_summary_md(analysis, source_filename=filename),
            encoding="utf-8",
        )
        (files_root / "report.md").write_text(
            render_report_md(analysis, source_filename=filename),
            encoding="utf-8",
        )
        (files_root / "document_structure.json").write_text(
            structure_json(analysis),
            encoding="utf-8",
        )

        manifest = {
            "artifact_id": artifact_id,
            "capability_id": "analyze_business_document",
            "document_type": analysis.structure.document_type,
            "title": analysis.structure.title,
            "source_filename": filename,
            "files": written,
            "building_blocks": {
                "document_structure": "files/document_structure.json",
                "report": "files/report.md",
                "executive_summary": "files/executive_summary.md",
            },
        }
        manifest_path = self._workspaces.path_for(workspace_id, "artifacts", f"{artifact_id}.json")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        logs = [
            "Принимаю документ",
            "Извлекаю текст",
            f"Тип документа: {analysis.structure.document_type}",
            "Структурный анализ",
            "SWOT и риски",
            "Формирую отчёты",
        ]

        result = CapabilityResult(
            workspace_id=workspace_id,
            artifact_id=artifact_id,
            files=written,
            artifacts=[
                CapabilityArtifact(
                    id=f"{artifact_id}-report",
                    kind="file",
                    path="files/report.md",
                    label="report.md",
                ),
                CapabilityArtifact(
                    id=f"{artifact_id}-summary",
                    kind="file",
                    path="files/executive_summary.md",
                    label="executive_summary.md",
                ),
                CapabilityArtifact(
                    id=f"{artifact_id}-structure",
                    kind="file",
                    path="files/document_structure.json",
                    label="document_structure.json",
                ),
            ],
            preview_url=f"/api/public/execution/workspace/{workspace_id}/files/report.md",
            logs=logs,
            status="completed",
            capability_id="analyze_business_document",
        )
        out = result.to_dict()
        out["document_type"] = analysis.structure.document_type
        out["title"] = analysis.structure.title
        out["source_filename"] = filename
        out["pages_analyzed"] = pages_included if source_path else 0
        out["readiness_score"] = analysis.readiness_score
        out["launch_probability_pct"] = analysis.launch_probability_pct
        self._workspaces.touch(workspace_id)
        return out

    def rollback(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        workspace_id = str(outputs.get("workspace_id") or inputs.get("workspace_id") or "")
        if not workspace_id:
            return
        for rel in ("executive_summary.md", "report.md", "document_structure.json"):
            path = self._workspaces.path_for(workspace_id, "files", rel)
            if path.is_file():
                path.unlink()
        artifact_id = str(outputs.get("artifact_id") or "")
        if artifact_id:
            manifest = self._workspaces.path_for(workspace_id, "artifacts", f"{artifact_id}.json")
            if manifest.is_file():
                manifest.unlink()
