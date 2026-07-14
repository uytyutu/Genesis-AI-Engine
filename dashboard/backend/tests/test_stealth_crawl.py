from unittest.mock import MagicMock, patch

import pytest

from app.integration.stealth_crawl_service import (
    STEALTH_USER_AGENT,
    StealthCrawlService,
    stealth_preflight,
)


def test_stealth_blocks_admin_paths():
    svc = StealthCrawlService(min_interval_sec=3.0)
    with pytest.raises(ValueError, match="forbidden_target"):
        svc.assert_read_only_target("https://example.com/wp-admin/")
    with pytest.raises(ValueError, match="forbidden_target"):
        svc.assert_read_only_target("https://example.com/login")


def test_stealth_blocks_write_methods():
    gate = stealth_preflight("https://example.com/", method="POST")
    assert gate.allowed is False
    assert gate.reason == "Unauthorized Operation"
    assert gate.read_only is False


def test_stealth_status_read_only():
    svc = StealthCrawlService()
    status = svc.status()
    assert status["enabled"] is True
    assert status["robots_txt_required"] is True
    assert status["read_only"] is True
    assert "GET" in status["allowed_methods"]
    assert "Chrome" in status["user_agent"]


def test_stealth_user_agent_is_browser_like():
    assert "Mozilla" in STEALTH_USER_AGENT
    assert "Chrome" in STEALTH_USER_AGENT


def test_stealth_robots_disallow_blocks_fetch():
    svc = StealthCrawlService(min_interval_sec=3.0)
    with patch.object(svc, "_robots_allows", return_value=(False, True)):
        gate = svc.preflight("https://example.com/page", skip_throttle=True)
    assert gate.allowed is False
    assert gate.reason == "robots_txt_disallowed"
    assert gate.robots_checked is True


def test_stealth_domain_throttle():
    svc = StealthCrawlService(min_interval_sec=3.0)
    with patch.object(svc, "_robots_allows", return_value=(True, True)):
        with patch("app.integration.stealth_http.time.sleep") as sleep_mock:
            svc.preflight("https://example.com/a", skip_throttle=False)
            svc.preflight("https://example.com/b", skip_throttle=False)
    sleep_mock.assert_called_once()


def test_stealth_fetch_get_read_only():
    svc = StealthCrawlService(min_interval_sec=3.0)
    mock_response = MagicMock()
    mock_response.request.method = "GET"
    with patch.object(svc, "preflight") as preflight_mock:
        preflight_mock.return_value = MagicMock(allowed=True, reason=None)
        with patch("httpx.Client") as client_cls:
            client_cls.return_value.__enter__.return_value.request.return_value = mock_response
            res = svc.fetch_get("https://example.com/")
    assert res is mock_response
    client_cls.return_value.__enter__.return_value.request.assert_called_once()
