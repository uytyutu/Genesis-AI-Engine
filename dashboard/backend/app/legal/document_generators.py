"""Generate legal documents from LegalEntityConfig — not static templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
from app.legal.locale_registry import DEFAULT_MARKET
from app.legal.entity_schema import (
    ALL_LEGAL_DOCUMENTS,
    DOCUMENT_AGB,
    DOCUMENT_AI_DISCLAIMER,
    DOCUMENT_COOKIES,
    DOCUMENT_DATENSCHUTZ,
    DOCUMENT_IMPRESSUM,
    DOCUMENT_INTELLECTUAL_PROPERTY,
    DOCUMENT_LABELS,
    DOCUMENT_WIDERRUF,
    LegalEntityConfig,
)


@dataclass
class LegalSection:
    heading: str
    body: str

    def to_dict(self) -> dict[str, str]:
        return {"heading": self.heading, "body": self.body}


@dataclass
class LegalDocument:
    id: str
    title: str
    locale: str
    subtitle: str
    publishable: bool
    missing_fields: list[str]
    sections: list[LegalSection]
    disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "locale": self.locale,
            "subtitle": self.subtitle,
            "publishable": self.publishable,
            "missing_fields": self.missing_fields,
            "sections": [s.to_dict() for s in self.sections],
            "disclaimer": self.disclaimer,
        }


def _providers_list(items: list[str], fallback: str) -> str:
    return ", ".join(items) if items else fallback


def generate_impressum(cfg: LegalEntityConfig, *, locale: str = "de") -> LegalDocument:
    op = cfg.operator
    missing = cfg.missing_impressum_fields()
    publishable = not missing
    sections: list[LegalSection] = []

    if publishable:
        body = (
            f"{op.full_name}\n"
            f"{op.trade_name or BRAND_NAME}\n"
            f"{cfg.formatted_address()}\n\n"
            f"E-Mail: {op.email}\n"
        )
        if op.phone.strip():
            body += f"Telefon: {op.phone}\n"
        if op.website.strip():
            body += f"Website: {op.website}\n"
        if op.legal_form.strip():
            body += f"\nRechtsform: {op.legal_form}\n"
        if op.handelsregister.strip():
            body += f"Handelsregister: {op.handelsregister}"
            if op.register_court.strip():
                body += f", Registergericht: {op.register_court}"
            body += "\n"
        if op.managing_director.strip():
            body += f"Vertretungsberechtigt: {op.managing_director}\n"
        if op.vat_id.strip():
            body += f"USt-IdNr.: {op.vat_id}\n"
        sections.append(LegalSection("Anbieterkennzeichnung (§ 5 DDG)", body.strip()))
        sections.append(LegalSection(
            "EU-Streitschlichtung",
            "Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: "
            "https://ec.europa.eu/consumers/odr/",
        ))
        sections.append(LegalSection(
            "Verbraucherstreitbeilegung",
            "Wir sind nicht verpflichtet, an Streitbeilegungsverfahren vor einer "
            "Verbraucherschlichtungsstelle teilzunehmen.",
        ))
    else:
        sections.append(LegalSection(
            "Dokument in Vorbereitung",
            "Dieses Impressum wird aus den offiziellen Unternehmensdaten generiert. "
            "Es wird veröffentlicht, sobald die Legal Foundation Interview abgeschlossen ist.",
        ))

    return LegalDocument(
        id=DOCUMENT_IMPRESSUM,
        title=DOCUMENT_LABELS[DOCUMENT_IMPRESSUM].get(locale, "Impressum"),
        locale=locale,
        subtitle=f"Stand: {cfg.documents_last_review}",
        publishable=publishable,
        missing_fields=missing,
        sections=sections,
        disclaimer="Generiert aus legal_entity.json — keine statische Vorlage.",
    )


def generate_datenschutz(cfg: LegalEntityConfig, *, locale: str = "de") -> LegalDocument:
    op = cfg.operator
    dp = cfg.data_processing
    missing = cfg.missing_datenschutz_fields()
    publishable = cfg.is_datenschutz_publishable()
    sections: list[LegalSection] = []

    if publishable:
        sections.append(LegalSection(
            "1. Verantwortlicher",
            f"{op.full_name} — {op.trade_name or BRAND_NAME}\n{cfg.formatted_address()}\n"
            f"E-Mail: {op.email}" + (f"\nTelefon: {op.phone}" if op.phone else ""),
        ))
        sections.append(LegalSection(
            "2. Welche Daten wir verarbeiten",
            "• Kontakt- und Bestelldaten (Name, E-Mail, Rechnungsdaten)\n"
            "• Projektdaten: Chat, hochgeladene Dateien (PDF, Bilder), Sprachaufnahmen\n"
            "• KI-Verarbeitung: Inhalte, die Sie an Vector übermitteln\n"
            "• Technische Logdaten (IP, Browser, Zeitstempel)\n"
            "• Zahlungsdaten über Zahlungsdienstleister (wir speichern keine vollständigen Kartendaten)",
        ))
        sections.append(LegalSection(
            "3. Zwecke der Verarbeitung",
            "• Erbringung von Dienstleistungen und Projektbetrieb\n"
            "• Vertragserfüllung und Kundensupport\n"
            "• Zahlungsabwicklung\n"
            "• Sicherheit und Missbrauchsprävention\n"
            "• Gesetzliche Aufbewahrungspflichten",
        ))
        sections.append(LegalSection(
            "4. Speicherort und Aufbewahrung",
            f"Speicherort: {dp.data_location}\n"
            f"Projektdaten: bis zu {dp.retention_project_days} Tage nach letzter Aktivität\n"
            f"Server-Logs: {dp.retention_logs_days} Tage\n"
            f"Bestell-/Rechnungsdaten: bis zu {dp.retention_order_days} Tage (gesetzliche Pflichten)\n"
            f"Löschung auf Anfrage: Bearbeitung innerhalb von {dp.deletion_on_request_days} Tagen",
        ))
        sections.append(LegalSection(
            "5. Dienstleister (Auftragsverarbeitung)",
            f"Hosting: {_providers_list(dp.hosting_providers, '—')}\n"
            f"Zahlung: {_providers_list(dp.payment_providers, '—')}\n"
            f"E-Mail: {_providers_list(dp.email_providers, '—')}\n"
            f"KI-Dienste: {_providers_list(dp.ai_providers, '—')}\n"
            f"Analyse: {_providers_list(dp.analytics_providers, 'Keine')}",
        ))
        sections.append(LegalSection(
            "6. Kein Verkauf an Dritte",
            "Wir verkaufen Ihre personenbezogenen Daten nicht an Dritte. "
            "Eine Weitergabe erfolgt nur zur Vertragserfüllung, mit Ihrer Einwilligung "
            "oder auf gesetzlicher Grundlage.",
        ))
        sections.append(LegalSection(
            "7. Ihre Rechte (DSGVO)",
            "Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit, Widerspruch — "
            f"Anfragen an: {op.email}",
        ))
        if dp.supervisory_authority.strip():
            sections.append(LegalSection(
                "8. Aufsichtsbehörde",
                dp.supervisory_authority,
            ))
    else:
        sections.append(LegalSection(
            "Dokument in Vorbereitung",
            "Die Datenschutzerklärung wird aus den offiziellen Unternehmens- und "
            "Verarbeitungsdaten generiert — speziell für KI, Dateien, Stimme und Projektspeicher.",
        ))

    return LegalDocument(
        id=DOCUMENT_DATENSCHUTZ,
        title=DOCUMENT_LABELS[DOCUMENT_DATENSCHUTZ].get(locale, "Datenschutzerklärung"),
        locale=locale,
        subtitle=f"Stand: {cfg.documents_last_review}",
        publishable=publishable,
        missing_fields=missing,
        sections=sections,
    )


def generate_agb(cfg: LegalEntityConfig, *, locale: str = "de") -> LegalDocument:
    op = cfg.operator
    sections = [
        LegalSection(
            "§ 1 Geltungsbereich",
            f"Diese AGB gelten für alle Leistungen von {op.trade_name or BRAND_NAME} "
            f"({ASSISTANT_NAME} — digitale Dienstleistungen).",
        ),
        LegalSection(
            "§ 2 Leistungsarten",
            "**Vector Free** — kostenlose Nutzung mit Limits.\n"
            "**Einmalige Dienstleistungen** — fertiges digitales Ergebnis mit Übergabe.\n"
            "**Abonnements** — fortlaufende Zusammenarbeit; Projekt bleibt in der Plattform.",
        ),
        LegalSection(
            "§ 3 Vertragsschluss",
            "Einmalige Leistungen: Vertrag nach ausdrücklicher Freigabe der Konzeptversion und Zahlung. "
            "Abonnements: nach gesonderter Freischaltung des Tarifs.",
        ),
        LegalSection(
            "§ 4 Leistungsumfang",
            "Umfang ergibt sich aus dem vereinbarten Projekt, der vorläufigen Smete und der "
            "Leistungsbeschreibung im Dialog mit Vector.",
        ),
        LegalSection(
            "§ 5 Widerruf",
            "Es gilt die gesonderte Widerrufsbelehrung. Bei digitalen Inhalten kann das Widerrufsrecht "
            "erlöschen, wenn die Ausführung mit ausdrücklicher Zustimmung vor Fristende beginnt.",
        ),
        LegalSection(
            "§ 6 Haftung",
            "Unbeschränkte Haftung bei Vorsatz und grober Fahrlässigkeit. Im Übrigen gesetzliche Grenzen.",
        ),
    ]
    return LegalDocument(
        id=DOCUMENT_AGB,
        title=DOCUMENT_LABELS[DOCUMENT_AGB].get(locale, "AGB"),
        locale=locale,
        subtitle=f"Stand: {cfg.documents_last_review}",
        publishable=True,
        missing_fields=[],
        sections=sections,
    )


def generate_widerruf(cfg: LegalEntityConfig, *, locale: str = "de") -> LegalDocument:
    op = cfg.operator
    sections = [
        LegalSection(
            "Widerrufsrecht",
            "Verbraucher haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen "
            "diesen Vertrag zu widerrufen.",
        ),
        LegalSection(
            "Digitale Inhalte und Dienstleistungen",
            "Das Widerrufsrecht erlischt bei digitalen Inhalten, wenn wir mit der Ausführung "
            "begonnen haben, nachdem Sie ausdrücklich zugestimmt haben und bestätigt haben, "
            "dass Sie Ihr Widerrufsrecht verlieren.",
        ),
        LegalSection(
            "Kontakt für Widerruf",
            f"{op.full_name or op.trade_name}\n{op.email or '[E-Mail nach Interview]'}",
        ),
    ]
    return LegalDocument(
        id=DOCUMENT_WIDERRUF,
        title=DOCUMENT_LABELS[DOCUMENT_WIDERRUF].get(locale, "Widerrufsbelehrung"),
        locale=locale,
        subtitle=f"Stand: {cfg.documents_last_review}",
        publishable=bool(op.email.strip()),
        missing_fields=[] if op.email.strip() else ["operator.email"],
        sections=sections,
    )


def generate_cookies(cfg: LegalEntityConfig, *, locale: str = "de") -> LegalDocument:
    ck = cfg.cookies
    sections = [
        LegalSection(
            "Notwendige Cookies",
            "\n".join(f"• {c}" for c in ck.essential) or "• Session, Sicherheit",
        ),
        LegalSection(
            "Funktionale Cookies",
            "\n".join(f"• {c}" for c in ck.functional) or "• Spracheinstellung",
        ),
        LegalSection(
            "Analyse-Cookies",
            "\n".join(f"• {c}" for c in ck.analytics) if ck.analytics else "Derzeit keine Analyse-Cookies.",
        ),
        LegalSection(
            "Marketing-Cookies",
            "\n".join(f"• {c}" for c in ck.marketing) if ck.marketing else "Derzeit keine Marketing-Cookies.",
        ),
    ]
    return LegalDocument(
        id=DOCUMENT_COOKIES,
        title=DOCUMENT_LABELS[DOCUMENT_COOKIES].get(locale, "Cookie-Richtlinie"),
        locale=locale,
        subtitle=f"Stand: {cfg.documents_last_review}",
        publishable=True,
        missing_fields=[],
        sections=sections,
    )


def generate_ai_disclaimer(cfg: LegalEntityConfig, *, locale: str = "de") -> LegalDocument:
    loc = (locale or "de").strip().lower()[:2]
    if loc == "ru":
        sections = [
            LegalSection(
                "Использование искусственного интеллекта",
                f"При разработке сайтов и цифровых продуктов {BRAND_NAME} использует инструменты "
                "искусственного интеллекта для ускорения создания дизайна, структуры, текстов, "
                "изображений и других элементов проекта.",
            ),
            LegalSection(
                "Качество и правки",
                "Каждый проект проходит автоматическую проверку качества. После покупки вы можете "
                "запросить изменения, если результат не соответствует вашим ожиданиям.",
            ),
            LegalSection(
                "Что делает ИИ",
                "• анализирует требования проекта\n"
                "• помогает подобрать дизайн и стиль\n"
                "• генерирует первоначальную структуру\n"
                "• создаёт тексты и изображения\n"
                "• ускоряет разработку",
            ),
            LegalSection(
                "Что ИИ не заменяет",
                "• ваши пожелания и решения\n"
                "• возможность внесения изменений\n"
                "• контроль качества готового проекта\n"
                f"• ответственность {ASSISTANT_NAME} и команды {BRAND_NAME} за результат сервиса",
            ),
            LegalSection(
                "Ваши решения",
                f"{ASSISTANT_NAME} поддерживает вас — конечные юридические, финансовые и деловые "
                "решения принимаете вы. Проверяйте важные шаги перед публикацией, договором или оплатой.",
            ),
        ]
        title = DOCUMENT_LABELS[DOCUMENT_AI_DISCLAIMER].get("ru", "Оговорка об ИИ")
        subtitle = f"Актуально: {cfg.documents_last_review}"
    elif loc == "en":
        sections = [
            LegalSection(
                "How we use artificial intelligence",
                f"When developing websites and digital products, {BRAND_NAME} uses artificial "
                "intelligence tools to accelerate design, structure, copy, imagery, and other "
                "project elements.",
            ),
            LegalSection(
                "Quality and edits",
                "Every project goes through automated quality checks. After purchase you can "
                "request changes if the result does not match your expectations.",
            ),
            LegalSection(
                "What AI helps with",
                "• analyzing project requirements\n"
                "• choosing design and style\n"
                "• generating an initial structure\n"
                "• creating copy and imagery\n"
                "• accelerating development",
            ),
            LegalSection(
                "What AI does not replace",
                "• your preferences and decisions\n"
                "• the ability to request changes\n"
                "• quality control of the finished project\n"
                f"• accountability of {ASSISTANT_NAME} and the {BRAND_NAME} team for the service outcome",
            ),
            LegalSection(
                "Your decisions",
                f"{ASSISTANT_NAME} supports you — final legal, financial, and business decisions "
                "remain yours. Review important steps before publishing, contracting, or paying.",
            ),
        ]
        title = "AI notice"
        subtitle = f"As of: {cfg.documents_last_review}"
    else:
        sections = [
            LegalSection(
                "Einsatz künstlicher Intelligenz",
                f"Bei der Entwicklung von Websites und digitalen Produkten setzt {BRAND_NAME} "
                "Werkzeuge der künstlichen Intelligenz ein, um Design, Struktur, Texte, Bilder "
                "und weitere Projektelemente schneller zu erstellen.",
            ),
            LegalSection(
                "Qualität und Änderungen",
                "Jedes Projekt durchläuft eine automatische Qualitätsprüfung. Nach dem Kauf "
                "können Sie Änderungen anfordern, wenn das Ergebnis Ihren Erwartungen nicht entspricht.",
            ),
            LegalSection(
                "Wobei KI unterstützt",
                "• Analyse der Projektanforderungen\n"
                "• Auswahl von Design und Stil\n"
                "• Erstellung der ersten Struktur\n"
                "• Erstellung von Texten und Bildern\n"
                "• Beschleunigung der Entwicklung",
            ),
            LegalSection(
                "Was KI nicht ersetzt",
                "• Ihre Wünsche und Entscheidungen\n"
                "• die Möglichkeit von Änderungen\n"
                "• die Qualitätskontrolle des fertigen Projekts\n"
                f"• die Verantwortung von {ASSISTANT_NAME} und dem Team von {BRAND_NAME} für das Service-Ergebnis",
            ),
            LegalSection(
                "Ihre Entscheidungen zählen",
                f"{ASSISTANT_NAME} kann Vorschläge machen und Entwürfe vorbereiten. "
                "**Endgültige rechtliche, finanzielle und geschäftliche Entscheidungen treffen Sie selbst.** "
                "Prüfen Sie wichtige Schritte — besonders vor Veröffentlichung, Vertragsabschluss oder Zahlung.",
            ),
            LegalSection(
                f"Was {ASSISTANT_NAME} nicht tut",
                "• Keine Rechtsberatung — juristische Texte sind Hilfen, keine Anwaltserklärung\n"
                "• Keine Steuer- oder Finanzberatung — Zahlen und Pläne sind Orientierung, keine Gutachten\n"
                "• Keine automatischen Zahlungen ohne Ihre Bestätigung\n"
                "• Keine Garantie für 100 % rechtliche Konformität ohne Ihre Prüfung\n"
                "• Keine medizinischen Gutachten",
            ),
        ]
        title = DOCUMENT_LABELS[DOCUMENT_AI_DISCLAIMER].get(locale, "KI-Hinweis")
        subtitle = f"Stand: {cfg.documents_last_review}"
    return LegalDocument(
        id=DOCUMENT_AI_DISCLAIMER,
        title=title,
        locale=locale,
        subtitle=subtitle,
        publishable=True,
        missing_fields=[],
        sections=sections,
    )


def generate_intellectual_property(cfg: LegalEntityConfig, *, locale: str = "de") -> LegalDocument:
    sections = [
        LegalSection(
            "Einmalige Dienstleistung — nach Zahlung erhalten Sie",
            "✓ vollständiges Projekt (z. B. Website, Dokumente)\n"
            "✓ Quellcode (HTML, CSS, JS — soweit zur Leistung gehörend)\n"
            "✓ ZIP-Archiv\n"
            "✓ Anleitungen\n"
            "✓ Nutzungsrechte gemäß vereinbarter Lizenz\n"
            "✓ Abschluss der Leistung durch Virtus Core für diese Bestellung",
        ),
        LegalSection(
            "Abonnement — anderes Modell",
            "Das Projekt bleibt in Virtus Core. Sie arbeiten weiter mit Vector. "
            "Nutungsrechte und Exporte richten sich nach dem Abonnementvertrag. "
            "Kein automatischer vollständiger Rechteabtretung wie bei Einmalkauf.",
        ),
        LegalSection(
            "Vorlieferung / Konzeptphase",
            "Bis zur Zahlung und Übergabe bleiben Vorlagen und Konzepte Eigentum von "
            f"{BRAND_NAME}, sofern nicht anders vereinbart.",
        ),
    ]
    return LegalDocument(
        id=DOCUMENT_INTELLECTUAL_PROPERTY,
        title=DOCUMENT_LABELS[DOCUMENT_INTELLECTUAL_PROPERTY].get(locale, "Urheberrecht"),
        locale=locale,
        subtitle=f"Stand: {cfg.documents_last_review}",
        publishable=True,
        missing_fields=[],
        sections=sections,
    )


_GENERATORS = {
    DOCUMENT_IMPRESSUM: generate_impressum,
    DOCUMENT_DATENSCHUTZ: generate_datenschutz,
    DOCUMENT_AGB: generate_agb,
    DOCUMENT_WIDERRUF: generate_widerruf,
    DOCUMENT_COOKIES: generate_cookies,
    DOCUMENT_AI_DISCLAIMER: generate_ai_disclaimer,
    DOCUMENT_INTELLECTUAL_PROPERTY: generate_intellectual_property,
}


def generate_document(
    doc_id: str,
    cfg: LegalEntityConfig,
    *,
    locale: str = "de",
    market: str = DEFAULT_MARKET,
) -> LegalDocument | None:
    _ = market  # Horizon: route doc_id via locale_registry per target market
    gen = _GENERATORS.get(doc_id)
    if not gen:
        return None
    return gen(cfg, locale=locale)


def list_document_catalog(cfg: LegalEntityConfig) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for doc_id in ALL_LEGAL_DOCUMENTS:
        doc = generate_document(doc_id, cfg)
        if doc:
            out.append({
                "id": doc.id,
                "title": doc.title,
                "publishable": doc.publishable,
                "path": f"/{doc.id.replace('_', '-')}",
            })
    return out
