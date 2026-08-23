"""Multi-market hunt rotation + slot efficiency (Mission 1.1)."""

from __future__ import annotations

from pathlib import Path

from app.integration.outreach_hunt_rotation import HuntRotationCursor, build_hunt_slots
from app.integration.outreach_hunt_slot_memory import (
    is_slot_exhausted,
    record_slot_hunt,
)
from app.integration.outreach_market_config import reload_outreach_markets


def test_hunt_slots_cover_enabled_markets():
    reload_outreach_markets()
    slots = build_hunt_slots()
    codes = {s["market"] for s in slots}
    assert "US" in codes and "DE" in codes and "UA" in codes and "PL" in codes
    assert len(slots) > 50  # hubs × niches


def test_hunt_slots_skip_paused_and_zero_cap():
    reload_outreach_markets()
    slots = build_hunt_slots(
        paused_markets={"DE": {"at": "x"}},
        effective_cap_fn=lambda c: 0 if c == "US" else 50,
    )
    codes = {s["market"] for s in slots}
    assert "DE" not in codes
    assert "US" not in codes
    assert "GB" in codes


def test_hunt_cursor_round_robin(tmp_path: Path):
    reload_outreach_markets()
    cur = HuntRotationCursor(tmp_path)
    seen = [cur.next_slot()["market"] for _ in range(12)]
    # Interleave countries — first N ticks must hit multiple markets, not only US hubs
    assert len(set(seen)) >= 5, seen
    assert seen[0] != seen[1] or seen[1] != seen[2], seen


def test_hunt_cursor_cycles_all_enabled(tmp_path: Path):
    reload_outreach_markets()
    cur = HuntRotationCursor(tmp_path)
    enabled = {
        m["code"]
        for m in __import__(
            "app.integration.outreach_market_config", fromlist=["list_markets"]
        ).list_markets(enabled_only=True)
    }
    seen = set()
    for _ in range(len(enabled) + 2):
        seen.add(cur.next_slot()["market"])
    assert enabled <= seen


def test_zero_yield_slot_skipped_without_research(tmp_path: Path):
    """Mission 1.1: after created=0, same city×niche must not be chosen again."""
    reload_outreach_markets()
    cur = HuntRotationCursor(tmp_path)
    first = cur.next_slot()
    assert first is not None
    market, city, query = first["market"], first["city"], first["query"]
    record_slot_hunt(tmp_path, market=market, city=city, query=query, created=0)
    assert is_slot_exhausted(tmp_path, market=market, city=city, query=query)

    for _ in range(40):
        slot = cur.next_slot()
        assert slot is not None
        assert not (
            slot["market"] == market and slot["city"] == city and slot["query"] == query
        ), slot


def test_exhausted_slot_still_allows_other_markets(tmp_path: Path):
    reload_outreach_markets()
    cur = HuntRotationCursor(tmp_path)
    s0 = cur.next_slot()
    record_slot_hunt(
        tmp_path,
        market=s0["market"],
        city=s0["city"],
        query=s0["query"],
        created=0,
    )
    nxt = cur.next_slot()
    assert nxt is not None
    assert (nxt["market"], nxt["city"], nxt["query"]) != (
        s0["market"],
        s0["city"],
        s0["query"],
    )


def test_archive_stale_pipeline_keeps_enrichment_hides_idle(tmp_path: Path):
    """Mission 1.3: Fresh Start must not bury needs_email / Ready lane."""
    from app.integration.acquisition_studio_service import AcquisitionStudioService
    from app.integration.opportunity_service import OpportunityService

    opp = OpportunityService(tmp_path)
    rows = []
    for name in ("Ready Lane Co", "Needs Email Co", "Idle None", "Already Sent"):
        row = opp.create(
            {
                "source_id": "manual",
                "company_name": name,
                "fit_reason": "test",
                "meta": {},
            }
        )
        rows.append(row)

    rows[0]["outreach_status"] = "pending_approval"
    rows[0]["contact"] = "info@ready-lane.example"
    rows[1]["outreach_status"] = "needs_email"
    rows[1]["website_url"] = "https://needs-email.example"
    rows[2]["outreach_status"] = "none"
    rows[3]["outreach_status"] = "sent"
    rows[3]["status"] = "contacted"
    opp._save_rows(rows)

    svc = AcquisitionStudioService(opp, object())
    cleared = svc.archive_stale_pipeline_for_fresh_run()
    assert cleared["archived"] == 1
    assert cleared.get("kept_pipeline", 0) >= 2
    visible = {v.get("company_name") for v in svc.pipeline_leads(limit=50)}
    assert "Ready Lane Co" in visible
    assert "Needs Email Co" in visible
    assert "Idle None" not in visible


def test_repair_mission13_lifts_fresh_archive_and_healthy_site(tmp_path: Path):
    from app.integration.acquisition_studio_service import AcquisitionStudioService
    from app.integration.lead_engine_premium import WEBSITE_OFFER_INELIGIBLE
    from app.integration.opportunity_service import OpportunityService

    opp = OpportunityService(tmp_path)
    ne = opp.create(
        {
            "source_id": "manual",
            "company_name": "Archived Needs Email",
            "website_url": "https://ne.example",
            "fit_reason": "test",
            "meta": {
                "quality_archive": True,
                "quality_archive_reason": "fresh_multi_market_start",
            },
        }
    )
    ne["outreach_status"] = "needs_email"
    healthy = opp.create(
        {
            "source_id": "manual",
            "company_name": "Legacy Healthy",
            "contact": "info@healthy.example",
            "website_url": "https://healthy.example",
            "fit_reason": "test",
            "meta": {
                "quality_archive": True,
                "quality_archive_reason": "healthy_site",
                "skip_outreach": True,
                "skip_reason": "healthy_site",
            },
        }
    )
    healthy["outreach_status"] = "none"
    opp._save_rows([ne, healthy])

    svc = AcquisitionStudioService(opp, object())
    repaired = svc.repair_mission13_enrichment_queue()
    assert repaired["restored_fresh_archive"] == 1
    assert repaired["migrated_healthy_site_archive"] == 1
    ne2 = opp.get(ne["id"])
    h2 = opp.get(healthy["id"])
    assert not (ne2.get("meta") or {}).get("quality_archive")
    assert not (h2.get("meta") or {}).get("quality_archive")
    assert (h2.get("meta") or {}).get("website_offer") == "rejected"
    assert (h2.get("meta") or {}).get("skip_reason") == WEBSITE_OFFER_INELIGIBLE
    visible = {v.get("company_name") for v in svc.pipeline_leads(limit=50)}
    assert "Archived Needs Email" in visible
    assert "Legacy Healthy" in visible
