"""Virtus Office capability audit — status from code reality, not marketing cards.

Statuses:
  SELLABLE  — executor + validator present; may appear on vitrine (LIVE still owner flip)
  PARTIAL   — executor exists but incomplete product promise
  BLOCKED   — high-risk SKU missing required validator (or executor incomplete)
  ROADMAP   — contract only; no sellable wiring
  FORBIDDEN — Product Rule / regulation; never sell
"""

from __future__ import annotations

from typing import Any, Literal

from app.integration.virtus_office.office_job_ssot import (
    OFFICE_PIPELINE_LIVE,
    OFFICE_SELLABLE_NOW,
    OFFICE_SKU_ROADMAP,
    OFFICE_VITRINE_FORBIDDEN,
    office_stripe_live,
)
from app.integration.virtus_office.understanding import (
    ACTION_CATALOG,
    CUSTOMER_EXECUTABLE_ACTIONS,
)

CapabilityStatus = Literal["SELLABLE", "PARTIAL", "BLOCKED", "ROADMAP", "FORBIDDEN"]

# High-risk file formats: must not be SELLABLE without a dedicated validator.
HIGH_RISK_SKUS: frozenset[str] = frozenset(
    {
        "xrechnung",
        "zugferd",
        "pdf_a_2b",
        "pdf_ua",
        "fillable_pdf",
        "searchable_pdf",
        "document_archive",
    }
)

FORBIDDEN_SKUS: frozenset[str] = frozenset(OFFICE_VITRINE_FORBIDDEN) | frozenset(
    {
        "beglaubigte_uebersetzung",
        "notarielle_beglaubigung",
        "apostille",
        "legalisation",
        "fuehrungszeugnis",
        "steuerberatung",
        "rechtsberatung",
        "medical_certificate",
    }
)


def _executor_ids() -> frozenset[str]:
    """Single source: what execute_office_action / job_engine will run."""
    from app.integration.virtus_office.execution import EXECUTABLE_ACTION_IDS

    return frozenset(EXECUTABLE_ACTION_IDS)


def _validator_probe(action_id: str) -> dict[str, Any]:
    """Detect whether a dedicated or adequate validator exists."""
    aid = (action_id or "").strip().lower()
    if aid == "document_quality_check":
        from app.integration.virtus_office import document_quality_check as dqc

        return {
            "ok": callable(getattr(dqc, "validate_quality_report_artifact", None)),
            "kind": "dedicated_report_validator",
            "module": "document_quality_check.validate_quality_report_artifact",
        }
    if aid in {
        "translate",
        "convert_docx",
        "extract_data",
        "lebenslauf_create",
        "lebenslauf_improve",
        "bewerbungsschreiben",
        "bewerbung_paket",
    }:
        return {
            "ok": True,
            "kind": "quality_gate",
            "module": "quality_gate.run_quality_gate",
        }
    # High-risk roadmap: probe optional modules
    module_map = {
        "xrechnung": ("app.integration.virtus_office.sku_xrechnung", "validate_xrechnung"),
        "zugferd": ("app.integration.virtus_office.sku_zugferd", "validate_zugferd"),
        "searchable_pdf": (
            "app.integration.virtus_office.sku_searchable_pdf",
            "validate_searchable_pdf",
        ),
        "fillable_pdf": (
            "app.integration.virtus_office.sku_fillable_pdf",
            "validate_fillable_pdf",
        ),
        "pdf_a_2b": ("app.integration.virtus_office.sku_pdf_a", "validate_pdf_a_2b"),
        "document_archive": (
            "app.integration.virtus_office.sku_document_archive",
            "validate_archive",
        ),
        "pdf_ua": ("app.integration.virtus_office.sku_pdf_ua", "validate_pdf_ua"),
    }
    if aid in module_map:
        mod_name, fn_name = module_map[aid]
        try:
            import importlib

            mod = importlib.import_module(mod_name)
            fn = getattr(mod, fn_name, None)
            enabled = bool(getattr(mod, "SKU_ENABLED", False))
            impl = bool(getattr(mod, "VALIDATOR_IMPLEMENTED", False)) and callable(fn)
            return {
                "ok": enabled and impl,
                "kind": "dedicated" if impl else "stub",
                "module": f"{mod_name}.{fn_name}",
                "sku_enabled": enabled,
                "validator_implemented": impl,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "kind": "missing",
                "module": mod_name,
                "error": str(exc)[:160],
            }
    return {"ok": False, "kind": "unknown", "module": None}


