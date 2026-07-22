"""R4.6 — End-to-End User Journey orchestration.

Composes **existing** R3.12 / R4 components into one continuous path.
Does **not** invent domain rules, AuthN/AuthZ policy, or Session semantics.

```text
Website (+ Ownership)
        ↓
ActivationToken → Account activated
        ↓
Primary Password → Account ready
        ↓
Login → Session → Middleware → Authorization → Dashboard
        ↓
Logout → Anonymous
```
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.account import Account, new_account
from app.portal.activation_token import ActivationToken, activate_token, new_activation_token
from app.portal.authentication_facade import InMemoryAuthenticationDirectory
from app.portal.client import Client, new_client, website_for_client
from app.portal.deployment import Deployment, attach_deployment, new_deployment
from app.portal.ownership import WebsiteOwnership, grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.password_credential import (
    PasswordCredential,
    complete_account_activation,
    create_primary_password,
)
from app.portal.read_service import PortalCatalog
from app.portal.website import Website

ENGINE_ID = "portal_user_journey_v1"


@dataclass(frozen=True)
class PortalOwnerJourneyState:
    """Ready state for the Minimum Complete User Journey (test / wiring only)."""

    account: Account
    credential: PasswordCredential
    client: Client
    website: Website
    ownership: WebsiteOwnership
    deployment: Deployment
    password_material: str
    catalog: PortalCatalog
    auth_directory: InMemoryAuthenticationDirectory
    ownership_directory: InMemoryOwnershipDirectory


def build_published_owner_journey(
    *,
    email: str = "owner@ex.de",
    display_name: str = "Owner",
    business_name: str = "Demo GmbH",
    product_id: str = "journey-site-1",
    market_code: str = "DE",
    password_material: str = "journey-secret-opaque",
) -> PortalOwnerJourneyState:
    """Orchestrate publish-like Website + activate + password + ownership.

    Steps use only existing domain helpers — no new invariants.
    """
    # 1) Account created
    account = new_account(email=email, display_name=display_name)
    # 2) Activation token issued + consumed → activated
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    # 3) Primary password → ready
    ready, credential = create_primary_password(
        activated,
        password_hash=password_material,
        activation_token=used,
    )
    # 4) "Published" website (commercial Client + Website + Deployment)
    client = new_client(display_name=business_name, primary_email=email)
    site = website_for_client(
        client,
        product_id=product_id,
        market_code=market_code,
        status="published",
    )
    deployment = new_deployment(website=site, artifact_id=product_id, status="active")
    site = attach_deployment(site, deployment)
    # 5) Portal access via Ownership (never Account → Client)
    ownership = grant_website_ownership(ready, site)

    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={deployment.deployment_id: deployment},
        assets={},
        edit_sessions={},
    )
    auth_directory = InMemoryAuthenticationDirectory(
        accounts_by_email={ready.email: ready},
        credentials_by_account={ready.account_id: credential},
    )
    ownership_directory = InMemoryOwnershipDirectory(ownerships=[ownership])

    return PortalOwnerJourneyState(
        account=ready,
        credential=credential,
        client=client,
        website=site,
        ownership=ownership,
        deployment=deployment,
        password_material=password_material,
        catalog=catalog,
        auth_directory=auth_directory,
        ownership_directory=ownership_directory,
    )


def assert_activation_token_one_shot(token: ActivationToken) -> None:
    """Document invariant for journey tests — token already used."""
    assert token.status == "used"
