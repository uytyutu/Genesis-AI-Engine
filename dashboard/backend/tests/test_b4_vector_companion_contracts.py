"""B4.0 — Vector Business Companion contract lock (no turn pipeline)."""

from __future__ import annotations

import pytest

from app.integration.vector.companion_contracts import (
    ASSISTANT_NAME,
    B4_ENGINE,
    B4_SLICE_ORDER,
    CONFIRM_CTA_LABEL,
    CONTEXT_ENGINE_REQUIRED,
    CONTEXT_PATH,
    DEFAULT_GREETING_DE,
    ENTRY_SURFACE,
    FIRST_ACTION_KINDS,
    FORBIDDEN_WORLDS,
    READ_SCOPES,
    RESEARCH_DISCLAIMER_DE,
    RESEARCH_SOURCE_KIND,
    ActionProposal,
    CompanionTurnRequest,
    CompanionTurnResponse,
    ContextRef,
    ResearchSource,
    assert_action_kind_allowed,
    assert_context_engine,
    assert_research_labeled,
    location_from_path,
)


def test_b4_slice_order_locked():
    assert B4_SLICE_ORDER == (
        "B4.0",
        "B4.1",
        "B4.2",
        "B4.3",
        "B4.4",
        "B4.5",
        "B4.6",
        "B4.7",
    )
    # Research after analysis, not deferred past honesty
    assert B4_SLICE_ORDER.index("B4.6") == B4_SLICE_ORDER.index("B4.5") + 1
    assert B4_SLICE_ORDER.index("B4.7") == B4_SLICE_ORDER.index("B4.6") + 1


def test_context_ssot_pointer():
    ref = ContextRef()
    assert ref.path == CONTEXT_PATH == "/api/client/context"
    assert ref.engine == CONTEXT_ENGINE_REQUIRED == "b3_client_context_v1"
    assert_context_engine("b3_client_context_v1")
    with pytest.raises(ValueError):
        assert_context_engine("vector_private_copy_v1")


def test_entry_and_voice_lock():
    assert ENTRY_SURFACE == "VectorDialogDock"
    assert ASSISTANT_NAME == "Vector"
    assert "Business Assistant" in DEFAULT_GREETING_DE
    assert CONFIRM_CTA_LABEL == "Übernehmen"


def test_read_scopes_match_context_contract():
    for scope in (
        "business",
        "products",
        "website",
        "shop",
        "ai",
        "analytics",
        "orders",
    ):
        assert scope in READ_SCOPES


def test_first_action_set_and_confirm_shape():
    assert "navigate" in FIRST_ACTION_KINDS
    assert "live_website_capability" in FIRST_ACTION_KINDS
    assert "live_store_capability" in FIRST_ACTION_KINDS
    assert_action_kind_allowed("navigate")
    with pytest.raises(ValueError):
        assert_action_kind_allowed("auto_apply_seo_without_confirm")

    prop = ActionProposal(
        proposal_id="p1",
        kind="navigate",
        capability_id=None,
        label="Analytics öffnen",
        summary="Zur Analytics-Seite navigieren",
        href="/client/analytics",
    )
    d = prop.to_dict()
    assert d["confirm_label"] == "Übernehmen"
    assert d["cancel_label"] == "Abbrechen"


def test_research_must_be_externally_labeled():
    with pytest.raises(ValueError):
        assert_research_labeled([])
    src = ResearchSource(
        title="Example",
        url="https://example.com/seo",
        retrieved_at="2026-08-24T12:00:00+00:00",
    )
    assert_research_labeled([src])
    payload = src.to_dict()
    assert payload["kind"] == RESEARCH_SOURCE_KIND == "external"
    assert "Externe Information" in payload["disclaimer"]
    assert RESEARCH_DISCLAIMER_DE in payload["disclaimer"]


def test_turn_response_defaults_honest():
    resp = CompanionTurnResponse(
        intent="read",
        message="Website Business ist aktiv; Analytics noch nicht verbunden.",
        cited_read_scopes=["products", "analytics"],
        location="dashboard",
    )
    d = resp.to_dict()
    assert d["engine"] == B4_ENGINE
    assert d["entry_surface"] == "VectorDialogDock"
    assert d["action_proposal"] is None
    assert "Übernehmen" in d["honesty"] or "ACTION" in d["honesty"]
    assert d["context_ref"]["engine"] == CONTEXT_ENGINE_REQUIRED


def test_request_envelope():
    req = CompanionTurnRequest(
        customer_id="cust_1",
        message="Was soll ich als Nächstes tun?",
        location="dashboard",
        page_path="/client",
    )
    assert req.to_dict()["surface"] == "customer"


def test_location_from_path():
    assert location_from_path("/client") == "dashboard"
    assert location_from_path("/client/analytics") == "analytics"
    assert location_from_path("/client/site") == "website"
    assert location_from_path("/client/shop") == "shop"
    assert location_from_path("/client/settings") == "settings"
    assert location_from_path("/client/support") == "support"
    assert location_from_path("/client/products") == "products"


def test_forbidden_worlds_boundary():
    for world in ("factory", "game", "farm", "other_tenant"):
        assert world in FORBIDDEN_WORLDS
