"""Alpha Hunter Adapter SDK — Opportunity Discovery Engine (not a money printer).

R2 foundation: each Income Source is a pluggable adapter (~100–200 lines).
Core stays stable; new markets = new adapter files under swarm/adapters/.

Uniform contract — every adapter answers:
  What can be earned? Expected value range?
  Has API? Automatable? ToS limits?
  Needs Browser? Needs owner action?

Honest status: if Playwright / API key missing → report Missing Capability,
never claim «I can work Upwork» without the tool.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any


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
    missing_capabilities: list[AdapterCapabilityNeed] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


class IncomeSourceAdapter(ABC):
    """Base adapter — discover / evidence / prepare / execute.

    execute() must never invent profit. Default = prepare-only until LIVE + Approve.
    """

    name: str = "unnamed"
    source_id: str = "unnamed"
    category: str = "marketplace"  # paid_work | money_program | marketplace | demand | new_market

    @abstractmethod
    def discover(self) -> AdapterDiscoverResult:
        """Find money-path signals on this platform (€0 search)."""

    @abstractmethod
    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        """Structured proof: links, rules, dates — not «I think»."""

    def prepare(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        """Build execution plan + materials. No spend."""
        return {
            "ok": True,
            "mode": "prepare",
            "source_id": self.source_id,
            "plan": [
                {"step": "1", "title_ru": "Регистрация / доступ"},
                {"step": "2", "title_ru": "Подготовка оффера / листинга"},
                {"step": "3", "title_ru": "Публикация / отклик"},
                {"step": "4", "title_ru": "Оплата (только realized)"},
            ],
            "needs_owner": True,
            "spend_eur": 0.0,
            "opportunity": opportunity,
        }

    def execute(self, opportunity: dict[str, Any], *, owner_approved: bool = False) -> dict[str, Any]:
        """Live actions only after owner_approved. Subclasses override."""
        if not owner_approved:
            return {
                "ok": False,
                "error": "owner_approval_required",
                "detail_ru": "Выполнение только после одобрения владельца.",
            }
        gaps = self.capability_gaps()
        missing = [g for g in gaps if g.status == "missing"]
        if missing:
            return {
                "ok": False,
                "error": "missing_capability",
                "missing": [asdict(m) for m in missing],
                "detail_ru": missing[0].detail_ru,
            }
        return {
            "ok": False,
            "error": "not_implemented",
            "detail_ru": (
                f"Адаптер «{self.name}» ещё не реализует live execute. "
                "Сейчас — Opportunity Discovery + prepare."
            ),
        }

    def capability_gaps(self) -> list[AdapterCapabilityNeed]:
        """What this adapter needs vs what is available."""
        return []

    def passport(self) -> dict[str, Any]:
        """Uniform answers for the director."""
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

    def what_can_earn_ru(self) -> str:
        return "См. адаптер — путь к деньгам на площадке."

    def expected_value_ru(self) -> str:
        return "Диапазон после discover+evidence; не одна «обещанная» цифра."

    def has_api(self) -> bool:
        return False

    def automatable(self) -> str:
        return "none"  # none | partial | full

    def tos_limits_ru(self) -> str:
        return "Только официальные правила площадки; без обхода ToS."

    def needs_browser(self) -> bool:
        return False

    def needs_owner_action(self) -> bool:
        return True


def _playwright_status() -> AdapterCapabilityNeed:
    try:
        import importlib.util

        ok = importlib.util.find_spec("playwright") is not None
    except Exception:  # noqa: BLE001
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


class RapidAPIAdapter(IncomeSourceAdapter):
    name = "RapidAPI"
    source_id = "rapidapi"
    category = "marketplace"

    def what_can_earn_ru(self) -> str:
        return "Провайдерский доход с вызовов API (после публикации и реальных users)."

    def has_api(self) -> bool:
        return True

    def automatable(self) -> str:
        return "partial"

    def needs_browser(self) -> bool:
        return False  # official provider API / dashboard; browser optional

    def capability_gaps(self) -> list[AdapterCapabilityNeed]:
        import os

        gaps = []
        key = (os.environ.get("RAPIDAPI_KEY") or "").strip()
        if not key:
            gaps.append(
                AdapterCapabilityNeed(
                    id="rapidapi_key",
                    title="RapidAPI Key",
                    status="missing",
                    detail_ru="Need: RAPIDAPI_KEY для live provider actions.",
                )
            )
        else:
            gaps.append(
                AdapterCapabilityNeed(
                    id="rapidapi_key",
                    title="RapidAPI Key",
                    status="ready",
                    detail_ru="RAPIDAPI_KEY найден.",
                )
            )
        return gaps

    def discover(self) -> AdapterDiscoverResult:
        gaps = self.capability_gaps()
        missing = [g for g in gaps if g.status == "missing"]
        opps: list[dict[str, Any]] = []
        if not missing:
            opps.append(
                {
                    "id": "rapidapi_provider_slot",
                    "title_ru": "RapidAPI — слот публикации существующего skill",
                    "money_path": "api_provider",
                    "needs_owner": True,
                }
            )
        return AdapterDiscoverResult(
            source_id=self.source_id,
            opportunities=opps,
            message_ru=(
                f"RapidAPI: {'ключ есть — можно готовить листинг' if opps else 'нет RAPIDAPI_KEY — только research'}"
            ),
            missing_capabilities=missing,
        )

    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "RapidAPI Provider docs",
            "reasons": [
                "Официальный API marketplace для провайдеров",
                "Выплата только после реальных вызовов (не гарантируется)",
                "Нужен ToS-compliant listing",
            ],
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

    def automatable(self) -> str:
        return "partial"

    def needs_browser(self) -> bool:
        return False

    def discover(self) -> AdapterDiscoverResult:
        return AdapterDiscoverResult(
            source_id=self.source_id,
            opportunities=[],
            message_ru="Gumroad adapter: discover stub — подключите API token в R2+",
            missing_capabilities=[
                AdapterCapabilityNeed(
                    id="gumroad_token",
                    title="Gumroad API",
                    status="missing",
                    detail_ru="Need: Gumroad access token для live listing.",
                )
            ],
        )

    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "Gumroad",
            "reasons": ["Digital product marketplace", "Owner must approve publish"],
            "opportunity": opportunity,
        }


class ProductHuntAdapter(IncomeSourceAdapter):
    name = "Product Hunt"
    source_id = "producthunt"
    category = "demand"

    def what_can_earn_ru(self) -> str:
        return "Спрос / запуск продукта; не прямой payout, а канал спроса."

    def has_api(self) -> bool:
        return True

    def automatable(self) -> str:
        return "partial"

    def needs_browser(self) -> bool:
        return True

    def capability_gaps(self) -> list[AdapterCapabilityNeed]:
        return [_playwright_status()]

    def discover(self) -> AdapterDiscoverResult:
        gaps = self.capability_gaps()
        return AdapterDiscoverResult(
            source_id=self.source_id,
            opportunities=[],
            message_ru="Product Hunt: спрос-сигналы; Browser может понадобиться для deep scan.",
            missing_capabilities=[g for g in gaps if g.status == "missing"],
        )

    def evidence(self, opportunity: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "Product Hunt",
            "reasons": ["Публичные запуски и спрос", "Не путать с гарантированным доходом"],
            "opportunity": opportunity,
        }


# Registry — add adapter class here when wiring a new Income Source
ADAPTER_REGISTRY: dict[str, type[IncomeSourceAdapter]] = {
    "rapidapi": RapidAPIAdapter,
    "gumroad": GumroadAdapter,
    "producthunt": ProductHuntAdapter,
}


def list_adapters() -> list[dict[str, Any]]:
    out = []
    for sid, cls in ADAPTER_REGISTRY.items():
        inst = cls()
        out.append(inst.passport())
    return out


def get_adapter(source_id: str) -> IncomeSourceAdapter | None:
    cls = ADAPTER_REGISTRY.get(source_id)
    return cls() if cls else None


def discover_all_registered() -> dict[str, Any]:
    """Run discover() on every registered adapter — €0."""
    results = []
    missing_browser = False
    for sid, cls in ADAPTER_REGISTRY.items():
        r = cls().discover()
        results.append(r.to_dict())
        for g in r.missing_capabilities:
            if g.id == "browser_playwright" and g.status == "missing":
                missing_browser = True
    return {
        "ok": True,
        "engine": "Alpha Hunter — Opportunity Discovery Engine",
        "adapters_run": len(results),
        "results": results,
        "browser_status": (
            {"status": "missing", "need": "Playwright", "title": "Browser Automation"}
            if missing_browser
            else {"status": "ok_or_unused"}
        ),
        "law_ru": (
            "Это Opportunity Discovery Engine, не движок гарантированного заработка. "
            "Новый рынок = новый адаптер, без переписывания ядра."
        ),
    }
