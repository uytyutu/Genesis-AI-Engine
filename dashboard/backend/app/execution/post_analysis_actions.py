"""Intent-aware next steps after document analysis — work agent, not chat bot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.integration.product_line import universal_first_version_scenario


@dataclass(frozen=True)
class AnalysisAction:
    label: str
    href: str
    group: str  # artifacts | next
    available: bool = True
    capability_id: str | None = None

    def to_cta(self) -> dict[str, Any]:
        return {
            "href": self.href,
            "label": self.label,
            "group": self.group,
            "available": self.available,
        }


_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "summary": "📊 Executive Summary",
        "conclusion": "📄 Бизнес-заключение",
        "fix_doc": "✏️ Исправить документ",
        "pro_version": "📄 Профессиональная версия",
        "translate": "🌍 Перевести",
        "financial_model": "📊 Финансовая модель",
        "investment": "📈 Готовность к инвестициям",
        "bank": "📑 Версия для банка",
        "presentation": "📋 Презентация",
        "site": "🌐 Создать сайт",
        "soon": " · скоро",
        "msg_intro": "Я полностью проанализировал ваш документ.",
        "msg_readiness": "Общая готовность",
        "msg_issues": "Обнаружено проблем",
        "msg_priorities": "Приоритетных действий",
        "msg_prepared": "Подготовлено",
        "msg_footer": "Ниже откройте заключение или выберите следующий шаг.",
        "msg_artifacts": "Executive Summary, бизнес-заключение, структура документа",
        "doc_business_plan": "бизнес-план",
        "doc_financial": "финансовый отчёт",
        "doc_pitch": "питч",
        "doc_contract": "договор",
        "doc_general": "документ",
    },
    "en": {
        "summary": "📊 Executive Summary",
        "conclusion": "📄 Business Conclusion",
        "fix_doc": "✏️ Fix document",
        "pro_version": "📄 Professional version",
        "translate": "🌍 Translate",
        "financial_model": "📊 Financial model",
        "investment": "📈 Investment readiness",
        "bank": "📑 Bank-ready version",
        "presentation": "📋 Presentation",
        "site": "🌐 Create website",
        "soon": " · soon",
        "msg_intro": "I fully analyzed your document.",
        "msg_readiness": "Overall readiness",
        "msg_issues": "Issues found",
        "msg_priorities": "Priority actions",
        "msg_prepared": "Prepared",
        "msg_footer": "Open the conclusion below or choose your next step.",
        "msg_artifacts": "Executive Summary, business conclusion, document structure",
        "doc_business_plan": "business plan",
        "doc_financial": "financial report",
        "doc_pitch": "pitch deck",
        "doc_contract": "contract",
        "doc_general": "document",
    },
    "de": {
        "summary": "📊 Executive Summary",
        "conclusion": "📄 Geschäftsgutachten",
        "fix_doc": "✏️ Dokument korrigieren",
        "pro_version": "📄 Professionelle Version",
        "translate": "🌍 Übersetzen",
        "financial_model": "📊 Finanzmodell",
        "investment": "📈 Investitionsreife",
        "bank": "📑 Bankversion",
        "presentation": "📋 Präsentation",
        "site": "🌐 Website erstellen",
        "soon": " · bald",
        "msg_intro": "Ich habe Ihr Dokument vollständig analysiert.",
        "msg_readiness": "Gesamtreife",
        "msg_issues": "Gefundene Probleme",
        "msg_priorities": "Prioritäre Maßnahmen",
        "msg_prepared": "Erstellt",
        "msg_footer": "Öffnen Sie unten das Gutachten oder wählen Sie den nächsten Schritt.",
        "msg_artifacts": "Executive Summary, Geschäftsgutachten, Dokumentstruktur",
        "doc_business_plan": "Geschäftsplan",
        "doc_financial": "Finanzbericht",
        "doc_pitch": "Pitch-Deck",
        "doc_contract": "Vertrag",
        "doc_general": "Dokument",
    },
}


def _L(locale: str, key: str) -> str:
    loc = locale if locale in _LABELS else "ru"
    return _LABELS[loc].get(key, _LABELS["ru"][key])


def _doc_label(locale: str, doc_type: str) -> str:
    mapping = {
        "business_plan": "doc_business_plan",
        "financial_report": "doc_financial",
        "pitch_deck": "doc_pitch",
        "contract": "doc_contract",
    }
    return _L(locale, mapping.get(doc_type, "doc_general"))


def _horizon(label_key: str, locale: str, capability_id: str) -> AnalysisAction:
    return AnalysisAction(
        _L(locale, label_key) + _L(locale, "soon"),
        f"#horizon:{capability_id}",
        "next",
        available=False,
        capability_id=capability_id,
    )


def suggest_post_analysis_actions(
    *,
    doc_type: str,
    locale: str,
    summary_href: str,
    conclusion_href: str,
    site_available: bool = True,
) -> list[dict[str, Any]]:
    """Contextual CTAs — artifacts first, then intent-matched next steps."""
    loc = locale if locale in _LABELS else "ru"
    actions: list[AnalysisAction] = [
        AnalysisAction(_L(loc, "summary"), summary_href, "artifacts"),
        AnalysisAction(_L(loc, "conclusion"), conclusion_href, "artifacts"),
    ]

    if doc_type in ("business_plan", "pitch_deck", "general_business_document"):
        actions.extend(
            [
                _horizon("fix_doc", loc, "revise_document"),
                _horizon("pro_version", loc, "professional_document"),
                _horizon("translate", loc, "translate_document"),
                _horizon("financial_model", loc, "financial_model"),
                _horizon("investment", loc, "investment_readiness"),
                _horizon("bank", loc, "bank_package"),
                _horizon("presentation", loc, "generate_presentation"),
            ]
        )
        if site_available and doc_type in ("business_plan", "pitch_deck"):
            site_msg = "Создай сайт" if loc == "ru" else ("Create website" if loc == "en" else "Erstelle Website")
            actions.append(
                AnalysisAction(
                    _L(loc, "site"),
                    f"#action:{site_msg}",
                    "next",
                    available=True,
                    capability_id="generate_site",
                )
            )
    elif doc_type == "financial_report":
        actions.extend(
            [
                _horizon("financial_model", loc, "financial_model"),
                _horizon("investment", loc, "investment_readiness"),
                _horizon("bank", loc, "bank_package"),
                _horizon("fix_doc", loc, "revise_document"),
            ]
        )
    elif doc_type == "contract":
        actions.extend(
            [
                _horizon("fix_doc", loc, "revise_document"),
                _horizon("translate", loc, "translate_document"),
            ]
        )
    else:
        actions.append(_horizon("fix_doc", loc, "revise_document"))

    return [a.to_cta() for a in actions]


def build_analysis_completion_message(
    *,
    locale: str,
    doc_type: str,
    source_name: str,
    readiness: int | None,
    issues_count: int,
    priority_count: int,
) -> str:
    """Work-agent completion — honest about what was done (no fake auto-fixes)."""
    loc = locale if locale in _LABELS else "ru"
    lines = [
        f"📄 {source_name}",
        f"✓ {_L(loc, 'msg_intro')}",
    ]
    if readiness is not None:
        lines.append(f"✓ {_L(loc, 'msg_readiness')}: **{readiness}/100**")
    if issues_count > 0:
        lines.append(f"✓ {_L(loc, 'msg_issues')}: **{issues_count}**")
    if priority_count > 0:
        lines.append(f"✓ {_L(loc, 'msg_priorities')}: **{priority_count}**")
    lines.append(f"✓ {_L(loc, 'msg_prepared')}: {_L(loc, 'msg_artifacts')}")
    lines.append("")
    if loc == "ru":
        lines.append(universal_first_version_scenario())
    else:
        lines.append(_L(loc, "msg_footer"))
    return "\n".join(lines)
