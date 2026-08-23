"""Global Market Registry — no fake LIVE coverage."""

from __future__ import annotations

from swarm.farm_channels.rapidapi import runtime_handlers
from swarm.farm_channels.rapidapi.markets import (
    coverage_summary,
    get_market,
    list_markets,
    market_capabilities_matrix,
    register_market,
)


def test_registry_has_iso_map_not_fake_live() -> None:
    cov = coverage_summary()
    assert cov["countries_total"] >= 200
    assert cov["live"] == 1
    assert cov["planned"] >= 200
    de = get_market("DE")
    assert de is not None
    assert de["status"] == "LIVE"
    at = get_market("AT")
    assert at is not None
    assert at["status"] == "PLANNED"
    us = get_market("US")
    assert us["status"] == "PLANNED"
    # No invented capabilities on PLANNED markets
    assert at["capabilities"]["postal"] is False
    assert us["capabilities"]["postal"] is False


def test_wave_matrix_honest() -> None:
    rows = market_capabilities_matrix(wave_only=True)
    by_cc = {r["country"]: r for r in rows}
    assert by_cc["DE"]["postal"] is True
    assert by_cc["DE"]["status"] == "LIVE"
    assert by_cc["AT"]["postal"] is False
    assert by_cc["AT"]["status"] == "PLANNED"


def test_register_market_does_not_invent_live() -> None:
    fr = register_market("FR")
    assert fr["ok"] is True
    assert fr["live_endpoints_allowed"] is False
    assert fr["status"] == "PLANNED"
    de = register_market("DE")
    assert de["live_endpoints_allowed"] is True


def test_de_plz_compat_still_works() -> None:
    code, body = runtime_handlers.handle_runtime(
        "de-plz-city-lookup", method="GET", path="/v1/de/plz/80331"
    )
    assert code == 200
    assert body["city"] == "München"
    assert body["country"] == "DE"
    assert body["postal_code"] == "80331"


def test_global_postal_live_de() -> None:
    code, body = runtime_handlers.handle_runtime(
        "global-postal-location", method="GET", path="/v1/de/postal/10115"
    )
    assert code == 200
    assert body["locality"] == "Berlin"
    assert body["postal_code"] == "10115"


def test_global_postal_blocks_planned_markets() -> None:
    for path in ("/v1/at/postal/1010", "/v1/us/postal/10001", "/v1/fr/postal/75001"):
        code, body = runtime_handlers.handle_runtime(
            "global-postal-location", method="GET", path=path
        )
        assert code == 403, path
        assert body["error"] == "market_not_live"
        assert body["status"] == "PLANNED"


def test_countries_list_is_registry_not_invented_cities() -> None:
    code, body = runtime_handlers.handle_runtime(
        "global-postal-location", method="GET", path="/v1/countries"
    )
    assert code == 200
    assert body["count"] >= 200
    # Must not invent a city field on country rows
    sample = body["countries"][0]
    assert "city" not in sample
    assert "status" in sample


def test_list_markets_count() -> None:
    assert len(list_markets()) >= 200


def test_planned_city_blocked() -> None:
    code, body = runtime_handlers.handle_runtime(
        "global-postal-location", method="GET", path="/v1/us/city/New%20York"
    )
    assert code == 403
    assert body["error"] == "market_not_live"


def test_de_city_from_sample() -> None:
    code, body = runtime_handlers.handle_runtime(
        "global-postal-location", method="GET", path="/v1/de/city/München"
    )
    assert code == 200
    assert "80331" in body["postal_codes"]


def test_quality_score_honest() -> None:
    from swarm.farm_channels.rapidapi.markets.quality import market_quality_score

    de = market_quality_score("DE")
    at = market_quality_score("AT")
    assert de["market_score"] > at["market_score"]
    assert at["market_score"] == 0
    assert de["coverage_score"] < 100  # sample, not national claim


def test_ingest_license_gate() -> None:
    from swarm.farm_channels.rapidapi.markets.ingestion import plan_ingest

    plan = plan_ingest("virtus_sample_de_plz")
    assert plan["ok"] is True
    assert plan["blocked_at"] is None
    unknown = plan_ingest("fake_unlicensed")
    assert unknown["ok"] is False
    assert unknown["blocked_at"] == "SOURCE"
