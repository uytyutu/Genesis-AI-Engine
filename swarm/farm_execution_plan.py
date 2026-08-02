"""Farm Execution Plan — layer between CEO GO and Confirmed €.

GO is not «start a business». GO runs automatable prep:
  Research → GO → Execution Plan → Checklist → Auto Tasks
  → Owner Auto Mode (if armed) OR Waiting for CEO → Production-ready → Confirmed €

Owner Gate still applies for first-time ToS / bank binding.
After Stripe Live + RapidAPI + Publish Token + Owner Auto Mode, publish steps
run without perpetual ceo_required.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env_present(*names: str) -> bool:
    return any(bool(str(os.environ.get(n) or "").strip()) for n in names)


def _env_flag(*names: str) -> bool:
    for n in names:
        v = str(os.environ.get(n) or "").strip().lower()
        if v in ("1", "true", "yes", "on"):
            return True
    return False


def stripe_live_ok() -> bool:
    """Stripe production secret present (sk_live_)."""
    sk = str(os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    return sk.startswith("sk_live_")


def rapidapi_account_ok() -> bool:
    """RapidAPI account credentials available in env."""
    return _env_present(
        "RAPIDAPI_KEY",
        "RAPIDAPI_PROVIDER_KEY",
        "RAPIDAPI_ACCOUNT_ID",
    )


def rapidapi_publish_token_ok() -> bool:
    """Token with rights to sync/publish provider listing (or shared RAPIDAPI_KEY)."""
    return _env_present(
        "RAPIDAPI_PUBLISH_TOKEN",
        "RAPIDAPI_PROVIDER_TOKEN",
        "RAPIDAPI_KEY",
    )


def owner_auto_mode_ok() -> bool:
    """CEO once enabled automatic commercial publish (not perpetual manual gates)."""
    return _env_flag("GENESIS_OWNER_AUTO_PUBLISH", "VIRTUS_OWNER_AUTO_MODE")


def auto_publish_prerequisites() -> dict[str, Any]:
    """Shared gate for RapidAPI (and similar) auto-publish."""
    checks = {
        "stripe_live": stripe_live_ok(),
        "rapidapi_account": rapidapi_account_ok(),
        "publish_token": rapidapi_publish_token_ok(),
        "owner_auto_mode": owner_auto_mode_ok(),
    }
    ready = all(checks.values())
    missing = [k for k, ok in checks.items() if not ok]
    return {
        "ready": ready,
        "checks": checks,
        "missing": missing,
        "rule_ru": (
            "IF Stripe Live = OK AND RapidAPI Account = Connected "
            "AND Publish Token = Available AND Owner Auto Mode = Enabled "
            "→ публиковать автоматически; ELSE → CEO Required"
        ),
    }


def _item(
    *,
    id: str,
    title_ru: str,
    status: str,
    detail_ru: str,
    auto: bool = True,
) -> dict[str, Any]:
    return {
        "id": id,
        "title_ru": title_ru,
        "status": status,  # pass | fail | ceo_required | done | skip
        "detail_ru": detail_ru,
        "auto": auto,
    }


def _stage_from_checklist(checklist: list[dict[str, Any]]) -> str:
    auto_fail = sum(1 for c in checklist if c["status"] == "fail" and c["auto"])
    ceo_n = sum(1 for c in checklist if c["status"] == "ceo_required")
    if auto_fail:
        return "blocked"
    if ceo_n:
        return "waiting_for_ceo"
    return "ready_for_production"


def plan_own_api_stripe(memory_dir: Path | None) -> dict[str, Any]:
    """Automatable readiness for Own API + Stripe (first Live Earn candidate)."""
    checklist: list[dict[str, Any]] = []

    stripe_ok = _env_present("STRIPE_SECRET_KEY")
    live_ok = stripe_live_ok()
    checklist.append(
        _item(
            id="stripe_keys",
            title_ru="Проверить Stripe Keys",
            status="pass" if stripe_ok else "fail",
            detail_ru=(
                (
                    "STRIPE_SECRET_KEY Live (sk_live_) — production"
                    if live_ok
                    else "STRIPE_SECRET_KEY найден (не Live — test/sk_test_)"
                )
                if stripe_ok
                else "Нет STRIPE_SECRET_KEY — задайте ключ (Owner Gate: Virtus не создаёт аккаунт Stripe)"
            ),
        )
    )

    webhook_ok = _env_present("STRIPE_WEBHOOK_SECRET")
    checklist.append(
        _item(
            id="stripe_webhook",
            title_ru="Проверить Webhook secret",
            status="pass" if webhook_ok else "fail",
            detail_ru=(
                "STRIPE_WEBHOOK_SECRET задан"
                if webhook_ok
                else "Нет STRIPE_WEBHOOK_SECRET — без webhook fulfillment API ключа ненадёжен"
            ),
        )
    )

    packages_ok = False
    micro_ok = False
    pkgs: list[Any] = []
    try:
        from app.commercial_api.packages import get_package, list_packages

        pkgs = list_packages(memory_dir)
        packages_ok = len(pkgs) >= 1
        micro = get_package("micro", memory_dir)
        micro_ok = bool(micro and float(micro.get("price_eur") or 0) == 5.0)
    except Exception as exc:
        checklist.append(
            _item(
                id="packages",
                title_ru="Проверить Packages",
                status="fail",
                detail_ru=f"Не удалось загрузить packages: {exc}",
            )
        )
    else:
        checklist.append(
            _item(
                id="packages",
                title_ru="Проверить Packages",
                status="pass" if packages_ok else "fail",
                detail_ru=(
                    f"Пакетов: {len(pkgs)} · Micro 5 €: {'да' if micro_ok else 'нет'}"
                ),
            )
        )

    checkout_ok = False
    try:
        from app.integration.payment_checkout_service import PaymentCheckoutService

        checkout_ok = PaymentCheckoutService is not None and stripe_ok
    except Exception:
        checkout_ok = False
    checklist.append(
        _item(
            id="checkout",
            title_ru="Проверить Checkout",
            status="pass" if checkout_ok else "fail",
            detail_ru=(
                "PaymentCheckoutService + Stripe key — путь checkout доступен"
                if checkout_ok
                else "Checkout недоступен без Stripe key / сервиса"
            ),
        )
    )

    checklist.append(
        _item(
            id="api_product",
            title_ru="API Product (каталог)",
            status="pass",
            detail_ru="commercial_api packages + /api-access landing уже в коде — продукт описан",
        )
    )
    checklist.append(
        _item(
            id="pricing",
            title_ru="Pricing (Micro 5 €)",
            status="pass" if micro_ok else "fail",
            detail_ru=(
                "Micro 5 € готов — первый покупатель API"
                if micro_ok
                else "Добавьте package micro = 5 €"
            ),
        )
    )
    checklist.append(
        _item(
            id="landing",
            title_ru="Landing /api-access",
            status="pass",
            detail_ru="Публичная витрина /api-access в Commercial Engine (не Farm Earn)",
        )
    )

    auto_mode = owner_auto_mode_ok()
    if live_ok and auto_mode:
        checklist.append(
            _item(
                id="owner_stripe_dashboard",
                title_ru="Owner: Stripe Dashboard / банк",
                status="pass",
                detail_ru=(
                    "Stripe Live + Owner Auto Mode — аккаунт уже подключён. "
                    "Virtus не спрашивает повторно ToS; payouts смотрите в Dashboard при необходимости."
                ),
                auto=True,
            )
        )
    elif live_ok:
        checklist.append(
            _item(
                id="owner_stripe_dashboard",
                title_ru="Owner: Stripe Dashboard / банк",
                status="ceo_required",
                detail_ru=(
                    "Stripe Live OK. Чтобы Virtus не останавливался на каждом шаге — "
                    "включите GENESIS_OWNER_AUTO_PUBLISH=1 (Owner Auto Mode)."
                ),
                auto=False,
            )
        )
    else:
        checklist.append(
            _item(
                id="owner_stripe_dashboard",
                title_ru="Owner: Stripe Dashboard / банк",
                status="ceo_required",
                detail_ru=(
                    "Нужен sk_live_ (не test). Virtus не создаёт аккаунт и не принимает ToS. "
                    "После Live + Auto Mode этот пункт станет автоматическим."
                ),
                auto=False,
            )
        )

    checklist.append(
        _item(
            id="first_buyer",
            title_ru="Первый покупатель → Hard REAL",
            status="pass" if (live_ok and checkout_ok and micro_ok) else "ceo_required",
            detail_ru=(
                "Система готова принимать оплату. € появятся после реальной покупки Micro "
                "(не баг — рынок). Ключи и checkout уже wired."
                if (live_ok and checkout_ok and micro_ok)
                else (
                    "Доход появится после реальной оплаты Stripe + External Payout ID "
                    "(Finance Reality Law). Сначала закройте Stripe Live / checkout / Micro."
                )
            ),
            auto=bool(live_ok and checkout_ok and micro_ok),
        )
    )

    auto_pass = sum(1 for c in checklist if c["status"] == "pass" and c["auto"])
    auto_fail = sum(1 for c in checklist if c["status"] == "fail" and c["auto"])
    ceo_n = sum(1 for c in checklist if c["status"] == "ceo_required")
    stage = _stage_from_checklist(checklist)

    manifest = {
        "opportunity_id": "earn-own-api-stripe",
        "product": "platform_api",
        "channel": "stripe",
        "prepared_at": _utc_now(),
        "stage": stage,
        "auto_pass": auto_pass,
        "auto_fail": auto_fail,
        "ceo_actions_left": ceo_n,
        "stripe_live": live_ok,
        "owner_auto_mode": auto_mode,
    }
    if memory_dir:
        path = Path(memory_dir) / "farm_exec_own_api_stripe.json"
        try:
            path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            checklist.append(
                _item(
                    id="write_manifest",
                    title_ru="Сохранить Execution Manifest",
                    status="done",
                    detail_ru=f"Записано: {path.name}",
                )
            )
        except OSError as exc:
            checklist.append(
                _item(
                    id="write_manifest",
                    title_ru="Сохранить Execution Manifest",
                    status="fail",
                    detail_ru=str(exc),
                )
            )

    stage = _stage_from_checklist(checklist)
    return {
        "ok": True,
        "plan_id": "own_api_stripe_v1",
        "opportunity_id": "earn-own-api-stripe",
        "title_ru": "Execution Plan · Own API + Stripe",
        "stage": stage,
        "checklist": checklist,
        "ceo_actions_ru": [
            c["title_ru"] for c in checklist if c["status"] == "ceo_required"
        ],
        "auto_publish": {
            "stripe_live": live_ok,
            "owner_auto_mode": auto_mode,
        },
        "why_no_eur_ru": (
            "Кнопка GO проверяет keys/packages/checkout. "
            "€ появляются только после оплаты клиента + Hard REAL payout — "
            "не из‑за ложного ceo_required на уже подключённом Stripe."
        ),
        "next_ru": (
            "Продайте Micro 5 € через /api-access. "
            "Для авто-публикации смежных каналов: GENESIS_OWNER_AUTO_PUBLISH=1."
            if live_ok
            else "Поставьте sk_live_ + webhook, затем продайте Micro 5 €."
        ),
        "updated_at": _utc_now(),
    }


def _arm_rapidapi_auto_publish(memory_dir: Path | None, gate: dict[str, Any]) -> dict[str, Any]:
    """Persist auto-publish armament; optional webhook if configured."""
    payload = {
        "status": "armed",
        "armed_at": _utc_now(),
        "gate": gate,
        "artifacts": [
            "farm_exec_rapidapi_openapi.json",
            "farm_exec_rapidapi_listing.json",
        ],
        "note_ru": (
            "Owner Auto Mode: OpenAPI + listing готовы к синхронизации. "
            "Virtus не останавливается на ceo_required, пока токены валидны."
        ),
    }
    webhook = str(os.environ.get("GENESIS_RAPIDAPI_PUBLISH_WEBHOOK") or "").strip()
    if webhook:
        try:
            import urllib.request

            req = urllib.request.Request(
                webhook,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:  # noqa: S310
                payload["webhook_status"] = int(getattr(resp, "status", 0) or 0)
                payload["status"] = "synced" if payload["webhook_status"] < 400 else "armed"
        except Exception as exc:  # noqa: BLE001
            payload["webhook_error"] = str(exc)[:240]
            payload["status"] = "armed_webhook_failed"

    if memory_dir:
        path = Path(memory_dir) / "farm_exec_rapidapi_auto_publish.json"
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            payload["manifest"] = path.name
        except OSError as exc:
            payload["manifest_error"] = str(exc)
    return payload


def plan_rapidapi_provider(memory_dir: Path | None) -> dict[str, Any]:
    """Prepare listing; auto-publish when Stripe Live + RapidAPI + token + Auto Mode."""
    checklist: list[dict[str, Any]] = []
    gate = auto_publish_prerequisites()

    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": "Virtus Core Platform API",
            "version": "0.1.0",
            "description": (
                "Website audit prepaid API — prepared by Farm Execution Plan "
                "(auto-publish when Owner Auto Mode is armed)."
            ),
        },
        "paths": {
            "/v1/audit": {
                "post": {
                    "summary": "Run website audit",
                    "operationId": "runAudit",
                    "responses": {"200": {"description": "Audit report"}},
                }
            }
        },
    }
    listing = {
        "name": "Virtus Core Website Audit API",
        "category": "Data",
        "pricing_hint": "metered / prepaid credit",
        "description_ru": (
            "URL → структурированный audit-отчёт. "
            "Публикация: автоматически при Owner Auto Mode, иначе — CEO."
        ),
        "owner_steps_ru": [
            "Один раз: Stripe Live + RapidAPI account + publish token",
            "Один раз: GENESIS_OWNER_AUTO_PUBLISH=1",
            "Далее: Virtus синхронизирует OpenAPI/listing сам",
        ],
        "auto_publish_gate": gate,
    }
    written = False
    if memory_dir:
        try:
            mem = Path(memory_dir)
            (mem / "farm_exec_rapidapi_openapi.json").write_text(
                json.dumps(openapi, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (mem / "farm_exec_rapidapi_listing.json").write_text(
                json.dumps(listing, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            written = True
        except OSError:
            written = False

    checklist.append(
        _item(
            id="openapi",
            title_ru="Сгенерировать OpenAPI stub",
            status="done" if written else "fail",
            detail_ru="farm_exec_rapidapi_openapi.json" if written else "Не удалось записать",
        )
    )
    checklist.append(
        _item(
            id="listing",
            title_ru="Подготовить Listing / описание",
            status="done" if written else "fail",
            detail_ru="farm_exec_rapidapi_listing.json" if written else "Не удалось записать",
        )
    )

    # Prerequisite visibility — missing items are Owner Gate (not hard blocked)
    checklist.append(
        _item(
            id="gate_stripe_live",
            title_ru="Stripe Live",
            status="pass" if gate["checks"]["stripe_live"] else "ceo_required",
            detail_ru=(
                "sk_live_ в окружении"
                if gate["checks"]["stripe_live"]
                else "Нужен STRIPE_SECRET_KEY=sk_live_… (не test)"
            ),
            auto=bool(gate["checks"]["stripe_live"]),
        )
    )
    checklist.append(
        _item(
            id="gate_rapidapi_account",
            title_ru="RapidAPI Account",
            status="pass" if gate["checks"]["rapidapi_account"] else "ceo_required",
            detail_ru=(
                "RAPIDAPI_KEY / PROVIDER_KEY найден"
                if gate["checks"]["rapidapi_account"]
                else "Задайте RAPIDAPI_KEY (аккаунт уже должен существовать у владельца)"
            ),
            auto=bool(gate["checks"]["rapidapi_account"]),
        )
    )
    checklist.append(
        _item(
            id="gate_publish_token",
            title_ru="Publish Token",
            status="pass" if gate["checks"]["publish_token"] else "ceo_required",
            detail_ru=(
                "Токен публикации доступен"
                if gate["checks"]["publish_token"]
                else "Задайте RAPIDAPI_PUBLISH_TOKEN или RAPIDAPI_KEY"
            ),
            auto=bool(gate["checks"]["publish_token"]),
        )
    )
    checklist.append(
        _item(
            id="gate_owner_auto",
            title_ru="Owner Auto Mode",
            status="pass" if gate["checks"]["owner_auto_mode"] else "ceo_required",
            detail_ru=(
                "GENESIS_OWNER_AUTO_PUBLISH=1 — авто-публикация разрешена владельцем"
                if gate["checks"]["owner_auto_mode"]
                else (
                    "Stripe/RapidAPI уже могут быть готовы, но Auto Mode выключен. "
                    "Поставьте GENESIS_OWNER_AUTO_PUBLISH=1 один раз — дальше без ceo_required."
                )
            ),
            auto=bool(gate["checks"]["owner_auto_mode"]),
        )
    )

    publish_armed: dict[str, Any] | None = None
    if written and gate["ready"]:
        publish_armed = _arm_rapidapi_auto_publish(memory_dir, gate)
        synced = str(publish_armed.get("status") or "") in ("armed", "synced")
        checklist.append(
            _item(
                id="publish_owner",
                title_ru="Публикация на RapidAPI",
                status="done" if synced else "pass",
                detail_ru=(
                    f"Auto Mode: {publish_armed.get('status')} · "
                    f"{publish_armed.get('manifest') or 'manifest ready'}. "
                    "Не требуется ручной CEO на каждом обновлении."
                ),
                auto=True,
            )
        )
    elif written:
        missing = ", ".join(gate["missing"]) or "prerequisites"
        checklist.append(
            _item(
                id="publish_owner",
                title_ru="Публикация на RapidAPI",
                status="ceo_required",
                detail_ru=(
                    f"Материалы готовы (OpenAPI + listing). Не хватает: {missing}. "
                    "После полного gate Virtus публикует сам."
                ),
                auto=False,
            )
        )
    else:
        checklist.append(
            _item(
                id="publish_owner",
                title_ru="Публикация на RapidAPI",
                status="fail",
                detail_ru="Сначала нужны OpenAPI + listing на диске",
                auto=True,
            )
        )

    payouts_ready = _env_flag("RAPIDAPI_PAYOUTS_READY", "GENESIS_RAPIDAPI_PAYOUTS_OK")
    if gate["ready"] and payouts_ready:
        checklist.append(
            _item(
                id="payouts_owner",
                title_ru="Payouts провайдера",
                status="pass",
                detail_ru="RAPIDAPI_PAYOUTS_READY=1 — владелец подтвердил payouts в кабинете",
                auto=True,
            )
        )
    elif gate["ready"]:
        checklist.append(
            _item(
                id="payouts_owner",
                title_ru="Payouts провайдера",
                status="ceo_required",
                detail_ru=(
                    "Публикация может идти автоматически; включение payouts/банка в RapidAPI "
                    "часто остаётся разовым Owner Gate. После настройки: RAPIDAPI_PAYOUTS_READY=1."
                ),
                auto=False,
            )
        )
    else:
        checklist.append(
            _item(
                id="payouts_owner",
                title_ru="Payouts провайдера",
                status="ceo_required",
                detail_ru="Сначала закройте gate авто-публикации, затем payouts в кабинете RapidAPI",
                auto=False,
            )
        )

    stage = _stage_from_checklist(checklist)
    if gate["ready"] and written and stage == "waiting_for_ceo":
        # Only payouts left — still waiting_for_ceo, but publish is not the blocker
        pass
    if gate["ready"] and written and not any(
        c["status"] == "ceo_required" for c in checklist
    ):
        stage = "ready_for_auto_publish"

    return {
        "ok": True,
        "plan_id": "rapidapi_provider_v1",
        "opportunity_id": "earn-rapidapi-provider",
        "title_ru": "Execution Plan · RapidAPI Provider",
        "stage": stage,
        "checklist": checklist,
        "ceo_actions_ru": [
            c["title_ru"] for c in checklist if c["status"] == "ceo_required"
        ],
        "auto_publish": gate,
        "auto_publish_result": publish_armed,
        "why_no_eur_ru": (
            "GO готовит OpenAPI + listing и проверяет gate. "
            "При полном gate публикация не требует повторного CEO. "
            "€ — после provider payout / External Payout ID (Finance Reality Law)."
        ),
        "next_ru": (
            "Auto Mode вооружён — синхронизация listing идёт без ручного ceo_required. "
            "При необходимости подтвердите payouts (RAPIDAPI_PAYOUTS_READY=1)."
            if gate["ready"]
            else (
                "Не хватает: "
                + ", ".join(gate["missing"])
                + ". Один раз закройте предпосылки — дальше Virtus сам."
            )
        ),
        "updated_at": _utc_now(),
    }


def plan_generic_service(opportunity: dict[str, Any]) -> dict[str, Any]:
    """B2B service seeds — prepare brief only."""
    oid = str(opportunity.get("id") or "")
    title = str(opportunity.get("title") or oid)
    live_ok = stripe_live_ok()
    auto_mode = owner_auto_mode_ok()
    wire_status = "pass" if (live_ok and auto_mode) else "ceo_required"
    checklist = [
        _item(
            id="brief",
            title_ru="Зафиксировать product brief",
            status="done",
            detail_ru=f"{title} · research brief сохранён в плане",
        ),
        _item(
            id="wire_stripe",
            title_ru="Привязать продажу к Stripe / Path A",
            status=wire_status,
            detail_ru=(
                "Stripe Live + Owner Auto Mode — Commercial Engine уже wired"
                if wire_status == "pass"
                else "Нужны sk_live_ и GENESIS_OWNER_AUTO_PUBLISH=1, либо ручной Path A заказ"
            ),
            auto=wire_status == "pass",
        ),
        _item(
            id="no_toloka_earn",
            title_ru="Не ждать € от Toloka Pipeline",
            status="pass",
            detail_ru="Toloka Requester = Spend. Pipeline OK ≠ выплата Virtus.",
        ),
    ]
    return {
        "ok": True,
        "plan_id": f"generic_{oid}",
        "opportunity_id": oid,
        "title_ru": f"Execution Plan · {title}",
        "stage": _stage_from_checklist(checklist),
        "checklist": checklist,
        "ceo_actions_ru": [
            c["title_ru"] for c in checklist if c["status"] == "ceo_required"
        ],
        "why_no_eur_ru": (
            "Это каталог + подготовка. Автозаработок центов с бирж-исполнителей "
            "запрещён / не подключён (нет Live Earn Performer)."
        ),
        "next_ru": "Выберите Own API + Stripe как первый Live Earn / Commercial путь.",
        "updated_at": _utc_now(),
    }


def run_execution_plan(
    opportunity: dict[str, Any],
    *,
    memory_dir: Path | None,
) -> dict[str, Any]:
    """Dispatch plan by opportunity id / kind."""
    oid = str(opportunity.get("id") or "")
    if oid == "earn-own-api-stripe":
        return plan_own_api_stripe(memory_dir)
    if oid == "earn-rapidapi-provider":
        return plan_rapidapi_provider(memory_dir)
    if str(opportunity.get("kind") or "").startswith("reject") or opportunity.get(
        "tos_automation"
    ) == "forbidden":
        return {
            "ok": False,
            "error": "hard_reject",
            "message_ru": "Hard reject — Execution Plan не запускается",
            "opportunity_id": oid,
        }
    return plan_generic_service(opportunity)
