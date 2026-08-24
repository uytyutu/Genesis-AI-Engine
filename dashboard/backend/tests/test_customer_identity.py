"""M2 Universal Identity — register, login, welcome."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.integration.customer_identity.service import CustomerIdentityService


@pytest.fixture
def svc(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "test-client-secret-m2")
    memory = tmp_path / "memory"
    memory.mkdir()
    return CustomerIdentityService(memory)


def test_register_otp_flow(svc: CustomerIdentityService, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_CLIENT_OTP_DEV", "1")
    start = svc.start_registration(
        name="Anna Kraft",
        email="anna.otp@example.com",
        password="securepass1",
        locale="en",
    )
    assert start["ok"] is True
    assert start["next"] == "confirm_code"
    assert start.get("dev_code")
    out = svc.confirm_registration(
        email="anna.otp@example.com", code=str(start["dev_code"])
    )
    assert out["token"]
    assert out["email"] == "anna.otp@example.com"
    me = svc.me(svc._store.find_customer_by_email("anna.otp@example.com") or "")
    assert me["email_verified"] is True


def test_register_otp_rejects_bad_code(
    svc: CustomerIdentityService, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("GENESIS_CLIENT_OTP_DEV", "1")
    svc.start_registration(
        name="Bad Code",
        email="badcode@example.com",
        password="securepass1",
    )
    with pytest.raises(HTTPException) as exc:
        svc.confirm_registration(email="badcode@example.com", code="000000")
    assert exc.value.status_code == 400
    assert exc.value.detail == "invalid_code"


def test_register_creates_company(svc: CustomerIdentityService):
    out = svc.register(
        name="Анна Крафт",
        email="anna@example.com",
        password="securepass1",
        locale="ru",
    )
    assert out["headline"] == "Ваша цифровая компания готова."
    assert out["welcome"]["phase"] == "greeting"
    assert "Vector" in (out["welcome"]["message"] or "")
    assert out["company"]["name"] == "Mein Unternehmen"
    assert out["platform_visitor_id"].startswith("vc-")
    assert out["company"]["project"]["project"]["title"] == "Mein Unternehmen"


def test_register_duplicate_email(svc: CustomerIdentityService):
    svc.register(name="Test", email="dup@example.com", password="securepass1")
    with pytest.raises(HTTPException) as exc:
        svc.register(name="Test2", email="dup@example.com", password="securepass1")
    assert exc.value.status_code == 409


def test_login_and_me(svc: CustomerIdentityService):
    svc.register(name="Иван", email="ivan@example.com", password="securepass1")
    login = svc.login(email="ivan@example.com", password="securepass1")
    assert login["token"]
    cid = svc._store.find_customer_by_email("ivan@example.com")
    me = svc.me(cid or "")
    assert me["name"] == "Иван"
    assert me["email"] == "ivan@example.com"


def test_welcome_wizard_flow(svc: CustomerIdentityService):
    svc.register(name="Мария", email="maria@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("maria@example.com")
    assert cid

    state = svc.advance_welcome(cid)
    assert state["phase"] == "wizard"
    assert state["wizard_question"]

    for text in ("У меня кафе", "Хочу сайт", "Сразу проект"):
        if state["phase"] != "wizard":
            break
        state = svc.answer_welcome(cid, answer=text)

    assert state["phase"] in ("personalized", "complete")
    if state["phase"] == "personalized":
        assert len(state["quick_actions"]) >= 1


def test_welcome_skip(svc: CustomerIdentityService):
    svc.register(name="Пётр", email="petr@example.com", password="securepass1")
    cid = svc._store.find_customer_by_email("petr@example.com")
    assert cid
    svc.advance_welcome(cid)
    state = svc.answer_welcome(cid, answer="", skip=True)
    assert state["phase"] == "personalized"


def test_merge_visitor(svc: CustomerIdentityService):
    svc.register(
        name="Олег",
        email="oleg@example.com",
        password="securepass1",
        prior_visitor_id="anon-visitor-12345678",
    )
    cid = svc._store.find_customer_by_email("oleg@example.com")
    assert cid
    merged = svc.merge_visitor(cid, visitor_id="anon-visitor-12345678")
    assert merged["ok"] == "true"
