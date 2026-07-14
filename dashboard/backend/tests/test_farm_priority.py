from pathlib import Path

import pytest

from app.integration.swarm_bridge import ensure_swarm_importable


@pytest.fixture
def swarm_modules():
    ensure_swarm_importable()
    from swarm.farm_learning import FarmLearningLedger, MIN_OPS_FOR_PRIORITY
    from swarm.priority_manager import (
        KnowledgeCache,
        PriorityManager,
        estimate_complexity,
        route_for_task,
    )

    return {
        "ledger": FarmLearningLedger,
        "MIN_OPS": MIN_OPS_FOR_PRIORITY,
        "cache": KnowledgeCache,
        "pm": PriorityManager,
        "estimate": estimate_complexity,
        "route": route_for_task,
    }


def test_complexity_routes_simple_vs_complex(swarm_modules):
    simple = swarm_modules["estimate"](adapter_id="data_clean", raw_text="short")
    complex_ = swarm_modules["estimate"](adapter_id="text_classify", raw_text="x" * 1200)
    assert simple == "simple"
    assert complex_ == "complex"

    flash = swarm_modules["route"](complexity="simple", adapter_id="ai_labeling")
    pro = swarm_modules["route"](complexity="complex", adapter_id="text_classify")
    assert flash["model_tier"] == "flash"
    assert flash["router_task"] == "simple"
    assert pro["model_tier"] == "pro"
    assert pro["router_task"] == "document_analysis"


def test_knowledge_cache_hit(swarm_modules, tmp_path: Path):
    cache = swarm_modules["cache"](tmp_path)
    fp = cache.fingerprint(raw_text="same text", company="Shop", url="https://a.com")
    labels = {"niche_tags": ["retail"], "quality_score": 0.8, "source": "llm"}
    cache.put(fp, labels)
    hit = cache.get(fp)
    assert hit is not None
    assert hit["niche_tags"] == ["retail"]


def test_learning_investor_mode_after_threshold(swarm_modules, tmp_path: Path):
    ledger = swarm_modules["ledger"](tmp_path)
    for _ in range(swarm_modules["MIN_OPS"]):
        ledger.record(adapter_id="ai_labeling", pay_eur=0.05, llm_cost_eur=0.001, duration_ms=50)
        ledger.record(adapter_id="data_clean", pay_eur=0.02, llm_cost_eur=0.0, duration_ms=200)
    snap = ledger.snapshot()
    assert snap["investor_mode"] is True
    order = ledger.recommend_order(("ai_labeling", "data_clean", "text_classify"))
    assert order[0] == "ai_labeling"


def test_priority_manager_snapshot(swarm_modules, tmp_path: Path):
    pm = swarm_modules["pm"](tmp_path)
    snap = pm.snapshot()
    assert snap["pipeline_parallelism"] is True
    assert "learning" in snap
    assert snap["cache"]["max_entries"] == 500


def test_farm_dashboard_exposes_priority_manager(tmp_path: Path):
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
    dash = farm.dashboard("Test")
    assert "priority_manager" in dash
    assert dash["priority_manager"]["pipeline_parallelism"] is True
