"""Business document intelligence — classify, structure, analyze (Commit 3)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DocumentSection:
    title: str
    excerpt: str
    line_start: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentStructure:
    document_type: str
    title: str
    filename: str
    word_count: int
    page_count: int
    pages_analyzed: int
    sections: list[DocumentSection] = field(default_factory=list)
    detected_topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_type": self.document_type,
            "title": self.title,
            "filename": self.filename,
            "word_count": self.word_count,
            "page_count": self.page_count,
            "pages_analyzed": self.pages_analyzed,
            "sections": [s.to_dict() for s in self.sections],
            "detected_topics": self.detected_topics,
        }


@dataclass
class DocumentAnalysis:
    structure: DocumentStructure
    executive_summary: str
    swot: dict[str, list[str]]
    strengths: list[str]
    weaknesses: list[str]
    risks: list[str]
    market_notes: list[str]
    finance_notes: list[str]
    recommendations: list[str]
    open_questions: list[str]
    evidence_quotes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure": self.structure.to_dict(),
            "executive_summary": self.executive_summary,
            "swot": self.swot,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "risks": self.risks,
            "market_notes": self.market_notes,
            "finance_notes": self.finance_notes,
            "recommendations": self.recommendations,
            "open_questions": self.open_questions,
            "evidence_quotes": self.evidence_quotes,
        }


_TYPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("business_plan", ("бизнес-план", "business plan", "бизнес план", "startup plan", "план развития")),
    ("commercial_proposal", ("коммерческ", "предложен", "proposal", "кп ", "offer")),
    ("financial_report", ("финансов", "отчёт", "отчет", "balance", "p&l", "выручк")),
    ("market_research", ("исследован", "рынок", "market research", "конкурент")),
)

_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "market": ("рынок", "market", "конкурент", "ниша", "спрос", "аудитор"),
    "finance": ("финанс", "выручк", "прибыл", "бюджет", "инвест", "revenue", "profit", "cash"),
    "product": ("продукт", "услуг", "product", "service", "решени"),
    "team": ("команд", "team", "основател", "персонал"),
    "strategy": ("стратег", "strategy", "миссия", "vision", "цел"),
    "risks": ("риск", "угроз", "risk", "опасност"),
}

_SWOT_HINTS: dict[str, tuple[str, ...]] = {
    "strengths": ("сильн", "преимуществ", "strong", "advantage", "уникальн", "опыт"),
    "weaknesses": ("слаб", "недостат", "weak", "пробел", "не хватает"),
    "opportunities": ("возможност", "потенциал", "opportunit", "рост", "тренд"),
    "threats": ("угроз", "риск", "threat", "конкурент", "регулятор"),
}


def classify_document(text: str, *, filename: str = "", goal: str = "") -> str:
    blob = f"{filename} {goal} {text[:4000]}".lower()
    for doc_type, words in _TYPE_RULES:
        if any(w in blob for w in words):
            return doc_type
    return "general_business_document"


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _find_sentences(text: str, keywords: tuple[str, ...], *, limit: int = 5) -> list[str]:
    sentences = _split_sentences(text)
    hits: list[str] = []
    for s in sentences:
        low = s.lower()
        if any(k in low for k in keywords):
            hits.append(s[:400])
        if len(hits) >= limit:
            break
    return hits


def _detect_sections(text: str) -> list[DocumentSection]:
    sections: list[DocumentSection] = []
    lines = text.splitlines()
    current_title = "Введение"
    buffer: list[str] = []
    line_no = 0

    def flush() -> None:
        nonlocal buffer, current_title, line_no
        excerpt = "\n".join(buffer).strip()
        if excerpt:
            sections.append(
                DocumentSection(title=current_title, excerpt=excerpt[:1200], line_start=line_no)
            )
        buffer = []

    heading_re = re.compile(
        r"^(?:\d+[\.\)]\s+|[#]+\s*)?([A-ZА-ЯЁ][\w\s\-]{3,60})$"
    )
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
        if len(line) < 80 and heading_re.match(line):
            flush()
            current_title = line[:80]
            line_no = i + 1
            continue
        buffer.append(line)
        if len(buffer) > 40:
            flush()
    flush()
    if not sections and text.strip():
        sections.append(DocumentSection(title="Содержание", excerpt=text[:2000]))
    return sections[:12]


def _detect_topics(text: str) -> list[str]:
    low = text.lower()
    return [topic for topic, words in _TOPIC_KEYWORDS.items() if any(w in low for w in words)]


def _infer_title(text: str, filename: str, doc_type: str) -> str:
    for line in text.splitlines()[:8]:
        s = line.strip()
        if 5 < len(s) < 120 and not s.endswith("."):
            return s
    base = PathStem(filename) if filename else doc_type.replace("_", " ").title()
    return base or "Документ"


def PathStem(name: str) -> str:
    return re.sub(r"\.[^.]+$", "", name).replace("_", " ").strip()


def build_structure(
    text: str,
    *,
    filename: str = "",
    goal: str = "",
    page_count: int = 0,
    pages_analyzed: int = 0,
) -> DocumentStructure:
    doc_type = classify_document(text, filename=filename, goal=goal)
    words = len(re.findall(r"\w+", text, flags=re.UNICODE))
    return DocumentStructure(
        document_type=doc_type,
        title=_infer_title(text, filename, doc_type),
        filename=filename or "document.pdf",
        word_count=words,
        page_count=page_count,
        pages_analyzed=pages_analyzed,
        sections=_detect_sections(text),
        detected_topics=_detect_topics(text),
    )


def analyze_document(
    text: str,
    *,
    filename: str = "",
    goal: str = "",
    page_count: int = 0,
    pages_analyzed: int = 0,
) -> DocumentAnalysis:
    structure = build_structure(
        text,
        filename=filename,
        goal=goal,
        page_count=page_count,
        pages_analyzed=pages_analyzed,
    )
    strengths = _find_sentences(text, _SWOT_HINTS["strengths"])
    weaknesses = _find_sentences(text, _SWOT_HINTS["weaknesses"])
    opportunities = _find_sentences(text, _SWOT_HINTS["opportunities"])
    threats = _find_sentences(text, _SWOT_HINTS["threats"])
    market_notes = _find_sentences(text, _TOPIC_KEYWORDS["market"])
    finance_notes = _find_sentences(text, _TOPIC_KEYWORDS["finance"])
    risks = _find_sentences(text, _TOPIC_KEYWORDS["risks"], limit=6) or threats[:4]

    swot = {
        "strengths": strengths or ["В документе мало явных формулировок о сильных сторонах."],
        "weaknesses": weaknesses or ["Слабые стороны не выделены явно — нужны уточнения."],
        "opportunities": opportunities or ["Потенциал роста требует отдельной проработки."],
        "threats": threats or risks or ["Внешние угрозы не описаны подробно."],
    }

    recommendations: list[str] = []
    if not finance_notes:
        recommendations.append("Добавить финансовую модель: выручка, расходы, точка безубыточности.")
    if not market_notes:
        recommendations.append("Расширить раздел о рынке: конкуренты, сегмент, размер рынка.")
    if structure.word_count < 400:
        recommendations.append("Документ короткий — добавьте детали по продукту, команде и go-to-market.")
    if not recommendations:
        recommendations.append("Сфокусироваться на 2–3 приоритетах из SWOT и зафиксировать KPI на 90 дней.")

    open_questions: list[str] = []
    if structure.word_count < 800:
        open_questions.append("Какова целевая аудитория и подтверждённый спрос?")
    if not finance_notes:
        open_questions.append("Какие допущения заложены в финансовый прогноз?")
    if not market_notes:
        open_questions.append("Кто основные конкуренты и чем вы отличаетесь?")
    if "team" not in structure.detected_topics:
        open_questions.append("Какой состав команды и ключевые роли?")

    evidence = (strengths + market_notes + finance_notes)[:5]
    type_label = {
        "business_plan": "бизнес-план",
        "commercial_proposal": "коммерческое предложение",
        "financial_report": "финансовый отчёт",
        "market_research": "исследование рынка",
        "general_business_document": "бизнес-документ",
    }.get(structure.document_type, structure.document_type)

    summary_lines = [
        f"**{structure.title}** — проанализирован как {type_label}.",
        f"Объём: ~{structure.word_count} слов"
        + (f", страниц в документе: {page_count}" if page_count else "")
        + ".",
    ]
    if market_notes:
        summary_lines.append(f"Рынок: {market_notes[0][:200]}")
    if finance_notes:
        summary_lines.append(f"Финансы: {finance_notes[0][:200]}")
    if risks:
        summary_lines.append(f"Ключевой риск: {risks[0][:200]}")
    summary_lines.append("Полный разбор — в `report.md`.")

    return DocumentAnalysis(
        structure=structure,
        executive_summary="\n\n".join(summary_lines),
        swot=swot,
        strengths=strengths,
        weaknesses=weaknesses,
        risks=risks,
        market_notes=market_notes,
        finance_notes=finance_notes,
        recommendations=recommendations,
        open_questions=open_questions,
        evidence_quotes=evidence,
    )


def render_executive_summary_md(analysis: DocumentAnalysis, *, source_filename: str) -> str:
    s = analysis.structure
    return f"""# Executive Summary

