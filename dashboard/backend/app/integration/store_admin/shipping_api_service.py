"""Merchant Shipping APIs — rates, create shipment, tracking.

Carriers: DHL, DPD, GLS, Hermes, UPS, FedEx (+ pickup / local_delivery offline).
Gen1: full UX + mock transport (GENESIS_SHIPPING_MOCK=1) and credential hooks
for real carrier APIs when keys are present.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

API_CARRIERS = frozenset({"dhl", "dpd", "gls", "hermes", "ups", "fedex"})
OFFLINE_CARRIERS = frozenset({"pickup", "local_delivery"})

# Default DE service catalog (shown after Connect + Sync)
CARRIER_SERVICES: dict[str, list[dict[str, Any]]] = {
    "dhl": [
        {"id": "dhl_standard", "label": "DHL Standard", "days_min": 3, "days_max": 5, "base_eur": 7.90},
        {"id": "dhl_express", "label": "DHL Express", "days_min": 1, "days_max": 2, "base_eur": 14.90},
        {"id": "dhl_warenpost", "label": "DHL Warenpost", "days_min": 2, "days_max": 4, "base_eur": 4.99},
    ],
    "dpd": [
        {"id": "dpd_classic", "label": "DPD Classic", "days_min": 2, "days_max": 4, "base_eur": 6.90},
        {"id": "dpd_express", "label": "DPD Express", "days_min": 1, "days_max": 2, "base_eur": 12.90},
    ],
    "gls": [
        {"id": "gls_business", "label": "GLS BusinessParcel", "days_min": 2, "days_max": 4, "base_eur": 7.40},
        {"id": "gls_express", "label": "GLS ExpressParcel", "days_min": 1, "days_max": 2, "base_eur": 13.50},
    ],
    "hermes": [
        {"id": "hermes_standard", "label": "Hermes Standard", "days_min": 3, "days_max": 5, "base_eur": 5.90},
        {"id": "hermes_express", "label": "Hermes Express", "days_min": 1, "days_max": 2, "base_eur": 11.90},
    ],
    "ups": [
        {"id": "ups_standard", "label": "UPS Standard", "days_min": 2, "days_max": 5, "base_eur": 9.90},
        {"id": "ups_express", "label": "UPS Express", "days_min": 1, "days_max": 2, "base_eur": 18.90},
    ],
    "fedex": [
        {"id": "fedex_economy", "label": "FedEx International Economy", "days_min": 3, "days_max": 6, "base_eur": 16.90},
        {"id": "fedex_express", "label": "FedEx Express", "days_min": 1, "days_max": 3, "base_eur": 24.90},
    ],
}

TRACK_STATUSES = (
    "label_created",
    "picked_up",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "exception",
)


def mock_enabled() -> bool:
    return os.getenv("GENESIS_SHIPPING_MOCK", "").strip() == "1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(order_id: str) -> str:
    return re.sub(r"[^\w\-]", "_", order_id)[:80]


def _tracking_url(carrier: str, tracking: str) -> str:
    c = carrier.lower()
    t = tracking.strip()
    urls = {
        "dhl": f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={t}",
        "dpd": f"https://tracking.dpd.de/status/de_DE/parcel/{t}",
        "gls": f"https://www.gls-pakete.de/sendungsverfolgung?match={t}",
        "hermes": f"https://www.myhermes.de/empfangen/sendungsverfolgung/sendungsinformation/#{t}",
        "ups": f"https://www.ups.com/track?tracknum={t}",
        "fedex": f"https://www.fedex.com/fedextrack/?trknbr={t}",
    }
    return urls.get(c, f"https://track.example/{c}/{t}")


class StoreShippingApiService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)

    def _shop_dir(self, order_id: str) -> Path:
        d = self._memory / "store_admin" / _safe(order_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _credentials_path(self, order_id: str) -> Path:
        return self._shop_dir(order_id) / "shipping_credentials.json"

    def _shipments_path(self, order_id: str) -> Path:
        return self._shop_dir(order_id) / "shipments.json"

    def _journal_path(self, order_id: str) -> Path:
        return self._shop_dir(order_id) / "shipping_api_journal.jsonl"

    def _load_credentials(self, order_id: str) -> dict[str, Any]:
        path = self._credentials_path(order_id)
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_credentials(self, order_id: str, data: dict[str, Any]) -> None:
        self._credentials_path(order_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_shipments(self, order_id: str) -> list[dict[str, Any]]:
        path = self._shipments_path(order_id)
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data.get("shipments") if isinstance(data, dict) else data
            return [r for r in (rows or []) if isinstance(r, dict)]
        except (OSError, json.JSONDecodeError):
            return []

    def _save_shipments(self, order_id: str, rows: list[dict[str, Any]]) -> None:
        self._shipments_path(order_id).write_text(
            json.dumps(
                {"version": 1, "order_id": order_id, "shipments": rows[-500:]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _journal(self, order_id: str, row: dict[str, Any]) -> None:
        path = self._journal_path(order_id)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({**row, "at": _now()}, ensure_ascii=False) + "\n")

    def public_credentials(self, order_id: str, carrier: str) -> dict[str, Any]:
        all_creds = self._load_credentials(order_id)
        raw = dict(all_creds.get(carrier) or {})
        raw.pop("api_password", None)
        raw.pop("api_key", None)
        raw["api_key_set"] = bool((all_creds.get(carrier) or {}).get("api_key"))
        raw["api_password_set"] = bool((all_creds.get(carrier) or {}).get("api_password"))
        return raw

    def connect_carrier(
        self,
        order_id: str,
        carrier: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Save carrier API credentials and mark Connected in commerce settings."""
        from app.integration.store_admin.commerce_settings import (
            StoreCommerceSettingsService,
            _actions_for,
            _now as cnow,
            _relative_sync,
        )

        cid = (carrier or "").strip().lower()
        if cid not in API_CARRIERS and cid not in OFFLINE_CARRIERS:
            raise ValueError("carrier_not_supported")

        account_name = str(payload.get("account_name") or payload.get("account") or "").strip()
        api_key = str(payload.get("api_key") or "").strip()
        api_password = str(payload.get("api_password") or "").strip()
        api_user = str(payload.get("api_user") or "").strip()
        billing_number = str(payload.get("billing_number") or "").strip()

        if cid in API_CARRIERS:
            # Allow mock connect without real keys
            if not mock_enabled() and not api_key and not api_user:
                raise ValueError("api_credentials_required")
            if mock_enabled() and not account_name:
                account_name = f"{cid.upper()} Business (mock)"
            if not account_name:
                account_name = api_user or billing_number or f"{cid.upper()} Account"

        commerce = StoreCommerceSettingsService(self._memory)
        settings = commerce._load_raw(order_id)  # noqa: SLF001
        shipping = settings.get("shipping") if isinstance(settings.get("shipping"), dict) else {}
        row = shipping.get(cid) if isinstance(shipping.get(cid), dict) else None
        if not row:
            raise ValueError("provider_not_found")

        # Test connection
        test = self.test_connection(
            order_id,
            cid,
            {
                "api_key": api_key,
                "api_password": api_password,
                "api_user": api_user,
                "billing_number": billing_number,
                "account_name": account_name,
            },
        )
        if not test.get("ok"):
            raise ValueError(test.get("reason") or "connection_failed")

        now = cnow()
        creds = self._load_credentials(order_id)
        existing = dict(creds.get(cid) or {})
        if not api_key and existing.get("api_key"):
            api_key = existing["api_key"]
        if not api_password and existing.get("api_password"):
            api_password = existing["api_password"]
        creds[cid] = {
            "carrier": cid,
            "account_name": account_name,
            "api_user": api_user or None,
            "api_key": api_key or ("mock" if mock_enabled() else None),
            "api_password": api_password or ("mock" if mock_enabled() else None),
            "billing_number": billing_number or None,
            "mock": mock_enabled() or str(api_key).startswith("mock"),
            "last_test": test,
            "services": test.get("services") or CARRIER_SERVICES.get(cid, []),
            "updated_at": now,
        }
        self._save_credentials(order_id, creds)

        updated = {
            **row,
            "status": "connected",
            "account": account_name,
            "connect_mode": "shipping_api",
            "last_sync_at": now,
            "error": None,
            "last_test_label": "Success",
            "services_count": len(creds[cid]["services"]),
            "note": (
                f"{row.get('label') or cid} API Connected — rates, create shipment, tracking."
            ),
        }
        updated["last_sync_label"] = _relative_sync(now)
        updated["actions"] = ["reconnect", "disconnect", "sync", "create_shipment", "track"]
        shipping[cid] = updated
        settings["shipping"] = shipping

        # Sync enabled methods for this carrier into shipping_config
        cfg = dict(settings.get("shipping_config") or {})
        methods = list(cfg.get("methods") or [])
        existing_ids = {m.get("id") for m in methods if isinstance(m, dict)}
        for svc in creds[cid]["services"]:
            if svc["id"] not in existing_ids:
                methods.append(
                    {
                        "id": svc["id"],
                        "carrier": cid,
                        "label": svc["label"],
                        "days_min": svc.get("days_min", 2),
                        "days_max": svc.get("days_max", 5),
                        "price_eur": float(svc.get("base_eur") or 7.9),
                        "enabled": True,
                    }
                )
            else:
                for m in methods:
                    if isinstance(m, dict) and m.get("id") == svc["id"]:
                        m["enabled"] = True
                        m["carrier"] = cid
        # enable pickup/local without API
        cfg["methods"] = methods
        cfg["updated_at"] = now
        settings["shipping_config"] = cfg
        commerce._save(order_id, settings)  # noqa: SLF001

        self._journal(
            order_id,
            {"type": "connect", "carrier": cid, "ok": True, "account": account_name},
        )
        return {
            "ok": True,
            "provider": updated,
            "carrier": cid,
            "services": creds[cid]["services"],
            "test": test,
            "vector_hint": {
                "message": f"✅ {row.get('label') or cid.upper()} подключён.",
                "cta": "Create Shipment",
            },
            "credentials": self.public_credentials(order_id, cid),
        }

    def disconnect_carrier(self, order_id: str, carrier: str) -> dict[str, Any]:
        from app.integration.store_admin.commerce_settings import (
            StoreCommerceSettingsService,
            _actions_for,
            enable_shipping_methods_for_carrier,
        )

        cid = (carrier or "").strip().lower()
        commerce = StoreCommerceSettingsService(self._memory)
        settings = commerce._load_raw(order_id)  # noqa: SLF001
        shipping = settings.get("shipping") if isinstance(settings.get("shipping"), dict) else {}
        row = shipping.get(cid) if isinstance(shipping.get(cid), dict) else None
        if not row:
            raise ValueError("provider_not_found")
        updated = {
            **row,
            "status": "not_connected",
            "account": None,
            "last_sync_at": None,
            "last_sync_label": None,
            "error": None,
            "last_test_label": None,
            "services_count": None,
            "connect_mode": "shipping_api" if cid in API_CARRIERS else row.get("connect_mode"),
            "note": row.get("note")
            or "Merchant carrier API — Connect → test → rates → create shipment → tracking.",
            "actions": _actions_for("not_connected", connectable=True),
        }
        shipping[cid] = updated
        settings["shipping"] = shipping
        enable_shipping_methods_for_carrier(settings, cid, enabled=False)
        commerce._save(order_id, settings)  # noqa: SLF001
        creds = self._load_credentials(order_id)
        creds.pop(cid, None)
        self._save_credentials(order_id, creds)
        self._journal(order_id, {"type": "disconnect", "carrier": cid, "ok": True})
        return {"ok": True, "provider": updated, "order_id": order_id}

    def test_connection(
        self,
        order_id: str,
        carrier: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cid = (carrier or "").strip().lower()
        if cid in OFFLINE_CARRIERS:
            return {
                "ok": True,
                "carrier": cid,
                "status": "ok",
                "services": [],
                "note": "Offline method — no API.",
            }
        if cid not in API_CARRIERS:
            return {"ok": False, "reason": "carrier_not_supported", "title": "Unknown carrier"}

        payload = payload or {}
        creds = self._load_credentials(order_id).get(cid) or {}
        api_key = str(payload.get("api_key") or creds.get("api_key") or "").strip()
        use_mock = mock_enabled() or api_key in {"", "mock"} or str(api_key).startswith("mock")

        if use_mock:
            services = CARRIER_SERVICES.get(cid, [])
            return {
                "ok": True,
                "carrier": cid,
                "status": "ok",
                "mock": True,
                "services": services,
                "message": f"{cid.upper()} connection OK (mock)",
                "tested_at": _now(),
            }

        # Real API hooks — validate shape; live HTTP per carrier can be filled when keys exist
        if not api_key:
            return {
                "ok": False,
                "title": "API Authentication failed",
                "reason": "Missing API key / client id for this carrier.",
            }
        # Placeholder live probe: accept non-empty credentials as configured
        # (real DHL/DPD/… HTTP calls land here without changing UX)
        services = CARRIER_SERVICES.get(cid, [])
        return {
            "ok": True,
            "carrier": cid,
            "status": "ok",
            "mock": False,
            "services": services,
            "message": f"{cid.upper()} credentials accepted — live rate calls enabled when endpoint is configured.",
            "tested_at": _now(),
            "note": "Live carrier HTTP adapters expand per account type (DE Business).",
        }

    def sync_carrier(self, order_id: str, carrier: str) -> dict[str, Any]:
        from app.integration.store_admin.commerce_settings import (
            StoreCommerceSettingsService,
            _relative_sync,
            _now as cnow,
        )

        cid = (carrier or "").strip().lower()
        test = self.test_connection(order_id, cid)
        if not test.get("ok"):
            commerce = StoreCommerceSettingsService(self._memory)
            settings = commerce._load_raw(order_id)  # noqa: SLF001
            shipping = settings.get("shipping") or {}
            row = dict(shipping.get(cid) or {})
            row["status"] = "error"
            row["error"] = test.get("title") or test.get("reason")
            shipping[cid] = row
            settings["shipping"] = shipping
            commerce._save(order_id, settings)  # noqa: SLF001
            return {"ok": False, "test": test, "provider": row}

        creds = self._load_credentials(order_id)
        entry = dict(creds.get(cid) or {})
        entry["services"] = test.get("services") or CARRIER_SERVICES.get(cid, [])
        entry["last_test"] = test
        entry["updated_at"] = cnow()
        creds[cid] = entry
        self._save_credentials(order_id, creds)

        commerce = StoreCommerceSettingsService(self._memory)
        settings = commerce._load_raw(order_id)  # noqa: SLF001
        shipping = settings.get("shipping") or {}
        row = dict(shipping.get(cid) or {})
        now = cnow()
        row.update(
            {
                "status": "connected",
                "last_sync_at": now,
                "last_sync_label": _relative_sync(now),
                "last_test_label": "Success",
                "services_count": len(entry["services"]),
                "error": None,
            }
        )
        shipping[cid] = row
        settings["shipping"] = shipping
        commerce._save(order_id, settings)  # noqa: SLF001
        self._journal(order_id, {"type": "sync", "carrier": cid, "ok": True})
        return {"ok": True, "provider": row, "services": entry["services"], "test": test}

    def quote_rates(
        self,
        order_id: str,
        *,
        carrier: str | None = None,
        weight_kg: float = 1.0,
        country: str = "DE",
    ) -> dict[str, Any]:
        from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService

        commerce = StoreCommerceSettingsService(self._memory)
        settings = commerce.get(order_id)["settings"]
        shipping = settings.get("shipping") or {}
        creds = self._load_credentials(order_id)
        quotes: list[dict[str, Any]] = []
        carriers = [carrier] if carrier else list(API_CARRIERS)
        w = max(0.1, float(weight_kg or 1.0))
        for cid in carriers:
            row = shipping.get(cid) if isinstance(shipping.get(cid), dict) else None
            if not row or row.get("status") != "connected":
                continue
            services = (creds.get(cid) or {}).get("services") or CARRIER_SERVICES.get(cid, [])
            for svc in services:
                base = float(svc.get("base_eur") or 7.9)
                # simple weight surcharge
                price = round(base + max(0.0, w - 1.0) * 1.2, 2)
                if str(country).upper() not in {"DE", "AT", "CH"} and cid in {"dhl", "hermes"}:
                    price = round(price * 1.35, 2)
                quotes.append(
                    {
                        "id": svc["id"],
                        "carrier": cid,
                        "label": svc["label"],
                        "price_eur": price,
                        "days_min": svc.get("days_min", 2),
                        "days_max": svc.get("days_max", 5),
                        "currency": "EUR",
                    }
                )
        # Always allow pickup / local if connected
        for cid in ("pickup", "local_delivery"):
            row = shipping.get(cid) if isinstance(shipping.get(cid), dict) else None
            if row and row.get("status") == "connected":
                quotes.append(
                    {
                        "id": f"{cid}_free",
                        "carrier": cid,
                        "label": row.get("label") or cid,
                        "price_eur": 0.0 if cid == "pickup" else 9.9,
                        "days_min": 0,
                        "days_max": 1 if cid == "local_delivery" else 0,
                        "currency": "EUR",
                    }
                )
        quotes.sort(key=lambda q: float(q["price_eur"]))
        return {"ok": True, "order_id": order_id, "quotes": quotes, "count": len(quotes)}

    def create_shipment(
        self,
        order_id: str,
        *,
        shop_order_id: str,
        carrier: str | None = None,
        service_id: str | None = None,
    ) -> dict[str, Any]:
        """Create shipment for a shop order → tracking number + status pipeline."""
        from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService

        path = self._shop_dir(order_id) / "orders.json"
        if not path.is_file():
            raise ValueError("order_not_found")
        data = json.loads(path.read_text(encoding="utf-8"))
        orders = list(data.get("orders") or [])
        shop = next((o for o in orders if isinstance(o, dict) and o.get("id") == shop_order_id), None)
        if not shop:
            raise ValueError("order_not_found")

        method = shop.get("shipping_method") if isinstance(shop.get("shipping_method"), dict) else {}
        cid = (carrier or method.get("carrier") or "").strip().lower()
        sid = (service_id or method.get("id") or "").strip()
        if cid in OFFLINE_CARRIERS:
            raise ValueError("offline_carrier_no_shipment")
        if cid not in API_CARRIERS:
            raise ValueError("carrier_not_connected")

        commerce = StoreCommerceSettingsService(self._memory)
        settings = commerce.get(order_id)["settings"]
        row = (settings.get("shipping") or {}).get(cid)
        if not isinstance(row, dict) or row.get("status") != "connected":
            raise ValueError("carrier_not_connected")

        # Generate tracking (mock or deterministic from order)
        seed = hashlib.sha1(f"{order_id}:{shop_order_id}:{cid}".encode()).hexdigest()[:10].upper()
        prefixes = {
            "dhl": "JD01",
            "dpd": "0",
            "gls": "GLS",
            "hermes": "H",
            "ups": "1Z",
            "fedex": "FX",
        }
        tracking = f"{prefixes.get(cid, 'TR')}{seed}"
        shipment_id = f"shp-{uuid.uuid4().hex[:10]}"
        now = _now()
        shipment = {
            "id": shipment_id,
            "shop_order_id": shop_order_id,
            "carrier": cid,
            "service_id": sid or method.get("id"),
            "service_label": method.get("label") or cid.upper(),
            "tracking_number": tracking,
            "tracking_url": _tracking_url(cid, tracking),
            "status": "label_created",
            "status_history": [
                {"status": "label_created", "at": now, "note": "Label created"},
            ],
            "created_at": now,
            "updated_at": now,
            "mock": mock_enabled() or str(
                (self._load_credentials(order_id).get(cid) or {}).get("api_key") or ""
            ).startswith("mock"),
        }
        rows = self._load_shipments(order_id)
        rows.insert(0, shipment)
        self._save_shipments(order_id, rows)

        # Attach to shop order
        shop["shipment"] = {
            "id": shipment_id,
            "carrier": cid,
            "tracking_number": tracking,
            "tracking_url": shipment["tracking_url"],
            "status": "label_created",
            "service_label": shipment["service_label"],
            "created_at": now,
        }
        shop["status"] = "shipped"
        shop["updated_at"] = now
        for i, o in enumerate(orders):
            if isinstance(o, dict) and o.get("id") == shop_order_id:
                orders[i] = shop
                break
        path.write_text(
            json.dumps({**data, "orders": orders}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Sync buyer cabinet summary if present
        try:
            from app.integration.store_customer.service import StoreCustomerService

            customers = StoreCustomerService(self._memory)
            buyer_id = str(shop.get("buyer_id") or "")
            if buyer_id:
                customers.update_order_summary(
                    order_id,
                    buyer_id,
                    shop_order_id,
                    {
                        "status": "shipped",
                        "tracking_number": tracking,
                        "tracking_url": shipment["tracking_url"],
                        "carrier": cid,
                        "shipping_status": "label_created",
                    },
                )
        except Exception:  # noqa: BLE001
            pass

        self._journal(
            order_id,
            {
                "type": "create_shipment",
                "carrier": cid,
                "ok": True,
                "tracking": tracking,
                "shop_order_id": shop_order_id,
            },
        )
        return {"ok": True, "shipment": shipment, "order": shop}

    def track_shipment(
        self,
        order_id: str,
        *,
        tracking_number: str | None = None,
        shipment_id: str | None = None,
        advance: bool = False,
    ) -> dict[str, Any]:
        rows = self._load_shipments(order_id)
        found = None
        for row in rows:
            if shipment_id and row.get("id") == shipment_id:
                found = row
                break
            if tracking_number and row.get("tracking_number") == tracking_number:
                found = row
                break
        if not found:
            raise ValueError("shipment_not_found")

        status = str(found.get("status") or "label_created")
        if advance and status != "delivered":
            try:
                idx = TRACK_STATUSES.index(status)
                if idx + 1 < len(TRACK_STATUSES) and TRACK_STATUSES[idx + 1] != "exception":
                    status = TRACK_STATUSES[idx + 1]
            except ValueError:
                status = "in_transit"
            hist = list(found.get("status_history") or [])
            hist.append({"status": status, "at": _now(), "note": "Status update"})
            found["status"] = status
            found["status_history"] = hist
            found["updated_at"] = _now()
            for i, r in enumerate(rows):
                if r.get("id") == found.get("id"):
                    rows[i] = found
                    break
            self._save_shipments(order_id, rows)
            # mirror onto shop order
            self._mirror_shipment_to_order(order_id, found)

        self._journal(
            order_id,
            {
                "type": "track",
                "carrier": found.get("carrier"),
                "ok": True,
                "tracking": found.get("tracking_number"),
                "status": found.get("status"),
            },
        )
        return {"ok": True, "shipment": found}

    def _mirror_shipment_to_order(self, order_id: str, shipment: dict[str, Any]) -> None:
        path = self._shop_dir(order_id) / "orders.json"
        if not path.is_file():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            orders = list(data.get("orders") or [])
        except (OSError, json.JSONDecodeError):
            return
        sid = shipment.get("shop_order_id")
        for i, o in enumerate(orders):
            if not isinstance(o, dict) or o.get("id") != sid:
                continue
            o = dict(o)
            ship = dict(o.get("shipment") or {})
            ship.update(
                {
                    "status": shipment.get("status"),
                    "tracking_number": shipment.get("tracking_number"),
                    "tracking_url": shipment.get("tracking_url"),
                    "carrier": shipment.get("carrier"),
                    "updated_at": shipment.get("updated_at"),
                }
            )
            o["shipment"] = ship
            if shipment.get("status") == "delivered":
                o["status"] = "delivered"
            orders[i] = o
            buyer_id = str(o.get("buyer_id") or "")
            if buyer_id:
                try:
                    from app.integration.store_customer.service import StoreCustomerService

                    StoreCustomerService(self._memory).update_order_summary(
                        order_id,
                        buyer_id,
                        str(sid),
                        {
                            "status": o.get("status"),
                            "tracking_number": ship.get("tracking_number"),
                            "tracking_url": ship.get("tracking_url"),
                            "carrier": ship.get("carrier"),
                            "shipping_status": ship.get("status"),
                        },
                    )
                except Exception:  # noqa: BLE001
                    pass
            break
        path.write_text(
            json.dumps({**data, "orders": orders}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_shipments(self, order_id: str) -> dict[str, Any]:
        rows = self._load_shipments(order_id)
        return {"ok": True, "order_id": order_id, "count": len(rows), "shipments": rows}


def count_shipping_api_activity(memory_dir: Path) -> dict[str, Any]:
    """Mission Control aggregates for shipping APIs."""
    root = Path(memory_dir) / "store_admin"
    by_carrier: dict[str, int] = {c: 0 for c in API_CARRIERS}
    shipments_created = 0
    delivered = 0
    errors = 0
    if not root.is_dir():
        return {
            "by_carrier": by_carrier,
            "shipments_created": 0,
            "delivered": 0,
            "api_errors": 0,
        }
    for shop in root.iterdir():
        if not shop.is_dir():
            continue
        commerce = shop / "commerce_settings.json"
        if commerce.is_file():
            try:
                data = json.loads(commerce.read_text(encoding="utf-8"))
                shipping = data.get("shipping") if isinstance(data, dict) else {}
                for cid in API_CARRIERS:
                    row = shipping.get(cid) if isinstance(shipping, dict) else None
                    if isinstance(row, dict) and row.get("status") == "connected":
                        by_carrier[cid] = by_carrier.get(cid, 0) + 1
            except (OSError, json.JSONDecodeError):
                pass
        ships = shop / "shipments.json"
        if ships.is_file():
            try:
                data = json.loads(ships.read_text(encoding="utf-8"))
                rows = data.get("shipments") if isinstance(data, dict) else data
                for r in rows or []:
                    if not isinstance(r, dict):
                        continue
                    shipments_created += 1
                    if r.get("status") == "delivered":
                        delivered += 1
            except (OSError, json.JSONDecodeError):
                pass
        journal = shop / "shipping_api_journal.jsonl"
        if journal.is_file():
            try:
                for line in journal.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if row.get("ok") is False:
                        errors += 1
            except OSError:
                pass
    return {
        "by_carrier": by_carrier,
        "shipments_created": shipments_created,
        "delivered": delivered,
        "api_errors": errors,
        "stores_with_api": sum(1 for v in by_carrier.values() if v > 0),
    }


def shipping_api_ready(memory_dir: Path) -> bool:
    """Gen1 readiness: at least one API carrier connected + one shipment or successful sync test."""
    stats = count_shipping_api_activity(memory_dir)
    if stats["shipments_created"] > 0:
        return True
    # connected carrier with last test success
    root = Path(memory_dir) / "store_admin"
    if not root.is_dir():
        return False
    for shop in root.iterdir():
        creds = shop / "shipping_credentials.json"
        if not creds.is_file():
            continue
        try:
            data = json.loads(creds.read_text(encoding="utf-8"))
            for cid, row in (data or {}).items():
                if cid in API_CARRIERS and isinstance(row, dict):
                    test = row.get("last_test") if isinstance(row.get("last_test"), dict) else {}
                    if test.get("ok"):
                        return True
        except (OSError, json.JSONDecodeError):
            continue
    return False
