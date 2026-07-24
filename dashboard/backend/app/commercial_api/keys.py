"""API key + prepaid balance store (memory JSON)."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

KEYS_FILE = "commercial_api_keys.json"
USAGE_FILE = "commercial_api_usage.jsonl"
DEFAULT_SCOPES = ("audit",)
DEFAULT_RATE_LIMIT = 100


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CommercialApiKeyStore:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._path = memory_dir / KEYS_FILE
        self._usage = memory_dir / USAGE_FILE

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"keys": []}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"keys": []}
            data.setdefault("keys", [])
            return data
        except (json.JSONDecodeError, OSError):
            return {"keys": []}

    def _save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_key(
        self,
        *,
        label: str = "client",
        balance_eur: float = 0.0,
        customer_email: str = "",
        scopes: list[str] | None = None,
        rate_limit_per_min: int = DEFAULT_RATE_LIMIT,
    ) -> dict[str, Any]:
        raw = f"vc_{secrets.token_urlsafe(24)}"
        scope_list = [str(s).strip() for s in (scopes or list(DEFAULT_SCOPES)) if str(s).strip()]
        if not scope_list:
            scope_list = list(DEFAULT_SCOPES)
        row = {
            "id": uuid.uuid4().hex[:12],
            "label": (label or "client")[:80],
            "customer_email": (customer_email or "")[:160],
            "key_hash": _hash_key(raw),
            "key_prefix": raw[:10],
            "balance_eur": round(float(balance_eur or 0), 4),
            "scopes": scope_list,
            "rate_limit_per_min": max(1, min(1000, int(rate_limit_per_min or DEFAULT_RATE_LIMIT))),
            "created_at": _now(),
            "active": True,
            "revoked_at": None,
            "requests": 0,
        }
        data = self._load()
        data["keys"].append(row)
        self._save(data)
        out = dict(row)
        out["api_key"] = raw
        out.pop("key_hash", None)
        return out

    def resolve(self, raw_key: str) -> dict[str, Any] | None:
        raw = (raw_key or "").strip()
        if not raw.startswith("vc_"):
            return None
        digest = _hash_key(raw)
        for row in self._load().get("keys", []):
            if row.get("key_hash") == digest and row.get("active"):
                return dict(row)
        return None

    def has_scope(self, account: dict[str, Any], scope: str) -> bool:
        scopes = account.get("scopes") or []
        if not isinstance(scopes, list):
            return False
        if "*" in scopes:
            return True
        return scope in scopes

    def revoke(self, key_id: str) -> dict[str, Any]:
        data = self._load()
        for row in data["keys"]:
            if row.get("id") == key_id:
                row["active"] = False
                row["revoked_at"] = _now()
                self._save(data)
                self._log_usage(
                    key_id=key_id,
                    product_id="revoke",
                    amount_eur=0.0,
                    ok=True,
                    detail="revoked",
                )
                return {"ok": True, "id": key_id, "active": False}
        return {"ok": False, "reason": "key_not_found"}

    def list_public(self) -> list[dict[str, Any]]:
        out = []
        for row in self._load().get("keys", []):
            out.append(
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "customer_email": row.get("customer_email"),
                    "key_prefix": row.get("key_prefix"),
                    "balance_eur": row.get("balance_eur"),
                    "scopes": row.get("scopes") or [],
                    "rate_limit_per_min": row.get("rate_limit_per_min") or DEFAULT_RATE_LIMIT,
                    "active": row.get("active"),
                    "revoked_at": row.get("revoked_at"),
                    "requests": row.get("requests"),
                    "created_at": row.get("created_at"),
                }
            )
        return out

    def credit(self, key_id: str, amount_eur: float, *, note: str = "") -> dict[str, Any]:
        amount = round(float(amount_eur or 0), 4)
        if amount <= 0:
            return {"ok": False, "reason": "amount_required"}
        data = self._load()
        for row in data["keys"]:
            if row.get("id") == key_id:
                row["balance_eur"] = round(float(row.get("balance_eur") or 0) + amount, 4)
                self._save(data)
                self._log_usage(
                    key_id=key_id,
                    product_id="credit",
                    amount_eur=amount,
                    ok=True,
                    detail=note or "manual_credit",
                )
                return {"ok": True, "balance_eur": row["balance_eur"], "id": key_id}
        return {"ok": False, "reason": "key_not_found"}

    def debit(self, key_id: str, amount_eur: float, *, product_id: str) -> dict[str, Any]:
        amount = round(float(amount_eur or 0), 4)
        if amount <= 0:
            return {"ok": False, "reason": "amount_required"}
        data = self._load()
        for row in data["keys"]:
            if row.get("id") == key_id and row.get("active"):
                bal = round(float(row.get("balance_eur") or 0), 4)
                if bal < amount:
                    return {"ok": False, "reason": "insufficient_balance", "balance_eur": bal}
                row["balance_eur"] = round(bal - amount, 4)
                row["requests"] = int(row.get("requests") or 0) + 1
                self._save(data)
                self._log_usage(
                    key_id=key_id,
                    product_id=product_id,
                    amount_eur=-amount,
                    ok=True,
                    detail="debit",
                )
                return {"ok": True, "balance_eur": row["balance_eur"], "charged_eur": amount}
        return {"ok": False, "reason": "key_not_found"}

    def _log_usage(
        self,
        *,
        key_id: str,
        product_id: str,
        amount_eur: float,
        ok: bool,
        detail: str,
    ) -> None:
        self._usage.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "at": _now(),
            "key_id": key_id,
            "product_id": product_id,
            "amount_eur": amount_eur,
            "ok": ok,
            "detail": detail[:200],
        }
        with self._usage.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def log_event(
        self,
        *,
        key_id: str,
        product_id: str,
        ok: bool,
        detail: str,
        amount_eur: float = 0.0,
    ) -> None:
        self._log_usage(
            key_id=key_id,
            product_id=product_id,
            amount_eur=amount_eur,
            ok=ok,
            detail=detail,
        )

    def recent_usage(self, *, limit: int = 50) -> list[dict[str, Any]]:
        if not self._usage.is_file():
            return []
        lines = self._usage.read_text(encoding="utf-8").strip().splitlines()
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(out))
