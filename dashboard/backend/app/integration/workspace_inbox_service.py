"""Virtus Unified Inbox — Phase 2.

Projects Telegram + Website Chat bot_sessions into one tenant-scoped inbox.
Does NOT rewrite generate_bot_reply. Does NOT implement Meta channels or AI Office.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from app.integration import workspace_ai_bots as wab
from app.integration.ai_employee_brain import SessionState, load_session, save_session
from app.integration.channel_engine import get_provider
from app.integration.channel_engine.types import NormalizedOutbound

LIVE_CHANNELS = ("telegram", "webchat")
_CABINET_PREFIX = "cabinet:"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sessions_root(memory_dir: Path, customer_id: str) -> Path:
    return Path(memory_dir) / "customer_identity" / str(customer_id) / "bot_sessions"


def _inbox_dir(memory_dir: Path, customer_id: str) -> Path:
    return Path(memory_dir) / "customer_identity" / str(customer_id) / "inbox"


def _reads_path(memory_dir: Path, customer_id: str) -> Path:
    return _inbox_dir(memory_dir, customer_id) / "reads.json"


def _load_reads(memory_dir: Path, customer_id: str) -> dict[str, str]:
    path = _reads_path(memory_dir, customer_id)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, str) and k and v:
            out[k] = v
    return out


def _save_reads(memory_dir: Path, customer_id: str, reads: dict[str, str]) -> None:
    path = _reads_path(memory_dir, customer_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def encode_thread_id(channel: str, bot_id: str, external_id: str) -> str:
    raw = f"{channel}|{bot_id}|{external_id}"
    return quote(raw, safe="")


def decode_thread_id(thread_id: str) -> tuple[str, str, str] | None:
    try:
        raw = unquote(str(thread_id or ""))
    except Exception:
        return None
    parts = raw.split("|", 2)
    if len(parts) != 3:
        return None
    channel, bot_id, external_id = (p.strip() for p in parts)
    if channel not in LIVE_CHANNELS or not bot_id or not external_id:
        return None
    return channel, bot_id, external_id


def _session_key(channel: str, external_id: str) -> str:
    if channel == "telegram":
        return f"tg:{external_id}"
    if channel == "webchat":
        return f"wch:{external_id}"
    return external_id


def _parse_session_file(name: str) -> tuple[str, str] | None:
    """Return (channel, external_id) from sanitized session filename stem."""
    stem = name[:-5] if name.endswith(".json") else name
    if stem.startswith("tg_"):
        return "telegram", stem[3:]
    if stem.startswith("tg:"):
        return "telegram", stem[3:]
    if stem.startswith("wch_"):
        return "webchat", stem[4:]
    if stem.startswith("wch:"):
        return "webchat", stem[4:]
    if stem.startswith("cabinet_") or stem.startswith("cabinet:"):
        return None
    return None


def _file_mtime_iso(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        )
    except OSError:
        return _utc_now()


def _preview_from_turns(turns: list[dict[str, str]]) -> str:
    if not turns:
        return ""
    last = turns[-1]
    return str(last.get("content") or "")[:180]


def _contact_label(channel: str, external_id: str, meta: dict[str, Any] | None) -> str:
    meta = meta if isinstance(meta, dict) else {}
    name = str(meta.get("sender_name") or meta.get("customer_name") or "").strip()
    if name:
        return name
    if channel == "telegram":
        return f"Telegram {external_id}"
    return f"Website {external_id[:12]}"


def _turns_to_messages(
    turns: list[dict[str, str]], *, channel: str
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, turn in enumerate(turns):
        role = str(turn.get("role") or "").lower()
        content = str(turn.get("content") or "")
        if not content:
            continue
        direction = "INBOUND" if role in ("user", "customer", "visitor") else "OUTBOUND"
        out.append(
            {
                "id": f"t{i}",
                "direction": direction,
                "role": role or ("user" if direction == "INBOUND" else "assistant"),
                "text": content,
                "channel": channel,
                "timestamp": str(turn.get("ts") or ""),
            }
        )
    return out


def list_threads(
    memory_dir: Path,
    customer_id: str,
    *,
    channel: str | None = None,
    unread_only: bool = False,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List inbox threads for this workspace only."""
    cid = str(customer_id)
    channel_filter = (channel or "").strip().lower() or None
    if channel_filter == "website":
        channel_filter = "webchat"
    if channel_filter and channel_filter not in LIVE_CHANNELS and channel_filter != "all":
        # Future channels accepted as empty filter result (extensible), not error.
        if channel_filter in ("whatsapp", "messenger", "instagram", "email"):
            return {
                "ok": True,
                "threads": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "channels_live": list(LIVE_CHANNELS),
            }

    reads = _load_reads(memory_dir, cid)
    bots = {b["bot_id"]: b for b in wab.list_bots(memory_dir, cid) if isinstance(b, dict)}
    root = _sessions_root(memory_dir, cid)
    threads: list[dict[str, Any]] = []

    if root.is_dir():
        for bot_dir in root.iterdir():
            if not bot_dir.is_dir():
                continue
            bot_id = bot_dir.name
            if bot_id not in bots:
                continue
            for path in bot_dir.glob("*.json"):
                parsed = _parse_session_file(path.name)
                if not parsed:
                    continue
                ch, external_id = parsed
                if channel_filter and channel_filter != "all" and ch != channel_filter:
                    continue
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                state = SessionState.from_dict(raw if isinstance(raw, dict) else {})
                if not state.turns:
                    continue
                session_key = _session_key(ch, external_id)
                # Prefer original external id from session_key if recoverable
                if session_key.startswith("tg:"):
                    external_id = session_key[3:]
                elif session_key.startswith("wch:"):
                    external_id = session_key[4:]
                # Recover from file content meta if present
                meta = raw.get("inbox_meta") if isinstance(raw, dict) else None
                thread_id = encode_thread_id(ch, bot_id, external_id)
                updated_at = str(
                    (raw.get("updated_at") if isinstance(raw, dict) else None) or _file_mtime_iso(path)
                )
                last_read = reads.get(thread_id) or ""
                unread = 1 if (not last_read or updated_at > last_read) else 0
                preview = _preview_from_turns(state.turns)
                label = _contact_label(ch, external_id, meta if isinstance(meta, dict) else {})
                bot_name = str(bots[bot_id].get("display_name") or bot_id)
                row = {
                    "thread_id": thread_id,
                    "channel": ch,
                    "bot_id": bot_id,
                    "bot_name": bot_name,
                    "external_id": external_id,
                    "session_key": session_key,
                    "customer_name": label,
                    "preview": preview,
                    "updated_at": updated_at,
                    "unread_count": unread,
                    "status": "open",
                    "handling": "ai_ready",
                    "message_count": len(state.turns),
                }
                if unread_only and unread <= 0:
                    continue
                if q:
                    needle = q.strip().lower()
                    hay = f"{label} {preview} {external_id} {bot_name} {ch}".lower()
                    # include turn text for search when reasonable
                    if needle and needle not in hay:
                        joined = " ".join(str(t.get("content") or "") for t in state.turns).lower()
                        if needle not in joined:
                            continue
                threads.append(row)

    threads.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
    total = len(threads)
    lim = max(1, min(int(limit or 50), 100))
    off = max(0, int(offset or 0))
    page = threads[off : off + lim]
    return {
        "ok": True,
        "threads": page,
        "total": total,
        "limit": lim,
        "offset": off,
        "channels_live": list(LIVE_CHANNELS),
    }


