"""Pipeline email/host dedupe for Acquisition Studio."""

from __future__ import annotations

from pathlib import Path

from app.integration.acquisition_studio_service import AcquisitionStudioService
from app.integration.opportunity_service import OpportunityService
from app.integration.sales_order_service import SalesOrderService
from app.factory.factory_service import FactoryService
from app.integration.factory_intent_service import FactoryIntentService


def test_pipeline_busy_keys_and_duplicate(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    sales = SalesOrderService(tmp_path, FactoryIntentService(tmp_path, FactoryService(tmp_path)))
    studio = AcquisitionStudioService(opp, sales)
    rows = [
        {
            "id": "a",
            "contact": "Owner <same@shop.de>",
            "website_url": "https://www.shop.de",
            "status": "contacted",
            "outreach_status": "sent",
        },
        {
            "id": "b",
            "contact": "other@x.de",
            "website_url": "https://shop.de/path",
            "status": "proposed",
            "outreach_status": "",
        },
        {
            "id": "c",
            "contact": "same@shop.de",
            "website_url": "https://other.de",
            "status": "proposed",
            "outreach_status": "",
        },
    ]
    emails, hosts = studio._pipeline_busy_keys(rows)
    assert "same@shop.de" in emails
    assert "shop.de" in hosts
    assert studio._is_pipeline_duplicate(rows[1], busy_emails=emails, busy_hosts=hosts)
    assert studio._is_pipeline_duplicate(rows[2], busy_emails=emails, busy_hosts=hosts)
    fresh = {
        "id": "d",
        "contact": "new@fresh.de",
        "website_url": "https://fresh.de",
        "status": "proposed",
    }
    assert not studio._is_pipeline_duplicate(fresh, busy_emails=emails, busy_hosts=hosts)
