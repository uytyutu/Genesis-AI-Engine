"""Foundation F1 — unified capability & feature registries."""

from pathlib import Path

from app.integration.capability_registry import CapabilityRegistry, REGISTRY_VERSION
from app.integration.feature_registry import FeatureRegistry


def test_capability_registry_merges_known_sources():
    reg = CapabilityRegistry()
    snap = reg.snapshot()
    assert snap["version"] == REGISTRY_VERSION
    caps = snap["capabilities"]
    ids = {c["id"] for c in caps}
    assert "genesis-rules" in ids
    assert "product:landing" in ids
    assert "subscription:free" in ids
    assert "factory:landing-page" in ids
    assert "opportunity:manual" in ids


def test_landing_enabled_factory_others_off():
    reg = CapabilityRegistry()
    landing = reg.get("factory:landing-page")
    bot = reg.get("factory:telegram-bot")
    assert landing is not None and landing.enabled is True
    assert bot is not None and bot.enabled is False


def test_public_product_landing_available():
    reg = CapabilityRegistry()
    row = reg.get("product:landing")
    assert row is not None
    assert row.enabled is True
    assert row.domain == "public_product"


def test_feature_registry_all_product_layers_disabled_by_default():
    reg = FeatureRegistry()
    snap = reg.snapshot()
    assert snap["summary"]["any_product_feature_enabled"] is False
    for fid in (
        "workspace",
        "co_creation",
        "specialists",
        "subscriptions",
        "marketplace",
        "business_automation",
        "device_continuity",
    ):
        row = reg.get(fid)
        assert row is not None
        assert row.enabled is False
    assert reg.is_enabled("attachment_transparency") is True


def test_feature_registry_memory_override(tmp_path: Path):
    cfg = tmp_path / "platform_features.json"
    cfg.write_text('{"features": {"workspace": true}}', encoding="utf-8")
    reg = FeatureRegistry(memory_dir=tmp_path)
    assert reg.is_enabled("workspace") is True
    assert reg.is_enabled("specialists") is False
