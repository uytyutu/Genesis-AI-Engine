"""Outreach drafts by market: DE formal · EN-US short · RU/UA contextual.

Language is resolved from lead ``market`` / ``meta.market`` / ``meta.country_code``
first — site-language guessing is fallback only.
"""

from __future__ import annotations

import os
import re
from typing import Any

from app.integration.engine_ai_service import EngineAIService
from app.integration.genesis_brain.public_brand import BRAND_NAME

_AI = EngineAIService()

# Path A markets we actively template for Mission 1 sniper.
MARKET_DE = "DE"
MARKET_US = "US"
MARKET_CIS_RU = "RU"
MARKET_CIS_UA = "UA"
MARKET_CIS = "CIS"

# market → template language code
_MARKET_TO_LANG: dict[str, str] = {
    "DE": "de",
    "AT": "de",
    "CH": "de",
    "US": "en-us",
    "CA": "en-us",
    "GB": "en-us",
    "UK": "en-us",
    "AU": "en-us",
    "RU": "ru",
    "UA": "uk",
    "BY": "ru",
    "KZ": "ru",
    "CIS": "ru",
}


def public_order_url(*, market: str | None = None) -> str:
    """Public Path A checkout — optional ?market= for future localization (no multisite yet)."""
    base = (
        os.getenv("GENESIS_PUBLIC_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or "https://genesis-ai-engine.vercel.app"
    ).rstrip("/")
    url = f"{base}/order"
    m = (market or "").strip().upper()
    if m in ("DE", "US", "UA", "RU", "CIS"):
        return f"{url}?market={m.lower()}"
    return url


def normalize_market_code(raw: str | None) -> str | None:
    if not raw:
        return None
    code = str(raw).strip().upper().replace(" ", "")
    aliases = {
        "GERMANY": "DE",
        "DEUTSCHLAND": "DE",
        "USA": "US",
        "AMERICA": "US",
        "UNITEDSTATES": "US",
        "UKRAINE": "UA",
        "UKRAINA": "UA",
        "RUSSIA": "RU",
        "SNG": "CIS",
        "СНГ": "CIS",
    }
    code = aliases.get(code, code)
    if code in _MARKET_TO_LANG:
        return "CIS" if code == "CIS" else code
    if len(code) == 2:
        return code
    return None


def resolve_market_from_row(row: dict[str, Any] | None) -> str | None:
    """Prefer explicit market on the lead over language guessing."""
    if not row:
        return None
    for key in ("market", "market_code", "country_code"):
        hit = normalize_market_code(row.get(key) if isinstance(row.get(key), str) else None)
        if hit:
            return hit
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    for key in ("market", "market_code", "country_code", "outreach_region"):
        raw = meta.get(key)
        if isinstance(raw, str):
            # outreach_region may be de|cis|us
            low = raw.strip().lower()
            if low == "de":
                return "DE"
            if low in ("cis", "sng"):
                return "CIS"
            if low in ("us", "usa", "america"):
                return "US"
            hit = normalize_market_code(raw)
            if hit:
                return hit
    # City heuristics (major hubs only — soft signal)
    city = " ".join(
        [
            str(meta.get("city") or ""),
            str(row.get("city") or ""),
            str(meta.get("query") or ""),
        ]
    ).lower()
    de_hubs = (
        "berlin", "hamburg", "münchen", "munich", "köln", "cologne", "frankfurt",
        "stuttgart", "düsseldorf", "dortmund", "essen", "leipzig", "dresden",
        "hannover", "nürnberg", "bremen", "pirna",
    )
    us_hubs = (
        "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
        "san antonio", "san diego", "dallas", "austin", "miami", "seattle", "denver",
    )
    ua_hubs = ("kyiv", "kiev", "київ", "kharkiv", "харків", "odesa", "одеса", "lviv", "львів", "dnipro")
    ru_hubs = ("москва", "moscow", "санкт-петербург", "spb", "казань", "новосибирск")
    if any(h in city for h in de_hubs):
        return "DE"
    if any(h in city for h in us_hubs):
        return "US"
    if any(h in city for h in ua_hubs):
        return "UA"
    if any(h in city for h in ru_hubs):
        return "RU"
    return None


def language_for_market(market: str | None) -> str | None:
    if not market:
        return None
    try:
        from app.integration.outreach_market_config import market_template_lang

        hit = market_template_lang(market)
        if hit:
            return hit
    except Exception:
        pass
    m = normalize_market_code(market) or market.upper()
    return _MARKET_TO_LANG.get(m)


# --- Path A templates (CEO review) -------------------------------------------------

_TEMPLATES: dict[str, dict[str, str]] = {
    # DE — formal, Sie, no hype
    "de": {
        "subject": "{company} — Vorschlag für einen digitalen Neustart (Landing Page)",
        "greeting": "Guten Tag,",
        "intro": (
            "wir haben uns den Online-Auftritt von {company} angesehen. "
            "Anstelle einer aufwendigen Sanierung eines bestehenden Systems "
            "schlagen wir einen klaren Neustart vor: eine moderne, schnelle Landing Page — "
            "mobil optimiert, mit nachvollziehbarem Weg zu Anruf oder Termin."
        ),
        "issues": "Beobachtungen zum Ist-Zustand:",
        "offer": (
            "Angebot «{package}» · {price:.0f} € (einmalig) — fertige Landing Page "
            "in ca. 5–7 Werktagen als HTML-Dateien für Ihren Hosting-Anbieter. "
            "Optional: Einrichtung auf Ihrer Domain durch uns."
        ),
        "cta": (
            "Wenn das für Sie infrage kommt, finden Sie die Pakete hier "
            "(ohne Verpflichtung):\n{order_url}"
        ),
        "close": "Mit freundlichen Grüßen\nRamish · {brand}",
        "style": "formal_de",
    },
    # EN-US — short / direct
    "en-us": {
        "subject": "{company} — quick idea for a cleaner landing page",
        "greeting": "Hi,",
        "intro": (
            "Took a look at {company}'s site. Instead of patching an old setup, "
            "we ship a fresh, fast landing page — mobile-first, clear path to call or book."
        ),
        "issues": "What stood out:",
        "offer": (
            "«{package}» · €{price:.0f} one-time — live HTML in about 5–7 business days. "
            "Optional: we put it on your domain."
        ),
        "cta": "Packages (no obligation):\n{order_url}",
        "close": "Thanks,\nRamish · {brand}",
        "style": "short_us",
    },
    # keep "en" as alias of en-us for older callers
    "en": {
        "subject": "{company} — quick idea for a cleaner landing page",
        "greeting": "Hi,",
        "intro": (
            "Took a look at {company}'s site. Instead of patching an old setup, "
            "we ship a fresh, fast landing page — mobile-first, clear path to call or book."
        ),
        "issues": "What stood out:",
        "offer": (
            "«{package}» · €{price:.0f} one-time — live HTML in about 5–7 business days. "
            "Optional: we put it on your domain."
        ),
        "cta": "Packages (no obligation):\n{order_url}",
        "close": "Thanks,\nRamish · {brand}",
        "style": "short_us",
    },
    # RU — contextual / trust
    "ru": {
        "subject": "{company} — аккуратный цифровой перезапуск сайта",
        "greeting": "Здравствуйте,",
        "intro": (
            "посмотрели онлайн-присутствие {company}. "
            "Мы не предлагаем «починить старый CMS», а сделать понятный перезапуск: "
            "современную быструю Landing Page — удобно с телефона, с ясным путём к звонку или заявке."
        ),
        "issues": "Что заметили по текущему состоянию:",
        "offer": (
            "Пакет «{package}» · {price:.0f} € разово — готовая страница за ~5–7 рабочих дней "
            "(HTML под ваш хостинг). По желанию поможем выложить на ваш домен."
        ),
        "cta": "Пакеты и оформление (без обязательств):\n{order_url}",
        "close": "С уважением,\nRamish · {brand}",
        "style": "contextual_ru",
    },
    # UA — contextual / trust
    "uk": {
        "subject": "{company} — акуратний цифровий перезапуск сайту",
        "greeting": "Доброго дня,",
        "intro": (
            "переглянули онлайн-присутність {company}. "
            "Ми не пропонуємо «лагодити старий CMS», а зробити зрозумілий перезапуск: "
            "сучасну швидку Landing Page — зручно з телефону, з ясним шляхом до дзвінка чи заявки."
        ),
        "issues": "Що помітили зараз:",
        "offer": (
            "Пакет «{package}» · {price:.0f} € разово — готова сторінка за ~5–7 робочих днів "
            "(HTML під ваш хостинг). За бажанням допоможемо викласти на ваш домен."
        ),
        "cta": "Пакети та оформлення (без зобов’язань):\n{order_url}",
        "close": "З повагою,\nRamish · {brand}",
        "style": "contextual_ua",
    },
}

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
            "Angebot «{package}» · {price:.0f} € — Fokus: Termin-/Kontaktweg, Leistungen, "
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
            "Angebot «{package}» · {price:.0f} € — Fokus: Patientenanfragen, Terminweg, "
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
            "Angebot «{package}» · {price:.0f} € — Fokus: Anfragen, Leistungen, Vertrauen. "
            "Fertige Landing Page in ca. 5–7 Werktagen (HTML). Optional: Upload durch uns."
        ),
    },
}

