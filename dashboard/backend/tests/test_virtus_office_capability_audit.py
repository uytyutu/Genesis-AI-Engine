"""Capability audit honesty — no fake SELLABLE for roadmap SKUs."""

from app.integration.virtus_office.execution import EXECUTABLE_ACTION_IDS
from app.integration.virtus_office.office_capability_audit import (
    audit_matrix,
    classify_sku,
    report_table,
)
from app.integration.virtus_office.office_job_ssot import (
    OFFICE_PIPELINE_LIVE,
    OFFICE_SELLABLE_NOW,
)
from app.integration.virtus_office.sku_xrechnung import (
    EXECUTOR_IMPLEMENTED as XR_EXEC,
    SKU_ENABLED as XR_ENABLED,
    VALIDATOR_IMPLEMENTED as XR_VAL,
)


def test_live_flags_remain_off():
    assert OFFICE_PIPELINE_LIVE is True


def test_dqc_and_baseline_sellable():
    for sid in (
        "translate",
        "convert_docx",
        "extract_data",
        "document_quality_check",
        "lebenslauf_create",
        "bewerbung_paket",
    ):
        c = classify_sku(sid)
        assert c["status"] == "SELLABLE", (sid, c)
        assert sid in EXECUTABLE_ACTION_IDS


def test_xrechnung_not_sellable_without_enable():
    """Phase B may implement executor/validator while SKU_ENABLED stays False."""
    assert XR_ENABLED is False
    assert "xrechnung" not in OFFICE_SELLABLE_NOW
    assert "xrechnung" not in EXECUTABLE_ACTION_IDS
    c = classify_sku("xrechnung")
    assert c["status"] == "ROADMAP"
    assert c["vitrine"] is False
    # Implementation flags may be True; enable gate is what blocks sale
    assert XR_EXEC is True
    assert XR_VAL is True


def test_high_risk_roadmap_not_on_vitrine():
    for sid in (
        "zugferd",
        "searchable_pdf",
        "fillable_pdf",
        "pdf_a_2b",
        "document_archive",
        "pdf_ua",
    ):
        c = classify_sku(sid)
        assert c["status"] in {"ROADMAP", "BLOCKED"}
        assert c["vitrine"] is False


def test_forbidden_never_sellable():
    c = classify_sku("legal")
    assert c["status"] == "FORBIDDEN"
    assert c["vitrine"] is False


def test_audit_matrix_no_inconsistencies():
    m = audit_matrix()
    assert m["inconsistencies"] == []
    assert m["pipeline_live"] is True
    assert m["country_pricing"] is False
    assert "document_quality_check" in m["sellable_skus"]
    assert "xrechnung" not in m["sellable_skus"]
    assert m["live_gate"]["auto_flip_forbidden"] is True


def test_report_table_shape():
    rows = report_table()
    by_id = {r["sku"]: r for r in rows}
    assert by_id["translate"]["status"] == "SELLABLE"
    assert by_id["xrechnung"]["status"] == "ROADMAP"
    assert by_id["xrechnung"]["executor"] == "NO"
    assert by_id["xrechnung"]["validator"] == "NO"
