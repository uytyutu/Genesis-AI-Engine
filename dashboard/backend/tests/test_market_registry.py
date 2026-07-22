"""R3.4.2.1 — Market Registry (behavior-preserving)."""

from __future__ import annotations

from app.factory.market_profile import MarketProfile, list_market_codes, resolve, resolve_or_none
from app.factory.market_registry import DEFAULT_REGISTRY, ENGINE_ID, MarketRegistry, get_registry


def test_registry_engine_and_seeded_markets():
    assert ENGINE_ID == "market_registry_v1"
    reg = get_registry()
    assert reg is DEFAULT_REGISTRY
    assert reg.codes() == ("DE", "GB", "US", "UA")
    assert list_market_codes() == ("DE", "GB", "US", "UA")


def test_resolve_uses_registry_unchanged_behavior():
    assert resolve("DE").default_cta == "Termin buchen"
    assert resolve("GB").currency == "GBP"
    assert resolve("US").default_cta == "Get Quote"
    assert resolve("UA").language == "uk"
    assert resolve("UK").market_code == "GB"  # alias
    assert resolve("ZZ").market_code == "DE"  # fallback
    assert resolve_or_none("ZZ") is None
    assert resolve_or_none("DE") is not None


def test_resolve_delegates_to_registry_instance():
    # Same object identity for registered markets
    assert resolve("DE") is DEFAULT_REGISTRY.get("DE")
    assert resolve("GB") is DEFAULT_REGISTRY.resolve("GB")


def test_register_new_market_on_isolated_registry():
    reg = MarketRegistry(fallback_code="DE")
    reg.register(resolve("DE"))
    reg.register(
        MarketProfile(
            market_code="FR",
            label="France",
            language="fr",
            currency="EUR",
            locale="fr_FR",
            phone_format="+33",
            address_format="FR",
            default_cta="Prendre rendez-vous",
            business_hours="Lun–Ven",
            legal_footer_keys=("mentions_legales", "confidentialite"),
            legal_page_slugs=("mentions-legales.html", "confidentialite.html"),
        )
    )
    assert "FR" in reg.codes()
    assert reg.resolve("FR").default_cta == "Prendre rendez-vous"
    # Default process registry unchanged
    assert "FR" not in DEFAULT_REGISTRY.codes()


def test_registry_table_matches_profiles():
    table = DEFAULT_REGISTRY.as_table()
    assert {r["market"] for r in table} == {"DE", "GB", "US", "UA"}
    de = next(r for r in table if r["market"] == "DE")
    assert de["cta"] == "Termin buchen"
    assert "impressum" in de["legal_keys"]
