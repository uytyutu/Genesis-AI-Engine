"""R4.1 — AuthenticationFacade (HTTP → Domain).

Looks up Account + PasswordCredential, calls ``authenticate``,
returns only a boolean. Never exposes ``failure_reason``.
Never creates Session / Cookie / JWT.

Presented secret is passed through as opaque material for the domain
(``presented_password_hash``). Real password hashing is infrastructure
in a later slice — not R4.1.

Architecture note: this Facade is the **sole application entry** for
credential verification. Future login channels (magic link, SSO, Google,
Microsoft) should converge here — not invent parallel paths into Domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.portal.account import Account
from app.portal.authentication import authenticate
from app.portal.password_credential import PasswordCredential

ENGINE_ID = "authentication_facade_v1"


class AuthenticationDirectory(Protocol):
    """Read-only lookup for login / session resolution — not a session store."""

    def find_account_by_email(self, email: str) -> Account | None: ...

    def find_account_by_id(self, account_id: str) -> Account | None: ...

    def find_credential(self, account_id: str) -> PasswordCredential | None: ...


@dataclass
class InMemoryAuthenticationDirectory:
    """Test / bootstrap directory. Not persistence."""

    accounts_by_email: dict[str, Account]
    credentials_by_account: dict[str, PasswordCredential]

    def find_account_by_email(self, email: str) -> Account | None:
        return self.accounts_by_email.get(email.strip().lower())

    def find_account_by_id(self, account_id: str) -> Account | None:
        for account in self.accounts_by_email.values():
            if account.account_id == account_id:
                return account
        return None

    def find_credential(self, account_id: str) -> PasswordCredential | None:
        return self.credentials_by_account.get(account_id)

    def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str = "",
    ) -> str:
        """Create ready account + credential. Raises ValueError on conflict/invalid."""
        from app.portal.account import new_account
        from app.portal.activation_token import activate_token, new_activation_token
        from app.portal.password_credential import (
            complete_account_activation,
            create_primary_password,
        )

        key = email.strip().lower()
        if not key or "@" not in key:
            raise ValueError("invalid_email")
        secret = (password or "").strip()
        if len(secret) < 6:
            raise ValueError("password_too_short")
        if key in self.accounts_by_email:
            raise ValueError("email_already_registered")
        name = (display_name or "").strip() or key.split("@")[0]
        account = new_account(
            email=key,
            display_name=name,
            status="pending_activation",
        )
        token = activate_token(new_activation_token(account))
        activated, used = complete_account_activation(account, token)
        ready, cred = create_primary_password(
            activated,
            password_hash=secret,
            activation_token=used,
        )
        self.accounts_by_email[ready.email] = ready
        self.credentials_by_account[ready.account_id] = cred
        return ready.account_id


class AuthenticationFacade:
    """Thin use-case entry: email + secret → account_id or None."""

    def __init__(self, directory: AuthenticationDirectory) -> None:
        self._directory = directory

    def login(self, *, email: str, password: str) -> str | None:
        """Return account_id when authenticated; else None.

        Does not create sessions, set cookies, mint tokens, or return failure reasons.
        """
        account = self._directory.find_account_by_email(email)
        if account is None:
            return None
        credential = self._directory.find_credential(account.account_id)
        # Identity pass-through until hash infra exists (R4.1 — no hashing).
        _attempt, result = authenticate(
            account,
            credential,
            presented_password_hash=password,
        )
        if not result.is_authenticated:
            return None
        return account.account_id

    def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str = "",
    ) -> str:
        """Register a new account. Requires directory with ``register``."""
        register_fn = getattr(self._directory, "register", None)
        if not callable(register_fn):
            raise ValueError("registration_unavailable")
        return str(
            register_fn(email=email, password=password, display_name=display_name)
        )


def empty_authentication_directory() -> InMemoryAuthenticationDirectory:
    return InMemoryAuthenticationDirectory(
        accounts_by_email={},
        credentials_by_account={},
    )
