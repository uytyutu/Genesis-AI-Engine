"""Multi-market hunt rotation + fresh pipeline archive."""

from __future__ import annotations

from pathlib import Path

from app.integration.outreach_hunt_rotation import HuntRotationCursor, build_hunt_slots
from app.integration.outreach_market_config import reload_outreach_markets


def test_hunt_slots_cover_enabled_markets():
    reload_outreach_markets()
    slots = build_hunt_slots()
    codes = {s["market"] for s in slots}
    assert "US" in codes and "DE" in codes and "UA" in codes and "PL" in codes
    assert "NZ" not in codes  # phase 2 disabled
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
    enabled = {m["code"] for m in __import__(
        "app.integration.outreach_market_config", fromlist=["list_markets"]
    ).list_markets(enabled_only=True)}
    seen = set()
    for _ in range(len(enabled) + 2):
        seen.add(cur.next_slot()["market"])
    assert enabled <= seen


def test_archive_stale_pipeline_hides_old_drafts(tmp_path: Path):
    from app.integration.acquisition_studio_service import AcquisitionStudioService
    from app.integration.opportunity_service import OpportunityService

    opp = OpportunityService(tmp_path)
    rows = []
    for i, name in enumerate(("Old Köln Garage", "Old Draft 2", "Already Sent")):
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
    rows[1]["outreach_status"] = "none"
    rows[2]["outreach_status"] = "sent"
    rows[2]["status"] = "contacted"
    opp._save_rows(rows)

    svc = AcquisitionStudioService(opp, object())
    cleared = svc.archive_stale_pipeline_for_fresh_run()
    assert cleared["archived"] == 2
    visible = {v.get("company_name") for v in svc.pipeline_leads(limit=50)}
    assert "Old Köln Garage" not in visible
    assert "Old Draft 2" not in visible
