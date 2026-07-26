"""AI Bot orders use dedicated product_kind=bot — not website packages."""

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


def test_bot_business_order_is_not_website_package(tmp_path: Path):
    svc = SalesOrderService(tmp_path / "mem", _Factory())
    created = svc.create_order(
        {
            "business_name": "Auto Service Bot GmbH",
            "description": "autoservice",
            "email": "owner@example.com",
            "package_id": "bot_business",
            "market_code": "DE",
            "purchase_type": "subscription",
            "bot_config": {
                "channels": ["telegram", "website_chat"],
                "channels_interest": ["whatsapp"],
                "capabilities": ["consult", "leads", "always_on"],
                "extras": ["ai_enabled", "company_training"],
                "knowledge_sources": ["website", "faq"],
                "handoff_rules": ["when_asks_manager", "when_unknown"],
                "languages": ["de", "ru"],
                "activity": "autoservice",
                "country": "DE",
            },
        }
    )
    assert created["ok"] is True
    assert created["package_name"] == "AI Bot Business"
    # Package 999 + second channel website_chat 149
    assert float(created["price_eur"]) == 1148.0
    order = svc.get_order(created["order_id"])
    assert order["package_id"] == "bot_business"
    assert order["product_kind"] == "bot"
    assert order.get("monthly_amount") == 199
    cfg = order.get("bot_config") or {}
    assert "telegram" in cfg["channels"]
    assert "website_chat" in cfg["channels"]
    assert "whatsapp" in cfg.get("channels_coming_soon_requested", [])
    assert "whatsapp" not in cfg["channels"]
    assert cfg["expandable_channels"] is True
    assert cfg["knowledge_sources"] == ["website", "faq"]
    assert "when_asks_manager" in cfg["handoff_rules"]
    assert cfg["languages"] == ["de", "ru"]
    assert cfg["channel_pricing"]["addon_setup_total_eur"] == 149


def test_coming_soon_channel_cannot_be_sold_as_available(tmp_path: Path):
    svc = SalesOrderService(tmp_path / "mem", _Factory())
    created = svc.create_order(
        {
            "business_name": "Test",
            "description": "demo",
            "email": "a@b.co",
            "package_id": "bot_starter",
            "market_code": "DE",
            "bot_config": {"channels": ["whatsapp", "telegram"]},
        }
    )
    order = svc.get_order(created["order_id"])
    cfg = order["bot_config"]
    assert cfg["channels"] == ["telegram"]
    assert float(created["price_eur"]) == float(order["price_eur"])


def test_single_channel_no_addon_fee(tmp_path: Path):
    svc = SalesOrderService(tmp_path / "mem", _Factory())
    created = svc.create_order(
        {
            "business_name": "Solo",
            "description": "demo",
            "email": "a@b.co",
            "package_id": "bot_business",
            "market_code": "DE",
            "bot_config": {"channels": ["telegram"]},
        }
    )
    assert float(created["price_eur"]) == 999.0
