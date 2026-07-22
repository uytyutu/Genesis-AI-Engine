"""Portal demo authentication directory (local / CEO path).

Seeds one ready Account so First Run can login without a separate Identity UI.
Uses existing Account · ActivationToken · PasswordCredential domains only.
"""

from __future__ import annotations

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.authentication_facade import InMemoryAuthenticationDirectory
from app.portal.password_credential import (
    complete_account_activation,
    create_primary_password,
)

ENGINE_ID = "portal_demo_directory_v1"

# Opaque pass-through secret (R4.1 — no hash infra yet).
DEMO_PORTAL_EMAIL = "client@virtus.local"
DEMO_PORTAL_PASSWORD = "demo-vector"


def build_demo_authentication_directory() -> InMemoryAuthenticationDirectory:
    account = new_account(
        email=DEMO_PORTAL_EMAIL,
        display_name="Vector Client",
        status="pending_activation",
    )
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated,
        password_hash=DEMO_PORTAL_PASSWORD,
        activation_token=used,
    )
    return InMemoryAuthenticationDirectory(
        accounts_by_email={ready.email: ready},
        credentials_by_account={ready.account_id: cred},
    )
