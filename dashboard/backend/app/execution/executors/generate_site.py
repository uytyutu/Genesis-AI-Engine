"""Generate site project — composable capability (Development scenario)."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.execution.artifact_result import CapabilityArtifact, CapabilityResult
from app.factory.landing_builder import build_landing_html
from app.execution.workspace import ExecutionWorkspaceStore
from app.execution.workspace_reuse import (
    analysis_for_site,
    brief_with_reuse,
    load_workspace_building_blocks,
)


def _split_html_css(html: str) -> tuple[str, str]:
    match = re.search(r"<style>(.*?)</style>", html, re.DOTALL | re.IGNORECASE)
    if not match:
        return "", html
    css = match.group(1).strip()
    html_out = html[: match.start()] + '  <link rel="stylesheet" href="style.css">\n' + html[match.end() :]
    return css, html_out


class GenerateSiteExecutor:
    """Build a complete site project in workspace — brief, HTML, CSS, assets, preview."""

    def __init__(self, workspace_store: ExecutionWorkspaceStore) -> None:
        self._workspaces = workspace_store

    def execute(self, inputs: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        workspace_id = str(inputs.get("workspace_id") or context.get("workspace_id") or "")
        if not workspace_id:
            raise ValueError("workspace_id required")
        brief_text = str(inputs.get("brief") or context.get("goal") or "").strip()
        if not brief_text:
            raise ValueError("brief required")

        blocks = load_workspace_building_blocks(self._workspaces, workspace_id)
        analysis, reuse = analysis_for_site(brief_text, blocks)
        html_full = build_landing_html(analysis)
        css, index_html = _split_html_css(html_full)
        if not css:
            css = "/* Vector site */\nbody { font-family: system-ui, sans-serif; }"

        artifact_id = f"site-{uuid.uuid4().hex[:8]}"
        logs: list[str] = ["Анализирую запрос"]
        if reuse.reuse_score > 0:
            logs.append("Использую document_structure.json из workspace")
            if "executive_summary" in reuse.reused_capabilities:
                logs.append("Использую executive_summary.md")
        logs.extend(
            [
                "Формирую структуру проекта",
                "Создаю brief",
                "Генерирую HTML",
                "Генерирую CSS",
                "Создаю preview",
            ]
        )

        files_root = self._workspaces.path_for(workspace_id, "files")
        written: list[str] = []
        payloads = {
            "brief.md": brief_with_reuse(brief_text, analysis, reuse),
            "index.html": index_html,
            "style.css": css,
        }
        for rel, content in payloads.items():
            target = files_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(rel)

        assets_dir = files_root / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / ".gitkeep").write_text("", encoding="utf-8")
        written.append("assets/")

        preview_dir = self._workspaces.path_for(workspace_id, "artifacts", "preview")
        if preview_dir.exists():
            shutil.rmtree(preview_dir)
        preview_dir.mkdir(parents=True, exist_ok=True)
        for rel in ("brief.md", "index.html", "style.css"):
            shutil.copy2(files_root / rel, preview_dir / rel)
        shutil.copytree(assets_dir, preview_dir / "assets", dirs_exist_ok=True)
        written.append("preview/")

        manifest = {
            "artifact_id": artifact_id,
            "capability_id": "generate_site",
            "files": list(written),
            "business_name": analysis.business_name,
            "niche": analysis.niche,
            "reuse": reuse.to_dict(),
        }
        (files_root / "site_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        written.append("site_manifest.json")
        manifest["files"] = list(written)

        manifest_path = self._workspaces.path_for(workspace_id, "artifacts", f"{artifact_id}.json")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        preview_url = f"/api/public/execution/preview/{workspace_id}"
        result = CapabilityResult(
            workspace_id=workspace_id,
            artifact_id=artifact_id,
            files=written,
            artifacts=[
                CapabilityArtifact(
                    id=artifact_id,
                    kind="bundle",
                    path="artifacts/preview",
                    label=analysis.business_name,
                ),
                CapabilityArtifact(
                    id=f"{artifact_id}-index",
                    kind="file",
                    path="files/index.html",
                    label="index.html",
                ),
            ],
            preview_url=preview_url,
            logs=logs,
            status="completed",
            capability_id="generate_site",
            reused_capabilities=reuse.reused_capabilities,
            reuse_score=reuse.reuse_score,
            source_files=reuse.source_files,
        )
        self._workspaces.touch(workspace_id)
        return result.to_dict()

    def rollback(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        workspace_id = str(outputs.get("workspace_id") or inputs.get("workspace_id") or "")
        if not workspace_id:
            return
        for rel in ("brief.md", "index.html", "style.css", "site_manifest.json"):
            path = self._workspaces.path_for(workspace_id, "files", rel)
            if path.is_file():
                path.unlink()
        preview = self._workspaces.path_for(workspace_id, "artifacts", "preview")
        if preview.is_dir():
            shutil.rmtree(preview, ignore_errors=True)
        artifact_id = str(outputs.get("artifact_id") or "")
        if artifact_id:
            manifest = self._workspaces.path_for(workspace_id, "artifacts", f"{artifact_id}.json")
            if manifest.is_file():
                manifest.unlink()
