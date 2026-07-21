"""Factory Quality Gate — PASS required before client ZIP."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.analyzer import analyze
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features
from app.factory.quality_gate import QualityGateError, run_quality_gate
from app.factory.validator import validate_landing


def test_quality_gate_passes_for_business_de():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate."),
        features=resolve_package_features("business"),
        market_code="DE",
        motion_level="css",
        client_gallery=["assets/g1.jpg", "assets/g2.jpg"],
    )
    result = run_quality_gate(
        html,
        meta={
            "market_code": "DE",
            "package_delivery": {"package_id": "business"},
        },
    )
    assert result.passed, result.failures
    assert 'rel="canonical"' in html


def test_quality_gate_fails_on_platform_chrome():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    poisoned = html.replace("</body>", "<p>Virtus Core Research Demo</p></body>")
    result = run_quality_gate(poisoned, meta={"market_code": "DE", "package_delivery": {"package_id": "business"}})
    assert not result.passed
    assert any("brand" in f for f in result.failures)


def test_quality_gate_fails_on_lorem():
    html = build_landing_html(
        analyze("Autowerkstatt Schmidt in Berlin. Inspektion."),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    poisoned = html.replace("</h1>", "</h1><p>Lorem ipsum dolor sit amet</p>", 1)
    result = run_quality_gate(poisoned, meta={"market_code": "DE", "package_delivery": {"package_id": "business"}})
    assert not result.passed
    assert any("localization" in f for f in result.failures)


def test_zip_blocked_when_gate_fails(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Mueller in Koeln. Prophylaxe.",
        package_id="business",
        client_legal={
            "owner_name": "Dr. Test",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "a@b.de",
        },
    )
    pid = product["product_id"]
    index = tmp_path / "sandbox" / pid / "index.html"
    text = index.read_text(encoding="utf-8")
    index.write_text(text.replace("</body>", "<div>Virtus Core Preview</div></body>"), encoding="utf-8")
    with pytest.raises(QualityGateError):
        factory.build_client_delivery_zip(pid)


def test_zip_passes_clean_product(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate.",
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "Dr. Test",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "a@b.de",
        },
    )
    assert product.get("quality_gate", {}).get("passed") is True or product.get("validation_passed") is True
    data, name = factory.build_client_delivery_zip(product["product_id"])
    assert name.endswith(".zip")
    assert len(data) > 100


def test_validate_landing_includes_gate():
    html = build_landing_html(
        analyze("Clínica Dental Sol in Madrid. Implantes."),
        features=resolve_package_features("business"),
        market_code="ES",
        motion_level="css",
    )
    result = validate_landing(
        html,
        meta={"market_code": "ES", "package_delivery": {"package_id": "business"}},
    )
    assert result.quality_gate is not None
    assert result.passed is True
    assert any(c["id"] == "quality_gate" for c in result.technical_checks)