def _executor_probe(action_id: str) -> dict[str, Any]:
    aid = (action_id or "").strip().lower()
    live = aid in _executor_ids()
    if live:
        return {"ok": True, "kind": "wired", "in_executable_set": True}
    module_map = {
        "xrechnung": "app.integration.virtus_office.sku_xrechnung",
        "zugferd": "app.integration.virtus_office.sku_zugferd",
        "searchable_pdf": "app.integration.virtus_office.sku_searchable_pdf",
        "fillable_pdf": "app.integration.virtus_office.sku_fillable_pdf",
        "pdf_a_2b": "app.integration.virtus_office.sku_pdf_a",
        "document_archive": "app.integration.virtus_office.sku_document_archive",
        "pdf_ua": "app.integration.virtus_office.sku_pdf_ua",
    }
    if aid in module_map:
        try:
            import importlib

            mod = importlib.import_module(module_map[aid])
            enabled = bool(getattr(mod, "SKU_ENABLED", False))
            impl = bool(getattr(mod, "EXECUTOR_IMPLEMENTED", False))
            return {
                "ok": enabled and impl,
                "kind": "module_stub" if not impl else "module",
                "in_executable_set": False,
                "sku_enabled": enabled,
                "executor_implemented": impl,
                "module": module_map[aid],
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "kind": "missing_module",
                "in_executable_set": False,
                "error": str(exc)[:160],
            }
    return {"ok": False, "kind": "none", "in_executable_set": False}


def classify_sku(action_id: str) -> dict[str, Any]:
    aid = (action_id or "").strip().lower()
    if aid in FORBIDDEN_SKUS or aid in OFFICE_VITRINE_FORBIDDEN:
        return {
            "id": aid,
            "status": "FORBIDDEN",
            "executor": {"ok": False},
            "validator": {"ok": False},
            "vitrine": False,
            "checkout": False,
            "reason": "Product Rule / regulated or misleading offer",
        }

    ex = _executor_probe(aid)
    va = _validator_probe(aid)
    in_sellable_list = aid in OFFICE_SELLABLE_NOW
    in_catalog_sellable = any(
        row.get("id") == aid and row.get("customer_sellable") for row in ACTION_CATALOG
    )
    in_customer_exec = aid in CUSTOMER_EXECUTABLE_ACTIONS

    status: CapabilityStatus
    reason = ""
    sku_enabled = bool(ex.get("sku_enabled") or va.get("sku_enabled"))
    validator_impl = bool(va.get("validator_implemented") or (va.get("kind") == "quality_gate" and va.get("ok")))
    executor_impl = bool(ex.get("executor_implemented") or ex.get("in_executable_set"))

    if ex["ok"] and va["ok"] and in_sellable_list and in_customer_exec:
        status = "SELLABLE"
        reason = "executor + validator wired; listed in OFFICE_SELLABLE_NOW"
    elif aid in HIGH_RISK_SKUS and (sku_enabled or ex.get("in_executable_set")) and not validator_impl:
        # Enabled / wired high-risk without validator = dangerous
        status = "BLOCKED"
        reason = "high-risk: enabled/wired without PASS validator"
    elif aid in HIGH_RISK_SKUS and not sku_enabled and not ex.get("in_executable_set"):
        # Impl may exist; not sellable until SKU_ENABLED + catalog wire
        status = "ROADMAP"
        reason = (
            "Phase B impl present — SKU_ENABLED=False (not sellable)"
            if executor_impl or validator_impl
            else "contract/scaffold only — no executable wiring"
        )
    elif ex["ok"] and not va["ok"]:
        status = "BLOCKED"
        reason = "executor without adequate validator"
    elif ex["ok"] and va["ok"] and not in_sellable_list:
        status = "PARTIAL"
        reason = "code path exists but not listed sellable / catalog mismatch"
    else:
        status = "ROADMAP"
        reason = "not implemented for sale"

    # Honesty: never SELLABLE if lists disagree with probes
    if status == "SELLABLE" and (not ex["ok"] or not va["ok"]):
        status = "BLOCKED"
        reason = "SELLABLE list lied — executor/validator missing"

    vitrine = status == "SELLABLE" and aid not in FORBIDDEN_SKUS
    # Checkout path exists for office packages, but LIVE flag is separate
    checkout = vitrine  # may still be demo/sandbox until owner LIVE flip

    return {
        "id": aid,
        "status": status,
        "executor": ex,
        "validator": va,
        "listed_sellable_now": in_sellable_list,
        "catalog_customer_sellable": in_catalog_sellable,
        "customer_executable_actions": in_customer_exec,
        "vitrine": vitrine,
        "checkout": checkout,
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "high_risk": aid in HIGH_RISK_SKUS,
        "reason": reason,
    }


