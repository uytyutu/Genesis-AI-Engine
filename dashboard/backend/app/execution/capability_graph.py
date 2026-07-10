"""Capability Graph — Rule №5: every capability declares Produces / Consumes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

CapabilityStatus = Literal["ready", "planned", "internal"]


@dataclass(frozen=True)
class ArtifactSpec:
    """Workspace artifact path (relative to files/ or artifacts/)."""

    path: str
    description: str = ""
    optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityNode:
    id: str
    label: str
    produces: tuple[ArtifactSpec, ...]
    consumes: tuple[ArtifactSpec, ...]
    status: CapabilityStatus = "ready"
    reuse_score_when_wired: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "produces": [a.to_dict() for a in self.produces],
            "consumes": [a.to_dict() for a in self.consumes],
            "reuse_score_when_wired": self.reuse_score_when_wired,
        }


# Canonical graph — planner reads this, not prompts.
CAPABILITY_GRAPH: tuple[CapabilityNode, ...] = (
    CapabilityNode(
        id="filesystem_write",
        label="Создавать документ по запросу",
        consumes=(
            ArtifactSpec("user.goal", "Текст запроса пользователя"),
        ),
        produces=(
            ArtifactSpec("files/{path}", "Созданный файл в workspace"),
        ),
        status="ready",
    ),
    CapabilityNode(
        id="analyze_business_document",
        label="Анализировать бизнес-документы",
        consumes=(
            ArtifactSpec("uploads/*", "Загруженный PDF/документ", optional=False),
            ArtifactSpec("user.goal", "Запрос на анализ", optional=True),
        ),
        produces=(
            ArtifactSpec("files/document_structure.json", "Структура, SWOT, темы — building block"),
            ArtifactSpec("files/executive_summary.md", "Краткое резюме для CEO"),
            ArtifactSpec("files/report.md", "Полный отчёт"),
            ArtifactSpec("files/uploads/*", "Копия исходника"),
            ArtifactSpec("artifacts/doc-*.json", "Manifest анализа"),
        ),
        status="ready",
    ),
    CapabilityNode(
        id="generate_site",
        label="Создавать сайт по запросу",
        consumes=(
            ArtifactSpec("user.goal", "Запрос (например «Создай сайт»)"),
            ArtifactSpec("files/document_structure.json", "Из анализа — рынок, SWOT, услуги", optional=True),
            ArtifactSpec("files/executive_summary.md", "Позиционирование из анализа", optional=True),
            ArtifactSpec("files/brand_profile.json", "Бренд-профиль", optional=True),
        ),
        produces=(
            ArtifactSpec("files/brief.md", "Brief проекта"),
            ArtifactSpec("files/index.html", "Главная страница"),
            ArtifactSpec("files/style.css", "Стили"),
            ArtifactSpec("files/assets/", "Статические assets"),
            ArtifactSpec("artifacts/preview/", "Preview bundle"),
            ArtifactSpec("files/site_manifest.json", "Manifest сайта — building block"),
            ArtifactSpec("artifacts/site-*.json", "Manifest в artifacts/"),
        ),
        status="ready",
        reuse_score_when_wired=2,
    ),
    CapabilityNode(
        id="generate_proposal",
        label="Создавать коммерческое предложение",
        consumes=(
            ArtifactSpec("files/report.md", "Анализ"),
            ArtifactSpec("files/executive_summary.md", "Резюме"),
            ArtifactSpec("files/site_manifest.json", "Данные сайта", optional=True),
        ),
        produces=(
            ArtifactSpec("files/proposal.md", "Черновик КП"),
            ArtifactSpec("files/proposal.pdf", "PDF КП"),
        ),
        status="planned",
    ),
    CapabilityNode(
        id="generate_presentation",
        label="Создавать презентацию",
        consumes=(
            ArtifactSpec("files/report.md", "Анализ"),
            ArtifactSpec("files/site_manifest.json", "Сайт", optional=True),
        ),
        produces=(
            ArtifactSpec("files/presentation.md", "Структура слайдов"),
        ),
        status="planned",
    ),
    CapabilityNode(
        id="dev_project",
        label="Работать с проектами разработки",
        consumes=(
            ArtifactSpec("workspace.logs", "Логи проекта"),
            ArtifactSpec("files/**", "Исходники в workspace"),
        ),
        produces=(
            ArtifactSpec("files/diff.patch", "Предлагаемые изменения"),
            ArtifactSpec("files/test_results.json", "Результаты тестов"),
        ),
        status="planned",
    ),
)


def graph_snapshot() -> dict[str, Any]:
    return {
        "version": "capability-graph-v1",
        "rule": "Each capability declares produces and consumes — planner uses graph, not prompts.",
        "nodes": [n.to_dict() for n in CAPABILITY_GRAPH],
    }


def get_node(capability_id: str) -> CapabilityNode | None:
    for node in CAPABILITY_GRAPH:
        if node.id == capability_id:
            return node
    return None


def _workspace_has(rel_path: str, present: set[str]) -> bool:
    if rel_path in present:
        return True
    if rel_path.endswith("/"):
        return any(p.startswith(rel_path) for p in present)
    if "*" in rel_path:
        prefix = rel_path.split("*")[0]
        return any(p.startswith(prefix) for p in present)
    return False


def suggest_next_capabilities(workspace_file_paths: list[str]) -> list[dict[str, Any]]:
    """
    Given files present in workspace, suggest capabilities whose required consumes are met.
    For future TaskPlannerV3 — not wired to chat yet.
    """
    present = set(workspace_file_paths)
    suggestions: list[dict[str, Any]] = []
    for node in CAPABILITY_GRAPH:
        if node.status != "ready":
            continue
        required = [c for c in node.consumes if not c.optional and not c.path.startswith("user.")]
        if not required:
            continue
        if all(_workspace_has(c.path.replace("files/", ""), present) for c in required):
            continue
        optional_boost = [
            c.path for c in node.consumes if c.optional and _workspace_has(c.path.replace("files/", ""), present)
        ]
        missing = [
            c.path
            for c in required
            if not _workspace_has(c.path.replace("files/", ""), present)
        ]
        if missing and node.id == "generate_site":
            # Site can run without analysis — only suggest analyze if user path needs report
            if "document_structure.json" in str(missing):
                suggestions.append(
                    {
                        "capability_id": node.id,
                        "reason": "optional_reuse_available",
                        "optional_inputs_present": optional_boost,
                    }
                )
            continue
        if not missing:
            suggestions.append(
                {
                    "capability_id": node.id,
                    "reason": "consumes_satisfied",
                    "reuse_inputs": optional_boost,
                }
            )
    return suggestions


def workflow_chain_open_clinic() -> list[dict[str, str]]:
    """Reference chain for «Открой стоматологическую клинику» — planner target."""
    return [
        {"step": "analyze_business_document", "until": "files/report.md"},
        {"step": "generate_site", "until": "files/site_manifest.json"},
        {"step": "generate_presentation", "until": "files/presentation.md"},
        {"step": "generate_proposal", "until": "files/proposal.pdf"},
    ]
