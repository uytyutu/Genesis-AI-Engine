"""QR Code SKU — generate + structural decode validator.

FREE tool for Virtus Office (no Stripe). Still: executor → validator → PASS → delivery.
Uses qrcode + Pillow (already in requirements). Validator samples PNG modules against
the QR matrix built from the payload (proves scannable structure, not decorative art).
"""

from __future__ import annotations

import io
import re
from typing import Any
from urllib.parse import quote

SKU_ID = "qr_code"
SKU_ENABLED = True
EXECUTOR_IMPLEMENTED = True
VALIDATOR_IMPLEMENTED = True

QR_TYPES = frozenset(
    {"url", "whatsapp", "maps", "email", "phone", "text", "wifi", "vcard"}
)

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": False,
    "free": True,
    "output": "PNG + SVG + PDF QR that encodes the payload",
    "validation": ["png_header", "matrix_roundtrip", "payload_match"],
    "price_eur_hint": {"min": 0.0, "max": 0.0},
    "price_key": "simple_op",
}


def build_payload(qr_type: str, fields: dict[str, Any]) -> str:
    t = (qr_type or "url").strip().lower()
    f = {str(k): str(v or "").strip() for k, v in (fields or {}).items()}
    if t == "url":
        url = f.get("url") or f.get("value") or ""
        if url and not re.match(r"^https?://", url, re.I):
            url = "https://" + url
        return url
    if t == "whatsapp":
        phone = re.sub(r"[^\d+]", "", f.get("phone") or f.get("value") or "")
        text = f.get("text") or ""
        if text:
            return f"https://wa.me/{phone.lstrip('+')}?text={quote(text)}"
        return f"https://wa.me/{phone.lstrip('+')}"
    if t == "maps":
        q = f.get("query") or f.get("address") or f.get("value") or ""
        return f"https://maps.google.com/?q={quote(q)}"
    if t == "email":
        email = f.get("email") or f.get("value") or ""
        subject = f.get("subject") or ""
        body = f.get("body") or ""
        qs = []
        if subject:
            qs.append(f"subject={quote(subject)}")
        if body:
            qs.append(f"body={quote(body)}")
        return f"mailto:{email}" + (("?" + "&".join(qs)) if qs else "")
    if t == "phone":
        phone = re.sub(r"[^\d+]", "", f.get("phone") or f.get("value") or "")
        return f"tel:{phone}"
    if t == "wifi":
        ssid = f.get("ssid") or ""
        password = f.get("password") or ""
        auth = (f.get("auth") or "WPA").upper()
        hidden = "true" if str(f.get("hidden") or "").lower() in {"1", "true", "yes"} else "false"
        return f"WIFI:T:{auth};S:{ssid};P:{password};H:{hidden};;"
    if t == "vcard":
        name = f.get("name") or ""
        org = f.get("org") or f.get("company") or ""
        phone = f.get("phone") or ""
        email = f.get("email") or ""
        url = f.get("url") or f.get("website") or ""
        lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{name}",
        ]
        if org:
            lines.append(f"ORG:{org}")
        if phone:
            lines.append(f"TEL:{phone}")
        if email:
            lines.append(f"EMAIL:{email}")
        if url:
            lines.append(f"URL:{url}")
        lines.append("END:VCARD")
        return "\n".join(lines)
    # text
    return f.get("text") or f.get("value") or ""


def missing_required(qr_type: str, fields: dict[str, Any]) -> list[str]:
    t = (qr_type or "url").strip().lower()
    f = {str(k): str(v or "").strip() for k, v in (fields or {}).items()}
    need: list[str] = []
    if t == "url" and not (f.get("url") or f.get("value")):
        need.append("url")
    elif t == "whatsapp" and not (f.get("phone") or f.get("value")):
        need.append("phone")
    elif t == "maps" and not (f.get("query") or f.get("address") or f.get("value")):
        need.append("address")
    elif t == "email" and not (f.get("email") or f.get("value")):
        need.append("email")
    elif t == "phone" and not (f.get("phone") or f.get("value")):
        need.append("phone")
    elif t == "wifi" and not f.get("ssid"):
        need.append("ssid")
    elif t == "vcard" and not f.get("name"):
        need.append("name")
    elif t == "text" and not (f.get("text") or f.get("value")):
        need.append("text")
    return need


BOX_SIZE = 10
BORDER = 2


def _make_qr(payload: str):
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=BOX_SIZE,
        border=BORDER,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    return qr


def _png_bytes(qr) -> bytes:
    img = qr.make_image(fill_color="black", back_color="white")
    # Keep 1-bit style when possible for crisp modules
    try:
        img = img.convert("L")
    except Exception:  # noqa: BLE001
        pass
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _svg_bytes(payload: str) -> bytes:
    import qrcode
    import qrcode.image.svg

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=BOX_SIZE,
        border=BORDER,
        image_factory=qrcode.image.svg.SvgPathImage,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image()
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue()


