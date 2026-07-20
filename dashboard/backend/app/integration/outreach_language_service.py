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

CEO_NAME = "Ramish Oltiiev"

# Localized sign-off — full name + title + Virtus Core for the recipient.
_OUTREACH_CLOSE: dict[str, str] = {
    "de": f"Mit freundlichen Grüßen\n{CEO_NAME}\nGeschäftsführer · Virtus Core für Sie",
    "en-us": f"Thanks,\n{CEO_NAME}\nManaging Director · Virtus Core for you",
    "en": f"Thanks,\n{CEO_NAME}\nManaging Director · Virtus Core for you",
    "ru": f"С уважением,\n{CEO_NAME}\nГенеральный директор · Virtus Core для вас",
    "uk": f"З повагою,\n{CEO_NAME}\nГенеральний директор · Virtus Core для вас",
    "cs": f"S pozdravem\n{CEO_NAME}\nGenerální ředitel · Virtus Core pro vás",
}


def outreach_signoff(lang: str) -> str:
    key = (lang or "en-us").lower().strip()
    if key in ("en", "en-gb"):
        key = "en-us"
    elif "-" in key and key not in _OUTREACH_CLOSE:
        key = key.split("-")[0]
    return _OUTREACH_CLOSE.get(key) or _OUTREACH_CLOSE["en-us"]

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
    "NZ": "en-us",
    "FR": "en-us",
    "IT": "en-us",
    "ES": "en-us",
    "NL": "en-us",
    "BE": "en-us",
    "PT": "en-us",
    "PL": "en-us",
    "RO": "en-us",
    "SK": "en-us",
    "CZ": "cs",
    "RU": "ru",
    "UA": "uk",
    "BY": "ru",
    "KZ": "ru",
    "CIS": "ru",
}


