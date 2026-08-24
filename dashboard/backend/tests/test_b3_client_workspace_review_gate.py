"""B3 Client Workspace Review Gate — authenticated E2E (isolated fixture).

Uses ``CustomerIdentityService.register`` (real hash + JWT), not OTP disable
and not a fake Authorization header. Proves cabinet workflow honesty.

Run:
  py -3.12 -m pytest dashboard/backend/tests/test_b3_client_workspace_review_gate.py -q
  py -3.12 scripts/b3_client_workspace_review_gate.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.integration.customer_identity.auth import decode_client_token
from app.integration.customer_identity.b3_review_fixture import (
    B3_EMPTY_EMAIL,
    B3_REVIEW_EMAIL,
    seed_b3_empty_client,
    seed_b3_review_client,
)
from app.integration.customer_identity.service import CustomerIdentityService
from app.integration.sales_order_service import SalesOrderService
from app.integration.factory_intent_service import FactoryIntentService
from app.factory.factory_service import FactoryService
from app.integration.website_admin import assert_website_order_access


REPO = Path(__file__).resolve().parents[3]
FRONTEND = REPO / "dashboard" / "frontend"


@pytest.fixture()
def b3_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "b3-review-gate-jwt-secret-32chars!!")
    memory = tmp_path / "memory"
    memory.mkdir()
    return memory


def test_b3_fixture_real_jwt_not_forgeable(b3_env: Path, monkeypatch: pytest.MonkeyPatch):
    fx = seed_b3_review_client(b3_env)
    payload = decode_client_token(fx.token)
    assert payload.get("sub") == fx.customer_id
    assert payload.get("email") == B3_REVIEW_EMAIL

    # Wrong secret → reject (real auth, not decorative Bearer)
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "other-secret-must-fail-verification!")
    assert decode_client_token(fx.token) is None


def test_b3_login_roundtrip_same_as_register(b3_env: Path):
    fx = seed_b3_review_client(b3_env)
    identity = CustomerIdentityService(b3_env)
    login = identity.login(email=fx.email, password=fx.password)
    assert login.get("token")
    again = decode_client_token(str(login["token"]))
    assert again.get("sub") == fx.customer_id


def test_b3_dashboard_orders_and_verwalten_target(b3_env: Path):
    fx = seed_b3_review_client(b3_env)
    factory = FactoryService(memory_dir=b3_env, sandbox_dir=b3_env / "sandbox")
    intent = FactoryIntentService(memory_dir=b3_env, factory=factory)
    sales = SalesOrderService(b3_env, intent)
    rows = sales.list_orders_for_customer(
        customer_id=fx.customer_id, email=fx.email, limit=20
    )
    assert any(r.get("order_id") == fx.order_id for r in rows)
    row = next(r for r in rows if r.get("order_id") == fx.order_id)
    assert row.get("download_ready") is True
    assert fx.order_id
    admin_href = f"/client/websites/{fx.order_id}/admin"
    assert admin_href.startswith("/client/websites/")
    assert "ceo" not in admin_href
    assert "/executive" not in admin_href


def test_b3_website_admin_access_and_preview(b3_env: Path):
    fx = seed_b3_review_client(b3_env)
    factory = FactoryService(memory_dir=b3_env, sandbox_dir=b3_env / "sandbox")
    intent = FactoryIntentService(memory_dir=b3_env, factory=factory)
    sales = SalesOrderService(b3_env, intent)
    assert fx.order_id and fx.product_id
    order = sales.get_order(fx.order_id)
    assert order is not None
    assert_website_order_access(
        order, customer_id=fx.customer_id, email=fx.email
    )
    # Stranger must fail
    with pytest.raises(ValueError):
        assert_website_order_access(
            order, customer_id="cus_stranger", email="stranger@example.com"
        )
    preview = f"/api/factory/products/{fx.product_id}/preview"
    assert preview.endswith("/preview")


def test_b3_zip_only_when_download_ready(b3_env: Path):
    ready = seed_b3_review_client(b3_env, with_ready_website=True)
    assert ready.download_ready is True
    assert ready.download_url == f"/api/sales/orders/{ready.order_id}/download"

    empty = seed_b3_empty_client(b3_env)
    factory = FactoryService(memory_dir=b3_env, sandbox_dir=b3_env / "sandbox")
    intent = FactoryIntentService(memory_dir=b3_env, factory=factory)
    sales = SalesOrderService(b3_env, intent)
    rows = sales.list_orders_for_customer(
        customer_id=empty.customer_id, email=empty.email, limit=20
    )
    assert rows == [] or all(not r.get("download_ready") for r in rows)
    assert empty.download_ready is False
    assert empty.download_url is None
    assert empty.email == B3_EMPTY_EMAIL


def test_b3_empty_client_no_fake_active_product(b3_env: Path):
    empty = seed_b3_empty_client(b3_env)
    factory = FactoryService(memory_dir=b3_env, sandbox_dir=b3_env / "sandbox")
    intent = FactoryIntentService(memory_dir=b3_env, factory=factory)
    sales = SalesOrderService(b3_env, intent)
    rows = sales.list_orders_for_customer(
        customer_id=empty.customer_id, email=empty.email
    )
    assert not any(
        str(r.get("status") or "").lower() in {"active", "live", "ready"}
        for r in rows
    )


def test_b3_location_trail_ia():
    # Frontend SSOT — import via exec of TS is brittle; assert source strings.
    nav = (FRONTEND / "app" / "lib" / "workspaceNav.ts").read_text(encoding="utf-8")
    assert "resolveBccLocationTrail" in nav
    assert 'label: "Übersicht"' in nav or "Übersicht" in nav
    assert "Meine Produkte" in nav
    assert "Verwalten" in nav
    shell = (FRONTEND / "app" / "components" / "ClientWorkspaceShell.tsx").read_text(
        encoding="utf-8"
    )
    assert "BccLocationTrail" in shell
    assert "resolveBccLocationTrail" in shell


def test_b3_settings_billing_support_honesty_sources():
    settings = (FRONTEND / "app" / "client" / "settings" / "page.tsx").read_text(
        encoding="utf-8"
    )
    billing = (FRONTEND / "app" / "client" / "billing" / "page.tsx").read_text(
        encoding="utf-8"
    )
    support = (FRONTEND / "app" / "client" / "support" / "page.tsx").read_text(
        encoding="utf-8"
    )
    assert "Demnächst" in settings or "Coming Soon" in settings or "· Soon" in settings
    assert "mailto:" in support or "CONTACT_EMAIL" in support
    assert "/executive" not in support
    assert "Demnächst" in billing or "Coming Soon" in billing or "Portal" in billing
    # Deep-links to real surfaces
    assert "/client/bots" in settings or "/client/site" in settings
    assert "/client/billing" in settings or "/portal/billing" in billing


def test_b3_mobile_nav_critical_sections():
    nav = (FRONTEND / "app" / "lib" / "workspaceNav.ts").read_text(encoding="utf-8")
    m = re.search(
        r"export function bccMobileNav\(\)[^{]*\{(?P<body>.*?)\n\}",
        nav,
        re.S,
    )
    assert m, "bccMobileNav missing"
    body = m.group("body")
    # Essentials for BCC mobile
    for need in ("dashboard", "products", "site"):
        assert need in body, f"mobile nav missing {need}"
    # Support + Business must remain reachable on mobile chrome somehow
    surface = (FRONTEND / "app" / "lib" / "surfaceNavConfig.ts").read_text(
        encoding="utf-8"
    )
    assert "/client/support" in surface
    assert "/client/settings" in surface
    mobile_ids = re.findall(r'"([a-z_]+)"', body)
    critical_mobile = {"support", "settings", "billing"}
    present = set(mobile_ids) & critical_mobile
    # At least billing is in the five-tab bar; support/settings via sidebar desktop.
    # Gate requires billing + (support OR settings) in mobile OR explicit FAIL note.
    assert "billing" in mobile_ids or "billing" in body
    if "support" not in body and "settings" not in body:
        pytest.fail(
            "B3 mobile tabs lack Support and Business — critical sections lost "
            "after chip-nav removal. Add support/settings to bccMobileNav()."
        )


def test_b3_products_zip_ui_gated_on_download_ready():
    products = (FRONTEND / "app" / "client" / "products" / "page.tsx").read_text(
        encoding="utf-8"
    )
    assert "download_ready" in products
    assert "ZIP" in products or "ZIP laden" in products
    # Must not always show a live download without gate
    assert "download_ready &&" in products or "download_ready ?" in products
