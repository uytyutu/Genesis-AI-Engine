"""Farm Engine v1 — legal digital work OS (no human-microtask bots)."""

from __future__ import annotations

from pathlib import Path

from app.integration.swarm_bridge import ensure_swarm_importable

ensure_swarm_importable()
from swarm.farm_engine_v1 import (
    FIRST_LIVE_EARN_ID,
    FarmEngineV1,
    distribution_model,
    dual_track_strategy,
    factory_model,
    legal_check,
    platform_earn_fit,
    roi_check,
    scan_earn_platforms,
)


def test_legal_rejects_captcha_and_toloka_bot():
    assert legal_check({"kind": "captcha", "tos_automation": "forbidden"})["ok"] is False
    assert (
        legal_check({"kind": "human_microtask_bot", "tos_automation": "forbidden"})["ok"]
        is False
    )


def test_legal_allows_own_api_product():
    assert (
        legal_check(
            {
                "kind": "earn_api_product",
                "tos_automation": "allowed",
                "legal_notes_ru": "merchant",
            }
        )["ok"]
        is True
    )


def test_roi_requires_positive_profit():
    assert roi_check({"est_revenue_eur_per_job": 10, "est_cost_eur_per_job": 1})["ok"] is True
    assert roi_check({"est_revenue_eur_per_job": 1, "est_cost_eur_per_job": 2})["ok"] is False


def test_scan_separates_legal_reject_from_research(tmp_path: Path):
    eng = FarmEngineV1(tmp_path)
    panel = eng.scan()
    assert panel["ok"] is True
    stages = {o["id"]: o["pipeline_stage"] for o in panel["opportunities"]}
    assert stages["reject-captcha-farm"] == "legal_reject"
    assert stages["reject-toloka-performer-bot"] == "legal_reject"
    assert stages["reject-mturk-performer-bot"] == "legal_reject"
    assert stages["reject-clickworker-bot"] == "legal_reject"
    assert stages["earn-own-api-stripe"] == "research"
    assert panel["counts"]["legal_reject"] >= 4


def test_factory_model_os_layers():
    model = factory_model()
    assert model["ok"] is True
    assert model["version"] == "1.2"
    ids = [layer["id"] for layer in model["layers"]]
    assert ids == ["capabilities", "composer", "digital_products", "distribution"]
    assert model["value_chain"][-2:] == ["finance_reality_law", "ledger"]
    assert "операционн" in model["identity_ru"].lower()
    products = next(l for l in model["layers"] if l["id"] == "digital_products")
    assert len(products["items"]) >= 15
    composer = next(l for l in model["layers"] if l["id"] == "composer")
    assert len(composer["fanout"]) >= 2
    assert any(r["id"] == "toloka_performer_bot" for r in model["hard_reject"])
    assert any("спрос" in x.lower() for x in model["cannot_ru"])
    assert "0 €" in model["gap_ru"]


def test_distribution_independent_of_factory():
    dist = distribution_model()
    assert dist["ok"] is True
    assert dist["status"] == "architecture_only"
    assert dist["version"] == "1.1"
    assert len(dist["platform_earn_criteria"]) == 4
    group_ids = [g["id"] for g in dist["groups"]]
    assert group_ids == ["inbound", "marketplace", "partners", "machine_to_machine"]
    assert "Finance Reality" in dist["finance_gate_ru"] or "Hard REAL" in dist["finance_gate_ru"]
    assert platform_earn_fit({})["ok"] is False
    assert (
        platform_earn_fit(
            {
                "automation_officially_allowed": True,
                "has_api": True,
                "pays_providers": True,
                "no_forbidden_human_judgment": True,
            }
        )["ok"]
        is True
    )


def test_dual_track_a_and_b():
    s = dual_track_strategy()
    assert s["first_live_earn_id"] == FIRST_LIVE_EARN_ID == "earn-own-api-stripe"
    ids = [t["id"] for t in s["tracks"]]
    assert ids == ["commercial_now", "farm_scanner"]
    assert "Micro 5" in s["priority_now_ru"]
    assert "RapidAPI" in s["do_not_ru"][0] or any("RapidAPI" in x for x in s["do_not_ru"])
    assert (
        "gap" in s["gap_ru"].lower()
        or "Нет механизма" in s["gap_ru"]
        or "Scanner" in s["gap_ru"]
        or "не создаёт рынок" in s["gap_ru"]
    )
    plats = scan_earn_platforms()
    assert plats["counts"]["hard_reject"] >= 2
    first = next(p for p in plats["platforms"] if p.get("is_first_pick"))
    assert first["id"] == "platform-own-stripe"
    assert first["pipeline_stage"] == "first_connector_candidate"
    rapid = next(p for p in plats["platforms"] if p["id"] == "platform-rapidapi")
    assert rapid["evidence_status"] == "auto_when_armed"
    reject = next(p for p in plats["platforms"] if p["id"] == "platform-toloka-performer")
    assert reject["hard_reject"] is True


