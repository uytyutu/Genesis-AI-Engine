"""Customer-facing preview only — never a free final artifact (CRA Fix Pack #1)."""

from __future__ import annotations

from typing import Any

from app.integration.virtus_office.bewerbung_generate import (
    build_anschreiben_paragraphs,
    build_lebenslauf_sections,
)
from app.integration.virtus_office.bewerbung_profile import normalize_profile
from app.integration.virtus_office.bewerbung_ssot import BEWERBUNG_ACTION_IDS


def build_customer_preview(
    *,
    action_id: str,
    profile: dict[str, Any] | None = None,
    document_hint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Short structural preview. No material_id, no downloadable bytes."""
    aid = (action_id or "").strip().lower()
    hint = dict(document_hint or {})

    if aid in BEWERBUNG_ACTION_IDS:
        return _bewerbung_preview(aid, profile or {})

    # Generic Office jobs (translate / convert / extract)
    pages = hint.get("pages") or hint.get("page_count")
    return {
        "kind": "preview",
        "product": str(hint.get("task_label_de") or aid or "Virtus Office"),
        "style": "Professional",
        "language": str(hint.get("language_label_de") or hint.get("language") or "—"),
        "estimated_pages": int(pages) if pages else None,
        "structure": list(hint.get("structure") or []),
        "excerpt": str(hint.get("excerpt") or "")[:480],
        "full_document_after_payment": True,
        "download_allowed": False,
    }


def _bewerbung_preview(action_id: str, profile: dict[str, Any]) -> dict[str, Any]:
    p = normalize_profile(profile)
    labels = {
        "lebenslauf_create": "Lebenslauf",
        "lebenslauf_improve": "Lebenslauf (verbessert)",
        "bewerbungsschreiben": "Anschreiben",
        "bewerbung_paket": "Bewerbung-Paket",
    }
    product = labels.get(action_id, "Bewerbung")

    if action_id in {"lebenslauf_create", "lebenslauf_improve", "bewerbung_paket"}:
        sections = build_lebenslauf_sections(p)
        structure = [title for title, _ in sections if title != "Hinweis"]
        excerpt_parts: list[str] = []
        for title, lines in sections[:2]:
            excerpt_parts.append(title)
            excerpt_parts.extend(str(x) for x in (lines or [])[:3])
        excerpt = "\n".join(excerpt_parts).strip()
        exp_n = len(p.get("experience") or [])
        pages = 2 if exp_n >= 3 or action_id == "bewerbung_paket" else 1
        if action_id == "bewerbung_paket":
            structure = structure + ["Anschreiben"]
            pages = max(pages, 2)
    else:
        paras = build_anschreiben_paragraphs(p)
        structure = [
            "Absender",
            "Empfänger",
            "Betreff",
            "Einleitung",
            "Qualifikation",
            "Schluss",
        ]
        excerpt = "\n\n".join(paras[:2]).strip()
        pages = 1

    if len(excerpt) > 480:
        excerpt = excerpt[:477].rstrip() + "…"

    return {
        "kind": "preview",
        "product": product,
        "style": "German Professional",
        "language": "Deutsch",
        "estimated_pages": pages,
        "structure": structure,
        "excerpt": excerpt,
        "full_document_after_payment": True,
        "download_allowed": False,
    }
