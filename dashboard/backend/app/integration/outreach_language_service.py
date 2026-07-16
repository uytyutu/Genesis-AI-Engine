"""Outreach language detection + localized draft (LLM Router fallback to templates)."""

from __future__ import annotations

import os
import re
from typing import Any

from app.integration.engine_ai_service import EngineAIService
from app.integration.genesis_brain.public_brand import BRAND_NAME

_AI = EngineAIService()


def public_order_url() -> str:
    """Public Path A checkout page — CTA target for sniper outreach (not /site chat)."""
    base = (
        os.getenv("GENESIS_PUBLIC_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or "https://genesis-ai-engine.vercel.app"
    ).rstrip("/")
    return f"{base}/order"


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

# Honest Path A: sell a NEW modern Landing Page (digital restart), never "we fix your CMS".
_TEMPLATES: dict[str, dict[str, str]] = {
    "de": {
        "subject": "{company} — digitaler Neustart mit moderner Landing Page",
        "greeting": "Guten Tag,",
        "intro": (
            "wir haben uns den aktuellen Online-Auftritt von {company} angeschaut. "
            "Statt an einem veralteten System zu „reparieren“, schlagen wir einen klaren "
            "Neustart vor: eine moderne, schnelle Landing Page — mobil optimiert, "
            "mit klarem Kontakt-/Terminweg."
        ),
        "issues": "Warum ein Neustart sinnvoll ist (Ist-Zustand):",
        "offer": (
            "Paket «{package}» für {price:.0f} € — fertige Landing Page in ca. 5–7 Werktagen "
            "(HTML-Dateien, bereit für Ihren Hosting-Anbieter). "
            "Optional: Upload auf Ihre Domain durch uns (Sorglos-Paket)."
        ),
        "cta": (
            "Wenn das für Sie interessant klingt — hier die Pakete und Bestellung "
            "(ohne Verpflichtung, Sie entscheiden in Ruhe):\n{order_url}"
        ),
        "close": "Beste Grüße\nRamish · {brand}",
    },
    "en": {
        "subject": "{company} — digital restart with a modern landing page",
        "greeting": "Hello,",
        "intro": (
            "we reviewed the current online presence of {company}. "
            "Rather than patching an outdated setup, we propose a clean restart: "
            "a modern, fast landing page — mobile-first, with a clear contact/booking path."
        ),
        "issues": "Why a restart makes sense (current state):",
        "offer": (
            "Package «{package}» for €{price:.0f} — finished landing page in about 5–7 business days "
            "(HTML files ready for your host). "
            "Optional: we upload to your domain for you (hands-off package)."
        ),
        "cta": (
            "If this sounds useful — packages and order (no obligation):\n{order_url}"
        ),
        "close": "Best regards\nRamish · {brand}",
    },
    "fr": {
        "subject": "{company} — nouveau départ digital avec une landing page",
        "greeting": "Bonjour,",
        "intro": (
            "nous avons consulté la présence en ligne de {company}. "
            "Au lieu de « réparer » un site obsolète, nous proposons un redémarrage clair : "
            "une landing page moderne et rapide, optimisée mobile."
        ),
        "issues": "Pourquoi un redémarrage est pertinent (état actuel) :",
        "offer": (
            "Forfait «{package}» — {price:.0f} €, landing page livrée en 5–7 jours ouvrés "
            "(fichiers HTML prêts pour votre hébergeur)."
        ),
        "cta": "Détails et commande (sans engagement) :\n{order_url}",
        "close": "Cordialement\nRamish · {brand}",
    },
    "es": {
        "subject": "{company} — reinicio digital con landing page moderna",
        "greeting": "Hola,",
        "intro": (
            "revisamos la presencia online de {company}. "
            "En lugar de «arreglar» un sitio anticuado, proponemos un reinicio claro: "
            "una landing page moderna y rápida, optimizada para móvil."
        ),
        "issues": "Por qué tiene sentido un reinicio (estado actual):",
        "offer": (
            "Paquete «{package}» — {price:.0f} €, landing page en 5–7 días hábiles "
            "(archivos HTML listos para su hosting)."
        ),
        "cta": "Detalles y pedido (sin compromiso):\n{order_url}",
        "close": "Saludos\nRamish · {brand}",
    },
}

# Simple niche overlays (DE) — Path A restart, niche-specific value.
_NICHE_TEMPLATES_DE: dict[str, dict[str, str]] = {
    "kfz": {
        "subject": "{company} — mehr Werkstatt-Termine über eine neue Landing Page",
        "intro": (
            "wir haben uns {company} angeschaut. Für Kfz-Betriebe zählt oft: "
            "schnelle Erreichbarkeit vom Smartphone, klare Leistungen "
            "(Inspektion, Reifen, Diagnose) und Vertrauen vor dem Anruf. "
            "Wir schlagen keinen WordPress-Flickenteppich vor, sondern eine neue, "
            "schlanke Werkstatt-Landing Page."
        ),
        "offer": (
            "Paket «{package}» für {price:.0f} € — Fokus: Termin-/Kontaktweg, Leistungen, "
            "Vertrauen. Fertige Landing Page in ca. 5–7 Werktagen "
            "(HTML, bereit für Ihren Host). Optional: Upload durch uns."
        ),
    },
    "zahnarzt": {
        "subject": "{company} — mehr Patientenanfragen über eine neue Praxis-Landing Page",
        "intro": (
            "wir haben uns {company} angeschaut. Für Zahnarztpraxen zählt oft: "
            "sichtbarer Online-Terminweg, Vertrauen (Team, Leistungen) und "
            "eine Seite, die mobil gut lesbar ist. "
            "Statt einer aufwendigen Sanierung des alten Auftritts: "
            "eine neue, klare Praxis-Landing Page."
        ),
        "offer": (
            "Paket «{package}» für {price:.0f} € — Fokus: Patientenanfragen, Terminweg, "
            "Praxis-Vertrauen. Fertige Landing Page in ca. 5–7 Werktagen "
            "(HTML, bereit für Ihren Host). Optional: Upload durch uns."
        ),
    },
    "dach": {
        "subject": "{company} — mehr Anfragen über eine neue Dachdecker-Landing Page",
        "intro": (
            "wir haben uns {company} angeschaut. Für Dachdecker und Handwerk zählt oft: "
            "klare Leistungen, schnelle Erreichbarkeit vom Smartphone und Vertrauen "
            "vor dem Anruf. Statt Flickwerk am alten Auftritt: eine neue, schlanke Landing Page."
        ),
        "offer": (
            "Paket «{package}» für {price:.0f} € — Fokus: Anfragen, Leistungen, Vertrauen. "
            "Fertige Landing Page in ca. 5–7 Werktagen (HTML). Optional: Upload durch uns."
        ),
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

        tpl = dict(_TEMPLATES.get(lang) or _TEMPLATES["en"])
        if row:
            from app.integration.lead_pipeline_service import detect_niche_key

            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            niche = detect_niche_key(
                company=company,
                query=str(meta.get("query") or fit_reason or ""),
                meta=meta,
            )
            if lang == "de" and niche in _NICHE_TEMPLATES_DE:
                tpl.update(_NICHE_TEMPLATES_DE[niche])

        issues = (analysis or {}).get("issues") or []
        issues_block = (
            "\n".join(f"• {i}" for i in issues[:7]) if issues else "• Room to improve online presence"
        )

        subject = tpl["subject"].format(company=company)
        order_url = public_order_url()
        body = (
            f"{tpl['greeting']}\n\n"
            f"{tpl['intro'].format(company=company)}\n\n"
            f"{tpl['issues']}\n{issues_block}\n\n"
            f"{tpl['offer'].format(package=package.get('name', 'Web'), price=price)}\n\n"
            f"{tpl['cta'].format(order_url=order_url)}\n\n"
            f"{tpl['close'].format(brand=BRAND_NAME)}\n"
        )
        # fit_reason is already used for niche detection; keep body clean (no awkward parenthetical).
        return subject, body, lang
