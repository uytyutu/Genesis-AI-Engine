import logging

import pytest

from app.integration.swarm_bridge import ensure_swarm_importable


def test_dry_run_log_line():
    ensure_swarm_importable()
    from swarm.dry_run import format_log_line, potential_profit_eur

    assert potential_profit_eur(adapter_id="ai_labeling", llm_cost_eur=0.0) == 0.15
    assert format_log_line(0.15) == "[DRY RUN] Potential profit: €0.15"


def test_dry_run_logs_to_console(caplog):
    ensure_swarm_importable()
    from swarm.dry_run import log_potential_profit

    caplog.set_level(logging.INFO, logger="genesis.farm")
    entry = log_potential_profit(adapter_id="ai_labeling", task_id="t1", streak=1)
    assert "[DRY RUN] Potential profit: €0.15" in entry["log_line"]
    assert any("[DRY RUN] Potential profit: €0.15" in r.message for r in caplog.records)


def test_dry_run_milestone_at_100(caplog):
    ensure_swarm_importable()
    from swarm.dry_run import MILESTONE_STREAK, log_potential_profit

    caplog.set_level(logging.INFO, logger="genesis.farm")
    entry = log_potential_profit(adapter_id="ai_labeling", task_id="t100", streak=MILESTONE_STREAK)
    assert entry["milestone_reached"] is True
    assert any("Milestone 100" in r.message for r in caplog.records)


def test_dry_run_streak_in_farm(tmp_path):
    from app.integration.business_mode_service import BusinessModeService
    from app.integration.finance_service import FinanceService
    from app.integration.micro_farm_service import MicroFarmService
    from app.integration.opportunity_service import OpportunityService

    memory = tmp_path / "memory"
    opp = OpportunityService(memory)
    opp.create(
        {
            "source_id": "asset_scan",
            "company_name": "Dry Shop",
            "website_url": "https://example.com",
            "status": "new",
            "meta": {"issues": ["slow site", "no mobile"], "swarm_labeled": False},
        }
    )
    farm = MicroFarmService(
        opp,
        FinanceService(memory),
        business_mode=BusinessModeService(memory),
        memory_dir=memory,
    )
    status_before = farm.dry_run_status()
    assert status_before["active"] is True
    assert status_before["execution_mode"] == "local"
    farm.run_tick(workers=3)
    state = farm._load_state()
    assert int(state.get("dry_run_streak") or 0) >= 1
    assert float(state.get("dry_run_total_potential_eur") or 0) > 0


def test_dry_run_forces_local_not_remote(tmp_path, monkeypatch):
    monkeypatch.setenv("FARM_EXECUTION_MODE", "remote")
    monkeypatch.setenv("FARM_WORKER_POOL_URL", "http://fake-pool:8100")
    monkeypatch.setenv("FARM_LIVE_MODE", "dry_run")

    from app.integration.business_mode_service import BusinessModeService
    from app.integration.finance_service import FinanceService
    from app.integration.micro_farm_service import MicroFarmService
    from app.integration.opportunity_service import OpportunityService

    memory = tmp_path / "memory"
    farm = MicroFarmService(
        OpportunityService(memory),
        FinanceService(memory),
        business_mode=BusinessModeService(memory),
        memory_dir=memory,
    )
    tick = farm.run_tick(workers=1)
    assert tick.get("execution", {}).get("target") == "local"
