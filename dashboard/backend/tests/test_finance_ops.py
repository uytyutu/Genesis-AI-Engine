"""Finance & Tax Center ops — CEO panel without tax calculation."""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

from app.integration.finance_ops_service import FinanceOpsService


def test_finance_ops_dashboard_seeds_vendors(tmp_path: Path):
    svc = FinanceOpsService(tmp_path)
    dash = svc.dashboard()
    assert dash["module"] == "finance_tax_center"
    assert "disclaimer_de" in dash
    vendors = dash["payment_center"]["vendors"]
    ids = {v["id"] for v in vendors}
    assert {"stripe", "railway", "openai", "hive", "hetzner"} <= ids
    assert dash["tax_export"]["available"] is True
    assert dash["infrastructure_health"]["overall"] in ("green", "amber", "red")
    assert (tmp_path / "finance_ops_vendors.json").is_file()


def test_finance_ops_income_from_paid_orders(tmp_path: Path):
    orders = [
        {
            "order_id": "ord-1",
            "status": "paid",
            "price_eur": 350,
            "business_name": "Werkstatt Müller",
            "package_name": "Landing Basic",
            "paid_at": "2026-07-18T10:00:00+00:00",
            "receipt_email_sent": True,
        },
        {
            "order_id": "ord-draft",
            "status": "awaiting_payment",
            "price_eur": 650,
            "business_name": "Draft",
        },
    ]
    (tmp_path / "sales_orders.json").write_text(json.dumps(orders), encoding="utf-8")
    dash = FinanceOpsService(tmp_path).dashboard()
    assert dash["income"]["total_eur"] == 350.0
    assert dash["income"]["rows"][0]["order_id"] == "ord-1"


def test_finance_ops_empty_export_and_no_fake_alerts(tmp_path: Path):
    svc = FinanceOpsService(tmp_path)
    dash = svc.dashboard()
    assert dash["empty"] is True
    assert dash["billing_monitor"]["alerts"] == []
    assert "reality_note_de" in dash
    domains = next(v for v in dash["payment_center"]["vendors"] if v["id"] == "domains")
    assert domains["pay_ready"] is False

    raw, name = svc.build_tax_export_zip(year=2026)
    assert name.endswith(".zip")
    with zipfile.ZipFile(BytesIO(raw)) as zf:
        names = zf.namelist()
        assert any("Einnahmen" in n for n in names)
        assert any("Uebersicht.csv" in n for n in names)

    svc = FinanceOpsService(tmp_path)
    svc.add_document(
        {
            "vendor": "Railway",
            "vendor_id": "railway",
            "amount_eur": 20,
            "category": "hosting",
            "kind": "invoice",
            "date": "2026-07-15",
            "has_pdf": False,
        }
    )
    dash = svc.dashboard()
    assert dash["expenses"]["total_eur"] == 20.0
    assert any("Railway" in (a.get("message_de") or "") for a in dash["billing_monitor"]["alerts"])

    raw, name = svc.build_tax_export_zip(year=2026)
    assert name.endswith(".zip")
    with zipfile.ZipFile(BytesIO(raw)) as zf:
        names = zf.namelist()
        assert any("Uebersicht.csv" in n for n in names)
        assert any("Hosting" in n for n in names)
        overview = next(n for n in names if n.endswith("Uebersicht.csv"))
        text = zf.read(overview).decode("utf-8")
        assert "Railway" in text