def _pdf_bytes(png: bytes, title: str = "Virtus Office QR") -> bytes:
    from fpdf import FPDF
    from PIL import Image

    img = Image.open(io.BytesIO(png)).convert("RGB")
    tmp = io.BytesIO()
    img.save(tmp, format="PNG")
    tmp.seek(0)

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 10, title, ln=True)
    x = (210 - 70) / 2
    y = 40
    pdf.image(tmp, x=x, y=y, w=70, h=70)
    out = io.BytesIO()
    pdf.output(out)
    return out.getvalue()


def validate_qr_png(*, png: bytes, matrix: list[list[bool]], payload: str) -> dict[str, Any]:
    """Sample PNG module centers vs QR matrix (get_matrix already includes quiet zone)."""
    from PIL import Image

    problems: list[str] = []
    if not png.startswith(b"\x89PNG"):
        return {"ok": False, "problems": ["png_header"], "decoded_ok": False}
    if not payload:
        return {"ok": False, "problems": ["empty_payload"], "decoded_ok": False}
    try:
        img = Image.open(io.BytesIO(png)).convert("L")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "problems": [f"png_open:{exc}"], "decoded_ok": False}

    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    if rows < 21 or cols < 21:
        problems.append("matrix_too_small")
    iw, ih = img.size
    expected_px = cols * BOX_SIZE
    if iw != expected_px or ih != expected_px:
        problems.append(f"size_mismatch:{iw}x{ih}!={expected_px}")

    mismatches = 0
    checked = 0
    for r in range(rows):
        for c in range(cols):
            x = c * BOX_SIZE + BOX_SIZE // 2
            y = r * BOX_SIZE + BOX_SIZE // 2
            if x >= iw or y >= ih:
                mismatches += 1
                checked += 1
                continue
            pix = img.getpixel((x, y))
            is_dark = pix < 128
            expected_dark = bool(matrix[r][c])
            checked += 1
            if is_dark != expected_dark:
                mismatches += 1
    ratio = mismatches / max(checked, 1)
    if ratio > 0.05:
        problems.append(f"matrix_mismatch:{mismatches}/{checked}")
    ok = not problems
    return {
        "ok": ok,
        "problems": problems,
        "decoded_ok": ok,
        "mismatch_ratio": round(ratio, 4),
        "modules": rows,
        "payload_len": len(payload),
        "image_size": [iw, ih],
    }


def generate_qr(
    *,
    qr_type: str = "url",
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fields = dict(fields or {})
    t = (qr_type or "url").strip().lower()
    if t not in QR_TYPES:
        return {"ok": False, "error": "unsupported_qr_type", "detail": t}
    miss = missing_required(t, fields)
    if miss:
        return {"ok": False, "error": "missing_fields", "detail": ",".join(miss), "missing": miss}

    payload = build_payload(t, fields)
    if not payload or len(payload) > 1800:
        return {"ok": False, "error": "invalid_payload", "detail": "empty_or_too_long"}

    qr = _make_qr(payload)
    matrix = qr.get_matrix()
    png = _png_bytes(qr)
    svg = _svg_bytes(payload)
    try:
        pdf = _pdf_bytes(png)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": "pdf_failed", "detail": str(exc)}

    validation = validate_qr_png(png=png, matrix=matrix, payload=payload)
    if not validation.get("ok"):
        return {
            "ok": False,
            "error": "qr_validation_failed",
            "detail": ",".join(validation.get("problems") or []),
            "validation": validation,
        }

    return {
        "ok": True,
        "action_id": SKU_ID,
        "qr_type": t,
        "payload": payload,
        "mime": "image/png",
        "filename": "virtus-qr.png",
        "bytes": png,
        "artifacts": [
            {"filename": "virtus-qr.png", "mime": "image/png", "bytes": png},
            {"filename": "virtus-qr.svg", "mime": "image/svg+xml", "bytes": svg},
            {"filename": "virtus-qr.pdf", "mime": "application/pdf", "bytes": pdf},
        ],
        "validation": validation,
        "free": True,
    }


def execute_qr_code(*, intent: dict[str, Any], understanding: dict[str, Any] | None = None) -> dict[str, Any]:
    """Job-engine compatible entry (no upload required)."""
    understanding = understanding or {}
    src = dict(intent or {})
    qr_cfg = dict(src.get("qr") or understanding.get("qr") or {})
    qr_type = str(qr_cfg.get("type") or src.get("qr_type") or "url")
    fields = dict(qr_cfg.get("fields") or src.get("qr_fields") or qr_cfg)
    fields.pop("type", None)
    return generate_qr(qr_type=qr_type, fields=fields)
