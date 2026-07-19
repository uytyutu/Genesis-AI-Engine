"""Country Desk Start/Stop runner."""

from __future__ import annotations

from pathlib import Path

from app.integration.outreach_runner_service import OutreachRunnerService


def test_runner_start_stop_tick(tmp_path: Path):
    calls = {"refresh": 0, "send": 0}

    def refresh_fn(**kwargs):
        calls["refresh"] += 1
        return {"ok": True, "message_ru": "hunt ok", "drafts": {"created": 2, "drafted": 1}}

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
    stopped = svc.stop()
    assert stopped["running"] is False
    idle = svc.tick()
    assert idle["ticked"] is False
    assert idle.get("reason") == "stopped"