def test_register_earn_platform_research(tmp_path: Path):
    eng = FarmEngineV1(tmp_path)
    bad = eng.register_earn_platform_research({"id": "x", "hard_reject": True})
    assert bad["ok"] is False
    ok = eng.register_earn_platform_research(
        {
            "id": "platform-test-hub",
            "title": "Test Hub",
            "has_api": True,
            "pays_providers": True,
            "automation_officially_allowed": True,
            "no_forbidden_human_judgment": True,
        }
    )
    assert ok["ok"] is True
    ids = [p["id"] for p in ok["earn_platforms"]["platforms"]]
    assert "platform-test-hub" in ids


def test_go_requires_legal_and_roi(tmp_path: Path):
    eng = FarmEngineV1(tmp_path)
    bad = eng.decide("reject-captcha-farm", "go")
    assert bad["ok"] is False
    good = eng.decide("earn-own-api-stripe", "go")
    assert good["ok"] is True
    assert "execution_plan" in good
    assert good["execution_plan"]["checklist"]
    scan = eng.scan()
    own = next(o for o in scan["opportunities"] if o["id"] == "earn-own-api-stripe")
    assert own["pipeline_stage"] in {
        "waiting_for_ceo",
        "execution_blocked",
        "production_ready",
        "execution_plan",
    }
    assert own["can_enqueue"] is True
    assert own["execution_plan"]["why_no_eur_ru"]


def test_go_runs_execution_plan_not_just_status(tmp_path: Path):
    eng = FarmEngineV1(tmp_path)
    out = eng.decide("earn-rapidapi-provider", "go")
    assert out["ok"] is True
    plan = out["execution_plan"]
    assert plan["stage"] in {"waiting_for_ceo", "blocked"}
    assert any(c["id"] == "openapi" for c in plan["checklist"])
    assert (tmp_path / "farm_exec_rapidapi_openapi.json").is_file()
    assert out["job"]["mode"] == "execution_plan"


def test_enqueue_plan_only_after_go(tmp_path: Path):
    eng = FarmEngineV1(tmp_path)
    assert eng.enqueue("earn-own-api-stripe")["ok"] is False
    eng.decide("earn-own-api-stripe", "go")
    job = eng.enqueue("earn-own-api-stripe")
    assert job["ok"] is True
    assert job["job"]["mode"] == "execution_plan"
    assert "execution_plan" in job
    q = eng.queue()
    assert q["count"] >= 1


def test_panel_shape(tmp_path: Path):
    panel = FarmEngineV1(tmp_path).panel()
    assert panel["engine"] == "farm_v1"
    assert "Opportunity Scanner" in panel["pipeline_ru"]
    assert panel["ledger"]["ok"] is True
    assert panel["strategy"]["tracks"][0]["id"] == "commercial_now"
    assert panel["earn_platforms"]["ok"] is True


def test_maturity_board_blocks_live_without_confirmed_eur(tmp_path: Path):
    board = FarmEngineV1(tmp_path).maturity_board()
    assert board["ok"] is True
    assert board["live_connector_allowed"] is False
    gates = {g["id"]: g["ok"] for g in board["live_gates"]}
    assert gates["legal"] is True
    assert gates["confirmed_eur"] is False
    assert board["kpi"]["funnel_ru"][-1] == "Confirmed €"
    evr = board["estimate_vs_real_ru"].lower()
    assert "моделирование" in evr or "modeling" in evr or "оценки" in evr
    assert board["factory"]["layers"][0]["id"] == "capabilities"
    assert board["factory"]["layers"][1]["id"] == "composer"
    assert board["distribution"]["status"] == "architecture_only"
    assert board["income_phase"]["is_modeling"] is True
    assert board["income_phase"]["phase"] == "modeling"
    assert "Micro 5" in board["law_ru"] or "Stripe" in board["law_ru"]
    assert board["strategy"]["first_live_earn_id"] == "earn-own-api-stripe"
    assert board["earn_platforms"]["counts"]["first_pick"] >= 1
    blocker = board["commercial_blocker"]
    assert blocker["ok"] is True
    by_id = {c["id"]: c["ok"] for c in blocker["checklist"]}
    assert by_id["live_earn_connector"] is False
    assert by_id["micro_stripe_buyer"] is False
    assert by_id["external_payout_id"] is False
    assert "Toloka" in blocker["why_real_zero_ru"] or "Micro" in blocker["why_real_zero_ru"]
    assert len(blocker["first_live_earn_candidates"]) >= 1
    assert "Micro" in blocker["question_right_ru"]
