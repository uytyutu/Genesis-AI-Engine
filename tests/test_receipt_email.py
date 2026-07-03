"""Receipt email after payment."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from app.integration.receipt_email_service import ReceiptEmailService


def test_receipt_skipped_without_config():
    svc = ReceiptEmailService()
    old_key = os.environ.pop("RESEND_API_KEY", None)
    old_from = os.environ.pop("GENESIS_EMAIL_FROM", None)
    try:
        result = svc.send_order_receipt(
            order={"order_id": "ord-x", "email": "client@example.com", "business_name": "Test"},
            receipt_text="Спасибо за оплату.",
        )
        assert result["skipped"] is True
        assert result["reason"] == "not_configured"
    finally:
        if old_key is not None:
            os.environ["RESEND_API_KEY"] = old_key
        if old_from is not None:
            os.environ["GENESIS_EMAIL_FROM"] = old_from


def test_receipt_skipped_without_client_email():
    svc = ReceiptEmailService()
    os.environ["RESEND_API_KEY"] = "re_test"
    os.environ["GENESIS_EMAIL_FROM"] = "Genesis <test@resend.dev>"
    try:
        result = svc.send_order_receipt(
            order={"order_id": "ord-x", "email": "", "business_name": "Test"},
            receipt_text="Спасибо.",
        )
        assert result["skipped"] is True
        assert result["reason"] == "no_email"
    finally:
        os.environ.pop("RESEND_API_KEY", None)
        os.environ.pop("GENESIS_EMAIL_FROM", None)
