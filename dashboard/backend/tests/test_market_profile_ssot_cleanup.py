"""R3.4.1.5 — Cleanup & SSOT validation (Market Profile)."""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.composer_engine import compose_landing
from app.factory.market_profile import list_market_codes, resolve
from app.factory.package_features import resolve_package_features

_FACTORY = Path(__file__).resolve().parents[1] / "app" / "factory"


def _source(mod_name: str) -> str:
    import importlib

    mod = importlib.import_module(mod_name)
    return inspect.getsource(mod)


def test_deleted_market_legal_profile_module_gone():
    assert not (_FACTORY / "market_legal_profile.py").is_file()


def test_composer_ssot_only_market_profile_resolve():
    src = _source("app.factory.composer_engine")
    assert "resolve_market_design" not in src
    assert "apply_legal_footer_hrefs" not in src
    assert "landing_lang_for_market" not in src
    assert "if market ==" not in src
    assert "resolve_market_profile" in src


def test_footer_no_resolve_no_country_branches():
    from app.factory import layout_variants as lv

    src = inspect.getsource(lv.compose_footer) + "\n" + inspect.getsource(lv._footer_legal_html)
    assert "if market ==" not in src
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "resolve"


def test_landing_builder_ssot_path_no_legal_pack_helper():
    """SSOT branch must not call apply_legal_footer_hrefs (legacy-only)."""
    import ast

    src = inspect.getsource(
        __import__("app.factory.landing_builder", fromlist=["build_landing_html"]).build_landing_html
    )
    tree = ast.parse(src)
    calls = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "apply_legal_footer_hrefs":
                calls += 1
    assert calls == 1  # legacy else-branch only
    assert "use_profile_footer = True" in src
    assert "market_profile" in src

def test_four_markets_e2e_match_market_profile_only():
    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    features = resolve_package_features("business")
    rows = []
    for code in ("DE", "GB", "US", "UA"):
        p = resolve(code)
        composed = compose_landing(analysis, features=features, market_code=code)
        assert composed.market_profile["market_code"] == p.market_code
        assert composed.plan.language == p.language
        assert composed.plan.currency == p.currency
        assert composed.plan.locale == p.locale
        assert composed.plan.default_cta == p.default_cta
        assert composed.analysis is not None
        # Plan still carries market chrome; analysis CTA is niche-aware (appointment niches follow market).
        assert composed.plan.default_cta == p.default_cta
        assert composed.analysis.cta_label
        assert composed.analysis.cta_label in composed.html
        # US/GB localize appointment niches; DE salon keeps Termin buchen.
        if code == "DE":
            assert "Termin buchen" in composed.html or composed.analysis.cta_label
        else:
            assert p.default_cta in composed.html or composed.analysis.cta_label in composed.html
        assert f'lang="{p.language}"' in composed.html
        foot = re.search(r"<footer\b.*?</footer>", composed.html, flags=re.I | re.S)
        assert foot
        for slug in p.legal_page_slugs:
            assert slug in foot.group(0)
        keys_attr = ",".join(p.legal_footer_keys)
        assert f'data-legal-keys="{keys_attr}"' in foot.group(0)
        rows.append(
            {
                "market": code,
                "cta": composed.analysis.cta_label,
                "market_cta": p.default_cta,
                "language": p.language,
                "currency": p.currency,
                "locale": p.locale,
                "legal_keys": keys_attr,
            }
        )
    assert {r["market"] for r in rows} == {"DE", "GB", "US", "UA"}
    # Distinct market chrome across markets (SSOT)
    assert len({r["market_cta"] for r in rows}) >= 3
    assert len({r["currency"] for r in rows}) == 4
