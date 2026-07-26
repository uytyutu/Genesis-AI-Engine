"""Email Provider Pool — Resend → Gmail → Mailbox.org SMTP failover.

Does not replace ReceiptEmailService / outreach APIs — only the transport chain.
Does not bypass provider rate limits. When one fails, try the next.
When Resend is healthy again (not in cooldown), it is automatically primary again.
Persists last errors + send journal (no secrets) for CEO Health Dashboard.
"""

from __future__ import annotations

import json
import logging
import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Callable

import httpx

logger = logging.getLogger("genesis.email_pool")

# Canonical chain (CEO): Resend → Gmail → Mailbox.org
# Optional extras stay available via EMAIL_PROVIDER_ORDER override.
_CORE_ORDER: tuple[str, ...] = ("resend", "gmail", "mailbox")
_OPTIONAL_ORDER: tuple[str, ...] = ("smtp", "ses", "mailgun")
_DEFAULT_ORDER: tuple[str, ...] = _CORE_ORDER + _OPTIONAL_ORDER
_KNOWN_PROVIDERS: frozenset[str] = frozenset(_DEFAULT_ORDER)
_STATE_FILE = "email_provider_pool_state.json"
_JOURNAL_FILE = "email_provider_send_journal.jsonl"
_JOURNAL_KEEP = 200
_COOLDOWN_SEC = {
    "resend": 900,
    "gmail": 600,
    "mailbox": 300,
    "smtp": 300,
    "ses": 300,
    "mailgun": 300,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


def _parse_iso(raw: object) -> datetime | None:
    if not raw:
        return None
    try:
        text = str(raw).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def provider_order() -> list[str]:
    raw = os.getenv("EMAIL_PROVIDER_ORDER", "").strip()
    if not raw:
        # Primary chain only unless extras are configured via order override
        return ["resend", "gmail", "mailbox"]
    out: list[str] = []
    for part in raw.split(","):
        key = part.strip().lower()
        if key in _KNOWN_PROVIDERS and key not in out:
            out.append(key)
    return out or ["resend", "gmail", "mailbox"]


def _state_path(memory_dir: Path | None) -> Path | None:
    if not memory_dir:
        return None
    return Path(memory_dir) / _STATE_FILE


def _load_state(memory_dir: Path | None) -> dict[str, Any]:
    path = _state_path(memory_dir)
    empty = {"providers": {}, "updated_at": None}
    if not path or not path.is_file():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    if not isinstance(data, dict):
        return empty
    providers = data.get("providers")
    if not isinstance(providers, dict):
        data["providers"] = {}
    return data


def _save_state(memory_dir: Path | None, data: dict[str, Any]) -> None:
    path = _state_path(memory_dir)
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _iso()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_provider_result(
    memory_dir: Path | None,
    provider: str,
    *,
    ok: bool,
    reason: str = "",
    http_status: int | None = None,
    detail: str = "",
    cooldown_sec: int | None = None,
) -> None:
    """Persist last outcome for Health Dashboard (never stores tokens)."""
    state = _load_state(memory_dir)
    providers = state.setdefault("providers", {})
    row: dict[str, Any] = {
        "last_ok": bool(ok),
        "last_at": _iso(),
        "last_reason": str(reason or "")[:120] or None,
        "last_http_status": http_status,
        "last_detail": str(detail or "")[:400] or None,
        "cooldown_until": None,
    }
    if not ok:
        sec = cooldown_sec
        if sec is None:
            # Rate limits get provider-specific pause
            if http_status == 429 or "429" in str(reason) or "rate" in str(reason).lower():
                sec = _COOLDOWN_SEC.get(provider, 300)
            else:
                sec = 60
        row["cooldown_until"] = _iso(_utc_now() + timedelta(seconds=max(30, int(sec))))
    providers[provider] = row
    # Also keep legacy Resend cooldown file in sync for older gates
    if provider == "resend" and not ok and (
        http_status == 429 or str(reason).startswith("resend_error:429")
    ):
        try:
            from app.integration.outreach_provider_cooldown import mark_resend_rate_limited

            mark_resend_rate_limited(
                memory_dir, reason=str(reason or "resend_error:429")[:80]
            )
        except Exception:
            pass
    _save_state(memory_dir, state)


def clear_provider_cooldown(
    memory_dir: Path | None,
    provider: str | None = None,
) -> dict[str, Any]:
    state = _load_state(memory_dir)
    providers = state.setdefault("providers", {})
    cleared: list[str] = []
    targets = [provider] if provider else list(providers.keys())
    for pid in targets:
        row = providers.get(pid)
        if isinstance(row, dict):
            row["cooldown_until"] = None
            cleared.append(pid)
    _save_state(memory_dir, state)
    if provider in (None, "resend"):
        try:
            from app.integration.outreach_provider_cooldown import clear_resend_cooldown

            clear_resend_cooldown(memory_dir, cleared_reason="cleared_via_provider_pool")
        except Exception:
            pass
    return {"ok": True, "cleared": cleared}


def _in_cooldown(memory_dir: Path | None, provider: str) -> bool:
    state = _load_state(memory_dir)
    row = (state.get("providers") or {}).get(provider) or {}
    until = _parse_iso(row.get("cooldown_until") if isinstance(row, dict) else None)
    if until and _utc_now() < until:
        return True
    # Legacy Resend file
    if provider == "resend":
        try:
            from app.integration.outreach_provider_cooldown import resend_available

            if not resend_available(memory_dir):
                return True
        except Exception:
            pass
    return False


def _default_from() -> str:
    return (
        os.getenv("GENESIS_EMAIL_FROM", "").strip()
        or os.getenv("MAILBOX_SMTP_FROM", "").strip()
        or os.getenv("GMAIL_SENDER", "").strip()
        or os.getenv("SMTP_FROM", "").strip()
        or os.getenv("SES_FROM", "").strip()
        or os.getenv("MAILGUN_FROM", "").strip()
    )


def _journal_path(memory_dir: Path | None) -> Path | None:
    if not memory_dir:
        return None
    return Path(memory_dir) / _JOURNAL_FILE


def append_send_journal(
    memory_dir: Path | None,
    *,
    provider: str,
    to: str,
    subject: str,
    message_id: str | None = None,
    attempts: list[dict[str, Any]] | None = None,
) -> None:
    """Append one successful delivery: provider in {resend, gmail, mailbox, ...}."""
    path = _journal_path(memory_dir)
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    to_safe = (to or "").strip()
    if "@" in to_safe:
        local, dom = to_safe.split("@", 1)
        to_safe = f"{(local[:1] or '*')}***@{dom}"
    row = {
        "at": _iso(),
        "provider": str(provider or "").strip().lower() or "unknown",
        "to": to_safe,
        "subject": str(subject or "")[:120],
        "id": (str(message_id)[:80] if message_id else None),
        "fallback_chain": [
            str(a.get("provider") or "")
            for a in (attempts or [])
            if isinstance(a, dict)
        ],
    }
    try:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("email send journal write failed: %s", exc)
        return
    # Trim to last N lines (best-effort)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > _JOURNAL_KEEP:
            path.write_text(
                "\n".join(lines[-_JOURNAL_KEEP:]) + "\n", encoding="utf-8"
            )
    except OSError:
        pass


def recent_send_journal(
    memory_dir: Path | None, *, limit: int = 20
) -> list[dict[str, Any]]:
    path = _journal_path(memory_dir)
    if not path or not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
        if len(out) >= max(1, int(limit)):
            break
    return out


def _mailbox_settings() -> dict[str, Any]:
    """Read MAILBOX_SMTP_* (CEO contract). Defaults match mailbox.org docs."""
    host = (
        os.getenv("MAILBOX_SMTP_HOST", "").strip()
        or os.getenv("SMTP_HOST", "").strip()
    )
    # If only MAILBOX_SMTP_USER is set, assume official mailbox.org host
    user = (
        os.getenv("MAILBOX_SMTP_USER", "").strip()
        or os.getenv("SMTP_USER", "").strip()
    )
    password = (
        os.getenv("MAILBOX_SMTP_PASSWORD", "").strip()
        or os.getenv("SMTP_PASSWORD", "").strip()
    )
    if user and not host:
        host = "smtp.mailbox.org"
    port_raw = (
        os.getenv("MAILBOX_SMTP_PORT", "").strip()
        or os.getenv("SMTP_PORT", "").strip()
        or "587"
    )
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    secure_raw = (
        os.getenv("MAILBOX_SMTP_SECURE", "").strip()
        or os.getenv("SMTP_USE_TLS", "").strip()
        or ("true" if port == 465 else "starttls")
    ).lower()
    # true / ssl / 1 → SMTP_SSL; false / 0 → plain; else STARTTLS
    if secure_raw in ("1", "true", "yes", "ssl", "smtps"):
        mode = "ssl"
    elif secure_raw in ("0", "false", "no", "plain"):
        mode = "plain"
    else:
        mode = "starttls"
    frm = (
        os.getenv("MAILBOX_SMTP_FROM", "").strip()
        or os.getenv("SMTP_FROM", "").strip()
        or user
        or _default_from()
    )
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "mode": mode,
        "from": frm,
        "configured": bool(host and user and password and frm),
    }


