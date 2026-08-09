"""Per-customer channel credentials (Telegram tokens, Meta tokens, …).

Secrets live only in per-connection JSON files — never in index.json or logs.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_SECRET_KEYS = frozenset(
    {
        "token",
        "access_token",
        "refresh_token",
        "page_access_token",
        "user_access_token",
        "app_secret",
        "bot_token",
    }
)

_TELEGRAM_TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]+$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _credentials_dir(memory_dir: Path, customer_id: str) -> Path:
    cid = str(customer_id or "").strip()
    if not cid:
        raise ValueError("customer_id_required")
    path = Path(memory_dir) / "customer_identity" / cid / "channel_credentials"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path(memory_dir: Path, customer_id: str) -> Path:
    return _credentials_dir(memory_dir, customer_id) / "index.json"


def _connection_path(memory_dir: Path, customer_id: str, connection_id: str) -> Path:
    return _credentials_dir(memory_dir, customer_id) / f"{connection_id}.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_index(memory_dir: Path, customer_id: str) -> list[dict[str, Any]]:
    raw = _read_json(_index_path(memory_dir, customer_id))
    if not raw:
        return []
    rows = raw.get("connections")
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict)]


def _save_index(memory_dir: Path, customer_id: str, rows: list[dict[str, Any]]) -> None:
    _write_json(
        _index_path(memory_dir, customer_id),
        {"connections": rows, "updated_at": _utc_now_iso()},
    )


def _index_meta(record: dict[str, Any]) -> dict[str, Any]:
    """Metadata only — never persist secrets in the index."""
    telegram = record.get("telegram") if isinstance(record.get("telegram"), dict) else {}
    meta = {
        "connection_id": record.get("connection_id"),
        "channel": record.get("channel"),
        "bot_id": record.get("bot_id"),
        "status": record.get("status"),
        "updated_at": record.get("updated_at"),
    }
    if telegram:
        meta["telegram"] = {
            "id": telegram.get("id"),
            "username": telegram.get("username"),
        }
    if record.get("meta_channel"):
        meta["meta_channel"] = record.get("meta_channel")
    if record.get("page_id"):
        meta["page_id"] = record.get("page_id")
    if record.get("page_name"):
        meta["page_name"] = record.get("page_name")
    return {k: v for k, v in meta.items() if v is not None}


def _upsert_index(memory_dir: Path, customer_id: str, record: dict[str, Any]) -> None:
    rows = _load_index(memory_dir, customer_id)
    cid = str(record.get("connection_id") or "")
    meta = _index_meta(record)
    replaced = False
    for i, row in enumerate(rows):
        if str(row.get("connection_id") or "") == cid:
            rows[i] = meta
            replaced = True
            break
    if not replaced:
        rows.append(meta)
    _save_index(memory_dir, customer_id, rows)


def _remove_from_index(memory_dir: Path, customer_id: str, connection_id: str) -> None:
    rows = [
        r
        for r in _load_index(memory_dir, customer_id)
        if str(r.get("connection_id") or "") != connection_id
    ]
    _save_index(memory_dir, customer_id, rows)


def _mask_secret(value: object) -> str:
    text = str(value or "")
    if not text:
        return ""
    if len(text) <= 8:
        return "****"
    return f"{text[:4]}…{text[-4:]}"


def _public_view(record: dict[str, Any]) -> dict[str, Any]:
    """Return a copy safe for API responses (tokens masked)."""
    out: dict[str, Any] = {}
    for key, value in record.items():
        if key in _SECRET_KEYS:
            out[key] = _mask_secret(value)
            out[f"{key}_present"] = bool(value)
        elif isinstance(value, dict):
            nested = dict(value)
            for sk in _SECRET_KEYS:
                if sk in nested:
                    nested[sk] = _mask_secret(nested[sk])
                    nested[f"{sk}_present"] = bool(value.get(sk))
            out[key] = nested
        else:
            out[key] = value
    return out


def list_connections(memory_dir: Path, customer_id: str) -> list[dict[str, Any]]:
    """List connections for a customer. Tokens are masked."""
    rows: list[dict[str, Any]] = []
    for meta in _load_index(memory_dir, customer_id):
        conn_id = str(meta.get("connection_id") or "")
        if not conn_id:
            continue
        full = _read_json(_connection_path(memory_dir, customer_id, conn_id))
        if full:
            rows.append(_public_view(full))
        else:
            rows.append(dict(meta))
    return rows


def get_connection_secret(
    memory_dir: Path,
    customer_id: str,
    connection_id: str,
) -> dict[str, Any] | None:
    """Internal: full credential record including secrets (webhook use only)."""
    conn_id = str(connection_id or "").strip()
    if not conn_id:
        return None
    return _read_json(_connection_path(memory_dir, customer_id, conn_id))


def save_telegram_token(
    memory_dir: Path,
    customer_id: str,
    *,
    bot_id: str,
    token: str,
    channel: str = "telegram",
    connection_id: str | None = None,
) -> dict[str, Any]:
    """Validate token via Telegram getMe and persist credentials."""
    raw_token = str(token or "").strip()
    if not raw_token:
        return {"ok": False, "reason": "token_empty"}

    bid = str(bot_id or "").strip()
    if not bid:
        return {"ok": False, "reason": "bot_id_required"}

    ch = str(channel or "telegram").strip().lower() or "telegram"
    conn_id = str(connection_id or "").strip() or f"tg-{uuid.uuid4().hex[:12]}"

    # Never log token — only length / format hints
    if not _TELEGRAM_TOKEN_RE.match(raw_token):
        logger.info(
            "telegram_token_rejected customer=%s bot=%s reason=token_invalid_format",
            customer_id,
            bid,
        )
        return {"ok": False, "reason": "token_invalid_format"}

    try:
        with httpx.Client(timeout=20.0) as client:
            # Token is path-sensitive; do not put it in logs or exception messages.
            resp = client.get(f"https://api.telegram.org/bot{raw_token}/getMe")
    except httpx.HTTPError:
        logger.info(
            "telegram_getMe_network_error customer=%s bot=%s",
            customer_id,
            bid,
        )
        return {"ok": False, "reason": "telegram_network_error"}

    if resp.status_code != 200:
        logger.info(
            "telegram_getMe_http_error customer=%s bot=%s status=%s",
            customer_id,
            bid,
            resp.status_code,
        )
        return {"ok": False, "reason": "telegram_http_error", "http_status": resp.status_code}

    try:
        body = resp.json()
    except ValueError:
        return {"ok": False, "reason": "telegram_invalid_response"}

    if not isinstance(body, dict) or not body.get("ok"):
        desc = ""
        if isinstance(body, dict):
            desc = str(body.get("description") or "")[:120]
        logger.info(
            "telegram_getMe_rejected customer=%s bot=%s desc=%s",
            customer_id,
            bid,
            desc,
        )
        return {"ok": False, "reason": "telegram_auth_failed", "detail": desc or None}

    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    tg_id = result.get("id")
    tg_username = result.get("username")
    now = _utc_now_iso()
    record: dict[str, Any] = {
        "connection_id": conn_id,
        "channel": ch,
        "bot_id": bid,
        "status": "online",
        "telegram": {
            "id": tg_id,
            "username": tg_username,
            "is_bot": result.get("is_bot"),
            "first_name": result.get("first_name"),
        },
        "token": raw_token,
        "updated_at": now,
        "created_at": now,
    }

    existing = get_connection_secret(memory_dir, customer_id, conn_id)
    if existing and existing.get("created_at"):
        record["created_at"] = existing["created_at"]

    _write_json(_connection_path(memory_dir, customer_id, conn_id), record)
    _upsert_index(memory_dir, customer_id, record)
    logger.info(
        "telegram_connection_saved customer=%s bot=%s connection=%s username=%s",
        customer_id,
        bid,
        conn_id,
        tg_username,
    )
    webhook: dict[str, Any] = {"ok": True, "webhook_registered": False}
    try:
        from app.integration.workspace_bot_runtime import register_telegram_webhook

        webhook = register_telegram_webhook(raw_token, bid)
        record["webhook"] = {
            "registered": bool(webhook.get("webhook_registered")),
            "url": webhook.get("webhook_url"),
            "reason": webhook.get("reason"),
            "updated_at": _utc_now_iso(),
        }
        _write_json(_connection_path(memory_dir, customer_id, conn_id), record)
        _upsert_index(memory_dir, customer_id, record)
    except Exception:
        logger.exception(
            "telegram_setWebhook_failed customer=%s bot=%s", customer_id, bid
        )
        webhook = {"ok": False, "webhook_registered": False, "reason": "setWebhook_error"}
    out = {"ok": True, "connection": _public_view(record), "webhook": webhook}
    return out


def test_connection(
    memory_dir: Path,
    customer_id: str,
    connection_id: str,
) -> dict[str, Any]:
    """Re-validate a stored connection (Telegram getMe when applicable)."""
    conn_id = str(connection_id or "").strip()
    if not conn_id:
        return {"ok": False, "reason": "connection_id_required"}

    record = get_connection_secret(memory_dir, customer_id, conn_id)
    if not record:
        return {"ok": False, "reason": "connection_not_found"}

    channel = str(record.get("channel") or "").lower()
    if channel in {"telegram", "tg"}:
        token = str(record.get("token") or "").strip()
        if not token:
            return {"ok": False, "reason": "token_empty"}
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(f"https://api.telegram.org/bot{token}/getMe")
        except httpx.HTTPError:
            return {"ok": False, "reason": "telegram_network_error", "connection_id": conn_id}

        if resp.status_code != 200:
            record["status"] = "error"
            record["updated_at"] = _utc_now_iso()
            _write_json(_connection_path(memory_dir, customer_id, conn_id), record)
            _upsert_index(memory_dir, customer_id, record)
            return {
                "ok": False,
                "reason": "telegram_http_error",
                "http_status": resp.status_code,
                "connection_id": conn_id,
            }

        try:
            body = resp.json()
        except ValueError:
            return {"ok": False, "reason": "telegram_invalid_response", "connection_id": conn_id}

        if not isinstance(body, dict) or not body.get("ok"):
            record["status"] = "offline"
            record["updated_at"] = _utc_now_iso()
            _write_json(_connection_path(memory_dir, customer_id, conn_id), record)
            _upsert_index(memory_dir, customer_id, record)
            return {"ok": False, "reason": "telegram_auth_failed", "connection_id": conn_id}

        result = body.get("result") if isinstance(body.get("result"), dict) else {}
        record["status"] = "online"
        record["telegram"] = {
            "id": result.get("id"),
            "username": result.get("username"),
            "is_bot": result.get("is_bot"),
            "first_name": result.get("first_name"),
        }
        record["updated_at"] = _utc_now_iso()
        _write_json(_connection_path(memory_dir, customer_id, conn_id), record)
        _upsert_index(memory_dir, customer_id, record)
        return {"ok": True, "status": "online", "connection": _public_view(record)}

    # Non-Telegram: presence check only
    has_secret = any(record.get(k) for k in _SECRET_KEYS)
    if not has_secret:
        return {"ok": False, "reason": "secret_missing", "connection_id": conn_id}
    return {
        "ok": True,
        "status": str(record.get("status") or "stored"),
        "connection": _public_view(record),
    }


def disconnect(
    memory_dir: Path,
    customer_id: str,
    connection_id: str,
) -> dict[str, Any]:
    """Remove a connection file and drop it from the index."""
    conn_id = str(connection_id or "").strip()
    if not conn_id:
        return {"ok": False, "reason": "connection_id_required"}

    path = _connection_path(memory_dir, customer_id, conn_id)
    existed = path.is_file()
    if existed:
        try:
            path.unlink()
        except OSError:
            return {"ok": False, "reason": "disconnect_failed"}
    _remove_from_index(memory_dir, customer_id, conn_id)
    logger.info(
        "channel_disconnected customer=%s connection=%s existed=%s",
        customer_id,
        conn_id,
        existed,
    )
    return {"ok": True, "connection_id": conn_id, "removed": existed}


def save_channel_record(
    memory_dir: Path,
    customer_id: str,
    record: dict[str, Any],
) -> dict[str, Any]:
    """Persist an arbitrary channel credential record (Meta OAuth, etc.)."""
    conn_id = str(record.get("connection_id") or "").strip()
    if not conn_id:
        return {"ok": False, "reason": "connection_id_required"}
    if not record.get("channel"):
        return {"ok": False, "reason": "channel_required"}
    now = _utc_now_iso()
    payload = dict(record)
    payload.setdefault("created_at", now)
    payload["updated_at"] = now
    existing = get_connection_secret(memory_dir, customer_id, conn_id)
    if existing and existing.get("created_at"):
        payload["created_at"] = existing["created_at"]
    _write_json(_connection_path(memory_dir, customer_id, conn_id), payload)
    _upsert_index(memory_dir, customer_id, payload)
    return {"ok": True, "connection": _public_view(payload)}
