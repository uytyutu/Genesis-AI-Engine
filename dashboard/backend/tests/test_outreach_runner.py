"""Country Desk Start/Stop runner."""

from __future__ import annotations

from pathlib import Path

from app.integration.outreach_runner_service import OutreachRunnerService


def test_runner_start_stop_tick(tmp_path: Path):
    calls = {"refresh": 0, "send": 0}

    def refresh_fn(**kwargs):
        calls["refresh"] += 1
        return {
            "ok": True,
            "message_ru": "hunt ok",
            "city": "Berlin",
            "query": "Zahnarztpraxis",
            "market_code": "DE",
            "drafts": {"created": 2, "drafted": 1},
        }

    def send_fn():
        calls["send"] += 1
        return {"sent": False, "skipped": True, "message_ru": "outreach off"}

    svc = OutreachRunnerService(
        tmp_path,
        refresh_fn=refresh_fn,
        send_next_fn=send_fn,
        interval_fn=lambda: 30,
    )
    st = svc.start()
    assert st["running"] is True
    assert st["interval_sec"] == 30
    tick = svc.tick()
    assert tick["ticked"] is True
    assert calls["refresh"] == 1
    assert tick["session_leads"] == 2
    assert tick["session_drafts"] == 1
    assert tick["session_places_requests"] == 1
    assert tick["search_efficiency_pct"] == 200.0
    stopped = svc.stop()
    assert stopped["running"] is False
    idle = svc.tick()
    assert idle["ticked"] is False
    assert idle.get("reason") == "stopped"


def test_runner_skips_places_when_no_huntable_slot(tmp_path: Path):
    calls = {"refresh": 0}

    def refresh_fn(**kwargs):
        calls["refresh"] += 1
        # No city/query → rotation exhausted; SearchText must not be counted
        return {
            "ok": True,
            "message_ru": "нет свежих слотов",
            "drafts": {"created": 0, "drafted": 0},
        }

    svc = OutreachRunnerService(
        tmp_path,
        refresh_fn=refresh_fn,
        send_next_fn=None,
        interval_fn=lambda: 30,
    )
    svc.start()
    tick = svc.tick()
    assert tick["ticked"] is True
    assert calls["refresh"] == 1
    assert tick["session_places_requests"] == 0
    assert tick["search_efficiency_pct"] is None
    assert "hunt_skip_slots" in (tick.get("actions") or [])


def test_runner_skips_places_when_no_huntable_slot(tmp_path: Path):
    calls = {"refresh": 0}

    def refresh_fn(**kwargs):
        calls["refresh"] += 1
        return {
            "ok": True,
            "message_ru": "нет свежих слотов",
            "drafts": {"created": 0, "drafted": 0},
        }

    svc = OutreachRunnerService(
        tmp_path,
        refresh_fn=refresh_fn,
        send_next_fn=None,
        interval_fn=lambda: 30,
    )
    svc.start()
    tick = svc.tick()
    assert tick["ticked"] is True
    assert calls["refresh"] == 1
    assert tick["session_places_requests"] == 0
    assert tick["search_efficiency_pct"] is None
    assert "hunt_skip_slots" in (tick.get("actions") or [])
