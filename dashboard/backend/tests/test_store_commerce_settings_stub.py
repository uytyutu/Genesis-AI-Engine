"""Commerce settings stubs for Store Admin (pre-R3.3)."""

from pathlib import Path

from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService


def test_commerce_settings_stub(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    out = svc.ensure_saved("ord-commerce-1")
    assert out["commerce_ready"] is False
    assert out["settings"]["payments"]["stripe"]["status"] == "not_connected"
    assert out["settings"]["shipping"]["dhl"]["status"] == "not_connected"
    assert out["settings"]["taxes"]["status"] == "not_connected"
    # persisted
    again = svc.get("ord-commerce-1")
    assert again["settings"]["currencies"]["primary"] == "EUR"
