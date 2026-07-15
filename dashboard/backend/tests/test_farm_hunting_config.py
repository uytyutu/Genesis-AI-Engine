"""Tests for farm hunting defaults and price filter."""

from __future__ import annotations

import json
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


def test_freeze_lists_keeps_ceo_targets(tmp_path: Path):
    path = tmp_path / "global_spider_config.json"
    path.write_text(
        json.dumps(
            {
                "freeze_lists": True,
                "target_mode": "places_only",
                "seed_targets": [],
                "places_queries": ["Autowerkstatt", "Handwerker"],
                "search_city": "Köln",
                "search_lat": 50.9375,
                "search_lng": 6.9603,
            }
        ),
        encoding="utf-8",
    )
    cfg = GlobalSpiderService(tmp_path).load_config()
    assert cfg["seed_targets"] == []
    assert cfg["places_queries"] == ["Autowerkstatt", "Handwerker"]
    assert "сравнение ответов чат-ботов" not in cfg["seed_targets"]
    assert cfg["search_city"] == "Köln"


def test_profitable_niches_cycle_target_city(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "global_spider_config.json"
    path.write_text(
        json.dumps(
            {
                "freeze_lists": True,
                "seed_targets": [],
                "profitable_niches": ["Kfz-Werkstatt", "Dachdecker"],
                "target_city": "Köln",
                "search_radius": 20000,
                "search_lat": 50.9375,
                "search_lng": 6.9603,
                "max_batch": 4,
            }
        ),
        encoding="utf-8",
    )
    spider = GlobalSpiderService(tmp_path)
    seen_queries: list[str] = []
    seen_cities: list[str] = []
    seen_radius: list[int] = []

    def _fake_search(
        self,
        query,
        *,
        region,
        city,
        seen,
        urls,
        batch_limit,
        stats,
        stat_key="query_seeds",
        lat=None,
        lng=None,
        radius_m=25000,
    ):
        seen_queries.append(query)
        seen_cities.append(city)
        seen_radius.append(radius_m)
        u = f"https://{query.replace(' ', '-').lower()}-{len(urls)}.koeln.de"
        if u not in seen and len(urls) < batch_limit:
            seen.add(u)
            urls.append(u)
            stats["places"] = int(stats.get("places") or 0) + 1

    monkeypatch.setattr(GlobalSpiderService, "_places_text_search", _fake_search)
    monkeypatch.setattr(spider._places, "configured", lambda: True)
    urls, stats = spider.discover_candidate_urls(batch_limit=4)
    assert stats.get("target_city") == "Köln"
    assert stats.get("search_radius_m") == 20000
    assert seen_cities and all(c == "Köln" for c in seen_cities)
    assert seen_queries == ["Kfz-Werkstatt", "Dachdecker"]
    assert seen_radius and all(r == 20000 for r in seen_radius)
    assert len(urls) == 2
    assert "Pirna" not in seen_cities


def test_acquisition_worklist_uses_target_city(tmp_path: Path):
    from app.integration.acquisition_studio_service import AcquisitionStudioService
    from app.integration.opportunity_service import OpportunityService

    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "global_spider_config.json").write_text(
        json.dumps(
            {
                "freeze_lists": True,
                "target_city": "Köln",
                "search_radius": 20000,
                "profitable_niches": ["Kfz-Werkstatt", "Dachdecker"],
                "seed_targets": [],
                "places_queries": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    opp = OpportunityService(memory)
    studio = AcquisitionStudioService(opp, sales_service=object())
    wl = studio.daily_worklist()
    assert wl["target_city"] == "Köln"
    assert wl["search_radius"] == 20000
    assert wl["profitable_niches"] == ["Kfz-Werkstatt", "Dachdecker"]
    cities = {c for seg in wl["segments"] for c in seg["cities"]}
    assert cities == {"Köln"}
    assert "Pirna" not in cities


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
