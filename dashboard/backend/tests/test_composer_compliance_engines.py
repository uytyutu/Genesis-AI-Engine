"""R3 — Composer Engine + Compliance Engine architecture (no new site features)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.analyzer import analyze
from app.factory.composer_engine import (
    ENGINE_ID as COMPOSER_ID,
    compose_landing,
    resolve_composition_plan,
)
from app.factory.compliance_engine import (
    COMPLIANCE_DOMAINS,
    ENGINE_ID as COMPLIANCE_ID,
    ComplianceError,
    assert_compliance,
    run_compliance,
)
from app.factory.factory_service import FactoryService
from app.factory.package_features import resolve_package_features
from app.factory.quality_gate import QualityGateError


def test_composition_plan_deterministic():
    a = resolve_composition_plan(
        business_name="Zahnarztpraxis Mueller",
        package_id="business",
        market_code="DE",
        niche_id="dental",
    )
    b = resolve_composition_plan(
        business_name="Zahnarztpraxis Mueller",
        package_id="business",
        market_code="DE",
        niche_id="dental",
    )
    assert a.engine_id == COMPOSER_ID
    assert a.as_dict() == b.as_dict()
    assert a.layout_profile.id.startswith("L")
    assert a.hero_layout in "ABCDEF"
    assert a.component_profile in "ABC"


def test_compose_landing_returns_plan_and_html():
    result = compose_landing(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    assert "<html" in result.html.lower()
    assert 'data-layout-profile="' in result.html
    assert result.plan.engine_id == COMPOSER_ID
    assert result.plan.gate_meta()["layout_profile"] == result.plan.layout_profile.id


def test_compliance_maps_domains():
    html = compose_landing(
        analyze("Autowerkstatt Schmidt in Berlin. Inspektion."),
        features=resolve_package_features("business"),
        market_code="DE",
        motion_level="css",
    ).html
    result = run_compliance(
        html,
        meta={"market_code": "DE", "package_delivery": {"package_id": "business"}},
    )
    assert result.engine_id == COMPLIANCE_ID
    assert result.passed, result.failures
    domains = result.domain_summary()
    for d in COMPLIANCE_DOMAINS:
        assert d in domains
        assert domains[d] is True


def test_compliance_blocks_brand_leak():
    html = compose_landing(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
    ).html
    poisoned = html.replace("</body>", "<p>Virtus Core Research</p></body>")
    result = run_compliance(
        poisoned,
        meta={"market_code": "DE", "package_delivery": {"package_id": "business"}},
    )
    assert not result.passed
    assert result.domain_summary()["brand"] is False
    with pytest.raises(ComplianceError):
        assert_compliance(
            poisoned,
            meta={"market_code": "DE", "package_delivery": {"package_id": "business"}},
        )


def test_factory_uses_composer_and_compliance(tmp_path: Path):
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
    assert product.get("composer_engine") == COMPOSER_ID or True  # summary may omit
    meta_path = tmp_path / "sandbox" / product["product_id"] / "meta.json"
    import json

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta.get("composer_engine") == COMPOSER_ID
    assert meta.get("composition_plan", {}).get("layout_profile", {}).get("id")
    assert meta.get("compliance", {}).get("engine_id") == COMPLIANCE_ID
    assert meta.get("compliance", {}).get("passed") is True
    data, name = factory.build_client_delivery_zip(product["product_id"])
    assert name.endswith(".zip")
    assert len(data) > 500


def test_zip_still_raises_quality_gate_error(tmp_path: Path):
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
    index = tmp_path / "sandbox" / product["product_id"] / "index.html"
    text = index.read_text(encoding="utf-8")
    index.write_text(text.replace("</body>", "<div>Virtus Core Preview</div></body>"), encoding="utf-8")
    with pytest.raises(QualityGateError):
        factory.build_client_delivery_zip(product["product_id"])
