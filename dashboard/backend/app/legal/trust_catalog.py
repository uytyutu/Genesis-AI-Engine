"""Trust catalog — product-facing transparency + Security Center architecture (horizon)."""

from __future__ import annotations

from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
from app.legal.entity_schema import LegalEntityConfig
from app.legal.locale_registry import localization_horizon_payload


def build_trust_checklist() -> list[dict[str, str]]:
    """Product-facing trust promises — visible on /trust, not buried in legal docs."""
    return [
        {
            "id": "data_protected",
            "icon": "lock",
            "emoji": "🔒",
            "title": "Ihre Daten sind geschützt",
            "body": (
                "Wir speichern nur, was für Ihr Projekt und den Vertrag nötig ist. "
                "Zugang haben nur Virtus Core und die Dienstleister, die wir für den Betrieb brauchen."
            ),
        },
        {
            "id": "project_ownership",
            "icon": "document",
            "emoji": "📄",
            "title": "Ihr Projekt gehört Ihnen",
            "body": (
                "Nach einer Einmalkauf-Leistung erhalten Sie das Ergebnis und die vereinbarten Nutzungsrechte. "
                "Bei Abo bleibt das Projekt in Virtus Core — mit voller Historie und Zugriff für Sie."
            ),
        },
        {
            "id": "full_delivery",
            "icon": "archive",
            "emoji": "💾",
            "title": "Nach dem Kauf erhalten Sie alles, was zur Leistung gehört",
            "body": (
                "Projekt, Dateien, Anleitungen — klar aufgelistet. "
                "Keine versteckten „Premium-Extras“ für das, was im Paket stand."
            ),
        },
        {
            "id": "no_data_sales",
            "icon": "handshake",
            "emoji": "🤝",
            "title": "Wir verkaufen Ihre Daten nicht",
            "body": (
                "Ihre personenbezogenen Daten werden nicht an Dritte verkauft. "
                "Weitergabe nur zur Vertragserfüllung oder wenn das Gesetz es verlangt."
            ),
        },
        {
            "id": "market_compliance",
            "icon": "globe",
            "emoji": "🌍",
            "title": "Arbeit nach den Anforderungen Ihres Marktes",
            "body": (
                "Wir berücksichtigen den Zielmarkt Ihres Projekts — z. B. Datenschutz, Sprache, "
                "lokale Pflichtangaben. Details in den rechtlichen Dokumenten für Ihre Region."
            ),
        },
    ]


def build_data_storage_guide(cfg: LegalEntityConfig) -> list[dict[str, str]]:
    """Plain-language storage transparency — no legal jargon."""
    dp = cfg.data_processing
    op = cfg.operator
    contact = op.email.strip() or "hello@genesis-ai-engine.com"
    return [
        {
            "id": "what",
            "question": "Was speichern wir?",
            "answer": (
                "Kontaktdaten und Bestellinfos, Ihr Projekt (Chat, hochgeladene Dateien, Ergebnisse), "
                "technische Logs zum Schutz der Plattform und Zahlungsmetadaten über unseren Zahlungsanbieter."
            ),
        },
        {
            "id": "why",
            "question": "Wozu?",
            "answer": (
                f"Damit {ASSISTANT_NAME} Ihr Projekt umsetzen kann, wir Sie erreichen, "
                "Rechnungen erstellen und die Plattform sicher betreiben."
            ),
        },
        {
            "id": "where",
            "question": "Wo?",
            "answer": f"Primär in: {dp.data_location}. Konkrete Anbieter nennen wir in der Datenschutzerklärung.",
        },
        {
            "id": "how_long",
            "question": "Wie lange?",
            "answer": (
                f"Projektdaten: bis zu {dp.retention_project_days} Tage nach letzter Aktivität. "
                f"Technische Logs: {dp.retention_logs_days} Tage. "
                f"Rechnungsdaten: bis zu {dp.retention_order_days} Tage (gesetzliche Pflichten)."
            ),
        },
        {
            "id": "delete_project",
            "question": "Wie lösche ich ein Projekt?",
            "answer": (
                f"Schreiben Sie an {contact} mit dem Betreff „Projekt löschen“. "
                f"Wir bearbeiten die Anfrage innerhalb von {dp.deletion_on_request_days} Tagen "
                "und bestätigen, was entfernt wurde."
            ),
        },
        {
            "id": "delete_account",
            "question": "Was passiert, wenn ich mein Konto lösche?",
            "answer": (
                "Aktive Projektdaten und Chat-Verläufe werden nach Ihrer Anfrage gelöscht, "
                "soweit keine gesetzliche Aufbewahrungspflicht besteht (z. B. Rechnungen). "
                "Backups werden im üblichen Turnus überschrieben. "
                "Einmalkauf-Ergebnisse, die Sie bereits heruntergeladen haben, liegen bei Ihnen."
            ),
        },
    ]