_LANG_MARKERS: dict[str, tuple[str, ...]] = {
    "de": ("guten tag", "ihr", "website", "öffnungszeiten", "kein https", "seitentitel"),
    "en": ("hello", "your website", "contact form", "opening hours", "no https", "page title"),
    "uk": ("доброго", "сайт", "заявк", "київ", "україн"),
    "ru": ("здравствуйте", "сайт", "заявк", "москв"),
}


def preview_market_templates(*, company: str = "Muster GmbH", price: float = 350.0) -> list[dict[str, str]]:
    """CEO review samples — one draft per Path A market language."""
    svc = OutreachLanguageService()
    out: list[dict[str, str]] = []
    for market, lang in (("DE", "de"), ("US", "en-us"), ("RU", "ru"), ("UA", "uk")):
        subject, body, used = svc.draft_outreach(
            company=company,
            analysis={"issues": ["Mobile weak", "No clear contact path"]},
            package={"name": "Landing Basic"},
            price=price,
            fit_reason="Path A preview",
            language=lang,
            row={"market": market, "meta": {"market": market}},
            allow_llm=False,
        )
        out.append(
            {
                "market": market,
                "language": used,
                "style": str(_TEMPLATES.get(used, {}).get("style") or ""),
                "subject": subject,
                "body": body,
            }
        )
    return out


