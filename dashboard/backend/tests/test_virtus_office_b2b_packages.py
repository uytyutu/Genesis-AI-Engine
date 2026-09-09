"""Virtus Office B2B packages + Sales Kit — LIVE gate checks."""

from __future__ import annotations

import io
import zipfile

import pytest

from app.integration.virtus_office.b2b_packages import (
    B2B_PACKAGE_SKUS,
    B2B_PRICE_EUR,
    SALES_KIT_BASIC,
    SALES_KIT_BUSINESS,
    SALES_KIT_LIVE,
    SALES_KIT_PROFESSIONAL,
    assert_not_in_sellable,
    detect_b2b_intent,
    live_flag_for_sku,
    readiness_record,
)
from app.integration.virtus_office.office_job_ssot import (
    OFFICE_PRICE_MATRIX_EUR,
    OFFICE_SELLABLE_NOW,
    OFFICE_SKU_ROADMAP,
)
from app.integration.virtus_office.sku_sales_kit import (
    EXECUTOR_IMPLEMENTED,
    SKU_ENABLED,
    VALIDATOR_IMPLEMENTED,
    can_purchase_sales_kit,
    generate_sales_kit,
    missing_required_fields,
    validate_sales_kit_artifact,
)


SAMPLE_COMPANY = {
    "company_name": "Muster Handwerk GmbH",
    "tagline": "Zuverlässige Elektroarbeiten",
    "description": "Wir installieren und warten Elektroanlagen für Privat und Gewerbe.",
    "services": [
        {"name": "Elektroinstallation", "description": "Neuinstallation", "price": "ab 89 €/h"},
        {"name": "Störungsdienst", "price": "119 €/h"},
    ],
    "contacts": {
        "email": "info@muster-handwerk.example",
        "phone": "+49 30 123456",
        "city": "Berlin",
    },
}


def test_sales_kit_live_enabled():
    assert SALES_KIT_LIVE is True
    assert SKU_ENABLED is True
    assert can_purchase_sales_kit() is True


def test_b2b_skus_not_in_sellable_now():
    leaked = assert_not_in_sellable(OFFICE_SELLABLE_NOW)
    assert leaked == []
    for sku in B2B_PACKAGE_SKUS:
        if sku in {SALES_KIT_BASIC, SALES_KIT_BUSINESS, SALES_KIT_PROFESSIONAL}:
            assert sku in OFFICE_SELLABLE_NOW
            assert live_flag_for_sku(sku) is True
        else:
            assert sku not in OFFICE_SELLABLE_NOW
            assert live_flag_for_sku(sku) is False


def test_b2b_skus_on_roadmap():
    for sku in (
        SALES_KIT_BASIC,
        SALES_KIT_BUSINESS,
        SALES_KIT_PROFESSIONAL,
        "company_profile",
        "document_cleanup_pack",
        "business_translation_pack",
        "excel_business_pack",
        "process_sop_pack",
    ):
        assert sku in OFFICE_SKU_ROADMAP


def test_pricing_config():
    assert B2B_PRICE_EUR[SALES_KIT_BASIC] == 99.0
    assert B2B_PRICE_EUR[SALES_KIT_BUSINESS] == 199.0
    assert B2B_PRICE_EUR[SALES_KIT_PROFESSIONAL] == 299.0
    assert OFFICE_PRICE_MATRIX_EUR["sales_kit_business"] == 199.0


def test_sales_kit_executor_and_validator_flags():
    assert EXECUTOR_IMPLEMENTED is True
    assert VALIDATOR_IMPLEMENTED is True


def test_missing_input_rejects_without_invention():
    miss = missing_required_fields({}, tier=SALES_KIT_BASIC)
    assert "company_name" in miss
    bad = generate_sales_kit(company={}, tier=SALES_KIT_BASIC)
    assert bad["ok"] is False
    assert bad["error"] == "missing_input"


def test_sales_kit_basic_zip_composition():
    out = generate_sales_kit(company=SAMPLE_COMPANY, tier=SALES_KIT_BASIC)
    assert out["ok"] is True
    assert out["live_allowed"] is True
    zf = zipfile.ZipFile(io.BytesIO(out["bytes"]))
    names = set(zf.namelist())
    assert "VIRTUS_SALES_KIT/Company_Profile.pdf" in names
    assert "VIRTUS_SALES_KIT/Company_Profile.docx" in names
    assert "VIRTUS_SALES_KIT/Angebot.pdf" not in names
    va = validate_sales_kit_artifact(
        data=out["bytes"], tier=SALES_KIT_BASIC, company=SAMPLE_COMPANY
    )
    assert va["pass"] is True
    assert va["delivery_allowed"] is True


def test_sales_kit_business_zip_composition():
    out = generate_sales_kit(company=SAMPLE_COMPANY, tier=SALES_KIT_BUSINESS)
    assert out["ok"] is True
    zf = zipfile.ZipFile(io.BytesIO(out["bytes"]))
    names = set(zf.namelist())
    for f in (
        "Company_Profile.pdf",
        "Company_Profile.docx",
        "Angebot.pdf",
        "Preislist.pdf",
        "Customer_Email_Template.docx",
    ):
        assert f"VIRTUS_SALES_KIT/{f}" in names
    va = validate_sales_kit_artifact(
        data=out["bytes"], tier=SALES_KIT_BUSINESS, company=SAMPLE_COMPANY
    )
    assert va["pass"] is True
    assert va["delivery_allowed"] is True


def test_validator_fails_on_empty_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("VIRTUS_SALES_KIT/Company_Profile.pdf", b"")
    va = validate_sales_kit_artifact(
        data=buf.getvalue(), tier=SALES_KIT_BASIC, company=SAMPLE_COMPANY
    )
    assert va["pass"] is False


def test_intent_sales_kit_not_sellable():
    hit = detect_b2b_intent("I need documents to present my company to customers.")
    assert hit is not None
    assert hit["product_id"] == "sales_kit"
    assert hit["live"] is True
    assert hit["sellable"] is True


def test_readiness_record_live_off_e2e_honest():
    rec = readiness_record()
    assert rec["SALES_KIT"]["live"] is True
    assert rec["SALES_KIT"]["executor"] == "PASS"
    assert rec["SALES_KIT"]["validator"] == "PASS"
    assert rec["SALES_KIT"]["e2e"] in {"PENDING", "PASS", "FAIL"}
    assert rec["COMPANY_PROFILE"]["live"] is False


def test_existing_sellable_unchanged():
    for sid in ("translate", "lebenslauf_create", "bewerbung_paket", "fillable_pdf"):
        assert sid in OFFICE_SELLABLE_NOW


def test_capability_audit_no_b2b_leak():
    from app.integration.virtus_office.office_capability_audit import audit_matrix

    caps = audit_matrix()
    assert caps["b2b_packages"]["sellable_leak"] == []
    assert caps["b2b_packages"]["sales_kit_live"] is True
    for sid in B2B_PACKAGE_SKUS:
        if sid in {SALES_KIT_BASIC, SALES_KIT_BUSINESS, SALES_KIT_PROFESSIONAL}:
            assert sid in caps["sellable_skus"]
            assert sid in caps["vitrine_skus"]
        else:
            assert sid not in caps["sellable_skus"]
            assert sid not in caps["vitrine_skus"]
