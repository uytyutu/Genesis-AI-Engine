"""Email OTP for client self-registration (anti-abuse)."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException

OTP_TTL_SEC = 15 * 60
OTP_LENGTH = 6
MAX_ATTEMPTS = 5


@dataclass
class PendingRegistration:
    email: str
    name: str
    password_hash: str
    locale: str
    country: str
    code_hash: str
    created_at: float
    attempts: int = 0
    visitor_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PendingRegistration:
        return cls(
            email=str(raw.get("email") or ""),
            name=str(raw.get("name") or ""),
            password_hash=str(raw.get("password_hash") or ""),
            locale=str(raw.get("locale") or "en"),
            country=str(raw.get("country") or ""),
            code_hash=str(raw.get("code_hash") or ""),
            created_at=float(raw.get("created_at") or 0),
            attempts=int(raw.get("attempts") or 0),
            visitor_id=(str(raw["visitor_id"]) if raw.get("visitor_id") else None),
        )


def _pending_dir(memory_dir: Path) -> Path:
    path = memory_dir / "client_registration_pending"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _email_key(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:40]


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def generate_otp_code() -> str:
    # 6 digits, no leading-zero loss as string
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def save_pending(memory_dir: Path, pending: PendingRegistration) -> None:
    path = _pending_dir(memory_dir) / f"{_email_key(pending.email)}.json"
    path.write_text(
        json.dumps(pending.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_pending(memory_dir: Path, email: str) -> PendingRegistration | None:
    path = _pending_dir(memory_dir) / f"{_email_key(email)}.json"
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    return PendingRegistration.from_dict(raw)


def delete_pending(memory_dir: Path, email: str) -> None:
    path = _pending_dir(memory_dir) / f"{_email_key(email)}.json"
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def verify_pending_code(
    memory_dir: Path, *, email: str, code: str
) -> PendingRegistration:
    pending = load_pending(memory_dir, email)
    if pending is None:
        raise HTTPException(status_code=400, detail="registration_not_started")
    if time.time() - pending.created_at > OTP_TTL_SEC:
        delete_pending(memory_dir, email)
        raise HTTPException(status_code=400, detail="code_expired")
    if pending.attempts >= MAX_ATTEMPTS:
        delete_pending(memory_dir, email)
        raise HTTPException(status_code=400, detail="too_many_attempts")
    pending.attempts += 1
    save_pending(memory_dir, pending)
    presented = _code_hash(code)
    if len(presented) != len(pending.code_hash) or not secrets.compare_digest(
        pending.code_hash, presented
    ):
        raise HTTPException(status_code=400, detail="invalid_code")
    return pending


def send_registration_code(*, to: str, code: str, name: str, locale: str) -> dict[str, Any]:
    """Send OTP via Resend/Gmail. Falls back to dev exposure when mail is offline."""
    from app.integration.genesis_brain.public_brand import BRAND_NAME

    lang = (locale or "en")[:2].lower()
    subjects = {
        "de": f"Ihr Bestätigungscode — {BRAND_NAME}",
        "ru": f"Код подтверждения — {BRAND_NAME}",
        "en": f"Your verification code — {BRAND_NAME}",
    }
    bodies = {
        "de": (
            f"Hallo {name},\n\n"
            f"Ihr Bestätigungscode für {BRAND_NAME}: {code}\n\n"
            f"Gültig {OTP_TTL_SEC // 60} Minuten. "
            "Wenn Sie das nicht waren, ignorieren Sie diese E-Mail.\n"
        ),
        "ru": (
            f"Здравствуйте, {name}!\n\n"
            f"Код подтверждения для {BRAND_NAME}: {code}\n\n"
            f"Действует {OTP_TTL_SEC // 60} минут. "
            "Если это не вы — просто проигнорируйте письмо.\n"
        ),
        "en": (
            f"Hello {name},\n\n"
            f"Your {BRAND_NAME} verification code: {code}\n\n"
            f"Valid for {OTP_TTL_SEC // 60} minutes. "
            "If you did not request this, ignore this email.\n"
        ),
    }
    subject = subjects.get(lang) or subjects["en"]
    text = bodies.get(lang) or bodies["en"]

    expose_dev = os.getenv("GENESIS_CLIENT_OTP_DEV", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    mail_configured = bool(
        os.getenv("RESEND_API_KEY", "").strip()
        or os.getenv("GMAIL_REFRESH_TOKEN", "").strip()
        or os.getenv("GMAIL_CREDENTIALS_JSON", "").strip()
    )

    send_result: dict[str, Any] = {"ok": False}
    try:
        from app.integration.receipt_email_service import ReceiptEmailService

        svc = ReceiptEmailService()
        send_result = svc._send(  # noqa: SLF001 — shared transactional transport
            to=to,
            subject=subject,
            text=text,
            html=f"<p>{text.replace(chr(10), '<br/>')}</p>",
        )
    except Exception as exc:
        send_result = {"ok": False, "error": str(exc)[:200]}

    delivered = bool(send_result.get("ok")) and not send_result.get("skipped")
    out: dict[str, Any] = {
        "delivery": "email" if delivered else "dev",
        "mail": send_result,
    }
    # Local / CEO path: no mail provider → show code so registration is possible.
    if (not delivered and not mail_configured) or expose_dev:
        out["code"] = code
        out["delivery"] = "dev"
    elif not delivered:
        raise HTTPException(
            status_code=503,
            detail="email_delivery_unavailable",
        )
    return out
