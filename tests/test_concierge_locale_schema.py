"""Concierge API locale fields."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.schemas import ConciergeRequest  # noqa: E402


def test_concierge_request_accepts_locale_fields():
    req = ConciergeRequest(
        question="Hello",
        ui_locale="de",
        assistant_locale="en",
        visitor_id="v1",
    )
    assert req.ui_locale == "de"
    assert req.assistant_locale == "en"