# --- Provider adapters ---------------------------------------------------------


def _probe_resend() -> dict[str, Any]:
    key = bool(os.getenv("RESEND_API_KEY", "").strip())
    frm = bool(_default_from())
    return {
        "id": "resend",
        "label": "Resend",
        "configured": key and frm,
        "env_required": ["RESEND_API_KEY", "GENESIS_EMAIL_FROM"],
        "role": "primary",
    }


def _send_resend(
    *,
    to: str,
    subject: str,
    text: str,
    html: str,
    from_addr: str,
    list_unsubscribe: str,
    bcc: str,
    memory_dir: Path | None,
) -> dict[str, Any]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    if not api_key or not from_addr:
        return {"ok": False, "skipped": True, "reason": "resend_not_configured", "provider": "resend"}
    if _in_cooldown(memory_dir, "resend"):
        return {
            "ok": False,
            "skipped": True,
            "reason": "resend_cooldown",
            "provider": "resend",
            "detail": "Resend on cooldown — trying next provider",
        }
    payload: dict[str, Any] = {
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "text": text,
        "html": html,
    }
    if bcc.strip():
        payload["bcc"] = [bcc.strip()]
    headers = {"Authorization": f"Bearer {api_key}"}
    if list_unsubscribe.strip():
        headers["List-Unsubscribe"] = list_unsubscribe.strip()
    try:
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        record_provider_result(
            memory_dir, "resend", ok=False, reason="network_error", detail=str(exc)[:200]
        )
        return {"ok": False, "provider": "resend", "reason": "network_error", "detail": str(exc)[:160]}
    if res.status_code < 400:
        record_provider_result(memory_dir, "resend", ok=True, http_status=res.status_code)
        return {
            "ok": True,
            "provider": "resend",
            "from": from_addr,
            "id": (res.json() or {}).get("id"),
        }
    reason = f"resend_error:{res.status_code}"
    detail = (res.text or "")[:400]
    record_provider_result(
        memory_dir,
        "resend",
        ok=False,
        reason=reason,
        http_status=res.status_code,
        detail=detail,
    )
    return {
        "ok": False,
        "provider": "resend",
        "reason": reason,
        "detail": detail[:200],
        "http_status": res.status_code,
    }