def get_thread(
    memory_dir: Path, customer_id: str, thread_id: str
) -> dict[str, Any]:
    from app.integration.ai_employee_brain import _session_path

    decoded = decode_thread_id(thread_id)
    if not decoded:
        return {"ok": False, "reason": "invalid_thread"}
    channel, bot_id, external_id = decoded
    cid = str(customer_id)
    bot = wab.get_bot(memory_dir, cid, bot_id)
    if not bot:
        return {"ok": False, "reason": "forbidden"}
    session_key = _session_key(channel, external_id)
    path = _session_path(memory_dir, cid, bot_id, session_key)
    if not path.is_file():
        return {"ok": False, "reason": "not_found"}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "reason": "not_found"}
    state = SessionState.from_dict(raw if isinstance(raw, dict) else {})
    if not state.turns:
        return {"ok": False, "reason": "not_found"}
    meta = raw.get("inbox_meta") if isinstance(raw, dict) else {}
    reads = _load_reads(memory_dir, cid)
    updated_at = str(
        (raw.get("updated_at") if isinstance(raw, dict) else None) or _file_mtime_iso(path)
    )
    last_read = reads.get(thread_id) or ""
    unread = 1 if (not last_read or updated_at > last_read) else 0
    return {
        "ok": True,
        "thread": {
            "thread_id": thread_id,
            "channel": channel,
            "bot_id": bot_id,
            "bot_name": str(bot.get("display_name") or bot_id),
            "external_id": external_id,
            "session_key": session_key,
            "customer_name": _contact_label(
                channel, external_id, meta if isinstance(meta, dict) else {}
            ),
            "updated_at": updated_at,
            "unread_count": unread,
            "status": "open",
            "handling": "ai_ready",
            "send_supported": channel == "telegram",
        },
        "messages": _turns_to_messages(state.turns, channel=channel),
    }


