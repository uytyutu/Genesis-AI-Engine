"""FinancialExportBridge — harvest ledger + Stripe/finance → DATEV-ready export."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.integration.engine_accounting_service import EngineAccountingService
from app.integration.finance_service import FinanceService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

# SKR03-inspired accounts (Kleingewerbe / Steuerberater mapping)
_ACCOUNT_REVENUE = "8400"
_ACCOUNT_BANK = "1200"
_ACCOUNT_PAYMENT_TRANSIT = "1360"
_ACCOUNT_FEES = "4970"
_ACCOUNT_CRYPTO_GAIN = "2742"


def _fmt_de_date(iso_or_date: str) -> str:
    raw = (iso_or_date or "").strip()
    if not raw:
        return ""
    try:
        if "T" in raw:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y")
        if len(raw) >= 10 and raw[4] == "-":
            y, m, d = raw[:10].split("-")
            return f"{d}.{m}.{y}"
    except (ValueError, TypeError):
        pass
    return raw[:10]


def _fmt_eur_de(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


class FinancialExportBridge:
    """Merge finance_snapshot, transactions, harvest events → DATEV Buchungsstapel (lite)."""

    def __init__(
        self,
        accounting: EngineAccountingService,
        finance: FinanceService,
        memory_dir: Path | None = None,
        *,
        business_mode: Any | None = None,
    ) -> None:
        self._accounting = accounting
        self._finance = finance
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._business_mode = business_mode

    def _require_live_export(self) -> None:
        if self._business_mode:
            self._business_mode.require_live()

    def _payment_rail(self, provider: str) -> str:
        p = (provider or "").strip().lower()
        if p in ("stripe", "sandbox"):
            return "fiat_stripe"
        if p in ("bitcoin", "usdt", "crypto", "engine"):
            return "crypto"
        if p in ("bank",):
            return "fiat_bank"
        return "other"

    def collect_ledger_entries(self) -> list[dict[str, Any]]:
        """Unified ledger rows for export (fiat + crypto + harvest)."""
        settings = self._accounting.load_tax_settings()
        entries: list[dict[str, Any]] = []
        seen: set[str] = set()

        for tx in _read_jsonl(self._memory / "finance_transactions.jsonl"):
            pid = str(tx.get("payment_id") or tx.get("order_id") or tx.get("at") or "")
            if pid in seen:
                continue
            seen.add(pid)
            amount = float(tx.get("amount_eur") or 0)
            if amount <= 0:
                continue
            provider = str(tx.get("provider") or "stripe")
            rail = self._payment_rail(provider)
            commission = 0.0
            if rail == "fiat_stripe":
                pct = float(settings.get("stripe_fee_percent") or 0) / 100.0
                fixed = float(settings.get("stripe_fee_fixed_eur") or 0)
                commission = round(amount * pct + fixed, 2)
            entries.append(
                {
                    "date": _fmt_de_date(str(tx.get("at", ""))),
                    "beleg": pid[:12],
                    "text": str(tx.get("label") or "Erlös Engine"),
                    "gross_eur": amount,
                    "commission_eur": commission,
                    "net_eur": round(max(0.0, amount - commission), 2),
                    "soll_haben": "H",
                    "konto": _ACCOUNT_REVENUE,
                    "gegenkonto": _ACCOUNT_PAYMENT_TRANSIT if rail == "fiat_stripe" else _ACCOUNT_BANK,
                    "payment_rail": rail,
                    "source": "finance_transactions",
                    "event_type": str(tx.get("category") or "sale"),
                }
            )
            if commission > 0:
                entries.append(
                    {
                        "date": _fmt_de_date(str(tx.get("at", ""))),
                        "beleg": f"{pid[:8]}-fee",
                        "text": "Stripe Provision",
                        "gross_eur": commission,
                        "commission_eur": 0.0,
                        "net_eur": commission,
                        "soll_haben": "S",
                        "konto": _ACCOUNT_FEES,
                        "gegenkonto": _ACCOUNT_PAYMENT_TRANSIT,
                        "payment_rail": "fiat_stripe",
                        "source": "finance_transactions",
                        "event_type": "fee",
                    }
                )

        for ev in _read_jsonl(self._memory / "engine_harvest_events.jsonl"):
            ev_type = str(ev.get("type") or "")
            amount = float(ev.get("amount_eur") or ev.get("data_product_value_eur") or 0)
            if amount <= 0 and ev_type not in ("pattern_intel", "junk_micro_revenue"):
                continue
            if ev_type == "pattern_intel":
                amount = float(ev.get("data_product_value_eur") or 0)
            oid = str(ev.get("opportunity_id") or ev.get("at") or "")
            key = f"harvest-{oid}-{ev_type}-{ev.get('at')}"
            if key in seen or amount <= 0:
                continue
            seen.add(key)
            provider = "engine"
            rail = "crypto" if ev_type in ("pattern_intel",) else "fiat_stripe"
            entries.append(
                {
                    "date": _fmt_de_date(str(ev.get("at", ""))),
                    "beleg": oid.replace("opp-", "")[:10],
                    "text": f"Harvest {ev_type}: {ev.get('company', '')}".strip(),
                    "gross_eur": amount,
                    "commission_eur": 0.0,
                    "net_eur": amount,
                    "soll_haben": "H",
                    "konto": _ACCOUNT_CRYPTO_GAIN if rail == "crypto" else _ACCOUNT_REVENUE,
                    "gegenkonto": _ACCOUNT_BANK,
                    "payment_rail": rail,
                    "source": "engine_harvest_events",
                    "event_type": ev_type,
                }
            )

        for payout in _read_jsonl(self._memory / "finance_payouts.jsonl"):
            amount = float(payout.get("amount_eur") or 0)
            if amount <= 0:
                continue
            key = f"payout-{payout.get('at')}-{amount}"
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                {
                    "date": _fmt_de_date(str(payout.get("at", ""))),
                    "beleg": "PAYOUT",
                    "text": f"Auszahlung {payout.get('provider', 'bank')}",
                    "gross_eur": amount,
                    "commission_eur": 0.0,
                    "net_eur": amount,
                    "soll_haben": "S",
                    "konto": _ACCOUNT_BANK,
                    "gegenkonto": _ACCOUNT_PAYMENT_TRANSIT,
                    "payment_rail": self._payment_rail(str(payout.get("provider") or "bank")),
                    "source": "finance_payouts",
                    "event_type": "payout",
                }
            )

        for line in self._accounting.harvest_lines():
            gross = float(line.get("gross_eur") or 0)
            if gross <= 0:
                continue
            key = f"asset-{line.get('asset_id')}-{line.get('date')}"
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                {
                    "date": _fmt_de_date(str(line.get("date", ""))),
                    "beleg": str(line.get("asset_id", "")).replace("opp-", "")[:10],
                    "text": f"Asset Erlös: {line.get('asset_name', '')}",
                    "gross_eur": gross,
                    "commission_eur": float(line.get("commission_eur") or 0),
                    "net_eur": float(line.get("net_clean_eur") or gross),
                    "soll_haben": "H",
                    "konto": _ACCOUNT_REVENUE,
                    "gegenkonto": _ACCOUNT_BANK,
                    "payment_rail": "fiat_stripe",
                    "source": "harvest_lines",
                    "event_type": "asset_revenue",
                    "mwst_reserve_eur": float(line.get("tax_reserve_eur") or 0),
                }
            )

        entries.sort(key=lambda x: x.get("date", ""), reverse=True)
        return entries

    def export_summary(self) -> dict[str, Any]:
        self._require_live_export()
        entries = self.collect_ledger_entries()
        fiat = sum(e["gross_eur"] for e in entries if e.get("payment_rail") == "fiat_stripe")
        crypto = sum(e["gross_eur"] for e in entries if e.get("payment_rail") == "crypto")
        payouts = sum(e["gross_eur"] for e in entries if e.get("event_type") == "payout")
        snap = self._finance._load_snapshot()  # noqa: SLF001 — export bridge
        return {
            "entries_count": len(entries),
            "fiat_gross_eur": round(fiat, 2),
            "crypto_gross_eur": round(crypto, 2),
            "payouts_eur": round(payouts, 2),
            "platform_balance_eur": float(snap.get("platform_balance_eur") or 0),
            "available_for_withdrawal_eur": float(snap.get("available_for_withdrawal_eur") or 0),
            "format": "DATEV_Buchungsstapel_lite",
            "note": "Import in Lexoffice/DATEV — mapping SKR03. Crypto = Konto 2742.",
        }

    def export_datev_csv(self) -> str:
        self._require_live_export()
        """DATEV-compatible Buchungsstapel (lite) — semicolon, DE decimals."""
        settings = self._accounting.load_tax_settings()
        vat = float(settings.get("vat_rate_percent") or 19)
        entries = self.collect_ledger_entries()

        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=";", lineterminator="\n")
        writer.writerow(
            [
                "Buchungsdatum",
                "Belegnummer",
                "Buchungstext",
                "Umsatz_EUR",
                "Soll_Haben",
                "Konto",
                "Gegenkonto",
                f"MwSt_{vat}%_Reserve_EUR",
                "Netto_EUR",
                "Provision_EUR",
                "Zahlungsweg",
                "Quelle",
                "Ereignis",
            ]
        )
        for e in entries:
            mwst = float(e.get("mwst_reserve_eur") or 0)
            if mwst <= 0 and e.get("soll_haben") == "H" and e.get("event_type") in ("sale", "asset_revenue"):
                net = float(e.get("net_eur") or e.get("gross_eur") or 0)
                mwst = round(net * (vat / 100.0) / (1 + vat / 100.0), 2)
            writer.writerow(
                [
                    e.get("date", ""),
                    e.get("beleg", ""),
                    e.get("text", ""),
                    _fmt_eur_de(float(e.get("gross_eur") or 0)),
                    e.get("soll_haben", ""),
                    e.get("konto", ""),
                    e.get("gegenkonto", ""),
                    _fmt_eur_de(mwst),
                    _fmt_eur_de(float(e.get("net_eur") or 0)),
                    _fmt_eur_de(float(e.get("commission_eur") or 0)),
                    e.get("payment_rail", ""),
                    e.get("source", ""),
                    e.get("event_type", ""),
                ]
            )
        return buf.getvalue()
