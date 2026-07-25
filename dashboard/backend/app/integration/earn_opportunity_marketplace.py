"""Earn Opportunity Marketplace — value opportunities, not €0.01 API scrape.

Separate from Toloka/Scale digital farm and from lead Opportunity Engine.
Reality over Simulation: KEYS_PRESENT ≠ commission; plan ≠ paid.

Farms (CEO map):
  Affiliate · Report · Content · API Products · Work Marketplace (own orders only)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MARKETPLACE_VERSION = "earn_marketplace_v0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digistore_key() -> bool:
    return bool(
        os.getenv("DIGISTORE24_API_KEY", "").strip()
        or os.getenv("DIGISTORE_API_KEY", "").strip()
    )


def _awin_key() -> bool:
    return bool(os.getenv("AWIN_API_TOKEN", "").strip()) and bool(
        os.getenv("AWIN_PUBLISHER_ID", "").strip()
    )


def _stripe_key() -> bool:
    return bool(os.getenv("STRIPE_SECRET_KEY", "").strip())


def build_earn_marketplace_board(memory_dir: Path | None = None) -> dict[str, Any]:
    """Daily board: farms + scored ways to create paid value today."""
    mem = Path(memory_dir) if memory_dir else None
    digi = _digistore_key()
    awin = _awin_key()
    stripe = _stripe_key()

    ready_now = 0
    waiting = 0
    autosend = False
    runner = False
    sent_today = 0
    work_landing_received = 0
    try:
        from app.integration.context import get_integration

        ctx = get_integration(mem)
        desk = ctx.acquisition.studio_status()
        ready_now = int(desk.get("ready_now") or 0)
        waiting = int(desk.get("waiting") or 0)
        autosend = bool(desk.get("auto_send") or desk.get("outreach_send_enabled"))
        runner = bool((desk.get("outreach_runner") or {}).get("running"))
        sent_today = int(desk.get("sent_today_count") or 0)
        try:
            st = ctx.work_farm.stats(work_type="landing_page")
            work_landing_received = int(st.get("received") or 0)
        except Exception:
            pass
    except Exception:
        pass

    farms = [
        {
            "id": "affiliate_farm",
            "label_ru": "Affiliate Farm",
            "stars": 5,
            "status": "partial" if digi or awin else "ready_to_wire",
            "status_ru": (
                "Digistore ключ на месте · комиссия → Ledger ещё не sync"
                if digi
                else "Нужен Digistore/Awin ключ + Recommendation → офер"
            ),
            "flow_ru": [
                "Аудит сайта",
                "Проблема / need",
                "Recommendation Engine",
                "Официальная партнёрская ссылка",
                "Покупка",
                "Комиссия → Ledger",
            ],
            "networks": [
                {"id": "digistore24", "connected": digi, "role": "primary"},
                {"id": "awin", "connected": awin, "role": "candidate"},
                {"id": "impact", "connected": False, "role": "planned"},
                {"id": "cj_affiliate", "connected": False, "role": "planned"},
            ],
            "rule_ru": "Не реклама всем подряд — только confirmed need.",
            "href": "/revenue",
        },
        {
            "id": "report_farm",
            "label_ru": "Report Farm",
            "stars": 5,
            "status": "partial",
            "status_ru": (
                "Аудит сайта live (Commercial API + /site analysis). "
                "SKU SEO/security/speed report — следующий Work Farm тип."
            ),
            "flow_ru": [
                "Найти компанию / URL",
                "ИИ-анализ",
                "Отчёт 10–100 €",
                "Stripe / API balance",
                "Ledger",
            ],
            "products": [
                {"id": "seo_report", "price_eur": "10–100", "enabled": False},
                {"id": "ai_audit", "price_eur": "API audit", "enabled": True},
                {"id": "competitor", "price_eur": "planned", "enabled": False},
                {"id": "security", "price_eur": "planned", "enabled": False},
                {"id": "speed", "price_eur": "planned", "enabled": False},
            ],
            "rule_ru": "ИИ делает отчёт за минуты — продаём ценность, не центы биржи.",
            "href": "/revenue",
        },
        {
            "id": "content_farm",
            "label_ru": "Content Farm",
            "stars": 4,
            "status": "planned",
            "status_ru": "Зарезервировано: статьи · описания · переводы через Virtus SKU.",
            "flow_ru": ["Заказ", "ИИ-контент", "Quality Gate", "Доставка", "Оплата"],
            "products": [
                {"id": "article", "enabled": False},
                {"id": "product_copy", "enabled": False},
                {"id": "translation", "enabled": False},
            ],
            "rule_ru": "После стабильного Landing / Report — не раньше.",
            "href": "/opportunities",
        },
        {
            "id": "api_products",
            "label_ru": "API Products",
            "stars": 5,
            "status": "live",
            "status_ru": "Commercial API: POST /api/v1/audit live · leads preview · factory reserved.",
            "flow_ru": [
                "CEO выдаёт ключ",
                "Клиент POST /audit",
                "Списание с баланса",
                "Ledger",
            ],
            "products": [
                {"id": "audit", "path": "POST /api/v1/audit", "enabled": True},
                {"id": "seo_report", "path": "POST /api/v1/seo-report", "enabled": False},
                {"id": "translate", "path": "POST /api/v1/translate", "enabled": False},
            ],
            "rule_ru": "Клиенты платят за инфраструктуру Virtus. Owner Gate на ключи.",
            "href": "/revenue",
        },
        {
            "id": "work_marketplace",
            "label_ru": "Work Marketplace",
            "stars": 4,
            "status": "own_orders_only",
            "status_ru": (
                f"Внешний marketplace = false. Work Farm v0: Landing jobs received={work_landing_received}. "
                "Источники: Country Desk · API · партнёры (позже)."
            ),
            "flow_ru": [
                "Свои лиды / API / партнёры",
                "Work Farm",
                "Quality Gate",
                "Delivered",
                "Revenue",
            ],
            "rule_ru": "Только где ToS позволяет. Не Upwork-автомат без проверки правил.",
            "href": "/revenue",
        },
    ]

    opportunities: list[dict[str, Any]] = []

    def add(
        *,
        title_ru: str,
        farm_id: str,
        roi: str,
        priority: int,
        action_ru: str,
        why_ru: str,
        live: bool,
    ) -> None:
        opportunities.append(
            {
                "id": f"opp-{len(opportunities) + 1}",
                "title_ru": title_ru,
                "farm_id": farm_id,
                "roi": roi,  # high | medium | low
                "priority": priority,
                "action_ru": action_ru,
                "why_ru": why_ru,
                "live": live,
                "at": _utc_now(),
            }
        )

    # High: close Path A leads
    if ready_now > 0 and autosend and runner:
        add(
            title_ru=f"Закрыть {ready_now} Ready-лидов (автоотправка)",
            farm_id="work_marketplace",
            roi="high",
            priority=5,
            action_ru="Country Desk уже шлёт — смотри Sent today и Live Monitor.",
            why_ru="Самый прямой путь к Stripe € без нового модуля.",
            live=True,
        )
    elif ready_now > 0:
        add(
            title_ru=f"Готово {ready_now} Ready — включи Пуск / автоотправку",
            farm_id="work_marketplace",
            roi="high",
            priority=8,
            action_ru="Country Desk → ▶ Пуск + автоотправка.",
            why_ru="Лиды готовы, конвейер не крутится.",
            live=True,
        )
    elif waiting > 0:
        add(
            title_ru=f"Протолкнуть {waiting} Waiting через Quality Gate",
            farm_id="work_marketplace",
            roi="high",
            priority=12,
            action_ru="Обогати email / Quality Gate — без Ready нет КП.",
            why_ru="Очередь есть, Ready=0 — типичный тормоз Path A.",
            live=True,
        )
    else:
        add(
            title_ru="Запустить hunt новых лидов (Country Desk)",
            farm_id="work_marketplace",
            roi="high",
            priority=15,
            action_ru="Пуск runner · обновить лиды по рынкам.",
            why_ru="Без лидов нет продаж Landing / отчётов.",
            live=True,
        )

    # API products
    add(
        title_ru="Продать Audit API (Commercial API)",
        farm_id="api_products",
        roi="high",
        priority=10,
        action_ru="Доход → пакеты / ключ vc_… · клиент POST /api/v1/audit.",
        why_ru="Продукт уже live; нужен buyer ключа, не новый код.",
        live=True,
    )

    # Affiliate
    if digi:
        add(
            title_ru="Предложить CRM/booking через Digistore (после аудита)",
            farm_id="affiliate_farm",
            roi="medium",
            priority=18,
            action_ru="Гоняй /site#analysis → Recommendation Engine → официальная ссылка.",
            why_ru="Ключ есть; комиссия = покупка на Digistore + sync в Ledger (ещё brick).",
            live=True,
        )
    else:
        add(
            title_ru="Подключить Digistore24 для Affiliate Farm",
            farm_id="affiliate_farm",
            roi="medium",
            priority=25,
            action_ru="DIGISTORE24_API_KEY в .env.local → перезапуск Genesis.",
            why_ru="Без ключа нет listCommissions / партнёрских оферов.",
            live=False,
        )

    # Report farm
    add(
        title_ru="Подготовить SEO-отчёт как платный SKU (10–100 €)",
        farm_id="report_farm",
        roi="high",
        priority=20,
        action_ru="Включить Work Farm type seo_audit + Stripe package (следующий brick).",
        why_ru="Анализ уже есть; не хватает упаковки «отчёт → оплата».",
        live=False,
    )

    # Content
    add(
        title_ru="Content Farm (статьи / переводы) — после Report",
        farm_id="content_farm",
        roi="medium",
        priority=40,
        action_ru="Не стартовать до Path A + Report стабильности.",
        why_ru="Ценность реальна, приоритет ниже Landing/Audit.",
        live=False,
    )

    if stripe:
        add(
            title_ru="Stripe live — принять оплату Path A",
            farm_id="work_marketplace",
            roi="high",
            priority=6,
            action_ru="Держи webhook checkout.session.completed · Work Farm подхватит Landing.",
            why_ru="Единственный CONFIRMED € вход сегодня.",
            live=True,
        )

    opportunities.sort(key=lambda o: int(o.get("priority") or 99))

    high = sum(1 for o in opportunities if o.get("roi") == "high")
    live_n = sum(1 for o in opportunities if o.get("live"))

    return {
        "ok": True,
        "version": MARKETPLACE_VERSION,
        "generated_at": _utc_now(),
        "title_ru": "Marketplace возможностей",
        "subtitle_ru": (
            "Не волшебные API по €0,01 — реальные способы создать ценность и получить оплату. "
            "Отдельный контур от цифровой фермы (Toloka/разметка)."
        ),
        "external_task_marketplace": False,
        "digital_farm_note_ru": "Ферма разметки (/) — не здесь. Здесь — заработок на ценности.",
        "desk_pulse": {
            "ready_now": ready_now,
            "waiting": waiting,
            "autosend": autosend,
            "runner": runner,
            "sent_today": sent_today,
            "stripe_key": stripe,
            "digistore_key": digi,
        },
        "headline_ru": (
            f"Сегодня найдено: {len(opportunities)} способов заработать · "
            f"{high} с высоким ROI · {live_n} можно делать сейчас"
        ),
        "farms": farms,
        "opportunities": opportunities,
        "principle_ru": (
            "Ищем возможности создать ценность и получить оплату — "
            "не источники микровыплат."
        ),
    }
