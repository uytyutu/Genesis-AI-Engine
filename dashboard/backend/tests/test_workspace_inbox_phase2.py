"""Phase 2 Unified Inbox — tenant-scoped Telegram + Website Chat threads."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration import workspace_ai_bots as bots
from app.integration import workspace_inbox_service as inbox
from app.integration.ai_employee_brain import SessionState, save_session


def _seed_bot(mem: Path, customer: str, name: str = "Inbox Bot") -> str:
    bots.set_entitlements(mem, customer, "bot_business")
    created = bots.create_bot(
        mem,
        customer,
        display_name=name,
        bot_config={"channels": ["telegram", "website_chat"], "ai_instructions": "Help."},
        channels=["telegram", "website_chat"],
    )
    return created["bot"]["bot_id"]


def _write_session(
    mem: Path,
    customer: str,
    bot_id: str,
    session_key: str,
    turns: list[dict[str, str]],
    *,
    meta: dict | None = None,
) -> None:
    state = SessionState(turns=turns)
    save_session(mem, customer, bot_id, session_key, state)
    from app.integration.ai_employee_brain import _session_path

    path = _session_path(mem, customer, bot_id, session_key)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["updated_at"] = "2026-08-13T12:00:00Z"
    if meta:
        raw["inbox_meta"] = meta
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def test_inbox_list_and_channel_filter(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-inbox-a"
    bot_id = _seed_bot(mem, customer)
    _write_session(
        mem,
        customer,
        bot_id,
        "tg:9001",
        [{"role": "user", "content": "Was kostet eine Website?"}],
        meta={"sender_name": "Max Müller"},
    )
    _write_session(
        mem,
        customer,
        bot_id,
        "wch:visitor-1",
        [{"role": "user", "content": "Ich habe eine Anfrage"}],
        meta={"sender_name": "Anna"},
    )
    _write_session(
        mem,
        customer,
        bot_id,
        "cabinet:cust-inbox-a:x",
        [{"role": "user", "content": "cabinet noise"}],
    )

    all_threads = inbox.list_threads(mem, customer)
    assert all_threads["ok"] is True
    assert all_threads["total"] == 2
    channels = {t["channel"] for t in all_threads["threads"]}
    assert channels == {"telegram", "webchat"}

    tg = inbox.list_threads(mem, customer, channel="telegram")
    assert tg["total"] == 1
    assert tg["threads"][0]["customer_name"] == "Max Müller"
    assert "Website" in tg["threads"][0]["preview"]

    wch = inbox.list_threads(mem, customer, channel="website")
    assert wch["total"] == 1
    assert wch["threads"][0]["channel"] == "webchat"


def test_inbox_search_and_unread(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-inbox-search"
    bot_id = _seed_bot(mem, customer)
    _write_session(
        mem,
        customer,
        bot_id,
        "tg:42",
        [{"role": "user", "content": "Brauche Termin nächste Woche"}],
        meta={"sender_name": "Thomas"},
    )
    found = inbox.list_threads(mem, customer, q="Termin")
    assert found["total"] == 1
    tid = found["threads"][0]["thread_id"]
    assert found["threads"][0]["unread_count"] == 1

    marked = inbox.mark_read(mem, customer, tid)
    assert marked["ok"] is True
    again = inbox.list_threads(mem, customer, unread_only=True)
    assert again["total"] == 0


def test_inbox_conversation_and_workspace_isolation(tmp_path: Path):
    mem = tmp_path / "memory"
    a = "cust-a"
    b = "cust-b"
    bot_a = _seed_bot(mem, a, "Bot A")
    bot_b = _seed_bot(mem, b, "Bot B")
    _write_session(
        mem,
        a,
        bot_a,
        "tg:1",
        [
            {"role": "user", "content": "Hallo A"},
            {"role": "assistant", "content": "Willkommen"},
        ],
        meta={"sender_name": "A User"},
    )
    _write_session(
        mem,
        b,
        bot_b,
        "tg:2",
        [{"role": "user", "content": "Hallo B"}],
        meta={"sender_name": "B User"},
    )

    listed_a = inbox.list_threads(mem, a)
    assert listed_a["total"] == 1
    tid_a = listed_a["threads"][0]["thread_id"]
    detail = inbox.get_thread(mem, a, tid_a)
    assert detail["ok"] is True
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["direction"] == "INBOUND"
    assert detail["messages"][1]["direction"] == "OUTBOUND"

    tid_b = inbox.list_threads(mem, b)["threads"][0]["thread_id"]
    assert inbox.get_thread(mem, a, tid_b)["reason"] == "forbidden"
    assert inbox.send_reply(mem, a, tid_b, "hack")["reason"] == "forbidden"


def test_inbox_send_via_telegram_provider(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    customer = "cust-send"
    bot_id = _seed_bot(mem, customer)
    _write_session(
        mem,
        customer,
        bot_id,
        "tg:777",
        [{"role": "user", "content": "Hi"}],
        meta={"sender_name": "Max"},
    )
    # credentials for TelegramProvider.health/send
    cred_dir = mem / "customer_identity" / customer / "channel_credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    secret = {
        "connection_id": "tg-1",
        "channel": "telegram",
        "bot_id": bot_id,
        "status": "online",
        "token": "123:TOKEN",
    }
    (cred_dir / "tg-1.json").write_text(json.dumps(secret), encoding="utf-8")
    (cred_dir / "index.json").write_text(
        json.dumps(
            {
                "connections": [
                    {
                        "connection_id": "tg-1",
                        "channel": "telegram",
                        "bot_id": bot_id,
                        "status": "online",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    sent: list[tuple] = []

    def _fake_send(token, chat_id, text):  # noqa: ANN001
        sent.append((token, chat_id, text))
        return {"ok": True, "result": {"message_id": 9}}

    import app.integration.workspace_bot_runtime as rt

    monkeypatch.setattr(rt, "send_telegram_message", _fake_send)

    tid = inbox.encode_thread_id("telegram", bot_id, "777")
    result = inbox.send_reply(mem, customer, tid, "Unser Angebot folgt.")
    assert result["ok"] is True
    assert sent and sent[0][2] == "Unser Angebot folgt."
    detail = inbox.get_thread(mem, customer, tid)
    assert any(m["text"] == "Unser Angebot folgt." and m["direction"] == "OUTBOUND" for m in detail["messages"])


def test_website_chat_send_unsupported(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-wch"
    bot_id = _seed_bot(mem, customer)
    _write_session(
        mem,
        customer,
        bot_id,
        "wch:abc",
        [{"role": "user", "content": "Hello web"}],
    )
    tid = inbox.encode_thread_id("webchat", bot_id, "abc")
    result = inbox.send_reply(mem, customer, tid, "Reply")
    assert result["ok"] is False
    assert result["reason"] == "CHANNEL_SEND_UNSUPPORTED"


def test_future_channel_filter_empty_not_error(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-future"
    _seed_bot(mem, customer)
    out = inbox.list_threads(mem, customer, channel="whatsapp")
    assert out["ok"] is True
    assert out["threads"] == []
