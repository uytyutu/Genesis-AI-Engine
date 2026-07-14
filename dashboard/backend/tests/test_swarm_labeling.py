import asyncio
from pathlib import Path

import pytest

from app.integration.business_mode_service import BusinessModeService
from app.integration.engine_ai_service import EngineAIService
from app.integration.finance_service import FinanceService
from app.integration.micro_farm_service import MicroFarmService
from app.integration.opportunity_service import OpportunityService
from app.integration.swarm_bridge import build_swarm_orchestrator, ensure_swarm_importable


@pytest.fixture
def farm_memory(tmp_path: Path) -> Path:
    return tmp_path / "memory"


def _seed(farm_memory: Path) -> None:
    opp = OpportunityService(farm_memory)
    opp.create(
        {
            "source_id": "asset_scan",
            "company_name": "Label Cafe",
            "website_url": "https://cafe.example",
            "status": "new",
            "meta": {
                "issues": ["slow mobile", "no https"],
                "title": "Cafe Berlin",
            },
        }
    )


def test_swarm_importable():
    root = ensure_swarm_importable()
    assert (root / "swarm" / "labeling_worker.py").is_file()


def test_labeling_worker_batch(farm_memory: Path):
    _seed(farm_memory)
    opp = OpportunityService(farm_memory)
    ai = EngineAIService(farm_memory)
    orch = build_swarm_orchestrator(opp, ai, memory_dir=farm_memory)
    batch = orch.run_labeling_swarm(workers=5, concurrency=10)
    assert batch.tasks_done >= 1
    assert batch.earned_eur >= 0.05


def test_farm_tick_uses_swarm(farm_memory: Path):
    _seed(farm_memory)
    farm = MicroFarmService(
        OpportunityService(farm_memory),
        FinanceService(farm_memory),
        business_mode=BusinessModeService(farm_memory),
        memory_dir=farm_memory,
    )
    result = farm.run_tick(workers=5)
    assert result["tasks_done"] >= 1
    assert result["earned_eur"] >= 0.05
