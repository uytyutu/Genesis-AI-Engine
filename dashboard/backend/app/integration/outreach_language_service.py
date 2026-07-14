"""Outreach language detection + localized draft (LLM Router fallback to templates)."""

from __future__ import annotations

import re
from typing import Any

from app.integration.engine_ai_service import EngineAIService
from app.integration.genesis_brain.public_brand import BRAND_NAME

_AI = EngineAIService()

_LANG_MARKERS: dict[str, tuple[str, ...]] = {
    "de": ("guten tag", "ihr", "website", "öffnungszeiten", "kein https", "seitentitel"),
    "en": ("hello", "your website", "contact form", "opening hours", "no https", "page title"),
    "fr": ("bonjour", "votre site", "formulaire", "horaires", "pas de https"),
    "es": ("hola", "su sitio", "formulario", "horario", "sin https"),
    "it": ("buongiorno", "sito web", "modulo", "orari", "senza https"),
    "pl": ("dzień dobry", "strona", "formularz", "godziny", "brak https"),
    "pt": ("olá", "seu site", "formulário", "horário", "sem https"),
    "hi": ("नमस्ते", "वेबसाइट", "संपर्क"),
}

_TEMPLATES: dict[str, dict[str, str]] = {
    "de": {
        "subject": "Idee für {company} — moderner Auftritt online",
        "greeting": "Guten Tag,",
        "intro": "wir haben uns {company} angeschaut und möchten einen konkreten Vorschlag machen.",
        "issues": "Was uns aufgefallen ist:",
        "offer": "Paket «{package}» für {price:.0f} € — Lieferzeit ca. 5–7 Werktage.",
        "close": "Beste Grüße\nRamish · {brand}",
    },
    "en": {
        "subject": "Quick idea for {company} — stronger web presence",
        "greeting": "Hello,",
        "intro": "we reviewed {company} and have a concrete, no-pressure proposal.",
        "issues": "What we noticed:",
        "offer": "Package «{package}» for €{price:.0f} — delivery in about 5–7 business days.",
        "close": "Best regards\nRamish · {brand}",
    },
    "fr": {
        "subject": "Idée pour {company} — présence web moderne",
        "greeting": "Bonjour,",
        "intro": "nous avons consulté {company} et souhaitons une proposition concrète.",
        "issues": "Ce que nous avons remarqué :",
        "offer": "Forfait «{package}» — {price:.0f} €, livraison en 5–7 jours ouvrés.",
        "close": "Cordialement\nRamish · {brand}",
    },
    "es": {
        "subject": "Idea para {company} — presencia web moderna",
        "greeting": "Hola,",
        "intro": "revisamos {company} y tenemos una propuesta concreta sin presión.",
        "issues": "Lo que notamos:",
        "offer": "Paquete «{package}» — {price:.0f} €, entrega en 5–7 días hábiles.",
        "close": "Saludos\nRamish · {brand}",
    },
}


class OutreachLanguageService:
    """Detect site language and draft outreach in the visitor's language."""

    def detect_language(self, row: dict[str, Any]) -> str:
        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        declared = str(analysis.get("detected_lang") or "").lower().strip()
        if declared and len(declared) <= 5:
            return declared.split("-")[0]

        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if meta.get("outreach_language"):
            return str(meta["outreach_language"]).split("-")[0]

        blob = " ".join(
            [
                str(analysis.get("title") or ""),
                " ".join(str(i) for i in (analysis.get("issues") or [])),
                str(row.get("fit_reason") or ""),
            ]
        ).lower()

        scores: dict[str, int] = {lang: 0 for lang in _LANG_MARKERS}
        for lang, markers in _LANG_MARKERS.items():
            for m in markers:
                if m in blob:
                    scores[lang] += 1

        if re.search(r"[\u0900-\u097F]", blob):
            return "hi"
        if re.search(r"[\u0400-\u04FF]", blob):
            return "ru"

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "en"

    def draft_outreach(
        self,
        *,
        company: str,
        analysis: dict | None,
        package: dict,
        price: float,
        fit_reason: str,
        language: str | None = None,
        row: dict[str, Any] | None = None,
    ) -> tuple[str, str, str]:
        lang = (language or (self.detect_language(row) if row else None) or "en").split("-")[0]

        llm_draft = _AI.generate_personalized_offer(
            company=company,
            analysis=analysis or {},
            language=lang,
            package_name=str(package.get("name", "Web")),
            price_eur=price,
            fit_reason=fit_reason,
        )
        if llm_draft:
            return llm_draft["subject"], llm_draft["body"], lang

        tpl = _TEMPLATES.get(lang) or _TEMPLATES["en"]
        issues = (analysis or {}).get("issues") or []
        issues_block = "\n".join(f"• {i}" for i in issues[:7]) if issues else "• Room to improve online presence"

        subject = tpl["subject"].format(company=company)
        body = (
            f"{tpl['greeting']}\n\n"
            f"{tpl['intro'].format(company=company)}\n\n"
            f"{tpl['issues']}\n{issues_block}\n\n"
            f"{tpl['offer'].format(package=package.get('name', 'Web'), price=price)}\n\n"
            f"{tpl['close'].format(brand=BRAND_NAME)}\n"
            f"https://genesis-ai-engine.vercel.app/site\n"
        )
        if fit_reason:
            body = body.replace(tpl["intro"].format(company=company), f"{tpl['intro'].format(company=company)} ({fit_reason.strip()[:80]})", 1)
        return subject, body, lang
