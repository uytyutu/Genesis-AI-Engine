"""Website Chat connector — commercial Live (Telegram + Website Chat).

Live flip after E2E PASS:

    create bot → create website channel → generate connection → embed
    → browser message → Virtus receives → AI processes → reply in widget
    → tenant isolation → disconnect / reconnect

WhatsApp / Instagram / Facebook Messenger stay Coming Soon until their
own connector E2E. Pricing SSOT: pricing_engine.BOT_CHANNELS_LIVE.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from app.integration import workspace_ai_bots as wab
from app.integration.workspace_bot_runtime import find_bot_owner, generate_bot_reply

ENGINE_ID = "website_chat_connector_v1"

# Commercial Live — flipped after pre-live gates + browser E2E PASS.
COMMERCIAL_LIVE = True
CHANNEL_ID = "website_chat"
CHANNEL_STATUS = "coming_soon" if not COMMERCIAL_LIVE else "live"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _channel_dir(memory_dir: Path, customer_id: str) -> Path:
    path = (
        Path(memory_dir)
        / "customer_identity"
        / str(customer_id).strip()
        / "website_chat"
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path(memory_dir: Path, customer_id: str) -> Path:
    return _channel_dir(memory_dir, customer_id) / "index.json"


def _conn_path(memory_dir: Path, customer_id: str, connection_id: str) -> Path:
    return _channel_dir(memory_dir, customer_id) / f"{connection_id}.json"


def _public_index_path(memory_dir: Path) -> Path:
    path = Path(memory_dir) / "website_chat_public_index.json"
    return path


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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _new_public_key() -> str:
    raw = secrets.token_urlsafe(24)
    return f"wc_{raw}"


def commercial_status() -> dict[str, Any]:
    return {
        "channel": CHANNEL_ID,
        "commercial_live": COMMERCIAL_LIVE,
        "status": CHANNEL_STATUS,
        "engine_id": ENGINE_ID,
        "note": (
            "Website Chat is commercial Live — connect in Client Workspace, "
            "embed widget, disconnect/reconnect supported."
            if COMMERCIAL_LIVE
            else "Not commercial Live — keep Coming Soon until E2E PASS."
        ),
    }


def list_connections(memory_dir: Path, customer_id: str) -> list[dict[str, Any]]:
    idx = _read_json(_index_path(memory_dir, customer_id)) or {}
    items = idx.get("connections") if isinstance(idx.get("connections"), list) else []
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("connection_id") or "")
        row = _read_json(_conn_path(memory_dir, customer_id, cid)) if cid else None
        if row:
            out.append(_public_view(row))
    return out


def _public_view(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "connection_id": row.get("connection_id"),
        "bot_id": row.get("bot_id"),
        "channel": CHANNEL_ID,
        "status": row.get("status"),
        "site_ref": row.get("site_ref"),
        "site_label": row.get("site_label"),
        "public_key": row.get("public_key"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "commercial_live": COMMERCIAL_LIVE,
    }


def _register_public_key(
    memory_dir: Path, *, public_key: str, customer_id: str, connection_id: str
) -> None:
    path = _public_index_path(memory_dir)
    idx = _read_json(path) or {"keys": {}}
    keys = idx.get("keys") if isinstance(idx.get("keys"), dict) else {}
    keys[public_key] = {
        "customer_id": customer_id,
        "connection_id": connection_id,
    }
    idx["keys"] = keys
    idx["updated_at"] = _utc_now_iso()
    _write_json(path, idx)


def _unregister_public_key(memory_dir: Path, public_key: str) -> None:
    path = _public_index_path(memory_dir)
    idx = _read_json(path) or {"keys": {}}
    keys = idx.get("keys") if isinstance(idx.get("keys"), dict) else {}
    keys.pop(str(public_key), None)
    idx["keys"] = keys
    idx["updated_at"] = _utc_now_iso()
    _write_json(path, idx)


def resolve_public_key(
    memory_dir: Path, public_key: str
) -> tuple[str, str] | None:
    idx = _read_json(_public_index_path(memory_dir)) or {}
    keys = idx.get("keys") if isinstance(idx.get("keys"), dict) else {}
    row = keys.get(str(public_key or "").strip())
    if not isinstance(row, dict):
        return None
    cid = str(row.get("customer_id") or "").strip()
    conn_id = str(row.get("connection_id") or "").strip()
    if not cid or not conn_id:
        return None
    return cid, conn_id


def create_website_channel(
    memory_dir: Path,
    customer_id: str,
    *,
    bot_id: str,
    site_ref: str | None = None,
    site_label: str | None = None,
) -> dict[str, Any]:
    """Create a Website Chat channel for an owned bot (Live)."""
    cid = str(customer_id or "").strip()
    bid = str(bot_id or "").strip()
    if not cid or not bid:
        return {"ok": False, "reason": "customer_or_bot_required"}

    bot = wab.get_bot(memory_dir, cid, bid)
    if not bot:
        return {"ok": False, "reason": "bot_not_found"}

    connection_id = f"wch-{uuid4().hex[:12]}"
    public_key = _new_public_key()
    now = _utc_now_iso()
    record = {
        "connection_id": connection_id,
        "bot_id": bid,
        "customer_id": cid,
        "channel": CHANNEL_ID,
        "status": "connected",
        "site_ref": (site_ref or "").strip() or None,
        "site_label": (site_label or "").strip() or (site_ref or "My website"),
        "public_key": public_key,
        "created_at": now,
        "updated_at": now,
        "engine_id": ENGINE_ID,
        "commercial_live": COMMERCIAL_LIVE,
        "message_count": 0,
    }
    _write_json(_conn_path(memory_dir, cid, connection_id), record)
    _register_public_key(
        memory_dir, public_key=public_key, customer_id=cid, connection_id=connection_id
    )

    idx = _read_json(_index_path(memory_dir, cid)) or {"connections": []}
    conns = idx.get("connections") if isinstance(idx.get("connections"), list) else []
    conns.append(
        {
            "connection_id": connection_id,
            "bot_id": bid,
            "public_key": public_key,
            "status": "connected",
        }
    )
    idx["connections"] = conns
    idx["updated_at"] = now
    _write_json(_index_path(memory_dir, cid), idx)

    return {
        "ok": True,
        "connection": _public_view(record),
        "embed": generate_embed_snippet(public_key),
        "commercial": commercial_status(),
    }


def generate_embed_snippet(public_key: str, *, api_base: str = "") -> dict[str, Any]:
    """Return install payload — primary UX is Connect, script is fallback."""
    key = str(public_key or "").strip()
    base = (api_base or "").rstrip("/")
    endpoint = f"{base}/api/public/website-chat/{key}/message" if base else f"/api/public/website-chat/{key}/message"
    script = (
        f'<script src="{base}/widget/website-chat.js" data-virtus-key="{key}" '
        f'data-endpoint="{endpoint}" async></script>'
        if base
        else f'<!-- Virtus Website Chat spike key={key} endpoint={endpoint} -->'
    )
    return {
        "public_key": key,
        "endpoint": endpoint,
        "script_fallback": script,
        "preferred_ux": "Connect to my website (no script required for Virtus-hosted sites)",
    }


def get_connection(
    memory_dir: Path, customer_id: str, connection_id: str
) -> dict[str, Any] | None:
    row = _read_json(_conn_path(memory_dir, customer_id, connection_id))
    return _public_view(row) if row else None


def disconnect_website_channel(
    memory_dir: Path, customer_id: str, connection_id: str
) -> dict[str, Any]:
    path = _conn_path(memory_dir, customer_id, connection_id)
    row = _read_json(path)
    if not row:
        return {"ok": False, "reason": "connection_not_found"}
    public_key = str(row.get("public_key") or "")
    row["status"] = "disconnected"
    row["updated_at"] = _utc_now_iso()
    _write_json(path, row)
    if public_key:
        _unregister_public_key(memory_dir, public_key)
    return {"ok": True, "connection": _public_view(row)}


def reconnect_website_channel(
    memory_dir: Path, customer_id: str, connection_id: str
) -> dict[str, Any]:
    path = _conn_path(memory_dir, customer_id, connection_id)
    row = _read_json(path)
    if not row:
        return {"ok": False, "reason": "connection_not_found"}
    if str(row.get("customer_id") or "") != str(customer_id):
        return {"ok": False, "reason": "tenant_mismatch"}
    public_key = str(row.get("public_key") or "") or _new_public_key()
    row["public_key"] = public_key
    row["status"] = "connected"
    row["updated_at"] = _utc_now_iso()
    _write_json(path, row)
    _register_public_key(
        memory_dir,
        public_key=public_key,
        customer_id=customer_id,
        connection_id=connection_id,
    )
    return {
        "ok": True,
        "connection": _public_view(row),
        "embed": generate_embed_snippet(public_key),
    }


def handle_website_chat_message(
    memory_dir: Path,
    public_key: str,
    message: str,
    *,
    visitor_id: str | None = None,
    llm_chat: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Inbound widget message → AI reply (tenant-scoped via public_key)."""
    resolved = resolve_public_key(memory_dir, public_key)
    if not resolved:
        return {"ok": False, "reason": "invalid_or_disconnected_key"}
    customer_id, connection_id = resolved
    row = _read_json(_conn_path(memory_dir, customer_id, connection_id))
    if not row:
        return {"ok": False, "reason": "connection_not_found"}
    if str(row.get("status") or "") != "connected":
        return {"ok": False, "reason": "disconnected"}
    if str(row.get("customer_id") or "") != customer_id:
        return {"ok": False, "reason": "tenant_mismatch"}

    bot_id = str(row.get("bot_id") or "")
    owned = find_bot_owner(memory_dir, bot_id)
    if not owned:
        return {"ok": False, "reason": "bot_not_found"}
    owner_id, bot = owned
    if owner_id != customer_id:
        return {"ok": False, "reason": "tenant_isolation_violation"}

    text = str(message or "").strip()
    if not text:
        return {"ok": False, "reason": "empty_message"}

    reply = generate_bot_reply(
        bot,
        text,
        llm_chat=llm_chat,
        memory_dir=memory_dir,
        customer_id=customer_id,
        session_key=f"wch:{visitor_id or public_key}",
    )
    row["message_count"] = int(row.get("message_count") or 0) + 1
    row["last_visitor_id"] = (
        str(visitor_id or "").strip()
        or hashlib.sha256(f"{public_key}:{row['message_count']}".encode()).hexdigest()[:16]
    )
    row["updated_at"] = _utc_now_iso()
    _write_json(_conn_path(memory_dir, customer_id, connection_id), row)

    return {
        "ok": True,
        "bot_id": bot_id,
        "customer_id": customer_id,
        "connection_id": connection_id,
        "reply": reply.get("text"),
        "source": reply.get("source"),
        "intent": reply.get("intent"),
        "commercial_live": COMMERCIAL_LIVE,
    }
