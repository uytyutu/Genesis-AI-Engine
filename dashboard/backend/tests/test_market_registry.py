"""R3.4.2.1 — Market Registry (behavior-preserving)."""

from __future__ import annotations

from app.factory.market_profile import MarketProfile, list_market_codes, resolve, resolve_or_none
from app.factory.market_registry import DEFAULT_REGISTRY, ENGINE_ID, MarketRegistry, get_registry


def test_registry_engine_and_seeded_markets():
    assert ENGINE_ID == "market_registry_v1"
    reg = get_registry()
    assert reg is DEFAULT_REGISTRY
    for code in ("DE", "GB", "US", "UA", "FR", "NL", "AT", "ES"):
        assert code in reg.codes()
        assert code in list_market_codes()


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
            market_code="XX",
            label="Testland",
            language="en",
            currency="EUR",
            locale="en_XX",
            phone_format="+99",
            address_format="XX",
            default_cta="Try Now",
            business_hours="Mon–Fri",
            legal_footer_keys=("privacy", "contact"),
            legal_page_slugs=("privacy.html", "#contact"),
        )
    )
    assert "XX" in reg.codes()
    assert reg.resolve("XX").default_cta == "Try Now"
    # Default process registry unchanged by isolated register
    assert "XX" not in DEFAULT_REGISTRY.codes()


def test_registry_table_matches_profiles():
    table = DEFAULT_REGISTRY.as_table()
    assert {"DE", "GB", "US", "UA", "FR", "NL", "AT", "ES"}.issubset(
        {r["market"] for r in table}
    )
    de = next(r for r in table if r["market"] == "DE")
    assert de["cta"] == "Termin buchen"
    assert "impressum" in de["legal_keys"]
