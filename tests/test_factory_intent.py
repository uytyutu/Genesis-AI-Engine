"""Factory intent API — product UI before full Factory."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_factory_intent_landing(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.post(
        "/api/factory/intent",
        json={"product_type": "landing-page", "description": "Сайт стоматологии"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["intent_id"]

    intents = (memory / "factory_intents.jsonl").read_text(encoding="utf-8")
    assert "стоматологии" in intents

    reset_integration()


def test_factory_intent_rejects_unknown_type(tmp_path: Path):
    reset_integration()
    get_integration(tmp_path / "memory")

    client = TestClient(app)
    res = client.post(
        "/api/factory/intent",
        json={"product_type": "telegram-bot", "description": "Бот доставки"},
    )
    assert res.status_code == 400

    reset_integration()


def test_factory_intent_wizard_fields(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.post(
        "/api/factory/intent",
        json={
            "product_type": "landing-page",
            "description": "Сайт автосервиса",
            "audience": "Владельцы авто",
            "goal": "Заявки на ремонт",
            "price_eur": 99,
            "deadline": "Июль",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"]

    intents = (memory / "factory_intents.jsonl").read_text(encoding="utf-8")
    assert "Владельцы авто" in intents
    assert "Заявки на ремонт" in intents

    reset_integration()
