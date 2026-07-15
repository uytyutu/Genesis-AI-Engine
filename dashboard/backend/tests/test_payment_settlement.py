"""Payment settlement — DE 3 business days hold."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.integration.finance_service import FinanceService
from app.integration.payment_settlement_service import (
    DE_SETTLEMENT_BUSINESS_DAYS,
    PaymentSettlementService,
    add_business_days,
)


def test_add_business_days_skips_weekend():
    # Friday 2026-07-10 + 3 business days = Wednesday 2026-07-15
    start = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)
    end = add_business_days(start, 3)
    assert end.weekday() < 5
    assert (end - start).days >= 3


def test_stripe_payment_pending_then_available(tmp_path: Path):
    svc = PaymentSettlementService(tmp_path)
    row = svc.record_payment(
        amount_eur=250.0,
        payment_id="pi_test_1",
        provider="stripe",
        label="Audit",
    )
    assert row["settlement_status"] == "pending_settlement"
    t = svc.totals()
    assert t["paid_by_client_eur"] == 250.0
    assert t["pending_settlement_eur"] == 250.0
    assert t["available_for_withdrawal_eur"] == 0.0

    rows = svc._load_rows()
    rows[0]["available_at"] = datetime.now(timezone.utc).isoformat()
    svc._save_rows(rows)
    t2 = svc.totals()
    assert t2["available_for_withdrawal_eur"] == 250.0
    assert t2["pending_settlement_eur"] == 0.0


def test_credit_order_payment_creates_settlement(tmp_path: Path):
    fin = FinanceService(tmp_path)
    fin.credit_order_payment(
        100.0,
        "Test order",
        provider="stripe",
        order_id="ord_1",
        external_id="cs_test_abc",
    )
    snap = fin._load_snapshot()
    assert snap["paid_by_client_eur"] == 100.0
    assert snap["pending_settlement_eur"] == 100.0
    assert snap["available_for_withdrawal_eur"] == 0.0


def test_allocate_withdrawal_only_available(tmp_path: Path):
    svc = PaymentSettlementService(tmp_path)
    svc.record_payment(amount_eur=30, payment_id="a", provider="stripe", label="A", immediate_available=True)
    svc.record_payment(amount_eur=20, payment_id="b", provider="stripe", label="B")
    assert svc.totals()["available_for_withdrawal_eur"] == 30.0
    ids = svc.allocate_withdrawal(30.0)
    assert len(ids) == 1
    assert svc.totals()["available_for_withdrawal_eur"] == 0.0
