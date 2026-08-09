"""Website Control v1 — content overlay + ownership."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.factory.media_history import (
    assert_unique_visual,
    default_fingerprint,
    record_fingerprint,
)
from app.integration.website_admin.ai_edit import (
    apply_content_intent,
    parse_ai_edit_prompt,
)
from app.integration.website_admin.apply import apply_website_overlay_to_product_dir
from app.integration.website_admin.content_service import WebsiteContentService
from app.integration.website_admin.design_service import WebsiteDesignService
from app.integration.website_admin.ownership import assert_website_order_access
from app.integration.website_admin.publish_safety import evaluate_publish_safety


def test_ownership_forbidden_other_customer() -> None:
    order = {
        "id": "ord-1",
        "customer_id": "cust-owner",
        "email": "owner@example.com",
        "product_kind": "website",
        "package_id": "business",
    }
    with pytest.raises(ValueError, match="forbidden"):
        assert_website_order_access(
            order, customer_id="cust-other", email="other@example.com"
        )


def test_ownership_allows_owner_customer_id() -> None:
    order = {
        "id": "ord-1",
        "customer_id": "cust-owner",
        "email": "owner@example.com",
        "product_kind": "website",
        "package_id": "business",
    }
    out = assert_website_order_access(
        order, customer_id="cust-owner", email="other@example.com"
    )
    assert out["id"] == "ord-1"


def test_ownership_allows_owner_email() -> None:
    order = {
        "id": "ord-1",
        "customer_id": "cust-owner",
        "email": "owner@example.com",
        "product_kind": "website",
        "package_id": "premium",
    }
    out = assert_website_order_access(
        order, customer_id="cust-other", email="owner@example.com"
    )
    assert out is order


def test_ownership_rejects_shop_order() -> None:
    order = {
        "id": "ord-shop",
        "customer_id": "cust-1",
        "email": "a@b.c",
        "product_kind": "shop",
        "package_id": "ecommerce_shop",
    }
    with pytest.raises(ValueError, match="not_a_website_order"):
        assert_website_order_access(order, customer_id="cust-1", email="a@b.c")


def test_ownership_order_not_found() -> None:
    with pytest.raises(ValueError, match="order_not_found"):
        assert_website_order_access(None, customer_id="x", email="y")


def test_content_persists(tmp_path: Path) -> None:
    svc = WebsiteContentService(tmp_path)
    order_id = "ord-web-1"
    out = svc.update_content(
        order_id,
        {
            "hero": {
                "headline": "Studio Test",
                "subheadline": "München",
                "cta_label": "Termin",
            }
        },
        seed_meta={"business_name": "Studio Test"},
    )
    assert out["ok"] is True
    assert out["content"]["hero"]["headline"] == "Studio Test"
    again = svc.get_content(order_id)
    assert again["content"]["hero"]["headline"] == "Studio Test"
    path = tmp_path / "website_admin" / "ord-web-1" / "content.json"
    assert path.is_file()


def test_about_and_prices_persist(tmp_path: Path) -> None:
    svc = WebsiteContentService(tmp_path)
    out = svc.update_content(
        "ord-about",
        {
            "about": {"title": "Wir", "body": "Luxury salon"},
            "prices": {
                "enabled": True,
                "title": "Preise",
                "intro": "Klar",
                "items": [{"id": "p1", "label": "A", "price": "50 €", "note": ""}],
            },
        },
        seed_meta={"business_name": "Salon"},
    )
    assert out["content"]["about"]["body"] == "Luxury salon"
    assert out["content"]["prices"]["enabled"] is True


def test_content_undo(tmp_path: Path) -> None:
    svc = WebsiteContentService(tmp_path)
    oid = "ord-undo"
    svc.update_content(
        oid, {"hero": {"headline": "V1"}}, seed_meta={"business_name": "X"}
    )
    svc.update_content(oid, {"hero": {"headline": "V2"}})
    assert svc.get_content(oid)["content"]["hero"]["headline"] == "V2"
    und = svc.undo(oid)
    assert und["content"]["hero"]["headline"] == "V1"
    assert und["content"]["can_redo"] is True


def test_design_undo(tmp_path: Path) -> None:
    svc = WebsiteDesignService(tmp_path)
    oid = "ord-d-undo"
    svc.update_design(oid, {"colors": {"primary": "#111111"}}, business_name="A")
    svc.update_design(oid, {"colors": {"primary": "#222222"}}, business_name="A")
    assert svc.get_design(oid)["design"]["colors"]["primary"] == "#222222"
    und = svc.undo(oid)
    assert und["design"]["colors"]["primary"] == "#111111"


def test_design_persists(tmp_path: Path) -> None:
    svc = WebsiteDesignService(tmp_path)
    order_id = "ord-web-2"
    out = svc.update_design(
        order_id,
        {"colors": {"primary": "#112233", "button": "#112233"}},
        business_name="Demo",
    )
    assert out["design"]["colors"]["primary"] == "#112233"
    assert (tmp_path / "website_admin" / "ord-web-2" / "design.json").is_file()


def test_apply_injects_overlay_markers(tmp_path: Path) -> None:
    memory = tmp_path / "memory"
    product = tmp_path / "product"
    product.mkdir()
    (product / "assets").mkdir()
    (product / "index.html").write_text(
        "<!doctype html><html><head><title>t</title></head>"
        "<body><h1>Old</h1></body></html>",
        encoding="utf-8",
    )
    (product / "meta.json").write_text(
        json.dumps({"business_name": "Demo Co"}), encoding="utf-8"
    )
    content = WebsiteContentService(memory)
    content.update_content(
        "ord-a",
        {"hero": {"headline": "New Headline", "subheadline": "Sub", "cta_label": "Go"}},
        seed_meta={"business_name": "Demo Co"},
    )
    design = WebsiteDesignService(memory)
    design.update_design(
        "ord-a", {"colors": {"primary": "#00aa88"}}, business_name="Demo Co"
    )

    ok = apply_website_overlay_to_product_dir(
        memory, "ord-a", product, business_name="Demo Co"
    )
    assert ok is True
    html = (product / "index.html").read_text(encoding="utf-8")
    assert "virtus-owner.css" in html
    assert "virtus-owner.js" in html
    assert (product / "assets" / "virtus-owner.css").is_file()
    assert (product / "assets" / "virtus-owner.js").is_file()
    css = (product / "assets" / "virtus-owner.css").read_text(encoding="utf-8")
    assert "#00aa88" in css or "--virtus-primary" in css


def test_publish_safety_blocks_empty_hero() -> None:
    result = evaluate_publish_safety(
        {
            "hero": {"headline": ""},
            "services": [],
            "contacts": {},
            "seo": {},
        }
    )
    assert result["ok"] is False
    ids = {b["id"] for b in result["blockers"]}
    assert "empty_hero_headline" in ids
    assert "no_services" in ids
    assert "no_contact" in ids


def test_publish_safety_pass() -> None:
    result = evaluate_publish_safety(
        {
            "hero": {"headline": "Salon"},
            "services": [{"title": "A"}],
            "contacts": {"phone": "+49 89 1"},
            "seo": {"title": "Salon"},
        }
    )
    assert result["ok"] is True


def test_ai_edit_add_service() -> None:
    parsed = parse_ai_edit_prompt("Добавь услугу: Massage 60 Min")
    assert "_append_service" in (parsed.get("content_patch") or {})
    current = {"services": [{"id": "1", "title": "A", "description": "", "price": ""}]}
    patch = apply_content_intent(current, parsed["content_patch"])
    assert len(patch["services"]) == 2
    assert "Massage" in patch["services"][-1]["title"]


def test_ai_edit_laser_service() -> None:
    parsed = parse_ai_edit_prompt('Добавь услугу "Laser Hair Removal"')
    svc = (parsed.get("content_patch") or {}).get("_append_service") or {}
    assert "Laser" in str(svc.get("title") or "")


def test_ai_edit_premium_and_prices() -> None:
    prem = parse_ai_edit_prompt("Замени тон сайта на более премиальный")
    assert "hero" in (prem.get("content_patch") or {})
    assert "colors" in (prem.get("design_patch") or {})
    prices = parse_ai_edit_prompt("Добавь раздел Цены")
    assert (prices.get("content_patch") or {}).get("prices", {}).get("enabled") is True


def test_ai_edit_hero_shorter() -> None:
    parsed = parse_ai_edit_prompt("Сделай Hero короче")
    assert "hero" in (parsed.get("content_patch") or {})


def test_ai_edit_darker_theme() -> None:
    parsed = parse_ai_edit_prompt("Сделай дизайн темнее")
    assert "colors" in (parsed.get("design_patch") or {})


def test_ai_edit_unsupported() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        parse_ai_edit_prompt("нарисуй мне кота в космосе")


def test_media_history_rejects_near_duplicate(tmp_path: Path) -> None:
    fp = default_fingerprint(
        project_id="p1",
        niche="nail",
        role="hero",
        composition="wide reception marble",
        palette=["#fff", "#gold"],
        scene_type="interior",
        interior="white marble gold",
        style="bright young",
        angle="front",
    )
    record_fingerprint(tmp_path, fp)
    twin = default_fingerprint(
        project_id="p2",
        niche="nail",
        role="hero",
        composition="wide reception marble",
        palette=["#fff", "#gold"],
        scene_type="interior",
        interior="white marble gold",
        style="bright young",
        angle="front",
    )
    gate = assert_unique_visual(tmp_path, twin)
    assert gate["ok"] is False
    assert gate["reject_reason"] == "visual_identity_collision"
