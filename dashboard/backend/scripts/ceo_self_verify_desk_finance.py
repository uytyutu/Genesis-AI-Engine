"""Self-verify: finance zero, kimi vendor, 15-min ETA, gallery assets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.integration.context import get_integration  # noqa: E402
from app.integration.finance_ops_service import FinanceOpsService  # noqa: E402
from app.integration.finance_service import FinanceService  # noqa: E402
from app.integration.outreach_language_service import OutreachLanguageService  # noqa: E402


def main() -> int:
    ctx = get_integration()
    mem = ctx.acquisition._memory_dir
    print("memory", mem)

    # 1) Full finance reset
    fin = FinanceService(mem)
    reset = fin.reset_ledger_and_wallet()
    print("RESET", reset.get("message_ru"), reset.get("cleared_files"), reset.get("orders_finance_cleared"))

    view = fin.financial_view(demo=False, connected=False)
    print(
        "VIEW gross",
        view.get("gross_synced_eur"),
        "safe",
        view.get("safe_to_withdraw_eur"),
        "pending",
        view.get("pending_at_provider_eur"),
    )
    assert float(view.get("gross_synced_eur") or 0) == 0.0, view
    assert float(view.get("safe_to_withdraw_eur") or 0) == 0.0, view

    ops = FinanceOpsService(mem).dashboard()
    print("OPS income", ops["income"]["total_eur"], "vendors", [v["id"] for v in ops["payment_center"]["vendors"]])
    assert float(ops["income"]["total_eur"]) == 0.0, ops["income"]
    assert any(v["id"] == "kimi" for v in ops["payment_center"]["vendors"]), "kimi missing"

    # 2) Rebuild quotes with new ETA templates
    rebuild = ctx.acquisition.rebuild_pipeline_quotes(limit=40)
    print("REBUILD", rebuild.get("message_ru"), "failed", rebuild.get("failed"))

    # 3) Sample outreach ETA
    subj, body, lang = OutreachLanguageService().draft_outreach(
        company="Test GmbH",
        analysis={"issues": ["Kein HTTPS"]},
        package={"name": "Landing Basic", "price_label": "350 €", "currency": "EUR"},
        price=350,
        fit_reason="test",
        row={"market": "DE", "meta": {"market": "DE"}},
    )
    print("LANG", lang)
    assert "15" in body and ("Minut" in body or "minut" in body.lower()), body[:400]
    assert "5–7" not in body and "5-7" not in body, body[:400]

    # 4) Gallery files exist and are small
    root = ROOT.parent / "frontend" / "public" / "package-previews" / "sites"
    for tier in ("basic", "business", "premium"):
        for niche_dir in (root / tier).iterdir():
            if not niche_dir.is_dir():
                continue
            g = niche_dir / "assets" / "gallery.jpg"
            assert g.is_file(), g
            assert g.stat().st_size < 200_000, (g, g.stat().st_size)
    print("GALLERY ok")

    # 5) Premium HTML has services list
    prem = root / "premium" / "auto" / "index.html"
    html = prem.read_text(encoding="utf-8")
    assert "showcase-services" in html
    assert "Computer-Diagnose" in html
    print("PREMIUM HTML ok")

    # 6) Desk reset + rebuild message
    desk = ctx.acquisition.reset_desk_counters_and_wallet()
    print("DESK", desk.get("message_ru"))
    q = ctx.acquisition._send_quota.health()
    assert int(q.get("sent_today_total") or 0) == 0

    print("ALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
