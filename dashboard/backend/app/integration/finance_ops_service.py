"""CEO Finance & Tax Center — Financial Truth (REAL Ledger only for taxes).

REAL Einnahmen / Finanzamt / ZIP ← virtus_finance_ledger.jsonl
  (CONFIRMED | BOOKED | WITHDRAWN only).

sales_orders.json may feed DEMO/TEST panel only — never REAL / Steuerexport.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_DEFAULT_VENDORS: tuple[dict[str, Any], ...] = (
    {
        "id": "stripe",
        "name": "Stripe",
        "category": "einnahmen",
        "pay_url": "https://dashboard.stripe.com/payments",
        "account_url": "https://dashboard.stripe.com",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "payments",
        "note": "Kundeneinnahmen · Auszahlungen · Live-Webhook → Ledger (nicht Auto-Import in Ops)",
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "category": "apis",
        "pay_url": "https://platform.openai.com/account/billing",
        "account_url": "https://platform.openai.com/account/billing/overview",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "llm",
        "note": "API-Billing — Vector / Factory LLM wenn OpenAI aktiv",
    },
    {
        "id": "groq",
        "name": "Groq",
        "category": "apis",
        "pay_url": "https://console.groq.com/settings/billing",
        "account_url": "https://console.groq.com",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "llm",
        "note": "Schnelle LLM-Antworten · optional kostenpflichtig",
    },
    {
        "id": "kimi",
        "name": "Kimi (Moonshot)",
        "category": "apis",
        "pay_url": "https://platform.moonshot.ai/console/account",
        "account_url": "https://platform.moonshot.ai",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "llm",
        "note": "GENESIS_KIMI_API_KEY / MOONSHOT_API_KEY — Billing Moonshot",
    },
    {
        "id": "resend",
        "name": "Resend",
        "category": "apis",
        "pay_url": "https://resend.com/emails",
        "account_url": "https://resend.com/overview",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "outreach_email",
        "note": "Outreach + Receipts · RESEND_API_KEY · Lead Engine Send",
    },
    {
        "id": "hive",
        "name": "Hive",
        "category": "apis",
        "pay_url": "https://thehive.ai/pricing",
        "account_url": "https://thehive.ai",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "media_moderation",
        "note": "Media / Moderation APIs · manueller Billing-Link",
    },
    {
        "id": "railway",
        "name": "Railway",
        "category": "hosting",
        "pay_url": "https://railway.app/account/billing",
        "account_url": "https://railway.app/dashboard",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "backend_host",
        "note": "Backend / Deploy · Production API + Support Inbox",
    },
    {
        "id": "vercel",
        "name": "Vercel",
        "category": "hosting",
        "pay_url": "https://vercel.com/account/billing",
        "account_url": "https://vercel.com/dashboard",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "frontend_host",
        "note": "Frontend Hosting · /site Storefront",
    },
    {
        "id": "hetzner",
        "name": "Hetzner",
        "category": "hosting",
        "pay_url": "https://accounts.hetzner.com/invoice",
        "account_url": "https://console.hetzner.com",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "infra",
        "note": "Server / Storage · optional Infrastruktur",
    },
    {
        "id": "domains",
        "name": "Domains",
        "category": "domains",
        "pay_url": "https://www.ionos.de/mein-konto",
        "account_url": "https://dash.cloudflare.com",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "dns",
        "note": "IONOS (DE) + Cloudflare DNS — Registrar je Kunde; Links öffnen Billing/Konto",
    },
    {
        "id": "toloka",
        "name": "Toloka",
        "category": "sonstiges",
        "pay_url": "https://toloka.ai",
        "account_url": "https://toloka.ai",
        "integration": "manual_link",
        "health": "green",
        "stack_role": "optional_crowd",
        "note": "Nur wenn genutzt · kein Auto-Import · nie REAL Virtus-Umsatz",
    },
)

_PAID_LIKE = frozenset({"paid", "in_production", "ready", "delivered"})


class FinanceOpsService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._memory.mkdir(parents=True, exist_ok=True)
        self._vendors_path = self._memory / "finance_ops_vendors.json"
        self._docs_path = self._memory / "finance_ops_documents.jsonl"
        self._alerts_path = self._memory / "finance_ops_alerts.json"

    def dashboard(self) -> dict[str, Any]:
        vendors = self._vendors()
        docs = self._documents()
        real_income = self._real_income_rows()
        demo_rows = self._demo_test_income_rows()
        # Tax-grade expenses: only uploaded Belege with PDF path/flag
        belege = [
            d
            for d in docs
            if str(d.get("kind") or "") != "income"
            and (d.get("has_pdf") or d.get("pdf_path"))
        ]
        expense_all = [d for d in docs if str(d.get("kind") or "") != "income"]
        invoices = [
            d
            for d in docs
            if str(d.get("kind") or "invoice") in ("invoice", "receipt", "credit_note")
            and (d.get("has_pdf") or d.get("pdf_path"))
        ]
        alerts = self._billing_alerts(vendors, docs)
        health = self._infrastructure_health(vendors, alerts)
        missing = self._missing_document_alerts(real_income, docs, demo_rows)
        brief = self._morning_brief(real_income, alerts, missing, demo_rows)

        real_total = round(sum(float(r.get("amount_eur") or 0) for r in real_income), 2)
        demo_total = round(sum(float(r.get("amount_eur") or 0) for r in demo_rows), 2)
        expense_total = round(sum(float(r.get("amount_eur") or 0) for r in belege), 2)
        auszahlbar = self._auszahlbar_eur()

        return {
            "module": "finance_tax_center",
            "version": "2.0",
            "disclaimer_de": (
                "Virtus Core zeigt REAL-Einnahmen nur aus dem Finance Ledger "
                "(CONFIRMED / BOOKED / WITHDRAWN). Demo-, Test- und Simulationsaufträge "
                "sind getrennt und gehören nicht in den Finanzamt-Bericht. "
                "Keine ELSTER-Anmeldung und keine Steuerberatung — Endgültige Steuer "
                "mit Steuerberater oder Finanzamt prüfen."
            ),
            "reality_note_de": (
                "REAL = Stripe/Live-Webhook → Payment ID → Ledger. "
                "sales_orders (demo/test/ceo_simulation) erscheinen nur unter DEMO/TEST. "
                "Belege = echte PDF/Rechnungen in der Registry — keine .txt-Platzhalter."
            ),
            "empty": real_total == 0 and expense_total == 0 and len(invoices) == 0,
            "layers": {
                "REAL": {
                    "total_eur": real_total,
                    "quelle_de": "virtus_finance_ledger.jsonl · CONFIRMED/BOOKED/WITHDRAWN",
                    "rows": real_income[:40],
                },
                "DEMO_TEST": {
                    "total_eur": demo_total,
                    "quelle_de": "sales_orders.json · demo/test/ceo_simulation (nicht für Steuern)",
                    "rows": demo_rows[:40],
                },
                "AUSZAHLBAR": {
                    "total_eur": auszahlbar,
                    "quelle_de": "Ledger · withdrawable CONFIRMED/BOOKED",
                },
            },
            # Backward-compatible: income = REAL only
            "income": {
                "total_eur": real_total,
                "rows": real_income[:40],
                "sources": ["Finance Ledger (CONFIRMED/BOOKED/WITHDRAWN)"],
                "quelle_de": "virtus_finance_ledger.jsonl",
            },
            "demo_test_income": {
                "total_eur": demo_total,
                "rows": demo_rows[:40],
                "quelle_de": "sales_orders.json (nie REAL / nie Steuerexport)",
            },
            "auszahlbar": {
                "total_eur": auszahlbar,
                "quelle_de": "Ledger withdrawable",
            },
            "expenses": {
                "total_eur": expense_total,
                "rows": belege[:40],
                "categories": sorted({str(d.get("category") or "sonstiges") for d in belege}),
                "quelle_de": "finance_ops_documents.jsonl · nur Einträge mit PDF/Beleg",
                "pending_without_pdf": len(expense_all) - len(belege),
            },
            "invoices": {
                "count": len(invoices),
                "rows": invoices[:60],
                "quelle_de": "Hochgeladene Rechnungen/Belege (PDF)",
            },
            "billing_monitor": {"alerts": alerts},
            "payment_center": {
                "vendors": [
                    {
                        "id": v["id"],
                        "name": v["name"],
                        "category": v.get("category"),
                        "pay_url": (v.get("pay_url") or "").strip() or None,
                        "account_url": (v.get("account_url") or "").strip() or None,
                        "note": v.get("note") or "",
                        "integration": v.get("integration") or "manual_link",
                        "pay_ready": bool(
                            (v.get("pay_url") or "").strip() or (v.get("account_url") or "").strip()
                        ),
                        "stack_role": v.get("stack_role") or "",
                        "health": v.get("health") or "green",
                    }
                    for v in vendors
                ]
            },
            "infrastructure_health": health,
            "missing_documents": missing,
            "morning_brief": brief,
            "order_receipt_path_template": "/order/receipt/{order_id}",
            "tax_export": {
                "available": True,
                "label_de": "Finanzamt-Bericht herunterladen (ZIP)",
                "endpoint": "/api/owner/finance/tax-export",
                "includes": [
                    "Finanzamt_Bericht.html",
                    "Finanzamt_Bericht.csv",
                    "Ledger_REAL.csv",
                    "Einnahmen (nur REAL)",
                    "Belege_Index (echte PDF falls vorhanden)",
                    "Uebersicht.csv",
                    "README.txt",
                ],
                "note_de": (
                    "Enthält nur REAL Ledger. Demo/Test-Aufträge werden nicht exportiert."
                ),
            },
            "finanzamt_report": self.finanzamt_report(),
            "stack_map_de": (
                "Customer → Order → Stripe Payment ID → Ledger CONFIRMED → "
                "Rechnung/Beleg → Finance REAL. Demo/Farm nie in dieser Kette."
            ),
        }

    def _steuerprofil(self) -> dict[str, Any]:
        path = self._memory / "engine_tax_config.json"
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("configured") is True:
                    vat = data.get("vat_rate_percent")
                    vat_f = None
                    if vat is not None and str(vat).strip() != "":
                        vat_f = max(0.0, min(50.0, float(vat)))
                    return {
                        "configured": True,
                        "status_de": str(data.get("status_de") or "Konfiguriert"),
                        "vat_rate_percent": vat_f,
                        "kleinunternehmer": data.get("kleinunternehmer"),
                        "steuerberater_modus": data.get("steuerberater_modus"),
                    }
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return {
            "configured": False,
            "status_de": "Nicht konfiguriert",
            "vat_rate_percent": None,
            "kleinunternehmer": None,
            "steuerberater_modus": None,
        }

    def finanzamt_report(self, *, year: int | None = None) -> dict[str, Any]:
        """EÜR-lite Arbeitshilfe — REAL Ledger only (never sales_orders demo)."""
        year = int(year or datetime.now(timezone.utc).year)
        profil = self._steuerprofil()
        income = self._real_income_rows()
        docs = self._documents()

        def _in_year(raw: str | None) -> bool:
            return str(raw or "").startswith(str(year))

        income_rows = [r for r in income if _in_year(str(r.get("date") or ""))]
        # No fallback to all-years demo — if no REAL this year, einnahmen = 0
        expense_rows = [
            d
            for d in docs
            if str(d.get("kind") or "") != "income"
            and (d.get("has_pdf") or d.get("pdf_path"))
            and _in_year(str(d.get("date") or ""))
        ]

        einnahmen = round(sum(float(r.get("amount_eur") or 0) for r in income_rows), 2)
        ausgaben = round(sum(float(r.get("amount_eur") or 0) for r in expense_rows), 2)
        ueberschuss = round(einnahmen - ausgaben, 2)

        ust_ruecklage: float | None = None
        nach_ruecklage: float | None = None
        vat_display: float | None = None
        if profil["configured"] and profil.get("vat_rate_percent") is not None:
            vat_display = float(profil["vat_rate_percent"])
            ust_ruecklage = round(max(0.0, ueberschuss) * (vat_display / 100.0), 2)
            nach_ruecklage = round(ueberschuss - ust_ruecklage, 2)

        return {
            "authority": "Finanzamt (Deutschland)",
            "authority_note_de": (
                "Für deutsche Steuerpflichtige: Finanzamt — nicht die US Federal Reserve. "
                "Dieser Bericht ist eine Arbeitshilfe aus dem REAL Finance Ledger "
                "(CONFIRMED/BOOKED/WITHDRAWN). Demo/Test/Simulation sind ausgeschlossen."
            ),
            "year": year,
            "currency": "EUR",
            "steuerprofil": profil,
            "vat_rate_percent": vat_display,
            "einnahmen_eur": einnahmen,
            "ausgaben_eur": ausgaben,
            "ueberschuss_eur": ueberschuss,
            "ust_ruecklage_eur": ust_ruecklage,
            "nach_ruecklage_eur": nach_ruecklage,
            "income_count": len(income_rows),
            "expense_count": len(expense_rows),
            "quelle_de": "virtus_finance_ledger.jsonl (REAL) · Belege nur mit PDF",
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer_de": (
                "Keine Steuerberatung und keine ELSTER-Anmeldung. "
                "Zahlen nur aus bestätigtem Ledger + echten Belegen. "
                "USt-Rücklage nur nach konfiguriertem Steuerprofil — sonst «Nicht konfiguriert». "
                "Endgültige Steuer mit Steuerberater oder Finanzamt prüfen."
            ),
            "download_zip": "/api/owner/finance/tax-export",
            "download_html": f"/api/owner/finance/finanzamt-report.html?year={year}",
        }

    def build_finanzamt_html(self, *, year: int | None = None) -> str:
        rep = self.finanzamt_report(year=year)
        y = rep["year"]
        profil = rep.get("steuerprofil") or {}

        def eur(v: float | None) -> str:
            if v is None:
                return "—"
            return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        vat_row = ""
        if profil.get("configured") and rep.get("vat_rate_percent") is not None:
            vat_row = (
                f'<tr><td>Empfohlene USt-/Steuer-Rücklage ({rep["vat_rate_percent"]:g}%)</td>'
                f'<td class="r">{eur(rep["ust_ruecklage_eur"])}</td></tr>'
                f'<tr><td>Nach Rücklage (Orientierung)</td>'
                f'<td class="r">{eur(rep["nach_ruecklage_eur"])}</td></tr>'
            )
        else:
            vat_row = (
                '<tr><td>USt-/Steuer-Rücklage</td>'
                '<td class="r">Nicht berechnet — Steuerprofil nicht konfiguriert</td></tr>'
            )

        return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8"/>
<title>Finanzamt-Bericht {y} — Virtus Core</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 720px; margin: 2rem auto; color: #111; }}
  h1 {{ font-size: 1.4rem; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; }}
  th, td {{ border-bottom: 1px solid #ccc; padding: 0.55rem 0; text-align: left; }}
  td.r {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .muted {{ color: #555; font-size: 0.9rem; }}
  .box {{ border: 1px solid #ddd; padding: 1rem; border-radius: 8px; background: #fafafa; }}
  @media print {{ body {{ margin: 0; }} }}
</style>
</head>
<body>
  <p class="muted">Virtus Core · Arbeitshilfe für das Finanzamt (DE) · nur REAL Ledger</p>
  <h1>Finanzamt-Bericht {y}</h1>
  <p class="muted">{rep["authority_note_de"]}</p>
  <p class="muted">Quelle: {rep.get("quelle_de") or "Ledger REAL"}</p>
  <p class="muted">Steuerstatus: {profil.get("status_de") or "Nicht konfiguriert"} ·
     Steuersatz: {eur(rep.get("vat_rate_percent")) if rep.get("vat_rate_percent") is not None else "—"} ·
     Kleinunternehmer: {profil.get("kleinunternehmer") if profil.get("kleinunternehmer") is not None else "—"} ·
     Steuerberater-Modus: {profil.get("steuerberater_modus") or "—"}</p>
  <div class="box">
    <table>
      <tr><th>Position</th><th class="r">Betrag (EUR)</th></tr>
      <tr><td>Einnahmen (REAL Ledger)</td><td class="r">{eur(rep["einnahmen_eur"])}</td></tr>
      <tr><td>Ausgaben (Belege mit PDF)</td><td class="r">{eur(rep["ausgaben_eur"])}</td></tr>
      <tr><td><strong>Überschuss (EÜR-lite)</strong></td><td class="r"><strong>{eur(rep["ueberschuss_eur"])}</strong></td></tr>
      {vat_row}
    </table>
  </div>
  <p class="muted">Einnahmen-Zeilen: {rep["income_count"]} · Ausgaben-Zeilen: {rep["expense_count"]} ·
  Erstellt: {rep["calculated_at"]}</p>
  <p class="muted"><strong>Hinweis:</strong> {rep["disclaimer_de"]}</p>
  <p class="muted">Drucken → PDF speichern für Ihre Unterlagen oder den Steuerberater.</p>
</body>
</html>
"""

    def add_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {
            "id": str(payload.get("id") or f"doc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"),
            "kind": str(payload.get("kind") or "invoice"),
            "vendor": str(payload.get("vendor") or "").strip() or "Unbekannt",
            "vendor_id": str(payload.get("vendor_id") or "").strip() or None,
            "date": str(payload.get("date") or datetime.now(timezone.utc).date().isoformat()),
            "amount_eur": float(payload.get("amount_eur") or 0),
            "currency": str(payload.get("currency") or "EUR"),
            "category": str(payload.get("category") or "sonstiges"),
            "label": str(payload.get("label") or "").strip(),
            "pdf_path": str(payload.get("pdf_path") or "").strip() or None,
            "has_pdf": bool(payload.get("has_pdf") or payload.get("pdf_path")),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._docs_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {"ok": True, "document": row}

    def build_tax_export_zip(self, *, year: int | None = None) -> tuple[bytes, str]:
        year = year or datetime.now(timezone.utc).year
        docs = [
            d
            for d in self._documents()
            if str(d.get("kind") or "") != "income"
            and (d.get("has_pdf") or d.get("pdf_path"))
        ]
        income = [
            r
            for r in self._real_income_rows()
            if str(r.get("date") or "").startswith(str(year))
        ]
        report = self.finanzamt_report(year=year)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            overview_lines = ["Datum;Quelle;Kategorie;Art;Betrag_EUR;Waehrung;PaymentID;OrderID;PDF"]
            folders = {
                "einnahmen": f"{year}/Einnahmen/",
                "ausgaben": f"{year}/Ausgaben/",
                "stripe": f"{year}/Stripe/",
                "domains": f"{year}/Domains/",
                "hosting": f"{year}/Hosting/",
                "apis": f"{year}/APIs/",
                "sonstiges": f"{year}/Sonstiges/",
                "belege": f"{year}/Belege/",
            }
            for folder in folders.values():
                zf.writestr(folder + ".keep", "")

            # REAL ledger CSV (canonical)
            try:
                from swarm.finance_ledger import FinanceLedger

                zf.writestr(
                    f"{year}/Ledger_REAL.csv",
                    FinanceLedger(self._memory).export_csv(real_only=True),
                )
            except Exception:
                zf.writestr(
                    f"{year}/Ledger_REAL.csv",
                    "uuid,booked_at,amount,currency,confidence\n",
                )

            if not income:
                zf.writestr(
                    f"{folders['einnahmen']}KEINE_REAL_EINNAHMEN.txt",
                    (
                        "Keine REAL-Einnahmen in diesem Jahr.\n"
                        "Demo/Test/Simulation aus sales_orders gehören nicht in diesen Export.\n"
                        "Einnahmen erscheinen erst nach Live-Payment → Ledger CONFIRMED.\n"
                    ),
                )
            else:
                for row in income:
                    date = str(row.get("date") or "")[:10]
                    amount = float(row.get("amount_eur") or 0)
                    pay_id = str(row.get("payment_id") or row.get("payout_id") or "")
                    oid = str(row.get("order_id") or row.get("task_id") or "")
                    overview_lines.append(
                        f"{date};Ledger REAL;einnahmen;income;{amount:.2f};EUR;{pay_id};{oid};nein"
                    )
                    # Index line only — no fake Beleg body as PDF substitute
                    zf.writestr(
                        f"{folders['einnahmen']}index_{date}_{oid or pay_id or 'entry'}.csv",
                        (
                            "date;amount_eur;payment_id;order_id;confidence;quelle\n"
                            f"{date};{amount:.2f};{pay_id};{oid};"
                            f"{row.get('confidence') or ''};Ledger\n"
                        ),
                    )

            if not docs:
                zf.writestr(
                    f"{folders['belege']}KEINE_BELEGE.txt",
                    (
                        "Keine Belege vorhanden.\n"
                        "Laden Sie Rechnungs-PDFs in die Finance-Beleg-Registry, "
                        "oder verknüpfen Sie Order → /order/receipt/{{order_id}}.\n"
                        "receipt_email_sent ist kein PDF-Nachweis.\n"
                    ),
                )
            else:
                belege_index = ["date;vendor;category;amount_eur;pdf;order_id"]
                for doc in docs:
                    date = str(doc.get("date") or "")[:10]
                    vendor = str(doc.get("vendor") or "Unbekannt")
                    cat = str(doc.get("category") or "sonstiges")
                    kind = str(doc.get("kind") or "invoice")
                    amount = float(doc.get("amount_eur") or 0)
                    pdf = "ja" if doc.get("has_pdf") or doc.get("pdf_path") else "nein"
                    overview_lines.append(
                        f"{date};{vendor};{cat};{kind};{amount:.2f};"
                        f"{doc.get('currency') or 'EUR'};;;{pdf}"
                    )
                    belege_index.append(
                        f"{date};{vendor};{cat};{amount:.2f};{pdf};{doc.get('order_id') or ''}"
                    )
                    folder_key = cat if cat in folders else "sonstiges"
                    pdf_path = str(doc.get("pdf_path") or "").strip()
                    if pdf_path:
                        src = Path(pdf_path)
                        if not src.is_file():
                            src = self._memory / pdf_path
                        if src.is_file():
                            zf.write(src, f"{folders['belege']}pdf/{src.name}")
                            zf.write(src, f"{folders[folder_key]}pdf/{src.name}")
                zf.writestr(f"{year}/Belege_Index_{year}.csv", "\n".join(belege_index) + "\n")

            zf.writestr(f"{year}/Uebersicht.csv", "\n".join(overview_lines) + "\n")

            profil = report.get("steuerprofil") or {}
            vat_line = (
                f"USt_Steuer_Ruecklage;{report['ust_ruecklage_eur']:.2f};Orientierung {report['vat_rate_percent']:g}%"
                if report.get("ust_ruecklage_eur") is not None
                else "USt_Steuer_Ruecklage;;Steuerprofil Nicht konfiguriert — nicht berechnet"
            )
            nach_line = (
                f"Nach_Ruecklage;{report['nach_ruecklage_eur']:.2f};nicht steuerfestgesetzt"
                if report.get("nach_ruecklage_eur") is not None
                else "Nach_Ruecklage;;—"
            )
            report_csv = "\n".join(
                [
                    "Kennzahl;Wert_EUR;Hinweis",
                    f"Einnahmen_REAL;{report['einnahmen_eur']:.2f};Ledger CONFIRMED/BOOKED/WITHDRAWN",
                    f"Ausgaben_Belege_PDF;{report['ausgaben_eur']:.2f};nur mit PDF",
                    f"Ueberschuss_EUR_lite;{report['ueberschuss_eur']:.2f};Einnahmen-Ausgaben",
                    vat_line,
                    nach_line,
                    f"Steuerstatus;{profil.get('status_de') or 'Nicht konfiguriert'};",
                ]
            )
            zf.writestr(f"{year}/Finanzamt_Bericht.csv", report_csv + "\n")
            zf.writestr(f"{year}/Einnahmen_{year}.csv", report_csv.split("\n")[0] + "\n" + report_csv.split("\n")[1] + "\n")
            zf.writestr(f"{year}/Ausgaben_{year}.csv", "Kennzahl;Wert_EUR\n" + f"Ausgaben;{report['ausgaben_eur']:.2f}\n")
            zf.writestr(f"{year}/Finanzamt_Bericht.html", self.build_finanzamt_html(year=year))
            zf.writestr(
                f"{year}/README.txt",
                (
                    "Finanzamt-Bericht — Virtus Core (Deutschland)\n"
                    "Nur REAL Finance Ledger (CONFIRMED/BOOKED/WITHDRAWN).\n"
                    "Demo/Test/ceo_simulation/Farm aus sales_orders sind NICHT enthalten.\n"
                    "Keine fiktiven Beleg-.txt als PDF-Ersatz.\n"
                    "Wenn REAL=0: Bericht zeigt 0,00 EUR — korrekt bis zum ersten Live-Payment.\n"
                    "Keine ELSTER-Anmeldung und keine Steuerberatung.\n"
                    f"Erstellt: {datetime.now(timezone.utc).isoformat()}\n"
                ),
            )

        name = f"virtus_finanzamt_bericht_{year}.zip"
        return buf.getvalue(), name

    def _vendors(self) -> list[dict[str, Any]]:
        defaults = {str(v["id"]): dict(v) for v in _DEFAULT_VENDORS}
        if not self._vendors_path.is_file():
            rows = [dict(v) for v in _DEFAULT_VENDORS]
            self._vendors_path.write_text(
                json.dumps({"vendors": rows}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return rows
        try:
            data = json.loads(self._vendors_path.read_text(encoding="utf-8"))
            stored = data.get("vendors") if isinstance(data, dict) else data
            if isinstance(stored, list) and stored:
                merged: list[dict[str, Any]] = []
                seen: set[str] = set()
                for item in stored:
                    if not isinstance(item, dict):
                        continue
                    vid = str(item.get("id") or "")
                    dflt = defaults.get(vid, {})
                    base = {**dflt, **item}
                    if not (base.get("note") or "").strip() and dflt.get("note"):
                        base["note"] = dflt["note"]
                    merged.append(base)
                    seen.add(vid)
                for vid, d in defaults.items():
                    if vid not in seen:
                        merged.append(dict(d))
                self._vendors_path.write_text(
                    json.dumps({"vendors": merged}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return merged
        except (OSError, json.JSONDecodeError):
            pass
        return [dict(v) for v in _DEFAULT_VENDORS]

    def _documents(self) -> list[dict[str, Any]]:
        if not self._docs_path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self._docs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        rows.sort(key=lambda r: str(r.get("date") or ""), reverse=True)
        return rows

    def _auszahlbar_eur(self) -> float:
        try:
            from swarm.finance_ledger import FinanceLedger

            return float(FinanceLedger(self._memory).summary().get("real_withdrawable_eur") or 0)
        except Exception:
            return 0.0

    def _real_income_rows(self) -> list[dict[str, Any]]:
        """REAL only — Finance Ledger tax-allowed confidence."""
        rows: list[dict[str, Any]] = []
        try:
            from swarm.finance_ledger import FinanceLedger
            from swarm.finance_reality_law import tax_export_allowed

            for entry in FinanceLedger(self._memory).list_entries(limit=10_000, real_only=True):
                conf = str(entry.get("confidence") or "")
                if not tax_export_allowed(conf):
                    continue
                rows.append(
                    {
                        "order_id": entry.get("task_id") or None,
                        "payment_id": entry.get("payout_id") or entry.get("bank_reference"),
                        "payout_id": entry.get("payout_id"),
                        "task_id": entry.get("task_id"),
                        "invoice_id": entry.get("invoice_id"),
                        "date": str(
                            entry.get("settlement_date")
                            or entry.get("accrual_date")
                            or entry.get("booked_at")
                            or ""
                        )[:10],
                        "amount_eur": float(entry.get("amount") or 0),
                        "label": str(entry.get("description") or entry.get("source_id") or "Ledger"),
                        "package": None,
                        "kind": "income",
                        "category": "einnahmen",
                        "confidence": conf,
                        "quelle": "ledger",
                        "has_pdf": bool(entry.get("invoice_id") or entry.get("proof_url")),
                        "receipt_url": (
                            f"/order/receipt/{entry['task_id']}"
                            if entry.get("task_id")
                            else None
                        ),
                        "proof_url": entry.get("proof_url"),
                    }
                )
        except Exception:
            return []
        rows.sort(key=lambda r: str(r.get("date") or ""), reverse=True)
        return rows

    def _load_sales_orders(self) -> list[dict[str, Any]]:
        path = self._memory / "sales_orders.json"
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(data, list):
            return [o for o in data if isinstance(o, dict)]
        if isinstance(data, dict):
            if isinstance(data.get("orders"), list):
                return [o for o in data["orders"] if isinstance(o, dict)]
            return [v for v in data.values() if isinstance(v, dict)]
        return []

    @staticmethod
    def _order_non_real_layer(order: dict[str, Any]) -> str | None:
        """Return demo|test|simulation layer, or None if looks like live commercial (still not REAL)."""
        mode = str(order.get("payment_mode") or "").lower()
        prov = str(order.get("payment_provider") or "").lower()
        email = str(order.get("email") or "").lower()
        name = str(order.get("business_name") or "").lower()
        if mode == "demo" or prov == "demo":
            return "demo"
        if prov == "ceo_simulation" or mode == "ceo_simulation":
            return "simulation"
        if any(
            x in email
            for x in (
                "@test.",
                "virtuscore-test",
                "example.com",
                "example.de",
                "+test",
                "golden.",
                "gwt-",
                "b3-review",
                "rc1-cert",
            )
        ):
            return "test"
        if "demo" in name or "golden" in name or "b3 review" in name:
            return "test"
        # Paid-like without live Stripe still never REAL — show as commercial_pipeline
        return "commercial_non_ledger"

    def _demo_test_income_rows(self) -> list[dict[str, Any]]:
        """UI-only: paid-like orders that are NOT Ledger REAL."""
        rows: list[dict[str, Any]] = []
        for order in self._load_sales_orders():
            status = str(order.get("status") or "")
            if status not in _PAID_LIKE:
                continue
            if order.get("finance_cleared_at"):
                continue
            layer = self._order_non_real_layer(order)
            if layer is None:
                continue
            oid = str(order.get("order_id") or "")
            paid_at = str(order.get("paid_at") or order.get("updated_at") or "")[:10]
            rows.append(
                {
                    "order_id": oid,
                    "date": paid_at,
                    "amount_eur": float(order.get("price_eur") or 0),
                    "label": str(order.get("business_name") or order.get("package_name") or "Auftrag"),
                    "package": order.get("package_name"),
                    "kind": "income",
                    "category": "demo_test",
                    "layer": layer,
                    "payment_mode": order.get("payment_mode"),
                    "payment_provider": order.get("payment_provider"),
                    "quelle": "sales_orders_non_real",
                    "has_pdf": False,
                    "receipt_email_sent": bool(order.get("receipt_email_sent")),
                    "receipt_url": f"/order/receipt/{oid}" if oid else None,
                    "note_de": (
                        "Nicht REAL — erscheint nicht im Finanzamt-Bericht. "
                        "receipt_email_sent ≠ PDF-Beleg."
                    ),
                }
            )
        rows.sort(key=lambda r: str(r.get("date") or ""), reverse=True)
        return rows

    def _billing_alerts(
        self, vendors: list[dict[str, Any]], docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc).date()
        custom: dict[str, Any] = {}
        if self._alerts_path.is_file():
            try:
                custom = json.loads(self._alerts_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                custom = {}

        renewals = custom.get("renewals") if isinstance(custom, dict) else {}
        if not isinstance(renewals, dict):
            renewals = {}

        vendor_by_id = {str(v.get("id") or ""): v for v in vendors}
        for vid, renew_on in renewals.items():
            v = vendor_by_id.get(str(vid)) or {"id": vid, "name": vid, "pay_url": None}
            try:
                due = datetime.fromisoformat(str(renew_on)[:10]).date()
            except ValueError:
                continue
            left = (due - now).days
            if left > 30:
                continue
            level = "red" if left <= 3 else "amber"
            alerts.append(
                {
                    "id": f"renew-{vid}",
                    "level": level,
                    "message_de": (
                        f"{'⚠ ' if level == 'amber' else '🚨 '}"
                        f"{v.get('name')}: läuft in {left} Tag(en) ab ({due.isoformat()})."
                    ),
                    "vendor_id": str(vid),
                    "pay_url": v.get("pay_url") or v.get("account_url"),
                }
            )

        for doc in docs[:30]:
            if doc.get("has_pdf") or doc.get("pdf_path"):
                continue
            if str(doc.get("kind") or "") == "income":
                continue
            alerts.append(
                {
                    "id": f"pdf-{doc.get('id')}",
                    "level": "amber",
                    "message_de": (
                        f"⚠ Für {doc.get('vendor')} vom {str(doc.get('date') or '')[:10]} "
                        f"fehlt der PDF-Beleg."
                    ),
                    "vendor_id": doc.get("vendor_id"),
                    "pay_url": None,
                }
            )
        return alerts[:40]

    def _missing_document_alerts(
        self,
        real_income: list[dict[str, Any]],
        docs: list[dict[str, Any]],
        demo_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        missing: list[dict[str, Any]] = []
        for row in real_income:
            if row.get("has_pdf") or row.get("invoice_id") or row.get("proof_url"):
                continue
            oid = row.get("order_id") or row.get("task_id")
            missing.append(
                {
                    "level": "amber",
                    "message_de": (
                        f"⚠ REAL-Zahlung {row.get('payment_id') or oid} "
                        f"({row.get('label')}) am {row.get('date')}: "
                        f"Rechnung/PDF fehlt. Receipt: /order/receipt/{oid}"
                        if oid
                        else f"⚠ REAL-Zahlung ({row.get('label')}) am {row.get('date')}: Beleg fehlt."
                    ),
                    "order_id": oid,
                    "receipt_url": row.get("receipt_url"),
                }
            )
        for doc in docs:
            if doc.get("has_pdf") or doc.get("pdf_path"):
                continue
            if str(doc.get("kind") or "") == "income":
                continue
            missing.append(
                {
                    "level": "amber",
                    "message_de": (
                        f"⚠ Ausgabe {doc.get('vendor')} vom {str(doc.get('date') or '')[:10]}: "
                        f"PDF-Beleg fehlt (Eintrag ohne Nachweis zählt nicht für Steuern)."
                    ),
                }
            )
        if demo_rows:
            missing.append(
                {
                    "level": "info",
                    "message_de": (
                        f"ℹ {len(demo_rows)} Demo/Test/Simulations-Aufträge in sales_orders "
                        f"({sum(float(r.get('amount_eur') or 0) for r in demo_rows):.2f} €) — "
                        f"nicht in REAL / Finanzamt."
                    ),
                }
            )
        return missing[:30]

    def _infrastructure_health(
        self, vendors: list[dict[str, Any]], alerts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        alert_by_vendor = {str(a.get("vendor_id") or ""): a for a in alerts if a.get("vendor_id")}
        items = []
        for v in vendors:
            vid = str(v.get("id") or "")
            status = str(v.get("health") or "green")
            detail = str(v.get("note") or "")
            integration = str(v.get("integration") or "manual_link")
            pay_url = (v.get("pay_url") or "").strip()
            account_url = (v.get("account_url") or "").strip()
            href = pay_url or account_url
            if not href:
                status = "amber"
                detail = "Zahlungslink nicht konfiguriert"
                integration = "not_configured"
            elif status == "amber" and vid not in alert_by_vendor:
                status = "green"
            if vid in alert_by_vendor:
                a = alert_by_vendor[vid]
                status = "red" if a.get("level") == "red" else "amber"
                detail = str(a.get("message_de") or detail)
            items.append(
                {
                    "id": vid,
                    "name": v.get("name"),
                    "status": status,
                    "detail": detail,
                    "integration": integration,
                    "stack_role": v.get("stack_role") or "",
                    "pay_url": pay_url or None,
                    "account_url": account_url or None,
                    "href": href or None,
                }
            )
        worst = "green"
        if any(i["status"] == "red" for i in items):
            worst = "red"
        elif any(i["status"] == "amber" for i in items):
            worst = "amber"
        return {
            "overall": worst,
            "items": items,
            "legend_de": (
                "Grün = Billing-Link bereit (manuell). Amber/Rot nur bei echten Hinweisen "
                "(Ablauf, fehlender Beleg) — keine Live-API zu Anbietern. "
                "Stripe-Link ≠ Auto-Import in REAL Ledger."
            ),
        }

    def _morning_brief(
        self,
        real_income: list[dict[str, Any]],
        alerts: list[dict[str, Any]],
        missing: list[dict[str, Any]],
        demo_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
        y_income = sum(
            float(r.get("amount_eur") or 0)
            for r in real_income
            if str(r.get("date") or "")[:10] == yesterday
        )
        demo_total = sum(float(r.get("amount_eur") or 0) for r in demo_rows)
        lines = [
            {"icon": "eur", "text": f"REAL gestern: {y_income:.2f} €"},
            {
                "icon": "ledger",
                "text": (
                    f"REAL gesamt: {sum(float(r.get('amount_eur') or 0) for r in real_income):.2f} € "
                    f"· Quelle: Ledger"
                ),
            },
            {
                "icon": "demo",
                "text": f"DEMO/TEST (nicht Steuern): {demo_total:.2f} €",
            },
        ]
        attention = list(alerts[:5]) + [m for m in missing if m.get("level") != "info"][:5]
        return {
            "headline_de": "Betrieb · Finanzen · Belege (Financial Truth)",
            "lines": lines,
            "attention": attention,
            "note_de": (
                "Finanzamt sieht nur REAL. Ohne Live-Payment bleibt REAL 0,00 € — korrekt."
            ),
        }
