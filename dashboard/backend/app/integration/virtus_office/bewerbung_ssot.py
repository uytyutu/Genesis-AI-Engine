"""Virtus Office Stage 5 — Bewerbung Office SSOT (honesty + field contracts)."""

from __future__ import annotations

from typing import Any

BEWERBUNG_ACTION_IDS: frozenset[str] = frozenset(
    {
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }
)

# Client-facing honesty — never claim job placement or invent skills.
BEWERBUNG_DISCLAIMER_DE = (
    "Virtus Office erstellt Dokumente nur aus Ihren Angaben. "
    "Keine erfundenen Qualifikationen, kein Garantieversprechen für eine Einstellung."
)

BEWERBUNG_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "garantierte einstellung",
    "garantiert eingestellt",
    "100% zusage",
    "jobgarantie",
    "einstellungsgarantie",
    "wir garantieren ihnen den job",
)

# Field ids returned to the structured form when incomplete.
PROFILE_FIELD_LABELS_DE: dict[str, str] = {
    "personal.full_name": "Vollständiger Name",
    "personal.email": "E-Mail",
    "personal.phone": "Telefon",
    "personal.city": "Wohnort / Stadt",
    "personal.contact": "E-Mail oder Telefon",
    "experience": "Berufserfahrung (mindestens ein Eintrag)",
    "experience.employer": "Arbeitgeber",
    "experience.title": "Position / Tätigkeit",
    "experience.start": "Beginn der Tätigkeit",
    "education": "Ausbildung / Studium (mindestens ein Eintrag)",
    "education.school": "Schule / Hochschule",
    "education.degree": "Abschluss / Richtung",
    "education.start": "Beginn Ausbildung",
    "vacancy.title": "Stellentitel",
    "vacancy.company": "Unternehmen der Stelle",
    "vacancy.text_or_title": "Stellenanzeige oder Stellentitel",
    "source_cv": "Alter Lebenslauf (Datei oder Text)",
    "experience_or_education": "Berufserfahrung oder Ausbildung",
}


def empty_bewerbung_profile() -> dict[str, Any]:
    return {
        "personal": {
            "full_name": None,
            "email": None,
            "phone": None,
            "address": None,
            "city": None,
            "postal_code": None,
            "birth_date": None,
            "nationality": None,
        },
        "photo_material_id": None,
        "experience": [],
        "education": [],
        "certificates": [],
        "languages": [],
        "skills": [],
        "drivers_license": [],
        "vacancy": {
            "title": None,
            "company": None,
            "text": None,
            "source": None,
        },
        "motivation_notes": None,
        "source_cv_text": None,
        "anlagen_notes": None,
        "honesty": {
            "no_invention": True,
            "no_job_guarantee": True,
            "disclaimer_de": BEWERBUNG_DISCLAIMER_DE,
        },
    }


def bewerbung_action_meta() -> list[dict[str, Any]]:
    return [
        {
            "id": "lebenslauf_create",
            "label_de": "Lebenslauf erstellen",
            "price_key": "cv_bewerbung",
            "default_output": "pdf",
            "needs_profile": True,
            "needs_vacancy": False,
            "needs_source_cv": False,
        },
        {
            "id": "lebenslauf_improve",
            "label_de": "Lebenslauf verbessern",
            "price_key": "cv_bewerbung",
            "default_output": "pdf",
            "needs_profile": True,
            "needs_vacancy": False,
            "needs_source_cv": True,
        },
        {
            "id": "bewerbungsschreiben",
            "label_de": "Bewerbungsschreiben",
            "price_key": "cv_bewerbung",
            "default_output": "pdf",
            "needs_profile": True,
            "needs_vacancy": True,
            "needs_source_cv": False,
        },
        {
            "id": "bewerbung_paket",
            "label_de": "Bewerbung-Paket",
            "price_key": "large_pack",
            "default_output": "zip",
            "needs_profile": True,
            "needs_vacancy": True,
            "needs_source_cv": False,
        },
    ]
