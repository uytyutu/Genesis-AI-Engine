"""Factual capability audit of farm revenue / platform sources.

Rule: only what Virtus Core code implements today — not marketing, not ToS hopes.
"""

from __future__ import annotations

from typing import Any

YES = "yes"
NO = "no"
PARTIAL = "partial"
STUB = "stub"
NA = "n/a"


def audit_sources() -> list[dict[str, Any]]:
    """Return one row per connected or registered source — facts only."""
    return [
        _internal_queue(),
        _toloka_pipeline(),
        _scale_ai(),
        _stripe_b2b(),
        _registry_stub("appen", "Appen Connect", "APPEN_API_KEY"),
        _registry_stub("mturk", "Amazon MTurk", "MTURK_AWS_SECRET_ACCESS_KEY"),
        _registry_stub(
            "hive_farm",
            "Hive (farm registry)",
            "HIVE_API_KEY",
            extra_note=(
                "Hive exists as content/LLM provider under dashboard/backend/app/providers/hive — "
                "not a farm payout adapter. Registry row is a stub."
            ),
        ),
        _registry_stub("dataloop", "Dataloop", "DATALOOP_API_KEY"),
        _registry_stub("labelbox", "Labelbox", "LABELBOX_API_KEY"),
        _cost_only(
            "kimi",
            "Kimi / Moonshot",
            "GENESIS_KIMI_API_KEY",
            "LLM cost provider (engine_ai / claude_engine). Not a revenue source.",
        ),
        _cost_only(
            "groq",
            "Groq",
            "GENESIS_GROQ_API_KEY",
            "LLM cost for labeling workers. Not a revenue source.",
        ),
    ]


def audit_report() -> dict[str, Any]:
    rows = audit_sources()
    implemented = [r for r in rows if r.get("adapter_implemented")]
    stubs = [r for r in rows if r.get("registry_only")]
    earnable = [r for r in rows if r.get("can_earn_via_virtus") is True]
    return {
        "title": "Farm / revenue source capability audit",
        "rule": (
            "Только факты из кода Virtus Core + endpoints, которые код реально вызывает."
        ),
        "columns": [
            "platform",
            "role",
            "fetch_tasks",
            "submit_results",
            "balance_api",
            "payout_history",
            "webhook",
            "auto_withdraw",
            "manual_withdraw",
            "can_earn_via_virtus",
        ],
        "sources": rows,
        "summary": {
            "adapter_implemented": len(implemented),
            "registry_stubs": len(stubs),
            "can_earn_via_virtus_today": len(earnable),
            "earnable_ids": [r["id"] for r in earnable],
            "critical_finding_ru": (
                "Toloka Pipeline и Scale API в коде — роль заказчика (requester/customer): "
                "отправка датасетов / чтение задач. Это не API заработка performer. "
                "Реальный доход B2B сегодня — Stripe webhook. "
                "Локальная ферма пишет только estimate_eur."
            ),
        },
    }


def _base(
    *,
    source_id: str,
    name: str,
    role: str,
    fetch_tasks: str,
    submit_results: str,
    balance_api: str,
    payout_history: str,
    webhook: str,
    auto_withdraw: str,
    manual_withdraw: str,
    can_earn_via_virtus: bool,
    adapter_implemented: bool,
    registry_only: bool,
    evidence: list[str],
    note_ru: str,
    env_var: str | None = None,
) -> dict[str, Any]:
    return {
        "id": source_id,
        "platform": name,
        "role": role,
        "env_var": env_var,
        "fetch_tasks": fetch_tasks,
        "submit_results": submit_results,
        "balance_api": balance_api,
        "payout_history": payout_history,
        "webhook": webhook,
        "auto_withdraw": auto_withdraw,
        "manual_withdraw": manual_withdraw,
        "can_earn_via_virtus": can_earn_via_virtus,
        "adapter_implemented": adapter_implemented,
        "registry_only": registry_only,
        "evidence": evidence,
        "note_ru": note_ru,
    }


def _internal_queue() -> dict[str, Any]:
    return _base(
        source_id="internal_queue",
        name="Virtus Core (внутренняя очередь)",
        role="local_simulator",
        fetch_tasks=YES,
        submit_results=YES,
        balance_api=NO,
        payout_history=NO,
        webhook=NO,
        auto_withdraw=NO,
        manual_withdraw=NA,
        can_earn_via_virtus=False,
        adapter_implemented=True,
        registry_only=False,
        evidence=[
            "swarm/task_source.py::InternalOpportunitySource",
            "micro_farm_service._ADAPTER_PAY_EUR (local estimate table)",
            "farm_lifecycle_ru: reward_estimate / cycle_accounted",
        ],
        note_ru=(
            "Локальные комбайны + таблица _ADAPTER_PAY_EUR. Это оценка, не выплата. "
            "К выводу на Stripe недоступно."
        ),
    )


