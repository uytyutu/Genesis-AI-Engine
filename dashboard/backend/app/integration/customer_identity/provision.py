"""Provision Digital Company on registration."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.integration.customer_identity.schema import (
    CustomerAccount,
    CustomerCard,
    DigitalCompany,
    MarketingConsent,
    WelcomeSession,
)
from app.integration.customer_identity.merge import merge_visitor_identity
from app.integration.customer_identity.store import CustomerIdentityStore
from app.integration.project_platform.service import ProjectPlatformService


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def platform_visitor_id(customer_id: str) -> str:
    return f"vc-{customer_id.replace('-', '')[:32]}"


class CustomerProvisioner:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._store = CustomerIdentityStore(memory_dir)
        self._projects = ProjectPlatformService(memory_dir)

    def provision(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        locale: str = "ru",
        country: str = "",
        prior_visitor_id: str | None = None,
    ) -> tuple[CustomerAccount, CustomerCard, DigitalCompany, WelcomeSession]:
        customer_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())
        now = _utc_now()
        vid = platform_visitor_id(customer_id)

        if prior_visitor_id:
            merge_visitor_identity(
                self._memory,
                from_visitor=prior_visitor_id,
                to_visitor=vid,
            )

        account = CustomerAccount(
            customer_id=customer_id,
            email=email,
            password_hash=password_hash,
            name=name.strip()[:120],
            email_verified=False,
            created_at=now,
            last_login_at=now,
            locale=locale[:8] or "ru",
            country=country[:64],
        )
        card = CustomerCard(
            customer_id=customer_id,
            name=account.name,
            email=email,
            locale=account.locale,
            country=account.country,
            tier="free",
            platform_visitor_id=vid,
            project_count=1,
            registered_at=now,
            last_activity_at=now,
            interests=[],
            gdpr_service_consent=True,
            marketing=MarketingConsent(),
        )
        company = DigitalCompany(
            company_id=company_id,
            customer_id=customer_id,
            name="Моя компания",
            platform_visitor_id=vid,
            document_vault_id=f"vault-{customer_id[:8]}",
            settings_id=f"settings-{customer_id[:8]}",
            created_at=now,
        )

        project = self._projects.activate_project(
            vid,
            title="Моя компания",
            service_id="website",
        )
        proj = project.get("project") or {}
        company.workspace_id = str(proj.get("workspace_id") or "")
        company.first_project_id = str(proj.get("project_id") or "")

        welcome = WelcomeSession(customer_id=customer_id, phase="greeting")

        self._store.save_account(account)
        self._store.save_card(card)
        self._store.save_company(company)
        self._store.save_welcome(welcome)

        return account, card, company, welcome
