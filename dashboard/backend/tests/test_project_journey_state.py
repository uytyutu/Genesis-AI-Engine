"""Tests for website journey state — panel source of truth."""

from __future__ import annotations

from pathlib import Path

from app.integration.project_platform.journey_state import build_website_journey_state
from app.integration.project_platform.service import ProjectPlatformService


def test_journey_greenline_brief_not_truncated(tmp_path: Path):
    """Regression — 120-char timeline cuts broke company name + goal detection."""
    memory = tmp_path / "memory"
    memory.mkdir()
    svc = ProjectPlatformService(memory)
    vid = "visitor-trunc"
    svc.bootstrap_from_message(vid, "Хочу создать сайт для своей компании")
    brief = (
        "Компания GreenLine. Мы устанавливаем солнечные панели для частных домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию."
    )
    svc.bootstrap_from_message(vid, brief)
    state = svc.get_for_visitor(vid)
    by_id = {row["id"]: row for row in state["project"]["journey"]["items"]}
    # Extractor may keep the «Компания …» prefix; brand token must remain GreenLine
    assert "GreenLine" in str(by_id["company"]["value"])
    assert by_id["goal"]["status"] == "done"
    assert by_id["design"]["status"] == "active"


def test_journey_company_active_on_site_intent(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    svc = ProjectPlatformService(memory)
    vid = "visitor-journey-start"
    svc.bootstrap_from_message(vid, "Хочу создать сайт для своей компании.")
    state = svc.get_for_visitor(vid)
    by_id = {row["id"]: row for row in state["project"]["journey"]["items"]}
    assert by_id["type"]["status"] == "done"
    assert by_id["company"]["status"] == "active"
    assert not by_id["company"].get("value")
    assert by_id["goal"]["status"] == "pending"


def test_journey_shows_company_name_after_brief(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    svc = ProjectPlatformService(memory)
    vid = "visitor-journey-co"
    svc.bootstrap_from_message(vid, "Хочу создать сайт для своей компании.")
    svc.bootstrap_from_message(
        vid,
        "Компания GreenLine. Мы устанавливаем солнечные панели для домов в Германии. "
        "На сайте человек должен оставить заявку на бесплатную консультацию.",
    )
    state = svc.get_for_visitor(vid)
    journey = state["project"]["journey"]
    by_id = {row["id"]: row for row in journey["items"]}
    assert by_id["company"]["status"] == "done"
    assert by_id["company"]["value"] == "GreenLine"
    assert by_id["goal"]["status"] == "done"
    assert by_id["country"]["status"] == "done"
    assert "Герман" in (by_id["country"].get("value") or "")


def test_journey_tracks_style_and_colors(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    svc = ProjectPlatformService(memory)
    vid = "visitor-journey-style"
    svc.bootstrap_from_message(vid, "Хочу создать сайт для своей компании.")
    svc.bootstrap_from_message(
        vid,
        "Компания GreenLine. Солнечные панели в Германии. Заявка на консультацию.",
    )
    svc.bootstrap_from_message(vid, "Современный минималистичный стиль, светлый и чистый.")
    svc.bootstrap_from_message(vid, "Цвета: зелёный и белый — энергия и природа.")
    state = svc.get_for_visitor(vid)
    by_id = {row["id"]: row for row in state["project"]["journey"]["items"]}
    assert by_id["design"]["status"] == "done"
    assert by_id["design"]["value"] == "Light Minimal"
    assert by_id["colors"]["status"] == "done"
    assert "зелён" in (by_id["colors"].get("value") or "").lower()


def test_enrich_attaches_project_state(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    svc = ProjectPlatformService(memory)
    vid = "visitor-enrich"
    svc.bootstrap_from_message(vid, "Хочу создать сайт для своей компании.")
    out = svc.enrich_with_project_state({"answer": "ok", "context": {}}, vid)
    assert out["context"]["project_state"]["has_project"] is True
    assert out["context"]["project_state"]["project"]["journey"]["items"]
