"""Legal entity — owner data for document generation (Legal Foundation Interview)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class OperatorInfo:
    legal_form: str = ""
    full_name: str = ""
    trade_name: str = "Virtus Core"
    address_street: str = ""
    address_zip: str = ""
    address_city: str = ""
    address_country: str = "DE"
    email: str = ""
    phone: str = ""
    website: str = ""
    vat_id: str = ""
    handelsregister: str = ""
    register_court: str = ""
    managing_director: str = ""


@dataclass
class DataProcessingInfo:
    hosting_providers: list[str] = field(default_factory=list)
    payment_providers: list[str] = field(default_factory=list)
    email_providers: list[str] = field(default_factory=list)
    ai_providers: list[str] = field(default_factory=list)
    analytics_providers: list[str] = field(default_factory=list)
    data_location: str = "EU / Deutschland"
    retention_project_days: int = 365
    retention_logs_days: int = 90
    retention_order_days: int = 2555  # ~7 years tax
    deletion_on_request_days: int = 30
    dpo_email: str = ""
    supervisory_authority: str = ""
    never_sold_to_third_parties: bool = True


@dataclass
class CookiePolicyInfo:
    essential: list[str] = field(default_factory=lambda: ["Sitzung / Session", "Sicherheit / CSRF"])
    functional: list[str] = field(default_factory=lambda: ["Sprache / Locale"])
    analytics: list[str] = field(default_factory=list)
    marketing: list[str] = field(default_factory=list)


@dataclass
class LegalEntityConfig:
    version: int = 1
    updated_at: str = ""
    operator: OperatorInfo = field(default_factory=OperatorInfo)
    data_processing: DataProcessingInfo = field(default_factory=DataProcessingInfo)
    cookies: CookiePolicyInfo = field(default_factory=CookiePolicyInfo)
    documents_last_review: str = "2026-07"
    interview_completed: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> LegalEntityConfig:
        if not data:
            return cls()
        op = data.get("operator") or {}
        dp = data.get("data_processing") or {}
        ck = data.get("cookies") or {}
        return cls(
            version=int(data.get("version") or 1),
            updated_at=str(data.get("updated_at") or ""),
            operator=OperatorInfo(
                legal_form=str(op.get("legal_form") or ""),
                full_name=str(op.get("full_name") or ""),
                trade_name=str(op.get("trade_name") or "Virtus Core"),
                address_street=str(op.get("address_street") or ""),
                address_zip=str(op.get("address_zip") or ""),
                address_city=str(op.get("address_city") or ""),
                address_country=str(op.get("address_country") or "DE"),
                email=str(op.get("email") or ""),
                phone=str(op.get("phone") or ""),
                website=str(op.get("website") or ""),
                vat_id=str(op.get("vat_id") or ""),
                handelsregister=str(op.get("handelsregister") or ""),
                register_court=str(op.get("register_court") or ""),
                managing_director=str(op.get("managing_director") or ""),
            ),
            data_processing=DataProcessingInfo(
                hosting_providers=list(dp.get("hosting_providers") or []),
                payment_providers=list(dp.get("payment_providers") or []),
                email_providers=list(dp.get("email_providers") or []),
                ai_providers=list(dp.get("ai_providers") or []),
                analytics_providers=list(dp.get("analytics_providers") or []),
                data_location=str(dp.get("data_location") or "EU / Deutschland"),
                retention_project_days=int(dp.get("retention_project_days") or 365),
                retention_logs_days=int(dp.get("retention_logs_days") or 90),
                retention_order_days=int(dp.get("retention_order_days") or 2555),
                deletion_on_request_days=int(dp.get("deletion_on_request_days") or 30),
                dpo_email=str(dp.get("dpo_email") or ""),
                supervisory_authority=str(dp.get("supervisory_authority") or ""),
                never_sold_to_third_parties=bool(dp.get("never_sold_to_third_parties", True)),
            ),
            cookies=CookiePolicyInfo(
                essential=list(ck.get("essential") or ["Sitzung / Session", "Sicherheit / CSRF"]),
                functional=list(ck.get("functional") or ["Sprache / Locale"]),
                analytics=list(ck.get("analytics") or []),
                marketing=list(ck.get("marketing") or []),
            ),
            documents_last_review=str(data.get("documents_last_review") or "2026-07"),
            interview_completed=bool(data.get("interview_completed")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def formatted_address(self) -> str:
        parts = [
            self.operator.address_street,
            f"{self.operator.address_zip} {self.operator.address_city}".strip(),
            self.operator.address_country,
        ]
        return "\n".join(p for p in parts if p.strip())

    def missing_impressum_fields(self) -> list[str]:
        missing: list[str] = []
        op = self.operator
        for key, val in (
            ("operator.full_name", op.full_name),
            ("operator.address_street", op.address_street),
            ("operator.address_zip", op.address_zip),
            ("operator.address_city", op.address_city),
            ("operator.email", op.email),
        ):
            if not str(val).strip():
                missing.append(key)
        return missing

    def missing_datenschutz_fields(self) -> list[str]:
        missing = list(self.missing_impressum_fields())
        if not self.data_processing.data_location.strip():
            missing.append("data_processing.data_location")
        return missing

    def is_impressum_publishable(self) -> bool:
        return not self.missing_impressum_fields()

    def is_datenschutz_publishable(self) -> bool:
        return not self.missing_datenschutz_fields()


DOCUMENT_IMPRESSUM = "impressum"
DOCUMENT_DATENSCHUTZ = "datenschutz"
DOCUMENT_AGB = "agb"
DOCUMENT_WIDERRUF = "widerruf"
DOCUMENT_COOKIES = "cookies"
DOCUMENT_AI_DISCLAIMER = "ai_disclaimer"
DOCUMENT_INTELLECTUAL_PROPERTY = "intellectual_property"

ALL_LEGAL_DOCUMENTS: tuple[str, ...] = (
    DOCUMENT_IMPRESSUM,
    DOCUMENT_DATENSCHUTZ,
    DOCUMENT_AGB,
    DOCUMENT_WIDERRUF,
    DOCUMENT_COOKIES,
    DOCUMENT_AI_DISCLAIMER,
    DOCUMENT_INTELLECTUAL_PROPERTY,
)

DOCUMENT_LABELS: dict[str, dict[str, str]] = {
    DOCUMENT_IMPRESSUM: {"de": "Impressum", "ru": "Impressum"},
    DOCUMENT_DATENSCHUTZ: {"de": "Datenschutzerklärung", "ru": "Политика конфиденциальности"},
    DOCUMENT_AGB: {"de": "AGB", "ru": "Условия использования"},
    DOCUMENT_WIDERRUF: {"de": "Widerrufsbelehrung", "ru": "Право отмены"},
    DOCUMENT_COOKIES: {"de": "Cookie-Richtlinie", "ru": "Политика cookies"},
    DOCUMENT_AI_DISCLAIMER: {"de": "KI-Hinweis", "ru": "Оговорка об ИИ"},
    DOCUMENT_INTELLECTUAL_PROPERTY: {"de": "Urheberrecht & Nutzungsrechte", "ru": "Интеллектуальная собственность"},
}
