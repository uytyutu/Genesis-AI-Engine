"""Research 3D gates — isolated; Path A must not depend on these modules at checkout."""

from __future__ import annotations

from pathlib import Path

from app.factory.research_3d.fallback_spec import resolve_delivery_mode
from app.factory.research_3d.glb_budget import check_glb_budget
from app.factory.research_3d.license_gate import check_asset_license
from app.factory.research_3d.niche_catalog import list_market_slots, list_niche_slots, niche_coverage


def test_license_gate_fixture(tmp_path: Path):
    (tmp_path / "LICENSE.txt").write_text("CC0-1.0\n", encoding="utf-8")
    (tmp_path / "CREDITS.txt").write_text(
        "Author: Test\nSource: https://example.com\nLicense: CC0-1.0\n",
        encoding="utf-8",
    )
    r = check_asset_license(tmp_path)
    assert r.ok and r.code == "ok"


def test_license_gate_blocks_nc(tmp_path: Path):
    (tmp_path / "LICENSE.txt").write_text("CC-BY-NC-4.0 non-commercial\n", encoding="utf-8")
    (tmp_path / "CREDITS.txt").write_text("Author: X\nSource: y\nLicense: NC\n", encoding="utf-8")
    r = check_asset_license(tmp_path)
    assert not r.ok
    assert r.code == "blocked_license"


def test_glb_budget(tmp_path: Path):
    glb = tmp_path / "hero.glb"
    glb.write_bytes(b"x" * 1000)
    ok = check_glb_budget(glb)
    assert ok.ok
    huge = tmp_path / "big.glb"
    huge.write_bytes(b"x" * (3_000_000))
    bad = check_glb_budget(huge)
    assert not bad.ok
    assert bad.code == "glb_too_large"


def test_fallback_matrix():
    assert resolve_delivery_mode(webgl_ok=True, license_ok=True, budget_ok=True) == "webgl_3d"
    assert resolve_delivery_mode(webgl_ok=False, license_ok=True, budget_ok=True) == "css_motion"
    assert resolve_delivery_mode(webgl_ok=True, license_ok=False, budget_ok=True) == "classic"
    assert resolve_delivery_mode(webgl_ok=True, license_ok=True, budget_ok=False) == "css_motion"


def test_niche_and_market_slots():
    niches = list_niche_slots()
    markets = list_market_slots()
    from app.factory.niche_profiles import known_niche_ids

    ids = {n["niche_id"] for n in niches}
    assert ids == set(known_niche_ids())
    assert "DE" in markets and "US" in markets and "UA" in markets
    cov = niche_coverage()
    assert cov["reference_niche"] == "dental"
    assert all(n["status"] == "ready" for n in niches)
    assert cov["niches_ready"] == cov["niches_total"]


def test_path_a_factory_does_not_import_research_3d():
    """Guard: production Factory entrypoints stay free of research_3d imports."""
    import ast
    from pathlib import Path

    roots = [
        Path(__file__).resolve().parents[1]
        / "app"
        / "factory"
        / "factory_service.py",
        Path(__file__).resolve().parents[1]
        / "app"
        / "integration"
        / "sales_order_service.py",
        Path(__file__).resolve().parents[1]
        / "app"
        / "integration"
        / "payment_checkout_service.py",
    ]
    for path in roots:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "research_3d" not in alias.name
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "research_3d" not in node.module
