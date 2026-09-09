"""Sales Kit LIVE readiness audit — no flip."""

from __future__ import annotations

from pathlib import Path

from app.integration.virtus_office.b2b_packages import SALES_KIT_LIVE
from app.integration.virtus_office.office_job_ssot import OFFICE_SELLABLE_NOW
from app.integration.virtus_office.sales_kit_live_readiness import audit_live_readiness
from app.integration.virtus_office.sku_sales_kit import SKU_ENABLED


def test_sales_kit_live_readiness_does_not_flip(tmp_path: Path):
    report = audit_live_readiness(memory_hint=tmp_path)
    assert report["CURRENT_STATE"]["SALES_KIT_LIVE"] is True
    assert report["CURRENT_STATE"]["SKU_ENABLED"] is True
    assert report["CURRENT_STATE"]["OFFICE_SELLABLE_NOW"] == "LIVE_WITH_SALES_KIT"
    assert SALES_KIT_LIVE is True
    assert SKU_ENABLED is True
    assert "sales_kit_business" in OFFICE_SELLABLE_NOW
    assert report["PRICE_INTEGRITY"] == "PASS"
    assert report["PUBLIC_LIVE_GATE"] == "PASS"
    assert report["PRODUCTION_SAFETY"] == "PASS"
    assert report["ROLLBACK_READY"] == "PASS"
    assert report["EXECUTOR"] == "PASS"
    assert report["VALIDATOR"] == "PASS"
    assert report["SALES_KIT_LIVE_READINESS"] == "PASS"
    assert "manual_live_flip" in report
    assert "DO NOT EXECUTE AUTOMATICALLY" in report["manual_live_flip"]["warning"]
