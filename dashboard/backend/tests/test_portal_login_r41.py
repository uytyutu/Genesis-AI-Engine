"""R4.1 — HTTP Login Endpoint (transport → Authentication Domain)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.authentication_facade import (
    ENGINE_ID as FACADE_ENGINE,
    InMemoryAuthenticationDirectory,
)
from app.portal.password_credential import (
    complete_account_activation,
    create_primary_password,
)
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import (
    ENGINE_ID as ROUTER_ENGINE,
    clear_authentication_facade,
    portal_login_router,
)


def _ready_directory(email: str = "owner@ex.de", secret: str = "opaque-secret-1"):
    account = new_account(email=email, display_name="Owner")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated,
        password_hash=secret,
        activation_token=used,
    )
    return InMemoryAuthenticationDirectory(
        accounts_by_email={ready.email: ready},
        credentials_by_account={ready.account_id: cred},
    ), secret


def _client(directory) -> TestClient:
    clear_authentication_facade()
    app = FastAPI()
    assert register_portal_login(app, directory=directory) is True
    return TestClient(app)


def test_engine_ids():
    assert ROUTER_ENGINE == "portal_login_router_v1"
    assert FACADE_ENGINE == "authentication_facade_v1"


def test_login_success_200():
    directory, secret = _ready_directory()
    http = _client(directory)
    try:
        r = http.post("/portal/login", json={"email": "owner@ex.de", "password": secret})
        assert r.status_code == 200
        assert r.json() == {"authenticated": True}
        assert "reason" not in r.json()
        assert "failure" not in r.json()
        # R4.2: successful login sets HttpOnly session cookie
        assert "set-cookie" in {k.lower() for k in r.headers.keys()}
        assert "httponly" in r.headers.get("set-cookie", "").lower()
    finally:
        clear_authentication_facade()


def test_login_failure_hides_reason():
    directory, secret = _ready_directory()
    http = _client(directory)
    try:
        r = http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": "wrong"},
        )
        assert r.status_code == 200
        assert r.json() == {"authenticated": False}
        assert "reason" not in r.json()
        assert "mismatch" not in r.text.lower()
    finally:
        clear_authentication_facade()


def test_unknown_email_same_shape():
    directory, _ = _ready_directory()
    http = _client(directory)
    try:
        r = http.post(
            "/portal/login",
            json={"email": "nobody@ex.de", "password": "x"},
        )
        assert r.status_code == 200
        assert r.json() == {"authenticated": False}
    finally:
        clear_authentication_facade()


def test_invalid_body_400():
    directory, _ = _ready_directory()
    http = _client(directory)
    try:
        assert http.post("/portal/login", json={}).status_code == 400
        assert http.post("/portal/login", json={"email": "a@b.c"}).status_code == 400
        assert http.post("/portal/login", content=b"not-json").status_code == 400
    finally:
        clear_authentication_facade()


def test_no_jwt_in_login_modules():
    import ast

    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for rel in (
        "authentication_facade.py",
        "portal_login_router.py",
        "portal_login_registration.py",
        "login_api_contract.py",
    ):
        tree = ast.parse((portal / rel).read_text(encoding="utf-8"))
        banned = {"jwt", "jose", "itsdangerous"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            for name in names:
                assert name not in banned, f"{rel} imports {name}"
    # Auth facade still must not set cookies itself
    facade_src = (portal / "authentication_facade.py").read_text(encoding="utf-8")
    assert "set_cookie" not in facade_src


def test_main_registers_login():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_login(app)" in text


def test_router_only_post_login():
    paths = [
        getattr(route, "path", "")
        for route in portal_login_router.routes
        if hasattr(route, "methods")
    ]
    assert any(p.endswith("/login") for p in paths)
    for route in portal_login_router.routes:
        if hasattr(route, "methods") and str(getattr(route, "path", "")).endswith(
            "/login"
        ):
            assert route.methods == {"POST"}
