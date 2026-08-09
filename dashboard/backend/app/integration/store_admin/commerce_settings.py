"""Store Admin Integrations + Commerce configs (R3.3.1–R3.3.6).

Virtus Core never charges shop buyers. Merchants connect their own accounts.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONNECTION_STATUSES = frozenset(
    {"connected", "not_connected", "error", "coming", "pending"}
)

SHIPPING_CARRIERS = [
    ("dhl", "DHL", "DE"),
    ("dpd", "DPD", "DE"),
    ("gls", "GLS", "DE"),
    ("hermes", "Hermes", "DE"),
    ("ups", "UPS", "EU"),
    ("fedex", "FedEx", "EU"),
    ("pickup", "Самовывоз / Click & Collect", "local"),
    ("local_delivery", "Local delivery", "local"),
]

RATE_MODES = frozenset(
    {"fixed", "weight", "order_value", "item_count", "free"}
)

EMAIL_PROVIDERS = [
    ("gmail", "Gmail"),
    ("outlook", "Outlook"),
    ("microsoft365", "Microsoft 365"),
    ("smtp", "SMTP"),
]

NOTIFICATION_CHANNELS = [
    ("email", "Email"),
    ("telegram", "Telegram"),
    ("push", "Push"),
]

NO_ACCOUNT_CONNECT = frozenset(
    {
        "invoice",
        "cash_on_delivery",
        "pickup",
        "local_delivery",
        "taxes",
        "invoices",
        "notif_email",
        "push",
    }
)

ACCOUNT_REQUIRED = frozenset(
    {
        # stripe → OAuth; email → SMTP form; carriers → shipping API form
        "paypal",
        "klarna",
        "sepa",
        "telegram",
    }
)

# Manual account string is rejected — merchant must complete Stripe Connect OAuth.
OAUTH_ONLY = frozenset({"stripe"})

# Email providers use SMTP credential form (presets for Gmail / Outlook / M365).
SMTP_FORM_PROVIDERS = frozenset({"gmail", "outlook", "microsoft365", "smtp"})

# Carrier APIs — credentials + test connection (not free-text account).
SHIPPING_API_CARRIERS = frozenset({"dhl", "dpd", "gls", "hermes", "ups", "fedex"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative_sync(iso: str | None) -> str | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        secs = int(delta.total_seconds())
        if secs < 60:
            return "just now"
        if secs < 3600:
            return f"{secs // 60} min ago"
        if secs < 86400:
            return f"{secs // 3600} h ago"
        return f"{secs // 86400} d ago"
    except Exception:
        return None


def connection_card(
    *,
    id: str,
    category: str,
    label: str,
    status: str = "not_connected",
    account: str | None = None,
    last_sync_at: str | None = None,
    phase: str,
    connectable: bool = True,
    coming: str | None = None,
    note: str | None = None,
    error: str | None = None,
    connect_mode: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    st = status if status in CONNECTION_STATUSES else "not_connected"
    if coming and st == "not_connected" and not connectable:
        st = "coming"
    card: dict[str, Any] = {
        "id": id,
        "category": category,
        "label": label,
        "status": st,
        "account": account,
        "last_sync_at": last_sync_at,
        "last_sync_label": _relative_sync(last_sync_at),
        "phase": phase,
        "connectable": bool(connectable) and st != "coming",
        "coming": coming,
        "note": note
        or "Owner account — Virtus Core never takes buyer funds.",
        "error": error,
        "actions": _actions_for(st, connectable=connectable and st != "coming"),
    }
    if connect_mode:
        card["connect_mode"] = connect_mode
    for key, val in extra.items():
        if val is not None:
            card[key] = val
    return card


def _actions_for(status: str, *, connectable: bool) -> list[str]:
    if not connectable or status == "coming":
        return []
    if status == "connected":
        return ["reconnect", "disconnect", "sync"]
    if status == "error":
        return ["reconnect", "disconnect"]
    return ["connect"]


def default_payment_providers() -> dict[str, dict[str, Any]]:
    base_note = "Merchant's own account. Virtus Core does not receive buyer payments."
    return {
        "stripe": connection_card(
            id="stripe",
            category="payments",
            label="Stripe",
            phase="Gen1 · Stripe OAuth",
            note=(
                f"{base_note} Connect with Stripe (OAuth) — no API keys to paste."
            ),
            connect_mode="oauth",
        ),
        "paypal": connection_card(
            id="paypal",
            category="payments",
            label="PayPal",
            phase="R3.3.1",
            note=base_note,
        ),
        "klarna": connection_card(
            id="klarna",
            category="payments",
            label="Klarna",
            phase="R3.3.1",
            note=base_note,
        ),
        "sepa": connection_card(
            id="sepa",
            category="payments",
            label="SEPA",
            phase="R3.3.1",
            note=base_note,
        ),
        "invoice": connection_card(
            id="invoice",
            category="payments",
            label="Invoice",
            phase="R3.3.1",
            note="Pay by invoice — no external PSP required.",
        ),
        "cash_on_delivery": connection_card(
            id="cash_on_delivery",
            category="payments",
            label="Cash on Delivery",
            phase="R3.3.1",
            note="Cash on delivery — local fulfillment.",
        ),
    }


def default_shipping_methods() -> list[dict[str, Any]]:
    """Catalog of possible methods — enabled only after carrier Connect."""
    return [
        {
            "id": "dhl_standard",
            "carrier": "dhl",
            "label": "DHL Standard",
            "days_min": 3,
            "days_max": 5,
            "price_eur": 7.90,
            "enabled": False,
        },
        {
            "id": "dhl_express",
            "carrier": "dhl",
            "label": "DHL Express",
            "days_min": 1,
            "days_max": 2,
            "price_eur": 14.90,
            "enabled": False,
        },
        {
            "id": "dpd_classic",
            "carrier": "dpd",
            "label": "DPD Classic",
            "days_min": 2,
            "days_max": 4,
            "price_eur": 6.90,
            "enabled": False,
        },
        {
            "id": "gls_business",
            "carrier": "gls",
            "label": "GLS BusinessParcel",
            "days_min": 2,
            "days_max": 4,
            "price_eur": 7.40,
            "enabled": False,
        },
        {
            "id": "pickup_free",
            "carrier": "pickup",
            "label": "Самовывоз",
            "days_min": 0,
            "days_max": 0,
            "price_eur": 0.0,
            "enabled": False,
        },
        {
            "id": "local_standard",
            "carrier": "local_delivery",
            "label": "Локальная доставка",
            "days_min": 0,
            "days_max": 1,
            "price_eur": 4.90,
            "enabled": False,
        },
    ]


def default_shipping_config() -> dict[str, Any]:
    return {
        "country": "DE",
        "regions": ["DE", "AT", "CH"],
        "postal_zones": [],
        "free_shipping_from_eur": None,
        "min_order_eur": None,
        "processing_days": 1,
        "rate_mode": "fixed",
        "methods": default_shipping_methods(),
        "updated_at": None,
    }


def default_shipping_providers() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for cid, label, region in SHIPPING_CARRIERS:
        local = cid in {"pickup", "local_delivery"}
        out[cid] = connection_card(
            id=cid,
            category="shipping",
            label=label,
            phase="Gen1 · Shipping API",
            connectable=True,
            connect_mode="offline" if local else "shipping_api",
            note=(
                "No external carrier — enable for checkout."
                if local
                else (
                    f"Merchant carrier API ({region}). Connect → test → rates → "
                    "create shipment → tracking."
                )
            ),
        )
    return out


def default_tax_config() -> dict[str, Any]:
    return {
        "profile": "de_standard",  # de_standard | de_reduced | vat_exempt | eu_sales | export
        "standard_rate_pct": 19.0,
        "reduced_rate_pct": 7.0,
        "vat_exempt": False,
        "eu_sales_enabled": True,
        "export_outside_eu_zero": True,
        "company_vat_id": None,
        "updated_at": None,
    }


def default_email_providers() -> dict[str, dict[str, Any]]:
    note = (
        "Transactional mail — order confirmations, invoices, buyer notices. "
        "Connect SMTP (App Password for Gmail) + Send Test Email."
    )
    return {
        pid: connection_card(
            id=pid,
            category="email",
            label=label,
            phase="Gen1 · SMTP",
            note=note,
            connect_mode="smtp_form",
        )
        for pid, label in EMAIL_PROVIDERS
    }


def default_email_transport() -> dict[str, Any]:
    return {
        "provider_id": None,
        "host": None,
        "port": 587,
        "username": None,
        "password": None,
        "encryption": "tls",
        "from_email": None,
        "from_name": None,
        "reply_to": None,
        "support_email": None,
        "sales_email": None,
        "last_test": None,
        "updated_at": None,
    }


def default_invoice_config() -> dict[str, Any]:
    return {
        "prefix": "INV",
        "next_number": 1001,
        "credit_note_prefix": "CN",
        "next_credit_number": 1,
        "include_order_number": True,
        "auto_pdf": True,
        "company_name": None,  # prefer Business Profile company_name
        "language": "de",
        "currency": "EUR",
        "date_format": "DD.MM.YYYY",
        "signature_text": None,
        "stamp_enabled": False,
        "show_payment_qr": True,
        "updated_at": None,
    }


def default_notification_channels() -> dict[str, dict[str, Any]]:
    return {
        "email": connection_card(
            id="notif_email",
            category="notifications",
            label="Email",
            phase="R3.3.6",
            note="Uses connected transactional email provider.",
        ),
        "telegram": connection_card(
            id="telegram",
            category="notifications",
            label="Telegram",
            phase="R3.3.6",
            note="Owner Telegram bot / chat for order alerts.",
        ),
        "push": connection_card(
            id="push",
            category="notifications",
            label="Push",
            phase="R3.3.6",
            note="Browser / app push for Store Admin.",
        ),
    }


def default_commerce_settings() -> dict[str, Any]:
    return {
        "version": 3,
        "phase": "R3.3.6",
        "payments": default_payment_providers(),
        "shipping": default_shipping_providers(),
        "shipping_config": default_shipping_config(),
        "taxes": connection_card(
            id="taxes",
            category="taxes",
            label="VAT / MwSt.",
            phase="R3.3.3",
            note="MwSt 19% / 7% · VAT exempt · EU sales · export outside EU.",
        ),
        "tax_config": default_tax_config(),
        "email": default_email_providers(),
        "email_transport": default_email_transport(),
        "invoices": connection_card(
            id="invoices",
            category="invoices",
            label="Invoices",
            phase="R3.3.5",
            note="PDF Invoice · Credit Note · order & invoice numbering.",
        ),
        "invoice_config": default_invoice_config(),
        "notifications": default_notification_channels(),
        "domains": connection_card(
            id="domains",
            category="domains",
            label="Domains",
            phase="Integrations",
            connectable=False,
            coming="R3.4",
            note="Custom domain mapping — later.",
        ),
        "analytics": connection_card(
            id="analytics",
            category="analytics",
            label="Analytics",
            phase="Post R3.3",
            connectable=False,
            coming="R3.4",
            note="Store analytics after Commerce.",
        ),
        "pixels": connection_card(
            id="pixels",
            category="pixels",
            label="Pixels",
            phase="Post R3.3",
            connectable=False,
            coming="R3.4",
            note="Meta / Google pixels — Marketing phase.",
        ),
        "crm": connection_card(
            id="crm",
            category="crm",
            label="CRM",
            phase="Post R3.3",
            connectable=False,
            coming="R4",
            note="CRM integrations after Commerce.",
        ),
        "marketplace": connection_card(
            id="marketplace",
            category="marketplace",
            label="Marketplace",
            phase="Post R3.3",
            connectable=False,
            coming="R4",
            note="Marketplace channels later.",
        ),
        "api_keys": connection_card(
            id="api_keys",
            category="api_keys",
            label="API Keys",
            phase="Integrations",
            connectable=False,
            coming="R3.4",
            note="Merchant API keys for storefront automation.",
        ),
        "currencies": {
            "status": "connected",
            "label": "Currencies",
            "primary": "EUR",
            "note": "EUR primary for DE/EU MVP",
        },
        "updated_at": None,
    }


def _merge_provider(base: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in raw.items():
        if k in {"id", "category", "label", "phase"} and out.get(k):
            continue
        out[k] = v
    out["last_sync_label"] = _relative_sync(out.get("last_sync_at"))
    out["actions"] = _actions_for(
        str(out.get("status") or "not_connected"),
        connectable=bool(out.get("connectable", True))
        and str(out.get("status")) != "coming",
    )
    return out


def _merge_dict_bucket(
    base: dict[str, Any], raw: dict[str, Any] | None
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return base
    merged = dict(base)
    for pid, prow in raw.items():
        if pid in merged and isinstance(prow, dict):
            merged[pid] = _merge_provider(merged[pid], prow)
        elif isinstance(prow, dict):
            merged[pid] = prow
    return merged


def _connected_any(bucket: dict[str, Any] | None) -> bool:
    if not isinstance(bucket, dict):
        return False
    return any(
        isinstance(p, dict) and p.get("status") == "connected" for p in bucket.values()
    )


def shipping_guidance(settings: dict[str, Any]) -> list[dict[str, Any]]:
    """Vector tips for shipping setup."""
    tips: list[dict[str, Any]] = []
    shipping = settings.get("shipping") if isinstance(settings.get("shipping"), dict) else {}
    cfg = (
        settings.get("shipping_config")
        if isinstance(settings.get("shipping_config"), dict)
        else {}
    )
    connected = [
        p.get("label") or pid
        for pid, p in shipping.items()
        if isinstance(p, dict) and p.get("status") == "connected"
    ]
    if connected:
        tips.append(
            {
                "id": "ship_connected",
                "priority": 10,
                "message": f"✅ {connected[0]} подключён."
                if len(connected) == 1
                else f"✅ Подключено: {', '.join(str(x) for x in connected[:4])}.",
                "section": "shipping",
                "cta_label": "Открыть Shipping",
            }
        )
    else:
        tips.append(
            {
                "id": "ship_none",
                "priority": 5,
                "message": "Магазин пока не может отправлять товары.",
                "section": "shipping",
                "cta_label": "Открыть Shipping",
            }
        )
    free_from = cfg.get("free_shipping_from_eur")
    if free_from is None and connected:
        tips.append(
            {
                "id": "ship_free",
                "priority": 20,
                "message": "У вас не настроена бесплатная доставка. Хотите добавить её от 100 €?",
                "section": "shipping",
                "cta_label": "Настроить",
            }
        )
    return tips


def enable_shipping_methods_for_carrier(
    settings: dict[str, Any], carrier: str, *, enabled: bool = True
) -> None:
    """Toggle checkout methods that belong to a carrier."""
    cfg = dict(settings.get("shipping_config") or default_shipping_config())
    methods = list(cfg.get("methods") or [])
    cid = (carrier or "").strip().lower()
    touched = False
    for m in methods:
        if isinstance(m, dict) and str(m.get("carrier") or "") == cid:
            m["enabled"] = bool(enabled)
            touched = True
    if enabled and not touched and cid in {"pickup", "local_delivery"}:
        label = "Самовывоз" if cid == "pickup" else "Локальная доставка"
        methods.append(
            {
                "id": f"{cid}_free" if cid == "pickup" else f"{cid}_standard",
                "carrier": cid,
                "label": label,
                "days_min": 0,
                "days_max": 0 if cid == "pickup" else 1,
                "price_eur": 0.0 if cid == "pickup" else 9.9,
                "enabled": True,
            }
        )
    cfg["methods"] = methods
    cfg["updated_at"] = _now()
    settings["shipping_config"] = cfg


class StoreCommerceSettingsService:
    """Owner commerce + integrations under store_admin — User Data Protection."""

    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "store_admin"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, order_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        d = self._root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d / "commerce_settings.json"

    def _load_raw(self, order_id: str) -> dict[str, Any]:
        path = self._path(order_id)
        base = default_commerce_settings()
        if not path.is_file():
            return base
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return base
        except (OSError, json.JSONDecodeError):
            return base

        # Migrate legacy single email card → provider map
        if isinstance(raw.get("email"), dict) and "gmail" not in raw["email"]:
            if raw["email"].get("id") == "email":
                raw = {**raw, "email": {}}

        for key in ("payments", "shipping", "email", "notifications"):
            if key in base:
                base[key] = _merge_dict_bucket(base[key], raw.get(key))

        for key in (
            "taxes",
            "invoices",
            "domains",
            "analytics",
            "pixels",
            "crm",
            "marketplace",
            "api_keys",
            "currencies",
        ):
            if isinstance(raw.get(key), dict) and isinstance(base.get(key), dict):
                base[key] = _merge_provider(base[key], raw[key])

        for key in ("shipping_config", "tax_config", "invoice_config", "email_transport"):
            if isinstance(raw.get(key), dict):
                merged = dict(base.get(key) or {})
                merged.update(raw[key])
                if key == "shipping_config" and isinstance(raw[key].get("methods"), list):
                    merged["methods"] = raw[key]["methods"]
                base[key] = merged

        base["updated_at"] = raw.get("updated_at")
        base["version"] = max(3, int(raw.get("version") or 3))
        return base

    def _save(self, order_id: str, data: dict[str, Any]) -> None:
        data = dict(data)
        data["updated_at"] = _now()
        data["version"] = 3
        data["phase"] = "R3.3.6"
        self._path(order_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get(self, order_id: str) -> dict[str, Any]:
        settings = self._load_raw(order_id)
        any_pay = _connected_any(settings.get("payments"))
        any_ship = _connected_any(settings.get("shipping"))
        taxes_ok = (
            isinstance(settings.get("taxes"), dict)
            and settings["taxes"].get("status") == "connected"
        )
        any_email = _connected_any(settings.get("email"))
        return {
            "ok": True,
            "order_id": order_id,
            "settings": settings,
            "commerce_ready": any_pay,
            "shipping_ready": any_ship,
            "taxes_ready": taxes_ok,
            "email_ready": any_email,
            "phase": "R3.3.6",
            "note": "R3.3 Commerce — merchant-owned Payments · Shipping · Taxes · Email · Invoices · Notifications.",
            "shipping_tips": shipping_guidance(settings),
        }

    def ensure_saved(self, order_id: str) -> dict[str, Any]:
        path = self._path(order_id)
        if not path.is_file():
            self._save(order_id, default_commerce_settings())
        return self.get(order_id)

    def integrations_hub(self, order_id: str) -> dict[str, Any]:
        self.ensure_saved(order_id)
        settings = self._load_raw(order_id)
        from app.integration import stripe_connect_oauth as stripe_oauth

        payment_items: list[dict[str, Any]] = []
        for row in (settings.get("payments") or {}).values():
            if not isinstance(row, dict):
                continue
            item = dict(row)
            if item.get("id") == "stripe":
                item["connect_mode"] = "oauth"
                item["oauth_ready"] = stripe_oauth.oauth_client_ready()
                item["oauth_mock"] = stripe_oauth.mock_enabled()
                if not item.get("oauth_ready") and item.get("status") != "connected":
                    item["note"] = (
                        "Stripe Connect OAuth requires STRIPE_CONNECT_CLIENT_ID (ca_…) "
                        "on the platform, or GENESIS_STRIPE_CONNECT_MOCK=1 for QA."
                    )
            payment_items.append(item)
        transport = settings.get("email_transport") or default_email_transport()
        last_test = transport.get("last_test") if isinstance(transport.get("last_test"), dict) else None
        email_items: list[dict[str, Any]] = []
        for row in (settings.get("email") or {}).values():
            if not isinstance(row, dict):
                continue
            item = dict(row)
            item["connect_mode"] = "smtp_form"
            if item.get("status") == "connected" and last_test:
                item["last_test"] = {
                    "ok": last_test.get("ok"),
                    "to": last_test.get("to"),
                    "sent_at": last_test.get("sent_at"),
                    "status": last_test.get("status"),
                    "title": last_test.get("title"),
                    "reason": last_test.get("reason"),
                }
                item["last_test_label"] = (
                    "Success"
                    if last_test.get("ok")
                    else (last_test.get("title") or "Failed")
                )
            email_items.append(item)
        notif_items = list((settings.get("notifications") or {}).values())
        sections = [
            {
                "id": "payments",
                "label": "Payments",
                "phase": "R3.3.1",
                "items": payment_items,
            },
            {
                "id": "shipping",
                "label": "Shipping",
                "phase": "R3.3.2",
                "items": list((settings.get("shipping") or {}).values()),
                "config": settings.get("shipping_config"),
            },
            {
                "id": "taxes",
                "label": "Taxes",
                "phase": "R3.3.3",
                "items": [settings["taxes"]],
                "config": settings.get("tax_config"),
            },
            {
                "id": "email",
                "label": "Email",
                "phase": "Gen1 · SMTP",
                "items": email_items,
                "config": self.public_email_transport(order_id),
            },
            {
                "id": "invoices",
                "label": "Invoices",
                "phase": "R3.3.5",
                "items": [settings["invoices"]],
                "config": settings.get("invoice_config"),
            },
            {
                "id": "notifications",
                "label": "Notifications",
                "phase": "R3.3.6",
                "items": notif_items,
            },
            {
                "id": "domains",
                "label": "Domains",
                "phase": "Integrations",
                "items": [settings["domains"]],
            },
            {
                "id": "analytics",
                "label": "Analytics",
                "phase": "Post R3.3",
                "items": [settings["analytics"]],
            },
            {
                "id": "pixels",
                "label": "Pixels",
                "phase": "Post R3.3",
                "items": [settings["pixels"]],
            },
            {
                "id": "crm",
                "label": "CRM",
                "phase": "Post R3.3",
                "items": [settings["crm"]],
            },
            {
                "id": "marketplace",
                "label": "Marketplace",
                "phase": "Post R3.3",
                "items": [settings["marketplace"]],
            },
            {
                "id": "api_keys",
                "label": "API Keys",
                "phase": "Integrations",
                "items": [settings["api_keys"]],
            },
        ]
        return {
            "ok": True,
            "order_id": order_id,
            "title": "Integrations",
            "sections": sections,
            "stripe_oauth": stripe_oauth.status(),
            "note": "One connection UX for every provider. Owner accounts only.",
        }

    def _find_provider(
        self, settings: dict[str, Any], provider_id: str
    ) -> tuple[str, dict[str, Any]] | None:
        pid = (provider_id or "").strip()
        # alias notif_email
        if pid == "email" and isinstance(settings.get("notifications"), dict):
            if "email" in settings["notifications"]:
                return "notifications", settings["notifications"]["email"]
        for bucket in ("payments", "shipping", "email", "notifications"):
            block = settings.get(bucket)
            if isinstance(block, dict) and pid in block:
                return bucket, block[pid]
            # notification channels keyed by short id but card id may differ
            if isinstance(block, dict):
                for key, row in block.items():
                    if isinstance(row, dict) and row.get("id") == pid:
                        return bucket, row
        for key in (
            "taxes",
            "invoices",
            "domains",
            "analytics",
            "pixels",
            "crm",
            "marketplace",
            "api_keys",
        ):
            row = settings.get(key)
            if isinstance(row, dict) and row.get("id") == pid:
                return key, row
        return None

    def _set_provider(
        self, settings: dict[str, Any], bucket: str, provider_id: str, updated: dict
    ) -> None:
        if bucket in ("payments", "shipping", "email", "notifications"):
            block = settings.get(bucket)
            if not isinstance(block, dict):
                settings[bucket] = {}
                block = settings[bucket]
            # find real key
            if provider_id in block:
                block[provider_id] = updated
                return
            for key, row in list(block.items()):
                if isinstance(row, dict) and row.get("id") == provider_id:
                    block[key] = updated
                    return
            block[provider_id] = updated
        else:
            settings[bucket] = updated

    def connect(
        self,
        order_id: str,
        provider_id: str,
        *,
        account: str | None = None,
    ) -> dict[str, Any]:
        settings = self._load_raw(order_id)
        found = self._find_provider(settings, provider_id)
        if not found:
            raise ValueError("provider_not_found")
        bucket, row = found
        if not row.get("connectable") or row.get("coming"):
            raise ValueError("provider_not_connectable")
        account_label = (account or "").strip() or None
        pid = str(row.get("id") or provider_id)
        if pid in OAUTH_ONLY:
            raise ValueError("oauth_required")
        if pid in SMTP_FORM_PROVIDERS:
            raise ValueError("smtp_form_required")
        if pid in SHIPPING_API_CARRIERS:
            raise ValueError("shipping_api_required")
        if pid in ACCOUNT_REQUIRED and not account_label:
            raise ValueError("account_required")
        now = _now()
        default_account = None
        if pid in NO_ACCOUNT_CONNECT:
            default_account = "Enabled"
        if pid == "taxes":
            default_account = f"MwSt {settings.get('tax_config', {}).get('standard_rate_pct', 19)}%"
        if pid == "invoices":
            cfg = settings.get("invoice_config") or {}
            default_account = f"{cfg.get('prefix', 'INV')}-{cfg.get('next_number', 1001)}"
        updated = {
            **row,
            "status": "connected",
            "account": account_label or row.get("account") or default_account,
            "last_sync_at": now,
            "error": None,
        }
        updated["last_sync_label"] = _relative_sync(now)
        updated["actions"] = _actions_for("connected", connectable=True)
        self._set_provider(settings, bucket, pid, updated)
        if pid in {"pickup", "local_delivery"}:
            enable_shipping_methods_for_carrier(settings, pid, enabled=True)
        self._save(order_id, settings)
        return {"ok": True, "provider": updated, "order_id": order_id}

    def apply_stripe_oauth(
        self,
        order_id: str,
        *,
        stripe_user_id: str,
        account_label: str | None = None,
        livemode: bool = False,
        scope: str | None = None,
        stripe_publishable_key: str | None = None,
        mock: bool = False,
    ) -> dict[str, Any]:
        """Persist Stripe Connect OAuth result — merchant Connected."""
        acct = (stripe_user_id or "").strip()
        if not acct.startswith("acct_"):
            raise ValueError("invalid_stripe_user_id")
        settings = self._load_raw(order_id)
        found = self._find_provider(settings, "stripe")
        if not found:
            raise ValueError("provider_not_found")
        bucket, row = found
        now = _now()
        updated = {
            **row,
            "status": "connected",
            "account": (account_label or "").strip() or acct,
            "stripe_user_id": acct,
            "livemode": bool(livemode),
            "scope": (scope or "read_write").strip(),
            "stripe_publishable_key": (stripe_publishable_key or "").strip() or None,
            "connect_mode": "oauth",
            "oauth_mock": bool(mock),
            "last_sync_at": now,
            "error": None,
            "note": (
                "Stripe Connect linked. Buyer payments go to this merchant account — "
                "Virtus Core never receives shop funds."
            ),
        }
        updated["last_sync_label"] = _relative_sync(now)
        updated["actions"] = _actions_for("connected", connectable=True)
        self._set_provider(settings, bucket, "stripe", updated)
        self._save(order_id, settings)
        return {"ok": True, "provider": updated, "order_id": order_id}

    def public_email_transport(self, order_id: str) -> dict[str, Any]:
        """Email transport without password — for Store Admin UI."""
        settings = self._load_raw(order_id)
        raw = dict(settings.get("email_transport") or default_email_transport())
        password = str(raw.pop("password", None) or "")
        raw["password_set"] = bool(password)
        return raw

    def connect_email_smtp(
        self,
        order_id: str,
        provider_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Connect Gmail / Outlook / M365 / SMTP with credentials + identity fields."""
        from app.integration.store_admin.merchant_smtp import (
            PROVIDER_PRESETS,
            normalize_transport,
            validate_transport,
        )

        pid = (provider_id or "").strip().lower()
        if pid not in SMTP_FORM_PROVIDERS:
            raise ValueError("provider_not_found")
        settings = self._load_raw(order_id)
        found = self._find_provider(settings, pid)
        if not found:
            raise ValueError("provider_not_found")
        transport = normalize_transport(pid, payload or {})
        # Keep existing password if UI sent blank and already stored
        existing = settings.get("email_transport") or {}
        if not transport.get("password") and existing.get("password"):
            transport["password"] = existing["password"]
        err = validate_transport(transport)
        if err:
            raise ValueError(err)
        now = _now()
        transport["updated_at"] = now
        # Preserve last_test until a new test runs
        if isinstance(existing.get("last_test"), dict) and not payload.get("clear_test"):
            transport["last_test"] = existing["last_test"]
        else:
            transport["last_test"] = None
        settings["email_transport"] = transport

        # Only one email provider connected at a time
        email_block = settings.get("email") if isinstance(settings.get("email"), dict) else {}
        active: dict[str, Any] | None = None
        for key, row in list(email_block.items()):
            if not isinstance(row, dict):
                continue
            rid = str(row.get("id") or key)
            if rid == pid:
                updated = {
                    **row,
                    "status": "connected",
                    "account": transport["from_email"],
                    "connect_mode": "smtp_form",
                    "last_sync_at": now,
                    "error": None,
                    "note": (
                        f"SMTP Connected ({PROVIDER_PRESETS.get(pid, {}).get('host') or transport['host']}). "
                        "Send Test Email to verify delivery."
                    ),
                }
                updated["last_sync_label"] = _relative_sync(now)
                updated["actions"] = ["reconnect", "disconnect", "sync", "test"]
                email_block[key] = updated
                active = updated
            else:
                email_block[key] = {
                    **row,
                    "status": "not_connected",
                    "account": None,
                    "last_sync_at": None,
                    "last_sync_label": None,
                    "error": None,
                    "connect_mode": "smtp_form",
                    "actions": _actions_for("not_connected", connectable=True),
                }
        settings["email"] = email_block
        self._save(order_id, settings)
        if not active:
            raise ValueError("provider_not_found")
        return {
            "ok": True,
            "order_id": order_id,
            "provider": active,
            "transport": self.public_email_transport(order_id),
            "vector_hint": {
                "message": "✅ Email успешно подключён.",
                "suggest_test": True,
                "cta": "Send Test Email",
            },
        }

    def send_test_email(
        self,
        order_id: str,
        *,
        to: str | None = None,
    ) -> dict[str, Any]:
        from app.integration.store_admin.business_profile import BusinessProfileService
        from app.integration.store_admin.merchant_smtp import (
            build_test_email,
            send_merchant_smtp,
        )

        settings = self._load_raw(order_id)
        transport = settings.get("email_transport") or {}
        if not transport.get("host") or not transport.get("password"):
            raise ValueError("smtp_not_connected")
        profile = BusinessProfileService(self._root.parent).get(order_id)["profile"]
        company = (
            transport.get("from_name")
            or profile.get("company_name")
            or "Virtus Core Store"
        )
        dest = (
            (to or "").strip()
            or str(transport.get("support_email") or "").strip()
            or str(transport.get("from_email") or "").strip()
            or str(profile.get("email_support") or "").strip()
        )
        subject, text, html = build_test_email(company_name=str(company))
        result = send_merchant_smtp(
            transport=transport,
            to=dest,
            subject=subject,
            text=text,
            html=html,
        )
        last_test = {
            "ok": bool(result.get("ok")),
            "to": dest,
            "sent_at": result.get("sent_at") or _now(),
            "status": result.get("status") or ("Delivered" if result.get("ok") else "Failed"),
            "title": result.get("title"),
            "reason": result.get("reason"),
            "detail": result.get("detail"),
            "mock": bool(result.get("mock")),
        }
        transport = dict(transport)
        transport["last_test"] = last_test
        transport["updated_at"] = _now()
        settings["email_transport"] = transport

        # Mirror last test onto active provider card
        pid = str(transport.get("provider_id") or "")
        email_block = settings.get("email") if isinstance(settings.get("email"), dict) else {}
        for key, row in list(email_block.items()):
            if isinstance(row, dict) and str(row.get("id") or key) == pid:
                row = dict(row)
                row["last_sync_at"] = last_test["sent_at"]
                row["last_sync_label"] = _relative_sync(last_test["sent_at"])
                if result.get("ok"):
                    row["error"] = None
                    row["status"] = "connected"
                else:
                    row["error"] = last_test.get("title") or "SMTP send failed"
                    row["status"] = "error"
                email_block[key] = row
        settings["email"] = email_block
        self._save(order_id, settings)

        # Append to store mail journal for analytics
        self._append_email_journal(order_id, {
            "type": "test_email",
            "ok": last_test["ok"],
            "to": dest,
            "at": last_test["sent_at"],
            "status": last_test["status"],
            "title": last_test.get("title"),
            "reason": last_test.get("reason"),
            "provider": pid,
        })

        return {
            "ok": bool(result.get("ok")),
            "order_id": order_id,
            "test": last_test,
            "transport": self.public_email_transport(order_id),
            "message": (
                "✓ Test Email sent"
                if result.get("ok")
                else (last_test.get("title") or "SMTP send failed")
            ),
        }

    def _append_email_journal(self, order_id: str, row: dict[str, Any]) -> None:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        path = self._root / safe / "email_send_journal.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def email_connected_with_test(self, order_id: str) -> bool:
        settings = self._load_raw(order_id)
        transport = settings.get("email_transport") or {}
        last = transport.get("last_test") if isinstance(transport.get("last_test"), dict) else {}
        any_email = _connected_any(settings.get("email"))
        return bool(any_email and last.get("ok"))

    def disconnect(self, order_id: str, provider_id: str) -> dict[str, Any]:
        pid = (provider_id or "").strip().lower()
        if pid in SHIPPING_API_CARRIERS:
            from app.integration.store_admin.shipping_api_service import (
                StoreShippingApiService,
            )

            return StoreShippingApiService(self._root.parent).disconnect_carrier(
                order_id, pid
            )
        settings = self._load_raw(order_id)
        found = self._find_provider(settings, provider_id)
        if not found:
            raise ValueError("provider_not_found")
        bucket, row = found
        if not row.get("connectable"):
            raise ValueError("provider_not_connectable")
        pid = str(row.get("id") or provider_id)
        deauth: dict[str, Any] | None = None
        if pid == "stripe":
            acct = str(row.get("stripe_user_id") or "").strip()
            if acct.startswith("acct_"):
                from app.integration import stripe_connect_oauth as stripe_oauth

                deauth = stripe_oauth.deauthorize(stripe_user_id=acct)
        updated = {
            **row,
            "status": "not_connected",
            "account": None,
            "last_sync_at": None,
            "last_sync_label": None,
            "error": None,
            "stripe_user_id": None,
            "livemode": None,
            "scope": None,
            "stripe_publishable_key": None,
            "oauth_mock": None,
        }
        if pid == "stripe":
            updated["connect_mode"] = "oauth"
            updated["note"] = (
                "Merchant's own account. Virtus Core does not receive buyer payments. "
                "Connect with Stripe (OAuth) — no API keys to paste."
            )
        if pid in SMTP_FORM_PROVIDERS:
            updated["connect_mode"] = "smtp_form"
            settings["email_transport"] = default_email_transport()
        if pid in {"pickup", "local_delivery"}:
            enable_shipping_methods_for_carrier(settings, pid, enabled=False)
        updated["actions"] = _actions_for("not_connected", connectable=True)
        self._set_provider(settings, bucket, pid, updated)
        self._save(order_id, settings)
        out: dict[str, Any] = {"ok": True, "provider": updated, "order_id": order_id}
        if deauth is not None:
            out["deauthorize"] = deauth
        return out

    def reconnect(
        self, order_id: str, provider_id: str, *, account: str | None = None
    ) -> dict[str, Any]:
        pid = (provider_id or "").strip()
        if pid in OAUTH_ONLY:
            return self.disconnect(order_id, provider_id)
        if pid in SMTP_FORM_PROVIDERS:
            raise ValueError("smtp_form_required")
        if pid in SHIPPING_API_CARRIERS:
            raise ValueError("shipping_api_required")
        self.disconnect(order_id, provider_id)
        return self.connect(order_id, provider_id, account=account)

    def sync(self, order_id: str, provider_id: str) -> dict[str, Any]:
        pid = (provider_id or "").strip().lower()
        if pid in SHIPPING_API_CARRIERS:
            from app.integration.store_admin.shipping_api_service import (
                StoreShippingApiService,
            )

            return StoreShippingApiService(self._root.parent).sync_carrier(
                order_id, pid
            )
        settings = self._load_raw(order_id)
        found = self._find_provider(settings, provider_id)
        if not found:
            raise ValueError("provider_not_found")
        bucket, row = found
        if row.get("status") != "connected":
            raise ValueError("provider_not_connected")
        pid = str(row.get("id") or provider_id)
        now = _now()
        updated = {**row, "last_sync_at": now, "last_sync_label": _relative_sync(now)}
        if pid == "stripe":
            from app.integration import stripe_connect_oauth as stripe_oauth

            acct = str(row.get("stripe_user_id") or "").strip()
            if not acct.startswith("acct_"):
                updated["status"] = "error"
                updated["error"] = "Missing stripe_user_id — reconnect via Stripe OAuth."
                updated["actions"] = _actions_for("error", connectable=True)
            else:
                info = stripe_oauth.retrieve_account(acct)
                if not info.get("ok"):
                    updated["status"] = "error"
                    updated["error"] = str(info.get("reason") or "sync_failed")
                    updated["actions"] = _actions_for("error", connectable=True)
                else:
                    email = str(info.get("email") or "").strip()
                    if email:
                        updated["account"] = email
                    updated["charges_enabled"] = info.get("charges_enabled")
                    updated["payouts_enabled"] = info.get("payouts_enabled")
                    updated["error"] = None
                    if info.get("charges_enabled") is False:
                        updated["error"] = "Stripe account cannot accept charges yet."
        self._set_provider(settings, bucket, pid, updated)
        self._save(order_id, settings)
        return {"ok": True, "provider": updated, "order_id": order_id}

    def update_shipping_config(
        self, order_id: str, patch: dict[str, Any]
    ) -> dict[str, Any]:
        settings = self._load_raw(order_id)
        cfg = dict(settings.get("shipping_config") or default_shipping_config())
        if "country" in patch and patch["country"]:
            cfg["country"] = str(patch["country"]).upper()[:2]
        if "regions" in patch and isinstance(patch["regions"], list):
            cfg["regions"] = [str(r).upper()[:8] for r in patch["regions"][:40]]
        if "postal_zones" in patch and isinstance(patch["postal_zones"], list):
            cfg["postal_zones"] = [str(z)[:16] for z in patch["postal_zones"][:200]]
        for key in ("free_shipping_from_eur", "min_order_eur"):
            if key in patch:
                val = patch[key]
                cfg[key] = None if val in (None, "", False) else float(val)
        if "processing_days" in patch:
            cfg["processing_days"] = max(0, int(patch["processing_days"] or 0))
        if "rate_mode" in patch:
            mode = str(patch["rate_mode"] or "fixed")
            if mode not in RATE_MODES:
                raise ValueError("invalid_rate_mode")
            cfg["rate_mode"] = mode
        if "methods" in patch and isinstance(patch["methods"], list):
            methods = []
            for m in patch["methods"][:40]:
                if not isinstance(m, dict):
                    continue
                methods.append(
                    {
                        "id": str(m.get("id") or uuid.uuid4().hex[:10]),
                        "carrier": str(m.get("carrier") or "dhl"),
                        "label": str(m.get("label") or "Shipping")[:80],
                        "days_min": int(m.get("days_min") or 0),
                        "days_max": int(m.get("days_max") or 0),
                        "price_eur": float(m.get("price_eur") or 0),
                        "enabled": bool(m.get("enabled", True)),
                    }
                )
            cfg["methods"] = methods
        cfg["updated_at"] = _now()
        settings["shipping_config"] = cfg
        self._save(order_id, settings)
        return {"ok": True, "order_id": order_id, "shipping_config": cfg}

    def update_tax_config(self, order_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        settings = self._load_raw(order_id)
        cfg = dict(settings.get("tax_config") or default_tax_config())
        allowed = {
            "de_standard",
            "de_reduced",
            "vat_exempt",
            "eu_sales",
            "export",
        }
        if "profile" in patch:
            profile = str(patch["profile"] or "de_standard")
            if profile not in allowed:
                raise ValueError("invalid_tax_profile")
            cfg["profile"] = profile
            cfg["vat_exempt"] = profile == "vat_exempt"
            if profile == "de_reduced":
                cfg["standard_rate_pct"] = 7.0
            elif profile == "vat_exempt":
                cfg["standard_rate_pct"] = 0.0
            elif profile == "de_standard":
                cfg["standard_rate_pct"] = 19.0
        for key in ("standard_rate_pct", "reduced_rate_pct"):
            if key in patch:
                cfg[key] = float(patch[key])
        for key in ("eu_sales_enabled", "export_outside_eu_zero", "vat_exempt"):
            if key in patch:
                cfg[key] = bool(patch[key])
        if "company_vat_id" in patch:
            cfg["company_vat_id"] = (
                str(patch["company_vat_id"]).strip()[:32] or None
            )
        cfg["updated_at"] = _now()
        settings["tax_config"] = cfg
        # Mark taxes connected when configured
        taxes = dict(settings.get("taxes") or {})
        taxes.update(
            {
                "status": "connected",
                "account": (
                    "VAT exempt"
                    if cfg.get("vat_exempt")
                    else f"MwSt {cfg.get('standard_rate_pct')}%"
                ),
                "last_sync_at": cfg["updated_at"],
                "last_sync_label": _relative_sync(cfg["updated_at"]),
                "connectable": True,
                "coming": None,
            }
        )
        taxes["actions"] = _actions_for("connected", connectable=True)
        settings["taxes"] = taxes
        self._save(order_id, settings)
        return {"ok": True, "order_id": order_id, "tax_config": cfg, "taxes": taxes}

    def update_invoice_config(
        self, order_id: str, patch: dict[str, Any]
    ) -> dict[str, Any]:
        settings = self._load_raw(order_id)
        cfg = dict(settings.get("invoice_config") or default_invoice_config())
        if "prefix" in patch:
            cfg["prefix"] = str(patch["prefix"] or "INV")[:24]
        if "credit_note_prefix" in patch:
            cfg["credit_note_prefix"] = str(patch["credit_note_prefix"] or "CN")[:12]
        if "next_number" in patch:
            cfg["next_number"] = max(1, int(patch["next_number"] or 1))
        if "next_credit_number" in patch:
            cfg["next_credit_number"] = max(1, int(patch["next_credit_number"] or 1))
        for key in ("include_order_number", "auto_pdf", "stamp_enabled", "show_payment_qr"):
            if key in patch:
                cfg[key] = bool(patch[key])
        if "company_name" in patch:
            cfg["company_name"] = str(patch["company_name"] or "").strip()[:120] or None
        if "signature_text" in patch:
            cfg["signature_text"] = str(patch["signature_text"] or "").strip()[:200] or None
        if "language" in patch:
            lang = str(patch["language"] or "de").lower()[:2]
            cfg["language"] = lang if lang in {"de", "en", "ru", "uk"} else "de"
        if "currency" in patch:
            cfg["currency"] = str(patch["currency"] or "EUR").upper()[:8]
        if "date_format" in patch:
            fmt = str(patch["date_format"] or "DD.MM.YYYY")
            cfg["date_format"] = (
                fmt if fmt in {"DD.MM.YYYY", "YYYY-MM-DD", "MM/DD/YYYY"} else "DD.MM.YYYY"
            )
        cfg["updated_at"] = _now()
        settings["invoice_config"] = cfg
        inv = dict(settings.get("invoices") or {})
        inv.update(
            {
                "status": "connected",
                "account": f"{cfg['prefix']}-{cfg['next_number']}",
                "last_sync_at": cfg["updated_at"],
                "last_sync_label": _relative_sync(cfg["updated_at"]),
                "connectable": True,
                "coming": None,
            }
        )
        inv["actions"] = _actions_for("connected", connectable=True)
        settings["invoices"] = inv
        self._save(order_id, settings)
        return {
            "ok": True,
            "order_id": order_id,
            "invoice_config": cfg,
            "invoices": inv,
        }

    def allocate_invoice_number(self, order_id: str) -> dict[str, Any]:
        """Reserve next invoice number (PDF generation hooks later)."""
        settings = self._load_raw(order_id)
        cfg = dict(settings.get("invoice_config") or default_invoice_config())
        number = int(cfg.get("next_number") or 1001)
        prefix = str(cfg.get("prefix") or "INV")
        full = f"{prefix}-{number}"
        cfg["next_number"] = number + 1
        cfg["updated_at"] = _now()
        settings["invoice_config"] = cfg
        self._save(order_id, settings)
        return {
            "ok": True,
            "invoice_number": full,
            "order_id": order_id,
            "type": "invoice",
            "auto_pdf": bool(cfg.get("auto_pdf", True)),
        }

    def allocate_credit_note(self, order_id: str) -> dict[str, Any]:
        settings = self._load_raw(order_id)
        cfg = dict(settings.get("invoice_config") or default_invoice_config())
        number = int(cfg.get("next_credit_number") or 1)
        prefix = str(cfg.get("credit_note_prefix") or "CN")
        full = f"{prefix}-{number}"
        cfg["next_credit_number"] = number + 1
        cfg["updated_at"] = _now()
        settings["invoice_config"] = cfg
        self._save(order_id, settings)
        return {
            "ok": True,
            "credit_note_number": full,
            "order_id": order_id,
            "type": "credit_note",
        }