def mark_read(memory_dir: Path, customer_id: str, thread_id: str) -> dict[str, Any]:
    detail = get_thread(memory_dir, customer_id, thread_id)
    if not detail.get("ok"):
        return detail
    reads = _load_reads(memory_dir, customer_id)
    reads[thread_id] = _utc_now()
    _save_reads(memory_dir, customer_id, reads)
    return {"ok": True, "thread_id": thread_id, "read_at": reads[thread_id]}


def send_reply(
    memory_dir: Path,
    customer_id: str,
    thread_id: str,
    text: str,
) -> dict[str, Any]:
    """Human outbound via Channel Engine (Telegram). Website Chat = no push yet."""
    body = str(text or "").strip()
    if not body:
        return {"ok": False, "reason": "empty_message"}
    if len(body) > 4000:
        body = body[:4000]

    detail = get_thread(memory_dir, customer_id, thread_id)
    if not detail.get("ok"):
        return detail
    thread = detail["thread"]
    channel = str(thread["channel"])
    bot_id = str(thread["bot_id"])
    external_id = str(thread["external_id"])
    session_key = str(thread["session_key"])

    if channel != "telegram":
        return {
            "ok": False,
            "reason": "CHANNEL_SEND_UNSUPPORTED",
            "channel": channel,
            "detail": "Website Chat is visitor-initiated; push reply is not available yet.",
        }

    provider = get_provider("telegram")
    if provider is None:
        return {"ok": False, "reason": "telegram_provider_unavailable"}

    sent = provider.send(
        memory_dir,
        customer_id,
        NormalizedOutbound(conversation_external_id=external_id, text=body),
        bot_id=bot_id,
    )
    if not sent.get("ok"):
        return {
            "ok": False,
            "reason": str(sent.get("error") or "SEND_FAILED"),
            "provider": sent,
        }

    # Append outbound turn into existing session (same brain transcript).
    state = load_session(memory_dir, customer_id, bot_id, session_key)
    state.turns.append({"role": "assistant", "content": body, "ts": _utc_now()})
    save_session(memory_dir, customer_id, bot_id, session_key, state)

    from app.integration.ai_employee_brain import _session_path

    path = _session_path(memory_dir, customer_id, bot_id, session_key)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                raw["updated_at"] = _utc_now()
                path.write_text(
                    json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
        except (OSError, json.JSONDecodeError):
            pass

    mark_read(memory_dir, customer_id, thread_id)
    refreshed = get_thread(memory_dir, customer_id, thread_id)
    return {
        "ok": True,
        "thread_id": thread_id,
        "provider": {"ok": True, "channel_type": "telegram"},
        "messages": refreshed.get("messages") or [],
    }
