"""B3 Client Workspace — isolated review fixture (dev/test only).

Seeds a real Customer Identity account via ``CustomerIdentityService.register``
(same path as GWT / unit tests): password hash + JWT. Does **not** disable
HTTP OTP and does **not** invent production login bypasses.

Email domain: ``@virtuscore-test.example`` (never a real customer).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.factory.factory_service import FactoryService
from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.customer_identity.store import CustomerIdentityStore
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService

ENGINE_ID = "b3_client_workspace_review_fixture_v1"

# Isolated test identity — not a personal mailbox.
B3_REVIEW_EMAIL = "b3-review-gate@virtuscore-test.example"
B3_REVIEW_PASSWORD = "B3ReviewGatePass1!"
B3_REVIEW_NAME = "B3 Review Gate"
B3_REVIEW_COMPANY = "B3 Review Handwerk Berlin"
B3_EMPTY_EMAIL = "b3-review-empty@virtuscore-test.example"
B3_EMPTY_PASSWORD = "B3ReviewEmptyPass1!"


@dataclass(frozen=True)
class B3ReviewFixture:
    memory_dir: Path
    email: str
    password: str
    customer_id: str
    token: str
    order_id: str | None
    product_id: str | None
    download_ready: bool
    download_url: str | None
    business_name: str


def _ensure_jwt_secret() -> None:
    if not (os.environ.get("GENESIS_CLIENT_JWT_SECRET") or "").strip():
        os.environ["GENESIS_CLIENT_JWT_SECRET"] = "b3-review-gate-jwt-secret-32chars!!"


def _build_sales(memory: Path) -> tuple[SalesOrderService, RevenuePipelineService]:
    factory = FactoryService(memory_dir=memory, sandbox_dir=memory / "sandbox")
    intent = FactoryIntentService(memory_dir=memory, factory=factory)
    sales = SalesOrderService(memory, intent)
    revenue = RevenuePipelineService(
        sales,
        FinanceService(memory),
        PaymentCheckoutService(memory),
        OwnerNotificationService(memory),
    )
    return sales, revenue


def _register_or_login(
    identity: CustomerIdentityService,
    *,
    email: str,
    password: str,
    name: str,
) -> dict[str, Any]:
    try:
        return identity.register(
            name=name,
            email=email,
            password=password,
            locale="de",
            country="DE",
        )
    except HTTPException as exc:
        if exc.detail == "email_already_registered":
            return identity.login(email=email, password=password)
        raise


def _plant_packable_website(
    memory: Path,
    *,
    order_id: str,
    business_name: str,
    customer_id: str,
    email: str,
) -> tuple[str, Path]:
    """Minimal demo product (index.html + meta) — avoids Factory Media Integrity.

    Still goes through real ``_client_download_ready`` / ownership gates.
    """
    product_id = f"b3-review-{order_id}"
    product_dir = memory / "sandbox" / product_id
    assets = product_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    # Non-trivial HTML (≥4KB) for demo packable check
    body = (
        f"<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/>"
        f"<title>{business_name}</title></head><body>"
        f"<h1>{business_name}</h1>"
        f"<p>B3 Review Gate fixture site — Handwerk Berlin.</p>"
        + ("<p>Virtus Core Client Workspace E2E.</p>\n" * 120)
        + "</body></html>"
    )
    (product_dir / "index.html").write_text(body, encoding="utf-8")
    meta = {
        "product_id": product_id,
        "business_name": business_name,
        "market_code": "DE",
        "demo_order": True,
        "allow_demo_pack": True,
        "validation_passed": True,
        "package_id": "business",
        "customer_id": customer_id,
        "email": email,
    }
    (product_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return product_id, product_dir


def seed_b3_review_client(
    memory_dir: Path,
    *,
    with_ready_website: bool = True,
    email: str = B3_REVIEW_EMAIL,
    password: str = B3_REVIEW_PASSWORD,
    name: str = B3_REVIEW_NAME,
) -> B3ReviewFixture:
    """Provision isolated client + optional paid Website with ZIP ready."""
    _ensure_jwt_secret()
    os.environ.setdefault("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    os.environ.setdefault("GENESIS_PAYMENT_SANDBOX", "1")
    os.environ.setdefault("GENESIS_SMTP_MOCK", "1")

    memory = Path(memory_dir)
    memory.mkdir(parents=True, exist_ok=True)

    identity = CustomerIdentityService(memory)
    session = _register_or_login(
        identity, email=email, password=password, name=name
    )
    token = str(session.get("token") or "").strip()
    if not token:
        raise RuntimeError("b3_fixture_token_missing")

    store = CustomerIdentityStore(memory)
    customer_id = str(store.find_customer_by_email(email) or "").strip()
    if not customer_id:
        raise RuntimeError("b3_fixture_customer_missing")

    # DE chrome: never leave RU default "Моя компания" on the review fixture.
    display_name = B3_REVIEW_COMPANY if with_ready_website else "Mein Unternehmen"
    company = store.load_company_by_customer(customer_id)
    if company:
        company.name = display_name
        store.save_company(company)
    card = store.load_card(customer_id)
    if card:
        card.company_display_name = display_name
        store.save_card(card)

    order_id: str | None = None
    product_id: str | None = None
    download_ready = False
    download_url: str | None = None
    business_name = B3_REVIEW_COMPANY

    if with_ready_website:
        from datetime import datetime, timezone

        sales, _revenue = _build_sales(memory)
        created = sales.create_order(
            {
                "business_name": B3_REVIEW_COMPANY,
                "description": (
                    "B3 Review Gate — Handwerk Berlin. "
                    "Isolated fixture for Client Workspace E2E."
                ),
                "email": email,
                "phone": "+49 30 0000000",
                "package_id": "business",
                "city": "Berlin",
                "niche": "handwerk",
                "market_code": "DE",
                "ui_lang": "de",
                "demo": True,
                "customer_id": customer_id,
                "client_legal": {
                    "owner_name": name,
                    "street": "Reviewstr. 1",
                    "zip": "10115",
                    "city": "Berlin",
                    "email": email,
                },
            }
        )
        order_id = str(created["order_id"])
        product_id, _dir = _plant_packable_website(
            memory,
            order_id=order_id,
            business_name=B3_REVIEW_COMPANY,
            customer_id=customer_id,
            email=email,
        )
        order = sales.get_order(order_id)
        if not order:
            raise RuntimeError("b3_fixture_order_missing")
        now = datetime.now(timezone.utc).isoformat()
        order["customer_id"] = customer_id
        order["email"] = email
        order["product_id"] = product_id
        order["demo"] = True
        order["payment_mode"] = "demo"
        order["status"] = "ready"
        order["paid_at"] = now
        order["updated_at"] = now
        order["status_label"] = "Ready"
        sales._save_order(order)  # noqa: SLF001 — fixture seed only

        status = sales.public_status(order_id)
        download_ready = bool(status.get("download_ready"))
        download_url = status.get("download_url")
        if not download_ready or not product_id:
            raise RuntimeError(
                f"b3_fixture_website_not_ready status={status.get('status')} "
                f"download_ready={download_ready}"
            )
        sales.attach_customer_by_email(customer_id=customer_id, email=email)

    return B3ReviewFixture(
        memory_dir=memory,
        email=email,
        password=password,
        customer_id=customer_id,
        token=token,
        order_id=order_id,
        product_id=product_id,
        download_ready=download_ready,
        download_url=str(download_url) if download_url else None,
        business_name=business_name,
    )


def seed_b3_empty_client(memory_dir: Path) -> B3ReviewFixture:
    """Client with real auth but zero products — honesty baseline."""
    return seed_b3_review_client(
        memory_dir,
        with_ready_website=False,
        email=B3_EMPTY_EMAIL,
        password=B3_EMPTY_PASSWORD,
        name="B3 Empty Gate",
    )
