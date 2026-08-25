"""Finance & Tax Center 2.0 — REAL Ledger only; demo never in Steuerexport."""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path

from swarm.finance_ledger import FinanceLedger
from swarm.revenue_source import CONFIDENCE_CONFIRMED, CONFIDENCE_SIMULATED

from app.integration.finance_ops_service import FinanceOpsService


def test_finance_ops_dashboard_seeds_vendors(tmp_path: Path):
    svc = FinanceOpsService(tmp_path)
    dash = svc.dashboard()
    assert dash["module"] == "finance_tax_center"
    assert dash["version"] == "2.0"
    assert "disclaimer_de" in dash
    vendors = dash["payment_center"]["vendors"]
    ids = {v["id"] for v in vendors}
    assert {"stripe", "railway", "openai", "hive", "hetzner"} <= ids
    assert dash["tax_export"]["available"] is True
    assert dash["infrastructure_health"]["overall"] in ("green", "amber", "red")
    assert (tmp_path / "finance_ops_vendors.json").is_file()
    fa = dash["finanzamt_report"]
    assert fa["authority"] == "Finanzamt (Deutschland)"
    assert fa["einnahmen_eur"] == 0.0
    assert fa["steuerprofil"]["configured"] is False
    assert fa["ust_ruecklage_eur"] is None
    assert fa["download_zip"]
    assert "finanzamt-report.html" in fa["download_html"]


def test_finanzamt_ignores_sales_orders_demo(tmp_path: Path):
    """sales_orders paid/demo must NEVER inflate REAL / Finanzamt."""
    orders = [
        {
            "order_id": "ord-demo",
            "status": "paid",
            "price_eur": 650,
            "business_name": "Café Berlin",
            "payment_mode": "demo",
            "paid_at": "2026-07-10T10:00:00+00:00",
        },
        {
            "order_id": "ord-b3",
            "status": "ready",
            "price_eur": 599,
            "business_name": "B3 Review",
            "payment_mode": "demo",
            "email": "b3-review-gate@virtuscore-test.example",
            "paid_at": "2026-08-24T10:00:00+00:00",
        },
    ]
    (tmp_path / "sales_orders.json").write_text(json.dumps(orders), encoding="utf-8")
    # Expense without PDF must not count toward tax ausgaben
    svc = FinanceOpsService(tmp_path)
    svc.add_document(
        {
            "vendor": "Railway",
            "amount_eur": 50,
            "category": "hosting",
            "kind": "invoice",
            "date": "2026-07-12",
            "has_pdf": False,
        }
    )
    rep = svc.finanzamt_report(year=2026)
    assert rep["einnahmen_eur"] == 0.0
    assert rep["ausgaben_eur"] == 0.0
    assert rep["ueberschuss_eur"] == 0.0
    assert rep["ust_ruecklage_eur"] is None
    dash = svc.dashboard()
    assert dash["income"]["total_eur"] == 0.0
    assert dash["layers"]["REAL"]["total_eur"] == 0.0
    assert dash["demo_test_income"]["total_eur"] == 1249.0
    assert dash["layers"]["DEMO_TEST"]["total_eur"] == 1249.0

    raw, name = svc.build_tax_export_zip(year=2026)
    assert "finanzamt" in name.lower()
    with zipfile.ZipFile(BytesIO(raw)) as zf:
        names = zf.namelist()
        assert any("Finanzamt_Bericht.html" in n for n in names)
        assert any("KEINE_REAL_EINNAHMEN" in n for n in names)
        assert any("KEINE_BELEGE" in n for n in names)
        html = zf.read(next(n for n in names if n.endswith("Finanzamt_Bericht.html"))).decode(
            "utf-8"
        )
        assert "0,00" in html or "0.00" in html
        assert "Café Berlin" not in html
        assert "ord-demo" not in "\n".join(names)
        overview = zf.read(next(n for n in names if n.endswith("Uebersicht.csv"))).decode("utf-8")
        assert "650" not in overview
        assert "ord-demo" not in overview


def test_finanzamt_real_from_ledger_only(tmp_path: Path):
    FinanceLedger(tmp_path).append(
        source_id="stripe",
        amount=299.0,
        description="Website Basic live",
        confidence=CONFIDENCE_CONFIRMED,
        payout_id="pi_live_1",
        task_id="ord-live-1",
        settlement_date="2026-08-20",
    )
    # Simulated ledger noise must not enter tax
    FinanceLedger(tmp_path).append(
        source_id="sim",
        amount=999.0,
        description="should not tax",
        confidence=CONFIDENCE_SIMULATED,
        payout_id="",
    )
    # Demo order must not add
    (tmp_path / "sales_orders.json").write_text(
        json.dumps(
            [
                {
                    "order_id": "ord-demo",
                    "status": "paid",
                    "price_eur": 11630,
                    "payment_mode": "demo",
                    "paid_at": "2026-08-01T00:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )
    # Tax PDF expense
    pdf = tmp_path / "railway.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake")
    svc = FinanceOpsService(tmp_path)
    svc.add_document(
        {
            "vendor": "Railway",
            "amount_eur": 50,
            "category": "hosting",
            "kind": "invoice",
            "date": "2026-08-21",
            "pdf_path": str(pdf),
            "has_pdf": True,
        }
    )
    (tmp_path / "engine_tax_config.json").write_text(
        json.dumps({"configured": True, "vat_rate_percent": 19, "kleinunternehmer": False}),
        encoding="utf-8",
    )
    rep = svc.finanzamt_report(year=2026)
    assert rep["einnahmen_eur"] == 299.0
    assert rep["ausgaben_eur"] == 50.0
    assert rep["ueberschuss_eur"] == 249.0
    assert rep["ust_ruecklage_eur"] == 47.31
    assert rep["steuerprofil"]["configured"] is True
    dash = svc.dashboard()
    assert dash["income"]["total_eur"] == 299.0
    assert dash["demo_test_income"]["total_eur"] == 11630.0
    assert dash["auszahlbar"]["total_eur"] >= 299.0

    raw, _ = svc.build_tax_export_zip(year=2026)
    with zipfile.ZipFile(BytesIO(raw)) as zf:
        text = "\n".join(zf.namelist())
        assert "11630" not in zf.read(
            next(n for n in zf.namelist() if n.endswith("Finanzamt_Bericht.csv"))
        ).decode("utf-8")
        assert "Ledger_REAL.csv" in text
        assert "ord-demo" not in text


def test_finance_ops_empty_export_and_no_fake_alerts(tmp_path: Path):
    svc = FinanceOpsService(tmp_path)
    dash = svc.dashboard()
    assert dash["empty"] is True
    assert dash["billing_monitor"]["alerts"] == []
    assert "reality_note_de" in dash
    domains = next(v for v in dash["payment_center"]["vendors"] if v["id"] == "domains")
    assert domains["pay_ready"] is True
    assert dash["infrastructure_health"]["overall"] == "green"
    assert all(i["status"] == "green" for i in dash["infrastructure_health"]["items"])
    assert any(v["id"] == "resend" for v in dash["payment_center"]["vendors"])

    raw, name = svc.build_tax_export_zip(year=2026)
    assert name.endswith(".zip")
    with zipfile.ZipFile(BytesIO(raw)) as zf:
        names = zf.namelist()
        assert any("Einnahmen" in n for n in names)
        assert any("Uebersicht.csv" in n for n in names)
        assert any("KEINE_BELEGE" in n for n in names)

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
    # Without PDF — not in tax expenses
    assert dash["expenses"]["total_eur"] == 0.0
    assert any("Railway" in (a.get("message_de") or "") for a in dash["billing_monitor"]["alerts"])