def public_order_url(*, market: str | None = None) -> str:
    """Public Path A checkout — ?market= so checkout shows local currency."""
    from app.integration.public_site_url import configured_public_base

    base = configured_public_base()
    url = f"{base}/order"
    m = (market or "").strip().upper()
    if m:
        return f"{url}?market={m}"
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
            str(meta.get("hunt_city") or ""),
            str(row.get("city") or ""),
            str(row.get("hunt_city") or ""),
            str(meta.get("query") or ""),
            str(row.get("company_name") or ""),
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
    cz_hubs = ("praha", "prague", "brno", "ostrava", "plzeň", "plzen", "liberec", "olomouc")
    pl_hubs = ("warsaw", "warszawa", "krakow", "kraków", "wrocław", "wroclaw", "gdańsk", "gdansk", "poznań", "poznan")
    ro_hubs = ("bucharest", "bucurești", "bucuresti", "cluj", "timisoara", "iași", "iasi")
    pt_hubs = ("lisboa", "lisbon", "porto", "faro", "braga")
    if any(h in city for h in de_hubs):
        return "DE"
    if any(h in city for h in us_hubs):
        return "US"
    if any(h in city for h in ua_hubs):
        return "UA"
    if any(h in city for h in ru_hubs):
        return "RU"
    if any(h in city for h in cz_hubs):
        return "CZ"
    if any(h in city for h in pl_hubs):
        return "PL"
    if any(h in city for h in ro_hubs):
        return "RO"
    if any(h in city for h in pt_hubs):
        return "PT"
    # Price-label / website TLD soft signals (when market field was lost)
    blob = " ".join(
        [
            str(row.get("recommended_price_label") or ""),
            str(meta.get("recommended_price_label") or ""),
            str(row.get("proposed_message") or "")[:400],
            str(row.get("website_url") or ""),
        ]
    )
    low = blob.lower()
    if "kč" in blob or ".cz" in low:
        return "CZ"
    if "zł" in blob or ".pl" in low:
        return "PL"
    if "₴" in blob or ".ua" in low:
        return "UA"
    if (".ro" in low) and ("lei" in low or "bucure" in city or "romania" in low):
        return "RO"
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
    # DE — company voice, concrete offer
    "de": {
        "subject": "{company}: unser Angebot für Ihren digitalen Neustart",
        "greeting": "Guten Tag,",
        "intro": (
            "hier schreibt Ramish Oltiiev, Geschäftsführer von {brand}. "
            "Wir haben den Online-Auftritt von {company} geprüft — "
            "und möchten Ihnen als Team ein klares Angebot machen: "
            "statt Flickwerk am alten System eine neue, schnelle Landing Page, "
            "die mobil überzeugt und Anrufe/Termine leichter macht."
        ),
        "issues": "Was uns am Ist-Zustand aufgefallen ist:",
        "offer": (
            "Unser Angebot «{package}» · {price_label} einmalig — fertige Landing Page "
            "oft in ca. 15 Minuten als HTML für Ihren Host. "
            "Optional richten wir die Seite auf Ihrer Domain für Sie ein."
        ),
        "cta": (
            "Wenn das zu {company} passt, sehen Sie Pakete und Preis hier "
            "(ohne Verpflichtung):\n{order_url}"
        ),
        "close": _OUTREACH_CLOSE["de"],
        "style": "formal_de",
    },
    # EN-US — short company pitch
    "en-us": {
        "subject": "{company}: a concrete offer from {brand}",
        "greeting": "Hi,",
        "intro": (
            "This is Ramish Oltiiev, Managing Director at {brand}. We reviewed {company}'s "
            "online presence and want to put a clear offer on the table: a fresh, fast landing page — "
            "mobile-first, with a clean path to call or book — instead of patching an old stack."
        ),
        "issues": "What stood out on the current site:",
        "offer": (
            "Our package «{package}» · {price_label} one-time — finished HTML often in about "
            "15 minutes. Optional: we place it on your domain."
        ),
        "cta": "See packages and pricing (no obligation):\n{order_url}",
        "close": _OUTREACH_CLOSE["en-us"],
        "style": "short_us",
    },
    "en": {
        "subject": "{company}: a concrete offer from {brand}",
        "greeting": "Hi,",
        "intro": (
            "This is Ramish Oltiiev, Managing Director at {brand}. We reviewed {company}'s "
            "online presence and want to put a clear offer on the table: a fresh, fast landing page — "
            "mobile-first, with a clean path to call or book — instead of patching an old stack."
        ),
        "issues": "What stood out on the current site:",
        "offer": (
            "Our package «{package}» · {price_label} one-time — finished HTML often in about "
            "15 minutes. Optional: we place it on your domain."
        ),
        "cta": "See packages and pricing (no obligation):\n{order_url}",
        "close": _OUTREACH_CLOSE["en"],
        "style": "short_us",
    },
    # RU
    "ru": {
        "subject": "{company}: предложение от {brand} по перезапуску сайта",
        "greeting": "Здравствуйте,",
        "intro": (
            "пишет Ramish Oltiiev, генеральный директор {brand}. "
            "Мы посмотрели онлайн-присутствие {company} "
            "и хотим дать живое предложение от нашей команды: не «чинить старый CMS», "
            "а сделать понятный перезапуск — современную быструю Landing Page "
            "с ясным путём к звонку или заявке."
        ),
        "issues": "Что заметили по текущему состоянию:",
        "offer": (
            "Наш пакет «{package}» · {price_label} разово — готовая страница часто за ~15 минут "
            "(HTML под ваш хостинг). По желанию поможем выложить на ваш домен."
        ),
        "cta": "Пакеты и оформление (без обязательств):\n{order_url}",
        "close": _OUTREACH_CLOSE["ru"],
        "style": "contextual_ru",
    },
    # UA — hryvnia in price_label
    "uk": {
        "subject": "{company}: пропозиція від {brand} щодо перезапуску сайту",
        "greeting": "Доброго дня,",
        "intro": (
            "пише Ramish Oltiiev, генеральний директор {brand}. "
            "Ми переглянули онлайн-присутність {company} "
            "і хочемо дати живу пропозицію від нашої команди: не «лагодити старий CMS», "
            "а зробити зрозумілий перезапуск — сучасну швидку Landing Page "
            "з ясним шляхом до дзвінка чи заявки."
        ),
        "issues": "Що помітили зараз:",
        "offer": (
            "Наш пакет «{package}» · {price_label} разово — готова сторінка часто за ~15 хвилин "
            "(HTML під ваш хостинг). За бажанням допоможемо викласти на ваш домен."
        ),
        "cta": "Пакети та оформлення (без зобов’язань):\n{order_url}",
        "close": _OUTREACH_CLOSE["uk"],
        "style": "contextual_ua",
    },
    # CS — Czech crowns via price_label
    "cs": {
        "subject": "{company}: nabídka od {brand} na nový web",
        "greeting": "Dobrý den,",
        "intro": (
            "píše Ramish Oltiiev, generální ředitel {brand}. "
            "Prohlédli jsme online prezentaci firmy {company} "
            "a chceme vám jako tým dát konkrétní nabídku: místo oprav starého CMS "
            "novou rychlou landing page — přehlednou v mobilu, s jasnou cestou k hovoru nebo poptávce."
        ),
        "issues": "Co nás na současném stavu zaujalo:",
        "offer": (
            "Naše nabídka «{package}» · {price_label} jednorázově — hotová landing page "
            "často do cca 15 minut (HTML pro váš hosting). "
            "Volitelně stránku nasadíme na vaši doménu."
        ),
        "cta": "Balíčky a ceny (bez závazku):\n{order_url}",
        "close": _OUTREACH_CLOSE["cs"],
        "style": "formal_cs",
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
            "Angebot «{package}» · {price_label} — Fokus: Termin-/Kontaktweg, Leistungen, "
            "Vertrauen. Fertige Landing Page oft in ca. 15 Minuten "
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
            "Angebot «{package}» · {price_label} — Fokus: Patientenanfragen, Terminweg, "
            "Praxis-Vertrauen. Fertige Landing Page oft in ca. 15 Minuten "
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
            "Angebot «{package}» · {price_label} — Fokus: Anfragen, Leistungen, Vertrauen. "
            "Fertige Landing Page oft in ca. 15 Minuten (HTML). Optional: Upload durch uns."
        ),
    },
}

