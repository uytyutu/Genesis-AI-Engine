"""Farm Opire capability snapshot — Virtus stack + task-type matrix."""

from __future__ import annotations

import re
from typing import Any

# Languages / stacks Virtus Farm can reasonably attempt.
VIRTUS_FARM_CAPABILITIES: frozenset[str] = frozenset(
    {
        "python",
        "fastapi",
        "pytest",
        "javascript",
        "typescript",
        "react",
        "nextjs",
        "next.js",
        "html",
        "css",
        "tailwind",
        "markdown",
        "mdx",
        "shell",
        "bash",
        "docker",
        "github-actions",
        "ci",
        "docs",
        "documentation",
        "testing",
        "bugfix",
        "stripe",
        "smtp",
        "pdf",
        "vue",
        "sql",
        "csv",
        "translation",
        "writing",
        "readme",
    }
)

# Capability Matrix — what Virtus can auto-attempt (Opire Farm only).
# severity: ✅ auto · ⚠️ conditional · ❌ never
CAPABILITY_MATRIX: list[dict[str, Any]] = [
    {"id": "bug_fix", "label": "Bug Fix", "auto": "✅"},
    {"id": "documentation", "label": "Documentation", "auto": "✅"},
    {"id": "readme", "label": "README", "auto": "✅"},
    {"id": "api_docs", "label": "API Docs", "auto": "✅"},
    {"id": "unit_tests", "label": "Unit Tests", "auto": "✅"},
    {"id": "refactoring", "label": "Refactoring", "auto": "✅"},
    {"id": "ci_cd", "label": "CI/CD", "auto": "✅"},
    {"id": "tech_article", "label": "Technical Article", "auto": "✅"},
    {"id": "translation", "label": "Translation", "auto": "✅"},
    {"id": "seo_article", "label": "SEO Article", "auto": "⚠️", "note_ru": "Только если правила площадки позволяют AI"},
    {"id": "research", "label": "Research", "auto": "✅"},
    {"id": "frontend", "label": "Frontend (HTML/CSS/React)", "auto": "✅"},
    {"id": "data", "label": "Data / CSV / SQL report", "auto": "✅"},
    {"id": "video", "label": "Video Editing", "auto": "⚠️"},
    {"id": "graphic", "label": "Graphic Design", "auto": "⚠️"},
    {"id": "human_interview", "label": "Human Interview", "auto": "❌"},
]

_TASK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("human_interview", re.compile(r"\binterview\b|call with|zoom meeting", re.I)),
    ("readme", re.compile(r"\breadme\b", re.I)),
    ("api_docs", re.compile(r"api\s*doc|openapi|swagger", re.I)),
    ("documentation", re.compile(r"\bdocs?\b|documentation|user guide|wiki|changelog", re.I)),
    ("unit_tests", re.compile(r"\bunit\s*test|add tests?|pytest|coverage", re.I)),
    ("ci_cd", re.compile(r"\bci\b|github actions|workflow|cd pipeline", re.I)),
    ("translation", re.compile(r"translat|i18n|localization|l10n", re.I)),
    ("seo_article", re.compile(r"\bseo\b|blog post|article for", re.I)),
    ("tech_article", re.compile(r"technical (writer|article|blog)|write.?up", re.I)),
    ("refactoring", re.compile(r"refactor", re.I)),
    ("frontend", re.compile(r"\breact\b|\bvue\b|tailwind|css|html component", re.I)),
    ("data", re.compile(r"\bcsv\b|\bsql\b|etl|dataset|spreadsheet", re.I)),
    ("research", re.compile(r"\bresearch\b|investigate|spike", re.I)),
    ("bug_fix", re.compile(r"\bfix\b|bug|race|leak|error|crash|typo", re.I)),
]


def detect_task_type(title: str, languages: list[str] | None = None) -> str:
    text = title or ""
    for tid, pat in _TASK_PATTERNS:
        if pat.search(text):
            return tid
    langs = {str(x).lower() for x in (languages or [])}
    if langs & {"html", "css", "react", "vue", "typescript", "javascript"}:
        return "frontend"
    if langs & {"markdown", "mdx"}:
        return "documentation"
    return "bug_fix" if text else "research"


def task_type_auto_ok(task_type: str) -> dict[str, Any]:
    row = next((r for r in CAPABILITY_MATRIX if r["id"] == task_type), None)
    if not row:
        return {
            "ok": True,
            "severity": "✅",
            "task_type": task_type,
            "note_ru": "Тип не в матрице — допустим как code/docs fallback",
        }
    auto = str(row.get("auto") or "✅")
    return {
        "ok": auto == "✅",
        "severity": auto,
        "task_type": task_type,
        "label": row.get("label"),
        "note_ru": row.get("note_ru")
        or (
            "Автоматически"
            if auto == "✅"
            else (
                "Условно — проверь правила площадки"
                if auto == "⚠️"
                else "Не берём автоматически"
            )
        ),
    }


def capability_snapshot() -> dict:
    return {
        "ok": True,
        "engine": "virtus_farm_capabilities_v1",
        "capabilities": sorted(VIRTUS_FARM_CAPABILITIES),
        "matrix": CAPABILITY_MATRIX,
        "contours_ru": {
            "opire_farm": "Исполняет bounty (код, docs, tests) → Draft PR → Payout",
            "alpha_hunter": "Ищет новые рынки / площадки (не выполняет Opire)",
            "sales_farm": "Country Desk → клиент → Stripe → Factory → REAL €",
        },
        "note_ru": (
            "Capability Matrix для Opire Farm. Alpha Hunter и Sales Farm — "
            "отдельные контуры, не смешивать с bounty Execution."
        ),
    }
