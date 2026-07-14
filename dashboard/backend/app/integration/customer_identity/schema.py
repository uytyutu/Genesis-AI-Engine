"""Customer identity entities — internal names; client UI uses plain language."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

WelcomePhase = Literal["greeting", "wizard", "personalized", "complete"]
WizardStep = Literal["occupation", "goal", "pace"]
InferredProfile = Literal["entrepreneur", "designer", "developer", "explorer"]

WIZARD_STEPS: tuple[WizardStep, ...] = ("occupation", "goal", "pace")

WIZARD_QUESTIONS_RU: dict[WizardStep, str] = {
    "occupation": "Чем вы занимаетесь?",
    "goal": "Для чего хотите использовать Virtus Core?",
    "pace": "Хотите сначала просто пообщаться или сразу перейти к делу?",
}

QUICK_ACTIONS_BY_PROFILE: dict[InferredProfile, list[dict[str, str]]] = {
    "entrepreneur": [
        {"id": "website", "label": "Создать сайт", "service_id": "website"},
        {"id": "business_plan", "label": "Создать бизнес-план", "service_id": "business_plan"},
        {"id": "crm", "label": "CRM", "service_id": "crm"},
        {"id": "automation", "label": "Автоматизация", "service_id": "automation"},
    ],
    "designer": [
        {"id": "portfolio", "label": "Портфолио", "service_id": "website"},
        {"id": "presentation", "label": "Презентация", "service_id": "presentation"},
        {"id": "images", "label": "Изображения", "service_id": "document_analysis"},
    ],
    "developer": [
        {"id": "app", "label": "Приложение", "service_id": "app"},
        {"id": "api", "label": "API", "service_id": "automation"},
        {"id": "architecture", "label": "Архитектура", "service_id": "business_plan"},
    ],
    "explorer": [
        {"id": "tour", "label": "Познакомиться с Vector", "service_id": "website"},
        {"id": "document", "label": "Загрузить документ", "service_id": "document_analysis"},
        {"id": "overview", "label": "Обзор возможностей", "service_id": "website"},
    ],
}


@dataclass
class MarketingConsent:
    news: bool = False
    features: bool = False
    offers: bool = False
    recommendations: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass
class CustomerAccount:
    customer_id: str
    email: str
    password_hash: str
    name: str
    email_verified: bool = False
    created_at: str = ""
    last_login_at: str = ""
    locale: str = "ru"
    country: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CustomerCard:
    """CRM record — not exposed to client under this name."""
    customer_id: str
    name: str
    email: str
    phone: str | None = None
    locale: str = "ru"
    country: str = ""
    tier: str = "free"
    platform_visitor_id: str = ""
    project_count: int = 0
    registered_at: str = ""
    last_activity_at: str = ""
    purchase_history: list[dict[str, Any]] = field(default_factory=list)
    subscription_history: list[dict[str, Any]] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    gdpr_service_consent: bool = True
    marketing: MarketingConsent = field(default_factory=MarketingConsent)
    devices: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class DigitalCompany:
    company_id: str
    customer_id: str
    name: str
    platform_visitor_id: str
    workspace_id: str = ""
    first_project_id: str = ""
    document_vault_id: str = ""
    settings_id: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WelcomeSession:
    customer_id: str
    phase: WelcomePhase = "greeting"
    wizard_step_index: int = 0
    wizard_answers: dict[str, str] = field(default_factory=dict)
    inferred_profile: InferredProfile = "explorer"
    quick_actions: list[dict[str, str]] = field(default_factory=list)
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
