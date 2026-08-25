"""Customer identity orchestration — register, login, welcome, merge."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.integration.customer_identity.auth import (
    hash_password,
    issue_client_token,
    validate_email,
    verify_password,
)
from app.integration.customer_identity.merge import merge_visitor_identity
from app.integration.customer_identity.provision import CustomerProvisioner
from app.integration.customer_identity.schema import (
    BusinessAddress,
    BusinessContact,
    BusinessMediaRefs,
    BusinessProfile,
    BusinessServiceItem,
    BusinessSocials,
    WelcomeSession,
)
from app.integration.customer_identity.store import CustomerIdentityStore
from app.integration.customer_identity.welcome import (
    advance_welcome,
    apply_wizard_answer,
    headline_ready,
    welcome_payload,
)
from app.integration.project_platform.service import ProjectPlatformService

IDENTITY_VERSION = "universal-identity-m2-v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CustomerIdentityService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._store = CustomerIdentityStore(memory_dir)
        self._provisioner = CustomerProvisioner(memory_dir)

    def start_registration(
        self,
        *,
        name: str,
        email: str,
        password: str,
        locale: str = "en",
        country: str = "",
        prior_visitor_id: str | None = None,
    ) -> dict[str, Any]:
        """Step 1 — validate + email a one-time code. Account is not created yet."""
        import time

        from app.integration.customer_identity.registration_otp import (
            OTP_TTL_SEC,
            PendingRegistration,
            _code_hash,
            generate_otp_code,
            save_pending,
            send_registration_code,
        )

        clean_name = (name or "").strip()
        if len(clean_name) < 2:
            raise HTTPException(status_code=400, detail="name_required")
        if len(password or "") < 8:
            raise HTTPException(status_code=400, detail="password_too_short")
        normalized_email = validate_email(email)
        if self._store.find_customer_by_email(normalized_email):
            raise HTTPException(status_code=409, detail="email_already_registered")

        code = generate_otp_code()
        pending = PendingRegistration(
            email=normalized_email,
            name=clean_name,
            password_hash=hash_password(password),
            locale=(locale or "en")[:8],
            country=(country or "")[:64],
            code_hash=_code_hash(code),
            created_at=time.time(),
            visitor_id=prior_visitor_id,
        )
        save_pending(self._memory, pending)
        delivery = send_registration_code(
            to=normalized_email,
            code=code,
            name=clean_name,
            locale=locale,
        )
        out: dict[str, Any] = {
            "ok": True,
            "email": normalized_email,
            "expires_in_sec": OTP_TTL_SEC,
            "delivery": delivery.get("delivery") or "email",
            "next": "confirm_code",
        }
        if delivery.get("code"):
            out["dev_code"] = delivery["code"]
        return out

    def confirm_registration(self, *, email: str, code: str) -> dict[str, Any]:
        """Step 2 — verify OTP, create personal office account."""
        from app.integration.customer_identity.registration_otp import (
            delete_pending,
            verify_pending_code,
        )

        normalized_email = validate_email(email)
        pending = verify_pending_code(
            self._memory, email=normalized_email, code=(code or "").strip()
        )
        if self._store.find_customer_by_email(normalized_email):
            delete_pending(self._memory, normalized_email)
            raise HTTPException(status_code=409, detail="email_already_registered")

        account, card, company, welcome = self._provisioner.provision(
            name=pending.name,
            email=normalized_email,
            password_hash=pending.password_hash,
            locale=pending.locale,
            country=pending.country,
            prior_visitor_id=pending.visitor_id,
        )
        account.email_verified = True
        self._store.save_account(account)
        delete_pending(self._memory, normalized_email)
        token = issue_client_token(customer_id=account.customer_id, email=account.email)
        try:
            from app.integration.sales_order_service import SalesOrderService
            from app.integration.factory_intent_service import FactoryIntentService
            from app.factory.factory_service import FactoryService

            factory = FactoryService(memory_dir=self._memory)
            intent = FactoryIntentService(memory_dir=self._memory, factory=factory)
            sales = SalesOrderService(self._memory, intent)
            sales.attach_customer_by_email(
                customer_id=account.customer_id, email=account.email
            )
        except Exception:
            pass
        return self._session_response(
            token=token,
            account=account,
            card=card,
            company=company,
            welcome=welcome,
        )

    def register(
        self,
        *,
        name: str,
        email: str,
        password: str,
        locale: str = "ru",
        country: str = "",
        prior_visitor_id: str | None = None,
    ) -> dict[str, Any]:
        """Direct register (tests / internal). Public HTTP uses start + confirm OTP."""
        clean_name = (name or "").strip()
        if len(clean_name) < 2:
            raise HTTPException(status_code=400, detail="name_required")
        if len(password or "") < 8:
            raise HTTPException(status_code=400, detail="password_too_short")
        normalized_email = validate_email(email)
        if self._store.find_customer_by_email(normalized_email):
            raise HTTPException(status_code=409, detail="email_already_registered")

        account, card, company, welcome = self._provisioner.provision(
            name=clean_name,
            email=normalized_email,
            password_hash=hash_password(password),
            locale=locale,
            country=country,
            prior_visitor_id=prior_visitor_id,
        )
        token = issue_client_token(customer_id=account.customer_id, email=account.email)
        try:
            from app.integration.sales_order_service import SalesOrderService
            from app.integration.factory_intent_service import FactoryIntentService
            from app.factory.factory_service import FactoryService

            factory = FactoryService(memory_dir=self._memory)
            intent = FactoryIntentService(memory_dir=self._memory, factory=factory)
            sales = SalesOrderService(self._memory, intent)
            sales.attach_customer_by_email(
                customer_id=account.customer_id, email=account.email
            )
        except Exception:
            pass
        return self._session_response(
            token=token,
            account=account,
            card=card,
            company=company,
            welcome=welcome,
        )

    def login(self, *, email: str, password: str) -> dict[str, Any]:
        normalized_email = validate_email(email)
        customer_id = self._store.find_customer_by_email(normalized_email)
        if not customer_id:
            raise HTTPException(status_code=401, detail="invalid_credentials")
        account = self._store.load_account(customer_id)
        if not account or not verify_password(password, account.password_hash):
            raise HTTPException(status_code=401, detail="invalid_credentials")
        account.last_login_at = _utc_now()
        self._store.save_account(account)
        card = self._store.load_card(customer_id)
        company = self._store.load_company_by_customer(customer_id)
        welcome = self._store.load_welcome(customer_id) or WelcomeSession(customer_id=customer_id)
        if card:
            card.last_activity_at = _utc_now()
            self._store.save_card(card)
        token = issue_client_token(customer_id=account.customer_id, email=account.email)
        try:
            from app.integration.sales_order_service import SalesOrderService
            from app.integration.factory_intent_service import FactoryIntentService
            from app.factory.factory_service import FactoryService

            factory = FactoryService(memory_dir=self._memory)
            intent = FactoryIntentService(memory_dir=self._memory, factory=factory)
            sales = SalesOrderService(self._memory, intent)
            sales.attach_customer_by_email(
                customer_id=account.customer_id, email=account.email
            )
        except Exception:
            pass
        return self._session_response(
            token=token,
            account=account,
            card=card,
            company=company,
            welcome=welcome,
        )

    def me(self, customer_id: str) -> dict[str, Any]:
        account = self._store.load_account(customer_id)
        if not account:
            raise HTTPException(status_code=404, detail="customer_not_found")
        card = self._store.load_card(customer_id)
        company = self._store.load_company_by_customer(customer_id)
        welcome = self._store.load_welcome(customer_id)
        business_id = ""
        if card:
            from app.integration.customer_identity.support_center import SupportCenterService

            card = SupportCenterService(self._memory).ensure_business_id(card)
            business_id = card.business_id
        return {
            "version": IDENTITY_VERSION,
            "customer_id": account.customer_id,
            "business_id": business_id,
            "name": account.name,
            "email": account.email,
            "email_verified": account.email_verified,
            "tier": card.tier if card else "free",
            "company_name": company.name if company else None,
            "company_display_name": (card.company_display_name if card else "")
            or (company.name if company else None),
            "headline": headline_ready(),
            "welcome": welcome_payload(welcome, name=account.name) if welcome else None,
            "platform_visitor_id": card.platform_visitor_id if card else None,
            "gift_account": bool(getattr(card, "gift_account", False)) if card else False,
            "gift_unlimited": bool(getattr(card, "gift_unlimited", False) or getattr(card, "unlimited", False))
            if card
            else False,
            "unlimited": bool(getattr(card, "unlimited", False) or getattr(card, "gift_unlimited", False))
            if card
            else False,
            "workspace_mode": str(getattr(card, "workspace_mode", "standard") or "standard")
            if card
            else "standard",
            "primary_niche": str(getattr(card, "primary_niche", "") or "") if card else "",
            "phone": (card.phone if card else None) or None,
            "business_profile": self.business_profile_read(customer_id),
            "company_profile": {
                "company_name": (card.company_display_name if card else "")
                or (company.name if company else "")
                or "",
                "email": account.email,
                "phone": (card.phone if card else None) or "",
                "primary_niche": str(getattr(card, "primary_niche", "") or "") if card else "",
                "complete": bool(
                    (
                        (card.company_display_name if card else "")
                        or (company.name if company else "")
                    )
                    and account.email
                ),
            },
            "forced_setup": False,
        }

    def get_welcome(self, customer_id: str) -> dict[str, Any]:
        account = self._store.load_account(customer_id)
        if not account:
            raise HTTPException(status_code=404, detail="customer_not_found")
        welcome = self._store.load_welcome(customer_id)
        if not welcome:
            welcome = WelcomeSession(customer_id=customer_id, phase="greeting")
            self._store.save_welcome(welcome)
        return welcome_payload(welcome, name=account.name)

    def advance_welcome(self, customer_id: str) -> dict[str, Any]:
        account = self._store.load_account(customer_id)
        if not account:
            raise HTTPException(status_code=404, detail="customer_not_found")
        welcome = self._store.load_welcome(customer_id)
        if not welcome:
            welcome = WelcomeSession(customer_id=customer_id, phase="greeting")
        welcome = advance_welcome(welcome)
        if welcome.phase == "complete":
            welcome.completed_at = _utc_now()
        self._store.save_welcome(welcome)
        self._touch_card(customer_id)
        return welcome_payload(welcome, name=account.name)

    def answer_welcome(
        self,
        customer_id: str,
        *,
        answer: str,
        skip: bool = False,
    ) -> dict[str, Any]:
        account = self._store.load_account(customer_id)
        if not account:
            raise HTTPException(status_code=404, detail="customer_not_found")
        welcome = self._store.load_welcome(customer_id)
        if not welcome:
            raise HTTPException(status_code=400, detail="welcome_not_started")
        if welcome.phase == "greeting":
            welcome = advance_welcome(welcome)
        if skip and welcome.phase == "wizard":
            welcome.inferred_profile = "explorer"
            welcome.quick_actions = welcome.quick_actions or []
            from app.integration.customer_identity.schema import QUICK_ACTIONS_BY_PROFILE

            welcome.quick_actions = list(QUICK_ACTIONS_BY_PROFILE["explorer"])
            welcome.phase = "personalized"
        else:
            welcome = apply_wizard_answer(welcome, answer or "позже")
        if welcome.phase == "complete":
            welcome.completed_at = _utc_now()
        self._store.save_welcome(welcome)
        self._update_interests(customer_id, welcome)
        self._touch_card(customer_id)
        return welcome_payload(welcome, name=account.name)

    def merge_visitor(self, customer_id: str, *, visitor_id: str) -> dict[str, str]:
        card = self._store.load_card(customer_id)
        if not card or not card.platform_visitor_id:
            raise HTTPException(status_code=404, detail="customer_not_found")
        result = merge_visitor_identity(
            self._memory,
            from_visitor=visitor_id,
            to_visitor=card.platform_visitor_id,
        )
        self._touch_card(customer_id)
        return {
            "ok": "true",
            "platform_visitor_id": card.platform_visitor_id,
            "merge": result,
        }

    def get_business_profile(self, customer_id: str) -> dict[str, Any] | None:
        """Business Profile SSOT — read primary profile for this User (or None)."""
        if not self._store.load_account(customer_id) and not self._store.load_card(customer_id):
            raise HTTPException(status_code=404, detail="customer_not_found")
        profile = self._store.load_business_profile_by_customer(customer_id)
        return profile.to_dict() if profile else None

    def business_profile_read(self, customer_id: str) -> dict[str, Any]:
        """Honest read API payload — does not create a profile."""
        profile = self.get_business_profile(customer_id)
        return {
            "ok": True,
            "has_profile": profile is not None,
            "profile": profile,
            "ssot": "customer_identity.business_profile",
            "note": (
                None
                if profile
                else "Business Profile not filled yet — Order/Giveaway should create via upsert, not a second entity."
            ),
        }

    def ensure_business_profile(self, customer_id: str) -> dict[str, Any]:
        """Idempotent: one primary Business Profile per User (Giveaway + Order share it)."""
        if not self._store.load_account(customer_id) and not self._store.load_card(customer_id):
            raise HTTPException(status_code=404, detail="customer_not_found")
        existing = self._store.load_business_profile_by_customer(customer_id)
        if existing:
            return existing.to_dict()

        import uuid

        company = self._store.load_company_by_customer(customer_id)
        card = self._store.load_card(customer_id)
        account = self._store.load_account(customer_id)
        now = _utc_now()
        name = (
            (card.company_display_name if card else "")
            or (company.name if company else "")
            or ""
        )
        profile = BusinessProfile(
            profile_id=str(uuid.uuid4()),
            customer_id=customer_id,
            company_name=name,
            niche=str(getattr(card, "primary_niche", "") or "") if card else "",
            contacts=BusinessContact(
                email=(account.email if account else "") or (card.email if card else "") or "",
                phone=(card.phone if card else "") or "",
            ),
            language=(account.locale if account and account.locale else "de")[:16] or "de",
            market=(account.country if account and account.country else "DE")[:8] or "DE",
            digital_company_id=company.company_id if company else "",
            created_at=now,
            updated_at=now,
            source="ensure",
        )
        self._store.save_business_profile(profile)
        return profile.to_dict()

    def upsert_business_profile(
        self,
        customer_id: str,
        patch: dict[str, Any] | None = None,
        *,
        source: str = "",
    ) -> dict[str, Any]:
        """Merge patch into primary Business Profile. Enter once → use everywhere."""
        data = self.ensure_business_profile(customer_id)
        profile = BusinessProfile.from_dict(data)
        if not profile:
            raise HTTPException(status_code=500, detail="business_profile_corrupt")

        body = patch if isinstance(patch, dict) else {}

        if "company_name" in body:
            profile.company_name = str(body.get("company_name") or "").strip()[:200]
        if "niche" in body:
            profile.niche = str(body.get("niche") or "").strip()[:120]
        if "description" in body:
            profile.description = str(body.get("description") or "").strip()[:8000]
        if "language" in body:
            profile.language = str(body.get("language") or profile.language).strip()[:16] or profile.language
        if "market" in body:
            profile.market = str(body.get("market") or profile.market).strip()[:8] or profile.market
        if "digital_company_id" in body:
            profile.digital_company_id = str(body.get("digital_company_id") or "").strip()[:80]

        if isinstance(body.get("contacts"), dict):
            c = body["contacts"]
            profile.contacts = BusinessContact(
                phone=str(c.get("phone", profile.contacts.phone) or "")[:64],
                email=str(c.get("email", profile.contacts.email) or "")[:200],
                whatsapp=str(c.get("whatsapp", profile.contacts.whatsapp) or "")[:64],
                website=str(c.get("website", profile.contacts.website) or "")[:300],
            )
        if isinstance(body.get("address"), dict):
            a = body["address"]
            profile.address = BusinessAddress(
                street=str(a.get("street", profile.address.street) or "")[:200],
                city=str(a.get("city", profile.address.city) or "")[:120],
                postal_code=str(a.get("postal_code", profile.address.postal_code) or "")[:32],
                country=str(a.get("country", profile.address.country) or "")[:8],
            )
        if "services" in body and isinstance(body.get("services"), list):
            services: list[BusinessServiceItem] = []
            for item in body["services"][:40]:
                if isinstance(item, dict):
                    services.append(
                        BusinessServiceItem(
                            name=str(item.get("name") or "").strip()[:160],
                            description=str(item.get("description") or "").strip()[:2000],
                            price_hint=str(item.get("price_hint") or "").strip()[:80],
                        )
                    )
                elif isinstance(item, str) and item.strip():
                    services.append(BusinessServiceItem(name=item.strip()[:160]))
            profile.services = [s for s in services if s.name]
        if isinstance(body.get("socials"), dict):
            s = body["socials"]
            other = s.get("other", profile.socials.other)
            if not isinstance(other, dict):
                other = {}
            profile.socials = BusinessSocials(
                instagram=str(s.get("instagram", profile.socials.instagram) or "")[:200],
                facebook=str(s.get("facebook", profile.socials.facebook) or "")[:200],
                linkedin=str(s.get("linkedin", profile.socials.linkedin) or "")[:200],
                tiktok=str(s.get("tiktok", profile.socials.tiktok) or "")[:200],
                youtube=str(s.get("youtube", profile.socials.youtube) or "")[:200],
                other={str(k)[:64]: str(v)[:300] for k, v in list(other.items())[:20]},
            )
        if isinstance(body.get("media"), dict):
            m = body["media"]
            heroes = m.get("hero_refs", profile.media.hero_refs)
            gallery = m.get("gallery_refs", profile.media.gallery_refs)
            if not isinstance(heroes, list):
                heroes = profile.media.hero_refs
            if not isinstance(gallery, list):
                gallery = profile.media.gallery_refs
            profile.media = BusinessMediaRefs(
                logo_path=str(m.get("logo_path", profile.media.logo_path) or "")[:500],
                hero_refs=[str(x)[:500] for x in heroes[:12]],
                gallery_refs=[str(x)[:500] for x in gallery[:40]],
            )

        if source:
            profile.source = str(source)[:40]
        profile.updated_at = _utc_now()
        self._store.save_business_profile(profile)

        # Mirror display name onto support card — not a second SSOT, just Owner search hint
        if profile.company_name:
            card = self._store.load_card(customer_id)
            if card and card.company_display_name != profile.company_name:
                card.company_display_name = profile.company_name
                self._store.save_card(card)

        self._touch_card(customer_id)
        return profile.to_dict()

    def _touch_card(self, customer_id: str) -> None:
        card = self._store.load_card(customer_id)
        if card:
            card.last_activity_at = _utc_now()
            self._store.save_card(card)

    def _update_interests(self, customer_id: str, welcome: WelcomeSession) -> None:
        card = self._store.load_card(customer_id)
        if not card:
            return
        interests: list[str] = []
        if welcome.inferred_profile:
            interests.append(welcome.inferred_profile)
        for val in welcome.wizard_answers.values():
            if val and val not in interests:
                interests.append(val[:80])
        card.interests = interests[:12]
        self._store.save_card(card)

    def _session_response(
        self,
        *,
        token: str,
        account,
        card,
        company,
        welcome: WelcomeSession,
    ) -> dict[str, Any]:
        project_state = None
        if card and card.platform_visitor_id:
            project_state = ProjectPlatformService(self._memory).get_for_visitor(
                card.platform_visitor_id,
                locale=account.locale,
            )
        return {
            "version": IDENTITY_VERSION,
            "token": token,
            "name": account.name,
            "email": account.email,
            "headline": headline_ready(),
            "welcome": welcome_payload(welcome, name=account.name),
            "company": {
                "name": company.name if company else "Mein Unternehmen",
                "project": project_state,
            },
            "platform_visitor_id": card.platform_visitor_id if card else None,
        }