**Документ:** {s.title}  
**Файл:** {source_filename}  
**Тип:** {s.document_type}  
**Слов:** {s.word_count}

---

{analysis.executive_summary}

## Ключевые выводы

- **Сильные стороны:** {len(analysis.strengths)} формулировок из текста документа
- **Риски:** {len(analysis.risks)} пунктов
- **Рекомендации:** {len(analysis.recommendations)} действий

---
*Создано Vector (Virtus Core) — анализ на основе извлечённого текста документа.*
"""


def render_report_md(analysis: DocumentAnalysis, *, source_filename: str) -> str:
    s = analysis.structure

    def bullets(items: list[str]) -> str:
        if not items:
            return "- —\n"
        return "\n".join(f"- {item}" for item in items) + "\n"

    def swot_block(key: str, title: str) -> str:
        return f"### {title}\n{bullets(analysis.swot.get(key, []))}"

    sections_block = ""
    if s.sections:
        sections_block = "## Структура документа\n\n"
        for sec in s.sections[:8]:
            sections_block += f"### {sec.title}\n{sec.excerpt[:500]}\n\n"

    evidence = ""
    if analysis.evidence_quotes:
        evidence = "## Цитаты из документа\n\n" + bullets(analysis.evidence_quotes)

    return f"""# Отчёт по документу

**Документ:** {s.title}  
**Файл:** {source_filename}  
**Тип:** {s.document_type}  
**Темы:** {", ".join(s.detected_topics) or "не определены"}

---

## SWOT

{swot_block("strengths", "Strengths (сильные стороны)")}
{swot_block("weaknesses", "Weaknesses (слабые стороны)")}
{swot_block("opportunities", "Opportunities (возможности)")}
{swot_block("threats", "Threats (угрозы)")}

## Рынок

{bullets(analysis.market_notes)}

## Финансы

{bullets(analysis.finance_notes)}

## Риски

{bullets(analysis.risks)}

## Рекомендации

{bullets(analysis.recommendations)}

## Вопросы при недостатке данных

{bullets(analysis.open_questions)}

{sections_block}
{evidence}
---
*Vector проанализировал извлечённый текст файла `{source_filename}` — не шаблонный ответ.*
"""


def structure_json(analysis: DocumentAnalysis) -> str:
    payload = {
        "version": "document-structure-v1",
        "analysis": analysis.to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
