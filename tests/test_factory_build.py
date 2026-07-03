"""Factory v0.1 build and improve tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.factory.analyzer import analyze
from app.factory.validator import validate_landing
from app.integration.context import get_integration, reset_integration
from app.main import app


def test_analyzer_dental():
    result = analyze("Мне нужен сайт для стоматологии")
    assert result.niche == "dental"
    assert "стоматолог" in result.business_name.lower() or "Стоматолог" in result.business_name


def test_factory_build_landing(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.post(
        "/api/factory/intent",
        json={"product_type": "landing-page", "description": "Сайт для автосервиса Premium"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"]
    assert data["quality_percent"] >= 95
    product_id = data["product_id"]
    assert any(c["id"] == "owner_review" and c.get("pending") for c in data["product"]["checks"])

    sandbox_html = tmp_path / "sandbox" / product_id / "index.html"
    assert sandbox_html.exists()
    assert "Premium" in sandbox_html.read_text(encoding="utf-8") or "автосервис" in sandbox_html.read_text(encoding="utf-8").lower()

    preview = client.get(f"/api/factory/products/{product_id}/preview")
    assert preview.status_code == 200
    assert "<!DOCTYPE html>" in preview.text

    improve = client.post(
        f"/api/factory/products/{product_id}/improve",
        json={"feedback": "Добавь больше синего и калькулятор"},
    )
    assert improve.status_code == 200
    assert improve.json()["revision"] == 1
    assert not improve.json()["owner_approved"]

    approve = client.post(f"/api/factory/products/{product_id}/approve")
    assert approve.status_code == 200
    assert approve.json()["owner_approved"] is True
    owner_check = next(c for c in approve.json()["checks"] if c["id"] == "owner_review")
    assert owner_check["ok"] is True

    publish = client.post(f"/api/factory/products/{product_id}/publish")
    assert publish.status_code == 200
    assert publish.json()["published"] is True
    assert (tmp_path / "published" / product_id / "index.html").exists()

    export = client.get(f"/api/factory/products/{product_id}/export")
    assert export.status_code == 200
    assert export.headers["content-type"] == "application/zip"
    assert "attachment" in export.headers.get("content-disposition", "")
    assert len(export.content) > 100

    delivered = client.post(f"/api/factory/products/{product_id}/delivered")
    assert delivered.status_code == 200
    body = delivered.json()
    assert body["delivered_to_client"] is True
    assert body["status_label"] == "Передано клиенту"
    assert any(c["id"] == "delivered" and c["done"] for c in body["handoff_checklist"])
    assert "Здравствуйте" in body["client_message"]

    milestones = json.loads((memory / "owner_milestones.json").read_text(encoding="utf-8"))
    assert milestones.get("delivered_to_client") is True

    html_after = (tmp_path / "sandbox" / product_id / "index.html").read_text(encoding="utf-8")
    assert "calculator" in html_after.lower() or "Калькулятор" in html_after

    reset_integration()


def test_surgical_improve_testimonials(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.post(
        "/api/factory/intent",
        json={"product_type": "landing-page", "description": "Сайт стоматологии"},
    )
    product_id = res.json()["product_id"]
    html_before = (tmp_path / "sandbox" / product_id / "index.html").read_text(encoding="utf-8")
    assert 'id="testimonials"' not in html_before

    improve = client.post(
        f"/api/factory/products/{product_id}/improve",
        json={"feedback": "Добавь блок с отзывами клиентов"},
    )
    assert improve.status_code == 200
    html_after = (tmp_path / "sandbox" / product_id / "index.html").read_text(encoding="utf-8")
    assert 'id="testimonials"' in html_after
    assert "Отзывы" in html_after

    reset_integration()


def test_mission_control_shows_production(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    client.post(
        "/api/factory/intent",
        json={"product_type": "landing-page", "description": "Лендинг стоматологии"},
    )
    mc = client.get("/api/owner/mission-control").json()
    assert mc["production_department"]["status_label"] == "Completed"
    assert len(mc["production_department"]["checks"]) >= 4

    reset_integration()