def _probe_gmail() -> dict[str, Any]:
    try:
        from app.integration.gmail_mail_service import send_ready

        ready = bool(send_ready())
    except Exception:
        ready = False
    return {
        "id": "gmail",
        "label": "Gmail",
        "configured": ready,
        "env_required": ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN", "GMAIL_SENDER"],
        "role": "failover",
    }


def _send_gmail(
    *,
    to: str,
    subject: str,
    text: str,
    html: str,
    from_addr: str,
    list_unsubscribe: str,
    bcc: str,  # noqa: ARG001
    memory_dir: Path | None,
) -> dict[str, Any]:
    if _in_cooldown(memory_dir, "gmail"):
        return {
            "ok": False,
            "skipped": True,
            "reason": "gmail_cooldown",
            "provider": "gmail",
            "detail": "Gmail on cooldown — trying next provider",
        }
    from app.integration.gmail_mail_service import send_email as gmail_send

    result = gmail_send(
        to=to,
        subject=subject,
        text=text,
        html=html,
        from_addr=from_addr or None,
        list_unsubscribe=list_unsubscribe,
    )
    result = dict(result)
    result["provider"] = result.get("provider") or "gmail"
    if result.get("ok"):
        record_provider_result(memory_dir, "gmail", ok=True)
    else:
        reason = str(result.get("reason") or "gmail_failed")
        detail = str(result.get("detail") or "")[:400]
        http_status = None
        if "gmail_error:" in reason:
            try:
                http_status = int(reason.split(":", 1)[1])
            except ValueError:
                http_status = None
        record_provider_result(
            memory_dir,
            "gmail",
            ok=False,
            reason=reason,
            http_status=http_status,
            detail=detail,
        )
    return result


