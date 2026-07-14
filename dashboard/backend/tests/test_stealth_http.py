from pathlib import Path

import pytest

from app.integration.stealth_http import (
    StealthHttpClient,
    UnauthorizedOperation,
    external_get,
    requires_stealth_policy,
)
from unittest.mock import patch


def test_requires_stealth_external_site():
    assert requires_stealth_policy("https://example.com/page") is True
    assert requires_stealth_policy("https://api.stripe.com/v1/balance") is False
    assert requires_stealth_policy("https://maps.googleapis.com/maps/api/place/textsearch/json") is False


def test_post_on_external_site_raises_unauthorized(tmp_path: Path):
    client = StealthHttpClient(memory_dir=tmp_path)
    with pytest.raises(UnauthorizedOperation, match="Unauthorized Operation"):
        client.request("POST", "https://example.com/submit")


def test_violation_logged_on_post(tmp_path: Path):
    client = StealthHttpClient(memory_dir=tmp_path)
    with pytest.raises(UnauthorizedOperation):
        client.request("PUT", "https://shop.example.de/cart")
    log_path = tmp_path / "stealth_violations.jsonl"
    assert log_path.is_file()
    text = log_path.read_text(encoding="utf-8")
    assert "Unauthorized Operation" in text
    assert "PUT" in text


def test_user_agent_chrome_120():
    client = StealthHttpClient()
    assert "Chrome/120.0.0.0" in client.browser_headers()["User-Agent"]


def test_external_get_delegates():
    with patch.object(StealthHttpClient, "get") as get_mock:
        get_mock.return_value = object()
        external_get("https://example.com/")
    get_mock.assert_called_once()
