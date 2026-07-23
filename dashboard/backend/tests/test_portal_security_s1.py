"""Security Gate S1 — adversarial checks (IDOR · isolation · prompt leak)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.billing_facade import BillingFacade
from app.portal.billing_store import InMemoryBillingStore
from app.portal.business_knowledge_store import InMemoryBusinessKnowledgeStore
from app.portal.channel_connection_store import InMemoryChannelConnectionStore
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import InMemoryChatBotBusinessProfileStore
from app.portal.conversation_assistance_view import AssistanceDraftView
from app.portal.conversation_facade import ConversationFacade
from app.portal.conversation_store import InMemoryConversationStore, InMemoryMessageStore
from app.portal.industry_template import InMemoryIndustryTemplateStore
from app.portal.license_facade import LicenseFacade
from app.portal.license_store import InMemoryLicenseStore
from app.portal.portal_billing_registration import register_portal_billing
from app.portal.portal_billing_router import clear_billing_facade
from app.portal.portal_chatbot_conversations_registration import (
    register_portal_chatbot_conversations,
)
from app.portal.portal_chatbot_conversations_router import clear_conversation_facade
from app.portal.portal_license_registration import register_portal_licenses
from app.portal.portal_license_router import clear_license_facade
from app.portal.portal_my_products_registration import register_portal_my_products
from app.portal.portal_my_products_router import clear_product_ownership_facade
from app.portal.portal_product_activation_registration import (
    register_portal_product_activation,
)
from app.portal.portal_product_activation_router import clear_product_activation_facade
from app.portal.portal_purchase_registration import register_portal_purchases
from app.portal.portal_purchase_router import clear_purchase_facade
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import InMemoryProductActivationStore
from app.portal.product_catalog_store import InMemoryProductCatalogStore
from app.portal.product_ownership_store import InMemoryProductOwnershipStore
from app.portal.purchase_facade import PurchaseFacade
from app.portal.purchase_store import InMemoryPurchaseStore


def _two_accounts_app():
    clear_conversation_facade()
    clear_billing_facade()
    clear_license_facade()
    clear_purchase_facade()
    clear_product_activation_facade()
    clear_product_ownership_facade()

    alice = new_account(email="alice@s1.test", display_name="Alice", status="ready")
    bob = new_account(email="bob@s1.test", display_name="Bob", status="ready")
    profiles = InMemoryChatBotBusinessProfileStore()
    ChatBotBusinessProfileFacade.from_parts(profiles=profiles).bootstrap(
        account_id=alice.account_id, industry="dental", business_name="Alice Shop"
    )
    ChatBotBusinessProfileFacade.from_parts(profiles=profiles).bootstrap(
        account_id=bob.account_id, industry="dental", business_name="Bob Shop"
    )

    knowledge = InMemoryBusinessKnowledgeStore()
    channels = InMemoryChannelConnectionStore()
    templates = InMemoryIndustryTemplateStore()
    conversations = InMemoryConversationStore()
    messages = InMemoryMessageStore()

    catalog = InMemoryProductCatalogStore()
    ownerships = InMemoryProductOwnershipStore()
    activations = InMemoryProductActivationStore()
    activation = ProductActivationFacade.from_parts(
        catalog=catalog, ownerships=ownerships, activations=activations
    )
    license_store = InMemoryLicenseStore()
    licenses = LicenseFacade.from_parts(
        catalog=catalog, licenses=license_store, activation=activation
    )
    billing_store = InMemoryBillingStore()
    billing = BillingFacade.from_store(billing_store)
    purchases = InMemoryPurchaseStore()

    holder: dict[str, object] = {"account": alice}

    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = holder["account"]
        return await call_next(request)

    register_portal_chatbot_conversations(
        app,
        profiles=profiles,
        knowledge=knowledge,
        channels=channels,
        templates=templates,
        conversation_store=conversations,
        message_store=messages,
    )
    register_portal_my_products(app, ownership_store=ownerships, catalog=catalog)
    register_portal_product_activation(
        app,
        ownership_store=ownerships,
        catalog=catalog,
        activation_store=activations,
        facade=activation,
    )
    register_portal_licenses(
        app, catalog=catalog, license_store=license_store, activation=activation
    )
    register_portal_billing(app, store=billing_store)
    register_portal_purchases(
        app, licenses=licenses, billing=billing, purchase_store=purchases
    )

    return (
        app,
        alice,
        bob,
        holder,
        PurchaseFacade.from_parts(
            catalog=catalog,
            purchases=purchases,
            licenses=licenses,
            billing=billing,
        ),
    )


def test_idor_conversation_not_visible_to_other_account():
    app, alice, bob, holder, _purchase = _two_accounts_app()
    http = TestClient(app)
    try:
        holder["account"] = alice
        created = http.post("/portal/chatbot/conversations", json={})
        assert created.status_code == 200
        conv_id = created.json()["conversation_id"]

        holder["account"] = bob
        stolen = http.get(f"/portal/chatbot/conversations/{conv_id}")
        assert stolen.status_code in {403, 404, 400}
        listed = http.get("/portal/chatbot/conversations")
        assert listed.status_code == 200
        ids = {row["conversation_id"] for row in listed.json()}
        assert conv_id not in ids
    finally:
        clear_conversation_facade()
        clear_billing_facade()
        clear_license_facade()
        clear_purchase_facade()
        clear_product_activation_facade()
        clear_product_ownership_facade()


def test_cross_account_licenses_and_billing_isolated():
    app, alice, bob, holder, purchase = _two_accounts_app()
    http = TestClient(app)
    try:
        purchase.purchase(account_id=alice.account_id, catalog_product_id="prod_chatbot")

        holder["account"] = bob
        bob_licenses = http.get("/portal/licenses")
        assert bob_licenses.status_code == 200
        assert bob_licenses.json() == []

        bob_billing = http.get("/portal/billing")
        assert bob_billing.status_code == 200
        assert bob_billing.json() == []

        bob_products = http.get("/portal/my-products")
        assert bob_products.status_code == 200
        assert bob_products.json() == []

        holder["account"] = alice
        alice_licenses = http.get("/portal/licenses")
        assert alice_licenses.status_code == 200
        assert len(alice_licenses.json()) >= 1
    finally:
        clear_conversation_facade()
        clear_billing_facade()
        clear_license_facade()
        clear_purchase_facade()
        clear_product_activation_facade()
        clear_product_ownership_facade()


def test_assistance_draft_view_does_not_expose_system_prompt():
    view = AssistanceDraftView(
        conversation_id="c1",
        draft_text="Hello customer",
        provider_type="stub",
        prompt_package_id="pkg",
        policy_language="de",
        auto_sent=False,
    )
    payload = view.as_dict()
    blob = str(payload).lower()
    assert "system_prompt" not in blob
    assert "operator assist only" not in blob
    assert payload["auto_sent"] is False
    assert set(payload.keys()) <= {
        "conversation_id",
        "draft_text",
        "provider_type",
        "prompt_package_id",
        "policy_language",
        "auto_sent",
    }
