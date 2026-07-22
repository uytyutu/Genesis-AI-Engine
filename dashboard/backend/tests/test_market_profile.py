"""R3.4.1.1 — Market Profile entity + resolve (no Factory migration)."""

from __future__ import annotations

from app.factory.market_profile import (
    ENGINE_ID,
    MarketProfile,
    format_profile_table,
    list_market_codes,
    profile_table,
    resolve,
    resolve_or_none,
)


def test_engine_id():
    assert ENGINE_ID == "market_profile_v1"


def test_resolve_four_core_markets():
    for code in ("DE", "GB", "US", "UA"):
        p = resolve(code)
        assert isinstance(p, MarketProfile)
        assert p.market_code == code
        assert p.language
        assert p.currency
        assert p.locale
        assert p.phone_format
        assert p.address_format
        assert p.default_cta
        assert p.business_hours
        assert p.legal_footer_keys
        assert p.legal_page_slugs


def test_profiles_differ_where_expected():
    de, gb, us, ua = resolve("DE"), resolve("GB"), resolve("US"), resolve("UA")
    assert de.currency == "EUR"
    assert gb.currency == "GBP"
    assert us.currency == "USD"
    assert ua.currency == "UAH"
    assert de.default_cta == "Termin buchen"
    assert gb.default_cta == "Book Now"
    assert us.default_cta == "Get Quote"
    assert de.legal_footer_keys == ("impressum", "datenschutz")
    assert gb.legal_footer_keys == ("privacy", "contact")
    assert us.legal_footer_keys == ("privacy", "terms")
    assert ua.language == "uk"


def test_uk_alias_resolves_to_gb():
    assert resolve("UK").market_code == "GB"


def test_unknown_falls_back_to_de():
    assert resolve("ZZ").market_code == "DE"


def test_resolve_or_none_strict():
    assert resolve_or_none("DE") is not None
    assert resolve_or_none("ZZ") is None


def test_list_and_table_cover_four():
    assert list_market_codes() == ("DE", "GB", "US", "UA")
    rows = profile_table()
    assert len(rows) == 4
    assert {r["market"] for r in rows} == {"DE", "GB", "US", "UA"}
    text = format_profile_table()
    assert "Termin buchen" in text
    assert "Book Now" in text
    assert "Get Quote" in text
    assert "impressum" in text
