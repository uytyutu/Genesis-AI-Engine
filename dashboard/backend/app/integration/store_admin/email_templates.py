"""Merchant transactional email templates (basic texts — Gen1)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEMPLATE_DEFS: list[dict[str, str]] = [
    {
        "id": "order_confirmation",
        "label": "Order Confirmation",
        "subject": "Bestellbestätigung {{order_id}} — {{company_name}}",
        "body": (
            "Guten Tag {{buyer_name}},\n\n"
            "vielen Dank für Ihre Bestellung {{order_id}}.\n"
            "Summe: {{total}} {{currency}}\n\n"
            "Mit freundlichen Grüßen\n{{company_name}}\n{{support_email}}"
        ),
    },
    {
        "id": "payment_received",
        "label": "Payment Received",
        "subject": "Zahlung erhalten — {{order_id}}",
        "body": (
            "Guten Tag {{buyer_name}},\n\n"
            "wir haben Ihre Zahlung für Bestellung {{order_id}} erhalten.\n\n"
            "{{company_name}}"
        ),
    },
    {
        "id": "invoice",
        "label": "Invoice",
        "subject": "Rechnung {{invoice_number}} — {{company_name}}",
        "body": (
            "Guten Tag {{buyer_name}},\n\n"
            "anbei Ihre Rechnung {{invoice_number}}.\n\n"
            "{{company_name}}\n{{support_email}}"
        ),
    },
    {
        "id": "shipping_update",
        "label": "Shipping Update",
        "subject": "Versandupdate {{order_id}}",
        "body": (
            "Guten Tag {{buyer_name}},\n\n"
            "Ihre Bestellung {{order_id}} ist unterwegs.\n"
            "Tracking: {{tracking_url}}\n\n"
            "{{company_name}}"
        ),
    },
    {
        "id": "password_reset",
        "label": "Password Reset",
        "subject": "Passwort zurücksetzen — {{company_name}}",
        "body": (
            "Guten Tag,\n\n"
            "Link zum Zurücksetzen: {{reset_url}}\n\n"
            "Wenn Sie das nicht waren, ignorieren Sie diese E-Mail.\n"
            "{{company_name}}"
        ),
    },
    {
        "id": "welcome",
        "label": "Welcome",
        "subject": "Willkommen bei {{company_name}}",
        "body": (
            "Guten Tag {{buyer_name}},\n\n"
            "willkommen! Wir freuen uns, Sie begrüßen zu dürfen.\n\n"
            "{{company_name}}\n{{support_email}}"
        ),
    },
    {
        "id": "contact_form",
        "label": "Contact Form",
        "subject": "Neue Kontaktanfrage — {{company_name}}",
        "body": (
            "Neue Nachricht über das Kontaktformular:\n\n"
            "Von: {{sender_name}} <{{sender_email}}>\n"
            "{{message}}\n"
        ),
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_templates() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": None,
        "templates": {
            t["id"]: {
                "id": t["id"],
                "label": t["label"],
                "subject": t["subject"],
                "body": t["body"],
                "enabled": True,
                "customized": False,
            }
            for t in TEMPLATE_DEFS
        },
    }


class EmailTemplatesService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)

    def _path(self, order_id: str) -> Path:
        return self._memory / "store_admin" / order_id / "email_templates.json"

    def get(self, order_id: str) -> dict[str, Any]:
        path = self._path(order_id)
        data = default_templates()
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and isinstance(raw.get("templates"), dict):
                    for tid, row in raw["templates"].items():
                        if tid in data["templates"] and isinstance(row, dict):
                            data["templates"][tid] = {**data["templates"][tid], **row}
                    data["updated_at"] = raw.get("updated_at")
            except (OSError, json.JSONDecodeError):
                pass
        items = list(data["templates"].values())
        return {
            "ok": True,
            "order_id": order_id,
            "templates": items,
            "count": len(items),
            "note": "Gen1 basic texts — customize later without breaking send.",
        }

    def render(
        self,
        order_id: str,
        template_id: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pack = self.get(order_id)
        row = next((t for t in pack["templates"] if t["id"] == template_id), None)
        if not row:
            raise ValueError("template_not_found")
        vars_map = {k: str(v) if v is not None else "" for k, v in (variables or {}).items()}

        def _sub(text: str) -> str:
            out = text
            for k, v in vars_map.items():
                out = out.replace("{{" + k + "}}", v)
            # strip leftover placeholders
            return re_sub_placeholders(out)

        return {
            "ok": True,
            "id": template_id,
            "subject": _sub(str(row.get("subject") or "")),
            "body": _sub(str(row.get("body") or "")),
        }


def re_sub_placeholders(text: str) -> str:
    import re

    return re.sub(r"\{\{[a-zA-Z0-9_]+\}\}", "", text)
