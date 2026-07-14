"""Engine accounting — harvest reports, tax reserve, Rechnungen (DE)."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.opportunity_service import OpportunityService
from app.legal.entity_store import LegalEntityStore

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_DEFAULT_TAX = {
    "vat_rate_percent": 19.0,
    "stripe_fee_percent": 1.4,
    "stripe_fee_fixed_eur": 0.25,
    "service_label": "IT-Analyse und Automatisierung von Internet-Assets",
    "dsgvo_public_business_only": True,
}


class EngineAccountingService:
    def __init__(self, opportunity: OpportunityService, memory_dir: Path | None = None) -> None:
        self._opportunity = opportunity
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._legal = LegalEntityStore(self._memory)

    def _config_path(self) -> Path:
        return self._memory / "engine_tax_config.json"

    def load_tax_settings(self) -> dict[str, Any]:
        path = self._config_path()
        if not path.is_file():
            return dict(_DEFAULT_TAX)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            merged = dict(_DEFAULT_TAX)
            merged.update(data)
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT_TAX)

    def save_tax_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        prev = self.load_tax_settings()
        if "vat_rate_percent" in payload:
            prev["vat_rate_percent"] = max(0.0, min(50.0, float(payload["vat_rate_percent"])))
        if "stripe_fee_percent" in payload:
            prev["stripe_fee_percent"] = max(0.0, min(10.0, float(payload["stripe_fee_percent"])))
        if "stripe_fee_fixed_eur" in payload:
            prev["stripe_fee_fixed_eur"] = max(0.0, float(payload["stripe_fee_fixed_eur"]))
        if "service_label" in payload and str(payload["service_label"]).strip():
            prev["service_label"] = str(payload["service_label"]).strip()
        path = self._config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")
        return prev

    def _stripe_fee(self, gross: float, settings: dict[str, Any]) -> float:
        if gross <= 0:
            return 0.0
        pct = float(settings.get("stripe_fee_percent") or 0) / 100.0
        fixed = float(settings.get("stripe_fee_fixed_eur") or 0)
        return round(gross * pct + fixed, 2)

    def _line_amounts(self, gross: float, settings: dict[str, Any]) -> dict[str, float]:
        commission = self._stripe_fee(gross, settings)
        net_after_fees = round(max(0.0, gross - commission), 2)
        vat_rate = float(settings.get("vat_rate_percent") or 0) / 100.0
        tax_reserve = round(net_after_fees * vat_rate, 2)
        net_clean = round(net_after_fees - tax_reserve, 2)
        return {
            "gross_eur": round(gross, 2),
            "commission_eur": commission,
            "net_after_fees_eur": net_after_fees,
            "tax_reserve_eur": tax_reserve,
            "net_clean_eur": net_clean,
        }

    def harvest_lines(self) -> list[dict[str, Any]]:
        """DSGVO: only business asset fields — no personal contacts."""
        settings = self.load_tax_settings()
        rows = self._opportunity.list_opportunities(source_id="asset_scan", limit=500)
        lines: list[dict[str, Any]] = []
        for row in rows:
            gross = float(row.get("revenue_eur") or 0)
            if gross <= 0 and row.get("status") != "won":
                continue
            amounts = self._line_amounts(gross, settings)
            meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
            lines.append(
                {
                    "date": (row.get("updated_at") or row.get("found_at") or "")[:10],
                    "asset_id": row.get("id", ""),
                    "asset_name": row.get("company_name", ""),
                    "asset_url": row.get("website_url", ""),
                    "niche": meta.get("niche", ""),
                    "status": row.get("status", ""),
                    **amounts,
                }
            )
        lines.sort(key=lambda x: x.get("date", ""), reverse=True)
        return lines

    def accounting_summary(self) -> dict[str, Any]:
        settings = self.load_tax_settings()
        lines = self.harvest_lines()
        totals = {
            "gross_eur": 0.0,
            "commission_eur": 0.0,
            "net_after_fees_eur": 0.0,
            "tax_reserve_eur": 0.0,
            "net_clean_eur": 0.0,
        }
        for line in lines:
            for key in totals:
                totals[key] += float(line.get(key) or 0)
        for key in totals:
            totals[key] = round(totals[key], 2)

        entity = self._legal.load()
        op = entity.operator

        return {
            "tax_settings": settings,
            "totals": totals,
            "harvest_count": len(lines),
            "harvest_lines": lines[:50],
            "dsgvo_note": (
                "Учёт только публичных бизнес-активов (URL, название). "
                "Персональные данные (имена клиентов, телефоны) в отчёты не попадают."
                if settings.get("dsgvo_public_business_only")
                else ""
            ),
            "service_label": settings.get("service_label"),
            "operator_ready": bool(op.full_name and op.address_street),
            "operator_trade_name": op.trade_name or "Virtus Core",
        }

    def export_csv(self) -> str:
        settings = self.load_tax_settings()
        lines = self.harvest_lines()
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=";", lineterminator="\n")
        writer.writerow(
            [
                "Datum",
                "Aktiv",
                "URL",
                "Brutto_EUR",
                "Provision_EUR",
                "Netto_nach_Gebuehren_EUR",
                f"MwSt_Reserve_{settings.get('vat_rate_percent')}%_EUR",
                "Netto_sauber_EUR",
            ]
        )
        for line in lines:
            writer.writerow(
                [
                    line.get("date", ""),
                    line.get("asset_name", ""),
                    line.get("asset_url", ""),
                    f"{line.get('gross_eur', 0):.2f}".replace(".", ","),
                    f"{line.get('commission_eur', 0):.2f}".replace(".", ","),
                    f"{line.get('net_after_fees_eur', 0):.2f}".replace(".", ","),
                    f"{line.get('tax_reserve_eur', 0):.2f}".replace(".", ","),
                    f"{line.get('net_clean_eur', 0):.2f}".replace(".", ","),
                ]
            )
        return buf.getvalue()

    def generate_invoice_html(self, opportunity_id: str) -> str:
        row = self._opportunity.get(opportunity_id)
        if not row:
            raise ValueError("not_found")
        gross = float(row.get("revenue_eur") or row.get("potential_value_eur") or 0)
        if gross <= 0:
            raise ValueError("no_revenue")

        settings = self.load_tax_settings()
        amounts = self._line_amounts(gross, settings)
        entity = self._legal.load()
        op = entity.operator
        vat_rate = float(settings.get("vat_rate_percent") or 19)
        invoice_no = f"VC-{opportunity_id.replace('opp-', '').upper()}"
        today = datetime.now(timezone.utc).strftime("%d.%m.%Y")
        service = str(settings.get("service_label") or _DEFAULT_TAX["service_label"])

        net = amounts["net_after_fees_eur"]
        vat = amounts["tax_reserve_eur"]
        total = amounts["gross_eur"]

        seller = op.trade_name or "Virtus Core"
        seller_addr = ", ".join(
            p
            for p in [
                op.address_street,
                f"{op.address_zip} {op.address_city}".strip(),
                op.address_country,
            ]
            if p and p.strip()
        )
        if not seller_addr.strip():
            seller_addr = "Adresse in legal_entity.json ergänzen"

        return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8"/>
  <title>Rechnung {invoice_no}</title>
  <style>
    body {{ font-family: Arial, sans-serif; max-width: 720px; margin: 2rem auto; color: #111; }}
    h1 {{ font-size: 1.4rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    .right {{ text-align: right; }}
    .muted {{ color: #555; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>Rechnung / Invoice</h1>
  <p class="muted">Nr. {invoice_no} · Datum {today}</p>
  <p><strong>{seller}</strong><br/>{seller_addr}<br/>
  {f"USt-IdNr.: {op.vat_id}" if op.vat_id else "USt-IdNr.: — (nach Gewerbe eintragen)"}</p>
  <p><strong>Leistung:</strong> {service}<br/>
  <strong>Asset:</strong> {row.get("company_name", "")}<br/>
  <strong>URL:</strong> {row.get("website_url", "")}</p>
  <table>
    <tr><th>Beschreibung</th><th class="right">Netto €</th><th class="right">MwSt {vat_rate}% €</th><th class="right">Brutto €</th></tr>
    <tr>
      <td>Monetarisierung Internet-Asset · {row.get("company_name", "")}</td>
      <td class="right">{net:.2f}</td>
      <td class="right">{vat:.2f}</td>
      <td class="right">{total:.2f}</td>
    </tr>
  </table>
  <p class="muted">Stripe-Provision (geschätzt): {amounts["commission_eur"]:.2f} € · Netto sauber: {amounts["net_clean_eur"]:.2f} €</p>
  <p class="muted">Nur öffentliche Geschäftsdaten · DSGVO-konform · Drucken → PDF für Finanzamt.</p>
</body>
</html>"""
