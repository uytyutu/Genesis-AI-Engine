"""Places daily quota cooldown — pause Hunt instead of hammering Google."""

from datetime import datetime, timezone
from pathlib import Path

from app.integration.places_quota_cooldown import (
    clear_places_quota_cooldown,
    is_places_quota_blocked,
    is_quota_exceeded_message,
    mark_places_quota_exceeded,
    next_pacific_midnight_utc,
    places_quota_status,
)


def test_quota_message_detect():
    assert is_quota_exceeded_message(
        "places_error:Quota exceeded for quota metric 'SearchTextRequest' "
        "and limit 'SearchTextRequest per day' of service 'places.googleapis.com'"
    )
    assert not is_quota_exceeded_message("places_error:REQUEST_DENIED")


def test_mark_and_block(tmp_path: Path):
    assert is_places_quota_blocked(tmp_path) is False
    marked = mark_places_quota_exceeded(tmp_path, detail="Quota exceeded SearchTextRequest")
    assert marked["until"]
    st = places_quota_status(tmp_path)
    assert st["active"] is True
    assert "SearchText" in (st["blocker_ru"] or "") or "квота" in (st["blocker_ru"] or "").lower()
    assert is_places_quota_blocked(tmp_path) is True
    clear_places_quota_cooldown(tmp_path)
    assert is_places_quota_blocked(tmp_path) is False


def test_pacific_midnight_in_future():
    until = next_pacific_midnight_utc(now=datetime(2026, 7, 31, 20, 0, tzinfo=timezone.utc))
    assert until > datetime(2026, 7, 31, 20, 0, tzinfo=timezone.utc)
