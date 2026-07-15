"""DSGVO lead phone retention purge."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.integration.lead_retention_service import purge_stale_lead_phones, strip_phone_from_text


def test_strip_phone_from_text():
    text = "info@test.de +49 171 1234567"
    cleaned, changed = strip_phone_from_text(text)
    assert changed is True
    assert "+49" not in cleaned
    assert "info@test.de" in cleaned


def test_purge_stale_lead_phones(tmp_path: Path):
    old = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    row = {
        "id": "opp-old",
        "contact": "+49 171 9998888 info@lead.de",
        "notes": "Телефон: +49 30 111222",
        "updated_at": old,
        "meta": {"phone": "+49 171 9998888"},
    }
    path = tmp_path / "opportunities.jsonl"
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    result = purge_stale_lead_phones(tmp_path, max_age_days=90, dry_run=False)
    assert result["purged_rows"] == 1

    saved = json.loads(path.read_text(encoding="utf-8").strip())
    assert "+49" not in saved.get("contact", "")
    assert saved["meta"].get("pii_phone_purged_at")
    assert "phone" not in saved["meta"]


def test_purge_skips_recent_leads(tmp_path: Path):
    recent = datetime.now(timezone.utc).isoformat()
    row = {
        "id": "opp-new",
        "contact": "+49 171 555",
        "updated_at": recent,
    }
    path = tmp_path / "opportunities.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    result = purge_stale_lead_phones(tmp_path, max_age_days=90)
    assert result["purged_rows"] == 0
    saved = json.loads(path.read_text(encoding="utf-8").strip())
    assert "+49" in saved["contact"]
