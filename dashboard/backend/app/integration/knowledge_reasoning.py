"""Knowledge Reasoning — Expert Review (first reasoning mode).

Source-agnostic: works on any parsed intake document (PDF today, DOCX later).
Intent → expert role → brain guidance block (not a separate LLM call).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from app.integration.feature_registry import FeatureRegistry
from app.integration.locale_service import resolve_locale

ExpertRole = Literal[
    "business_consultant",
    "legal_reviewer",
    "ux_expert",
    "senior_engineer",
    "investor",
    "marketer",
    "hr_reviewer",
    "jobcenter_advisor",
    "editor",
]

DocumentKind = Literal[
    "business_plan",
    "contract",
    "resume",
    "presentation",
    "technical_spec",
    "marketing",
    "generic",
]

# --- Intent: evaluation / advice vs factual lookup ---------------------------------

_EVAL_PATTERNS = re.compile(
    r"(?i)(?:"
    r"профессиональн|хорош(?:ий|ая|ее|и)\s+(?:ли\s+)?(?:документ|план|текст|материал)|"
    r"что\s+(?:бы\s+)?(?:ты\s+)?(?:изменил|улучшил|посоветовал|добавил)|"
    r"слаб(?:ые|ое|ая|ост)|что\s+не\s+так|критик|оцени|убедительн|"
    r"стоит\s+ли\s+(?:отправ|показ|подав)|что\s+бы\s+сказал|"
    r"опасн|риск(?:и)?\s+(?:для|в)|современн|"
    r"professional|good\s+document|what\s+would\s+you\s+change|weak(?:ness)?|"
    r"improve|critique|evaluate|persuasive|convincing|worth\s+send|"
    r"what\s+would\s+(?:a\s+)?(?:bank|investor|lawyer)|"
    r"professionell|gut(?:er|e|es)?\s+dokument|was\s+würdest\s+du\s+ändern|schwach"
    r")",
)

_FACTUAL_ONLY = re.compile(
    r"(?i)(?:"
    r"какой\s+дедлайн|сколько\s+стр|кто\s+автор|когда\s+создан|"
    r"what\s+is\s+the\s+deadline|how\s+many\s+pages|who\s+wrote"
    r")",
)

_ROLE_HINTS: list[tuple[ExpertRole, re.Pattern[str]]] = [
    (
        "legal_reviewer",
        re.compile(
            r"(?i)(договор|контракт|contract|clause|юрист|legal|опасн|риск\s+для\s+меня|liability)"
        ),
    ),
    (
        "ux_expert",
        re.compile(r"(?i)(дизайн|design|ux|ui|оформлен|современн|presentation|презентац|slides)"),
    ),
    (
        "senior_engineer",
        re.compile(r"(?i)(код|code|архитектур|technical|технич|тз|spec|api|software|репозитор)"),
    ),
    (
        "hr_reviewer",
        re.compile(r"(?i)(резюме|resume|cv|взял\s+бы\s+на\s+работу|hire|кандидат)"),
    ),
    (
        "marketer",
        re.compile(r"(?i)(маркетинг|marketing|продвижен|реклам|brand|бренд)"),
    ),
    (
        "jobcenter_advisor",
        re.compile(r"(?i)(jobcenter|аргайт|agentur\s+für\s+arbeit|соискател)"),
    ),
    (
        "investor",
        re.compile(r"(?i)(инвестор|investor|венчур|fund|roi|pitch|купил\s+бы)"),
    ),
    (
        "business_consultant",
        re.compile(
            r"(?i)(бизнес-план|business\s+plan|банк|bank|профессиональн|убедительн|слаб)"
        ),
    ),
]

_KIND_HINTS: list[tuple[DocumentKind, re.Pattern[str]]] = [
    ("business_plan", re.compile(r"(?i)(бизнес-план|business\s+plan|geschäftsplan)")),
    ("contract", re.compile(r"(?i)(договор|contract|vereinbarung|agreement)")),
    ("resume", re.compile(r"(?i)(резюме|resume|lebenslauf|cv)")),
    ("presentation", re.compile(r"(?i)(презентац|presentation|pitch\s+deck|slides)")),
    ("technical_spec", re.compile(r"(?i)(технич|technical|specification|тз|architecture)")),
    ("marketing", re.compile(r"(?i)(маркетинг|marketing|brochure|проспект)")),
]

_EXPERT_LABELS: dict[str, dict[ExpertRole, str]] = {
    "ru": {
        "business_consultant": "Бизнес-консультант",
        "legal_reviewer": "Юрист (обзор рисков, не юр. заключение)",
        "ux_expert": "UX/UI эксперт",
        "senior_engineer": "Senior Software Engineer",
        "investor": "Инвестор",
        "marketer": "Маркетолог",
        "hr_reviewer": "HR-специалист",
        "jobcenter_advisor": "Консультант Jobcenter / Arbeitsagentur",
        "editor": "Редактор документов",
    },
    "en": {
        "business_consultant": "Business consultant",
        "legal_reviewer": "Legal reviewer (risk scan, not legal advice)",
        "ux_expert": "UX/UI expert",
        "senior_engineer": "Senior software engineer",
        "investor": "Investor",
        "marketer": "Marketer",
        "hr_reviewer": "HR reviewer",
        "jobcenter_advisor": "Jobcenter / employment agency advisor",
        "editor": "Document editor",
    },
    "de": {
        "business_consultant": "Business-Berater",
        "legal_reviewer": "Legal Reviewer (Risiko-Check, keine Rechtsberatung)",
        "ux_expert": "UX/UI-Experte",
        "senior_engineer": "Senior Software Engineer",
        "investor": "Investor",
        "marketer": "Marketing-Experte",
        "hr_reviewer": "HR-Spezialist",
        "jobcenter_advisor": "Jobcenter / Arbeitsagentur-Berater",
        "editor": "Dokumenten-Editor",
    },
}

_GUIDANCE: dict[str, str] = {
    "ru": (
        "РЕЖИМ EXPERT REVIEW — оценивай КАЧЕСТВО ДОКУМЕНТА/МАТЕРИАЛА, не личность автора.\n"
        "Если спрашивают «профессиональный ли документ» — отвечай про структуру, полноту, "
        "ясность, оформление и убедительность текста. НЕ оценивай сертификаты/биографию автора, "
        "если об этом явно не спросили.\n"
        "Формат ответа:\n"
        "1) Прямой ответ на вопрос (да/нет/частично + краткое обоснование по тексту).\n"
        "2) Сильные стороны документа (по содержимому).\n"
        "3) 3–5 конкретных улучшений.\n"
        "4) Оговорка: оценка по загруженному тексту, не проверка реального бизнеса.\n"
        "Опирайся на текст документа; не выдумывай факты, которых нет в материале."
    ),
    "en": (
        "EXPERT REVIEW MODE — evaluate DOCUMENT QUALITY, not the author's personal credentials.\n"
        "If asked whether the document is professional — comment on structure, completeness, "
        "clarity, layout, and persuasiveness. Do NOT judge certificates/bio unless explicitly asked.\n"
        "Answer format:\n"
        "1) Direct answer (yes/no/partially + brief rationale from the text).\n"
        "2) Document strengths (from content).\n"
        "3) 3–5 concrete improvements.\n"
        "4) Disclaimer: assessment from uploaded text only, not real-world verification.\n"
        "Ground in the document; do not invent facts not present in the material."
    ),
    "de": (
        "EXPERT REVIEW MODE — bewerte DIE QUALITÄT DES DOKUMENTS, nicht die Person des Autors.\n"
        "Bei «professionell?» — Struktur, Vollständigkeit, Klarheit, Layout, Überzeugungskraft. "
        "KEINE Zertifikate/Biografie, außer explizit gefragt.\n"
        "Antwortformat:\n"
        "1) Direkte Antwort (ja/nein/teilweise + Begründung aus dem Text).\n"
        "2) Stärken des Dokuments.\n"
        "3) 3–5 konkrete Verbesserungen.\n"
        "4) Hinweis: Bewertung nur aus dem hochgeladenen Text.\n"
        "Am Dokumenttext festhalten; keine erfundenen Fakten."
    ),
}


def expert_review_enabled(memory_dir: Path | None) -> bool:
    return FeatureRegistry(memory_dir=memory_dir).is_enabled("knowledge_expert_review")


def has_parsed_intake(files: list[dict[str, Any]]) -> bool:
    return any((f.get("parsed_excerpt") or "").strip() for f in files)


def detect_expert_review_intent(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if _FACTUAL_ONLY.search(q):
        return False
    return bool(_EVAL_PATTERNS.search(q))


def infer_document_kind(files: list[dict[str, Any]]) -> DocumentKind:
    blob = " ".join(
        f"{f.get('filename', '')} {f.get('parsed_excerpt', '')[:2000]}" for f in files
    )
    for kind, pat in _KIND_HINTS:
        if pat.search(blob):
            return kind
    return "generic"


def select_expert_role(question: str, *, document_kind: DocumentKind) -> ExpertRole:
    q = question or ""
    for role, pat in _ROLE_HINTS:
        if pat.search(q):
            return role
    defaults: dict[DocumentKind, ExpertRole] = {
        "business_plan": "business_consultant",
        "contract": "legal_reviewer",
        "resume": "hr_reviewer",
        "presentation": "ux_expert",
        "technical_spec": "senior_engineer",
        "marketing": "marketer",
        "generic": "editor",
    }
    return defaults.get(document_kind, "editor")


def build_expert_review_context(
    question: str,
    files: list[dict[str, Any]],
    *,
    memory_dir: Path | None = None,
    locale: str | None = None,
) -> str:
    """Brain block appended when expert review intent + parsed intake."""
    if not expert_review_enabled(memory_dir):
        return ""
    if not has_parsed_intake(files):
        return ""
    if not detect_expert_review_intent(question):
        return ""

    loc = resolve_locale(locale)
    if loc not in _GUIDANCE:
        loc = "en"

    doc_kind = infer_document_kind(files)
    role = select_expert_role(question, document_kind=doc_kind)
    role_label = _EXPERT_LABELS.get(loc, _EXPERT_LABELS["en"])[role]

    names = ", ".join(str(f.get("filename") or "document") for f in files[:3])
    return (
        f"{_GUIDANCE[loc]}\n\n"
        f"Expert hat: {role_label}\n"
        f"Document kind (inferred): {doc_kind}\n"
        f"Files: {names}\n"
        f"User question to answer as this expert: {question.strip()}"
    )


def maybe_append_expert_review(
    question: str,
    intake_note: str,
    files: list[dict[str, Any]],
    *,
    memory_dir: Path | None = None,
    locale: str | None = None,
) -> str:
    """Merge intake note with expert review guidance when applicable."""
    extra = build_expert_review_context(
        question, files, memory_dir=memory_dir, locale=locale
    )
    if not extra:
        return intake_note
    if intake_note:
        return f"{intake_note}\n\n{extra}"
    return extra
