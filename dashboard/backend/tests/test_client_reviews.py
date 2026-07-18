"""Client reviews after Delivered — token gate, pending, CEO publish."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.client_review_service import ClientReviewService, screen_review_text
from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def submit(self, _intent):
        return {"product_id": "prod-rev-1"}


def _sales_reviews(tmp_path: Path) -> tuple[SalesOrderService, ClientReviewService]:
    sales = SalesOrderService(tmp_path, _Factory())
    reviews = ClientReviewService(tmp_path, sales)
    return sales, reviews


def _paid_delivered(sales: SalesOrderService) -> dict:
    created = sales.create_order(
        {
            "business_name": "Autohaus Müller",
            "description": "KFZ Dresden",
            "email": "owner@autohaus.test",
            "package_id": "basic",
            "city": "Dresden",
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    assert order is not None
    order["status"] = "in_production"
    order["product_id"] = "prod-rev-1"
    order["paid_at"] = "2026-01-01T00:00:00+00:00"
    sales._save_order(order)
    return sales.mark_order_delivered(order_id)


def test_screen_flags_url_and_profanity():
    flags = screen_review_text("Besuchen Sie https://spam.example.com bitte jetzt")
    assert "contains_url" in flags
    flags2 = screen_review_text("Das war einfach nur Scheiße und Betrug")
    assert "profanity" in flags2


def test_ineligible_before_delivered(tmp_path: Path):
    sales, reviews = _sales_reviews(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Cafe Test",
            "description": "Test",
            "email": "a@b.de",
            "package_id": "basic",
            "city": "Berlin",
        }
    )
    with pytest.raises(ValueError, match="not_eligible"):
        reviews.submit(
            order_id=created["order_id"],
            token="x" * 16,
            stars=5,
            text="Sehr zufrieden mit der neuen Website und dem Ablauf.",
        )


def test_submit_pending_then_publish_public(tmp_path: Path):
    sales, reviews = _sales_reviews(tmp_path)
    order = _paid_delivered(sales)
    token = order["review_token"]
    status = sales.public_status(order["order_id"])
    assert status["review_eligible"] is True
    assert status["review_url"]

    result = reviews.submit(
        order_id=order["order_id"],
        token=token,
        stars=5,
        text="In sechs Tagen hatten wir die neue Website. Alles ohne Probleme.",
        show_company_name=True,
        company_display_name="Autohaus Müller, Dresden",
    )
    assert result["status"] == "pending"
    assert result["review_id"]

    feed = reviews.public_feed(lang="de")
    assert feed["has_reviews"] is False
    assert feed["empty_message"]
    assert feed["average_stars"] is None

    pending = reviews.list_pending()
    assert len(pending) == 1
    published = reviews.moderate(pending[0]["review_id"], action="publish")
    assert published["status"] == "published"

    feed2 = reviews.public_feed(lang="de")
    assert feed2["has_reviews"] is True
    assert feed2["count"] == 1
    assert feed2["average_stars"] == 5.0
    assert feed2["reviews"][0]["company_display_name"] == "Autohaus Müller, Dresden"
    assert feed2["reviews"][0]["verified_purchase"] is True
    assert pending[0].get("verified_purchase") is True


def test_reject_hidden_from_public(tmp_path: Path):
    sales, reviews = _sales_reviews(tmp_path)
    order = _paid_delivered(sales)
    reviews.submit(
        order_id=order["order_id"],
        token=order["review_token"],
        stars=2,
        text="Leider war der Prozess etwas langsam und unklar insgesamt.",
    )
    rid = reviews.list_pending()[0]["review_id"]
    reviews.moderate(rid, action="reject", note="tone")
    feed = reviews.public_feed()
    assert feed["has_reviews"] is False
    assert feed["count"] == 0


def test_one_review_per_order(tmp_path: Path):
    sales, reviews = _sales_reviews(tmp_path)
    order = _paid_delivered(sales)
    reviews.submit(
        order_id=order["order_id"],
        token=order["review_token"],
        stars=4,
        text="Gute Zusammenarbeit und schnelle Lieferung der Landing Page.",
    )
    with pytest.raises(ValueError, match="already_submitted"):
        reviews.submit(
            order_id=order["order_id"],
            token=order["review_token"],
            stars=5,
            text="Zweiter Versuch sollte blockiert werden wegen Einmaligkeit.",
        )


def test_mark_delivered_by_product(tmp_path: Path):
    sales, _reviews = _sales_reviews(tmp_path)
    order = _paid_delivered(sales)
    # already delivered — second call is idempotent on token
    again = sales.mark_delivered_by_product("prod-rev-1")
    assert again is not None
    assert again["order_id"] == order["order_id"]
    assert again.get("review_token")
