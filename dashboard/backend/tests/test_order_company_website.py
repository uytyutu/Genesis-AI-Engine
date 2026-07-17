"""Path A — optional company website analysis on order create."""

from __future__ import annotations

from pathlib import Path

from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-test-1"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def test_create_order_stores_website_and_analysis(tmp_path: Path, monkeypatch):
    sales = SalesOrderService(tmp_path, _Factory())

    def fake_analyze(self, url: str, *, use_cache: bool = True):  # noqa: ANN001
        return {
            "url": url,
            "final_url": url,
            "title": "Autohaus Demo",
            "has_https": True,
            "has_viewport": False,
            "load_ms": 900,
            "issues": ["Kein viewport — oft schlecht auf dem Handy"],
            "strengths": ["HTTPS aktiv"],
            "tech_stack": ["wordpress"],
            "improvement_score": 42,
            "detected_lang": "de",
            "analyzed_at": "2026-07-17T12:00:00+00:00",
        }

    monkeypatch.setattr(
        "app.integration.site_analysis_service.SiteAnalysisService.analyze",
        fake_analyze,
    )

    created = sales.create_order(
        {
            "business_name": "Autohaus Müller",
            "description": "KFZ-Werkstatt in Köln",
            "email": "info@mueller.de",
            "package_id": "business",
            "city": "Köln",
            "company_website": "mueller-auto.de",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert order["company_website"] == "https://mueller-auto.de"
    assert order["site_analysis"]["title"] == "Autohaus Demo"
    assert "Kein viewport" in order["site_analysis"]["issues"][0]

    brief = sales._factory_brief(order)
    assert "https://mueller-auto.de" in brief
    assert "Analyse der bestehenden Website" in brief
    assert "wordpress" in brief.lower()


def test_create_order_without_website_skips_analysis(tmp_path: Path):
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "Neu GmbH",
            "description": "Neues Geschäft ohne Website",
            "email": "neu@example.de",
            "package_id": "basic",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert not order.get("company_website")
    assert order.get("site_analysis") is None
