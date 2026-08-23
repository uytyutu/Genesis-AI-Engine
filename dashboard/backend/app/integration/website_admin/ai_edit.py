"""Website Admin AI edit — NL prompt → structured content/design PATCH."""

from __future__ import annotations

import re
import uuid
from typing import Any


def _uid(prefix: str = "item") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _extract_quoted_or_tail(text: str) -> str:
    q = re.search(r"[\"«»„“](.+?)[\"«»„“]", text)
    if q:
        return q.group(1).strip()
    m = re.search(
        r"(?:услуг[ауи]?|service|leistung|dienstleistung)\s*[:\-]?\s*(.+)$",
        text,
        flags=re.I,
    )
    if m:
        return m.group(1).strip(" .")
    return ""


def parse_ai_edit_prompt(prompt: str) -> dict[str, Any]:
    """
    Rule-based intents for Website Control v1.
    Returns { content_patch?, design_patch?, summary }.
    """
    text = (prompt or "").strip()
    low = text.lower().replace("ё", "е")
    if not text:
        raise ValueError("empty_prompt")

    content_patch: dict[str, Any] = {}
    design_patch: dict[str, Any] = {}

    # Add Prices section
    if any(
        k in low
        for k in (
            "раздел цены",
            "раздел «цены»",
            'раздел "цены"',
            "добавь раздел цен",
            "add prices",
            "add price section",
            "preise abschnitt",
            "abschnitt preise",
            "добавь цены",
            "enable prices",
        )
    ):
        content_patch["prices"] = {
            "enabled": True,
            "title": "Preise",
            "intro": "Transparente Preise — ohne Überraschungen.",
            "items": [
                {
                    "id": _uid("price"),
                    "label": "Basis",
                    "price": "ab 49 €",
                    "note": "",
                },
                {
                    "id": _uid("price"),
                    "label": "Premium",
                    "price": "ab 89 €",
                    "note": "",
                },
            ],
        }
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Prices section enabled",
        }

    # Premium tone
    if any(
        k in low
        for k in (
            "премиальн",
            "premium",
            "luxus",
            "luxury",
            "более премиальн",
            "тон сайта",
            "tone",
            "элегантн",
        )
    ) and any(
        k in low
        for k in (
            "тон",
            "tone",
            "стиль",
            "style",
            "замени",
            "сделай",
            "mach",
            "make",
            "премиальн",
            "premium",
            "luxus",
        )
    ):
        content_patch["hero"] = {
            "subheadline": "Exklusiv. Präzise. Für anspruchsvolle Gäste.",
            "cta_label": "Privattermin anfragen",
        }
        content_patch["about"] = {
            "title": "Unsere Haltung",
            "body": (
                "Wir arbeiten ruhig, präzise und ohne Kompromisse — "
                "jedes Detail ist Teil des Erlebnisses."
            ),
        }
        design_patch["colors"] = {
            "primary": "#1c1917",
            "secondary": "#f5f0e8",
            "button": "#a16207",
            "link": "#a16207",
            "background": "#faf7f2",
            "text": "#1c1917",
        }
        design_patch["typography"] = {"font_preset": "dm_fraunces"}
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Premium tone applied to copy and design",
        }

    # Add service
    add_service = any(
        k in low
        for k in (
            "добавь услуг",
            "добавь новую услугу",
            "add service",
            "add a service",
            "neue leistung",
            "neue dienstleistung",
            "добавь услугу",
        )
    )
    if add_service:
        title = _extract_quoted_or_tail(text)
        if not title:
            m = re.search(
                r"(?:add|добавь|додай|neue dienstleistung|neue leistung|add service)[:\s]+(.+)$",
                text,
                flags=re.I,
            )
            title = (m.group(1).strip() if m else "").strip(" .")
        if not title:
            title = "Neue Leistung"
        # strip leading "услугу " leftovers
        title = re.sub(
            r"^(услугу|услуга|service|leistung)\s+", "", title, flags=re.I
        ).strip(" :.-")
        content_patch["_append_service"] = {
            "id": _uid("svc"),
            "title": title[:80] or "Neue Leistung",
            "description": "",
            "price": "",
        }
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": f"Service added: {title[:80]}",
        }

    # Hero shorter / modern
    if any(
        k in low
        for k in (
            "hero короче",
            "hero shorter",
            "kürzerer hero",
            "hero kürzer",
            "headline shorter",
            "сделай hero короче",
            "короче hero",
        )
    ):
        content_patch["hero"] = {
            "subheadline": "Klar. Modern. Für Ihr Unternehmen.",
        }
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Hero subheadline shortened",
        }

    if any(
        k in low
        for k in (
            "hero современ",
            "hero modern",
            "moderneren hero",
            "современн",
            "modernere headline",
        )
    ):
        content_patch["hero"] = {
            "headline": "Willkommen — Ihr Auftritt, neu gedacht.",
            "subheadline": "Klarer Fokus. Starke Bilder. Direkter Kontakt.",
            "cta_label": "Jetzt Termin anfragen",
        }
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Hero copy modernized",
        }

    # Design lighter / darker
    if any(k in low for k in ("heller", "lighter", "светлее", "helleres design")):
        design_patch["colors"] = {
            "background": "#f8fafc",
            "secondary": "#ffffff",
            "text": "#0f172a",
            "primary": "#0f766e",
            "button": "#0f766e",
            "link": "#0d9488",
        }
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Design set to lighter theme",
        }

    if any(k in low for k in ("dunkler", "darker", "темнее", "dunkles design")):
        design_patch["colors"] = {
            "background": "#0b1220",
            "secondary": "#111827",
            "text": "#e5e7eb",
            "primary": "#34d399",
            "button": "#10b981",
            "link": "#6ee7b7",
        }
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Design set to darker theme",
        }

    # Button color green
    if any(k in low for k in ("кнопк", "button", "cta")) and any(
        k in low for k in ("grün", "green", "зелен")
    ):
        design_patch["colors"] = {"button": "#16a34a", "primary": "#16a34a"}
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Button color set to green",
        }

    # Contacts phone
    phone_m = re.search(
        r"(?:phone|telefon|телефон|whatsapp)[:\s]+([+\d][\d\s\-()]{6,})",
        text,
        flags=re.I,
    )
    if phone_m:
        phone = phone_m.group(1).strip()
        content_patch["contacts"] = {"phone": phone}
        if "whatsapp" in low:
            content_patch["contacts"]["whatsapp"] = phone
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": f"Contact phone updated: {phone}",
        }

    # Explicit hero headline set
    hm = re.search(
        r"(?:headline|заголовок|titel)[:\s]+(.+)$",
        text,
        flags=re.I,
    )
    if hm:
        content_patch["hero"] = {"headline": hm.group(1).strip()[:120]}
        return {
            "content_patch": content_patch,
            "design_patch": design_patch,
            "summary": "Hero headline updated",
        }

    raise ValueError("unsupported_ai_edit_intent")


def apply_content_intent(
    current_content: dict[str, Any], content_patch: dict[str, Any]
) -> dict[str, Any]:
    """Merge AI content patch including _append_service."""
    out = dict(content_patch)
    append = out.pop("_append_service", None)
    if append and isinstance(append, dict):
        services = list(current_content.get("services") or [])
        services.append(append)
        out["services"] = services
    return out