def _toloka_pipeline() -> dict[str, Any]:
    return _base(
        source_id="toloka",
        name="Toloka Pipeline API v2",
        role="requester",
        fetch_tasks=PARTIAL,
        submit_results=YES,
        balance_api=NO,
        payout_history=NO,
        webhook=NO,
        auto_withdraw=NO,
        manual_withdraw=YES,
        can_earn_via_virtus=False,
        adapter_implemented=True,
        registry_only=False,
        env_var="TOLOKA_API_TOKEN",
        evidence=[
            "swarm/adapter_toloka.py — projects/datasets/items/pipelines/runs",
            "swarm/adapter_toloka.py::fetch_balance — no wallet endpoint",
            "swarm/toloka_submit.py — push labels as requester dataset items",
            "platform_registry: performer wallet = separate toloka.ai account",
        ],
        note_ru=(
            "Pipeline API как заказчик. Баланс/выплаты в API нет. "
            "Заработок performer в Virtus не подключён."
        ),
    )


def _scale_ai() -> dict[str, Any]:
    return _base(
        source_id="scale_ai",
        name="Scale AI",
        role="customer_requester",
        fetch_tasks=PARTIAL,
        submit_results=NO,
        balance_api=PARTIAL,
        payout_history=NO,
        webhook=NO,
        auto_withdraw=NO,
        manual_withdraw=YES,
        can_earn_via_virtus=False,
        adapter_implemented=True,
        registry_only=False,
        env_var="SCALE_API_KEY",
        evidence=[
            "swarm/adapter_scale_ai.py::check_connection — GET /v1/tasks",
            "swarm/adapter_scale_ai.py::fetch_scale_live_tasks",
            "swarm/adapter_scale_ai.py::fetch_scale_balance — probe paths; often manual fallback",
            "No Scale submit / webhook / withdraw in swarm/",
        ],
        note_ru=(
            "Probe + список задач. Submit и автовывод отсутствуют. "
            "Баланс — best-effort; иначе ручной кабинет."
        ),
    )


def _stripe_b2b() -> dict[str, Any]:
    return _base(
        source_id="stripe",
        name="Stripe (B2B / orders)",
        role="payment_processor",
        fetch_tasks=NA,
        submit_results=NA,
        balance_api=YES,
        payout_history=YES,
        webhook=YES,
        auto_withdraw=PARTIAL,
        manual_withdraw=YES,
        can_earn_via_virtus=True,
        adapter_implemented=True,
        registry_only=False,
        env_var="STRIPE_SECRET_KEY",
        evidence=[
            "dashboard/backend/app/services/finance_center.py::handle_stripe_webhook_event",
            "payment settlement / apply_stripe_checkout_payment",
        ],
        note_ru=(
            "Подтверждённый денежный вход: клиент → Stripe webhook → settlement. "
            "Вывод на банк — через Stripe (настройка аккаунта / Dashboard)."
        ),
    )


def _registry_stub(
    source_id: str,
    name: str,
    env_var: str,
    *,
    extra_note: str = "",
) -> dict[str, Any]:
    note = (
        f"Только строка в swarm/platform_registry.py. Адаптера нет. "
        "Ключ в .env ничего не включает."
    )
    if extra_note:
        note = f"{note} {extra_note}"
    return _base(
        source_id=source_id,
        name=name,
        role="unwired",
        fetch_tasks=STUB,
        submit_results=STUB,
        balance_api=STUB,
        payout_history=STUB,
        webhook=STUB,
        auto_withdraw=STUB,
        manual_withdraw=STUB,
        can_earn_via_virtus=False,
        adapter_implemented=False,
        registry_only=True,
        env_var=env_var,
        evidence=[f"swarm/platform_registry.py id={source_id}"],
        note_ru=note,
    )


def _cost_only(source_id: str, name: str, env_var: str, note_ru: str) -> dict[str, Any]:
    return _base(
        source_id=source_id,
        name=name,
        role="cost_provider",
        fetch_tasks=NA,
        submit_results=NA,
        balance_api=NO,
        payout_history=NO,
        webhook=NO,
        auto_withdraw=NA,
        manual_withdraw=NA,
        can_earn_via_virtus=False,
        adapter_implemented=True,
        registry_only=False,
        env_var=env_var,
        evidence=[f"env {env_var} used as LLM/API cost, not farm payout"],
        note_ru=note_ru,
    )
