"""Owner Auto Mode gate — no perpetual ceo_required when prerequisites met."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.swarm_bridge import ensure_swarm_importable

ensure_swarm_importable()
from swarm.farm_execution_plan import (
    auto_publish_prerequisites,
    plan_rapidapi_provider,
)


@pytest.fixture(autouse=True)
def _clear_auto_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "STRIPE_SECRET_KEY",
        "RAPIDAPI_KEY",
        "RAPIDAPI_PUBLISH_TOKEN",
        "RAPIDAPI_PROVIDER_TOKEN",
        "GENESIS_OWNER_AUTO_PUBLISH",
        "VIRTUS_OWNER_AUTO_MODE",
        "RAPIDAPI_PAYOUTS_READY",
        "GENESIS_RAPIDAPI_PUBLISH_WEBHOOK",
    ):
        monkeypatch.delenv(key, raising=False)


def test_rapidapi_materials_alone_still_ceo_required(tmp_path: Path):
    plan = plan_rapidapi_provider(tmp_path)
    assert plan["ok"] is True
    assert (tmp_path / "farm_exec_rapidapi_openapi.json").is_file()
    pub = next(c for c in plan["checklist"] if c["id"] == "publish_owner")
    assert pub["status"] == "ceo_required"
    assert plan["stage"] == "waiting_for_ceo"
    assert plan["auto_publish"]["ready"] is False


def test_auto_publish_when_all_gates_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_test_fixture_not_real")
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid_key_fixture")
    monkeypatch.setenv("GENESIS_OWNER_AUTO_PUBLISH", "1")
    monkeypatch.setenv("RAPIDAPI_PAYOUTS_READY", "1")

    gate = auto_publish_prerequisites()
    assert gate["ready"] is True

    plan = plan_rapidapi_provider(tmp_path)
    pub = next(c for c in plan["checklist"] if c["id"] == "publish_owner")
    assert pub["status"] in ("pass", "done")
    assert pub["auto"] is True
    assert "ceo_required" not in {c["status"] for c in plan["checklist"]}
    assert plan["stage"] in {"ready_for_auto_publish", "ready_for_production"}
    assert (tmp_path / "farm_exec_rapidapi_auto_publish.json").is_file()


def test_missing_auto_mode_keeps_ceo_even_if_keys_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_test_fixture_not_real")
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid_key_fixture")
    # no GENESIS_OWNER_AUTO_PUBLISH

    plan = plan_rapidapi_provider(tmp_path)
    assert plan["auto_publish"]["checks"]["owner_auto_mode"] is False
    pub = next(c for c in plan["checklist"] if c["id"] == "publish_owner")
    assert pub["status"] == "ceo_required"
    auto_gate = next(c for c in plan["checklist"] if c["id"] == "gate_owner_auto")
    assert auto_gate["status"] == "ceo_required"
    assert "GENESIS_OWNER_AUTO_PUBLISH" in auto_gate["detail_ru"]
