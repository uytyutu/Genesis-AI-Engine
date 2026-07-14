"""Load and reuse prior capability artifacts from workspace (Rule №4)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.execution.workspace import ExecutionWorkspaceStore
from app.factory.analyzer import AnalysisResult, analyze

_STRUCTURE_FILE = "document_structure.json"
_SUMMARY_FILE = "executive_summary.md"
_REPORT_FILE = "report.md"


@dataclass
class ReuseContext:
    reused_capabilities: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)

    @property
    def reuse_score(self) -> int:
        return len(self.reused_capabilities)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reused_capabilities": list(self.reused_capabilities),
            "source_files": list(self.source_files),
            "reuse_score": self.reuse_score,
        }


def load_workspace_building_blocks(
    workspace_store: ExecutionWorkspaceStore,
    workspace_id: str,
) -> dict[str, Any]:
    """Read composable artifacts produced by earlier capabilities in this workspace."""
    files_root = workspace_store.path_for(workspace_id, "files")
    blocks: dict[str, Any] = {}
    structure_path = files_root / _STRUCTURE_FILE
    if structure_path.is_file():
        try:
            blocks["document_structure"] = json.loads(structure_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    summary_path = files_root / _SUMMARY_FILE
    if summary_path.is_file():
        try:
            blocks["executive_summary"] = summary_path.read_text(encoding="utf-8")
        except OSError:
            pass
    report_path = files_root / _REPORT_FILE
    if report_path.is_file():
        try:
            blocks["report_md"] = report_path.read_text(encoding="utf-8")
        except OSError:
            pass
    return blocks


def _niche_from_text(*chunks: str) -> str:
    blob = " ".join(c for c in chunks if c).lower()
    if any(w in blob for w in ("стоматолог", "dental", "зуб", "клиник", "имплант")):
        return "dental"
    if any(w in blob for w in ("автосервис", "авто", "машин", "garage", "шиномонтаж")):
        return "auto"
    if any(w in blob for w in ("салон", "красот", "spa", "маникюр")):
        return "beauty"
    return "generic"


def _summary_line(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("*") or s.startswith("-"):
            continue
        s = re.sub(r"^\*\*|\*\*$", "", s).strip()
        if len(s) > 15:
            return s[:220]
    return ""


def analysis_for_site(
    goal: str,
    blocks: dict[str, Any],
) -> tuple[AnalysisResult, ReuseContext]:
    """
    Build landing AnalysisResult — reuse document analysis when present, else goal-only.
    """
    reuse = ReuseContext()
    fallback = analyze(goal)

    structure_payload = blocks.get("document_structure")
    if not structure_payload:
        return fallback, reuse

    reuse.reused_capabilities.append("analyze_business_document")
    reuse.source_files.append(f"files/{_STRUCTURE_FILE}")

    analysis = structure_payload.get("analysis") or {}
    structure = analysis.get("structure") or {}
    title = str(structure.get("title") or fallback.business_name).strip()[:80]
    doc_type = str(structure.get("document_type") or "")

    swot = analysis.get("swot") or {}
    strengths = list(analysis.get("strengths") or swot.get("strengths") or [])
    market_notes = list(analysis.get("market_notes") or [])
    recommendations = list(analysis.get("recommendations") or [])

    services: list[str] = []
    for item in strengths + recommendations:
        s = str(item).strip()[:120]
        if s and s not in services:
            services.append(s)
        if len(services) >= 4:
            break
    if len(services) < 2:
        services = list(fallback.services)

    subtitle = ""
    if blocks.get("executive_summary"):
        reuse.reused_capabilities.append("executive_summary")
        reuse.source_files.append(f"files/{_SUMMARY_FILE}")
        subtitle = _summary_line(str(blocks["executive_summary"]))
    if not subtitle and market_notes:
        subtitle = str(market_notes[0])[:220]
    if not subtitle:
        for sec in structure.get("sections") or []:
            if isinstance(sec, dict) and sec.get("excerpt"):
                subtitle = str(sec["excerpt"])[:220]
                break
    if not subtitle:
        subtitle = fallback.subtitle

    niche = _niche_from_text(title, doc_type, goal, blocks.get("report_md", ""))
    niche_base = analyze(f"сайт для {title} {niche}")

    return AnalysisResult(
        niche=niche,
        template_id=f"landing-{niche}-v1",
        business_name=title,
        headline=title,
        subtitle=subtitle,
        services=services,
        service_descriptions=niche_base.service_descriptions,
        cta_label=niche_base.cta_label,
        trust_points=niche_base.trust_points,
        about_text=niche_base.about_text,
        benefits=niche_base.benefits,
        hours=niche_base.hours,
        phone=niche_base.phone,
        email=niche_base.email,
    ), reuse


def format_reuse_explanation(cap: dict[str, Any]) -> str:
    """Rule №7 — Explain Reuse for chat (not just a score)."""
    score = int(cap.get("reuse_score") or 0)
    if score <= 0:
        return ""

    lines = [
        "Использую информацию из вашего проекта — повторно описывать бизнес не нужно.",
        "",
        "**Учтено из проекта:**",
    ]
    path_labels = {
        "files/document_structure.json": "структура бизнеса",
        "files/executive_summary.md": "краткое резюме",
        "files/report.md": "анализ документа",
        "files/site_manifest.json": "данные предыдущего сайта",
    }
    used_files = [
        path_labels.get(p, "данные проекта")
        for p in (cap.get("source_files") or [])
    ]
    if not used_files and cap.get("reused_capabilities"):
        for cap_id in cap.get("reused_capabilities") or []:
            if cap_id == "analyze_business_document":
                used_files.extend(["структура бизнеса", "анализ документа"])
            elif cap_id == "executive_summary":
                used_files.append("краткое резюме")
        used_files = list(dict.fromkeys(used_files))

    lines.extend(f"✓ {name}" for name in used_files[:6] if name)
    if len(lines) <= 3:
        lines.append("✓ материалы вашего проекта")
    return "\n".join(lines)


def brief_with_reuse(
    goal: str,
    analysis: AnalysisResult,
    reuse: ReuseContext,
) -> str:
    services = "\n".join(f"- {s}" for s in analysis.services)
    reuse_note = ""
    if reuse.reuse_score > 0:
        sources = ", ".join(f"`{p}`" for p in reuse.source_files)
        reuse_note = f"""
## Источник данных (Reuse)
Сайт построен на основе предыдущего анализа в этом workspace: {sources}.
Повторные вопросы о рынке и позиционировании не задавались — данные взяты из артефактов.
"""
    return f"""# Project brief

## Запрос
{goal.strip()}
{reuse_note}
## Бизнес
- **Название:** {analysis.business_name}
- **Ниша:** {analysis.niche}
- **Шаблон:** {analysis.template_id}

## Позиционирование
**{analysis.headline}**

{analysis.subtitle}

## Услуги
{services}

## CTA
{analysis.cta_label}

---
Создано Vector (Virtus Core).
"""
