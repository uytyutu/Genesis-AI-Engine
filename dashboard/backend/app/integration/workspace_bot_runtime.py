"""AI Business Bot runtime — Telegram webhook replies from bot_config (ads-ready MVP)."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable

import httpx

from app.integration import workspace_ai_bots as wab
from app.integration import workspace_channel_credentials as wcc

logger = logging.getLogger(__name__)


def public_api_base() -> str:
    return (
        os.getenv("GENESIS_PUBLIC_URL", "").strip().rstrip("/")
        or os.getenv("GENESIS_PUBLIC_API_BASE", "").strip().rstrip("/")
        or ""
    )


def find_bot_owner(memory_dir: Path, bot_id: str) -> tuple[str, dict[str, Any]] | None:
    bid = str(bot_id or "").strip()
    if not bid:
        return None
    root = Path(memory_dir) / "customer_identity"
    if not root.is_dir():
        return None
    for cust_dir in root.iterdir():
        if not cust_dir.is_dir():
            continue
        bot = wab.get_bot(memory_dir, cust_dir.name, bid)
        if bot:
            return cust_dir.name, bot
    return None


def find_telegram_connection(
    memory_dir: Path, customer_id: str, bot_id: str
) -> dict[str, Any] | None:
    """Return secret credential record for this bot's Telegram connection."""
    bid = str(bot_id or "").strip()
    if not bid:
        return None
    # Prefer index lookup, then fall back to scanning connection files.
    for meta in wcc.list_connections(memory_dir, customer_id):
        if str(meta.get("bot_id") or "") != bid:
            continue
        ch = str(meta.get("channel") or "").lower()
        if ch and ch not in ("telegram", "tg"):
            continue
        conn_id = str(meta.get("connection_id") or "")
        secret = wcc.get_connection_secret(memory_dir, customer_id, conn_id)
        if secret and secret.get("token"):
            return secret

    cred_root = Path(memory_dir) / "customer_identity" / str(customer_id) / "channel_credentials"
    if not cred_root.is_dir():
        return None
    for path in cred_root.glob("*.json"):
        if path.name == "index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        if str(data.get("bot_id") or "") != bid:
            continue
        ch = str(data.get("channel") or "").lower()
        if ch and ch not in ("telegram", "tg"):
            continue
        if data.get("token"):
            return data
    return None


def build_system_prompt(bot: dict[str, Any]) -> str:
    cfg = bot.get("bot_config") if isinstance(bot.get("bot_config"), dict) else {}
    name = str(bot.get("display_name") or "Assistant")
    instructions = str(
        cfg.get("instructions")
        or cfg.get("ai_instructions")
        or cfg.get("system_prompt")
        or ""
    ).strip()
    tone = str(cfg.get("tone") or "professional").strip()
    faq = cfg.get("faq")
    faq_text = ""
    if isinstance(faq, list):
        parts = []
        for item in faq[:20]:
            if isinstance(item, dict):
                q = str(item.get("q") or item.get("question") or "").strip()
                a = str(item.get("a") or item.get("answer") or "").strip()
                if q or a:
                    parts.append(f"Q: {q}\nA: {a}")
            elif isinstance(item, str) and item.strip():
                parts.append(item.strip())
        faq_text = "\n\n".join(parts)
    elif isinstance(faq, str):
        faq_text = faq.strip()

    languages = cfg.get("languages") or []
    lang_hint = ", ".join(str(x) for x in languages[:6]) if languages else "user language"

    lines = [
        f"You are {name}, a digital employee for a small business.",
        f"Tone: {tone}.",
        f"Reply in the customer's language (prefer: {lang_hint}).",
        "Be concise and helpful. Collect leads when appropriate.",
        "Never invent company legal facts. If unknown, say you will have a human follow up.",
    ]
    if instructions:
        lines.append(f"Owner instructions:\n{instructions}")
    if faq_text:
        lines.append(f"FAQ knowledge:\n{faq_text}")
    return "\n\n".join(lines)


def faq_fallback_reply(bot: dict[str, Any], user_text: str) -> str:
    """Deterministic reply when LLM is unavailable — match FAQ or use instructions."""
    cfg = bot.get("bot_config") if isinstance(bot.get("bot_config"), dict) else {}
    name = str(bot.get("display_name") or "Assistant")
    low = (user_text or "").lower()
    faq = cfg.get("faq")
    if isinstance(faq, list):
        for item in faq:
            if not isinstance(item, dict):
                continue
            q = str(item.get("q") or item.get("question") or "")
            a = str(item.get("a") or item.get("answer") or "").strip()
            if not a:
                continue
            tokens = [t for t in re.split(r"\W+", q.lower()) if len(t) > 3]
            if tokens and any(t in low for t in tokens):
                return a
    instructions = str(
        cfg.get("instructions")
        or cfg.get("ai_instructions")
        or cfg.get("system_prompt")
        or ""
    ).strip()
    if instructions:
        snippet = instructions[:280]
        return (
            f"{name}: Thanks for your message. Based on our setup: {snippet}"
            + ("…" if len(instructions) > 280 else "")
        )
    return (
        f"{name}: Thanks for writing. A team member will follow up shortly. "
        "Please share your name and how we can help."
    )


