"""Commerce Engine — localized checkout (C-001 Trust Item)."""

from __future__ import annotations

from pathlib import Path

from app.integration.commerce_engine import (
    resolve_checkout_market,
    resolve_final_offer,
    resolve_checkout_packages,
)


def test_de_checkout_unchanged():
    offer = resolve_final_offer("basic", "DE")
    assert offer.amount == 350
    assert offer.currency == "EUR"
    assert offer.symbol == "€"


def test_poland_basic_not_euro():
    offer = resolve_final_offer("basic", "PL")
    assert offer.currency == "PLN"
    assert offer.symbol == "zł"
    assert offer.amount == 1200
    assert "zł" in offer.price_label
    assert "€" not in offer.price_label


def test_krakow_city_resolves_poland():
    code = resolve_checkout_market(city="Kraków")
    assert code == "PL"


def test_krakow_resident_german_target_market():
    text = "Я живу в Кракове, но строю сайт для немецкой компании."
    code = resolve_checkout_market(city="Kraków", extra_text=text)
    assert code == "DE"
    offer = resolve_final_offer("basic", code)
    assert offer.currency == "EUR"


def test_poland_packages_api_shape():
    payload = resolve_checkout_packages("PL", deliverables_by_id={"basic": ["x"]})
    basic = payload["packages"][0]
    assert payload["currency"] == "PLN"
    assert basic["price_eur"] == 1200.0
    assert basic["currency"] == "PLN"


def test_sales_order_packages_pl(tmp_path: Path):
    from app.integration.sales_order_service import SalesOrderService

    class _Factory:
        def submit(self, _intent):
            return {"product_id": "p1"}

    sales = SalesOrderService(tmp_path, _Factory())
    payload = sales.checkout_packages(city="Kraków")
    assert payload["market_code"] == "PL"
    assert payload["packages"][0]["currency"] == "PLN"
