"""R3.4.2.2 — Factory consumers read markets via Registry / MarketProfile."""

from __future__ import annotations

from app.factory.landing_i18n import (
    apply_legal_footer_hrefs,
    landing_lang_for_market,
    maps_country_label,
    ui_strings,
)
from app.factory.market_delivery import market_ui_lang
from app.factory.market_profile import legal_link_pairs, resolve
from app.factory.market_registry import DEFAULT_REGISTRY


def test_landing_lang_uses_registry_for_registered():
    assert landing_lang_for_market("DE") == resolve("DE").language
    assert landing_lang_for_market("GB") == resolve("GB").language
    assert landing_lang_for_market("UK") == resolve("GB").language
    assert landing_lang_for_market("UA") == resolve("UA").language
    # Unregistered still uses delivery map (no behavior regression)
    assert landing_lang_for_market("RU") == "ru"


def test_market_ui_lang_uses_registry_for_registered():
    assert market_ui_lang("DE") == "de"
    assert market_ui_lang("US") == "en"
    assert market_ui_lang("UA") == "uk"
    assert market_ui_lang("RU") == "ru"


def test_legal_footer_hrefs_from_profile_when_registered():
    ui = ui_strings("en")
    out = apply_legal_footer_hrefs(ui, "GB")
    pairs = legal_link_pairs(resolve("GB"))
    assert out["legal_a"] == pairs[0][0]
    assert out["legal_a_href"] == pairs[0][1]
    assert out["legal_b_href"] == pairs[1][1]
    de = apply_legal_footer_hrefs(ui_strings("de"), "DE")
    assert de["legal_a_href"] == "impressum.html"
    assert de["legal_b_href"] == "datenschutz.html"


def test_maps_country_label_from_profile_label():
    assert maps_country_label("DE") == resolve("DE").label
    assert maps_country_label("GB") == resolve("GB").label
    # Unregistered keeps delivery map
    assert maps_country_label("FR") == "France"


def test_no_duplicate_registered_market_list_outside_registry():
    """Factory chrome consumers must not hardcode DE/GB/US/UA as a second registry."""
    import ast
    from pathlib import Path

    factory = Path(__file__).resolve().parents[1] / "app" / "factory"
    offenders = []
    skip = {"market_profile.py", "market_registry.py", "market_delivery.py", "market_design.py"}
    for path in factory.glob("*.py"):
        if path.name in skip:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Tuple, ast.List)):
                vals = []
                for elt in node.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        vals.append(elt.value)
                if {"DE", "GB", "US", "UA"}.issubset(set(vals)) and len(vals) <= 6:
                    offenders.append(f"{path.name}: hardcoded {vals}")
    assert not offenders, offenders


def test_registry_is_single_source_for_registered_codes():
    for code in ("DE", "GB", "US", "UA", "FR", "NL", "AT", "ES"):
        assert code in DEFAULT_REGISTRY.codes()
        assert resolve(code) is DEFAULT_REGISTRY.get(code)
