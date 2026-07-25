"""Detect confirmed digital needs from audit HTML/flags — heuristics only."""

from __future__ import annotations

from typing import Any

# Markers = evidence the capability likely exists. Absence → confirmed gap.
_CRM_MARKERS = (
    "hubspot",
    "pipedrive",
    "salesforce",
    "force.com",
    "zoho",
    "freshsales",
    "freshworks",
    "intercom",
    "bitrix24",
    "amocrm",
    "amo.crm",
    "close.com",
    "copper.com",
    "insightly",
    "capsulecrm",
    "monday.com/crm",
    "attio.com",
)

_BOOKING_MARKERS = (
    "calendly.com",
    "simplybook",
    "booksy",
    "acuityscheduling",
    "setmore",
    "terminland",
    "reservio",
    "youcanbook.me",
    "bookafy",
    "appointlet",
    "supersaas",
    "vcita.com",
)

_EMAIL_MARKETING_MARKERS = (
    "list-manage.com",
    "mailchimp",
    "klaviyo",
    "brevo.com",
    "sendinblue",
    "mailerlite",
    "activecampaign",
    "getresponse",
    "convertkit",
    "omnisend",
    "newsletter-signup",
    "mc.us",
)

NEED_META: dict[str, dict[str, str]] = {
    "crm": {
        "id": "crm",
        "label_ru": "CRM отсутствует",
        "label_de": "Keine CRM erkannt",
        "label_en": "No CRM detected",
        "why_ru": "На сайте не обнаружены признаки CRM (HubSpot, Pipedrive, Bitrix24 и т.п.).",
        "why_de": "Keine CRM-Signaturen auf der Website erkannt.",
        "why_en": "No CRM signatures (HubSpot, Pipedrive, Bitrix24, etc.) found on the site.",
    },
    "online_booking": {
        "id": "online_booking",
        "label_ru": "Онлайн-запись отсутствует",
        "label_de": "Keine Online-Terminbuchung",
        "label_en": "No online booking detected",
        "why_ru": "Не найдены виджеты онлайн-записи (Calendly, SimplyBook, Booksy и т.п.).",
        "why_de": "Keine Buchungs-Widgets (Calendly, SimplyBook, …) gefunden.",
        "why_en": "No online booking widgets (Calendly, SimplyBook, Booksy, etc.) found.",
    },
    "email_marketing": {
        "id": "email_marketing",
        "label_ru": "Email-маркетинг отсутствует",
        "label_de": "Kein E-Mail-Marketing erkannt",
        "label_en": "No email marketing detected",
        "why_ru": "Не обнаружены инструменты email-маркетинга (Mailchimp, Brevo, Klaviyo и т.п.).",
        "why_de": "Keine E-Mail-Marketing-Tools (Mailchimp, Brevo, …) erkannt.",
        "why_en": "No email marketing tools (Mailchimp, Brevo, Klaviyo, etc.) detected.",
    },
}


def _has_any(haystack: str, markers: tuple[str, ...]) -> bool:
    return any(m in haystack for m in markers)


def detect_confirmed_needs(
    *,
    html: str = "",
    flags: dict[str, Any] | None = None,
    fetch_ok: bool = True,
) -> list[dict[str, Any]]:
    """Return only needs that are confirmed gaps. Empty if fetch failed."""
    del flags  # reserved for future structured signals
    if not fetch_ok:
        return []
    lower = (html or "").lower()
    # Thin/empty page — still allow gap detection if we have any markup
    if len(lower) < 80:
        return []

    needs: list[dict[str, Any]] = []
    checks = (
        ("crm", _CRM_MARKERS),
        ("online_booking", _BOOKING_MARKERS),
        ("email_marketing", _EMAIL_MARKETING_MARKERS),
    )
    for need_id, markers in checks:
        if _has_any(lower, markers):
            continue
        meta = NEED_META[need_id]
        needs.append(
            {
                "id": need_id,
                "confirmed": True,
                "label_ru": meta["label_ru"],
                "label_de": meta["label_de"],
                "label_en": meta["label_en"],
                "why_ru": meta["why_ru"],
                "why_de": meta["why_de"],
                "why_en": meta["why_en"],
                "evidence": "markers_absent",
            }
        )
    return needs
