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
from app.integration.customer_identity.schema import WelcomeSession
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
        return {
            "version": IDENTITY_VERSION,
            "name": account.name,
            "email": account.email,
            "email_verified": account.email_verified,
            "tier": card.tier if card else "free",
            "company_name": company.name if company else None,
            "headline": headline_ready(),
            "welcome": welcome_payload(welcome, name=account.name) if welcome else None,
            "platform_visitor_id": card.platform_visitor_id if card else None,
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
                "name": company.name if company else "Моя компания",
                "project": project_state,
            },
            "platform_visitor_id": card.platform_visitor_id if card else None,
        }
