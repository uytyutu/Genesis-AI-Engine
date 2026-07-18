"""Payment amount/currency gates + niche landings for DE Path A."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.analyzer import analyze
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def submit(self, _intent):
        return {"product_id": "prod-pay-1"}


def _pipeline(tmp_path: Path) -> tuple[SalesOrderService, RevenuePipelineService]:
    sales = SalesOrderService(tmp_path, _Factory())
    checkout = PaymentCheckoutService(tmp_path)
    finance = FinanceService(tmp_path)
    notifications = OwnerNotificationService(tmp_path)
    revenue = RevenuePipelineService(sales, finance, checkout, notifications)
    return sales, revenue


def test_business_order_stores_650_and_rejects_wrong_amount(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    sales, revenue = _pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Handwerk Fischer",
            "description": "Handwerker Allrounder Köln",
            "email": "fischer@test.de",
            "package_id": "business",
            "city": "Köln",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order["package_id"] == "business"
    assert float(order["price_eur"]) == 650.0
    assert str(order.get("currency") or "EUR").upper() == "EUR"

    with pytest.raises(ValueError, match="amount_mismatch"):
        revenue._apply_payment(
            order_id=created["order_id"],
            amount_eur=350.0,
            currency="eur",
            provider="stripe",
            sender="pay@test.de",
            external_id="cs_wrong_amount",
        )


def test_currency_mismatch_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    sales, revenue = _pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "PC Service",
            "description": "PC-Reparatur Laptop",
            "email": "pc@test.de",
            "package_id": "business",
            "city": "Bonn",
        }
    )
    with pytest.raises(ValueError, match="currency_mismatch"):
        revenue._apply_payment(
            order_id=created["order_id"],
            amount_eur=650.0,
            currency="usd",
            provider="stripe",
            sender="pay@test.de",
            external_id="cs_wrong_cur",
        )


def test_niche_profiles_ready_for_niche_id():
    from app.factory.niche_profiles import known_niche_ids, resolve_niche_profile

    assert "auto" in known_niche_ids()
    assert resolve_niche_profile("auto").style.primary.startswith("#")
    assert resolve_niche_profile("dental").niche_id == "dental"
    assert resolve_niche_profile("unknown-xyz").niche_id == "generic"
    html_auto = build_landing_html(analyze("Autowerkstatt Müller KFZ Köln"))
    html_dental = build_landing_html(analyze("Zahnarztpraxis Weber dental Köln"))
    assert html_auto != html_dental
    assert "#b91c1c" in html_auto or "b91c1c" in html_auto
    assert "Zahn" in html_dental or "dental" in html_dental.lower()


def test_business_factory_path_three_meister_niches(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp_path, factory=factory)
    sales = SalesOrderService(tmp_path, intent)

    cases = (
        ("Handwerk Fischer", "Handwerker Allrounder renovierung montage", "handwerk", "Montage"),
        ("PC Service Schmidt", "PC-Reparatur Laptop Datenrettung", "computer", "Laptop"),
        ("Hausgeräte Schneider", "Hausgeräte Waschmaschine Kühlschrank", "appliance", "Waschmaschine"),
    )
    for name, desc, niche, marker in cases:
        created = sales.create_order(
            {
                "business_name": name,
                "description": desc,
                "email": f"{niche}@test.de",
                "phone": "+49 221 100200",
                "whatsapp": "+49 171 100200",
                "city": "Köln",
                "package_id": "business",
            }
        )
        order = sales.get_order(created["order_id"])
        assert float(order["price_eur"]) == 650.0
        order["status"] = "paid"
        sales._save_order(order)
        prod = sales.start_production(created["order_id"])
        html = (tmp_path / "sandbox" / prod["product_id"] / "index.html").read_text(encoding="utf-8")
        assert analyze(desc).niche == niche
        assert name in html
        assert marker in html or niche in html.lower() or "Reparatur" in html or "Handwerk" in html
        assert "wa.me/" in html
        assert 'id="maps"' in html
        assert "Beispieltexte" in html
        assert 'src="assets/logo.png"' in html
        assert "G-XXXXXXXXXX" not in html
