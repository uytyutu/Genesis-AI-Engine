"""Phase B — XRechnung executor + validator (SKU stays ROADMAP / not sellable)."""

from __future__ import annotations

from app.integration.virtus_office.execution import EXECUTABLE_ACTION_IDS
from app.integration.virtus_office.office_capability_audit import classify_sku
from app.integration.virtus_office.office_job_ssot import OFFICE_PIPELINE_LIVE, OFFICE_SELLABLE_NOW
from app.integration.virtus_office.sku_xrechnung import (
    EXECUTOR_IMPLEMENTED,
    SKU_ENABLED,
    VALIDATOR_IMPLEMENTED,
    execute_xrechnung,
    validate_xrechnung,
)

COMPLETE_INVOICE = {
    "invoice_number": "RE-2025-0042",
    "issue_date": "2025-03-15",
    "buyer_reference": "04011000-12345-67",
    "seller": {
        "name": "Muster Liefer GmbH",
        "vat_id": "DE123456789",
        "email": "billing@muster-liefer.de",
        "country": "DE",
        "city": "Berlin",
        "post_code": "10115",
        "street": "Beispielstrasse 1",
    },
    "buyer": {
        "name": "Stadt Musterhausen",
        "country": "DE",
        "city": "Musterhausen",
        "post_code": "12345",
        "street": "Rathausplatz 1",
        "endpoint": "04011000-12345-67",
    },
    "payment": {"iban": "DE89370400440532013000", "means_code": "58"},
    "lines": [
        {
            "id": "1",
            "name": "Beratung März",
            "quantity": 2,
            "unit_price": 100.00,
            "vat_percent": 19,
        }
    ],
}


def test_xrechnung_not_sellable_or_live():
    assert OFFICE_PIPELINE_LIVE is True
    assert SKU_ENABLED is False
    assert EXECUTOR_IMPLEMENTED is True
    assert VALIDATOR_IMPLEMENTED is True
    assert "xrechnung" not in OFFICE_SELLABLE_NOW
    assert "xrechnung" not in EXECUTABLE_ACTION_IDS
    c = classify_sku("xrechnung")
    assert c["status"] == "ROADMAP"
    assert c["vitrine"] is False


def test_xrechnung_complete_pass():
    out = execute_xrechnung(invoice=COMPLETE_INVOICE)
    assert out["ok"] is True, out
    assert out["passed"] is True
    assert out["bytes"].startswith(b"<?xml")
    assert b"Invoice" in out["bytes"]
    assert b"RE-2025-0042" in out["bytes"]
    v = validate_xrechnung(artifact_bytes=out["bytes"], invoice=COMPLETE_INVOICE)
    assert v["passed"] is True, v


def test_xrechnung_missing_fields_fail_no_bytes():
    bad = dict(COMPLETE_INVOICE)
    bad["buyer_reference"] = ""
    out = execute_xrechnung(invoice=bad)
    assert out["ok"] is False
    assert out.get("passed") is False
    assert out.get("bytes") in (None, b"", "")
    assert out.get("error") == "incomplete_invoice"


def test_xrechnung_validator_rejects_broken_xml():
    v = validate_xrechnung(xml_text="<not-closed>")
    assert v["passed"] is False
    assert any(p["code"] == "well_formed_xml" for p in v["problems"])


def test_xrechnung_validator_rejects_missing_buyer_ref():
    import re

    out = execute_xrechnung(invoice=COMPLETE_INVOICE)
    assert out["ok"] is True
    xml = out["bytes"].decode("utf-8")
    xml2 = re.sub(
        r"<([^:>]+:)?BuyerReference>[^<]*</([^:>]+:)?BuyerReference>",
        "",
        xml,
        count=1,
    )
    assert xml2 != xml
    v = validate_xrechnung(xml_text=xml2)
    assert v["passed"] is False
    assert any(p["code"] == "br_de_15_buyer_reference" for p in v["problems"])
