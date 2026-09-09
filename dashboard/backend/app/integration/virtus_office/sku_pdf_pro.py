"""PDF PRO package — one-time 29.90 € wrapping LIVE PDF executors.

User selects which ops to run (subset of wraps). Output = ZIP of PASS artifacts.
No veraPDF / ISO certification claims.
"""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any

SKU_ID = "pdf_pro"
SKU_ENABLED = True
EXECUTOR_IMPLEMENTED = True
VALIDATOR_IMPLEMENTED = True

ALLOWED_OPS = (
    "searchable_pdf",
    "redaction",
    "fillable_pdf",
    "pdf_a_2b",
    "document_archive",
    "document_quality_check",
)

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "ZIP of selected PDF tool outputs + quality reports",
    "validation": ["zip_has_files", "each_child_pass"],
    "not_enough": ["verapdf_certificate", "iso_certification", "legal_advice"],
    "price_eur_hint": {"min": 29.90, "max": 29.90},
    "price_key": "pdf_pro",
}


def _normalize_ops(raw: Any) -> list[str]:
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
    elif isinstance(raw, list):
        parts = [str(p).strip() for p in raw]
    else:
        parts = []
    out: list[str] = []
    for p in parts:
        if p in ALLOWED_OPS and p not in out:
            out.append(p)
    return out or ["searchable_pdf", "document_quality_check"]


def validate_pdf_pro_zip(data: bytes, *, expected_ops: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    if not data.startswith(b"PK"):
        return {"ok": False, "problems": ["not_zip"]}
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            names = zf.namelist()
            if not names:
                problems.append("empty_zip")
            if "manifest.json" not in names:
                problems.append("missing_manifest")
            else:
                man = json.loads(zf.read("manifest.json").decode("utf-8"))
                results = list(man.get("results") or [])
                for op in expected_ops:
                    row = next((r for r in results if r.get("op") == op), None)
                    if not row:
                        problems.append(f"missing_op:{op}")
                    elif not row.get("ok"):
                        problems.append(f"op_failed:{op}")
            if len(names) < 2:
                problems.append("too_few_files")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "problems": [f"zip_error:{exc}"]}
    return {"ok": not problems, "problems": problems}


def execute_pdf_pro(
    *,
    data: bytes,
    filename: str,
    file_kind: str,
    content_type: str,
    intent: dict[str, Any],
    understanding: dict[str, Any],
    extra_pages: list[tuple[bytes, str]] | None = None,
) -> dict[str, Any]:
    ops = _normalize_ops((intent or {}).get("pdf_pro_ops") or (intent or {}).get("ops"))
    results: list[dict[str, Any]] = []
    files: list[tuple[str, bytes]] = []

    for op in ops:
        try:
            if op == "searchable_pdf":
                from app.integration.virtus_office.sku_searchable_pdf import execute_searchable_pdf

                res = execute_searchable_pdf(
                    data=data,
                    filename=filename,
                    file_kind=file_kind,
                    content_type=content_type,
                    intent=intent,
                    understanding=understanding,
                    extra_pages=extra_pages,
                )
            elif op == "redaction":
                from app.integration.virtus_office.sku_redaction import execute_redaction

                res = execute_redaction(
                    data=data,
                    filename=filename,
                    file_kind=file_kind,
                    content_type=content_type,
                    intent=intent,
                    understanding=understanding,
                    extra_pages=extra_pages,
                )
            elif op == "fillable_pdf":
                from app.integration.virtus_office.sku_fillable_pdf import execute_fillable_pdf

                res = execute_fillable_pdf(
                    data=data,
                    filename=filename,
                    file_kind=file_kind,
                    content_type=content_type,
                    intent=intent,
                    understanding=understanding,
                    extra_pages=extra_pages,
                )
            elif op == "pdf_a_2b":
                from app.integration.virtus_office.sku_pdf_a import execute_pdf_a_2b

                res = execute_pdf_a_2b(
                    data=data,
                    filename=filename,
                    file_kind=file_kind,
                    content_type=content_type,
                    intent=intent,
                    understanding=understanding,
                    extra_pages=extra_pages,
                )
            elif op == "document_archive":
                from app.integration.virtus_office.sku_document_archive import (
                    execute_document_archive,
                )

                res = execute_document_archive(
                    data=data,
                    filename=filename,
                    file_kind=file_kind,
                    content_type=content_type,
                    intent=intent,
                    understanding=understanding,
                    extra_pages=extra_pages,
                )
            elif op == "document_quality_check":
                from app.integration.virtus_office.document_quality_check import (
                    execute_document_quality_check,
                )

                res = execute_document_quality_check(
                    data=data,
                    filename=filename,
                    file_kind=file_kind,
                    content_type=content_type,
                    intent=intent,
                    understanding=understanding,
                    extra_pages=extra_pages,
                )
            else:
                res = {"ok": False, "error": "unknown_op", "detail": op}
        except Exception as exc:  # noqa: BLE001
            res = {"ok": False, "error": "executor_exception", "detail": str(exc)}

        ok = bool(res.get("ok"))
        entry: dict[str, Any] = {
            "op": op,
            "ok": ok,
            "error": res.get("error"),
            "detail": res.get("detail"),
        }
        if ok:
            out_name = str(res.get("filename") or f"{op}.bin")
            out_bytes = res.get("bytes")
            if isinstance(out_bytes, (bytes, bytearray)) and out_bytes:
                files.append((f"{op}/{out_name}", bytes(out_bytes)))
                entry["filename"] = out_name
            for art in res.get("artifacts") or []:
                if isinstance(art, dict) and art.get("bytes") and art.get("filename"):
                    files.append((f"{op}/{art['filename']}", bytes(art["bytes"])))
        results.append(entry)

    passed = [r for r in results if r.get("ok")]
    if not passed:
        return {
            "ok": False,
            "error": "pdf_pro_all_failed",
            "detail": "No PDF PRO operation produced a valid artifact",
            "results": results,
        }

    manifest = {
        "product": SKU_ID,
        "ops_requested": ops,
        "results": results,
        "honesty": (
            "Technical PDF processing only. No veraPDF certificate, "
            "no ISO certification, no legal advice."
        ),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for path, blob in files:
            zf.writestr(path, blob)
    zip_bytes = buf.getvalue()
    validation = validate_pdf_pro_zip(zip_bytes, expected_ops=[r["op"] for r in passed])
    if not validation.get("ok"):
        return {
            "ok": False,
            "error": "pdf_pro_validation_failed",
            "detail": ",".join(validation.get("problems") or []),
            "results": results,
            "validation": validation,
        }

    return {
        "ok": True,
        "action_id": SKU_ID,
        "mime": "application/zip",
        "filename": "virtus-pdf-pro.zip",
        "bytes": zip_bytes,
        "results": results,
        "validation": validation,
    }
