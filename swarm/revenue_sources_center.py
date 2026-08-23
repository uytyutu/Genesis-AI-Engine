"""Revenue Sources v0 — income control center (no web discovery).

Bound by Finance Reality Law (swarm/finance_reality_law.py).
Owner Gate: Virtus never creates accounts or accepts ToS for the CEO.
"""

from __future__ import annotations

from typing import Any

from swarm.finance_reality_law import law_manifest, trial_passed
from swarm.revenue_source import (
    CONFIDENCE_BOOKED,
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_ESTIMATED,
    CONFIDENCE_PENDING,
    CONFIDENCE_SIMULATED,
    confidence_label,
)

# Display statuses for the control center
STATUS_ACTIVE = "active"
STATUS_CANDIDATE = "candidate"
STATUS_UNSUPPORTED = "unsupported"
STATUS_COST = "cost"
STATUS_STUB = "stub"

STATUS_LABEL_RU = {
    STATUS_ACTIVE: "Active",
    STATUS_CANDIDATE: "Candidate",
    STATUS_UNSUPPORTED: "Unsupported",
    STATUS_COST: "Cost only",
    STATUS_STUB: "Not wired",
}

STATUS_EMOJI = {
    STATUS_ACTIVE: "🟢",
    STATUS_CANDIDATE: "🟡",
    STATUS_UNSUPPORTED: "🔴",
    STATUS_COST: "⚪",
    STATUS_STUB: "🔴",
}

# Extra display confidences for center (not bookkeeping ladder)
CONF_NOT_CONNECTED = "NOT_CONNECTED"
CONF_KEYS_PRESENT = "KEYS_PRESENT"
CONF_UNSUPPORTED = "UNSUPPORTED"
CONF_COST = "COST"


