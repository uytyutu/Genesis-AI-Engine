"""Per-shop Store Customer Account service (not Virtus Client Identity)."""

from __future__ import annotations

import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.store_customer.auth import (
    _RESET_TTL_SEC,
    hash_password,
    hash_reset_token,
    issue_store_buyer_token,
    make_reset_token,
    validate_email,
    verify_password,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_buyer(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "email": row.get("email"),
        "first_name": row.get("first_name") or "",
        "last_name": row.get("last_name") or "",
        "phone": row.get("phone") or "",
        "locale": row.get("locale") or "en",
        "marketing_opt_in": bool(row.get("marketing_opt_in")),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


class StoreCustomerService:
    """
    Buyer accounts scoped to one shop (order_id).
    Stored under store_admin/{order_id}/customers/ — User Data Protection.
    """

    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "store_admin"
        self._root.mkdir(parents=True, exist_ok=True)

    def _shop_dir(self, order_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        d = self._root / safe / "customers"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _index_path(self, order_id: str) -> Path:
        return self._shop_dir(order_id) / "index.json"

    def _load_index(self, order_id: str) -> list[dict[str, Any]]:
        path = self._index_path(order_id)
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        buyers = data.get("buyers") if isinstance(data, dict) else data
        if not isinstance(buyers, list):
            return []
        return [b for b in buyers if isinstance(b, dict)]

    def _save_index(self, order_id: str, buyers: list[dict[str, Any]]) -> None:
        payload = {
            "version": 1,
            "order_id": order_id,
            "updated_at": _now(),
            "buyers": buyers,
        }
        self._index_path(order_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _find(self, order_id: str, *, buyer_id: str | None = None, email: str | None = None) -> dict[str, Any] | None:
        for row in self._load_index(order_id):
            if buyer_id and row.get("id") == buyer_id:
                return row
            if email and str(row.get("email") or "").lower() == email.lower():
                return row
        return None

    def register(
        self,
        order_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        email = validate_email(str(payload.get("email") or ""))
        password = str(payload.get("password") or "")
        if len(password) < 8:
            raise ValueError("password_too_short")
        if self._find(order_id, email=email):
            raise ValueError("email_already_registered")

        buyers = self._load_index(order_id)
        buyer_id = f"buy-{uuid.uuid4().hex[:12]}"
        row = {
            "id": buyer_id,
            "email": email,
            "password_hash": hash_password(password),
            "first_name": str(payload.get("first_name") or "").strip()[:80],
            "last_name": str(payload.get("last_name") or "").strip()[:80],
            "phone": str(payload.get("phone") or "").strip()[:40],
            "locale": str(payload.get("locale") or "en").strip()[:8],
            "marketing_opt_in": bool(payload.get("marketing_opt_in")),
            "addresses": [],
            "wishlist": [],
            "orders": [],  # R3.3 Commerce fills this
            "reset": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        buyers.append(row)
        self._save_index(order_id, buyers)
        token = issue_store_buyer_token(
            buyer_id=buyer_id, email=email, order_id=order_id
        )
        return {
            "ok": True,
            "token": token,
            "buyer": _public_buyer(row),
            "scope": "store_buyer",
            "note": "Separate from Virtus Core Client Workspace accounts.",
        }

    def login(self, order_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        email = validate_email(str(payload.get("email") or ""))
        password = str(payload.get("password") or "")
        row = self._find(order_id, email=email)
        if not row or not verify_password(password, str(row.get("password_hash") or "")):
            raise ValueError("invalid_credentials")
        token = issue_store_buyer_token(
            buyer_id=str(row["id"]), email=email, order_id=order_id
        )
        return {
            "ok": True,
            "token": token,
            "buyer": _public_buyer(row),
            "scope": "store_buyer",
        }

    def me(self, order_id: str, buyer_id: str) -> dict[str, Any]:
        row = self._find(order_id, buyer_id=buyer_id)
        if not row:
            raise ValueError("buyer_not_found")
        return {
            "ok": True,
            "buyer": _public_buyer(row),
            "addresses": list(row.get("addresses") or []),
            "wishlist": list(row.get("wishlist") or []),
            "orders": list(row.get("orders") or []),
            "orders_note": "Order history activates with Commerce (R3.3).",
        }

    def update_profile(
        self, order_id: str, buyer_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        buyers = self._load_index(order_id)
        for i, row in enumerate(buyers):
            if row.get("id") != buyer_id:
                continue
            for key in ("first_name", "last_name", "phone", "locale"):
                if key in payload:
                    row[key] = str(payload.get(key) or "").strip()[:80]
            if "marketing_opt_in" in payload:
                row["marketing_opt_in"] = bool(payload.get("marketing_opt_in"))
            if payload.get("password"):
                password = str(payload.get("password") or "")
                if len(password) < 8:
                    raise ValueError("password_too_short")
                row["password_hash"] = hash_password(password)
            row["updated_at"] = _now()
            buyers[i] = row
            self._save_index(order_id, buyers)
            return {"ok": True, "buyer": _public_buyer(row)}
        raise ValueError("buyer_not_found")

    def request_password_reset(
        self, order_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        email = validate_email(str(payload.get("email") or ""))
        buyers = self._load_index(order_id)
        token = None
        for i, row in enumerate(buyers):
            if str(row.get("email") or "").lower() != email:
                continue
            raw = make_reset_token()
            row["reset"] = {
                "token_hash": hash_reset_token(raw),
                "expires_at": int(time.time()) + _RESET_TTL_SEC,
            }
            row["updated_at"] = _now()
            buyers[i] = row
            self._save_index(order_id, buyers)
            token = raw
            break
        # Always OK (no email enumeration). Dev token only when account exists.
        out: dict[str, Any] = {
            "ok": True,
            "message": "If an account exists, a reset link was prepared.",
            "delivery": "dev_inline",
            "note": "Email delivery arrives with Commerce/ops; token returned for local verify.",
        }
        if token:
            out["dev_reset_token"] = token
        return out

    def reset_password(self, order_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        email = validate_email(str(payload.get("email") or ""))
        token = str(payload.get("token") or "").strip()
        password = str(payload.get("password") or "")
        if not token:
            raise ValueError("reset_token_required")
        if len(password) < 8:
            raise ValueError("password_too_short")
        token_hash = hash_reset_token(token)
        buyers = self._load_index(order_id)
        for i, row in enumerate(buyers):
            if str(row.get("email") or "").lower() != email:
                continue
            reset = row.get("reset") if isinstance(row.get("reset"), dict) else None
            if not reset or reset.get("token_hash") != token_hash:
                raise ValueError("invalid_reset_token")
            if int(reset.get("expires_at") or 0) < int(time.time()):
                raise ValueError("reset_token_expired")
            row["password_hash"] = hash_password(password)
            row["reset"] = None
            row["updated_at"] = _now()
            buyers[i] = row
            self._save_index(order_id, buyers)
            auth = issue_store_buyer_token(
                buyer_id=str(row["id"]), email=email, order_id=order_id
            )
            return {"ok": True, "token": auth, "buyer": _public_buyer(row)}
        raise ValueError("invalid_reset_token")

    def list_addresses(self, order_id: str, buyer_id: str) -> dict[str, Any]:
        row = self._find(order_id, buyer_id=buyer_id)
        if not row:
            raise ValueError("buyer_not_found")
        return {"ok": True, "addresses": list(row.get("addresses") or [])}

    def save_address(
        self, order_id: str, buyer_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        buyers = self._load_index(order_id)
        for i, row in enumerate(buyers):
            if row.get("id") != buyer_id:
                continue
            addresses = list(row.get("addresses") or [])
            addr_id = str(payload.get("id") or "").strip() or f"addr-{uuid.uuid4().hex[:10]}"
            entry = {
                "id": addr_id,
                "label": str(payload.get("label") or "Home").strip()[:40],
                "full_name": str(payload.get("full_name") or "").strip()[:120],
                "line1": str(payload.get("line1") or "").strip()[:160],
                "line2": str(payload.get("line2") or "").strip()[:160],
                "city": str(payload.get("city") or "").strip()[:80],
                "postal_code": str(payload.get("postal_code") or "").strip()[:20],
                "country": str(payload.get("country") or "DE").strip()[:2].upper(),
                "phone": str(payload.get("phone") or "").strip()[:40],
                "is_default": bool(payload.get("is_default")),
            }
            if not entry["line1"] or not entry["city"]:
                raise ValueError("address_incomplete")
            replaced = False
            for j, existing in enumerate(addresses):
                if existing.get("id") == addr_id:
                    addresses[j] = entry
                    replaced = True
                    break
            if not replaced:
                addresses.append(entry)
            if entry["is_default"]:
                for a in addresses:
                    a["is_default"] = a.get("id") == addr_id
            row["addresses"] = addresses
            row["updated_at"] = _now()
            buyers[i] = row
            self._save_index(order_id, buyers)
            return {"ok": True, "addresses": addresses}
        raise ValueError("buyer_not_found")

    def delete_address(
        self, order_id: str, buyer_id: str, address_id: str
    ) -> dict[str, Any]:
        buyers = self._load_index(order_id)
        for i, row in enumerate(buyers):
            if row.get("id") != buyer_id:
                continue
            addresses = [
                a
                for a in (row.get("addresses") or [])
                if isinstance(a, dict) and a.get("id") != address_id
            ]
            row["addresses"] = addresses
            row["updated_at"] = _now()
            buyers[i] = row
            self._save_index(order_id, buyers)
            return {"ok": True, "addresses": addresses}
        raise ValueError("buyer_not_found")

    def get_wishlist(self, order_id: str, buyer_id: str) -> dict[str, Any]:
        row = self._find(order_id, buyer_id=buyer_id)
        if not row:
            raise ValueError("buyer_not_found")
        return {"ok": True, "wishlist": list(row.get("wishlist") or [])}

    def set_wishlist(
        self, order_id: str, buyer_id: str, items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        buyers = self._load_index(order_id)
        for i, row in enumerate(buyers):
            if row.get("id") != buyer_id:
                continue
            cleaned: list[dict[str, Any]] = []
            seen: set[str] = set()
            for raw in items:
                if not isinstance(raw, dict):
                    continue
                pid = str(raw.get("product_id") or raw.get("id") or "").strip()
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                cleaned.append(
                    {
                        "product_id": pid,
                        "title": str(raw.get("title") or raw.get("name") or "")[:120],
                        "price": float(raw.get("price") or 0),
                        "image": str(raw.get("image") or "")[:300] or None,
                        "added_at": str(raw.get("added_at") or _now()),
                    }
                )
                if len(cleaned) >= 100:
                    break
            row["wishlist"] = cleaned
            row["updated_at"] = _now()
            buyers[i] = row
            self._save_index(order_id, buyers)
            return {"ok": True, "wishlist": cleaned}
        raise ValueError("buyer_not_found")

    def get_orders(self, order_id: str, buyer_id: str) -> dict[str, Any]:
        row = self._find(order_id, buyer_id=buyer_id)
        if not row:
            raise ValueError("buyer_not_found")
        return {
            "ok": True,
            "orders": list(row.get("orders") or []),
            "commerce_ready": False,
            "note": "Checkout and payments arrive in R3.3 Commerce.",
        }

    def admin_list_customers(self, order_id: str) -> dict[str, Any]:
        """Store Admin read-only customer list (no passwords)."""
        buyers = self._load_index(order_id)
        rows = []
        for b in buyers:
            rows.append(
                {
                    **_public_buyer(b),
                    "address_count": len(b.get("addresses") or []),
                    "wishlist_count": len(b.get("wishlist") or []),
                    "order_count": len(b.get("orders") or []),
                }
            )
        return {
            "ok": True,
            "order_id": order_id,
            "count": len(rows),
            "customers": rows,
            "note": "Store buyers — not Virtus Core clients.",
        }
