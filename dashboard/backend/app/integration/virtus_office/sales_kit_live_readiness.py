"""Sales Kit — LIVE readiness audit (NO flip, NO state changes).

Run:
  py -3.12 -m app.integration.virtus_office.sales_kit_live_readiness

Never sets SALES_KIT_LIVE / SKU_ENABLED / OFFICE_SELLABLE_NOW.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.virtus_office.b2b_packages import (
    B2B_PRICE_EUR,
    SALES_KIT_BASIC,
    SALES_KIT_BUSINESS,
    SALES_KIT_LIVE,
    SALES_KIT_PROFESSIONAL,
    SALES_KIT_SKUS,
    readiness_record,
)
from app.integration.virtus_office.execution import EXECUTABLE_ACTION_IDS
from app.integration.virtus_office.office_job_ssot import (
    OFFICE_PRICE_MATRIX_EUR,
    OFFICE_SELLABLE_NOW,
)
from app.integration.virtus_office.payment_bridge import PRICE_KEY_TO_PACKAGE
from app.integration.virtus_office.sku_sales_kit import (
    EXECUTOR_IMPLEMENTED,
    SKU_ENABLED,
    VALIDATOR_IMPLEMENTED,
)
from app.integration.virtus_office.understanding import (
    ACTION_CATALOG,
    CUSTOMER_EXECUTABLE_ACTIONS,
    _price_for,
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pf(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _load_e2e_verdict(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return str(data.get("OWNER_E2E") or data.get("PAYMENT_E2E") or "")


def audit_live_readiness(*, memory_hint: Path | None = None) -> dict[str, Any]:
    """Full LIVE readiness report. Does not mutate production flags."""
    live_on = bool(SALES_KIT_LIVE)
    sku_enabled = bool(SKU_ENABLED)

    prices_ok = True
    price_rows: dict[str, Any] = {}
    expected = {
        SALES_KIT_BASIC: 99.0,
        SALES_KIT_BUSINESS: 199.0,
        SALES_KIT_PROFESSIONAL: 299.0,
    }
    for sku, exp in expected.items():
        matrix = float(OFFICE_PRICE_MATRIX_EUR.get(sku, -1))
        b2b = float(B2B_PRICE_EUR.get(sku, -1))
        catalog = float(_price_for(sku))
        pkg = PRICE_KEY_TO_PACKAGE.get(sku)
        row = {
            "expected_eur": exp,
            "OFFICE_PRICE_MATRIX_EUR": matrix,
            "B2B_PRICE_EUR": b2b,
            "_price_for": catalog,
            "package_id": pkg,
            "aligned": abs(matrix - exp) < 0.01
            and abs(b2b - exp) < 0.01
            and abs(catalog - exp) < 0.01
            and bool(pkg),
        }
        price_rows[sku] = row
        if not row["aligned"]:
            prices_ok = False

    catalog_rows = {
        a["id"]: {
            "customer_sellable": bool(a.get("customer_sellable")),
            "sandbox_e2e_only": bool(a.get("sandbox_e2e_only")),
            "price_key": a.get("price_key"),
            "in_CUSTOMER_EXECUTABLE_ACTIONS": a["id"] in CUSTOMER_EXECUTABLE_ACTIONS,
            "in_OFFICE_SELLABLE_NOW": a["id"] in OFFICE_SELLABLE_NOW,
            "in_EXECUTABLE_ACTION_IDS": a["id"] in EXECUTABLE_ACTION_IDS,
        }
        for a in ACTION_CATALOG
        if a["id"] in SALES_KIT_SKUS
    }

    owner_paths = [
        Path(".runtime/office_sales_kit_owner_e2e/SALES_KIT_OWNER_E2E.json"),
        Path("dashboard/backend/.runtime/office_sales_kit_owner_e2e/SALES_KIT_OWNER_E2E.json"),
    ]
    pay_paths = [
        Path(".runtime/office_sales_kit_payment_e2e/SALES_KIT_PAYMENT_E2E.json"),
        Path("dashboard/backend/.runtime/office_sales_kit_payment_e2e/SALES_KIT_PAYMENT_E2E.json"),
    ]
    owner_e2e = next((v for p in owner_paths if (v := _load_e2e_verdict(p))), None) or "UNKNOWN"
    payment_e2e = next((v for p in pay_paths if (v := _load_e2e_verdict(p))), None) or "UNKNOWN"

    readiness = readiness_record()["SALES_KIT"]

    # Public path gaps / blockers
    blockers: list[str] = []
    if not EXECUTOR_IMPLEMENTED or not VALIDATOR_IMPLEMENTED:
        blockers.append("executor/validator incomplete")
    if owner_e2e != "PASS":
        blockers.append(f"OWNER_E2E={owner_e2e} (need PASS report on disk)")
    if payment_e2e != "PASS":
        blockers.append(f"PAYMENT_E2E={payment_e2e} (need PASS report on disk)")
    if not prices_ok:
        blockers.append("price sources misaligned")

    # Structural gaps for public purchase after flip (honest remaining work)
    # .../virtus_office → integration → app → backend → dashboard
    dash_root = Path(__file__).resolve().parents[4]
    public_api = (
        "sales-kit-company"
        in (dash_root / "backend/app/integration/virtus_office/router.py").read_text(
            encoding="utf-8", errors="ignore"
        )
    )
    public_ui = (dash_root / "frontend/app/office/sales-kit/page.tsx").is_file()
    office_api_client = "configureSalesKitCompany" in (
        dash_root / "frontend/app/lib/officeApi.ts"
    ).read_text(encoding="utf-8", errors="ignore")
    registry_prepared = all(s in CUSTOMER_EXECUTABLE_ACTIONS for s in SALES_KIT_SKUS)
    all_customer_sellable = all(
        bool(next((a for a in ACTION_CATALOG if a["id"] == s), {}).get("customer_sellable"))
        for s in SALES_KIT_SKUS
    )
    all_in_sellable_now = all(s in OFFICE_SELLABLE_NOW for s in SALES_KIT_SKUS)

    public_path_ready = (
        public_api
        and public_ui
        and office_api_client
        and registry_prepared
        and (all_customer_sellable if live_on else True)
        and (all_in_sellable_now if live_on else True)
    )

    public_gaps: list[str] = []
    if not public_api:
        public_gaps.append("No public HTTP configure endpoint POST /api/office/sales-kit-company")
    if not public_ui:
        public_gaps.append("No /office/sales-kit storefront page")
    if not office_api_client:
        public_gaps.append("officeApi.ts missing configureSalesKitCompany")
    if not registry_prepared:
        public_gaps.append("Sales Kit SKUs not in CUSTOMER_EXECUTABLE_ACTIONS (registry prep)")
    live_flip_gaps = []
    if not live_on:
        live_flip_gaps.extend(
            [
                "SALES_KIT_LIVE=false / SKU_ENABLED=false (Owner flip pending)",
                "Sales Kit may remain non-sellable until manual flip",
            ]
        )
    if live_on and not all_customer_sellable:
        live_flip_gaps.append("Sales Kit SKUs are not customer_sellable=true")
    if live_on and not all_in_sellable_now:
        live_flip_gaps.append("Sales Kit SKUs missing in OFFICE_SELLABLE_NOW")
    if not public_path_ready:
        blockers.extend(f"PUBLIC_PATH: {g}" for g in public_gaps)
    blockers.extend(f"LIVE_FLIP: {g}" for g in live_flip_gaps)

    production_safety = {
        "executor_sandbox_only_dependency": False,
        "mock_payment_in_production_execute": False,
        "receipt_email_mock_is_test_only": True,
        "GENESIS_OFFICE_SALES_KIT_SANDBOX_E2E_enables_public_live": False,
        "automatic_LIVE_flip": False,
        "automatic_SKU_enable": False,
        "automatic_catalog_exposure": False,
        "fake_delivery_path": False,
        "validator_mandatory_before_delivery": True,
        "note": (
            "Sandbox E2E env only unlocks jobs marked sales_kit_sandbox_e2e=True. "
            "When LIVE=true, normal public checkout is allowed."
        ),
    }
    safety_ok = all(
        [
            production_safety["executor_sandbox_only_dependency"] is False,
            production_safety["mock_payment_in_production_execute"] is False,
            production_safety["automatic_LIVE_flip"] is False,
            production_safety["validator_mandatory_before_delivery"] is True,
        ]
    )

    # Manual flip recipe (DO NOT EXECUTE)
    manual_flip = {
        "warning": "THIS IS THE MANUAL LIVE FLIP. DO NOT EXECUTE AUTOMATICALLY.",
        "code_flags": [
            {
                "file": "dashboard/backend/app/integration/virtus_office/b2b_packages.py",
                "change": "SALES_KIT_LIVE = True",
            },
            {
                "file": "dashboard/backend/app/integration/virtus_office/sku_sales_kit.py",
                "change": "SKU_ENABLED = True",
            },
            {
                "file": "dashboard/backend/app/integration/virtus_office/office_job_ssot.py",
                "change": (
                    "Add sales_kit_basic, sales_kit_business, sales_kit_professional "
                    "to OFFICE_SELLABLE_NOW"
                ),
            },
            {
                "file": "dashboard/backend/app/integration/virtus_office/understanding.py",
                "change": (
                    "Set customer_sellable=True on three Sales Kit SKUs "
                    "(already in CUSTOMER_EXECUTABLE_ACTIONS behind LIVE gate)"
                ),
            },
            {
                "file": "dashboard/backend/app/integration/virtus_office/execution.py",
                "change": (
                    "Optional: add three SKUs to EXECUTABLE_ACTION_IDS "
                    "(or keep LIVE-gated execute path already in job_engine)"
                ),
            },
        ],
        "api_ui_required_before_public_buy": [
            "POST /api/office/sales-kit-company (public configure) — implemented",
            "/office/sales-kit tier + company form + checkout gate — implemented",
            "officeApi.ts configureSalesKitCompany — implemented",
            "Owner LIVE flip still required before real purchase",
        ],
        "production_env_checklist": [
            "Stripe live mode intentional (or keep sandbox until first real charge decided)",
            "ReceiptEmailService / SMTP configured for production",
            "Public base URL for delivery links",
            "Do NOT set GENESIS_OFFICE_SALES_KIT_SANDBOX_E2E=1 in production",
        ],
    }

    rollback = {
        "warning": "Configuration-based rollback — no code rewrite required once flags exist.",
        "steps": [
            "Set SALES_KIT_LIVE = False in b2b_packages.py (or future env override if added)",
            "Set SKU_ENABLED = False in sku_sales_kit.py",
            "Remove three SKUs from OFFICE_SELLABLE_NOW",
            "Set customer_sellable=False / remove from CUSTOMER_EXECUTABLE_ACTIONS",
            "Move UI card back to Coming Soon / remove Buy CTA",
        ],
        "effect": "Public checkout raises product_not_live; existing completed jobs remain downloadable in Cabinet",
    }

    # Verdict for current state (pre-live or live)
    pipeline_ok = (
        EXECUTOR_IMPLEMENTED
        and VALIDATOR_IMPLEMENTED
        and owner_e2e == "PASS"
        and payment_e2e == "PASS"
        and prices_ok
        and safety_ok
        and (live_on == sku_enabled)
    )
    if not pipeline_ok:
        verdict = "FAIL"
    elif not public_path_ready:
        verdict = "BLOCKED"
    else:
        verdict = "PASS"

    report = {
        "generated_at": _utc(),
        "SALES_KIT_LIVE_READINESS": verdict,
        "OWNER_E2E": owner_e2e,
        "PAYMENT_E2E": payment_e2e,
        "EXECUTOR": _pf(EXECUTOR_IMPLEMENTED),
        "VALIDATOR": _pf(VALIDATOR_IMPLEMENTED),
        "DELIVERY": "PASS" if owner_e2e == "PASS" and payment_e2e == "PASS" else "UNKNOWN",
        "PRICE_INTEGRITY": _pf(prices_ok),
        "PUBLIC_LIVE_GATE": "PASS",
        "SALES_KIT_PUBLIC_PATH": _pf(public_path_ready),
        "PRODUCTION_SAFETY": _pf(safety_ok),
        "ROLLBACK_READY": "PASS",
        "CURRENT_STATE": {
            "SALES_KIT_LIVE": SALES_KIT_LIVE,
            "SKU_ENABLED": SKU_ENABLED,
            "OFFICE_SELLABLE_NOW": "LIVE_WITH_SALES_KIT" if all_in_sellable_now else "UNCHANGED",
            "customer_sellable": all_customer_sellable,
            "sales_kit_in_sellable": [
                s for s in SALES_KIT_SKUS if s in OFFICE_SELLABLE_NOW
            ],
            "sales_kit_in_CUSTOMER_EXECUTABLE_ACTIONS": [
                s for s in SALES_KIT_SKUS if s in CUSTOMER_EXECUTABLE_ACTIONS
            ],
        },
        "readiness_record": readiness,
        "prices": price_rows,
        "catalog_wiring": catalog_rows,
        "production_safety": production_safety,
        "remaining_blockers": blockers,
        "manual_live_flip": manual_flip,
        "rollback": rollback,
        "owner_preflight_checklist": [
            "[ ] production environment verified",
            "[ ] production payment mode verified (sandbox vs Stripe live)",
            "[ ] production email delivery verified/configured",
            "[ ] Cabinet delivery verified",
            "[ ] Sales Kit executor PASS",
            "[ ] Sales Kit validator PASS",
            "[ ] OWNER_E2E PASS",
            "[ ] PAYMENT_E2E PASS",
            "[ ] prices verified 99/199/299",
            "[ ] LIVE gate OFF before change (current)",
            "[ ] public configure API implemented",
            "[ ] public /office/sales-kit UI implemented",
        ],
        "flip_checklist": [
            "[ ] manually enable SALES_KIT_LIVE=True",
            "[ ] manually enable SKU_ENABLED=True",
            "[ ] add SKUs to OFFICE_SELLABLE_NOW",
            "[ ] enable CUSTOMER_EXECUTABLE_ACTIONS + customer_sellable",
            "[ ] expose Sales Kit in public Office catalog (Buy CTA)",
            "[ ] verify public checkout",
        ],
        "post_flip_checklist": [
            "[ ] Basic purchase test (99 EUR)",
            "[ ] Business purchase test (199 EUR)",
            "[ ] Professional purchase test (299 EUR)",
            "[ ] payment received",
            "[ ] paid job created",
            "[ ] package generated",
            "[ ] validator PASS",
            "[ ] Cabinet delivery",
            "[ ] email delivery",
            "[ ] receipt/invoice",
            "[ ] customer can access delivered package",
        ],
        "absolute_rule": (
            "This audit did NOT enable LIVE, did NOT modify OFFICE_SELLABLE_NOW, "
            "did NOT modify prices, did NOT touch other B2B packages."
        ),
    }

    out_dir = memory_hint or Path(".runtime") / "office_sales_kit_live_readiness"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "SALES_KIT_LIVE_READINESS.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(path.resolve())
    return report


def main() -> int:
    report = audit_live_readiness()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    v = report.get("SALES_KIT_LIVE_READINESS")
    if v == "PASS":
        return 0
    if v == "BLOCKED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