def build_revenue_sources_center(
    *,
    stripe_income_eur: float = 0.0,
    stripe_connected: bool = False,
    stripe_webhook: bool = False,
    awin_connected: bool = False,
    digistore_connected: bool = False,
    ledger_real_eur: float = 0.0,
    farm_estimate_eur: float = 0.0,
    stripe_confirmed_ops: int = 0,
    stripe_active_days: int = 0,
    keys_probe: dict[str, Any] | None = None,
    opire: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Curated catalog — candidates added manually, never auto-scraped."""
    law = law_manifest()
    stripe_amt = round(float(stripe_income_eur or 0) + float(ledger_real_eur or 0), 2)
    if stripe_income_eur > 0:
        stripe_amt = round(float(stripe_income_eur), 2)

    stripe_trial_ok = trial_passed(
        confirmed_ops=stripe_confirmed_ops,
        active_days=stripe_active_days,
    )
    # Proven inflows → Active. Key alone ≠ Active (Reality over Simulation).
    stripe_active = stripe_amt > 0 or (stripe_connected and stripe_trial_ok)

    if stripe_amt > 0:
        stripe_stage = "PAID"
        stripe_why_not = "Доход подтверждён (есть платежи)."
        stripe_next = "Сверять Ledger / Stripe Dashboard."
    elif stripe_connected and stripe_webhook:
        stripe_stage = "WAITING_FIRST_PAYMENT"
        stripe_why_not = "Нет оплаченных заказов в Ledger (ключ ≠ доход)."
        stripe_next = "Найти первого клиента → Checkout → webhook → Ledger."
    elif stripe_connected:
        stripe_stage = "KEYS_PRESENT"
        stripe_why_not = "Нет STRIPE_WEBHOOK_SECRET — оплаты могут не попасть в Ledger."
        stripe_next = "Добавить STRIPE_WEBHOOK_SECRET → перезапуск → тест-оплата."
    else:
        stripe_stage = "NOT_CONNECTED"
        stripe_why_not = "Нет STRIPE_SECRET_KEY."
        stripe_next = "Добавь STRIPE_SECRET_KEY в .env.local → перезапуск Genesis."

    sources = [
        _row(
            source_id="stripe",
            name="Stripe",
            status=STATUS_ACTIVE if stripe_active else STATUS_CANDIDATE,
            income_type="Merchant",
            income_eur=stripe_amt,
            income_label=_money_or_dash(stripe_amt),
            roi_label="+" if stripe_amt > 0 else ("?" if not stripe_connected else "0"),
            confidence=(
                CONFIDENCE_BOOKED
                if stripe_amt > 0
                else (
                    CONF_NOT_CONNECTED
                    if not stripe_connected
                    else CONF_KEYS_PRESENT
                )
            ),
            automation_score=100,
            why_ru=(
                (
                    "Реальные платежи клиентов через Checkout/webhook. "
                    "Единственный подтверждённый денежный вход продукта сегодня. "
                    "Вывод на банк — через Stripe Dashboard / payout schedule. "
                    + str(law["trial"]["note_ru"])
                )
                if stripe_amt > 0
                else (
                    "Ключ STRIPE_SECRET_KEY виден. "
                    + (
                        "Webhook тоже есть. "
                        if stripe_webhook
                        else "Нет STRIPE_WEBHOOK_SECRET — оплаты не попадут в Ledger. "
                    )
                    + "Active только после реальной оплаты клиента (ключ ≠ доход)."
                    if stripe_connected
                    else "Кандидат: нужен STRIPE_SECRET_KEY (+ webhook). Пока нет оплат — доход 0."
                )
            ),
            action_ru=(
                "Работает"
                if stripe_active
                else (
                    "Ключи есть · ждём первую оплату клиента"
                    if stripe_connected
                    else "Добавь STRIPE_SECRET_KEY в .env.local → перезапуск Genesis"
                )
            ),
            scalable=True,
            trial_passed_flag=bool(stripe_amt > 0 or stripe_trial_ok),
            keys_present=bool(stripe_connected),
            stage=stripe_stage,
            why_not_earned_ru=stripe_why_not,
            next_step_ru=stripe_next,
            pipeline_steps=_stripe_pipeline(stripe_amt > 0, stripe_connected, stripe_webhook),
        ),
        _row(
            source_id="awin",
            name="Awin",
            status=STATUS_CANDIDATE,
            income_type="Affiliate",
            income_eur=None,
            income_label="—",
            roi_label="?",
            confidence=CONF_KEYS_PRESENT if awin_connected else CONF_NOT_CONNECTED,
            automation_score=90,
            why_ru=(
                "Партнёрская сеть с официальным reporting API. "
                "Комиссии реальные после продаж; вывод обычно SEPA/кабинет. "
                + (
                    "Ключи AWIN_API_TOKEN + AWIN_PUBLISHER_ID на месте — адаптер ещё не пишет комиссии в Ledger."
                    if awin_connected
                    else "Нет ключей: нужен вход в кабинет Awin (Owner Gate — только CEO)."
                )
            ),
            action_ru=(
                "Ключи есть · ждём первую комиссию / дописать адаптер"
                if awin_connected
                else "Подключить AWIN_API_TOKEN + AWIN_PUBLISHER_ID"
            ),
            scalable=True,
            keys_present=bool(awin_connected),
            stage="KEYS_PRESENT" if awin_connected else "NOT_CONNECTED",
            why_not_earned_ru=(
                "Нет подтверждённых комиссий Awin в Ledger."
                if awin_connected
                else "Нет AWIN_API_TOKEN / AWIN_PUBLISHER_ID."
            ),
            next_step_ru=(
                "Дописать адаптер комиссий → первая CONFIRMED выплата."
                if awin_connected
                else "Подключить ключи Awin (Owner Gate)."
            ),
        ),
        _row(
            source_id="digistore24",
            name="Digistore24",
            status=STATUS_CANDIDATE,
            income_type="Affiliate",
            income_eur=None,
            income_label="—",
            roi_label="?",
            confidence=CONF_KEYS_PRESENT if digistore_connected else CONF_NOT_CONNECTED,
            automation_score=90,
            why_ru=(
                "Партнёрские комиссии (часто DE/EU). IPN/API для учёта конверсий. "
                + (
                    "Ключ DIGISTORE24_API_KEY найден. Active/доход — только после реальной комиссии, не от факта ключа."
                    if digistore_connected
                    else "Ключ не виден процессу. Имя в .env.local: DIGISTORE24_API_KEY → перезапуск Genesis."
                )
            ),
            action_ru=(
                "Ключ есть · ждём первую комиссию"
                if digistore_connected
                else "Добавь DIGISTORE24_API_KEY → Остановить/Запустить Genesis"
            ),
            scalable=True,
            keys_present=bool(digistore_connected),
            stage="KEYS_PRESENT" if digistore_connected else "NOT_CONNECTED",
            why_not_earned_ru=(
                "Нет подтверждённых комиссий Digistore в Ledger."
                if digistore_connected
                else "Нет DIGISTORE24_API_KEY."
            ),
            next_step_ru=(
                "Ждать первую комиссию / проверить IPN → Ledger."
                if digistore_connected
                else "Добавить DIGISTORE24_API_KEY → перезапуск."
            ),
        ),
        _row(
            source_id="toloka",
            name="Toloka Pipeline",
            status=STATUS_UNSUPPORTED,
            income_type="Requester",
            income_eur=0.0,
            income_label="0 €",
            roi_label="—",
            confidence=CONF_UNSUPPORTED,
            automation_score=10,
            why_ru=(
                "В Virtus подключён Pipeline API как заказчик (submit datasets/runs), "
                "не performer-кошелёк. Баланса выплат в API нет. "
                "Не использовать как источник дохода исполнителя."
            ),
            action_ru="Не использовать как доход",
            scalable=False,
        ),
        _row(
            source_id="scale_ai",
            name="Scale AI",
            status=STATUS_UNSUPPORTED,
            income_type="Requester",
            income_eur=0.0,
            income_label="0 €",
            roi_label="—",
            confidence=CONF_UNSUPPORTED,
            automation_score=5,
            why_ru=(
                "Адаптер — probe + список задач customer API. "
                "Submit/performer earnings в коде отсутствуют. Не источник дохода Virtus."
            ),
            action_ru="Не использовать как доход",
            scalable=False,
        ),
        _row(
            source_id="internal_queue",
            name="Внутренняя ферма",
            status=STATUS_STUB,
            income_type="Simulator",
            income_eur=round(float(farm_estimate_eur or 0), 4),
            income_label=f"~{float(farm_estimate_eur or 0):.2f} € est.",
            roi_label="est.",
            confidence=CONFIDENCE_ESTIMATED,
            automation_score=95,
            why_ru=(
                "Локальные комбайны + таблица estimate. Высокая автоматизация, "
                "но Confidence=ESTIMATED — это не деньги на счёте и не Stripe."
            ),
            action_ru="Только обучение / оценка",
            scalable=False,
            stage="SIMULATION",
            why_not_earned_ru=(
                "Это ESTIMATED / simulation — не деньги на счёте и не налоговый доход."
            ),
            next_step_ru="Не использовать в DATEV/EÜR. Смотреть Stripe / Opire REAL.",
        ),
        _row(
            source_id="rapidapi",
            name="RapidAPI / API Farm",
            status=STATUS_CANDIDATE,
            income_type="Marketplace",
            income_eur=0.0,
            income_label="0 € Actual",
            roi_label="—",
            confidence=CONF_KEYS_PRESENT
            if (keys_probe or {}).get("RAPIDAPI_KEY")
            or (keys_probe or {}).get("RAPIDAPI_PROVIDER_KEY")
            else CONF_NOT_CONNECTED,
            automation_score=70,
            why_ru=(
                "API Farm channel: discover→build→Quality Gate→CEO approve→publish. "
                "Payout RapidAPI → PayPal. Actual Revenue только после PAID_OUT Hard REAL. "
                "Не смешивать с Stripe B2B."
            ),
            action_ru="Mission Control → API Farm",
            scalable=True,
            stage="API_FARM",
            why_not_earned_ru="Нет подтверждённого RapidAPI PAID_OUT в Ledger.",
            next_step_ru=(
                "Запустить Research → довести 1 API до APPROVAL_REQUIRED → "
                "CEO Approve → ключи RapidAPI → Publish → 1 платящий пользователь."
            ),
        ),
        _opire_row(opire or {}),
        _row(
            source_id="groq",
            name="Groq",
            status=STATUS_COST,
            income_type="Infrastructure",
            income_eur=None,
            income_label="расход",
            roi_label="—",
            confidence=CONF_COST,
            automation_score=100,
            why_ru="LLM API — стоимость разметки/ответов. Не источник дохода.",
            action_ru="Игнорировать как доход",
            scalable=False,
            stage="COST",
            why_not_earned_ru="Инфраструктурный расход, не доход.",
            next_step_ru="Игнорировать в Revenue Lab.",
        ),
        _row(
            source_id="kimi",
            name="Kimi / Moonshot",
            status=STATUS_COST,
            income_type="Infrastructure",
            income_eur=None,
            income_label="расход",
            roi_label="—",
            confidence=CONF_COST,
            automation_score=100,
            why_ru="LLM API — инфраструктурный расход. Не источник дохода.",
            action_ru="Игнорировать как доход",
            scalable=False,
            stage="COST",
            why_not_earned_ru="Инфраструктурный расход, не доход.",
            next_step_ru="Игнорировать в Revenue Lab.",
        ),
    ]

    active = [s for s in sources if s["status"] == STATUS_ACTIVE]
    candidates = [s for s in sources if s["status"] == STATUS_CANDIDATE]
    unsupported = [s for s in sources if s["status"] in {STATUS_UNSUPPORTED, STATUS_STUB, STATUS_COST}]

    return {
        "title": "Revenue Sources",
        "subtitle_ru": "Центр управления доходами — только подтверждённые и вручную добавленные кандидаты",
        "law": law,
        "owner_gate_ru": law["owner_gate_ru"],
        "discovery_ru": (
            "Revenue Discovery (автопоиск по интернету) — отложен. "
            "v0 = ядро каталога + оценка. Кандидаты добавляются вручную."
        ),
        "reality_law_ru": law["title_ru"] + " — " + law["rules_ru"][0],
        "columns": [
            "source",
            "status",
            "type",
            "income",
            "roi",
            "confidence",
            "automation",
            "why",
            "action",
        ],
        "sources": sources,
        "keys_probe": keys_probe
        or {
            "stripe_secret": bool(stripe_connected),
            "stripe_webhook": bool(stripe_webhook),
            "awin": bool(awin_connected),
            "digistore24": bool(digistore_connected),
            "note_ru": (
                "Ключ в файле ≠ Active. Active = реальные деньги. "
                "После правки .env.local нужен перезапуск Genesis.exe."
            ),
        },
        "summary": {
            "active": len(active),
            "candidates": len(candidates),
            "blocked_or_cost": len(unsupported),
            "real_income_eur": stripe_amt,
            "keys_present": sum(
                1
                for flag in (stripe_connected, awin_connected, digistore_connected)
                if flag
            ),
            "verdict_ru": (
                "Ключи не равны доходу: Candidate + KEYS_PRESENT = ключ виден, ждём деньги. "
                "Active только после CONFIRMED поступлений. "
                "Toloka/Scale — Unsupported как доход. Ферма — только estimate."
            ),
        },
    }


def _money_or_dash(amount: float) -> str:
    if amount <= 0:
        return "0 €"
    return f"{amount:.2f} €"


def _stripe_pipeline(paid: bool, connected: bool, webhook: bool) -> list[dict[str, Any]]:
    return [
        {"id": "keys", "label": "Keys", "done": connected},
        {"id": "webhook", "label": "Webhook", "done": webhook},
        {"id": "payment", "label": "Client payment", "done": paid},
        {"id": "ledger", "label": "Ledger CONFIRMED", "done": paid},
    ]


def _opire_row(opire: dict[str, Any]) -> dict[str, Any]:
    approved = int(opire.get("ceo_approved") or 0)
    started = int(opire.get("execution_started") or opire.get("executed") or 0)
    draft = int(opire.get("draft_pr") or 0)
    failed = int(opire.get("failed") or 0)
    skipped = int(opire.get("skipped") or 0)
    paid = int(opire.get("paid") or 0)
    gh = bool(opire.get("github_token"))
    confirmed_usd = float(opire.get("confirmed_usd") or 0)

    if paid > 0 or confirmed_usd > 0:
        stage = "PAID"
        why_not = "Есть подтверждённое вознаграждение."
        next_step = "Сверить payout → Ledger REAL."
        status = STATUS_ACTIVE
        conf = CONFIDENCE_CONFIRMED
    elif draft > 0:
        stage = "DRAFT_PR"
        why_not = "Draft PR готов, но Merge/Payout ещё нет (внешний maintainer)."
        next_step = "CEO Submit (если не отправлено) → ждать Merge → Sync payout."
        status = STATUS_CANDIDATE
        conf = CONFIDENCE_ESTIMATED
    elif started > 0:
        stage = "EXECUTING"
        why_not = "Execution идёт или застрял до Draft PR."
        next_step = "Смотреть timeline задачи · Skip если Impossible."
        status = STATUS_CANDIDATE
        conf = CONFIDENCE_PENDING
    elif approved > 0 and started == 0:
        stage = "EXECUTION_PAUSED"
        why_not = (
            "Approve выполнен, но Execution Engine не стартовал "
            "(или FARM_AUTO_EXECUTE_ON_APPROVE=0)."
        )
        next_step = "Повторить Execution Engine на задаче / проверить логи."
        status = STATUS_CANDIDATE
        conf = CONFIDENCE_PENDING
    else:
        stage = "WAITING_APPROVE"
        why_not = "Нет CEO Approve на TAKE-кандидатах."
        next_step = "Scanner → Approve (авто Execution)."
        status = STATUS_CANDIDATE
        conf = CONF_NOT_CONNECTED

    pipeline = [
        {"id": "found", "label": "Opportunity Found", "done": approved > 0 or started > 0},
        {"id": "approved", "label": "CEO Approved", "done": approved > 0},
        {"id": "started", "label": "Execution Started", "done": started > 0},
        {"id": "draft", "label": "Draft PR", "done": draft > 0},
        {"id": "paid", "label": "Reward Confirmed", "done": paid > 0 or confirmed_usd > 0},
    ]
    if not gh and stage not in {"PAID", "WAITING_APPROVE"}:
        why_not += " · Нет GITHUB_TOKEN — Push/Draft PR live может быть заблокирован."

    return _row(
        source_id="opire",
        name="Opire Farm",
        status=status,
        income_type="Bounty",
        income_eur=confirmed_usd if confirmed_usd > 0 else None,
        income_label=(
            f"{confirmed_usd:.2f} $"
            if confirmed_usd > 0
            else f"Approved {approved} · Started {started} · Draft {draft}"
        ),
        roi_label="+" if confirmed_usd > 0 else "?",
        confidence=conf,
        automation_score=85,
        why_ru=(
            "Bounty конвейер: Approve → Execution → Draft PR → Merge → Payout. "
            f"Failed {failed} · Skipped {skipped}."
        ),
        action_ru=next_step,
        scalable=True,
        keys_present=gh,
        stage=stage,
        why_not_earned_ru=why_not,
        next_step_ru=next_step,
        pipeline_steps=pipeline,
    )


def _row(
    *,
    source_id: str,
    name: str,
    status: str,
    income_type: str,
    income_eur: float | None,
    income_label: str,
    roi_label: str,
    confidence: str,
    automation_score: int,
    why_ru: str,
    action_ru: str,
    scalable: bool,
    trial_passed_flag: bool = False,
    keys_present: bool = False,
    stage: str = "",
    why_not_earned_ru: str = "",
    next_step_ru: str = "",
    pipeline_steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    conf_display = confidence
    if confidence in {
        CONFIDENCE_BOOKED,
        CONFIDENCE_CONFIRMED,
        CONFIDENCE_ESTIMATED,
        CONFIDENCE_SIMULATED,
        CONFIDENCE_PENDING,
    }:
        conf_label_ru = confidence_label(confidence)
    elif confidence == CONF_KEYS_PRESENT:
        conf_label_ru = "KEYS_PRESENT · ключ есть"
    else:
        conf_label_ru = confidence

    # Candidate + keys: keep Candidate (no fake Active), clarify label for CEO.
    if status == STATUS_CANDIDATE and keys_present:
        status_label = "Ключ есть"
        status_emoji = "🟡"
    else:
        status_label = STATUS_LABEL_RU.get(status, status)
        status_emoji = STATUS_EMOJI.get(status, "⚪")

    return {
        "id": source_id,
        "name": name,
        "status": status,
        "status_emoji": status_emoji,
        "status_label": status_label,
        "keys_present": bool(keys_present),
        "type": income_type,
        "income_eur": income_eur,
        "income_label": income_label,
        "roi_label": roi_label,
        "confidence": conf_display,
        "confidence_label_ru": conf_label_ru,
        "automation_score": int(automation_score),
        "automation_label": f"{int(automation_score)}%",
        "why_ru": why_ru,
        "action_ru": action_ru,
        "scalable": scalable,
        "trial_passed": trial_passed_flag,
        "stage": stage or status.upper(),
        "why_not_earned_ru": why_not_earned_ru or why_ru,
        "next_step_ru": next_step_ru or action_ru,
        "pipeline_steps": pipeline_steps or [],
        "why_button_label_ru": "Почему не заработало?",
    }
