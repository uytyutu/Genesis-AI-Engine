"""Stripe Connect OAuth for shop merchants (Standard accounts).

Buyer money goes to the merchant's Stripe account — Virtus never receives shop funds.
Platform uses STRIPE_SECRET_KEY + Stripe-Account header for later Direct Charges.

Env:
  STRIPE_CONNECT_CLIENT_ID=ca_...
  STRIPE_SECRET_KEY=sk_...   (platform secret; used as client_secret for token exchange)
  STRIPE_CONNECT_REDIRECT_URI=optional override
  GENESIS_STRIPE_CONNECT_MOCK=1  — local/QA without real Stripe Connect app
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integration.payment_checkout_service import _resolve_stripe_secret

logger = logging.getLogger("genesis.stripe_connect")

_AUTH_URL = "https://connect.stripe.com/oauth/authorize"
_TOKEN_URL = "https://connect.stripe.com/oauth/token"
_DEAUTH_URL = "https://connect.stripe.com/oauth/deauthorize"
_ACCOUNT_URL = "https://api.stripe.com/v1/accounts"

_oauth_states: dict[str, dict[str, Any]] = {}
_STATE_TTL_SEC = 900


def _client_id() -> str:
    return os.getenv("STRIPE_CONNECT_CLIENT_ID", "").strip()


def mock_enabled() -> bool:
    return os.getenv("GENESIS_STRIPE_CONNECT_MOCK", "").strip() == "1"


def oauth_client_ready() -> bool:
    if mock_enabled():
        return True
    return bool(_client_id() and _resolve_stripe_secret())


def default_redirect_uri(public_api_base: str) -> str:
    override = os.getenv("STRIPE_CONNECT_REDIRECT_URI", "").strip()
    if override:
        return override
    base = public_api_base.rstrip("/")
    return f"{base}/api/client/stores/stripe/oauth/callback"


def frontend_return_url(order_id: str, *, public_frontend_base: str = "") -> str:
    base = (
        public_frontend_base
        or os.getenv("GENESIS_FRONTEND_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or "http://localhost:3000"
    ).rstrip("/")
    oid = (order_id or "").strip()
    return f"{base}/client/stores/{oid}/admin?section=payments&stripe=connected"


def create_oauth_state(*, order_id: str, return_url: str | None = None) -> str:
    now = time.time()
    expired = [k for k, row in _oauth_states.items() if now - float(row.get("ts") or 0) > _STATE_TTL_SEC]
    for k in expired:
        _oauth_states.pop(k, None)
    state = secrets.token_urlsafe(24)
    _oauth_states[state] = {
        "order_id": str(order_id).strip(),
        "return_url": (return_url or "").strip() or None,
        "ts": now,
    }
    return state


def consume_oauth_state(state: str) -> dict[str, Any] | None:
    row = _oauth_states.pop(state or "", None)
    if not row:
        return None
    if time.time() - float(row.get("ts") or 0) > _STATE_TTL_SEC:
        return None
    return row


def authorization_url(*, redirect_uri: str, state: str) -> str:
    if not oauth_client_ready():
        raise ValueError("stripe_connect_not_configured")
    if mock_enabled():
        # Caller should short-circuit mock start; URL unused in mock path.
        return f"{_AUTH_URL}?{urlencode({'state': state, 'mock': '1'})}"
    params = {
        "response_type": "code",
        "client_id": _client_id(),
        "scope": "read_write",
        "state": state,
        "redirect_uri": redirect_uri,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def exchange_code(*, code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange OAuth code for connected account credentials."""
    if mock_enabled():
        acct = f"acct_mock_{(code or 'demo')[-12:]}".replace("-", "")[:24]
        if len(acct) < 12:
            acct = "acct_mock_demo01"
        return {
            "ok": True,
            "stripe_user_id": acct,
            "livemode": False,
            "scope": "read_write",
            "stripe_publishable_key": "pk_test_mock",
            "access_token_present": True,
            "mock": True,
        }
    if not oauth_client_ready():
        return {"ok": False, "reason": "stripe_connect_not_configured"}
    if not (code or "").strip():
        return {"ok": False, "reason": "missing_code"}
    secret = _resolve_stripe_secret()
    with httpx.Client(timeout=30.0) as client:
        res = client.post(
            _TOKEN_URL,
            data={
                "client_secret": secret,
                "code": code.strip(),
                "grant_type": "authorization_code",
                # redirect_uri optional for Stripe but keep for parity with dashboard config
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if res.status_code >= 400:
        logger.warning("stripe connect token exchange failed status=%s", res.status_code)
        return {
            "ok": False,
            "reason": f"token_error:{res.status_code}",
            "detail": (res.text or "")[:240],
        }
    data = res.json() if res.content else {}
    stripe_user_id = str(data.get("stripe_user_id") or "").strip()
    if not stripe_user_id.startswith("acct_"):
        return {"ok": False, "reason": "missing_stripe_user_id", "detail": str(data)[:200]}
    return {
        "ok": True,
        "stripe_user_id": stripe_user_id,
        "livemode": bool(data.get("livemode")),
        "scope": str(data.get("scope") or "read_write"),
        "stripe_publishable_key": str(data.get("stripe_publishable_key") or "").strip() or None,
        "access_token_present": bool(str(data.get("access_token") or "").strip()),
        "refresh_token_present": bool(str(data.get("refresh_token") or "").strip()),
        "mock": False,
    }


def deauthorize(*, stripe_user_id: str) -> dict[str, Any]:
    acct = (stripe_user_id or "").strip()
    if not acct.startswith("acct_"):
        return {"ok": False, "reason": "invalid_account"}
    if mock_enabled() or acct.startswith("acct_mock_"):
        return {"ok": True, "deauthorized": True, "mock": True}
    if not oauth_client_ready():
        return {"ok": False, "reason": "stripe_connect_not_configured"}
    with httpx.Client(timeout=30.0) as client:
        res = client.post(
            _DEAUTH_URL,
            data={
                "client_id": _client_id(),
                "stripe_user_id": acct,
            },
            auth=(_resolve_stripe_secret(), ""),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if res.status_code >= 400:
        logger.warning("stripe connect deauthorize failed status=%s acct=%s", res.status_code, acct[:12])
        return {
            "ok": False,
            "reason": f"deauth_error:{res.status_code}",
            "detail": (res.text or "")[:200],
        }
    return {"ok": True, "deauthorized": True}


def retrieve_account(stripe_user_id: str) -> dict[str, Any]:
    """Verify connected account still reachable with platform secret."""
    acct = (stripe_user_id or "").strip()
    if not acct.startswith("acct_"):
        return {"ok": False, "reason": "invalid_account"}
    if mock_enabled() or acct.startswith("acct_mock_"):
        return {
            "ok": True,
            "id": acct,
            "email": "mock-merchant@example.de",
            "charges_enabled": True,
            "payouts_enabled": True,
            "mock": True,
        }
    secret = _resolve_stripe_secret()
    if not secret:
        return {"ok": False, "reason": "stripe_not_configured"}
    with httpx.Client(timeout=30.0) as client:
        res = client.get(
            f"{_ACCOUNT_URL}/{acct}",
            auth=(secret, ""),
        )
    if res.status_code >= 400:
        return {
            "ok": False,
            "reason": f"account_error:{res.status_code}",
            "detail": (res.text or "")[:200],
        }
    data = res.json() if res.content else {}
    return {
        "ok": True,
        "id": str(data.get("id") or acct),
        "email": str(data.get("email") or "").strip() or None,
        "business_profile": data.get("business_profile") if isinstance(data.get("business_profile"), dict) else {},
        "charges_enabled": bool(data.get("charges_enabled")),
        "payouts_enabled": bool(data.get("payouts_enabled")),
        "details_submitted": bool(data.get("details_submitted")),
        "country": str(data.get("country") or "").strip() or None,
    }


def status(*, public_api_base: str = "") -> dict[str, Any]:
    redirect = default_redirect_uri(public_api_base) if public_api_base else ""
    return {
        "oauth_client_ready": oauth_client_ready(),
        "mock": mock_enabled(),
        "has_client_id": bool(_client_id()),
        "has_platform_secret": bool(_resolve_stripe_secret()),
        "redirect_uri": redirect or None,
        "note": (
            "Merchants Connect Stripe via OAuth. Set STRIPE_CONNECT_CLIENT_ID (ca_…) "
            "and register redirect_uri in Stripe Dashboard → Connect → Settings. "
            "Virtus never receives shop buyer funds."
        ),
    }


def account_label_from_oauth(result: dict[str, Any], *, account_info: dict[str, Any] | None = None) -> str:
    info = account_info or {}
    email = str(info.get("email") or "").strip()
    if email:
        return email
    acct = str(result.get("stripe_user_id") or "").strip()
    return acct or "Stripe Connected"
