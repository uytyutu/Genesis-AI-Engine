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


def test_quality_gate_blocks_placeholder_dental():
    from app.factory.research_3d.quality_gate import (
        quality_allows_client_3d,
        resolve_visual_mode,
    )

    assert quality_allows_client_3d("placeholder") is False
    assert quality_allows_client_3d("approved") is True
    # Professional niche + placeholder → photo (or css), never webgl_3d
    assert (
        resolve_visual_mode(
            niche_id="dental",
            quality_tier="placeholder",
            webgl_ok=True,
            license_ok=True,
            budget_ok=True,
            photo_available=True,
        )
        == "photo"
    )
    assert (
        resolve_delivery_mode(
            webgl_ok=True,
            license_ok=True,
            budget_ok=True,
            niche_id="dental",
            quality_tier="placeholder",
            photo_available=True,
        )
        == "photo"
    )
    assert (
        resolve_delivery_mode(
            webgl_ok=True,
            license_ok=True,
            budget_ok=True,
            niche_id="dental",
            quality_tier="approved",
            photo_available=True,
        )
        == "webgl_3d"
    )


def test_niche_showcase_map_and_tiers():
    from app.factory.research_3d.niche_showcase import (
        resolve_package_visual_tier,
        showcase_for_niche,
    )

    dental = showcase_for_niche("dental")
    assert dental is not None
    assert "implant" in (dental.get("preferred_assets") or [])
    assert dental.get("glb_candidates")
    assert resolve_package_visual_tier("basic") == "basic"
    assert resolve_package_visual_tier("business") == "business"
    assert resolve_package_visual_tier("premium") == "premium"


def test_showcase_registry_delivery():
    from app.factory.research_3d.showcase_registry import (
        canonicalize_niche,
        list_showcase_niches,
        resolve_showcase,
        resolve_showcase_delivery,
        build_showcase_embed_config,
    )

    niches = list_showcase_niches()
    assert "dental" in niches
    assert "auto" in niches
    assert len(niches) >= 8

    assert canonicalize_niche("solar") == "energy"
    assert canonicalize_niche("hvac") == "appliance"
    assert canonicalize_niche("windows") == "handwerk"
    assert canonicalize_niche("dentist") == "dental"

    dental = resolve_showcase("dental")
    assert dental is not None
    assert dental.preview_rel
    assert dental.products

    solar = resolve_showcase("solar")
    assert solar is not None
    assert solar.niche_id == "energy"

    basic = resolve_showcase_delivery(niche_id="dental", tier="basic")
    assert basic["mode"] == "none"

    business = resolve_showcase_delivery(niche_id="dental", tier="business")
    assert business["mode"] == "preview"
    assert business["preview"]

    premium = resolve_showcase_delivery(niche_id="dental", tier="premium")
    assert premium["mode"] == "preview"
    assert premium["preview"]
    assert premium["reason"] == "premium_awaiting_approved_model"
    assert premium["engine"] == "visual_experience"
    assert premium["product_id"]

    implant = resolve_showcase_delivery(
        niche_id="dental",
        tier="premium",
        specialization="implantology oral surgery",
    )
    assert implant["ok"]
    assert implant["product_id"] == "implant"
    assert implant["match_score"] >= implant["product_score"]

    scanner = resolve_showcase_delivery(
        niche_id="dental",
        tier="premium",
        specialization="diagnostics digital scanner",
    )
    assert scanner["product_id"] == "scanner"

    auto = resolve_showcase_delivery(niche_id="auto", tier="premium")
    assert auto["mode"] == "preview"
    assert auto["reason"] == "premium_awaiting_approved_model"

    unknown = resolve_showcase_delivery(niche_id="totally_unknown_xyz", tier="premium")
    assert unknown["ok"] is True
    assert unknown["fallback_generic"] is True
    assert unknown["mode"] in ("preview", "css_motion")

    embed = build_showcase_embed_config(niche_id="kitchen", tier="premium")
    assert embed["component"] == "visual_experience"
    assert embed["never_empty"] is True
    assert embed["niche_id"] == "appliance"


def test_visual_experience_specialization_map():
    from app.factory.research_3d.visual_experience_registry import (
        load_specialization_map,
        resolve_specialization_profile,
        resolve_visual_experience,
    )

    data = load_specialization_map()
    assert data.get("specializations")
    assert "implantology" in data["specializations"]

    profile = resolve_specialization_profile(
        "implantology oral surgery", niche_id="dental"
    )
    assert profile is not None
    assert profile["id"] == "implantology"
    assert "implant" in profile["products"]
    assert len(profile.get("hotspots") or []) <= 4
    assert profile.get("cta_resolved")
    assert profile.get("messages_resolved")

    exp = resolve_visual_experience(
        niche_id="dental",
        tier="premium",
        specialization="implantology",
    )
    assert exp["ok"]
    assert exp["engine"] == "visual_experience"
    assert exp["product_id"] == "implant"
    assert exp["specialization_id"] == "implantology"
    assert exp["cta"]["id"] == "appointment"
    assert len(exp.get("hotspots") or []) <= 4

    scan = resolve_visual_experience(
        niche_id="dental",
        tier="premium",
        specialization="diagnostics scanner",
    )
    assert scan["product_id"] == "scanner"


def test_showcase_library_scales_without_dental_lock():
    from app.factory.research_3d.showcase_registry import (
        load_library_manifest,
        resolve_showcase_delivery,
        list_niche_products,
        pick_product,
        resolve_niche_catalog,
        score_product,
    )

    for niche in ("auto", "beauty", "energy", "appliance", "generic"):
        d = resolve_showcase_delivery(niche_id=niche, tier="premium")
        assert d["ok"]
        assert d["niche_id"] == niche
        assert d["mode"] in ("preview", "interactive_3d", "css_motion")
        assert d["engine"] == "visual_experience"

    assert "implant" in list_niche_products("dental")
    assert "engine" in list_niche_products("auto")
    assert "solar_panel" in list_niche_products("energy")

    dental = resolve_niche_catalog("dental")
    assert dental is not None
    align = pick_product(dental, specialization="orthodontics aligners")
    assert align.product_id == "aligners"

    engine = resolve_niche_catalog("auto")
    assert engine is not None
    e = pick_product(engine, specialization="turbo performance tuning")
    assert e.product_id == "turbo"
    assert score_product(e, specialization="turbo") > score_product(
        pick_product(engine, specialization="brakes safety"),
        specialization="turbo",
    )

    manifest = load_library_manifest()
    assert manifest.get("engine") == "visual_experience"
    assert manifest.get("aliases")
    assert any(n.get("niche_id") == "dental" for n in (manifest.get("niches") or []))


def test_niche_and_market_slots():
    niches = list_niche_slots()
    markets = list_market_slots()
    from app.factory.niche_profiles import known_niche_ids
    from pathlib import Path

    ids = {n["niche_id"] for n in niches}
    assert ids == set(known_niche_ids())
    assert "DE" in markets and "US" in markets and "UA" in markets
    cov = niche_coverage()
    assert cov["reference_niche"] == "dental"
    assert cov.get("examples_per_niche") == 5
    assert all(n["status"] == "ready" for n in niches)
    assert cov["niches_ready"] == cov["niches_total"]
    scenes = Path(__file__).resolve().parents[1] / "_research_3d" / "scenes"
    for niche in known_niche_ids():
        examples = list((scenes / niche / "examples").glob("*.glb"))
        assert len(examples) == 5, niche


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
