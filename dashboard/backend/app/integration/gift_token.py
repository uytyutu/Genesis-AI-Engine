"""One-time Virtus Core friend/gift tokens — no Stripe, no finance inflate.

Owner mints → friend opens /order?gift=CODE → fills business form → gift pay → Workspace.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()

DEFAULT_TTL_DAYS = 14
DEFAULT_PACKAGE = "standalone"


def _memory_root() -> Path:
    env = (os.getenv("GENESIS_MEMORY_DIR") or "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1] / "memory"


def _store_path() -> Path:
    return _memory_root() / "gift_tokens.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"version": 1, "tokens": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "tokens": {}}
    if not isinstance(raw, dict):
        return {"version": 1, "tokens": {}}
    tokens = raw.get("tokens")
    if not isinstance(tokens, dict):
        raw["tokens"] = {}
    return raw


def _save(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def mint_token(
    *,
    label: str = "Friend gift",
    package_id: str = DEFAULT_PACKAGE,
    ttl_days: int = DEFAULT_TTL_DAYS,
    minted_by: str = "owner",
) -> dict[str, Any]:
    """Create a single-use gift code. Returns plaintext code once."""
    code = secrets.token_urlsafe(10).replace("-", "").replace("_", "")[:12].upper()
    if len(code) < 10:
        code = secrets.token_hex(6).upper()
    code_h = hash_code(code)
    now = _now()
    expires = now + timedelta(days=max(1, int(ttl_days)))
    row = {
        "code_hash": code_h,
        "label": (label or "Friend gift").strip()[:120],
        "package_id": (package_id or DEFAULT_PACKAGE).strip() or DEFAULT_PACKAGE,
        "minted_at": _iso(now),
        "expires_at": _iso(expires),
        "minted_by": minted_by,
        "redeemed_at": None,
        "order_id": None,
        "status": "active",
    }
    with _LOCK:
        data = _load()
        data.setdefault("tokens", {})[code_h] = row
        _save(data)
    return {
        "ok": True,
        "code": code,
        "label": row["label"],
        "package_id": row["package_id"],
        "expires_at": row["expires_at"],
        "path": f"/order?form=1&gift={code}",
        "gift_path": f"/gift/{code}",
    }


def peek_token(code: str) -> dict[str, Any]:
    """Public validate — does not redeem."""
    raw = (code or "").strip()
    if not raw or len(raw) < 8:
        return {"ok": False, "error": "gift_code_invalid"}
    code_h = hash_code(raw)
    with _LOCK:
        data = _load()
        row = data.get("tokens", {}).get(code_h)
    if not row:
        return {"ok": False, "error": "gift_code_not_found"}
    if row.get("status") == "redeemed" or row.get("redeemed_at"):
        return {"ok": False, "error": "gift_code_used"}
    try:
        exp = datetime.fromisoformat(str(row.get("expires_at") or "").replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if _now() > exp:
            return {"ok": False, "error": "gift_code_expired"}
    except ValueError:
        return {"ok": False, "error": "gift_code_invalid"}
    return {
        "ok": True,
        "label": row.get("label") or "Virtus Core Geschenk",
        "package_id": row.get("package_id") or DEFAULT_PACKAGE,
        "expires_at": row.get("expires_at"),
        "banner_de": "Virtus Core Geschenk — keine Zahlung. Website + Workspace nach dem Absenden.",
        "banner_ru": "Подарок Virtus Core — без оплаты. Сайт + пульт управления после заполнения.",
        "banner_en": "Virtus Core gift — no payment. Website + Workspace after you submit.",
    }


def redeem_token(code: str, *, order_id: str) -> dict[str, Any]:
    """Mark token used. Raises ValueError with stable codes."""
    peek = peek_token(code)
    if not peek.get("ok"):
        raise ValueError(str(peek.get("error") or "gift_code_invalid"))
    code_h = hash_code(code)
    oid = str(order_id or "").strip()
    if not oid:
        raise ValueError("order_id_required")
    with _LOCK:
        data = _load()
        row = data.get("tokens", {}).get(code_h)
        if not row:
            raise ValueError("gift_code_not_found")
        if row.get("status") == "redeemed" or row.get("redeemed_at"):
            raise ValueError("gift_code_used")
        row["status"] = "redeemed"
        row["redeemed_at"] = _iso(_now())
        row["order_id"] = oid
        data["tokens"][code_h] = row
        _save(data)
    return {"ok": True, "order_id": oid, "package_id": row.get("package_id")}


def gift_public_flags(order: dict[str, Any] | None, *, ui_lang: str | None = None) -> dict[str, Any]:
    if not isinstance(order, dict):
        return {}
    is_gift = (
        str(order.get("payment_mode") or "").lower() == "gift"
        or order.get("gift") is True
        or order.get("is_gift") is True
    )
    if not is_gift:
        return {}
    lang = (ui_lang or "de")[:2].lower()
    if lang == "ru":
        banner = "Подарок Virtus Core — оплата не требуется. Деньги не списываются."
    elif lang == "en":
        banner = "Virtus Core gift — no payment required. No money is charged."
    else:
        banner = "Virtus Core Geschenk — keine Zahlung erforderlich. Es wird kein Geld abgebucht."
    awaiting = str(order.get("status") or "") in {
        "pending_confirmation",
        "confirmed",
        "awaiting_payment",
        "draft",
    } and not order.get("paid_at")
    return {
        "gift": True,
        "is_gift": True,
        "payment_mode": "gift",
        "gift_payment_available": awaiting,
        "demo_payment_available": awaiting,  # reuse existing checkout UI path
        "demo_payment_banner": banner,
        "demo": False,
        "counts_toward_revenue": False,
    }
