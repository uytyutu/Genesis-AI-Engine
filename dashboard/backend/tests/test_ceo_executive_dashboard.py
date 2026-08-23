"""CEO Executive Dashboard aggregates."""

from pathlib import Path

from app.integration.ceo_executive_dashboard import build_ceo_executive_dashboard


def test_ceo_dashboard_shape(tmp_path: Path):
    out = build_ceo_executive_dashboard(
        tmp_path,
        finance={"mrr_eur": 0, "revenue_total_eur": 0},
        include_deployment=True,
    )
    assert out["ok"] is True
    assert out["phase"]["id"] == "D"
    assert out["phase"]["name"] == "Proof"
    assert out["frontend_deployment"]["local_commit"]
    assert out["deployment_inspector"]["id"] == "deployment_inspector"
    assert out["deployment_inspector"]["explanation_ru"]
    assert isinstance(out["deployment_inspector"]["actions"], list)
    assert out["deployment_manager"]["id"] == "deployment_manager"
    assert out["deployment_manager"]["policy"]["production"] == "ovh"
    assert out["deployment_manager"]["explanation_ru"]
    assert len(out["income_contours"]["farms"]) == 3
    assert {f["id"] for f in out["income_contours"]["farms"]} >= {
        "opire_farm",
        "alpha_hunter",
        "sales_farm",
    }
    assert "virtus" in out
    assert "farm" in out
    assert "company" in out
    assert isinstance(out["today_focus"], list)
    assert len(out["today_focus"]) >= 1
    assert out["virtus"]["first_clients"]["goal"] == 5
    assert out["company"]["website_launch"] == "BLOCKED"
    assert out["company"]["ads_allowed"] is False
    assert "golden_website_test" in out["company"]
    ids = {f["id"] for f in out["today_focus"]}
    assert "golden_website_blockers" in ids
    assert out["first_real_euro"]["reached"] is False
    assert out["first_real_euro"]["status"] == "not_reached"
    health = out["dashboard_health"]
    assert health["items"]
    labels = {i["label"] for i in health["items"]}
    assert {"Finance", "Factory", "Country Desk", "Revenue Lab", "Opire", "Awin"} <= labels
    assert out["growth_ladder"]["steps"][0]["id"] == "first_real_euro"
    assert out["growth_ladder"]["steps"][0]["reached"] is False
    wc = out["weekly_constraint"]
    assert wc["label"] == "THIS WEEK"
    assert wc["owner"] == "CEO"
    assert wc["constraint"]
    assert wc["impact"]
    assert wc["action"]
    assert wc["rule_ru"]


def test_ceo_dashboard_defers_deployment_by_default(tmp_path: Path):
    out = build_ceo_executive_dashboard(tmp_path, finance={})
    assert out["deployment_manager"]["status"] == "deferred"
    assert out["deployment_manager"].get("deferred") is True
    assert out["frontend_deployment"]["status"] == "deferred"
    assert out.get("stage") == "core"
    assert out["farm"].get("deferred") is True


def test_ceo_dashboard_full_stage_loads_farm(tmp_path: Path):
    out = build_ceo_executive_dashboard(tmp_path, finance={}, stage="full")
    assert out.get("stage") == "full"
    assert out["farm"].get("deferred") is not True


def test_first_real_euro_reached_from_ledger(tmp_path: Path):
    from swarm.finance_ledger import FinanceLedger
    from swarm.revenue_source import CONFIDENCE_CONFIRMED

    FinanceLedger(tmp_path).append(
        source_id="stripe",
        amount=1.0,
        confidence=CONFIDENCE_CONFIRMED,
        payout_id="po_1",
        description="first euro",
    )
    out = build_ceo_executive_dashboard(tmp_path, finance={})
    assert out["first_real_euro"]["reached"] is True
    assert out["first_real_euro"]["ledger_confirmed_eur"] >= 1.0
    assert out["growth_ladder"]["steps"][0]["reached"] is True
