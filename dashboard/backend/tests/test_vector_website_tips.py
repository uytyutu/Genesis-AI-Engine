"""Website Admin Tips + progress memory + AI Health."""

from __future__ import annotations

from pathlib import Path

from app.integration.vector.ai_health import build_ai_health
from app.integration.vector.business_setup import build_business_setup
from app.integration.vector.progress import VectorProgressStore
from app.integration.vector.website_tips import scan_website_tips


def test_progress_persists(tmp_path: Path):
    store = VectorProgressStore(tmp_path)
    store.save("store_admin", "ord-1", learning_mode="skip", step_id="products")
    loaded = store.load("store_admin", "ord-1")
    assert loaded["learning_mode"] == "skip"
    assert loaded["step_id"] == "products"


def test_ai_health_honest_coming():
    health = build_ai_health(has_website=True, has_store=False)
    assert health["live_count"] >= 2  # website + vector
    commerce = next(m for m in health["modules"] if m["id"] == "commerce")
    assert commerce["status"] == "coming"
    assert commerce["coming"] == "R3.3"


def test_business_ready_bars():
    biz = build_business_setup(
        has_website=True,
        has_store=True,
        product_count=3,
        branding_done=True,
        primary_store_order_id="s1",
    )
    # Locale-safe: RU owner UI may use «Запуск бизнеса» instead of EN title.
    assert biz["title"] in ("Business Ready", "Запуск бизнеса", "Развитие бизнеса")
    assert any(b["label"] == "Website" and b["pct"] == 100 for b in biz["bars"])
    assert any(b["label"] == "Payments" for b in biz["bars"])


def test_website_tips_golden_demo():
    # Use a golden demo if present
    app = Path(__file__).resolve().parents[1] / "app" / "factory" / "golden_demos"
    law = app / "law"
    if not (law / "meta.json").is_file():
        # skip soft
        return
    out = scan_website_tips(product_dir=law, niche="Law")
    assert out["ok"] is True
    assert out["score"] >= 0
    cats = {t["category"] for t in out["tips"]}
    assert "legal" in cats
    assert "seo" in cats
    assert out["honesty"]