def _probe_mailbox() -> dict[str, Any]:
    cfg = _mailbox_settings()
    return {
        "id": "mailbox",
        "label": "Mailbox.org",
        "configured": bool(cfg.get("configured")),
        "env_required": [
            "MAILBOX_SMTP_HOST",
            "MAILBOX_SMTP_PORT",
            "MAILBOX_SMTP_USER",
            "MAILBOX_SMTP_PASSWORD",
            "MAILBOX_SMTP_SECURE",
        ],
        "role": "failover",
        "host": cfg.get("host") or None,
        "port": cfg.get("port"),
        "mode": cfg.get("mode"),
    }


def _send_mailbox(
    *,
    to: str,
    subject: str,
    text: str,
    html: str,
    from_addr: str,
    list_unsubscribe: str,
    bcc: str,
    memory_dir: Path | None,
) -> dict[str, Any]:
    cfg = _mailbox_settings()
    host = str(cfg.get("host") or "")
    port = int(cfg.get("port") or 587)
    user = str(cfg.get("user") or "")
    password = str(cfg.get("password") or "")
    mode = str(cfg.get("mode") or "starttls")
    # Mailbox.org only accepts From owned by the SMTP user — never reuse Resend domain.
    mailbox_from = (str(cfg.get("from") or "") or user).strip()
    frm = mailbox_from
    if from_addr.strip():
        candidate = from_addr.strip()
        # Allow explicit override only when it matches mailbox identity
        cand_addr = candidate
        if "<" in candidate and ">" in candidate:
            cand_addr = candidate.split("<", 1)[1].split(">", 1)[0].strip()
        if cand_addr.lower() == user.lower() or cand_addr.lower() == mailbox_from.lower():
            frm = candidate
    if not (host and user and password and frm):
        return {
            "ok": False,
            "skipped": True,
            "reason": "mailbox_not_configured",
            "provider": "mailbox",
        }
    if _in_cooldown(memory_dir, "mailbox"):
        return {
            "ok": False,
            "skipped": True,
            "reason": "mailbox_cooldown",
            "provider": "mailbox",
            "detail": "Mailbox.org on cooldown — trying next provider",
        }
    if html.strip():
        msg: MIMEMultipart | MIMEText = MIMEMultipart("alternative")
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = frm
    msg["To"] = to
    if list_unsubscribe.strip():
        msg["List-Unsubscribe"] = list_unsubscribe.strip()
    recipients = [to]
    if bcc.strip():
        recipients.append(bcc.strip())
    context = ssl.create_default_context()
    try:
        if mode == "ssl":
            with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as server:
                server.login(user, password)
                server.sendmail(frm, recipients, msg.as_string())
        elif mode == "plain":
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.login(user, password)
                server.sendmail(frm, recipients, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(user, password)
                server.sendmail(frm, recipients, msg.as_string())
    except Exception as exc:
        detail = str(exc)[:400]
        record_provider_result(
            memory_dir, "mailbox", ok=False, reason="mailbox_error", detail=detail
        )
        return {
            "ok": False,
            "provider": "mailbox",
            "reason": "mailbox_error",
            "detail": detail[:200],
        }
    mid = f"mailbox-{_iso()}"
    record_provider_result(memory_dir, "mailbox", ok=True)
    return {"ok": True, "provider": "mailbox", "from": frm, "id": mid}


def _probe_smtp() -> dict[str, Any]:
    # Generic SMTP — skip if same credentials already covered by mailbox
    mb = _mailbox_settings()
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    frm = bool(os.getenv("SMTP_FROM", "").strip() or _default_from())
    configured = bool(host and user and password and frm)
    if configured and mb.get("configured") and host == mb.get("host") and user == mb.get("user"):
        configured = False
    return {
        "id": "smtp",
        "label": "SMTP",
        "configured": configured,
        "env_required": ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM"],
        "role": "failover",
    }


def _send_smtp(
    *,
    to: str,
    subject: str,
    text: str,
    html: str,
    from_addr: str,
    list_unsubscribe: str,
    bcc: str,
    memory_dir: Path | None,
) -> dict[str, Any]:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587") or 587)
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    frm = (from_addr or os.getenv("SMTP_FROM", "").strip() or _default_from()).strip()
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in ("0", "false", "no")
    if not (host and user and password and frm):
        return {"ok": False, "skipped": True, "reason": "smtp_not_configured", "provider": "smtp"}
    if _in_cooldown(memory_dir, "smtp"):
        return {"ok": False, "skipped": True, "reason": "smtp_cooldown", "provider": "smtp"}
    msg: MIMEMultipart | MIMEText
    if html.strip():
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = frm
    msg["To"] = to
    if list_unsubscribe.strip():
        msg["List-Unsubscribe"] = list_unsubscribe.strip()
    recipients = [to]
    if bcc.strip():
        recipients.append(bcc.strip())
    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(user, password)
                server.sendmail(frm, recipients, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.login(user, password)
                server.sendmail(frm, recipients, msg.as_string())
    except Exception as exc:
        detail = str(exc)[:400]
        record_provider_result(
            memory_dir, "smtp", ok=False, reason="smtp_error", detail=detail
        )
        return {"ok": False, "provider": "smtp", "reason": "smtp_error", "detail": detail[:200]}
    record_provider_result(memory_dir, "smtp", ok=True)
    return {"ok": True, "provider": "smtp", "from": frm, "id": f"smtp-{_iso()}"}


def _probe_ses() -> dict[str, Any]:
    key = bool(os.getenv("AWS_ACCESS_KEY_ID", "").strip())
    secret = bool(os.getenv("AWS_SECRET_ACCESS_KEY", "").strip())
    region = bool(os.getenv("AWS_REGION", "").strip() or os.getenv("SES_REGION", "").strip())
    frm = bool(os.getenv("SES_FROM", "").strip() or _default_from())
    has_boto = False
    try:
        import boto3  # noqa: F401

        has_boto = True
    except ImportError:
        has_boto = False
    return {
        "id": "ses",
        "label": "Amazon SES",
        "configured": key and secret and region and frm and has_boto,
        "env_required": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "SES_FROM"],
        "role": "failover",
        "note_ru": None if has_boto else "Нужен пакет boto3 (pip install boto3)",
    }


def _send_ses(
    *,
    to: str,
    subject: str,
    text: str,
    html: str,
    from_addr: str,
    list_unsubscribe: str,
    bcc: str,
    memory_dir: Path | None,
) -> dict[str, Any]:
    frm = (from_addr or os.getenv("SES_FROM", "").strip() or _default_from()).strip()
    region = (
        os.getenv("AWS_REGION", "").strip() or os.getenv("SES_REGION", "").strip() or "eu-central-1"
    )
    if not (
        os.getenv("AWS_ACCESS_KEY_ID", "").strip()
        and os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
        and frm
    ):
        return {"ok": False, "skipped": True, "reason": "ses_not_configured", "provider": "ses"}
    if _in_cooldown(memory_dir, "ses"):
        return {"ok": False, "skipped": True, "reason": "ses_cooldown", "provider": "ses"}
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        return {
            "ok": False,
            "skipped": True,
            "reason": "ses_boto3_missing",
            "provider": "ses",
            "detail": "pip install boto3",
        }
    dest: dict[str, Any] = {"ToAddresses": [to]}
    if bcc.strip():
        dest["BccAddresses"] = [bcc.strip()]
    body: dict[str, Any] = {"Text": {"Data": text, "Charset": "UTF-8"}}
    if html.strip():
        body["Html"] = {"Data": html, "Charset": "UTF-8"}
    headers = []
    if list_unsubscribe.strip():
        headers.append({"Name": "List-Unsubscribe", "Value": list_unsubscribe.strip()})
    try:
        client = boto3.client("ses", region_name=region)
        kwargs: dict[str, Any] = {
            "Source": frm,
            "Destination": dest,
            "Message": {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body,
            },
        }
        # Simple send_email does not support arbitrary headers; omit List-Unsubscribe if needed.
        resp = client.send_email(**kwargs)
        mid = (resp or {}).get("MessageId")
        record_provider_result(memory_dir, "ses", ok=True)
        return {"ok": True, "provider": "ses", "from": frm, "id": mid}
    except (BotoCoreError, ClientError, Exception) as exc:
        detail = str(exc)[:400]
        status = None
        if hasattr(exc, "response") and isinstance(getattr(exc, "response", None), dict):
            status = (exc.response.get("ResponseMetadata") or {}).get("HTTPStatusCode")
        record_provider_result(
            memory_dir,
            "ses",
            ok=False,
            reason="ses_error",
            http_status=status,
            detail=detail,
        )
        return {
            "ok": False,
            "provider": "ses",
            "reason": "ses_error",
            "detail": detail[:200],
            "http_status": status,
        }


def _probe_mailgun() -> dict[str, Any]:
    key = bool(os.getenv("MAILGUN_API_KEY", "").strip())
    domain = bool(os.getenv("MAILGUN_DOMAIN", "").strip())
    frm = bool(os.getenv("MAILGUN_FROM", "").strip() or _default_from())
    return {
        "id": "mailgun",
        "label": "Mailgun",
        "configured": key and domain and frm,
        "env_required": ["MAILGUN_API_KEY", "MAILGUN_DOMAIN", "MAILGUN_FROM"],
        "role": "failover",
    }


def _send_mailgun(
    *,
    to: str,
    subject: str,
    text: str,
    html: str,
    from_addr: str,
    list_unsubscribe: str,
    bcc: str,
    memory_dir: Path | None,
) -> dict[str, Any]:
    api_key = os.getenv("MAILGUN_API_KEY", "").strip()
    domain = os.getenv("MAILGUN_DOMAIN", "").strip()
    frm = (from_addr or os.getenv("MAILGUN_FROM", "").strip() or _default_from()).strip()
    base = os.getenv("MAILGUN_API_BASE", "https://api.mailgun.net/v3").rstrip("/")
    if not (api_key and domain and frm):
        return {
            "ok": False,
            "skipped": True,
            "reason": "mailgun_not_configured",
            "provider": "mailgun",
        }
    if _in_cooldown(memory_dir, "mailgun"):
        return {
            "ok": False,
            "skipped": True,
            "reason": "mailgun_cooldown",
            "provider": "mailgun",
        }
    data: dict[str, Any] = {
        "from": frm,
        "to": [to],
        "subject": subject,
        "text": text,
    }
    if html.strip():
        data["html"] = html
    if bcc.strip():
        data["bcc"] = bcc.strip()
    if list_unsubscribe.strip():
        data["h:List-Unsubscribe"] = list_unsubscribe.strip()
    try:
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                f"{base}/{domain}/messages",
                auth=("api", api_key),
                data=data,
            )
    except httpx.HTTPError as exc:
        record_provider_result(
            memory_dir, "mailgun", ok=False, reason="network_error", detail=str(exc)[:200]
        )
        return {
            "ok": False,
            "provider": "mailgun",
            "reason": "network_error",
            "detail": str(exc)[:160],
        }
    if res.status_code < 400:
        body = res.json() if res.content else {}
        record_provider_result(memory_dir, "mailgun", ok=True, http_status=res.status_code)
        return {
            "ok": True,
            "provider": "mailgun",
            "from": frm,
            "id": body.get("id"),
        }
    detail = (res.text or "")[:400]
    record_provider_result(
        memory_dir,
        "mailgun",
        ok=False,
        reason=f"mailgun_error:{res.status_code}",
        http_status=res.status_code,
        detail=detail,
    )
    return {
        "ok": False,
        "provider": "mailgun",
        "reason": f"mailgun_error:{res.status_code}",
        "detail": detail[:200],
        "http_status": res.status_code,
    }


