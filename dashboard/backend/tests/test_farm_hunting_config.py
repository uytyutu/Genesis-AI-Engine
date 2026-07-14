"""Tests for farm hunting defaults and price filter."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.farm_hunting_defaults import (
    DEFAULT_MIN_TASK_PRICE,
    merge_hunting_config,
    hunting_settings,
)
from app.integration.global_spider_service import GlobalSpiderService
from app.integration.business_mode_service import BusinessModeService
from app.integration.finance_service import FinanceService
from app.integration.micro_farm_service import MicroFarmService
from app.integration.opportunity_service import OpportunityService


def test_merge_hunting_config_adds_defaults():
    cfg = merge_hunting_config({})
    assert cfg["min_task_price"] == DEFAULT_MIN_TASK_PRICE
    assert "сравнение ответов чат-ботов" in cfg["seed_targets"]
    assert "LLM response comparison" in cfg["toloka_task_categories"]
    assert cfg["polling_interval_sec"] == 8


def test_hunting_settings_clamps_polling():
    s = hunting_settings({"min_task_price": 0.02, "polling_interval_sec": 120})
    assert s["polling_interval_sec"] == 60


def test_global_spider_load_merges_config(tmp_path: Path):
    path = tmp_path / "global_spider_config.json"
    path.write_text('{"seed_targets":["https://only.example"],"min_task_price":0.03}', encoding="utf-8")
    spider = GlobalSpiderService(tmp_path)
    cfg = spider.load_config()
    assert cfg["min_task_price"] == 0.03
    assert "https://only.example" in cfg["seed_targets"]
    assert "проверка фактов в текстах" in cfg["seed_targets"]


def test_price_filter_skips_record_verify(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    cfg = memory / "global_spider_config.json"
    cfg.write_text('{"min_task_price":0.02}', encoding="utf-8")
    opp = OpportunityService(memory)
    farm = MicroFarmService(
        opp,
        FinanceService(memory),
        business_mode=BusinessModeService(memory),
        memory_dir=memory,
    )
    opp.create(
        {
            "source_id": "asset_scan",
            "company_name": "Cheap Co",
            "website_url": "https://cheap.example",
            "meta": {
                "farm_data_cleaned": True,
                "classified_niche": "x",
                "farm_verified": False,
            },
        }
    )
    picked = farm._pick_tasks(5)
    assert picked == []
    events = farm._recent_events(5)
    assert any("[Filter] Task too cheap, skipped" in str(e.get("detail")) for e in events)
