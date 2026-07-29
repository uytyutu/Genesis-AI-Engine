"""Regression: generated outreach must not mix German into other locales.

Run:
  py -3.12 -m pytest tests/test_generation_language_regression.py -q
"""

from __future__ import annotations

import re

import pytest

from app.integration.outreach_language_service import OutreachLanguageService

# German fingerprints that must not appear outside DE (and AT/CH market packs).
_DE_LEAK_MARKERS = (
    "Kein ",
    "Keine ",
    "Sehr geehrte",
    "Mit freundlichen Grüßen",
    "Guten Tag",
    "Langsame Antwort",
    "Website nicht",
    "öffnungszeiten",
    "seitentitel",
)

# Markets → expected generation locale + whether German body is expected.
_CASES: list[tuple[str, str, bool]] = [
    ("US", "en-us", False),
    ("FR", "fr", False),
    ("PL", "pl", False),
    ("DE", "de", True),
    ("UA", "uk", False),
    ("ES", "es", False),
    ("IT", "it", False),
    ("NL", "nl", False),
]

# Poison analysis: classic DE diagnosis strings (must not leak into non-DE drafts).
_POISON_ISSUES = [
    "Kein HTTPS — Risiko für Besucher und Vertrauen.",
    "Langsame Antwort (~800 ms).",
    "Fehlender oder leerer Seitentitel.",
]


def _draft_for(market: str) -> tuple[str, str, str]:
    svc = OutreachLanguageService()
    row = {"market": market, "meta": {"market": market}}
    subject, body, lang = svc.draft_outreach(
        company="Acme Test GmbH",
        analysis={"issues": list(_POISON_ISSUES), "url": "https://example.com"},
        package={"name": "Landing Basic", "price_label": "99 EUR", "id": "basic"},
        price=99.0,
        fit_reason="language regression",
        row=row,
        allow_llm=False,
    )
    return subject, body, lang


def _has_de_leak(text: str) -> list[str]:
    low = text
    hits: list[str] = []
    for m in _DE_LEAK_MARKERS:
        if m.lower() in low.lower() or m in low:
            hits.append(m.strip())
    return hits


@pytest.mark.parametrize("market,expect_lang,expect_german", _CASES)
def test_generation_language_no_cross_mix(
    market: str, expect_lang: str, expect_german: bool
) -> None:
    subject, body, lang = _draft_for(market)
    sample = f"{subject}\n{body}"[:500]
    hits = _has_de_leak(sample)

    if expect_lang.startswith("en"):
        assert lang.startswith("en"), f"{market}: lang={lang!r} want en*"
    else:
        assert lang == expect_lang or lang.startswith(expect_lang.split("-")[0]), (
            f"{market}: lang={lang!r} want {expect_lang!r}"
        )

    if expect_german:
        # DE pack may use markers; at least one German fingerprint or "Guten"/"Mit freundlichen".
        assert hits or re.search(r"\b(und|für|Ihr|Sie)\b", sample), (
            f"{market}: expected German copy, sample={sample!r}"
        )
    else:
        assert not hits, f"{market}: German leak {hits} in: {sample!r}"


def test_generation_language_matrix_report(capsys: pytest.CaptureFixture[str]) -> None:
    """Print PASS/FAIL table for CEO glance (always runs with the parametrized suite)."""
    rows: list[str] = []
    all_ok = True
    for market, expect_lang, expect_german in _CASES:
        subject, body, lang = _draft_for(market)
        sample = f"{subject}\n{body}"[:500]
        hits = _has_de_leak(sample)
        lang_ok = (
            lang.startswith("en")
            if expect_lang.startswith("en")
            else (lang == expect_lang or lang.startswith(expect_lang.split("-")[0]))
        )
        if expect_german:
            content_ok = bool(hits) or bool(re.search(r"\b(und|für|Ihr|Sie)\b", sample))
        else:
            content_ok = not hits
        ok = lang_ok and content_ok
        all_ok = all_ok and ok
        status = "PASS" if ok else "FAIL"
        note = ""
        if not lang_ok:
            note = f"lang={lang}"
        elif hits and not expect_german:
            note = f"leak={hits[:2]}"
        rows.append(f"| {market:4} | {expect_lang:6} | {lang:6} | {status:4} | {note}")

    print("\n| Mkt  | expect | got    | result | note")
    print("|------|--------|--------|--------|------")
    for r in rows:
        print(r)
    assert all_ok
