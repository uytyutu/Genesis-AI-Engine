"""Store Admin Commerce settings stubs — ready for R3.3 activation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_commerce_settings() -> dict[str, Any]:
    return {
        "version": 1,
        "payments": {
            "stripe": {
                "id": "stripe",
                "label": "Stripe Connect",
                "status": "not_connected",
            },
            "paypal": {
                "id": "paypal",
                "label": "PayPal",
                "status": "not_connected",
            },
            "klarna": {
                "id": "klarna",
                "label": "Klarna",
                "status": "not_connected",
            },
            "sepa": {
                "id": "sepa",
                "label": "SEPA",
                "status": "not_connected",
            },
        },
        "shipping": {
            "dhl": {"id": "dhl", "label": "DHL", "status": "not_connected"},
            "hermes": {
                "id": "hermes",
                "label": "Hermes",
                "status": "not_connected",
            },
            "dpd": {"id": "dpd", "label": "DPD", "status": "not_connected"},
            "ups": {"id": "ups", "label": "UPS", "status": "not_connected"},
        },
        "taxes": {
            "status": "not_connected",
            "label": "VAT / MwSt.",
            "note": "Tax rules activate in Commerce R3.3.4",
        },
        "currencies": {
            "status": "not_connected",
            "primary": "EUR",
            "label": "Currencies",
            "note": "Multi-currency arrives with Commerce",
        },
        "email": {
            "status": "not_connected",
            "label": "Transactional email",
            "note": "Order and account emails — R3.3",
        },
        "invoices": {
            "status": "not_connected",
            "label": "Invoices",
            "note": "Invoice PDF and numbering — R3.3.4",
        },
        "updated_at": None,
    }


class StoreCommerceSettingsService:
    """Owner commerce config under store_admin — User Data Protection."""

    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "store_admin"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, order_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        d = self._root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d / "commerce_settings.json"

    def get(self, order_id: str) -> dict[str, Any]:
        path = self._path(order_id)
        base = default_commerce_settings()
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    for key in (
                        "payments",
                        "shipping",
                        "taxes",
                        "currencies",
                        "email",
                        "invoices",
                    ):
                        if isinstance(raw.get(key), dict):
                            if key in ("payments", "shipping"):
                                base[key] = {**base[key], **raw[key]}
                            else:
                                base[key] = {**base[key], **raw[key]}
                    base["updated_at"] = raw.get("updated_at")
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "ok": True,
            "order_id": order_id,
            "settings": base,
            "commerce_ready": False,
            "note": "Stubs only — payment providers connect in R3.3.1",
        }

    def ensure_saved(self, order_id: str) -> dict[str, Any]:
        """Persist defaults once so regenerate never invents a blank slate."""
        path = self._path(order_id)
        if not path.is_file():
            data = default_commerce_settings()
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return self.get(order_id)
