import json
from pathlib import Path

import pytest

from app.integration.business_mode_service import BusinessModeService
from app.integration.finance_service import FinanceService
from app.integration.micro_farm_service import MicroFarmService
from app.integration.opportunity_service import OpportunityService


@pytest.fixture
def farm_memory(tmp_path: Path) -> Path:
    return tmp_path / "memory"


def _make_farm(memory: Path) -> MicroFarmService:
    opp = OpportunityService(memory)
    fin = FinanceService(memory)
    bm = BusinessModeService(memory)
    return MicroFarmService(opp, fin, business_mode=bm, memory_dir=memory)


def _seed_opportunity(memory: Path) -> str:
    opp = OpportunityService(memory)
    row = opp.create(
        {
            "source_id": "asset_scan",
            "company_name": "Test Shop",
            "website_url": "https://example.com",
            "status": "new",
            "meta": {"issues": [" slow ", "", "no https"]},
        }
    )
    return str(row["id"])


def test_farm_dashboard_defaults(farm_memory: Path):
    farm = _make_farm(farm_memory)
    dash = farm.dashboard("Test")
    assert dash["mode"] == "micro_farm"
    assert dash["running"] is False
    assert dash["workers_target"] == 10
    assert len(dash["combiners"]) == 4
    assert dash["primary_combiner"] == "ai_labeling"
    assert len(dash["platforms"]) >= 8
    assert dash["platforms"][0]["connected"] is True


def test_farm_tick_earns_on_data_clean(farm_memory: Path):
    _seed_opportunity(farm_memory)
    farm = _make_farm(farm_memory)
    result = farm.run_tick(workers=5)
    assert result["tasks_done"] >= 1
    assert result["earned_eur"] >= 0.02
    state = farm._load_state()
    assert state["total_earned_eur"] >= 0.02


def test_farm_start_stop(farm_memory: Path):
    farm = _make_farm(farm_memory)
    start = farm.start_swarm(workers=3)
    assert start["ok"] is True
    assert farm._load_state()["running"] is True
    stop = farm.stop_swarm()
    assert stop["running"] is False
