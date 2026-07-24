"""Gmail OAuth + send fallback unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.integration import gmail_mail_service as gmail


def test_authorization_url_contains_offline_consent(monkeypatch):
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid.apps.googleusercontent.com")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "csecret")
    url = gmail.authorization_url(
        redirect_uri="http://127.0.0.1:8000/api/owner/gmail/oauth/callback",
        state="abc",
    )
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "gmail.send" in url
    assert "cid.apps.googleusercontent.com" in url


def test_oauth_state_roundtrip():
    state = gmail.create_oauth_state()
    assert gmail.consume_oauth_state(state) is True
    assert gmail.consume_oauth_state(state) is False


def test_exchange_code_returns_refresh(monkeypatch):
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "sec")
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.content = b"{}"
    mock_res.json.return_value = {
        "access_token": "ya29.a",
        "refresh_token": "1//refresh-xyz",
        "expires_in": 3600,
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_res
    with patch("app.integration.gmail_mail_service.httpx.Client", return_value=mock_client):
        out = gmail.exchange_code(
            code="code123",
            redirect_uri="http://127.0.0.1:8000/api/owner/gmail/oauth/callback",
        )
    assert out["ok"] is True
    assert out["refresh_token"] == "1//refresh-xyz"


def test_send_email_uses_refresh_then_gmail_api(monkeypatch):
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "sec")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "1//rt")
    monkeypatch.setenv("GMAIL_SENDER", "virtuscoreit@gmail.com")

    token_res = MagicMock()
    token_res.status_code = 200
    token_res.content = b"{}"
    token_res.json.return_value = {"access_token": "ya29.send"}

    send_res = MagicMock()
    send_res.status_code = 200
    send_res.content = b"{}"
    send_res.json.return_value = {"id": "msg_1"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.side_effect = [token_res, send_res]

    with patch("app.integration.gmail_mail_service.httpx.Client", return_value=mock_client):
        out = gmail.send_email(
            to="lead@example.com",
            subject="Hello",
            text="Body",
            html="<p>Body</p>",
        )
    assert out["ok"] is True
    assert out["provider"] == "gmail"
    assert out["id"] == "msg_1"
    assert mock_client.post.call_count == 2


def test_receipt_send_falls_back_to_gmail(monkeypatch, tmp_path):
    from app.integration.receipt_email_service import ReceiptEmailService

    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("GENESIS_EMAIL_FROM", "hello@example.com")
    monkeypatch.setenv("GMAIL_CLIENT_ID", "cid")
    monkeypatch.setenv("GMAIL_CLIENT_SECRET", "sec")
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "1//rt")
    monkeypatch.setenv("GMAIL_SENDER", "virtuscoreit@gmail.com")

    resend_res = MagicMock()
    resend_res.status_code = 429
    resend_res.text = "rate limited"

    mock_resend_client = MagicMock()
    mock_resend_client.__enter__.return_value = mock_resend_client
    mock_resend_client.post.return_value = resend_res

    with patch("app.integration.receipt_email_service.httpx.Client", return_value=mock_resend_client):
        with patch(
            "app.integration.gmail_mail_service.send_email",
            return_value={"ok": True, "provider": "gmail", "id": "g1", "from": "virtuscoreit@gmail.com"},
        ) as gsend:
            svc = ReceiptEmailService(tmp_path)
            out = svc._send(  # noqa: SLF001
                to="a@b.com",
                subject="S",
                text="T",
                html="<p>T</p>",
            )
    assert out["ok"] is True
    assert out["provider"] == "gmail"
    assert out.get("fallback_after") == "resend_error:429"
    gsend.assert_called_once()
