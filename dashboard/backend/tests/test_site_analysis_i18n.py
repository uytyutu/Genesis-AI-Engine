"""Site analysis issue strings must follow market/locale, not hardcoded German."""

from __future__ import annotations

from app.integration.site_analysis_i18n import localize_analysis_issues


def test_legacy_german_issues_localize_to_english_for_sg():
    de = [
        "Kein sichtbares Kontaktformular / E-Mail-Feld",
        "Kein direkter Anruf / WhatsApp-Link",
        "Kein klares CTA auf der Startseite",
        "Keine Google Maps Einbindung erkannt",
    ]
    out = localize_analysis_issues(de, market="SG")
    joined = " ".join(out).lower()
    assert "kein" not in joined
    assert "no visible contact form" in joined
    assert "whatsapp" in joined
    assert "call-to-action" in joined or "cta" in joined


def test_issue_codes_render_in_english():
    out = localize_analysis_issues(
        None,
        language="en",
        codes=["no_contact_form", "http_error:403", "slow_response:3200"],
    )
    assert out[0].startswith("No visible")
    assert "403" in out[1]
    assert "3200" in out[2]
    assert all("Kein" not in x for x in out)


def test_de_market_keeps_german():
    out = localize_analysis_issues(
        ["Kein HTTPS — unsicher für Besucher"],
        market="DE",
    )
    assert out[0].startswith("Kein HTTPS")