_LANG_MARKERS: dict[str, tuple[str, ...]] = {
    "de": ("guten tag", "ihr", "website", "öffnungszeiten", "kein https", "seitentitel"),
    "en": ("hello", "your website", "contact form", "opening hours", "no https", "page title"),
    "uk": ("доброго", "сайт", "заявк", "київ", "україн"),
    "ru": ("здравствуйте", "сайт", "заявк", "москв"),
}


def preview_market_templates(*, company: str = "Muster GmbH", price: float | None = None) -> list[dict[str, str]]:
    """CEO review samples — one draft per Path A market language (market-local price)."""
    from app.integration.commerce_engine import resolve_final_offer

    svc = OutreachLanguageService()
    out: list[dict[str, str]] = []
    for market, lang in (("DE", "de"), ("US", "en-us"), ("RU", "ru"), ("UA", "uk")):
        offer = resolve_final_offer("basic", market)
        sample_price = float(price) if price is not None else float(offer.amount)
        subject, body, used = svc.draft_outreach(
            company=company,
            analysis={"issues": ["Mobile weak", "No clear contact path"]},
            package={"name": "Landing Basic", "price_label": offer.price_label},
            price=sample_price,
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
                "price_label": offer.price_label,
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
            price_label_llm = str(package.get("price_label") or "").strip()
            if not price_label_llm:
                try:
                    from app.integration.market_registry import format_amount, get_market

                    mkt = get_market(market or "DE")
                    price_label_llm = format_amount(int(round(float(price))), mkt.symbol)
                except Exception:
                    price_label_llm = f"{float(price):.0f} €"
            llm_draft = _AI.generate_personalized_offer(
                company=company,
                analysis=analysis or {},
                language=llm_lang,
                package_name=str(package.get("name", "Web")),
                price_eur=price,
                price_label=price_label_llm,
                currency=str(package.get("currency") or ""),
                market=market or "",
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
        elif lang == "cs":
            empty_issue = "• Je prostor zlepšit mobil a cestu ke kontaktu"
        else:
            empty_issue = "• Room to tighten mobile + contact path"
        issues_block = (
            "\n".join(f"• {i}" for i in issues[:7]) if issues else empty_issue
        )

        subject = tpl["subject"].format(company=company, brand=BRAND_NAME)
        order_url = public_order_url(market=market)
        price_label = str(package.get("price_label") or "").strip()
        if not price_label:
            try:
                from app.integration.market_registry import format_amount, get_market

                m = get_market(market or "DE")
                price_label = format_amount(int(round(float(price))), m.symbol)
            except Exception:
                price_label = f"{float(price):.0f} €"
        body = (
            f"{tpl['greeting']}\n\n"
            f"{tpl['intro'].format(company=company, brand=BRAND_NAME)}\n\n"
            f"{tpl['issues']}\n{issues_block}\n\n"
            f"{tpl['offer'].format(package=package.get('name', 'Web'), price_label=price_label)}\n\n"
            f"{tpl['cta'].format(order_url=order_url, company=company)}\n\n"
            f"{outreach_signoff(lang)}\n"
        )
        return subject, body, lang
