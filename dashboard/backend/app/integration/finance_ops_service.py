"""CEO Finance & Tax Center — ops panel (not tax calculation).

Income from paid orders / settlements. Vendor spend + invoices are a CEO-managed
registry with official pay URLs. Export für Steuerberater packs classified docs.
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
        "note": "Kundeneinnahmen · Auszahlungen · Orders /finance ↔ Stripe",
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
        "note": "Nur wenn genutzt · kein Auto-Import",
    },
)


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
        income = self._income_rows()
        expenses = [d for d in docs if str(d.get("kind") or "") != "income"]
        invoices = [d for d in docs if str(d.get("kind") or "invoice") in ("invoice", "receipt", "credit_note")]
        alerts = self._billing_alerts(vendors, docs)
        health = self._infrastructure_health(vendors, alerts)
        missing = self._missing_document_alerts(income, docs)
        brief = self._morning_brief(income, alerts, missing)

        income_total = sum(float(r.get("amount_eur") or 0) for r in income)
        expense_total = sum(float(r.get("amount_eur") or 0) for r in expenses)

        return {
            "module": "finance_tax_center",
            "disclaimer_de": (
                "Virtus Core berechnet automatisch eine EÜR-lite Arbeitshilfe (Einnahmen − Ausgaben + "
                "USt-Rücklage) für das deutsche Finanzamt. Keine ELSTER-Anmeldung und keine Steuerberatung — "
                "Endgültige Steuer mit Steuerberater oder Finanzamt prüfen."
            ),
            "reality_note_de": (
                "Heute: Einnahmen aus bezahlten Aufträgen + manuell hinterlegte Belege + "
                "Links zu Billing-Seiten. Noch nicht: Auto-PDF von Anbietern, E-Mail-Import, "
                "Buchhaltungs-Kategorien, gemeinsames Projekt-Archiv mit Logos/Fotos."
            ),
            "empty": income_total == 0 and expense_total == 0 and len(invoices) == 0,
            "income": {
                "total_eur": round(income_total, 2),
                "rows": income[:40],
                "sources": ["Stripe / bezahlte Bestellungen", "manuelle Einträge"],
            },
            "expenses": {
                "total_eur": round(expense_total, 2),
                "rows": expenses[:40],
                "categories": sorted({str(d.get("category") or "sonstiges") for d in expenses}),
            },
            "invoices": {
                "count": len(invoices),
                "rows": invoices[:60],
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
                        "stack_role": v.get("stack_role") or "",
                        "pay_ready": bool(
                            (v.get("pay_url") or "").strip()
                            or (v.get("account_url") or "").strip()
                        ),
                        "health": v.get("health") or "green",
                    }
                    for v in vendors
                ]
            },
            "infrastructure_health": health,
            "missing_documents": missing,
            "morning_brief": brief,
            "stack_map_de": (
                "Stripe ← bezahlte Aufträge · Resend ← Outreach/Receipts · "
                "Railway ← Backend · Vercel ← /site · Domains ← IONOS/Cloudflare · "
                "LLM (OpenAI/Groq/Kimi) ← Vector"
            ),
            "tax_export": {
                "available": True,
                "endpoint": "/api/owner/finance/tax-export",
                "label_de": "Finanzamt-Bericht herunterladen (ZIP)",
                "includes": [
                    "Finanzamt_Bericht.html",
                    "Finanzamt_Bericht.csv",
                    "Einnahmen",
                    "Ausgaben",
                    "Stripe",
                    "Domains",
                    "Hosting",
                    "APIs",
                    "Sonstiges",
                    "Uebersicht.csv",
                ],
            },
            "finanzamt_report": self.finanzamt_report(),
        }

    def _vat_rate_percent(self) -> float:
        path = self._memory / "engine_tax_config.json"
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return max(0.0, min(50.0, float(data.get("vat_rate_percent") or 19)))
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return 19.0

    def finanzamt_report(self, *, year: int | None = None) -> dict[str, Any]:
        """Auto-calculated work aid for German Finanzamt / Steuerberater (not ELSTER filing).

        Builds EÜR-lite totals from paid orders + Belege so the CEO does not re-sum by hand.
        """
        year = int(year or datetime.now(timezone.utc).year)
        docs = self._documents()
        income = self._income_rows()

        def _in_year(raw: str | None) -> bool:
            return str(raw or "").startswith(str(year))

        income_rows = [r for r in income if _in_year(str(r.get("date") or ""))]
        # If nothing dated this year yet, still show all (first-year / empty dates)
        if not income_rows and income:
            income_rows = list(income)
        expense_rows = [
            d
            for d in docs
            if str(d.get("kind") or "") != "income" and _in_year(str(d.get("date") or ""))
        ]
        if not expense_rows:
            expense_rows = [d for d in docs if str(d.get("kind") or "") != "income"]

        einnahmen = round(sum(float(r.get("amount_eur") or 0) for r in income_rows), 2)
        ausgaben = round(sum(float(r.get("amount_eur") or 0) for r in expense_rows), 2)
        ueberschuss = round(einnahmen - ausgaben, 2)
        vat = self._vat_rate_percent()
        # Conservative set-aside on surplus (Arbeitshilfe — not a tax assessment)
        ust_ruecklage = round(max(0.0, ueberschuss) * (vat / 100.0), 2)
        nach_ruecklage = round(ueberschuss - ust_ruecklage, 2)

        return {
            "authority": "Finanzamt (Deutschland)",
            "authority_note_de": (
                "Für deutsche Steuerpflichtige: Finanzamt — nicht die US Federal Reserve. "
                "Dieser Bericht ist eine Arbeitshilfe aus Ihren Einnahmen/Ausgaben in Virtus Core."
            ),
            "year": year,
            "currency": "EUR",
            "vat_rate_percent": vat,
            "einnahmen_eur": einnahmen,
            "ausgaben_eur": ausgaben,
            "ueberschuss_eur": ueberschuss,
            "ust_ruecklage_eur": ust_ruecklage,
            "nach_ruecklage_eur": nach_ruecklage,
            "income_count": len(income_rows),
            "expense_count": len(expense_rows),
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer_de": (
                "Keine Steuerberatung und keine ELSTER-Anmeldung. "
                "Zahlen automatisch aus Stripe/Aufträgen und Belegen. "
                "Endgültige Steuer mit Steuerberater oder Finanzamt prüfen."
            ),
            "download_zip": "/api/owner/finance/tax-export",
            "download_html": f"/api/owner/finance/finanzamt-report.html?year={year}",
        }

    def build_finanzamt_html(self, *, year: int | None = None) -> str:
        rep = self.finanzamt_report(year=year)
        y = rep["year"]

        def eur(v: float) -> str:
            return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
  <p class="muted">Virtus Core · Arbeitshilfe für das Finanzamt (DE)</p>
  <h1>Finanzamt-Bericht {y}</h1>
  <p class="muted">{rep["authority_note_de"]}</p>
  <div class="box">
    <table>
      <tr><th>Position</th><th class="r">Betrag (EUR)</th></tr>
      <tr><td>Einnahmen (bezahlt / erfasst)</td><td class="r">{eur(rep["einnahmen_eur"])}</td></tr>
      <tr><td>Ausgaben (Belege)</td><td class="r">{eur(rep["ausgaben_eur"])}</td></tr>
      <tr><td><strong>Überschuss (EÜR-lite)</strong></td><td class="r"><strong>{eur(rep["ueberschuss_eur"])}</strong></td></tr>
      <tr><td>Empfohlene USt-/Steuer-Rücklage ({rep["vat_rate_percent"]:g}%)</td><td class="r">{eur(rep["ust_ruecklage_eur"])}</td></tr>
      <tr><td>Nach Rücklage (Orientierung)</td><td class="r">{eur(rep["nach_ruecklage_eur"])}</td></tr>
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
        docs = self._documents()
        income = self._income_rows()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            overview_lines = ["Datum;Lieferant;Kategorie;Art;Betrag_EUR;Waehrung;PDF"]
            folders = {
                "einnahmen": f"{year}/Einnahmen/",
                "ausgaben": f"{year}/Ausgaben/",
                "stripe": f"{year}/Stripe/",
                "domains": f"{year}/Domains/",
                "hosting": f"{year}/Hosting/",
                "apis": f"{year}/APIs/",
                "sonstiges": f"{year}/Sonstiges/",
            }
            for folder in folders.values():
                zf.writestr(folder + ".keep", "")

            for row in income:
                date = str(row.get("date") or "")[:10]
                vendor = "Stripe / Kunde"
                cat = "einnahmen"
                amount = float(row.get("amount_eur") or 0)
                line = f"{date};{vendor};{cat};income;{amount:.2f};EUR;"
                overview_lines.append(line)
                zf.writestr(
                    f"{folders['einnahmen']}{date}_{row.get('order_id') or 'income'}.txt",
                    (
                        f"Einnahme\nDatum: {date}\n"
                        f"Auftrag: {row.get('order_id')}\n"
                        f"Kunde: {row.get('label')}\n"
                        f"Betrag: {amount:.2f} EUR\n"
                    ),
                )

            for doc in docs:
                date = str(doc.get("date") or "")[:10]
                vendor = str(doc.get("vendor") or "Unbekannt")
                cat = str(doc.get("category") or "sonstiges")
                kind = str(doc.get("kind") or "invoice")
                amount = float(doc.get("amount_eur") or 0)
                pdf = "ja" if doc.get("has_pdf") else "nein"
                overview_lines.append(
                    f"{date};{vendor};{cat};{kind};{amount:.2f};{doc.get('currency') or 'EUR'};{pdf}"
                )
                folder_key = cat if cat in folders else "sonstiges"
                if kind == "income":
                    folder_key = "einnahmen"
                body = (
                    f"{kind}\nLieferant: {vendor}\nDatum: {date}\n"
                    f"Kategorie: {cat}\nBetrag: {amount:.2f} {doc.get('currency') or 'EUR'}\n"
                    f"Label: {doc.get('label') or ''}\n"
                    f"PDF: {doc.get('pdf_path') or ('vorhanden' if doc.get('has_pdf') else 'fehlt')}\n"
                )
                safe_vendor = "".join(c if c.isalnum() or c in "-_" else "_" for c in vendor)[:40]
                zf.writestr(f"{folders[folder_key]}{date}_{safe_vendor}_{doc.get('id')}.txt", body)
                pdf_path = str(doc.get("pdf_path") or "").strip()
                if pdf_path:
                    src = Path(pdf_path)
                    if not src.is_file():
                        src = self._memory / pdf_path
                    if src.is_file():
                        zf.write(src, f"{folders[folder_key]}pdf/{src.name}")

            zf.writestr(f"{year}/Uebersicht.csv", "\n".join(overview_lines) + "\n")
            report = self.finanzamt_report(year=year)
            report_csv = "\n".join(
                [
                    "Kennzahl;Wert_EUR;Hinweis",
                    f"Einnahmen;{report['einnahmen_eur']:.2f};bezahlt/erfasst",
                    f"Ausgaben;{report['ausgaben_eur']:.2f};Belege",
                    f"Ueberschuss_EUR_lite;{report['ueberschuss_eur']:.2f};Einnahmen-Ausgaben",
                    f"USt_Steuer_Ruecklage_{report['vat_rate_percent']:g}pct;{report['ust_ruecklage_eur']:.2f};Orientierung",
                    f"Nach_Ruecklage;{report['nach_ruecklage_eur']:.2f};nicht steuerfestgesetzt",
                ]
            )
            zf.writestr(f"{year}/Finanzamt_Bericht.csv", report_csv + "\n")
            zf.writestr(f"{year}/Finanzamt_Bericht.html", self.build_finanzamt_html(year=year))
            zf.writestr(
                f"{year}/README.txt",
                (
                    "Finanzamt-Bericht — Virtus Core (Deutschland)\n"
                    "Automatisch berechnet aus Einnahmen und Belegen.\n"
                    "Dateien: Finanzamt_Bericht.html (drucken/PDF), Finanzamt_Bericht.csv, Uebersicht.csv\n"
                    "Keine ELSTER-Anmeldung und keine Steuerberatung — mit Steuerberater pruefen.\n"
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
            rows = data.get("vendors") if isinstance(data, dict) else data
            if isinstance(rows, list) and rows:
                merged: list[dict[str, Any]] = []
                seen: set[str] = set()
                for r in rows:
                    if not isinstance(r, dict):
                        continue
                    vid = str(r.get("id") or "")
                    base = dict(defaults.get(vid) or {})
                    # Stored overrides, but empty strings must not wipe default billing URLs.
                    for k, v in r.items():
                        if v is None:
                            continue
                        if k in ("pay_url", "account_url") and not str(v).strip():
                            continue
                        if k == "integration" and str(v) == "not_configured":
                            # Allow upgrade when defaults now ship working links.
                            if (defaults.get(vid) or {}).get("integration") == "manual_link":
                                continue
                        if k == "health" and str(v) == "amber":
                            # Stale amber without renewal alert — heal to default green.
                            continue
                        base[k] = v
                    if "integration" not in base:
                        base["integration"] = "manual_link"
                    base.pop("renewal_hint_days", None)
                    # Heal link readiness
                    if (base.get("pay_url") or "").strip() or (base.get("account_url") or "").strip():
                        if base.get("integration") == "not_configured":
                            base["integration"] = "manual_link"
                        if str(base.get("health") or "") in ("", "amber"):
                            base["health"] = "green"
                    # Fill missing URLs from defaults
                    dflt = defaults.get(vid) or {}
                    if not (base.get("pay_url") or "").strip() and (dflt.get("pay_url") or "").strip():
                        base["pay_url"] = dflt["pay_url"]
                    if not (base.get("account_url") or "").strip() and (
                        dflt.get("account_url") or ""
                    ).strip():
                        base["account_url"] = dflt["account_url"]
                    if dflt.get("stack_role") and not base.get("stack_role"):
                        base["stack_role"] = dflt["stack_role"]
                    if dflt.get("note") and (
                        not base.get("note")
                        or "noch nicht hinterlegt" in str(base.get("note") or "")
                    ):
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

    def _income_rows(self) -> list[dict[str, Any]]:
        path = self._memory / "sales_orders.json"
        rows: list[dict[str, Any]] = []
        if not path.is_file():
            return rows
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return rows
        orders = data if isinstance(data, list) else data.get("orders") if isinstance(data, dict) else []
        if not isinstance(orders, list):
            # dict keyed by order_id
            if isinstance(data, dict):
                orders = list(data.values()) if all(isinstance(v, dict) for v in data.values()) else []
        for order in orders:
            if not isinstance(order, dict):
                continue
            status = str(order.get("status") or "")
            if status not in ("paid", "in_production", "ready", "delivered"):
                continue
            if order.get("finance_cleared_at"):
                continue
            paid_at = str(order.get("paid_at") or order.get("updated_at") or "")[:10]
            rows.append(
                {
                    "order_id": order.get("order_id"),
                    "date": paid_at,
                    "amount_eur": float(order.get("price_eur") or 0),
                    "label": str(order.get("business_name") or order.get("package_name") or "Auftrag"),
                    "package": order.get("package_name"),
                    "kind": "income",
                    "category": "einnahmen",
                    "has_pdf": bool(order.get("receipt_email_sent")),
                }
            )
        rows.sort(key=lambda r: str(r.get("date") or ""), reverse=True)
        return rows

    def _billing_alerts(
        self, vendors: list[dict[str, Any]], docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Only real CEO-configured renewals + missing PDFs — no fake countdown noise."""
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
            if doc.get("has_pdf"):
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
        self, income: list[dict[str, Any]], docs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        missing: list[dict[str, Any]] = []
        for row in income:
            if row.get("has_pdf"):
                continue
            missing.append(
                {
                    "level": "amber",
                    "message_de": (
                        f"⚠ Für Zahlung {row.get('order_id')} ({row.get('label')}) "
                        f"am {row.get('date')} fehlt Kundenbeleg/PDF."
                    ),
                }
            )
        for doc in docs:
            if doc.get("has_pdf"):
                continue
            missing.append(
                {
                    "level": "amber",
                    "message_de": (
                        f"⚠ Für Zahlung {doc.get('vendor')} vom {str(doc.get('date') or '')[:10]} "
                        f"Rechnung nicht gefunden."
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
                # Linked + no renewal/PDF alert → green (stale amber healed)
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
                "(Ablauf, fehlender Beleg) — keine Live-API zu Anbietern."
            ),
        }

    def _morning_brief(
        self,
        income: list[dict[str, Any]],
        alerts: list[dict[str, Any]],
        missing: list[dict[str, Any]],
    ) -> dict[str, Any]:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
        y_income = sum(
            float(r.get("amount_eur") or 0)
            for r in income
            if str(r.get("date") or "")[:10] == yesterday
        )
        new_orders = [r for r in income if str(r.get("date") or "")[:10] == yesterday]
        lines = [
            {"icon": "eur", "text": f"Einkommen gestern: {y_income:.0f} €"},
            {"icon": "orders", "text": f"Neue bezahlte Aufträge: {len(new_orders)}"},
            {"icon": "alerts", "text": f"Billing-Hinweise: {len(alerts)}"},
            {"icon": "docs", "text": f"Fehlende Belege: {len(missing)}"},
        ]
        attention = [a for a in alerts if a.get("level") == "red"]
        return {
            "headline_de": "CEO Morning Brief · Finanzen",
            "lines": lines,
            "attention": attention[:5],
            "note_de": "Kurzüberblick — Details unten in Monitor und Beleg-Archiv.",
        }
