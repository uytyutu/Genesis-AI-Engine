"""Dokument anpassen — settings parse + catalog."""

from __future__ import annotations

from app.integration.virtus_office.document_settings import (
    apply_text_replacements,
    build_document_settings,
    parse_special_wishes,
    settings_catalog,
)


def test_businessplan_translate_catalog_includes_identity_fields():
    cat = settings_catalog(action_id="translate", document_type="businessplan")
    ids = {f["id"] for f in cat}
    assert "target_language" in ids
    assert "change_date" in ids
    assert "change_company" in ids
    assert "remove_section" in ids


def test_parse_special_wishes_date_and_keep():
    explanation = {
        "key_facts": [
            {"id": "document_date", "value": "31.07.2026"},
            {"id": "brand", "value": "Virtus Core"},
        ]
    }
    ops = parse_special_wishes(
        "Ändere das Datum auf 04.09.2026, Firmenname ohne Änderungen, "
        "SWOT behalten, Finanzteil vollständig übersetzen.",
        explanation=explanation,
    )
    ids = {o["id"] for o in ops}
    assert "replace_text" in ids
    assert "keep_value" in ids
    assert "keep_section" in ids
    assert "translate_section_fully" in ids
    date_op = next(o for o in ops if o["id"] == "replace_text")
    assert date_op["from"] == "31.07.2026"
    assert date_op["to"] == "04.09.2026"
    assert date_op["executable_now"] is True


def test_parse_preserve_names_and_full_translate_wish():
    explanation = {
        "key_facts": [
            {"id": "document_date", "value": "31.07.2026"},
            {"id": "brand", "value": "Virtus Core"},
        ]
    }
    wish = (
        "Übersetze den vollständigen Businessplan von Deutsch nach Englisch. "
        "Die Firmennamen und Personennamen nicht verändern."
    )
    ops = parse_special_wishes(wish, explanation=explanation)
    ids = {o["id"] for o in ops}
    assert "free_instruction" not in ids
    assert "set_target_language" in ids
    assert "set_source_language" in ids
    assert "preserve_names" in ids
    assert "scope_full" in ids
    assert next(o for o in ops if o["id"] == "set_target_language")["to"] == "en"

    explanation = {"key_facts": [{"id": "document_date", "value": "31.07.2026"}]}
    settings = build_document_settings(
        action_id="translate",
        document_type="businessplan",
        explanation=explanation,
        values={
            "target_language": "en",
            "output_format": "docx",
            "change_date": "04.09.2026",
        },
        special_wishes=None,
        sections=[{"id": "swot"}, {"id": "finance"}],
    )
    assert settings["filled"] is True
    assert any(o.get("id") == "set_target_language" for o in settings["ops"])
    assert settings["preview"]
    text = "Dokumentstand: 31.07.2026 — Virtus Core"
    out = apply_text_replacements(text, settings)
    assert "04.09.2026" in out
    assert "31.07.2026" not in out
