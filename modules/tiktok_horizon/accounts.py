"""Multi-account store for connected TikTok profiles (Owner Horizon only)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.tiktok_horizon.token_vault import public_token_meta, seal_secret, unseal_secret


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TikTokAccountStore:
    def __init__(self, root: Path) -> None:
        self._path = root / "accounts.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({"accounts": []})

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"accounts": []}
        if not isinstance(data, dict):
            return {"accounts": []}
        accounts = data.get("accounts")
        if not isinstance(accounts, list):
            data["accounts"] = []
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def list_public(self) -> list[dict[str, Any]]:
        return [self.to_public(a) for a in self._read().get("accounts") or []]

    def get_raw(self, account_id: str) -> dict[str, Any] | None:
        for row in self._read().get("accounts") or []:
            if row.get("id") == account_id or row.get("open_id") == account_id:
                return dict(row)
        return None

    def to_public(self, row: dict[str, Any]) -> dict[str, Any]:
        username = row.get("username")
        display = row.get("display_name")
        return {
            "id": row.get("id"),
            "open_id": row.get("open_id"),
            "display_name": display,
            "username": username,
            "status": row.get("status") or "disconnected",
            "connected_at": row.get("connected_at"),
            "last_sync_at": row.get("last_sync_at"),
            "avatar_url": row.get("avatar_url"),
            "label": f"@{username}" if username else (display or row.get("open_id") or row.get("id")),
            "tokens": public_token_meta(row),
            "publish_enabled": False,
        }

    def upsert_from_oauth(
        self,
        *,
        open_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        refresh_expires_in: int,
        scopes: list[str],
        display_name: str | None = None,
        username: str | None = None,
        avatar_url: str | None = None,
    ) -> dict[str, Any]:
        data = self._read()
        accounts: list[dict[str, Any]] = list(data.get("accounts") or [])
        now = _now()
        existing = next((a for a in accounts if a.get("open_id") == open_id), None)
        access_exp = _expiry_iso(expires_in)
        refresh_exp = _expiry_iso(refresh_expires_in)

        if existing:
            existing.update(
                {
                    "status": "connected",
                    "display_name": display_name or existing.get("display_name"),
                    "username": username or existing.get("username"),
                    "avatar_url": avatar_url or existing.get("avatar_url"),
                    "access_token_sealed": seal_secret(access_token),
                    "refresh_token_sealed": seal_secret(refresh_token) if refresh_token else existing.get("refresh_token_sealed"),
                    "access_token_expires_at": access_exp,
                    "refresh_token_expires_at": refresh_exp,
                    "scopes": scopes,
                    "last_sync_at": now,
                    "updated_at": now,
                }
            )
            if not existing.get("connected_at"):
                existing["connected_at"] = now
            row = existing
        else:
            row = {
                "id": f"tta-{uuid.uuid4().hex[:10]}",
                "open_id": open_id,
                "display_name": display_name,
                "username": username,
                "avatar_url": avatar_url,
                "status": "connected",
                "connected_at": now,
                "last_sync_at": now,
                "updated_at": now,
                "access_token_sealed": seal_secret(access_token),
                "refresh_token_sealed": seal_secret(refresh_token) if refresh_token else "",
                "access_token_expires_at": access_exp,
                "refresh_token_expires_at": refresh_exp,
                "scopes": scopes,
            }
            accounts.append(row)

        data["accounts"] = accounts
        self._write(data)
        return self.to_public(row)

    def upsert_sandbox_owner_account(
        self,
        *,
        username: str = "virtus_sandbox",
        display_name: str = "Virtus Sandbox",
    ) -> dict[str, Any]:
        """Owner-only placeholder so trend/draft pipeline runs before real OAuth keys."""
        open_id = "sandbox-owner-tiktok"
        data = self._read()
        accounts: list[dict[str, Any]] = list(data.get("accounts") or [])
        now = _now()
        existing = next((a for a in accounts if a.get("open_id") == open_id), None)
        if existing:
            existing.update(
                {
                    "status": "connected",
                    "display_name": display_name,
                    "username": username,
                    "last_sync_at": now,
                    "updated_at": now,
                    "sandbox": True,
                    "publish_enabled": False,
                }
            )
            if not existing.get("connected_at"):
                existing["connected_at"] = now
            row = existing
        else:
            row = {
                "id": f"tta-{uuid.uuid4().hex[:10]}",
                "open_id": open_id,
                "display_name": display_name,
                "username": username,
                "avatar_url": None,
                "status": "connected",
                "connected_at": now,
                "last_sync_at": now,
                "updated_at": now,
                "access_token_sealed": "",
                "refresh_token_sealed": "",
                "access_token_expires_at": None,
                "refresh_token_expires_at": None,
                "scopes": ["sandbox.local"],
                "sandbox": True,
                "publish_enabled": False,
            }
            accounts.append(row)
        data["accounts"] = accounts
        self._write(data)
        public = self.to_public(row)
        public["sandbox"] = True
        public["label"] = f"@{username} (sandbox)"
        return public

    def disconnect(self, account_id: str, *, revoke_ok: bool | None = None) -> dict[str, Any]:
        data = self._read()
        accounts = list(data.get("accounts") or [])
        found = None
        for row in accounts:
            if row.get("id") == account_id or row.get("open_id") == account_id:
                found = row
                break
        if not found:
            raise ValueError("account_not_found")
        found["status"] = "disconnected"
        found["access_token_sealed"] = ""
        found["refresh_token_sealed"] = ""
        found["access_token_expires_at"] = None
        found["updated_at"] = _now()
        found["disconnected_at"] = _now()
        if revoke_ok is not None:
            found["last_revoke_ok"] = bool(revoke_ok)
        data["accounts"] = accounts
        self._write(data)
        return self.to_public(found)

    def remove(self, account_id: str) -> None:
        data = self._read()
        before = list(data.get("accounts") or [])
        after = [
            a
            for a in before
            if a.get("id") != account_id and a.get("open_id") != account_id
        ]
        if len(after) == len(before):
            raise ValueError("account_not_found")
        data["accounts"] = after
        self._write(data)

    def mark_synced(self, account_id: str, *, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        data = self._read()
        for row in data.get("accounts") or []:
            if row.get("id") == account_id or row.get("open_id") == account_id:
                row["last_sync_at"] = _now()
                row["updated_at"] = _now()
                row["status"] = "connected"
                if profile:
                    if profile.get("display_name"):
                        row["display_name"] = profile["display_name"]
                    if profile.get("username"):
                        row["username"] = profile["username"]
                    if profile.get("avatar_url"):
                        row["avatar_url"] = profile["avatar_url"]
                self._write(data)
                return self.to_public(row)
        raise ValueError("account_not_found")

    def update_tokens(
        self,
        account_id: str,
        *,
        access_token: str,
        refresh_token: str | None,
        expires_in: int,
        refresh_expires_in: int | None,
        scopes: list[str] | None = None,
    ) -> dict[str, Any]:
        data = self._read()
        for row in data.get("accounts") or []:
            if row.get("id") == account_id or row.get("open_id") == account_id:
                row["access_token_sealed"] = seal_secret(access_token)
                if refresh_token:
                    row["refresh_token_sealed"] = seal_secret(refresh_token)
                row["access_token_expires_at"] = _expiry_iso(expires_in)
                if refresh_expires_in is not None:
                    row["refresh_token_expires_at"] = _expiry_iso(refresh_expires_in)
                if scopes is not None:
                    row["scopes"] = scopes
                row["last_sync_at"] = _now()
                row["status"] = "connected"
                row["updated_at"] = _now()
                self._write(data)
                return self.to_public(row)
        raise ValueError("account_not_found")

    def get_access_token(self, account_id: str) -> str:
        row = self.get_raw(account_id)
        if not row or row.get("status") != "connected":
            raise ValueError("account_not_connected")
        sealed = row.get("access_token_sealed") or ""
        return unseal_secret(sealed)

    def get_refresh_token(self, account_id: str) -> str:
        row = self.get_raw(account_id)
        if not row:
            raise ValueError("account_not_found")
        sealed = row.get("refresh_token_sealed") or ""
        if not sealed:
            raise ValueError("refresh_token_missing")
        return unseal_secret(sealed)

    def connected_count(self) -> int:
        return sum(1 for a in self._read().get("accounts") or [] if a.get("status") == "connected")


def _expiry_iso(expires_in: int) -> str:
    from datetime import timedelta

    sec = max(0, int(expires_in or 0))
    return (datetime.now(timezone.utc) + timedelta(seconds=sec)).isoformat()
