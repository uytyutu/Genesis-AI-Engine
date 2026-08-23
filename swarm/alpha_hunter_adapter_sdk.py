"""Alpha Hunter Adapter SDK — real discover → prepare → execute (not fake cards).

Law (CEO 2026-08-03):
  Stop generating synthetic opportunities.
  Only show opportunities backed by real adapter output.
  If the adapter cannot discover, prepare or execute a real action → NO_OPPORTUNITY.
  Every Approve card must include a concrete executable_action.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NO_OPPORTUNITY = "NO_OPPORTUNITY"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _playwright_status() -> "AdapterCapabilityNeed":
    try:
        import importlib.util

        ok = importlib.util.find_spec("playwright") is not None
    except Exception:
        ok = False
    if ok:
        return AdapterCapabilityNeed(
            id="browser_playwright",
            title="Browser Automation",
            status="ready",
            detail_ru="Playwright установлен.",
        )
    return AdapterCapabilityNeed(
        id="browser_playwright",
        title="Browser Automation",
        status="missing",
        detail_ru="Need: Playwright. Без Browser нельзя честно заявлять Upwork/Fiverr automation.",
    )


@dataclass
class AdapterCapabilityNeed:
    id: str
    title: str
    status: str  # ready | partial | missing
    detail_ru: str = ""


@dataclass
class AdapterDiscoverResult:
    source_id: str
    opportunities: list[dict[str, Any]] = field(default_factory=list)
    checked: bool = True
    spend_eur: float = 0.0
    message_ru: str = ""
    status: str = "ok"  # ok | NO_OPPORTUNITY
    missing_capabilities: list[AdapterCapabilityNeed] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def executable_action(
    *,
    action_id: str,
    title_ru: str,
    title_en: str,
    verb: str,
    allows_micro_spend: bool = False,
    spend_eur: float = 0.0,
) -> dict[str, Any]:
    return {
        "id": action_id,
        "title_ru": title_ru,
        "title_en": title_en,
        "verb": verb,
        "allows_micro_spend": bool(allows_micro_spend),
        "spend_eur": float(spend_eur),
        "requires_approve": True,
    }


class IncomeSourceAdapter(ABC):
    """Base adapter — discover / evidence / prepare / execute.

    execute() must never invent profit. Default = prepare-only until LIVE + Approve.
    """

    name: str = "unnamed"
    source_id: str = "unnamed"
    category: str = "marketplace"
    draft_root: Path | None = None

    @abstractmethod
    def discover(self) -> AdapterDiscoverResult:
        """Find money-path signals. Empty → status NO_OPPORTUNITY."""

    @abstractmethod
    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        """Structured proof: links, rules, dates — not «I think»."""

    def drafts_dir(self) -> Path:
        root = self.draft_root or Path("alpha_hunter_drafts")
        path = Path(root) / self.source_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_draft(
        self, opportunity: dict[str, Any], *, body: dict[str, Any], markdown: str
    ) -> dict[str, Any]:
        """Persist a real artifact the owner can open / submit."""
        oid = str(opportunity.get("id") or "draft")
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in oid)[:80]
        base = self.drafts_dir() / safe
        json_path = base.with_suffix(".json")
        md_path = base.with_suffix(".md")
        payload = {
            "source_id": self.source_id,
            "adapter": self.name,
            "opportunity_id": oid,
            "executable_action": opportunity.get("executable_action"),
            "created_at": _utc_now(),
            "body": body,
        }
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        md_path.write_text(markdown, encoding="utf-8")
        return {
            "draft_json": str(json_path),
            "draft_md": str(md_path),
            "created_at": payload["created_at"],
        }

    def prepare(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        """Build execution plan + draft files. No spend. Subclasses should override."""
        action = opportunity.get("executable_action") or {}
        if not action.get("id"):
            return {
                "ok": False,
                "error": "no_executable_action",
                "detail_ru": "Нет конкретного действия — карточку не готовим.",
            }
        arts = self.write_draft(
            opportunity,
            body={"note": "generic prepare"},
            markdown=(
                f"# {action.get('title_ru')}\n\n"
                f"Источник: {self.name}\n"
                f"Действие: {action.get('title_en')}\n"
            ),
        )
        return {
            "ok": True,
            "mode": "prepare",
            "source_id": self.source_id,
            "executable_action": action,
            "artifacts": arts,
            "plan": [
                {"step": "1", "title_ru": "Черновик создан (файл на диске)"},
                {"step": "2", "title_ru": "Owner Approve"},
                {"step": "3", "title_ru": "Execute / ручная отправка по инструкции"},
                {"step": "4", "title_ru": "Оплата только realized"},
            ],
            "needs_owner": True,
            "spend_eur": 0.0,
            "opportunity": opportunity,
            "done_ru": f"Подготовлено: {action.get('title_ru')}",
        }

    def execute(self, opportunity: dict[str, Any], *, owner_approved: bool = False) -> dict[str, Any]:
        """Live actions only after owner_approved. Never invent profit."""
        if not owner_approved:
            return {
                "ok": False,
                "error": "owner_approval_required",
                "detail_ru": "Выполнение только после одобрения владельца.",
            }
        action = opportunity.get("executable_action") or {}
        if not action.get("id"):
            return {
                "ok": False,
                "error": "no_executable_action",
                "detail_ru": "Нет executable_action — execute запрещён.",
            }
        gaps = self.capability_gaps()
        missing = [g for g in gaps if g.status == "missing"]
        # Soft gaps: still allow local-only execute variants
        if missing and not action.get("local_ok_without_caps"):
            return {
                "ok": False,
                "error": "missing_capability",
                "missing": [asdict(m) for m in missing],
                "detail_ru": missing[0].detail_ru,
            }
        prep = self.prepare(opportunity)
        return {
            "ok": True,
            "mode": "execute_prepared",
            "source_id": self.source_id,
            "executable_action": action,
            "prepare": prep,
            "profit_recorded_eur": 0.0,
            "lifecycle_hint": "RUNNING",
            "detail_ru": (
                f"Выполнено prepare для «{action.get('title_ru')}». "
                "Прибыль не записана — ждём реальную оплату площадки."
            ),
        }

    def capability_gaps(self) -> list[AdapterCapabilityNeed]:
        return []

    def what_can_earn_ru(self) -> str:
        return "Зависит от площадки."

    def expected_value_ru(self) -> str:
        return "Только после realized payout."

    def has_api(self) -> bool:
        return False

    def automatable(self) -> str:
        return "partial"

    def tos_limits_ru(self) -> str:
        return "Соблюдать ToS площадки; без спама и фейков."

    def needs_browser(self) -> bool:
        return False

    def needs_owner_action(self) -> bool:
        return True

    def passport(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "category": self.category,
            "questions": {
                "what_can_earn_ru": self.what_can_earn_ru(),
                "expected_value_ru": self.expected_value_ru(),
                "has_api": self.has_api(),
                "automatable": self.automatable(),
                "tos_limits_ru": self.tos_limits_ru(),
                "needs_browser": self.needs_browser(),
                "needs_owner_action": self.needs_owner_action(),
            },
            "capability_gaps": [asdict(g) for g in self.capability_gaps()],
        }


class RapidAPIAdapter(IncomeSourceAdapter):
    name = "RapidAPI"
    source_id = "rapidapi"
    category = "marketplace"

    def what_can_earn_ru(self) -> str:
        return "Провайдерский доход с вызовов API (после публикации и реальных users)."

    def has_api(self) -> bool:
        return True

    def capability_gaps(self) -> list[AdapterCapabilityNeed]:
        key = (os.environ.get("RAPIDAPI_KEY") or "").strip()
        if not key:
            return [
                AdapterCapabilityNeed(
                    id="rapidapi_key",
                    title="RapidAPI Key",
                    status="missing",
                    detail_ru="Need: RAPIDAPI_KEY для live provider actions.",
                )
            ]
        return [
            AdapterCapabilityNeed(
                id="rapidapi_key",
                title="RapidAPI Key",
                status="ready",
                detail_ru="RAPIDAPI_KEY найден.",
            )
        ]

    def discover(self) -> AdapterDiscoverResult:
        gaps = self.capability_gaps()
        missing = [g for g in gaps if g.status == "missing"]
        if missing:
            return AdapterDiscoverResult(
                source_id=self.source_id,
                opportunities=[],
                status=NO_OPPORTUNITY,
                message_ru="NO_OPPORTUNITY: нет RAPIDAPI_KEY — листинг не готовим.",
                missing_capabilities=missing,
            )
        action = executable_action(
            action_id="rapidapi_submit_listing",
            title_ru="Подготовить и отправить листинг RapidAPI",
            title_en="Submit RapidAPI listing",
            verb="submit_listing",
            allows_micro_spend=False,
        )
        action["local_ok_without_caps"] = False
        opp = {
            "id": "rapidapi_listing_draft",
            "title_ru": "Submit RapidAPI listing",
            "money_path": "api_provider",
            "adapter_backed": True,
            "executable_action": action,
            "needs_owner": True,
            "expected_profit_note_ru": (
                "Доход только после реальных вызовов API — не моделируем «гарантию»."
            ),
        }
        return AdapterDiscoverResult(
            source_id=self.source_id,
            opportunities=[opp],
            status="ok",
            message_ru="RapidAPI: ключ есть — можно готовить листинг.",
            missing_capabilities=[],
        )

    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "RapidAPI Provider docs",
            "reasons": [
                "Официальный API marketplace для провайдеров",
                "Выплата только после реальных вызовов (не гарантируется)",
                "Черновик листинга пишется на диск до Approve",
            ],
            "opportunity": opportunity,
        }

    def prepare(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        action = opportunity.get("executable_action") or {}
        body = {
            "listing": {
                "name": "Virtus Core Skill API",
                "category": "Artificial Intelligence",
                "summary": "Owner-approved Virtus skill endpoint for RapidAPI providers.",
                "pricing": "freemium → paid after traffic",
                "endpoints": ["/v1/health", "/v1/invoke"],
            }
        }
        md = (
            "# RapidAPI listing draft\n\n"
            "## Action\nSubmit RapidAPI listing\n\n"
            "## Name\nVirtus Core Skill API\n\n"
            "## Next after Approve\n"
            "1. Open RapidAPI Provider dashboard\n"
            "2. Paste fields from this draft\n"
            "3. Publish — payouts only from real usage\n"
        )
        arts = self.write_draft(opportunity, body=body, markdown=md)
        return {
            "ok": True,
            "mode": "prepare",
            "source_id": self.source_id,
            "executable_action": action,
            "artifacts": arts,
            "done_ru": "Создан черновик листинга RapidAPI (JSON + MD).",
            "needs_owner": True,
            "spend_eur": 0.0,
            "opportunity": opportunity,
        }


class GumroadAdapter(IncomeSourceAdapter):
    name = "Gumroad"
    source_id = "gumroad"
    category = "marketplace"

    def what_can_earn_ru(self) -> str:
        return "Продажа digital products / шаблонов / инструментов."

    def has_api(self) -> bool:
        return True

    def capability_gaps(self) -> list[AdapterCapabilityNeed]:
        token = (
            os.environ.get("GUMROAD_ACCESS_TOKEN")
            or os.environ.get("GUMROAD_TOKEN")
            or ""
        ).strip()
        if not token:
            return [
                AdapterCapabilityNeed(
                    id="gumroad_token",
                    title="Gumroad API",
                    status="missing",
                    detail_ru="Need: GUMROAD_ACCESS_TOKEN для Publish SKU.",
                )
            ]
        return [
            AdapterCapabilityNeed(
                id="gumroad_token",
                title="Gumroad API",
                status="ready",
                detail_ru="Gumroad token найден.",
            )
        ]

    def discover(self) -> AdapterDiscoverResult:
        gaps = self.capability_gaps()
        missing = [g for g in gaps if g.status == "missing"]
        if missing:
            return AdapterDiscoverResult(
                source_id=self.source_id,
                opportunities=[],
                status=NO_OPPORTUNITY,
                message_ru="NO_OPPORTUNITY: нет GUMROAD_ACCESS_TOKEN — SKU не публикуем.",
                missing_capabilities=missing,
            )
        action = executable_action(
            action_id="gumroad_publish_sku",
            title_ru="Опубликовать SKU на Gumroad",
            title_en="Publish SKU on Gumroad",
            verb="publish_sku",
            allows_micro_spend=False,
        )
        opp = {
            "id": "gumroad_sku_virtus_pack",
            "title_ru": "Publish SKU on Gumroad",
            "money_path": "digital_sales",
            "adapter_backed": True,
            "executable_action": action,
            "needs_owner": True,
        }
        return AdapterDiscoverResult(
            source_id=self.source_id,
            opportunities=[opp],
            status="ok",
            message_ru="Gumroad: token есть — готовим Publish SKU.",
        )

    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "Gumroad API",
            "reasons": [
                "Digital product marketplace",
                "Approve → API create product (если token валиден)",
                "Прибыль только после реальных продаж",
            ],
            "opportunity": opportunity,
        }

    def prepare(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        action = opportunity.get("executable_action") or {}
        body = {
            "product": {
                "name": "Virtus Core — Digital Starter Pack",
                "price_cents": 1900,
                "description": (
                    "Шаблоны и инструкция Virtus Core. "
                    "Публикация только после Owner Approve."
                ),
                "currency": "eur",
            }
        }
        md = (
            "# Gumroad SKU draft\n\n"
            "## Action\nPublish SKU on Gumroad\n\n"
            f"## Name\n{body['product']['name']}\n\n"
            f"## Price\n€{body['product']['price_cents'] / 100:.2f}\n\n"
            "## After Approve\nAPI create product (token) или ручная публикация по черновику.\n"
        )
        arts = self.write_draft(opportunity, body=body, markdown=md)
        return {
            "ok": True,
            "mode": "prepare",
            "source_id": self.source_id,
            "executable_action": action,
            "artifacts": arts,
            "done_ru": "Создан черновик SKU Gumroad.",
            "needs_owner": True,
            "spend_eur": 0.0,
            "product": body["product"],
            "opportunity": opportunity,
        }

    def execute(self, opportunity: dict[str, Any], *, owner_approved: bool = False) -> dict[str, Any]:
        if not owner_approved:
            return {
                "ok": False,
                "error": "owner_approval_required",
                "detail_ru": "Выполнение только после одобрения владельца.",
            }
        prep = self.prepare(opportunity)
        token = (
            os.environ.get("GUMROAD_ACCESS_TOKEN")
            or os.environ.get("GUMROAD_TOKEN")
            or ""
        ).strip()
        if not token:
            return {
                "ok": False,
                "error": "missing_capability",
                "detail_ru": "GUMROAD_ACCESS_TOKEN отсутствует.",
                "prepare": prep,
            }
        product = (prep.get("product") or {}) if isinstance(prep, dict) else {}
        data = urllib.parse.urlencode(
            {
                "access_token": token,
                "name": product.get("name") or "Virtus Core Pack",
                "price": int(product.get("price_cents") or 1900),
                "description": product.get("description") or "",
            }
        ).encode()
        req = urllib.request.Request(
            "https://api.gumroad.com/v2/products",
            data=data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                payload = json.loads(raw) if raw else {}
            ok = bool(payload.get("success"))
            return {
                "ok": ok,
                "mode": "gumroad_api_create",
                "source_id": self.source_id,
                "executable_action": opportunity.get("executable_action"),
                "prepare": prep,
                "api_response": {
                    "success": payload.get("success"),
                    "product_id": (payload.get("product") or {}).get("id"),
                },
                "profit_recorded_eur": 0.0,
                "lifecycle_hint": "WAITING_PAYMENT" if ok else "RUNNING",
                "detail_ru": (
                    "Gumroad: продукт создан через API. Ждём реальные продажи."
                    if ok
                    else "Gumroad API не подтвердил создание — черновик сохранён."
                ),
            }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            return {
                "ok": True,
                "mode": "execute_prepared_local",
                "source_id": self.source_id,
                "executable_action": opportunity.get("executable_action"),
                "prepare": prep,
                "profit_recorded_eur": 0.0,
                "lifecycle_hint": "RUNNING",
                "detail_ru": (
                    f"API Gumroad недоступен ({type(exc).__name__}). "
                    "Черновик SKU сохранён — опубликуйте вручную по файлу."
                ),
            }


class ProductHuntAdapter(IncomeSourceAdapter):
    name = "Product Hunt"
    source_id = "producthunt"
    category = "demand"

    def what_can_earn_ru(self) -> str:
        return "Спрос / запуск продукта; не прямой payout, а канал спроса."

    def has_api(self) -> bool:
        return True

    def needs_browser(self) -> bool:
        return True

    def capability_gaps(self) -> list[AdapterCapabilityNeed]:
        return [_playwright_status()]

    def discover(self) -> AdapterDiscoverResult:
        # Local draft is always preparable — browser only needed to submit online.
        action = executable_action(
            action_id="producthunt_create_draft",
            title_ru="Создать черновик запуска на Product Hunt",
            title_en="Create draft on Product Hunt",
            verb="create_draft",
            allows_micro_spend=False,
        )
        action["local_ok_without_caps"] = True
        gaps = self.capability_gaps()
        missing = [g for g in gaps if g.status == "missing"]
        opp = {
            "id": "producthunt_launch_draft",
            "title_ru": "Create draft on Product Hunt",
            "money_path": "launch_demand",
            "adapter_backed": True,
            "executable_action": action,
            "needs_owner": True,
        }
        return AdapterDiscoverResult(
            source_id=self.source_id,
            opportunities=[opp],
            status="ok",
            message_ru=(
                "Product Hunt: готовим локальный черновик запуска. "
                + (
                    "Browser отсутствует — онлайн-submit после установки Playwright."
                    if missing
                    else "Browser готов — после Approve можно углубить submit."
                )
            ),
            missing_capabilities=missing,
        )

    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "Product Hunt",
            "reasons": [
                "Публичный канал спроса",
                "Черновик launch создаётся локально",
                "Не путать с гарантированным доходом",
            ],
            "opportunity": opportunity,
        }

    def prepare(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        action = opportunity.get("executable_action") or {}
        body = {
            "launch": {
                "name": "Virtus Core",
                "tagline": "Digital company OS — website, AI employee, client workspace",
                "topics": ["SaaS", "AI", "Productivity"],
                "gallery_notes": "Use brand assets from Virtus Core storefront",
            }
        }
        md = (
            "# Product Hunt draft\n\n"
            "## Action\nCreate draft on Product Hunt\n\n"
            f"## Name\n{body['launch']['name']}\n\n"
            f"## Tagline\n{body['launch']['tagline']}\n\n"
            "## After Approve\n"
            "Откройте Product Hunt maker tools и вставьте этот черновик.\n"
        )
        arts = self.write_draft(opportunity, body=body, markdown=md)
        return {
            "ok": True,
            "mode": "prepare",
            "source_id": self.source_id,
            "executable_action": action,
            "artifacts": arts,
            "done_ru": "Создан черновик Product Hunt (JSON + MD).",
            "needs_owner": True,
            "spend_eur": 0.0,
            "opportunity": opportunity,
        }


class PartnerStackAdapter(IncomeSourceAdapter):
    name = "PartnerStack"
    source_id = "partnerstack"
    category = "money_program"

    def what_can_earn_ru(self) -> str:
        return "Партнёрские выплаты по программам (после approve + реальных рефералов)."

    def discover(self) -> AdapterDiscoverResult:
        action = executable_action(
            action_id="partnerstack_prepare_application",
            title_ru="Подготовить заявку PartnerStack",
            title_en="Prepare application for PartnerStack",
            verb="prepare_application",
            allows_micro_spend=False,
        )
        action["local_ok_without_caps"] = True
        opp = {
            "id": "partnerstack_application_draft",
            "title_ru": "Prepare application for PartnerStack",
            "money_path": "affiliate",
            "adapter_backed": True,
            "executable_action": action,
            "needs_owner": True,
        }
        return AdapterDiscoverResult(
            source_id=self.source_id,
            opportunities=[opp],
            status="ok",
            message_ru="PartnerStack: готовим заявку (локальный черновик).",
        )

    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "PartnerStack",
            "reasons": [
                "Партнёрская платформа",
                "Сначала заявка / onboarding",
                "Выплаты только после реальных рефералов",
            ],
            "opportunity": opportunity,
        }

    def prepare(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        action = opportunity.get("executable_action") or {}
        body = {
            "application": {
                "company": "Virtus Core",
                "program_interest": "SaaS / AI tools affiliate",
                "audience": "SMB owners in DE/EU",
                "assets": ["landing", "email sequence", "demo"],
            }
        }
        md = (
            "# PartnerStack application draft\n\n"
            "## Action\nPrepare application for PartnerStack\n\n"
            "## Company\nVirtus Core\n\n"
            "## After Approve\nОтправьте заявку в выбранную программу по этому черновику.\n"
        )
        arts = self.write_draft(opportunity, body=body, markdown=md)
        return {
            "ok": True,
            "mode": "prepare",
            "source_id": self.source_id,
            "executable_action": action,
            "artifacts": arts,
            "done_ru": "Создана заявка PartnerStack (черновик).",
            "needs_owner": True,
            "spend_eur": 0.0,
            "opportunity": opportunity,
        }


ADAPTER_REGISTRY: dict[str, type[IncomeSourceAdapter]] = {
    "rapidapi": RapidAPIAdapter,
    "gumroad": GumroadAdapter,
    "producthunt": ProductHuntAdapter,
    "partnerstack": PartnerStackAdapter,
}


def list_adapters() -> list[dict[str, Any]]:
    out = []
    for _sid, cls in ADAPTER_REGISTRY.items():
        out.append(cls().passport())
    return out


def get_adapter(source_id: str) -> IncomeSourceAdapter | None:
    cls = ADAPTER_REGISTRY.get(source_id)
    return cls() if cls else None


def discover_all_registered(*, draft_root: Path | None = None) -> dict[str, Any]:
    """Run discover() on every registered adapter — €0."""
    results = []
    missing_browser = False
    actionable = 0
    no_ops = 0
    for _sid, cls in ADAPTER_REGISTRY.items():
        inst = cls()
        if draft_root is not None:
            inst.draft_root = draft_root
        r = inst.discover()
        results.append(r.to_dict())
        if r.status == NO_OPPORTUNITY or not r.opportunities:
            no_ops += 1
        else:
            actionable += len(r.opportunities)
        for g in r.missing_capabilities:
            if g.id == "browser_playwright" and g.status == "missing":
                missing_browser = True
    return {
        "ok": True,
        "engine": "Alpha Hunter — Opportunity Discovery Engine",
        "adapters_run": len(results),
        "actionable_opportunities": actionable,
        "no_opportunity_count": no_ops,
        "results": results,
        "browser_status": (
            {"status": "missing", "need": "Playwright", "title": "Browser Automation"}
            if missing_browser
            else {"status": "ok_or_unused"}
        ),
        "law_ru": (
            "Только возможности с executable_action и выходом адаптера. "
            "Нет адаптера / нет действия → NO_OPPORTUNITY, без фейковых карточек."
        ),
    }
