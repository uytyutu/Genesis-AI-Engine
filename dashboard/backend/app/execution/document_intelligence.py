"""Business document intelligence — classify, structure, analyze (Commit 3 + 3.1)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

# Commit 3.1 — full-document analysis for execution (not Brain 5-page intake cap).
_MAX_ANALYSIS_TEXT_CHARS = 120_000


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
    # Commit 3.1 — investor-grade outputs
    report_locale: str = "ru"
    readiness_score: int = 0
    readiness_explanation: str = ""
    launch_probability_pct: int = 0
    verdict: str = ""
    main_advantage: str = ""
    main_risk: str = ""
    priority_actions: list[str] = field(default_factory=list)

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
            "report_locale": self.report_locale,
            "readiness_score": self.readiness_score,
            "readiness_explanation": self.readiness_explanation,
            "launch_probability_pct": self.launch_probability_pct,
            "verdict": self.verdict,
            "main_advantage": self.main_advantage,
            "main_risk": self.main_risk,
            "priority_actions": self.priority_actions,
        }


_TYPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("business_plan", ("бизнес-план", "business plan", "бизнес план", "startup plan", "план развития", "geschäftsplan")),
    ("commercial_proposal", ("коммерческ", "предложен", "proposal", "кп ", "offer", "angebot")),
    ("financial_report", ("финансов", "отчёт", "отчет", "balance", "p&l", "выручк", "jahresabschluss")),
    ("market_research", ("исследован", "рынок", "market research", "конкурент", "marktforschung")),
)

_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "market": ("рынок", "market", "конкурент", "ниша", "спрос", "аудитор", "markt", "wettbewerb"),
    "finance": ("финанс", "выручк", "прибыл", "бюджет", "инвест", "revenue", "profit", "cash", "umsatz", "gewinn"),
    "product": ("продукт", "услуг", "product", "service", "решени", "dienstleist"),
    "team": ("команд", "team", "основател", "персонал", "mitarbeiter", "gründer"),
    "strategy": ("стратег", "strategy", "миссия", "vision", "цел", "strategie"),
    "risks": ("риск", "угроз", "risk", "опасност", "risiko", "bedrohung"),
}

_SWOT_SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "strengths": re.compile(
        r"(?:сильн|преимуществ|strength|vorteil|stärk|competitive advantage)",
        re.IGNORECASE,
    ),
    "weaknesses": re.compile(
        r"(?:слаб|недостат|weak|nachteil|schwäche|пробел)",
        re.IGNORECASE,
    ),
    "opportunities": re.compile(
        r"(?:возможност|потенциал|opportunit|chance|wachstum|рост)",
        re.IGNORECASE,
    ),
    "threats": re.compile(
        r"(?:угроз|threat|bedrohung|risiko|конкурент)",
        re.IGNORECASE,
    ),
}

_SWOT_LINE_HINTS: dict[str, tuple[str, ...]] = {
    "strengths": ("сильн", "преимуществ", "strong", "advantage", "уникальн", "опыт", "vorteil", "stärk"),
    "weaknesses": ("слаб", "недостат", "weak", "пробел", "не хватает", "schwäche", "nachteil"),
    "opportunities": ("возможност", "потенциал", "opportunit", "рост", "тренд", "chance", "wachstum"),
    "threats": ("угроз", "риск", "threat", "конкурент", "регулятор", "risiko", "bedrohung"),
}

_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "exec_title": "Executive Summary",
        "verdict": "Вердикт",
        "readiness": "Готовность проекта",
        "main_adv": "Главное преимущество",
        "main_risk": "Главный риск",
        "next_steps": "Следующие шаги",
        "launch_prob": "Вероятность успешного запуска",
        "report_title": "Отчёт по документу",
        "priorities": "Что исправить в первую очередь",
        "swot": "SWOT-анализ",
        "strengths": "Сильные стороны",
        "weaknesses": "Слабые стороны",
        "opportunities": "Возможности",
        "threats": "Угрозы",
        "market": "Рынок",
        "finance": "Финансы",
        "risks": "Риски",
        "recommendations": "Рекомендации",
        "questions": "Вопросы при недостатке данных",
        "structure": "Структура документа",
        "quotes": "Цитаты из документа (оригинал)",
        "topics": "Темы",
        "footer": "Vector (Virtus Core) — анализ на основе извлечённого текста документа.",
        "doc_label": "Документ",
        "file_label": "Файл",
        "type_label": "Тип",
        "words_label": "Слов",
        "pages_label": "Страниц проанализировано",
        "viable": "Проект выглядит жизнеспособным при устранении ключевых пробелов.",
        "needs_work": "Проект требует доработки перед презентацией инвестору или партнёру.",
        "early": "Идея на ранней стадии — нужна проработка модели и подтверждение спроса.",
    },
    "en": {
        "exec_title": "Executive Summary",
        "verdict": "Verdict",
        "readiness": "Project readiness",
        "main_adv": "Main advantage",
        "main_risk": "Main risk",
        "next_steps": "Next steps",
        "launch_prob": "Launch success probability",
        "report_title": "Document report",
        "priorities": "Top priorities",
        "swot": "SWOT analysis",
        "strengths": "Strengths",
        "weaknesses": "Weaknesses",
        "opportunities": "Opportunities",
        "threats": "Threats",
        "market": "Market",
        "finance": "Finance",
        "risks": "Risks",
        "recommendations": "Recommendations",
        "questions": "Open questions",
        "structure": "Document structure",
        "quotes": "Quotes from document (original)",
        "topics": "Topics",
        "footer": "Vector (Virtus Core) — analysis based on extracted document text.",
        "doc_label": "Document",
        "file_label": "File",
        "type_label": "Type",
        "words_label": "Words",
        "pages_label": "Pages analyzed",
        "viable": "The project appears viable if key gaps are addressed.",
        "needs_work": "The project needs work before investor or partner presentation.",
        "early": "Early-stage idea — validate demand and refine the model.",
    },
    "de": {
        "exec_title": "Executive Summary",
        "verdict": "Urteil",
        "readiness": "Projektreife",
        "main_adv": "Hauptvorteil",
        "main_risk": "Hauptrisiko",
        "next_steps": "Nächste Schritte",
        "launch_prob": "Wahrscheinlichkeit eines erfolgreichen Starts",
        "report_title": "Dokumentbericht",
        "priorities": "Top-Prioritäten",
        "swot": "SWOT-Analyse",
        "strengths": "Stärken",
        "weaknesses": "Schwächen",
        "opportunities": "Chancen",
        "threats": "Bedrohungen",
        "market": "Markt",
        "finance": "Finanzen",
        "risks": "Risiken",
        "recommendations": "Empfehlungen",
        "questions": "Offene Fragen",
        "structure": "Dokumentstruktur",
        "quotes": "Zitate aus dem Dokument (Original)",
        "topics": "Themen",
        "footer": "Vector (Virtus Core) — Analyse auf Basis des extrahierten Dokumenttexts.",
        "doc_label": "Dokument",
        "file_label": "Datei",
        "type_label": "Typ",
        "words_label": "Wörter",
        "pages_label": "Analysierte Seiten",
        "viable": "Das Projekt wirkt tragfähig, wenn zentrale Lücken geschlossen werden.",
        "needs_work": "Das Projekt braucht Nacharbeit vor Investor- oder Partnergespräch.",
        "early": "Frühe Phase — Nachfrage validieren und Modell schärfen.",
    },
}


def resolve_report_locale(*, goal: str = "", text: str = "", explicit: str | None = None) -> str:
    if explicit:
        base = explicit.lower().split("-")[0]
        if base in _LABELS:
            return base
    blob = f"{goal} {text[:3000]}"
    cyr = len(re.findall(r"[а-яёА-ЯЁ]", blob))
    de = len(re.findall(r"[äöüßÄÖÜ]", blob))
    lat = len(re.findall(r"[a-zA-Z]", blob))
    if cyr >= max(lat, de) and cyr > 20:
        return "ru"
    if de > lat and de > 10:
        return "de"
    if lat > 20:
        return "en"
    return "ru"


def _L(locale: str, key: str) -> str:
    loc = locale if locale in _LABELS else "ru"
    return _LABELS[loc].get(key, _LABELS["ru"][key])


def classify_document(text: str, *, filename: str = "", goal: str = "") -> str:
    blob = f"{filename} {goal} {text[:4000]}".lower()
    for doc_type, words in _TYPE_RULES:
        if any(w in blob for w in words):
            return doc_type
    return "general_business_document"


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _find_sentences(text: str, keywords: tuple[str, ...], *, limit: int = 8) -> list[str]:
    sentences = _split_sentences(text)
    hits: list[str] = []
    seen: set[str] = set()
    for s in sentences:
        low = s.lower()
        if any(k in low for k in keywords):
            key = low[:80]
            if key in seen:
                continue
            seen.add(key)
            hits.append(s[:450])
        if len(hits) >= limit:
            break
    return hits


def _extract_bullet_lines(text: str, *, limit: int = 12) -> list[str]:
    items: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if re.match(r"^[-•*–]\s+.+", line) or re.match(r"^\d+[\.\)]\s+.{10,}", line):
            cleaned = re.sub(r"^[-•*–\d\.\)]\s*", "", line).strip()
            if len(cleaned) > 10:
                items.append(cleaned[:400])
        if len(items) >= limit:
            break
    return items


def _extract_under_section_headings(text: str, pattern: re.Pattern[str], *, limit: int = 8) -> list[str]:
    lines = text.splitlines()
    items: list[str] = []
    capture = False
    heading_re = re.compile(r"^[#*\d\.\)]*\s*[A-ZА-ЯЁa-zäöü].{2,80}$")

    for raw in lines:
        line = raw.strip()
        if not line:
            if capture and items:
                break
            continue
        if pattern.search(line) and len(line) < 100:
            capture = True
            continue
        if capture and heading_re.match(line) and not pattern.search(line):
            break
        if capture:
            if re.match(r"^[-•*–]\s+", line) or re.match(r"^\d+[\.\)]\s+", line):
                cleaned = re.sub(r"^[-•*–\d\.\)]\s*", "", line).strip()
                if len(cleaned) > 8:
                    items.append(cleaned[:400])
            elif 20 < len(line) < 350 and not line.endswith(":"):
                items.append(line[:400])
        if len(items) >= limit:
            break
    return items


def _swot_bucket(text: str, bucket: str) -> list[str]:
    from_section = _extract_under_section_headings(text, _SWOT_SECTION_PATTERNS[bucket])
    if from_section:
        return from_section[:8]
    from_lines = _find_sentences(text, _SWOT_LINE_HINTS[bucket], limit=6)
    if from_lines:
        return from_lines
    return []


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
                DocumentSection(title=current_title, excerpt=excerpt[:2000], line_start=line_no)
            )
        buffer = []

    heading_re = re.compile(
        r"^(?:\d+[\.\)]\s+|[#]+\s*)?([A-ZА-ЯЁ][\w\s\-äöüÄÖÜß]{3,80})$"
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
        if len(buffer) > 50:
            flush()
    flush()
    if not sections and text.strip():
        sections.append(DocumentSection(title="Содержание", excerpt=text[:3000]))
    return sections[:16]


def _detect_topics(text: str) -> list[str]:
    low = text.lower()
    return [topic for topic, words in _TOPIC_KEYWORDS.items() if any(w in low for w in words)]


def _infer_title(text: str, filename: str, doc_type: str) -> str:
    for line in text.splitlines()[:12]:
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


def _readiness_bar(score: int) -> str:
    filled = max(0, min(10, score // 10))
    return "█" * filled + "░" * (10 - filled)


def _compute_readiness(
    structure: DocumentStructure,
    *,
    strengths: list[str],
    weaknesses: list[str],
    market_notes: list[str],
    finance_notes: list[str],
    risks: list[str],
    locale: str,
) -> tuple[int, str, int, str]:
    score = 35
    reasons: list[str] = []

    if market_notes:
        score += 12
        reasons.append("описан рынок" if locale == "ru" else "market described")
    if finance_notes:
        score += 12
        reasons.append("есть финансовые данные" if locale == "ru" else "financial data present")
    if len(strengths) >= 2:
        score += 10
        reasons.append("сильные стороны подтверждены текстом" if locale == "ru" else "strengths evidenced")
    if structure.word_count >= 800:
        score += 10
        reasons.append("достаточный объём документа" if locale == "ru" else "sufficient document depth")
    elif structure.word_count < 350:
        score -= 15
        reasons.append("документ слишком краткий" if locale == "ru" else "document too short")
    if "team" in structure.detected_topics:
        score += 8
        reasons.append("упомянута команда" if locale == "ru" else "team covered")
    if risks:
        score += 5
    if len(weaknesses) >= 2:
        score -= 5

    score = max(0, min(100, score))
    launch_pct = max(0, min(95, score - 5 + min(10, len(strengths) * 2)))

    if score >= 75:
        verdict = _L(locale, "viable")
    elif score >= 50:
        verdict = _L(locale, "needs_work")
    else:
        verdict = _L(locale, "early")

    explanation = "; ".join(reasons[:5]) if reasons else (
        "оценка по полноте разделов документа" if locale == "ru" else "score based on section completeness"
    )
    return score, explanation, launch_pct, verdict


def _build_priority_actions(
    *,
    weaknesses: list[str],
    risks: list[str],
    recommendations: list[str],
    open_questions: list[str],
    locale: str,
    limit: int = 8,
) -> list[str]:
    actions: list[str] = []
    for w in weaknesses[:3]:
        if locale == "ru":
            actions.append(f"Устранить слабое место: {w[:200]}")
        elif locale == "de":
            actions.append(f"Schwäche beheben: {w[:200]}")
        else:
            actions.append(f"Address weakness: {w[:200]}")
    for r in risks[:2]:
        if locale == "ru":
            actions.append(f"Снизить риск: {r[:200]}")
        elif locale == "de":
            actions.append(f"Risiko mindern: {r[:200]}")
        else:
            actions.append(f"Mitigate risk: {r[:200]}")
    actions.extend(recommendations)
    for q in open_questions[:2]:
        if locale == "ru":
            actions.append(f"Закрыть пробел: {q[:200]}")
        else:
            actions.append(f"Close gap: {q[:200]}")
    seen: set[str] = set()
    out: list[str] = []
    for i, a in enumerate(actions, start=1):
        key = a[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(f"{i}. {a}" if not re.match(r"^\d+\.", a) else a)
        if len(out) >= limit:
            break
    return out


def _build_executive_narrative(
    structure: DocumentStructure,
    *,
    locale: str,
    verdict: str,
    readiness_score: int,
    launch_pct: int,
    main_advantage: str,
    main_risk: str,
    priority_actions: list[str],
) -> str:
    lines = [
        f"**{structure.title}**",
        "",
        f"### {_L(locale, 'verdict')}",
        verdict,
        "",
        f"### {_L(locale, 'readiness')}: **{readiness_score}/100**",
        _readiness_bar(readiness_score),
        "",
        f"**{_L(locale, 'launch_prob')}:** {launch_pct}%",
        "",
        f"### {_L(locale, 'main_adv')}",
        main_advantage or "—",
        "",
        f"### {_L(locale, 'main_risk')}",
        main_risk or "—",
        "",
        f"### {_L(locale, 'next_steps')}",
    ]
    for idx, step in enumerate(priority_actions[:5], start=1):
        clean = re.sub(r"^\d+\.\s*", "", step)
        lines.append(f"{idx}. {clean}")
    return "\n".join(lines)


def analyze_document(
    text: str,
    *,
    filename: str = "",
    goal: str = "",
    page_count: int = 0,
    pages_analyzed: int = 0,
    locale: str | None = None,
) -> DocumentAnalysis:
    work_text = text[:_MAX_ANALYSIS_TEXT_CHARS]
    report_locale = resolve_report_locale(goal=goal, text=work_text, explicit=locale)

    structure = build_structure(
        work_text,
        filename=filename,
        goal=goal,
        page_count=page_count,
        pages_analyzed=pages_analyzed,
    )

    strengths = _swot_bucket(work_text, "strengths")
    weaknesses = _swot_bucket(work_text, "weaknesses")
    opportunities = _swot_bucket(work_text, "opportunities")
    threats = _swot_bucket(work_text, "threats")
    market_notes = _find_sentences(work_text, _TOPIC_KEYWORDS["market"], limit=8)
    finance_notes = _find_sentences(work_text, _TOPIC_KEYWORDS["finance"], limit=8)
    risks = _find_sentences(work_text, _TOPIC_KEYWORDS["risks"], limit=8) or threats[:6]

    def _fallback(bucket: str, found: list[str]) -> list[str]:
        if found:
            return found
        if report_locale == "ru":
            msgs = {
                "strengths": ["В явном виде не выделены — см. разделы документа и цитаты ниже."],
                "weaknesses": ["Требуется уточнение слабых мест в отдельном разделе плана."],
                "opportunities": ["Потенциал роста следует описать количественно (рынок, CAGR)."],
                "threats": ["Внешние угрозы описаны недостаточно конкретно."],
            }
        else:
            msgs = {
                "strengths": ["Not explicitly listed — see document sections and quotes."],
                "weaknesses": ["Weak points need a dedicated section in the plan."],
                "opportunities": ["Growth potential should be quantified (market size, CAGR)."],
                "threats": ["External threats are not described concretely enough."],
            }
        return msgs.get(bucket, found)

    swot = {
        "strengths": _fallback("strengths", strengths),
        "weaknesses": _fallback("weaknesses", weaknesses),
        "opportunities": _fallback("opportunities", opportunities),
        "threats": _fallback("threats", threats) or risks[:4] or _fallback("threats", []),
    }

    recommendations: list[str] = []
    if not finance_notes:
        recommendations.append(
            "Добавить финансовую модель: выручка, расходы, точка безубыточности, горизонт 24 мес."
            if report_locale == "ru"
            else "Add financial model: revenue, costs, break-even, 24-month horizon."
        )
    if not market_notes:
        recommendations.append(
            "Расширить раздел о рынке: TAM/SAM, конкуренты, позиционирование."
            if report_locale == "ru"
            else "Expand market section: TAM/SAM, competitors, positioning."
        )
    if structure.word_count < 500:
        recommendations.append(
            "Увеличить глубину: продукт, команда, go-to-market, KPI на 90 дней."
            if report_locale == "ru"
            else "Add depth: product, team, go-to-market, 90-day KPIs."
        )
    if not recommendations:
        recommendations.append(
            "Зафиксировать 3 приоритета из SWOT и назначить ответственных и сроки."
            if report_locale == "ru"
            else "Set 3 SWOT priorities with owners and deadlines."
        )

    open_questions: list[str] = []
    if structure.word_count < 800:
        open_questions.append(
            "Какова целевая аудитория и подтверждённый спрос?"
            if report_locale == "ru"
            else "What is the target audience and validated demand?"
        )
    if not finance_notes:
        open_questions.append(
            "Какие допущения заложены в финансовый прогноз?"
            if report_locale == "ru"
            else "What assumptions underpin the financial forecast?"
        )
    if "team" not in structure.detected_topics:
        open_questions.append(
            "Какой состав команды и ключевые роли?"
            if report_locale == "ru"
            else "What is the team composition and key roles?"
        )

    evidence = list(dict.fromkeys((strengths + market_notes + finance_notes + _extract_bullet_lines(work_text))[:8]))

    readiness_score, readiness_explanation, launch_pct, verdict = _compute_readiness(
        structure,
        strengths=strengths,
        weaknesses=weaknesses,
        market_notes=market_notes,
        finance_notes=finance_notes,
        risks=risks,
        locale=report_locale,
    )

    main_advantage = strengths[0] if strengths else (market_notes[0][:250] if market_notes else "")
    main_risk = risks[0] if risks else (weaknesses[0][:250] if weaknesses else "")

    priority_actions = _build_priority_actions(
        weaknesses=weaknesses,
        risks=risks,
        recommendations=recommendations,
        open_questions=open_questions,
        locale=report_locale,
    )

    executive_summary = _build_executive_narrative(
        structure,
        locale=report_locale,
        verdict=verdict,
        readiness_score=readiness_score,
        launch_pct=launch_pct,
        main_advantage=main_advantage,
        main_risk=main_risk,
        priority_actions=priority_actions,
    )

    return DocumentAnalysis(
        structure=structure,
        executive_summary=executive_summary,
        swot=swot,
        strengths=strengths,
        weaknesses=weaknesses,
        risks=risks,
        market_notes=market_notes,
        finance_notes=finance_notes,
        recommendations=recommendations,
        open_questions=open_questions,
        evidence_quotes=evidence,
        report_locale=report_locale,
        readiness_score=readiness_score,
        readiness_explanation=readiness_explanation,
        launch_probability_pct=launch_pct,
        verdict=verdict,
        main_advantage=main_advantage,
        main_risk=main_risk,
        priority_actions=priority_actions,
    )


def render_executive_summary_md(analysis: DocumentAnalysis, *, source_filename: str) -> str:
    loc = analysis.report_locale
    s = analysis.structure
    return f"""# {_L(loc, "exec_title")}

