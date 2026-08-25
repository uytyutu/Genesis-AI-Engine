"""Customer identity entities — internal names; client UI uses plain language."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
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
    """Internal support record — client UI never uses this class name."""

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
    # Public support key — assigned on registration (never expose DB UUID to clients).
    business_id: str = ""
    account_status: str = "active"
    company_display_name: str = ""
    support_notes: list[dict[str, Any]] = field(default_factory=list)

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
class BusinessContact:
    phone: str = ""
    email: str = ""
    whatsapp: str = ""
    website: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class BusinessAddress:
    street: str = ""
    city: str = ""
    postal_code: str = ""
    country: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class BusinessServiceItem:
    name: str = ""
    description: str = ""
    price_hint: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class BusinessSocials:
    instagram: str = ""
    facebook: str = ""
    linkedin: str = ""
    tiktok: str = ""
    youtube: str = ""
    other: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessMediaRefs:
    """Paths/URLs only — binaries live in media vault / Factory export."""

    logo_path: str = ""
    hero_refs: list[str] = field(default_factory=list)
    gallery_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessProfile:
    """Company facts SSOT — Enter once → Factory / Website / Workspace / Vector.

    Not payment. Not a second User. Giveaway and paid Order both attach here.
    """

    profile_id: str
    customer_id: str
    company_name: str = ""
    niche: str = ""
    description: str = ""
    contacts: BusinessContact = field(default_factory=BusinessContact)
    address: BusinessAddress = field(default_factory=BusinessAddress)
    services: list[BusinessServiceItem] = field(default_factory=list)
    socials: BusinessSocials = field(default_factory=BusinessSocials)
    media: BusinessMediaRefs = field(default_factory=BusinessMediaRefs)
    language: str = "de"
    market: str = "DE"
    digital_company_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    source: str = ""  # giveaway | order | workspace | import | ensure

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "customer_id": self.customer_id,
            "company_name": self.company_name,
            "niche": self.niche,
            "description": self.description,
            "contacts": self.contacts.to_dict(),
            "address": self.address.to_dict(),
            "services": [s.to_dict() for s in self.services],
            "socials": self.socials.to_dict(),
            "media": self.media.to_dict(),
            "language": self.language,
            "market": self.market,
            "digital_company_id": self.digital_company_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BusinessProfile | None:
        if not isinstance(data, dict):
            return None
        pid = str(data.get("profile_id") or "").strip()
        cid = str(data.get("customer_id") or "").strip()
        if not pid or not cid:
            return None

        def _sub(model: type, key: str):
            raw = data.get(key)
            if not isinstance(raw, dict):
                return model()
            known = {f.name for f in fields(model)}
            return model(**{k: v for k, v in raw.items() if k in known})

        services_raw = data.get("services") or []
        services: list[BusinessServiceItem] = []
        if isinstance(services_raw, list):
            for item in services_raw:
                if isinstance(item, dict):
                    known = {f.name for f in fields(BusinessServiceItem)}
                    services.append(
                        BusinessServiceItem(**{k: v for k, v in item.items() if k in known})
                    )
                elif isinstance(item, str) and item.strip():
                    services.append(BusinessServiceItem(name=item.strip()))

        socials = _sub(BusinessSocials, "socials")
        other = getattr(socials, "other", None)
        if not isinstance(other, dict):
            socials.other = {}

        media = _sub(BusinessMediaRefs, "media")
        if not isinstance(media.hero_refs, list):
            media.hero_refs = []
        if not isinstance(media.gallery_refs, list):
            media.gallery_refs = []

        return cls(
            profile_id=pid,
            customer_id=cid,
            company_name=str(data.get("company_name") or ""),
            niche=str(data.get("niche") or ""),
            description=str(data.get("description") or ""),
            contacts=_sub(BusinessContact, "contacts"),
            address=_sub(BusinessAddress, "address"),
            services=services,
            socials=socials,
            media=media,
            language=str(data.get("language") or "de")[:16] or "de",
            market=str(data.get("market") or "DE")[:8] or "DE",
            digital_company_id=str(data.get("digital_company_id") or ""),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
            source=str(data.get("source") or ""),
        )


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