_SENDERS: dict[str, Callable[..., dict[str, Any]]] = {
    "resend": _send_resend,
    "gmail": _send_gmail,
    "mailbox": _send_mailbox,
    "smtp": _send_smtp,
    "ses": _send_ses,
    "mailgun": _send_mailgun,
}

_PROBERS: dict[str, Callable[[], dict[str, Any]]] = {
    "resend": _probe_resend,
    "gmail": _probe_gmail,
    "mailbox": _probe_mailbox,
    "smtp": _probe_smtp,
    "ses": _probe_ses,
    "mailgun": _probe_mailgun,
}


def send_via_pool(
    *,
    to: str,
    subject: str,
    text: str,
    html: str = "",
    from_addr: str | None = None,
    list_unsubscribe: str = "",
    bcc: str = "",
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    """Try providers in order until one succeeds. Never stops the system on one failure."""
    if not to:
        return {"ok": False, "skipped": True, "reason": "no_email"}
    resolved_from = (from_addr or "").strip() or _default_from()
    attempts: list[dict[str, Any]] = []
    for pid in provider_order():
        sender = _SENDERS.get(pid)
        if not sender:
            continue
        probe = _PROBERS[pid]()
        if not probe.get("configured"):
            attempts.append(
                {
                    "provider": pid,
                    "ok": False,
                    "skipped": True,
                    "reason": f"{pid}_not_configured",
                }
            )
            continue
        result = sender(
            to=to,
            subject=subject,
            text=text,
            html=html,
            from_addr=resolved_from,
            list_unsubscribe=list_unsubscribe,
            bcc=bcc,
            memory_dir=memory_dir,
        )
        attempts.append(
            {
                "provider": pid,
                "ok": bool(result.get("ok")),
                "skipped": bool(result.get("skipped")),
                "reason": result.get("reason"),
                "http_status": result.get("http_status"),
            }
        )
        if result.get("ok"):
            provider_used = str(result.get("provider") or pid)
            append_send_journal(
                memory_dir,
                provider=provider_used,
                to=to,
                subject=subject,
                message_id=str(result.get("id") or "") or None,
                attempts=attempts,
            )
            # Successful Resend delivery clears cooldown so it stays primary
            if provider_used == "resend":
                clear_provider_cooldown(memory_dir, "resend")
            return {
                **result,
                "pool": True,
                "attempts": attempts,
                "fallback_chain": [a["provider"] for a in attempts],
            }
    return {
        "ok": False,
        "skipped": False,
        "reason": "all_providers_failed",
        "provider": None,
        "pool": True,
        "attempts": attempts,
        "detail_ru": (
            "Все почтовые провайдеры недоступны или на cooldown. "
            "Очередь ждёт — система не остановлена."
        ),
    }


def any_provider_ready(memory_dir: Path | None = None) -> bool:
    for pid in provider_order():
        probe = _PROBERS[pid]()
        if probe.get("configured") and not _in_cooldown(memory_dir, pid):
            return True
    return False


def email_providers_health(
    memory_dir: Path | None = None,
    *,
    domain_quota: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """CEO Health Dashboard payload — lamps + today's quota + last errors."""
    state = _load_state(memory_dir)
    providers_out: list[dict[str, Any]] = []
    ready_ids: list[str] = []
    for pid in provider_order():
        probe = _PROBERS[pid]()
        row = (state.get("providers") or {}).get(pid) or {}
        if not isinstance(row, dict):
            row = {}
        cooling = _in_cooldown(memory_dir, pid)
        configured = bool(probe.get("configured"))
        if configured and not cooling:
            lamp = "green"
            ready_ids.append(pid)
        elif configured and cooling:
            lamp = "yellow"
        elif configured:
            lamp = "red"
        else:
            lamp = "gray"
        # Strong red if last error was 429
        if row.get("last_http_status") == 429 or (
            isinstance(row.get("last_reason"), str) and "429" in row["last_reason"]
        ):
            if cooling or not (row.get("last_ok")):
                lamp = "red" if configured else lamp
        providers_out.append(
            {
                **probe,
                "lamp": lamp,
                "ready": pid in ready_ids,
                "cooldown_active": cooling,
                "cooldown_until": row.get("cooldown_until"),
                "last_ok": row.get("last_ok"),
                "last_at": row.get("last_at"),
                "last_reason": row.get("last_reason"),
                "last_http_status": row.get("last_http_status"),
                "last_detail": row.get("last_detail"),
            }
        )

    quota_today: dict[str, Any] = {
        "resend": None,
        "gmail": None,
        "mailbox": None,
        "ses": None,
        "smtp": None,
        "mailgun": None,
    }
    if isinstance(domain_quota, dict):
        domains = domain_quota.get("domains") or []
        if isinstance(domains, list) and domains:
            d0 = domains[0] if isinstance(domains[0], dict) else {}
            used = d0.get("used_today")
            rem = d0.get("remaining")
            quota_today["resend"] = {
                "used": used,
                "remaining": rem,
                "at_cap": bool(d0.get("at_cap")),
                "label": f"{used} / {int(used or 0) + int(rem or 0)}"
                if used is not None and rem is not None
                else None,
                "domain": d0.get("domain"),
            }
    # Annotate Gmail last 429 into quota board
    for p in providers_out:
        if p["id"] == "gmail" and p.get("last_http_status") == 429:
            quota_today["gmail"] = {
                "status": "429",
                "detail": p.get("last_detail"),
                "until": p.get("cooldown_until"),
                "retry_hint": p.get("last_detail"),
            }
        if p["id"] in ("mailbox", "ses", "smtp", "mailgun"):
            if p["lamp"] == "green":
                quota_today[p["id"]] = {"status": "OK"}
            elif p["lamp"] == "gray":
                quota_today[p["id"]] = {"status": "not_configured"}
            else:
                quota_today[p["id"]] = {
                    "status": p.get("last_reason") or p["lamp"],
                    "detail": p.get("last_detail"),
                }

    next_action = ""
    if not ready_ids:
        next_action = (
            "Нет доступных провайдеров. Добавьте MAILBOX_SMTP_* в .env.local "
            "или дождитесь снятия 429 у Gmail/Resend."
        )
    elif ready_ids[0] != "resend":
        next_action = (
            f"Основной сейчас: {ready_ids[0]} "
            "(Resend недоступен или на паузе — после восстановления снова станет первым)."
        )

    journal = recent_send_journal(memory_dir, limit=15)

    return {
        "ok": True,
        "version": "email_provider_pool_v2",
        "title_ru": "Email Providers",
        "order": provider_order(),
        "ready_providers": ready_ids,
        "any_ready": bool(ready_ids),
        "providers": providers_out,
        "quota_today": quota_today,
        "send_journal": journal,
        "next_action_ru": next_action,
        "note_ru": (
            "Цепочка: Resend → Gmail → Mailbox.org. "
            "При ошибке одного письмо уходит через следующий. "
            "После восстановления Resend снова основной. Лимиты не обходятся."
        ),
        "env_help_ru": {
            "resend": "RESEND_API_KEY, GENESIS_EMAIL_FROM",
            "gmail": "GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, GMAIL_SENDER",
            "mailbox": (
                "MAILBOX_SMTP_HOST, MAILBOX_SMTP_PORT, MAILBOX_SMTP_USER, "
                "MAILBOX_SMTP_PASSWORD, MAILBOX_SMTP_SECURE"
            ),
            "order": "EMAIL_PROVIDER_ORDER=resend,gmail,mailbox",
        },
    }
