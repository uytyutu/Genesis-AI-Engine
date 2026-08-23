"""Merchant SMTP send + Test Email (store-owned credentials).

Virtus never uses platform Resend/Gmail for shop transactional mail once the
merchant connects their own SMTP / Gmail App Password / Outlook / M365.
"""

from __future__ import annotations

import os
import re
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any

PROVIDER_PRESETS: dict[str, dict[str, Any]] = {
    "gmail": {
        "host": "smtp.gmail.com",
        "port": 587,
        "encryption": "tls",
        "hint": "Use a Google App Password (not your normal Gmail password).",
    },
    "outlook": {
        "host": "smtp-mail.outlook.com",
        "port": 587,
        "encryption": "tls",
        "hint": "Outlook.com personal account — enable SMTP if required.",
    },
    "microsoft365": {
        "host": "smtp.office365.com",
        "port": 587,
        "encryption": "tls",
        "hint": "Microsoft 365 business mailbox.",
    },
    "smtp": {
        "host": "",
        "port": 587,
        "encryption": "tls",
        "hint": "Any SMTP host (Mailbox.org, IONOS, Strato, …).",
    },
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def mock_enabled() -> bool:
    return os.getenv("GENESIS_SMTP_MOCK", "").strip() == "1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_smtp_error(exc: BaseException) -> dict[str, str]:
    """Human-readable SMTP failure — not just 'Error'."""
    text = str(exc) or type(exc).__name__
    low = text.lower()
    if isinstance(exc, smtplib.SMTPAuthenticationError) or "auth" in low or "535" in low:
        return {
            "title": "SMTP Authentication failed",
            "reason": "Invalid username or App Password. For Gmail, create an App Password.",
            "detail": text[:240],
        }
    if isinstance(exc, smtplib.SMTPConnectError) or "connection refused" in low or "timed out" in low:
        return {
            "title": "SMTP Connection failed",
            "reason": "Cannot reach host/port. Check SMTP Host, Port, and Encryption.",
            "detail": text[:240],
        }
    if isinstance(exc, smtplib.SMTPRecipientsRefused) or "recipient" in low:
        return {
            "title": "Recipient rejected",
            "reason": "The destination address was refused by the mail server.",
            "detail": text[:240],
        }
    if "ssl" in low or "tls" in low or "certificate" in low:
        return {
            "title": "TLS/SSL error",
            "reason": "Encryption mismatch — try TLS (587) or SSL (465).",
            "detail": text[:240],
        }
    return {
        "title": "SMTP send failed",
        "reason": text[:160] or type(exc).__name__,
        "detail": text[:240],
    }


def validate_transport(cfg: dict[str, Any]) -> str | None:
    host = str(cfg.get("host") or "").strip()
    port = cfg.get("port")
    username = str(cfg.get("username") or "").strip()
    password = str(cfg.get("password") or "").strip()
    from_email = str(cfg.get("from_email") or username or "").strip()
    encryption = str(cfg.get("encryption") or "tls").strip().lower()
    if not host:
        return "smtp_host_required"
    try:
        p = int(port)
    except (TypeError, ValueError):
        return "smtp_port_invalid"
    if p < 1 or p > 65535:
        return "smtp_port_invalid"
    if not username:
        return "smtp_username_required"
    if not password:
        return "smtp_password_required"
    if not from_email or not EMAIL_RE.match(from_email):
        return "smtp_from_invalid"
    if encryption not in {"tls", "ssl", "none"}:
        return "smtp_encryption_invalid"
    return None


def normalize_transport(
    provider_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    pid = (provider_id or "smtp").strip().lower()
    preset = PROVIDER_PRESETS.get(pid, PROVIDER_PRESETS["smtp"])
    encryption = str(payload.get("encryption") or preset["encryption"]).strip().lower()
    if encryption not in {"tls", "ssl", "none"}:
        encryption = "tls"
    try:
        port = int(payload.get("port") if payload.get("port") not in (None, "") else preset["port"])
    except (TypeError, ValueError):
        port = int(preset["port"])
    username = str(payload.get("username") or "").strip()
    from_email = str(payload.get("from_email") or username).strip()
    return {
        "provider_id": pid if pid in PROVIDER_PRESETS else "smtp",
        "host": str(payload.get("host") or preset["host"] or "").strip(),
        "port": port,
        "username": username,
        "password": str(payload.get("password") or ""),
        "encryption": encryption,
        "from_email": from_email,
        "from_name": str(payload.get("from_name") or "").strip() or None,
        "reply_to": str(payload.get("reply_to") or "").strip() or None,
        "support_email": str(payload.get("support_email") or "").strip() or None,
        "sales_email": str(payload.get("sales_email") or "").strip() or None,
    }


def send_merchant_smtp(
    *,
    transport: dict[str, Any],
    to: str,
    subject: str,
    text: str,
    html: str = "",
) -> dict[str, Any]:
    """Send one message with merchant SMTP credentials."""
    err = validate_transport(transport)
    if err:
        return {"ok": False, "reason": err, "title": "SMTP not configured", "detail": err}
    to_addr = (to or "").strip()
    if not to_addr or not EMAIL_RE.match(to_addr):
        return {
            "ok": False,
            "title": "Invalid recipient",
            "reason": "Provide a valid To address for the test email.",
            "detail": to_addr,
        }

    if mock_enabled():
        return {
            "ok": True,
            "provider": transport.get("provider_id") or "smtp",
            "to": to_addr,
            "status": "Delivered",
            "mock": True,
            "sent_at": _now(),
            "message_id": f"mock-{_now()}",
        }

    host = str(transport["host"])
    port = int(transport["port"])
    user = str(transport["username"])
    password = str(transport["password"])
    encryption = str(transport.get("encryption") or "tls")
    from_email = str(transport["from_email"])
    from_name = str(transport.get("from_name") or "").strip()
    reply_to = str(transport.get("reply_to") or "").strip()
    frm = formataddr((from_name, from_email)) if from_name else from_email

    if html.strip():
        msg: MIMEMultipart | MIMEText = MIMEMultipart("alternative")
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = frm
    msg["To"] = to_addr
    if reply_to and EMAIL_RE.match(reply_to):
        msg["Reply-To"] = reply_to

    try:
        context = ssl.create_default_context()
        if encryption == "ssl":
            with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as server:
                server.login(user, password)
                server.sendmail(from_email, [to_addr], msg.as_string())
        elif encryption == "none":
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.login(user, password)
                server.sendmail(from_email, [to_addr], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(user, password)
                server.sendmail(from_email, [to_addr], msg.as_string())
    except Exception as exc:  # noqa: BLE001 — surface classified SMTP errors
        classified = classify_smtp_error(exc)
        return {
            "ok": False,
            "provider": transport.get("provider_id") or "smtp",
            "to": to_addr,
            "status": "Failed",
            "sent_at": _now(),
            **classified,
        }

    return {
        "ok": True,
        "provider": transport.get("provider_id") or "smtp",
        "to": to_addr,
        "status": "Delivered",
        "sent_at": _now(),
        "message_id": f"smtp-{_now()}",
    }


def build_test_email(*, company_name: str | None = None) -> tuple[str, str, str]:
    brand = (company_name or "Virtus Core Store").strip() or "Virtus Core Store"
    subject = f"[{brand}] Test Email — Virtus Core"
    text = (
        f"This is a test email from {brand}.\n\n"
        "If you received this message, your SMTP connection works.\n"
        "Virtus Core · Store Admin · Email\n"
    )
    html = (
        f"<p>This is a test email from <strong>{brand}</strong>.</p>"
        "<p>If you received this message, your SMTP connection works.</p>"
        "<p style='color:#666;font-size:12px'>Virtus Core · Store Admin · Email</p>"
    )
    return subject, text, html