def generate_bot_reply(
    bot: dict[str, Any],
    user_text: str,
    *,
    llm_chat: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate reply text from bot_config. Uses LLM when available, else FAQ fallback."""
    text = str(user_text or "").strip() or "Hello"
    system = build_system_prompt(bot)

    if llm_chat is not None:
        try:
            out = llm_chat(system=system, messages=[{"role": "user", "content": text}])
            answer = str((out or {}).get("answer") or "").strip()
            if answer:
                return {"ok": True, "text": answer, "source": "llm"}
        except Exception:
            logger.exception("bot_llm_reply_failed bot=%s", bot.get("bot_id"))

    # Try platform Groq/OpenAI-compatible providers
    try:
        from app.integration.genesis_brain.providers import build_provider_registry

        registry = build_provider_registry()
        for pid in ("groq", "openai", "openrouter", "ollama"):
            provider = registry.get(pid)
            if provider is None:
                continue
            try:
                if hasattr(provider, "available") and not provider.available():
                    continue
            except Exception:
                pass
            try:
                raw = provider.chat(
                    system=system,
                    messages=[{"role": "user", "content": text}],
                )
                answer = str(getattr(raw, "answer", None) or "").strip()
                if not answer and isinstance(raw, dict):
                    answer = str(
                        raw.get("answer") or raw.get("content") or raw.get("text") or ""
                    ).strip()
                if answer:
                    return {"ok": True, "text": answer, "source": pid}
            except Exception:
                logger.info("bot_provider_skip provider=%s bot=%s", pid, bot.get("bot_id"))
                continue
    except Exception:
        logger.exception("bot_provider_registry_failed")

    return {
        "ok": True,
        "text": faq_fallback_reply(bot, text),
        "source": "faq_fallback",
    }


def telegram_api(token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    with httpx.Client(timeout=25.0) as client:
        resp = client.post(url, json=payload or {})
    try:
        body = resp.json()
    except ValueError:
        body = {"ok": False, "description": "invalid_json"}
    if not isinstance(body, dict):
        return {"ok": False, "description": "invalid_response"}
    return body


def register_telegram_webhook(
    token: str,
    bot_id: str,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """setWebhook when public URL is configured; otherwise report skipped."""
    base = (base_url or public_api_base()).rstrip("/")
    if not base or "localhost" in base or "127.0.0.1" in base:
        return {
            "ok": True,
            "webhook_registered": False,
            "reason": "public_url_required",
            "hint": "Set GENESIS_PUBLIC_URL to an https base so Telegram can reach the webhook.",
        }
    webhook_url = f"{base}/api/webhooks/telegram/{bot_id}"
    body = telegram_api(
        token,
        "setWebhook",
        {"url": webhook_url, "allowed_updates": ["message"]},
    )
    return {
        "ok": bool(body.get("ok")),
        "webhook_registered": bool(body.get("ok")),
        "webhook_url": webhook_url,
        "telegram": body,
    }


def send_telegram_message(token: str, chat_id: int | str, text: str) -> dict[str, Any]:
    return telegram_api(
        token,
        "sendMessage",
        {"chat_id": chat_id, "text": text[:4000]},
    )


def handle_telegram_update(
    memory_dir: Path,
    bot_id: str,
    update: dict[str, Any],
    *,
    llm_chat: Callable[..., dict[str, Any]] | None = None,
    send: Callable[[str, int | str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Process one Telegram update: reply using bot_config."""
    owned = find_bot_owner(memory_dir, bot_id)
    if not owned:
        return {"ok": False, "reason": "bot_not_found"}
    customer_id, bot = owned

    message = update.get("message") if isinstance(update.get("message"), dict) else None
    if not message:
        return {"ok": True, "ignored": True, "reason": "no_message"}

    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    chat_id = chat.get("id")
    user_text = str(message.get("text") or message.get("caption") or "").strip()
    if chat_id is None:
        return {"ok": True, "ignored": True, "reason": "no_chat"}
    if not user_text:
        return {"ok": True, "ignored": True, "reason": "empty_text"}

    conn = find_telegram_connection(memory_dir, customer_id, bot_id)
    if not conn:
        return {"ok": False, "reason": "telegram_not_connected"}
    token = str(conn.get("token") or "")
    if not token:
        return {"ok": False, "reason": "token_missing"}

    reply = generate_bot_reply(bot, user_text, llm_chat=llm_chat)
    sender = send or send_telegram_message
    sent = sender(token, chat_id, reply["text"])
    return {
        "ok": bool(sent.get("ok")),
        "bot_id": bot_id,
        "customer_id": customer_id,
        "reply_source": reply.get("source"),
        "reply_text": reply.get("text"),
        "telegram": sent,
    }
