"""CRA #3 — Virtus Office i18n gate.

Ensures Office locale packs stay complete and honesty copy does not regress
to outdated CC-1/CC-2 / «no Stripe» customer messaging.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]  # dashboard/
I18N_DIR = REPO / "frontend" / "app" / "office" / "i18n"
LOCALES = ("de", "en", "uk", "ru", "pl", "tr", "fr", "es", "it")
FORBIDDEN_IN_HONESTY = re.compile(
    r"CC[- ]?[12]\b|без Stripe|no Stripe|kein Stripe|pas de Stripe|sin Stripe|"
    r"Stripe yok|nessun Stripe|w CC-2|в CC-2|у CC-2|CC-1|CC-2",
    re.I,
)
# Hard-coded DE UI leftovers that must not remain in Bewerbung storefront
BEWERBUNG_FILE = (
    REPO
    / "frontend"
    / "app"
    / "components"
    / "storefront"
    / "VirtusBewerbungStorefront.tsx"
)
FORBIDDEN_BEWERBUNG_LITERALS = (
    "Owner-Preview",
    "Zur Zahlung",
    "Profil prüfen",
    "Lebenslauf erstellen",
    "Vollständiger Name",
    "Checkout derzeit nicht verfügbar (Stripe/Sandbox)",
    "Delivery-Link ungültig",
)


def _flatten(obj, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.update(_flatten(v, key))
    else:
        out[prefix] = "" if obj is None else str(obj)
    return out


def _load(code: str) -> dict:
    path = I18N_DIR / f"{code}.json"
    assert path.is_file(), f"missing locale file {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_office_i18n_dir_exists():
    assert I18N_DIR.is_dir(), f"missing {I18N_DIR}"


def test_office_locale_key_parity():
    de_keys = set(_flatten(_load("de")))
    assert de_keys, "de.json empty"
    for code in LOCALES:
        keys = set(_flatten(_load(code)))
        missing = sorted(de_keys - keys)
        extra_note = sorted(keys - de_keys)
        assert not missing, f"{code} missing keys vs de: {missing[:20]}"
        # Extra keys allowed but discouraged — soft check printed via assert empty preferred
        assert not extra_note or code == "de", (
            f"{code} has unexpected extra keys vs de: {extra_note[:20]}"
        )


def test_office_honesty_no_outdated_cc_or_stripe_denial():
    paths = ("honestyCc1", "proposal.payHint", "proposal.payLocked")
    for code in LOCALES:
        flat = _flatten(_load(code))
        for p in paths:
            val = flat.get(p, "")
            assert val, f"{code} missing {p}"
            assert not FORBIDDEN_IN_HONESTY.search(val), (
                f"{code}.{p} contains outdated honesty wording: {val!r}"
            )


# CRA #4+#5 — vitrine must not oversell engine capabilities
FORBIDDEN_OVERSELL = re.compile(
    r"100\s*%|гарантированн|garantiert(?:er)?\s+Job|Jobgarantie(?!\s*—)|"
    r"мгновенн|instant(?:ly)?\s+(?:result|download|excel)|"
    r"perfekt(?:e|en)?\s+(?:Tabelle|Excel)|ideal(?:er)?\s+Excel|"
    r"any\s+table\s*→\s*perfect|любая\s+таблица|"
    r"Vollständige Übersetzung(?!\s+in)",
    re.I,
)


def test_office_copy_no_oversell_claims():
    """Customer-facing locale strings must not promise impossible certainty."""
    for code in LOCALES:
        flat = _flatten(_load(code))
        for path, val in flat.items():
            # Bewerbung may honestly say «Keine Job-Garantie» / «no hire guarantee»
            if "keine job-garantie" in val.lower() or "no hire guarantee" in val.lower():
                continue
            if "no job guarantee" in val.lower() or "ohne job-garantie" in val.lower():
                continue
            if "немає гарантії" in val.lower() or "нет гарантии" in val.lower():
                continue
            if "no promise of perfect" in val.lower() or "keine garantie für perfekte" in val.lower():
                continue
            assert not FORBIDDEN_OVERSELL.search(val), (
                f"{code}.{path} oversells: {val!r}"
            )


def test_excel_and_ocr_honesty_keys_present():
    for code in LOCALES:
        flat = _flatten(_load(code))
        assert flat.get("ocrHonesty"), f"{code} missing ocrHonesty"
        assert flat.get("excelHonesty"), f"{code} missing excelHonesty"
        assert "ocr" in flat["excelHonesty"].lower() or "CSV" in flat["excelHonesty"]
        excel_lead = flat.get("service.excel.lead", "")
        assert "CSV" in excel_lead or "csv" in excel_lead.lower() or "XLSX" in excel_lead


def test_office_lang_separation_keys_present():
    required = (
        "uiLangLabel",
        "docLangNote",
        "documentLanguage",
        "translationTarget",
        "cvTargetMarket",
        "langSeparationHint",
    )
    for code in LOCALES:
        flat = _flatten(_load(code))
        for p in required:
            assert flat.get(p), f"{code} missing language-separation key {p}"


def test_bewerbung_storefront_uses_office_i18n():
    text = BEWERBUNG_FILE.read_text(encoding="utf-8")
    assert "useOfficeT" in text
    assert 'from "../../lib/useOfficeT"' in text or "from '../../lib/useOfficeT'" in text
    for lit in FORBIDDEN_BEWERBUNG_LITERALS:
        assert lit not in text, f"hard-coded leftover in Bewerbung storefront: {lit!r}"


def test_office_components_no_owner_preview_literal():
    office_dir = REPO / "frontend" / "app" / "components" / "office"
    hits = []
    for path in office_dir.rglob("*.tsx"):
        raw = path.read_text(encoding="utf-8")
        if "Owner-Preview" in raw or "ohne Zahlung" in raw:
            hits.append(str(path))
    assert not hits, f"Owner-Preview leftovers: {hits}"
