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
        "note": "Kundeneinnahmen · Auszahlungen (Dashboard-Link)",
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "category": "apis",
        "pay_url": "https://platform.openai.com/account/billing",
        "account_url": "https://platform.openai.com/account/billing/overview",
        "integration": "manual_link",
        "health": "green",
        "note": "API-Billing — Link öffnet Konto, keine Auto-Rechnung",
    },
    {
        "id": "groq",
        "name": "Groq",
        "category": "apis",
        "pay_url": "https://console.groq.com/settings/billing",
        "account_url": "https://console.groq.com",
        "integration": "manual_link",
        "health": "green",
        "note": "Optional · wenn kostenpflichtig",
    },
    {
        "id": "hive",
        "name": "Hive",
        "category": "apis",
        "pay_url": "https://thehive.ai",
        "account_url": "https://thehive.ai",
        "integration": "manual_link",
        "health": "green",
        "note": "Manueller Link — Rechnungen nicht auto-importiert",
    },
    {
        "id": "railway",
        "name": "Railway",
        "category": "hosting",
        "pay_url": "https://railway.app/account/billing",
        "account_url": "https://railway.app/account",
        "integration": "manual_link",
        "health": "green",
        "note": "Billing-Seite öffnen — kein Auto-Abruf von PDFs",
    },
    {
        "id": "vercel",
        "name": "Vercel",
        "category": "hosting",
        "pay_url": "https://vercel.com/account/billing",
        "account_url": "https://vercel.com/account",
        "integration": "manual_link",
        "health": "green",
        "note": "Frontend Hosting · manueller Link",
    },
    {
        "id": "hetzner",
        "name": "Hetzner",
        "category": "hosting",
        "pay_url": "https://accounts.hetzner.com/invoice",
        "account_url": "https://accounts.hetzner.com",
        "integration": "manual_link",
        "health": "green",
        "note": "Server / Storage · manueller Link",
    },
    {
        "id": "domains",
        "name": "Domains",
        "category": "domains",
        "pay_url": "",
        "account_url": "",
        "integration": "not_configured",
        "health": "green",
        "note": "Registrar je Kunde — Zahlungslink noch nicht hinterlegt",
    },
    {
        "id": "toloka",
        "name": "Toloka",
        "category": "sonstiges",
        "pay_url": "https://toloka.ai",
        "account_url": "https://toloka.ai",
        "integration": "manual_link",
        "health": "green",
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
                "Virtus Core sammelt und klassifiziert Belege — keine automatische Steuerberechnung. "
                "Endgültige Steuer bleibt bei Ihnen oder Ihrem Steuerberater."
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
                        "pay_ready": bool((v.get("pay_url") or "").strip() or (v.get("account_url") or "").strip()),
                    }
                    for v in vendors
                ]
            },
            "infrastructure_health": health,
            "missing_documents": missing,
            "morning_brief": brief,
            "tax_export": {
                "available": True,
                "endpoint": "/api/owner/finance/tax-export",
                "label_de": "Export für Steuerberater",
                "includes": [
                    "Einnahmen",
                    "Ausgaben",
                    "Stripe",
                    "Domains",
                    "Hosting",
                    "APIs",
                    "Sonstiges",
                    "Übersicht.csv",
                    "Uebersicht.csv",
                ],
            },
        }

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
            zf.writestr(
                f"{year}/README.txt",
                (
                    "Export fuer Steuerberater — Virtus Core\n"
                    "Keine Steuerberechnung. Bitte mit Steuerberater pruefen.\n"
                    f"Erstellt: {datetime.now(timezone.utc).isoformat()}\n"
                    "Hinweis: Uebersicht.csv = Zusammenfassung aller Belege.\n"
                ),
            )

        name = f"virtus_steuer_export_{year}.zip"
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
                    base.update({k: v for k, v in r.items() if v is not None})
                    if "integration" not in base:
                        base["integration"] = "manual_link"
                    # Drop obsolete fake countdown fields from older seeds
                    base.pop("renewal_hint_days", None)
                    # Keep canonical "not_configured" vendors honest (no stale pay URLs)
                    if (defaults.get(vid) or {}).get("integration") == "not_configured":
                        base["pay_url"] = defaults[vid].get("pay_url") or ""
                        base["account_url"] = defaults[vid].get("account_url") or ""
                        base["integration"] = "not_configured"
                        base["note"] = defaults[vid].get("note") or base.get("note")
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
            if not (v.get("pay_url") or v.get("account_url")):
                status = "amber"
                detail = "Zahlungslink nicht konfiguriert"
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
            "legend_de": "Status manuell / aus CEO-Hinweisen — keine Live-API zu Anbietern.",
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
