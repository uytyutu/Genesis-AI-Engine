"""Income Sources + Tool Belt — money markets, honest capabilities."""

from __future__ import annotations

from pathlib import Path

from swarm.alpha_hunter_income_layer import (
    MONEY_HUNTER_CATEGORIES,
    IncomeSourcesStore,
    capability_registry_snapshot,
    gap_report_for_opportunity,
)
from swarm.alpha_hunter_v1 import AlphaHunterLab


class _Mem:
    def __init__(self, root: Path) -> None:
        self.root = root


def test_five_money_hunter_categories():
    ids = {c["id"] for c in MONEY_HUNTER_CATEGORIES}
    assert ids == {
        "paid_work",
        "money_program",
        "marketplace",
        "demand",
        "new_market",
    }


def test_income_sources_scan_message(tmp_path: Path):
    store = IncomeSourcesStore(tmp_path)
    out = store.scan_active_sources(bank_eur=20.0)
    assert out["ok"] is True
    assert out["spend_eur"] == 0.0
    assert out["checked"] >= 1
    assert "площадок" in (out["message_ru"] or "")
    assert "возможност" in (out["message_ru"] or "").lower() or "0" in out["message_ru"]


def test_capability_registry_honest_gaps():
    snap = capability_registry_snapshot()
    assert snap["north_star_ru"]
    assert snap["counts"]["total"] >= 10
    assert "checklist" in snap
    # Calendar intentionally missing
    cal = next(c for c in snap["checklist"] if c["id"] == "calendar")
    assert cal["ok"] is False


def test_gap_report_says_missing_tool():
    # Force path: paid_work needs browser — if playwright missing, report it
    gaps = gap_report_for_opportunity(category_id="paid_work")
    assert "required" in gaps
    assert gaps["can_prepare_only"] is True
    # If browser missing, message must be explicit
    for m in gaps.get("missing") or []:
        assert "нужен инструмент" in m["message_ru"].lower() or "нет" in m["message_ru"].lower()


def test_lab_scan_income_sources_sets_analysis_ready(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    out = lab.scan_income_sources(bank_eur=20.0)
    assert out["ok"] is True
    assert out.get("adapter_cycle") is True
    assert lab._load_lab()["analysis_ready"] is True
    panel = lab.panel()
    assert panel["income_layer"]["income_sources"]["total"] >= 10
    assert panel["income_layer"]["tool_belt"]["counts"]["total"] >= 10


def test_toggle_income_source(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    r = lab.set_income_source("upwork", active=False)
    assert r["ok"] is True
    view = lab.income_sources_panel()["income_sources"]
    up = next(i for i in view["items"] if i["id"] == "upwork")
    assert up["active"] is False


def test_adapter_sdk_naming_and_passport():
    from swarm.alpha_hunter_adapter_sdk import (
        NO_OPPORTUNITY,
        RapidAPIAdapter,
        discover_all_registered,
        list_adapters,
    )

    passport = RapidAPIAdapter().passport()
    assert passport["name"] == "RapidAPI"
    assert "has_api" in passport["questions"]
    assert "needs_browser" in passport["questions"]
    adapters = list_adapters()
    assert len(adapters) >= 4
    dig = discover_all_registered()
    assert "Opportunity Discovery Engine" in dig["engine"]
    # Without RapidAPI key → NO_OPPORTUNITY, not a fake card
    rapid = RapidAPIAdapter().discover()
    assert rapid.status == NO_OPPORTUNITY
    assert rapid.opportunities == []