**{_L(loc, "doc_label")}:** {s.title}  
**{_L(loc, "file_label")}:** {source_filename}  
**{_L(loc, "type_label")}:** {s.document_type}  
**{_L(loc, "words_label")}:** {s.word_count}  
**{_L(loc, "pages_label")}:** {s.pages_analyzed or s.page_count or "—"}

---

{analysis.executive_summary}

---

**{_L(loc, "readiness")}:** {analysis.readiness_score}/100 — {analysis.readiness_explanation}

---
*{_L(loc, "footer")}*
"""


def render_report_md(analysis: DocumentAnalysis, *, source_filename: str) -> str:
    loc = analysis.report_locale
    s = analysis.structure

    def bullets(items: list[str]) -> str:
        if not items:
            return "- —\n"
        return "\n".join(f"- {item}" for item in items) + "\n"

    def swot_block(key: str, title_key: str) -> str:
        return f"### {_L(loc, title_key)}\n{bullets(analysis.swot.get(key, []))}"

    priorities = f"## {_L(loc, 'priorities')}\n\n{bullets(analysis.priority_actions)}\n"

    readiness_block = f"""## {_L(loc, "readiness")}

**{analysis.readiness_score}/100** `{_readiness_bar(analysis.readiness_score)}`

{_L(loc, "launch_prob")}: **{analysis.launch_probability_pct}%**

