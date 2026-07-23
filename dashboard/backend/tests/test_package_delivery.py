"""Path A — Factory HTML must match paid package deliverables."""

from __future__ import annotations

from pathlib import Path

from app.factory.factory_service import FactoryService
from app.factory.package_features import resolve_package_features, whatsapp_href
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.sales_order_service import SalesOrderService
from app.schemas import FactoryIntentRequest


def test_package_feature_matrix():
    basic = resolve_package_features("basic")
    business = resolve_package_features("business")
    premium = resolve_package_features("premium")
    assert basic.whatsapp and basic.contact_form and not basic.maps
    assert basic.testimonials and basic.process and basic.mid_cta and basic.trust_bar
    assert business.maps and business.testimonials and business.logo_slot and business.faq
    assert premium.analytics and premium.calculator and premium.premium_design


def test_whatsapp_href_de_mobile():
    assert whatsapp_href("+49 171 1234567").endswith("491711234567")
    assert whatsapp_href("0171 1234567").endswith("491711234567")


def test_factory_basic_includes_whatsapp_and_form(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Autowerkstatt Müller in Köln — Inspektion und Reifen",
        package_id="basic",
        contacts={
            "business_name": "Autowerkstatt Müller",
            "phone": "+49 221 555 0101",
            "whatsapp": "+49 171 5550101",
            "email": "info@mueller-werkstatt.de",
            "city": "Köln",
        },
    )
    html = (tmp_path / "sandbox" / product["product_id"] / "index.html").read_text(encoding="utf-8")
    assert "wa.me/491715550101" in html
    assert "contact-form" in html or "Anfrage senden" in html
    assert "Autowerkstatt Müller" in html
    assert "+49 221 555 0101" in html
    assert 'id="maps"' not in html
    # RC1: fabricated Kundenstimmen forbidden — section only with real client reviews
    assert 'id="testimonials"' not in html
    assert "Beispieltexte" not in html
    assert "G-XXXXXXXXXX" not in html


def test_factory_business_maps_reviews_logo(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Kfz-Werkstatt Schmidt — Diagnose und Ölwechsel",
        package_id="business",
        contacts={
            "business_name": "Kfz Schmidt",
            "phone": "+49 221 111",
            "email": "hallo@schmidt.de",
            "city": "Köln",
            "street": "Hauptstr. 1",
        },
    )
    html = (tmp_path / "sandbox" / product["product_id"] / "index.html").read_text(encoding="utf-8")
    assert 'id="maps"' in html
    assert "maps.google.com" in html
    # RC1: no placeholder reviews without real client evidence
    assert 'id="testimonials"' not in html
    assert "Beispieltexte" not in html
    assert 'src="assets/logo.png"' in html
    assert "application/ld+json" in html
    assert "G-XXXXXXXXXX" not in html


def test_factory_premium_analytics_calculator(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Premium Autowerkstatt — Festpreis Diagnose",
        package_id="premium",
        contacts={
            "business_name": "Premium Auto",
            "phone": "+49 221 999",
            "email": "go@premium.de",
            "city": "Bonn",
        },
    )
    html = (tmp_path / "sandbox" / product["product_id"] / "index.html").read_text(encoding="utf-8")
    assert "G-XXXXXXXXXX" in html
    assert 'id="calculator"' in html
    assert 'id="maps"' in html
    meta = product.get("package_delivery") or {}
    # summary may not expose package_delivery — check meta file
    meta_path = tmp_path / "sandbox" / product["product_id"] / "meta.json"
    assert meta_path.is_file()
    text = meta_path.read_text(encoding="utf-8")
    assert '"analytics": true' in text
    assert '"calculator": true' in text


def test_sales_start_production_passes_package(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp_path, factory=factory)
    sales = SalesOrderService(tmp_path, intent)
    created = sales.create_order(
        {
            "business_name": "Werkstatt Pilot",
            "description": "Autowerkstatt mit Inspektion",
            "email": "pilot@test.de",
            "phone": "+49 221 777",
            "whatsapp": "+49 171 7770000",
            "city": "Köln",
            "package_id": "business",
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    order["status"] = "paid"
    sales._save_order(order)
    result = sales.start_production(order_id)
    product_id = result["product_id"]
    html = (tmp_path / "sandbox" / product_id / "index.html").read_text(encoding="utf-8")
    assert "Werkstatt Pilot" in html
    assert 'id="maps"' in html
    assert "wa.me/" in html


def test_factory_intent_request_accepts_package():
    req = FactoryIntentRequest(
        product_type="landing-page",
        description="Landing für Autowerkstatt",
        package_id="premium",
        contacts={"city": "Köln", "phone": "+49 1"},
    )
    assert req.package_id == "premium"