def build_trust_catalog(cfg: LegalEntityConfig) -> dict[str, Any]:
    dp = cfg.data_processing
    return {
        "version": "legal-trust-v2",
        "brand": BRAND_NAME,
        "trust_checklist": build_trust_checklist(),
        "data_storage_guide": build_data_storage_guide(cfg),
        "principles": [
            "Welche Daten gesammelt werden — offen benannt",
            "Wofür sie gebraucht werden — nur für den Dienst",
            "Wo sie gespeichert werden — Region aus Konfiguration",
            "Wer Zugriff hat — Virtus Core, Auftragsverarbeiter, nicht „alle“",
            "Wie lange — mit konkreten Fristen",
            "Wann gelöscht — auf Anfrage und nach Fristen",
            "Niemals verkauft an Dritte",
        ],
        "data_collected": [
            {"id": "contact", "label": "Kontakt- und Bestelldaten", "purpose": "Vertrag, Support"},
            {"id": "project", "label": "Projektdaten (Chat, Dateien, Stimme)", "purpose": "Leistungserbringung"},
            {"id": "ai", "label": "KI-Eingaben an Vector", "purpose": "Konzepte und Ergebnisse"},
            {"id": "technical", "label": "Technische Logs", "purpose": "Sicherheit"},
            {"id": "payment", "label": "Zahlungsmetadaten", "purpose": "Abrechnung (über Stripe o. ä.)"},
        ],
        "retention": {
            "project_days": dp.retention_project_days,
            "logs_days": dp.retention_logs_days,
            "order_days": dp.retention_order_days,
            "deletion_request_days": dp.deletion_on_request_days,
        },
        "storage_location": dp.data_location,
        "access": {
            "owner_team": "Virtus Core Betrieb",
            "processors": {
                "hosting": dp.hosting_providers,
                "payment": dp.payment_providers,
                "email": dp.email_providers,
                "ai": dp.ai_providers,
                "analytics": dp.analytics_providers,
            },
            "never_sold": dp.never_sold_to_third_parties,
        },
        "localization": localization_horizon_payload(),
        "security_center_horizon": {
            "status": "architecture_only",
            "planned_modules": [
                "Schutzstatus",
                "Backups",
                "Aktive Sitzungen",
                "Verdächtige Anmeldungen",
                "API-Schlüssel",
                "Audit-Logs",
            ],
            "internal_security": [
                "Owner-only API-Routen",
                "Digitale Signaturen (Horizon)",
                "Rollen und Änderungsjournal",
            ],
        },
        "interview_completed": cfg.interview_completed,
        "publishable_impressum": cfg.is_impressum_publishable(),
        "publishable_datenschutz": cfg.is_datenschutz_publishable(),
    }


def trust_rules_for_vector() -> str:
    return f"""## Trust — Teil des Produkts, nicht nur Juristisches

Zeige Kunden die **Trust Checklist** (/trust):
🔒 Daten geschützt · 📄 Projekt gehört Ihnen · 💾 volle Lieferung · 🤝 keine Datenverkäufe · 🌍 Marktanforderungen

Bei Datenfragen: /trust (einfache Sprache) + /datenschutz (rechtlich).

Nach Zahlung: Übergabe in **menschlicher Sprache** — siehe Handoff-Regeln.

Security Center — Horizon (Architektur geplant, nicht alles live)."""
