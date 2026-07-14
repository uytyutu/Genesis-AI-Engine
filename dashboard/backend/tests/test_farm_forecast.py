import pytest

from app.integration.swarm_bridge import ensure_swarm_importable


def test_revenue_model_50_nodes():
    ensure_swarm_importable()
    from swarm.revenue_model import forecast_labeling_swarm, full_forecast

    result = forecast_labeling_swarm(nodes=50, hours=10.0)
    assert result["gross_usd"] == 125.0
    assert result["net_usd"] < result["gross_usd"]
    full = full_forecast(labeling_nodes=50)
    assert "disclaimer" in full
    assert len(full["phases"]) == 3


def test_adaptive_arbitrage_labeling_wins():
    ensure_swarm_importable()
    from swarm.adaptive_arbitrage import compare_streams

    result = compare_streams(labeling_eur_per_hour=12.0, node_eur_per_day=0.5)
    assert result["winner"] == "labeling"
    assert result["allocation_labeling_pct"] >= 55


def test_node_monitor_snapshot(tmp_path):
    ensure_swarm_importable()
    from swarm.node_monitor import NodeMonitor

    mon = NodeMonitor(tmp_path, env_getter=lambda k: "10" if k == "FARM_NODE_COUNT" else "0.07")
    snap = mon.snapshot()
    assert snap["effective_nodes"] == 10
    assert snap["projected_eur_per_day"] > 0


def test_battle_test_runs(tmp_path):
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
    result = farm.run_battle_test()
    assert result["ok"] is True
    assert "checks" in result
    assert "forecast" in result
    assert "measured" in result