def audit_matrix() -> dict[str, Any]:
    """Full matrix for CEO report + /api/office/status."""
    ids: list[str] = []
    for row in ACTION_CATALOG:
        rid = str(row.get("id") or "")
        if rid and rid not in ids:
            ids.append(rid)
    for rid in OFFICE_SELLABLE_NOW:
        if rid not in ids:
            ids.append(rid)
    for rid in OFFICE_SKU_ROADMAP:
        if rid not in ids:
            ids.append(rid)
    # Alias display rows for Documents / Excel product names
    display_aliases = {
        "convert_docx": "documents_word",
        "extract_data": "excel_extract",
    }

    rows = [classify_sku(i) for i in ids]
    by_status: dict[str, list[str]] = {}
    for r in rows:
        by_status.setdefault(str(r["status"]), []).append(str(r["id"]))

    sellable = [r["id"] for r in rows if r["status"] == "SELLABLE"]
    inconsistencies: list[str] = []
    for sid in OFFICE_SELLABLE_NOW:
        c = classify_sku(sid)
        if c["status"] != "SELLABLE":
            inconsistencies.append(
                f"{sid} in OFFICE_SELLABLE_NOW but capability={c['status']}: {c['reason']}"
            )
    for r in rows:
        if r["status"] == "SELLABLE" and r["id"] not in OFFICE_SELLABLE_NOW:
            inconsistencies.append(f"{r['id']} SELLABLE but missing from OFFICE_SELLABLE_NOW")

    return {
        "product_rule": {
            "no_executor_no_sku": True,
            "no_validator_no_high_risk_sku": True,
            "no_pass_no_delivery": True,
        },
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "stripe_live": office_stripe_live(),
        "country_pricing": False,
        "sellable_skus": sellable,
        "vitrine_skus": [r["id"] for r in rows if r.get("vitrine")],
        "vitrine_forbidden": list(OFFICE_VITRINE_FORBIDDEN),
        "sku_roadmap": [
            r["id"]
            for r in rows
            if r["status"] in {"ROADMAP", "BLOCKED"} and r["id"] in OFFICE_SKU_ROADMAP
        ],
        "by_status": by_status,
        "rows": rows,
        "display_aliases": display_aliases,
        "inconsistencies": inconsistencies,
        "b2b_packages": {
            "status": "ROADMAP",
            "note": (
                "10/50 Rechnungen batches only after xrechnung/zugferd SELLABLE. "
                "No fake package SKUs."
            ),
            "planned": [
                "batch_xrechnung_10",
                "batch_xrechnung_50",
                "batch_searchable_pdf",
                "batch_document_archive",
            ],
        },
        "next_b2b_candidates": [
            "xrechnung",
            "zugferd",
        ],
        "live_gate": {
            "office_pipeline_live": OFFICE_PIPELINE_LIVE,
            "required_before_flip": [
                "Owner E2E: upload→pay→execute→PASS→cabinet→email for each SELLABLE SKU",
                "Stripe live decision (manual)",
                "No inconsistencies in capability audit",
                "Businessplan Commercial PASS if selling BP translation at scale",
            ],
            "auto_flip_forbidden": True,
        },
    }


def report_table() -> list[dict[str, str]]:
    """CEO table rows."""
    order = [
        "translate",
        "convert_docx",
        "extract_data",
        "lebenslauf_create",
        "bewerbung_paket",
        "document_quality_check",
        "xrechnung",
        "zugferd",
        "searchable_pdf",
        "fillable_pdf",
        "pdf_a_2b",
        "document_archive",
        "pdf_ua",
    ]
    out: list[dict[str, str]] = []
    for sid in order:
        c = classify_sku(sid)
        out.append(
            {
                "sku": sid,
                "executor": "YES" if c["executor"].get("ok") else "NO",
                "validator": "YES" if c["validator"].get("ok") else "NO",
                "e2e": "CODE" if c["status"] == "SELLABLE" else "—",
                "payment": "YES*" if c.get("checkout") else "NO",
                "delivery": "ON_PASS" if c["status"] == "SELLABLE" else "NO",
                "status": str(c["status"]),
                "reason": str(c.get("reason") or ""),
            }
        )
    return out
