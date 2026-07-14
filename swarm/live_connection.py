"""Live connection test — real exchange APIs via vault keys."""

from __future__ import annotations

import logging
from typing import Any, Callable

from swarm.payment_monitor import PaymentMonitor
from swarm.platform_vault import PlatformVault

logger = logging.getLogger("genesis.farm")


def _exchange_label(row: dict[str, Any]) -> str:
    """OK = connected · SKIP = no key · FAIL = key present but API error."""
    if row.get("connected"):
        return "OK"
    if not row.get("configured"):
        return "SKIP"
    return "FAIL"


def test_connection_live(
    *,
    vault: PlatformVault | None = None,
    env_getter: Callable[[str], str] | None = None,
    require_live_mode: bool = True,
) -> dict[str, Any]:
    """Verify Scale/Toloka return real API data — not dry-run simulation."""
    v = vault or PlatformVault(env_getter=env_getter)
    snap = v.snapshot()

    if require_live_mode and snap.get("dry_run"):
        return {
            "ok": False,
            "live_mode": False,
            "message": (
                "FARM_LIVE_MODE=dry_run (или dry) — Live test только в live. "
                "Для тренировки нажми «Боевой тест (dry-run)»."
            ),
            "vault": snap,
            "hint": "battle_test",
        }

    missing = snap.get("missing_for_exchange") or []
    if missing:
        return {
            "ok": False,
            "live_mode": snap.get("farm_mode") == "live",
            "message": f"Не хватает ключей в vault: {', '.join(missing)}",
            "vault": snap,
        }

    remote_missing = snap.get("missing_for_remote") or []
    monitor = PaymentMonitor(v, env_getter=env_getter)
    scan = monitor.scan_all()
    scale_row = scan["scale"]
    toloka_row = scan["toloka"]
    scale_ok = bool(scale_row.get("connected"))
    toloka_ok = bool(toloka_row.get("connected"))
    live_tasks = bool(scan.get("any_live_tasks"))
    scale_label = _exchange_label(scale_row)
    toloka_label = _exchange_label(toloka_row)

    log_line = (
        f"Live connect: scale={scale_label} "
        f"toloka={toloka_label} "
        f"live_tasks={'yes' if live_tasks else 'no'}"
    )
    logger.info(log_line)

    any_exchange_ok = scale_ok or toloka_ok
    ok = any_exchange_ok

    next_steps = [
        "Withdraw на Stripe только вручную в кабинете биржи",
    ]
    if remote_missing:
        next_steps.insert(
            0,
            "FARM_EXECUTION_MODE=remote требует FARM_WORKER_POOL_URL — пока поставь local или добавь VPS",
        )
    if not scale_row.get("configured"):
        next_steps.append("Scale не подключён (SKIP) — для Toloka-only это нормально")
    elif scale_label == "FAIL":
        next_steps.append("Scale ключ задан, но API не принял — Toloka-only режим всё равно OK")

    return {
        "ok": ok,
        "live_mode": True,
        "log_line": log_line,
        "scale": scale_row,
        "toloka": toloka_row,
        "any_live_tasks": live_tasks,
        "remote_execution_ready": not remote_missing,
        "message": (
            "Биржа отдаёт живые данные — не симуляция"
            if ok
            else (
                "Toloka/Scale не ответили — проверь ключ и перезапуск Genesis.exe"
                if not any_exchange_ok
                else "API подключён, но очередь задач пуста — проверь проекты на бирже"
            )
        ),
        "vault": {"farm_mode": snap.get("farm_mode"), "key_source": snap.get("storage")},
        "next": next_steps,
    }
