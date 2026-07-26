"""Forever outreach suppress — survives lead reset."""

from __future__ import annotations

from pathlib import Path

from app.integration.lead_engine_quality_gate import quality_gate_before_send
from app.integration.lead_engine_v2 import LeadEngineV2
from app.integration.outreach_sent_forever import OutreachSentForever


def test_forever_blocks_after_reset(tmp_path: Path):
    forever = OutreachSentForever(tmp_path)
    forever.record_sent(
        email="old@firma.de",
        website_url="https://firma.de",
        source="test",
    )
    eng = LeadEngineV2(tmp_path)
    (tmp_path / "opportunities.jsonl").write_text(
        '{"id":"x","contact":"old@firma.de","outreach_status":"sent"}\n',
        encoding="utf-8",
    )
    out = eng.reset_old_base()
    assert out["ok"] is True
    assert forever.path.is_file()
    blocked, reason = forever.was_sent(email="old@firma.de")
    assert blocked is True
    assert reason == "email_ever_sent"
    assert eng.was_contacted(email="old@firma.de") is True


def test_quality_gate_ever_sent(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GENESIS_MEMORY_DIR", str(tmp_path))
    OutreachSentForever(tmp_path).record_sent(email="repeat@shop.de", source="test")
    row = {
        "id": "n1",
        "contact": "repeat@shop.de",
        "website_url": "https://shop.de",
        "proposed_message": "Hallo",
        "recommended_package_id": "basic",
        "meta": {},
        "site_analysis": {"fetch_ok": True},
    }
    gate = quality_gate_before_send(row, all_rows=[])
    assert gate["ok"] is False
    assert gate["reason"] == "ever_sent"


def test_bootstrap_from_contact_history(tmp_path: Path):
    v2 = tmp_path / "lead_engine_v2"
    v2.mkdir(parents=True)
    (v2 / "contact_history.jsonl").write_text(
        '{"at":"2024-01-01T00:00:00+00:00","domain":"oldbiz.de","email":"ceo@oldbiz.de"}\n',
        encoding="utf-8",
    )
    forever = OutreachSentForever(tmp_path)
    result = forever.bootstrap_from_memory()
    assert result["ok"] is True
    blocked, _ = forever.was_sent(email="ceo@oldbiz.de")
    assert blocked is True
