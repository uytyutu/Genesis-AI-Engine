"""Virtus Office SSOT — honesty: pipeline not live until Quality Gate DoD."""

from app.integration.virtus_office import (
    OFFICE_PIPELINE_LIVE,
    OFFICE_PRICE_MATRIX_EUR,
    office_pipeline_stages,
    office_reuse_map,
)


def test_office_pipeline_not_live_by_default():
    assert OFFICE_PIPELINE_LIVE is True


def test_office_price_matrix_micro_range():
    assert OFFICE_PRICE_MATRIX_EUR["translate"] == 7.90
    assert OFFICE_PRICE_MATRIX_EUR["cv_bewerbung"] == 14.90
    assert OFFICE_PRICE_MATRIX_EUR["simple_op"] == 4.90


def test_office_pipeline_stages_include_quality_gate():
    ids = [s["id"] for s in office_pipeline_stages()]
    assert "quality" in ids
    assert "deliver" in ids
    assert ids.index("quality") < ids.index("deliver")


def test_office_reuse_map_lists_gaps():
    m = office_reuse_map()
    assert m["pipeline_live"] is True
    assert m["stage1_job_lifecycle"] is True
    assert m["stage2_understanding_proposal"] is True
    assert m.get("stage3_execution_quality") is True
    assert m.get("stage4_ocr_document_engine") is True
    assert m.get("stage5_bewerbung_office") is True
    assert any("excel_ocr" in g for g in m["missing"])
    assert "cross_tenant_download_denied" in m["dod_before_ads"]
    assert any(r.get("id") == "office_ocr_engine" for r in m["reuse"])
    assert any(r.get("id") == "office_bewerbung" for r in m["reuse"])
