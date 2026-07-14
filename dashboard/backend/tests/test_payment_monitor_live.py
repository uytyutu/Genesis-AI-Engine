from unittest.mock import MagicMock, patch

import pytest

from app.integration.swarm_bridge import ensure_swarm_importable


def test_payment_monitor_uses_vault_not_hardcoded(monkeypatch):
    ensure_swarm_importable()
    from swarm.payment_monitor import PaymentMonitor
    from swarm.platform_vault import PlatformVault

    env = {"SCALE_API_KEY": "live_test_scale", "TOLOKA_API_TOKEN": ""}
    vault = PlatformVault(env_getter=lambda k: env.get(k, ""))

    with patch("swarm.payment_monitor.fetch_scale_balance") as mock_bal:
        with patch("swarm.payment_monitor.fetch_scale_live_tasks") as mock_tasks:
            mock_bal.return_value = {"ok": True, "balance_usd": 12.5}
            mock_tasks.return_value = {"ok": True, "live_tasks": True, "count": 2}
            scan = PaymentMonitor(vault).scan_scale()

    mock_bal.assert_called_once_with(api_key="live_test_scale")
    assert scan["balance_usd"] == 12.5
    assert scan["live_tasks"] is True


def test_payout_notifier_threshold_alert(tmp_path):
    ensure_swarm_importable()
    from swarm.payout_notifier import PayoutNotifier

    notifier = PayoutNotifier(tmp_path, threshold_usd=10.0)
    result = notifier.evaluate(
        {
            "scale": {"balance_usd": 15.0, "platform": "scale_ai"},
            "toloka": {"balance_usd": 3.0, "platform": "toloka"},
        }
    )
    assert result["has_withdraw_ready"] is True
    assert result["pending_alerts"][0]["platform"] == "scale"
    assert result["auto_payout"] is False


def test_connection_live_blocks_dry_run():
    ensure_swarm_importable()
    from swarm.live_connection import test_connection_live
    from swarm.platform_vault import PlatformVault

    vault = PlatformVault(env_getter=lambda k: "dry_run" if k == "FARM_LIVE_MODE" else "")
    result = test_connection_live(vault=vault, require_live_mode=True)
    assert result["ok"] is False
    assert "dry_run" in result["message"]


def test_connection_live_success_mocked():
    ensure_swarm_importable()
    from swarm.live_connection import test_connection_live
    from swarm.platform_vault import PlatformVault

    env = {
        "FARM_LIVE_MODE": "live",
        "GENESIS_GROQ_API_KEY": "gsk_x",
        "SCALE_API_KEY": "live_scale",
    }
    vault = PlatformVault(env_getter=lambda k: env.get(k, ""))

    mock_scan = {
        "scale": {"connected": True, "live_tasks": True, "balance_usd": 5.0},
        "toloka": {"connected": False, "live_tasks": False},
        "any_live_tasks": True,
    }
    with patch("swarm.live_connection.PaymentMonitor") as MockMon:
        MockMon.return_value.scan_all.return_value = mock_scan
        result = test_connection_live(vault=vault)

    assert result["ok"] is True
    assert "Live connect" in result["log_line"]
    assert "scale=OK" in result["log_line"]


def test_connection_live_remote_pool_not_required_for_exchange():
    ensure_swarm_importable()
    from swarm.live_connection import test_connection_live
    from swarm.platform_vault import PlatformVault

    env = {
        "FARM_LIVE_MODE": "live",
        "FARM_EXECUTION_MODE": "remote",
        "GENESIS_GROQ_API_KEY": "gsk_x",
        "TOLOKA_API_TOKEN": "tok",
    }
    vault = PlatformVault(env_getter=lambda k: env.get(k, ""))

    mock_scan = {
        "scale": {"connected": False, "live_tasks": False},
        "toloka": {"connected": True, "live_tasks": True, "task_count": 2},
        "any_live_tasks": True,
    }
    with patch("swarm.live_connection.PaymentMonitor") as MockMon:
        MockMon.return_value.scan_all.return_value = mock_scan
        result = test_connection_live(vault=vault)

    assert result["ok"] is True
    assert result["remote_execution_ready"] is False
    assert "FARM_WORKER_POOL_URL" in (result.get("next") or [""])[0]


def test_farm_test_connection_live_endpoint(tmp_path):
    from app.integration.business_mode_service import BusinessModeService
    from app.integration.finance_service import FinanceService
    from app.integration.micro_farm_service import MicroFarmService
    from app.integration.opportunity_service import OpportunityService

    memory = tmp_path / "memory"
    farm = MicroFarmService(
        OpportunityService(memory),
        FinanceService(memory),
        business_mode=BusinessModeService(memory),
        memory_dir=memory,
    )
    result = farm.run_test_connection_live()
    assert "ok" in result
    assert farm._load_state().get("last_live_connection_test")
