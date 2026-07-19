"""ExternalCapability registry + Nominatim/Wiki fallbacks (disabled by default)."""

from __future__ import annotations

import os

import pytest


def test_external_catalog_has_mission1_fields():
    from app.integration.external_capabilities import list_external_defs, snapshot

    rows = list_external_defs()
    assert any(r.id == "nominatim" for r in rows)
    assert any(r.id == "wikipedia" for r in rows)
    for r in rows:
        assert r.commercial_value
        assert r.mission_required in ("Mission1", "Mission2", "Optional", "Internal")

    snap = snapshot()
    assert snap["llm_chain_untouched"] is True
    assert snap["summary"]["enabled"] == 0  # default off
    nominatim = next(c for c in snap["capabilities"] if c["id"] == "nominatim")
    assert nominatim["mission1_activatable"] is True
    assert nominatim["enabled"] is False
    telegram = next(c for c in snap["capabilities"] if c["id"] == "telegram_bot")
    assert telegram["mission1_activatable"] is False


def test_nominatim_disabled_falls_back_to_google(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GENESIS_CAP_NOMINATIM", raising=False)
    from app.integration.external_capabilities import resolve_maps_embed
    from app.factory.package_features import maps_embed_src

    result = resolve_maps_embed(business_name="Test GmbH", city="Köln")
    assert result.used_fallback is True
    assert "google.com/maps" in result.data["embed_url"]

    src = maps_embed_src(business_name="Test GmbH", city="Köln")
    assert "google.com/maps" in src


def test_nominatim_enabled_without_network_still_falls_back(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_CAP_NOMINATIM", "1")

    def _boom(*_a, **_k):
        return None, "forced_offline"

    monkeypatch.setattr(
        "app.integration.external_capabilities.nominatim.http_get_json",
        _boom,
    )
    from app.integration.external_capabilities import resolve_maps_embed

    result = resolve_maps_embed(business_name="Praxis", city="Berlin")
    assert result.ok is True
    assert result.used_fallback is True
    assert "google.com/maps" in result.data["embed_url"]


def test_wiki_disabled_skips_enrichment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GENESIS_CAP_WIKIPEDIA", raising=False)
    monkeypatch.delenv("GENESIS_CAP_WIKIDATA", raising=False)
    from app.integration.external_capabilities import enrich_brief

    result = enrich_brief(niche_label="Zahnmedizin", city="Köln")
    assert result.used_fallback is True
    assert result.data.get("snippets") == []


def test_wiki_enabled_includes_source_disclaimer(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_CAP_WIKIPEDIA", "1")
    monkeypatch.delenv("GENESIS_CAP_WIKIDATA", raising=False)

    def _fake_get(url: str, **_kwargs):
        if "search/title" in url:
            return {"pages": [{"title": "Zahnmedizin", "key": "Zahnmedizin"}]}, None
        if "page/summary" in url:
            return {
                "extract": "Zahnmedizin ist ein Fachgebiet.",
                "content_urls": {
                    "desktop": {"page": "https://de.wikipedia.org/wiki/Zahnmedizin"}
                },
            }, None
        return None, "unexpected"

    monkeypatch.setattr(
        "app.integration.external_capabilities.wikiknowledge.http_get_json",
        _fake_get,
    )
    from app.integration.external_capabilities import enrich_brief

    result = enrich_brief(niche_label="Zahnmedizin")
    assert result.used_fallback is False
    sn = result.data["snippets"][0]
    assert sn["source_url"].startswith("https://")
    assert "nicht" in sn["disclaimer_de"].lower() or "Enzyklopädie" in sn["disclaimer_de"]


def test_foundation_registry_includes_external_api():
    from app.integration.capability_registry import CapabilityRegistry

    snap = CapabilityRegistry().snapshot()
    assert "external_api" in snap["summary"]["domains"]
    ext = [c for c in snap["capabilities"] if c["domain"] == "external_api"]
    assert len(ext) >= 3
    assert all("mission=" in (c.get("notes") or "") for c in ext)
