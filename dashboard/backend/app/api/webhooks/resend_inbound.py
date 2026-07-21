"""POST /api/webhooks/resend-inbound — Resend Inbound email.received."""

from __future__ import annotations

import base64
import hashlib
import html as html_lib
import hmac
import json
import os
import re
import time

from fastapi import APIRouter, HTTPException, Request

from app.integration.context import get_integration
from app.integration.support_inbox_service import SupportInboxService

router = APIRouter(tags=["webhooks"])


def _inbound_secret() -> str:
    return (
        os.getenv("RESEND_INBOUND_WEBHOOK_SECRET", "").strip()
        or os.getenv("RESEND_WEBHOOK_SECRET", "").strip()
    )


def _verify_svix(secret: str, body: bytes, headers: dict[str, str]) -> bool:
    """Verify Resend/Svix webhook signature (whsec_…)."""
    msg_id = headers.get("svix-id") or headers.get("webhook-id") or ""
    timestamp = headers.get("svix-timestamp") or headers.get("webhook-timestamp") or ""
    signature_header = headers.get("svix-signature") or headers.get("webhook-signature") or ""
    if not (msg_id and timestamp and signature_header):
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    # Reject stale/replayed timestamps (±5 min)
    if abs(int(time.time()) - ts) > 300:
        return False

    if secret.startswith("whsec_"):
        try:
            key = base64.b64decode(secret[len("whsec_") :])
        except Exception:
            return False
    else:
        key = secret.encode("utf-8")

    to_sign = f"{msg_id}.{timestamp}.".encode("utf-8") + body
    digest = base64.b64encode(hmac.new(key, to_sign, hashlib.sha256).digest()).decode("ascii")
    for part in signature_header.split(" "):
        part = part.strip()
        if not part.startswith("v1,"):
            continue
        candidate = part[3:]
        if candidate and hmac.compare_digest(candidate, digest):
            return True
    return False


def _verify_shared_secret(secret: str, request: Request) -> bool:
    """Local smoke / custom header path (Bearer or X-Webhook-Secret)."""
    auth = (request.headers.get("authorization") or "").strip()
    bearer = ""
    if auth.lower().startswith("bearer "):
        bearer = auth[7:].strip()
    header_secret = (
        request.headers.get("x-webhook-secret")
        or request.headers.get("x-resend-webhook-secret")
        or ""
    ).strip()
    if bearer and hmac.compare_digest(bearer, secret):
        return True
    if header_secret and hmac.compare_digest(header_secret, secret):
        return True
    return False


def _verify_inbound_secret(request: Request, body: bytes) -> None:
    secret = _inbound_secret()
    if not secret:
        if os.getenv("GENESIS_ENV", "").strip().lower() == "production":
            raise HTTPException(status_code=503, detail="inbound_webhook_secret_missing")
        return

    hdrs = {k.lower(): v for k, v in request.headers.items()}
    ok = _verify_svix(secret, body, hdrs) or _verify_shared_secret(secret, request)
    if not ok:
        raise HTTPException(status_code=401, detail="invalid_webhook_secret")


def _html_to_text(html_body: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html_body or "")
    text = re.sub(r"(?s)<br\s*/?>", "\n", text)
    text = re.sub(r"(?s)</p>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return " ".join(html_lib.unescape(text).split())


@router.post("/api/webhooks/resend-inbound")
@router.post("/webhooks/resend-inbound")
async def resend_inbound_webhook(request: Request) -> dict:
    body = await request.body()
    _verify_inbound_secret(request, body)
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid_json") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_payload")

    event_type = str(payload.get("type") or payload.get("event") or "").lower()
    if event_type.startswith("email.sent") or event_type.startswith("email.delivered"):
        return {"ok": True, "skipped": True, "reason": "ignored_event"}

    parsed = SupportInboxService.parse_resend_inbound_payload(payload)
    # Resend email.received metadata has no body — fetch via Receiving API.
    if parsed.get("external_id") and not (parsed.get("text") or parsed.get("html")):
        enriched = get_integration().support.fetch_received_email(parsed["external_id"])
        if enriched.get("ok"):
            data = enriched.get("email") or {}
            if not parsed.get("from_email") and data.get("from"):
                parsed = SupportInboxService.parse_resend_inbound_payload(
                    {"data": {**data, "email_id": parsed["external_id"]}}
                )
            else:
                parsed["text"] = str(data.get("text") or parsed.get("text") or "")
                parsed["html"] = str(data.get("html") or parsed.get("html") or "")
                if data.get("subject") and not parsed.get("subject"):
                    parsed["subject"] = str(data.get("subject") or "")
                if data.get("from") and not parsed.get("from_email"):
                    from_p = SupportInboxService.parse_resend_inbound_payload({"data": data})
                    parsed["from_email"] = from_p["from_email"]
                    parsed["to_email"] = parsed.get("to_email") or from_p["to_email"]

    if not parsed.get("text") and parsed.get("html"):
        parsed["text"] = _html_to_text(parsed["html"])

    if not parsed.get("from_email"):
        raise HTTPException(status_code=400, detail="missing_from")

    svc = get_integration().support
    try:
        result = svc.ingest_inbound(
            from_email=parsed["from_email"],
            subject=parsed["subject"],
            text=parsed["text"],
            html_body=parsed["html"],
            to_email=parsed["to_email"],
            external_id=parsed["external_id"],
            auto_reply=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "ok": True,
        "thread_id": (result.get("thread") or {}).get("id"),
        "status": (result.get("thread") or {}).get("status"),
        "auto_reply": result.get("auto_reply"),
    }
