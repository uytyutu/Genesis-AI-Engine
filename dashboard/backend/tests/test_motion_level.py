"""motion_level brief + Classic CSS-motion kit (deterministic, no LLM)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.factory.css_motion import write_motion_assets
from app.factory.engines.base import EngineError, EngineRequest
from app.factory.engines.classic_engine import generate as classic_generate
from app.factory.factory_service import FactoryService
from app.factory.motion_brief import (
    detect_motion_intent,
    empty_vector_brief,
    gate_motion_level,
    merge_motion_into_brief,
    normalize_motion_level,
)


BRIEFS_10 = [
    {"niche": "dental", "market": "DE", "motion_level": "none", "desc": "Zahnarztpraxis Berlin Prophylaxe"},
    {"niche": "dental", "market": "DE", "motion_level": "css", "desc": "Zahnarztpraxis Berlin Prophylaxe"},
    {"niche": "law", "market": "AT", "motion_level": "css", "desc": "Rechtsanwalt Wien Familienrecht"},
    {"niche": "auto", "market": "CH", "motion_level": "none", "desc": "Autowerkstatt Zurich Service"},
    {"niche": "clinic", "market": "US", "motion_level": "css", "desc": "Dental clinic Austin Texas"},
    {"niche": "cafe", "market": "FR", "motion_level": "css", "desc": "Cafe Paris brunch terrasse"},
    {"niche": "salon", "market": "PL", "motion_level": "none", "desc": "Salon fryzjerski Warszawa"},
    {"niche": "it", "market": "UA", "motion_level": "css", "desc": "IT studio Kyiv websites"},
    {"niche": "law", "market": "GB", "motion_level": "css", "desc": "Solicitor London family law"},
    {"niche": "dental", "market": "DE", "motion_level": "3d_premium", "desc": "Zahnarzt 3D Tour Praxis"},
]


def test_normalize_and_gate():
    assert normalize_motion_level("CSS") == "css"
    assert normalize_motion_level("3d") == "3d_premium"
    assert gate_motion_level("css")["ok"] is True
    assert gate_motion_level("3d_premium")["ok"] is False
    assert gate_motion_level("3d_premium")["code"] == "WAITLIST_REQUIRED"


def test_detect_motion_intent():
    assert detect_motion_intent("хочу живой сайт с анимацией") == "css"
    assert detect_motion_intent("нужен настоящий 3D webgl") == "3d_premium"
    assert detect_motion_intent("сайт для стоматологии в Кельне") is None


def test_brief_merge_3d_waitlist():
    brief = merge_motion_into_brief(empty_vector_brief(), motion_level="3d_premium")
    assert brief["status"] == "WAITLIST_REQUIRED"
    assert brief["engine_route"] == "reject_3d"


def test_classic_css_motion_html_links_assets():
    result = classic_generate(
        EngineRequest(
            description="Zahnarztpraxis Mueller in Koeln. Prophylaxe.",
            business_name="Praxis Mueller",
            market_code="DE",
            motion_level="css",
        )
    )
    assert "assets/motion_kit.css" in result.html
    assert "assets/reveal.js" in result.html
    assert 'class="hero-text"' in result.html or "hero-text" in result.html
    assert "reveal" in result.html
    assert result.meta.get("motion_level") == "css"


def test_classic_none_has_no_motion_kit():
    result = classic_generate(
        EngineRequest(
            description="Zahnarztpraxis Mueller in Koeln.",
            business_name="Praxis Mueller",
            motion_level="none",
        )
    )
    assert "motion_kit.css" not in result.html
    assert result.meta.get("motion_level") == "none"


def test_classic_rejects_3d_premium():
    with pytest.raises(EngineError) as ei:
        classic_generate(
            EngineRequest(
                description="Dental with WebGL",
                motion_level="3d_premium",
            )
        )
    assert ei.value.code == "WAITLIST_REQUIRED"


def test_factory_css_writes_assets_and_zip(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Test in Koeln.",
        market_code="DE",
        motion_level="css",
        client_legal={
            "owner_name": "Dr. Test",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "test@example.com",
        },
    )
    pid = product["product_id"]
    root = tmp_path / "sandbox" / pid
    assert (root / "assets" / "motion_kit.css").is_file()
    assert (root / "assets" / "reveal.js").is_file()
    html = (root / "index.html").read_text(encoding="utf-8")
    assert "motion_kit.css" in html
    zbytes, _name = factory.build_client_delivery_zip(pid)
    with zipfile.ZipFile(io := __import__("io").BytesIO(zbytes)) as zf:
        names = set(zf.namelist())
    assert "assets/motion_kit.css" in names
    assert "assets/reveal.js" in names


def test_factory_3d_raises(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    with pytest.raises(ValueError, match="WAITLIST_REQUIRED"):
        factory.build_landing("Clinic 3D", motion_level="3d_premium", market_code="DE")


def test_ten_briefs_smoke(tmp_path: Path):
    """10 briefs: none/css build; 3d_premium waitlisted."""
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    outcomes = []
    for i, brief in enumerate(BRIEFS_10):
        ml = brief["motion_level"]
        if ml == "3d_premium":
            with pytest.raises(ValueError, match="WAITLIST_REQUIRED"):
                factory.build_landing(brief["desc"], market_code=brief["market"], motion_level=ml)
            outcomes.append({"i": i, "status": "WAITLIST_REQUIRED", **brief})
            continue
        product = factory.build_landing(
            brief["desc"],
            market_code=brief["market"],
            motion_level=ml,
            client_legal={
                "owner_name": "Owner",
                "street": "Street 1",
                "zip": "10000",
                "city": "City",
                "email": "o@example.com",
            },
        )
        root = tmp_path / "sandbox" / product["product_id"]
        html = (root / "index.html").read_text(encoding="utf-8")
        if ml == "css":
            assert "motion_kit.css" in html
            assert (root / "assets" / "motion_kit.css").is_file()
        else:
            assert "motion_kit.css" not in html
        outcomes.append({"i": i, "status": "ok", "product_id": product["product_id"], **brief})
    assert len(outcomes) == 10
    assert sum(1 for o in outcomes if o["status"] == "WAITLIST_REQUIRED") == 1
    assert sum(1 for o in outcomes if o["motion_level"] == "css" and o["status"] == "ok") == 6


def test_write_motion_assets_idempotent(tmp_path: Path):
    a = write_motion_assets(tmp_path)
    b = write_motion_assets(tmp_path)
    assert a == b == ["assets/motion_kit.css", "assets/reveal.js"]