class OutreachLanguageService:
    """Draft sniper outreach in the market's language (templates → optional LLM)."""

    def detect_language(self, row: dict[str, Any]) -> str:
        market = resolve_market_from_row(row)
        by_market = language_for_market(market)
        if by_market:
            return by_market

        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        declared = str(analysis.get("detected_lang") or "").lower().strip()
        if declared and len(declared) <= 8:
            base = declared.split("-")[0]
            if base == "en":
                return "en-us"
            if base in _TEMPLATES:
                return base

        meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
        if meta.get("outreach_language"):
            raw = str(meta["outreach_language"]).split("-")[0]
            return "en-us" if raw == "en" else raw

        blob = " ".join(
            [
                str(analysis.get("title") or ""),
                " ".join(str(i) for i in (analysis.get("issues") or [])),
                str(row.get("fit_reason") or ""),
            ]
        ).lower()

        if re.search(r"[іїєґ]", blob):
            return "uk"
        if re.search(r"[\u0400-\u04FF]", blob):
            return "ru"

        scores: dict[str, int] = {lang: 0 for lang in _LANG_MARKERS}
        for lang, markers in _LANG_MARKERS.items():
            for m in markers:
                if m in blob:
                    scores[lang] += 1
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return "en-us" if best == "en" else best
        return "en-us"

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
        allow_llm: bool = True,
    ) -> tuple[str, str, str]:
        market = resolve_market_from_row(row)
        lang = (
            language
            or language_for_market(market)
            or (self.detect_language(row) if row else None)
            or "en-us"
        )
        lang = str(lang).lower().strip()
        if lang in ("en", "en-gb", "en-us"):
            lang = "en-us"
        elif "-" in lang and lang not in _TEMPLATES:
            lang = lang.split("-")[0]
        if lang not in _TEMPLATES:
            lang = "en-us"

        if allow_llm:
            llm_lang = "en" if lang == "en-us" else lang
            llm_draft = _AI.generate_personalized_offer(
                company=company,
                analysis=analysis or {},
                language=llm_lang,
                package_name=str(package.get("name", "Web")),
                price_eur=price,
                fit_reason=fit_reason,
            )
            if llm_draft:
                return llm_draft["subject"], llm_draft["body"], lang

        tpl = dict(_TEMPLATES.get(lang) or _TEMPLATES["en-us"])
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
        if lang == "de":
            empty_issue = "• Online-Auftritt wirkt ausbaufähig"
        elif lang == "ru":
            empty_issue = "• Есть запас по ясности и мобильной версии"
        elif lang == "uk":
            empty_issue = "• Є запас за ясністю та мобільною версією"
        else:
            empty_issue = "• Room to tighten mobile + contact path"
        issues_block = (
            "\n".join(f"• {i}" for i in issues[:7]) if issues else empty_issue
        )

        subject = tpl["subject"].format(company=company)
        order_url = public_order_url(market=market)
        body = (
            f"{tpl['greeting']}\n\n"
            f"{tpl['intro'].format(company=company)}\n\n"
            f"{tpl['issues']}\n{issues_block}\n\n"
            f"{tpl['offer'].format(package=package.get('name', 'Web'), price=price)}\n\n"
            f"{tpl['cta'].format(order_url=order_url)}\n\n"
            f"{tpl['close'].format(brand=BRAND_NAME)}\n"
        )
        return subject, body, lang
