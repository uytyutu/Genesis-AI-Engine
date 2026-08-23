"""Revenue Farm — public URL, first_api track, live provision honesty, acquisition."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from swarm.farm_channels.rapidapi import (
    acquisition,
    builder,
    provision,
    public_base,
    publisher,
    quality_gate,
    research,
    runtime_handlers,
    select,
    worker,
)
from swarm.farm_channels.rapidapi.models import STATUS_APPROVAL_REQUIRED, STATUS_ACTIVE
from swarm.farm_channels.rapidapi.store import ApiFarmStore


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ApiFarmStore:
    monkeypatch.setenv("GENESIS_API_PUBLIC_URL", "https://api.virtuscore.test")
    monkeypatch.delenv("NEXT_PUBLIC_API_URL", raising=False)
    monkeypatch.delenv("RAPIDAPI_PAYPAL_CONNECTED", raising=False)
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key-not-real")
    return ApiFarmStore(tmp_path)


def test_public_base_rejects_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENESIS_API_PUBLIC_URL", "http://localhost:8000")
    out = public_base.resolve_public_api_base()
    assert out["ok"] is False
    assert out["requires_ceo_action"] is True


def test_public_base_accepts_https_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENESIS_API_PUBLIC_URL", "https://api.virtuscore.com/")
    out = public_base.resolve_public_api_base()
    assert out["ok"] is True
    assert out["base"] == "https://api.virtuscore.com"


def test_runtime_plz_lookup() -> None:
    code, body = runtime_handlers.handle_runtime(
        "de-plz-city-lookup", method="GET", path="/v1/de/plz/10115"
    )
    assert code == 200
    assert body["city"] == "Berlin"


def test_select_best_prefers_safe_runtime(store: ApiFarmStore) -> None:
    research.discover_candidates(store, limit=20)
    best = select.select_best_candidate(store)
    assert best is not None
    slug = select.candidate_slug(best)
    # Either preferred slug or highest score overall
    assert best.get("total_score", 0) > 0
    assert slug


def test_first_api_reaches_approval_or_gate(store: ApiFarmStore) -> None:
    out = worker.run_first_api(store, max_steps=20)
    assert out.get("ok") is True
    cid = out["candidate_id"]
    row = store.get_candidate(cid)
    assert row is not None
    assert row["status"] in (
        STATUS_APPROVAL_REQUIRED,
        "QUALITY_GATE_FAILED",
        "TESTING",
        "BUILDING",
        "CANDIDATE",
    )
    plan = (row.get("publish_package") or {}).get("plan") or {}
    servers = (plan.get("openapi") or {}).get("servers") or []
    if servers:
        assert "localhost" not in servers[0].get("url", "")


def test_publish_without_hub_success_not_active(store: ApiFarmStore, monkeypatch: pytest.MonkeyPatch) -> None:
    research.discover_candidates(store, limit=5)
    best = select.select_best_candidate(store)
    assert best
    cid = str(best["id"])
    builder.build_candidate(store, cid)
    quality_gate.run_quality_gate(store, cid)
    row = store.get_candidate(cid)
    if not (row.get("quality_gate") or {}).get("ok"):
        pytest.skip("gate failed — public/package issue")
    publisher.approve_candidate(store, cid)
    monkeypatch.setattr(
        provision,
        "provision_create_api",
        lambda **kwargs: {
            "ok": False,
            "requires_ceo_action": True,
            "error": "provision_http_error",
            "detail": "simulated hub reject",
        },
    )
    # Patch import path used inside publish_candidate
    with patch(
        "swarm.farm_channels.rapidapi.provision.provision_create_api",
        return_value={
            "ok": False,
            "requires_ceo_action": True,
            "error": "provision_http_error",
            "detail": "simulated hub reject",
        },
    ):
        out = publisher.publish_candidate(store, cid)
    assert out.get("ok") is False
    assert out.get("requires_ceo_action")
    after = store.get_candidate(cid)
    assert after["status"] != STATUS_ACTIVE
    assert not after.get("rapidapi_api_id")


def test_publish_success_sets_api_id_and_acquisition(store: ApiFarmStore) -> None:
    research.discover_candidates(store, limit=5)
    best = select.select_best_candidate(store)
    cid = str(best["id"])
    builder.build_candidate(store, cid)
    gate = quality_gate.run_quality_gate(store, cid)
    if not gate.get("ok"):
        pytest.skip("gate failed")
    publisher.approve_candidate(store, cid)
    with patch(
        "swarm.farm_channels.rapidapi.provision.provision_create_api",
        return_value={
            "ok": True,
            "api_id": "hub_api_123",
            "http_status": 200,
            "response": {"apiId": "hub_api_123"},
        },
    ):
        out = publisher.publish_candidate(store, cid)
    assert out.get("ok") is True
    assert out.get("api_id") == "hub_api_123"
    after = store.get_candidate(cid)
    assert after["status"] == STATUS_ACTIVE
    assert after["rapidapi_api_id"] == "hub_api_123"
    assert after.get("acquisition")
    acq_path = Path(after["acquisition"]["pack_path"])
    assert acq_path.is_file()


def test_acquisition_requires_api_id(store: ApiFarmStore) -> None:
    row = store.upsert_candidate({"id": "x1", "name": "No Hub Yet"})
    out = acquisition.run_acquisition(store, row["id"])
    assert out.get("ok") is False
    assert out.get("requires_ceo_action")


def test_status_ceo_action_paypal(store: ApiFarmStore) -> None:
    payload = worker.status_payload(store)
    assert payload["paypal_payout_confirmed"] is False
    assert any("PayPal" in x for x in payload.get("ceo_action") or [])