{analysis.readiness_explanation}

### {_L(loc, "verdict")}

{analysis.verdict}

"""

    sections_block = ""
    if s.sections:
        sections_block = f"## {_L(loc, 'structure')}\n\n"
        for sec in s.sections[:10]:
            sections_block += f"### {sec.title}\n{sec.excerpt[:600]}\n\n"

    evidence = ""
    if analysis.evidence_quotes:
        evidence = f"## {_L(loc, 'quotes')}\n\n"
        for q in analysis.evidence_quotes[:6]:
            evidence += f"> {q}\n\n"

    topics_label = _L(loc, "topics")
    topics_val = ", ".join(s.detected_topics) if s.detected_topics else "—"

    return f"""# {_L(loc, "report_title")}

**{_L(loc, "doc_label")}:** {s.title}  
**{_L(loc, "file_label")}:** {source_filename}  
**{_L(loc, "type_label")}:** {s.document_type}  
**{topics_label}:** {topics_val}

---

{readiness_block}
{priorities}
## {_L(loc, "swot")}

{swot_block("strengths", "strengths")}
{swot_block("weaknesses", "weaknesses")}
{swot_block("opportunities", "opportunities")}
{swot_block("threats", "threats")}

## {_L(loc, "market")}

{bullets(analysis.market_notes)}

## {_L(loc, "finance")}

{bullets(analysis.finance_notes)}

## {_L(loc, "risks")}

{bullets(analysis.risks)}

## {_L(loc, "recommendations")}

{bullets(analysis.recommendations)}

## {_L(loc, "questions")}

{bullets(analysis.open_questions)}

{sections_block}
{evidence}
---
*{_L(loc, "footer")}*
"""


def structure_json(analysis: DocumentAnalysis) -> str:
    payload = {
        "version": "document-structure-v2",
        "analysis": analysis.to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
