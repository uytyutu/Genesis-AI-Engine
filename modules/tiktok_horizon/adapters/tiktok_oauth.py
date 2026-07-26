"""TikTok OAuth Adapter — official Login Kit / token endpoints (independent of content pipeline)."""

from __future__ import annotations

import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from modules.tiktok_horizon.adapters.base import AdapterResult, ExternalAdapter

_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
_REVOKE_URL = "https://open.tiktokapis.com/v2/oauth/revoke/"
_USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"

# Stage 2: identity only — no video.publish
_DEFAULT_SCOPES = ("user.info.basic", "user.info.profile")

_oauth_states: dict[str, float] = {}
_STATE_TTL_SEC = 600


class TikTokOAuthAdapter(ExternalAdapter):
    """Official OAuth 2.0 adapter — swappable, Horizon-agnostic."""

    provider_id = "tiktok_oauth_official"

    def __init__(
        self,
        *,
        client_key: str | None = None,
        client_secret: str | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._client_key = (client_key if client_key is not None else os.getenv("TIKTOK_CLIENT_KEY", "")).strip()
        self._client_secret = (
            client_secret if client_secret is not None else os.getenv("TIKTOK_CLIENT_SECRET", "")
        ).strip()
        self._http = http_client

    def health(self) -> AdapterResult:
        return AdapterResult(
            ok=True,
            provider=self.provider_id,
            data={
                "oauth_client_ready": self.oauth_client_ready(),
                "scopes": list(_DEFAULT_SCOPES),
                "publish_enabled": False,
            },
            meta={
                "auth_url": _AUTH_URL,
                "token_url": _TOKEN_URL,
                "note": "Stage 2: connect accounts only. No publish.",
            },
        )

    def oauth_client_ready(self) -> bool:
        return bool(self._client_key and self._client_secret)

    def default_redirect_uri(self, public_api_base: str) -> str:
        override = os.getenv("TIKTOK_REDIRECT_URI", "").strip()
        if override:
            return override
        base = public_api_base.rstrip("/")
        return f"{base}/api/owner/tiktok-horizon/oauth/callback"

    def create_state(self) -> str:
        now = time.time()
        expired = [k for k, ts in _oauth_states.items() if now - ts > _STATE_TTL_SEC]
        for k in expired:
            _oauth_states.pop(k, None)
        state = secrets.token_urlsafe(24)
        _oauth_states[state] = now
        return state

    def consume_state(self, state: str) -> bool:
        ts = _oauth_states.pop(state or "", None)
        if ts is None:
            return False
        return (time.time() - ts) <= _STATE_TTL_SEC

    def authorization_url(self, *, redirect_uri: str, state: str, scopes: list[str] | None = None) -> str:
        if not self.oauth_client_ready():
            raise ValueError("tiktok_oauth_not_configured")
        scope = ",".join(scopes or list(_DEFAULT_SCOPES))
        params = {
            "client_key": self._client_key,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
        }
        return f"{_AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, *, code: str, redirect_uri: str) -> dict[str, Any]:
        if not self.oauth_client_ready():
            return {"ok": False, "reason": "tiktok_oauth_not_configured"}
        if not (code or "").strip():
            return {"ok": False, "reason": "missing_code"}
        payload = {
            "client_key": self._client_key,
            "client_secret": self._client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        return self._token_request(payload)

    def refresh_access_token(self, *, refresh_token: str) -> dict[str, Any]:
        if not self.oauth_client_ready():
            return {"ok": False, "reason": "tiktok_oauth_not_configured"}
        payload = {
            "client_key": self._client_key,
            "client_secret": self._client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        return self._token_request(payload)

    def revoke(self, *, access_token: str) -> dict[str, Any]:
        if not self.oauth_client_ready():
            return {"ok": False, "reason": "tiktok_oauth_not_configured"}
        try:
            with self._client() as client:
                res = client.post(
                    _REVOKE_URL,
                    data={
                        "client_key": self._client_key,
                        "client_secret": self._client_secret,
                        "token": access_token,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except httpx.HTTPError as exc:
            return {"ok": False, "reason": "http_error", "detail": str(exc)}
        if res.status_code >= 400:
            return {
                "ok": False,
                "reason": "revoke_failed",
                "status": res.status_code,
                "detail": res.text[:400],
            }
        return {"ok": True}

    def fetch_user_profile(self, *, access_token: str) -> dict[str, Any]:
        """Best-effort profile via Display API. Fields depend on granted scopes."""
        fields = "open_id,union_id,avatar_url,display_name,username"
        try:
            with self._client() as client:
                res = client.get(
                    _USER_INFO_URL,
                    params={"fields": fields},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.HTTPError as exc:
            return {"ok": False, "reason": "http_error", "detail": str(exc)}
        if res.status_code >= 400:
            # Retry with basic fields only
            try:
                with self._client() as client:
                    res = client.get(
                        _USER_INFO_URL,
                        params={"fields": "open_id,avatar_url,display_name"},
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
            except httpx.HTTPError as exc:
                return {"ok": False, "reason": "http_error", "detail": str(exc)}
        if res.status_code >= 400:
            return {
                "ok": False,
                "reason": "user_info_failed",
                "status": res.status_code,
                "detail": res.text[:400],
            }
        try:
            body = res.json()
        except ValueError:
            return {"ok": False, "reason": "invalid_json"}
        user = ((body.get("data") or {}).get("user") or {}) if isinstance(body, dict) else {}
        return {
            "ok": True,
            "open_id": user.get("open_id"),
            "display_name": user.get("display_name"),
            "username": user.get("username"),
            "avatar_url": user.get("avatar_url"),
            "raw": user,
        }

    def _token_request(self, payload: dict[str, str]) -> dict[str, Any]:
        try:
            with self._client() as client:
                res = client.post(
                    _TOKEN_URL,
                    data=payload,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Cache-Control": "no-cache",
                    },
                )
        except httpx.HTTPError as exc:
            return {"ok": False, "reason": "http_error", "detail": str(exc)}
        try:
            body = res.json()
        except ValueError:
            return {"ok": False, "reason": "invalid_json", "detail": res.text[:300]}
        if not isinstance(body, dict):
            return {"ok": False, "reason": "invalid_response"}
        if body.get("error") or res.status_code >= 400:
            return {
                "ok": False,
                "reason": str(body.get("error") or "token_error"),
                "detail": body.get("error_description") or body.get("message") or res.text[:300],
            }
        access = body.get("access_token")
        open_id = body.get("open_id")
        if not access or not open_id:
            return {"ok": False, "reason": "missing_token_fields", "detail": body}
        scopes_raw = str(body.get("scope") or "")
        scopes = [s.strip() for s in scopes_raw.split(",") if s.strip()]
        return {
            "ok": True,
            "open_id": str(open_id),
            "access_token": str(access),
            "refresh_token": str(body.get("refresh_token") or ""),
            "expires_in": int(body.get("expires_in") or 86400),
            "refresh_expires_in": int(body.get("refresh_expires_in") or 0),
            "scopes": scopes,
            "token_type": str(body.get("token_type") or "Bearer"),
        }

    def _client(self):
        if self._http is not None:
            return _NullCtx(self._http)
        return httpx.Client(timeout=30.0)


class _NullCtx:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def __enter__(self) -> httpx.Client:
        return self._client

    def __exit__(self, *args: object) -> None:
        return None
