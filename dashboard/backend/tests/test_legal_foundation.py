"""Legal & Trust Foundation — document generation, gates, handoff."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.legal.document_generators import generate_document, list_document_catalog
from app.legal.entity_env import apply_env_overlay
from app.legal.entity_schema import LegalEntityConfig, OperatorInfo
from app.legal.entity_store import LegalEntityStore
from app.legal.handoff import one_time_purchase_handoff, subscription_handoff
from app.legal.locale_registry import list_market_profiles, localization_horizon_payload
from app.legal.service import LegalFoundationService
from app.legal.vector_rules import legal_trust_rules_for_vector
from app.legal.trust_catalog import build_trust_catalog
from app.integration.product_line import one_time_handoff_summary


def _complete_entity() -> LegalEntityConfig:
    return LegalEntityConfig(
        interview_completed=True,
        operator=OperatorInfo(
            full_name="Max Mustermann",
            address_street="Musterstraße 1",
            address_zip="10115",
            address_city="Berlin",
            email="hello@example.com",
            phone="+49 30 123456",
        ),
        documents_last_review="2026-07",
    )


def test_impressum_not_publishable_without_owner_data():
    doc = generate_document("impressum", LegalEntityConfig())
    assert doc is not None
    assert doc.publishable is False
    assert "operator.full_name" in doc.missing_fields


def test_impressum_publishable_with_complete_entity():
    doc = generate_document("impressum", _complete_entity())
    assert doc.publishable is True
    assert "Max Mustermann" in doc.sections[0].body


def test_all_seven_documents_in_catalog():
    catalog = list_document_catalog(LegalEntityConfig())
    ids = {item["id"] for item in catalog}
    assert ids == {
        "impressum",
        "datenschutz",
        "agb",
        "widerruf",
        "cookies",
        "ai_disclaimer",
        "intellectual_property",
    }


def test_agb_and_cookies_publishable_without_interview():
    cfg = LegalEntityConfig()
    assert generate_document("agb", cfg).publishable is True
    assert generate_document("cookies", cfg).publishable is True
    assert generate_document("ai_disclaimer", cfg).publishable is True
    assert generate_document("intellectual_property", cfg).publishable is True


def test_trust_catalog_never_sold_flag():
    trust = build_trust_catalog(_complete_entity())
    assert trust["access"]["never_sold"] is True
    assert trust["storage_location"]
    assert len(trust["data_collected"]) >= 4
    assert len(trust["trust_checklist"]) == 5
    assert len(trust["data_storage_guide"]) >= 6


def test_trust_checklist_covers_product_promises():
    trust = build_trust_catalog(_complete_entity())
    ids = {item["id"] for item in trust["trust_checklist"]}
    assert ids == {
        "data_protected",
        "project_ownership",
        "full_delivery",
        "no_data_sales",
        "market_compliance",
    }


def test_data_storage_guide_covers_deletion():
    guide = build_trust_catalog(_complete_entity())["data_storage_guide"]
    ids = {item["id"] for item in guide}
    assert "delete_project" in ids
    assert "delete_account" in ids


def test_handoff_one_time_lists_deliverables():
    text = one_time_purchase_handoff()
    assert "ZIP" in text
    assert "Quellcode" in text
    assert "Virtus Core" in text
    assert "Domain" in text


def test_handoff_one_time_domain_scenarios():
    text = one_time_purchase_handoff()
    assert "über uns gekauft" in text.lower() or "über uns" in text
    assert "DNS" in text


def test_handoff_subscription_lists_memory():
    text = subscription_handoff()
    assert "Projektspeicher" in text or "Projekthistorie" in text
    assert "Vector" in text
    assert "innerhalb" in text.lower() or "bleibt" in text.lower()


def test_ai_disclaimer_user_makes_final_decisions():
    doc = generate_document("ai_disclaimer", LegalEntityConfig())
    body = "\n".join(s.body for s in doc.sections)
    assert "Endgültige" in body or "treffen Sie selbst" in body
    assert "finanzielle" in body.lower() or "geschäftliche" in body.lower()


def test_locale_registry_architecture_ready():
    payload = localization_horizon_payload()
    assert payload["status"] == "architecture_ready"
    markets = list_market_profiles()
    codes = {m["market_code"] for m in markets}
    assert "DE" in codes
    assert "PL" in codes
    assert "US-CA" in codes
    pl = next(m for m in markets if m["market_code"] == "PL")
    assert "RODO" in str(pl) or any("rodo" in str(v).lower() for v in [pl])


def test_product_line_uses_legal_handoff():
    text = one_time_handoff_summary("website")
    assert text == one_time_purchase_handoff()


def test_legal_trust_rules_for_vector():
    rules = legal_trust_rules_for_vector()
    assert "Legal & Trust Foundation" in rules
    assert "legal_entity.json" in rules


def test_entity_store_loads_example_when_missing(tmp_path: Path):
    store = LegalEntityStore(tmp_path)
    cfg = store.load()
    assert cfg.operator.trade_name == "Virtus Core"
    assert cfg.operator.email == "hello@genesis-ai-engine.com"
    assert store.status()["impressum_publishable"] is False


def test_env_overlay_makes_impressum_publishable(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_LEGAL_OPERATOR_NAME", "Ramish Oltiiev")
    monkeypatch.setenv("GENESIS_LEGAL_ADDRESS_STREET", "Musterstraße 1")
    monkeypatch.setenv("GENESIS_LEGAL_ADDRESS_ZIP", "01067")
    monkeypatch.setenv("GENESIS_LEGAL_ADDRESS_CITY", "Dresden")
    monkeypatch.setenv("GENESIS_LEGAL_EMAIL", "hello@genesis-ai-engine.com")
    cfg = apply_env_overlay(LegalEntityConfig())
    assert cfg.is_impressum_publishable() is True
    assert cfg.interview_completed is True


def test_operator_preview_shape(tmp_path: Path):
    store = LegalEntityStore(tmp_path)
    store.save(_complete_entity())
    svc = LegalFoundationService(tmp_path)
    preview = svc.operator_preview()
    assert preview["trade_name"] == "Virtus Core"
    assert preview["full_name"] == "Max Mustermann"
    assert preview["email"] == "hello@example.com"
    assert preview["impressum_publishable"] is True
    assert preview["address_lines"]


def test_entity_store_save_and_reload(tmp_path: Path):
    store = LegalEntityStore(tmp_path)
    entity = _complete_entity()
    store.save(entity)
    loaded = store.load()
    assert loaded.operator.full_name == "Max Mustermann"
    assert store.status()["impressum_publishable"] is True


def test_entity_store_persists_env_overlay_when_publishable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("GENESIS_LEGAL_OPERATOR_NAME", "Ramish Oltiiev")
    monkeypatch.setenv("GENESIS_LEGAL_ADDRESS_STREET", "Teststraße 1")
    monkeypatch.setenv("GENESIS_LEGAL_ADDRESS_ZIP", "01237")
    monkeypatch.setenv("GENESIS_LEGAL_ADDRESS_CITY", "Dresden")
    monkeypatch.setenv("GENESIS_LEGAL_EMAIL", "hello@genesis-ai-engine.com")
    store = LegalEntityStore(tmp_path)
    cfg = store.load()
    assert cfg.is_impressum_publishable() is True
    assert (tmp_path / "legal_entity.json").is_file()
    reloaded = LegalEntityStore(tmp_path)
    monkeypatch.delenv("GENESIS_LEGAL_OPERATOR_NAME", raising=False)
    monkeypatch.delenv("GENESIS_LEGAL_ADDRESS_STREET", raising=False)
    persisted = reloaded.load()
    assert persisted.operator.full_name == "Ramish Oltiiev"


def test_legal_foundation_service_api_shape(tmp_path: Path):
    store = LegalEntityStore(tmp_path)
    store.save(_complete_entity())
    svc = LegalFoundationService(tmp_path)
    status = svc.status()
    assert "impressum_publishable" in status
    trust = svc.trust()
    assert trust["version"] == "legal-trust-v2"
    doc = svc.document("impressum")
    assert doc is not None
    assert doc["publishable"] is True
    assert svc.handoff_one_time()["type"] == "one_time"
