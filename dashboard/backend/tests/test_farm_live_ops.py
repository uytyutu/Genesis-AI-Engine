import pytest

from app.integration.swarm_bridge import ensure_swarm_importable


def test_platform_vault_dry_run(monkeypatch):
    ensure_swarm_importable()
    from swarm.platform_vault import PlatformVault

    monkeypatch.delenv("FARM_LIVE_MODE", raising=False)
    monkeypatch.delenv("SCALE_API_KEY", raising=False)
    vault = PlatformVault(env_getter=lambda k: "")
    snap = vault.snapshot()
    assert snap["farm_mode"] == "dry_run"
    assert snap["live_ready"] is False


def test_platform_vault_live_ready(monkeypatch):
    ensure_swarm_importable()
    from swarm.platform_vault import PlatformVault

    env = {
        "FARM_LIVE_MODE": "live",
        "GENESIS_GROQ_API_KEY": "gsk_test_key_123456",
        "SCALE_API_KEY": "live_scale_key_99",
    }
    vault = PlatformVault(env_getter=lambda k: env.get(k, ""))
    snap = vault.snapshot()
    assert snap["live_ready"] is True
    assert snap["farm_mode"] == "live"
    masked = next(p for p in snap["platforms"] if p["env_var"] == "SCALE_API_KEY")
    assert "…" in masked["masked"]


def test_self_healing_disables_low_roi(tmp_path):
    ensure_swarm_importable()
    from swarm.farm_learning import FarmLearningLedger, MIN_OPS_FOR_PRIORITY
    from swarm.node_monitor import NodeMonitor
    from swarm.self_healing import SelfHealingLoop

    ledger = FarmLearningLedger(tmp_path)
    for _ in range(MIN_OPS_FOR_PRIORITY):
        ledger.record(adapter_id="record_verify", pay_eur=0.00001, duration_ms=10000)
    healing = SelfHealingLoop(min_eur_per_hour=0.05)
    result = healing.evaluate(ledger, NodeMonitor(tmp_path))
    assert result["active"] is True
    assert "record_verify" in result["disabled_adapters"]


def test_api_cost_optimizer_picks_groq():
    ensure_swarm_importable()
    from swarm.api_cost_optimizer import ApiCostOptimizer

    opt = ApiCostOptimizer()
    pick = opt.pick_cheapest(opt.provider_chain("simple"), router_task="simple")
    assert pick["provider_id"] in {"groq", "ollama", "gemini"}


def test_prepare_live_endpoint(tmp_path):
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
    prep = farm.prepare_live_mode()
    assert "checklist" in prep
    assert prep["farm_mode"] == "dry_run"
