"""Translation Pack — one-time 19.90 € wrapping translate executor.

Supports primary file + optional extra files into one ZIP.
Plain chat text translation stays FREE (not this SKU).
"""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any

SKU_ID = "translation_pack"
SKU_ENABLED = True
EXECUTOR_IMPLEMENTED = True
VALIDATOR_IMPLEMENTED = True
MAX_FILES = 5

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": False,
    "output": "ZIP of translated PDF/DOCX files",
    "validation": ["zip_has_files", "target_language_set"],
    "price_eur_hint": {"min": 19.90, "max": 19.90},
    "price_key": "translation_pack",
}


def validate_translation_pack_zip(data: bytes) -> dict[str, Any]:
    problems: list[str] = []
    if not data.startswith(b"PK"):
        return {"ok": False, "problems": ["not_zip"]}
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if len(names) < 2:
                problems.append("too_few_files")
            if "manifest.json" not in names:
                problems.append("missing_manifest")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "problems": [f"zip_error:{exc}"]}
    return {"ok": not problems, "problems": problems}


def execute_translation_pack(
    *,
    data: bytes,
    filename: str,
    file_kind: str,
    content_type: str,
    intent: dict[str, Any],
    understanding: dict[str, Any],
    extra_pages: list[tuple[bytes, str]] | None = None,
) -> dict[str, Any]:
    from app.integration.virtus_office.execution import execute_office_action

    target = str((intent or {}).get("target_language") or "").strip()
    if not target:
        return {"ok": False, "error": "missing_target_language", "detail": "target_language required"}

    jobs: list[tuple[bytes, str, str, str]] = [
        (data, filename, file_kind, content_type),
    ]
    for i, (blob, name) in enumerate((extra_pages or [])[: MAX_FILES - 1]):
        ext = (name.rsplit(".", 1)[-1] if "." in name else "pdf").lower()
        kind = (
            "pdf"
            if ext == "pdf"
            else "docx"
            if ext == "docx"
            else "image"
            if ext in {"jpg", "jpeg", "png"}
            else file_kind
        )
        jobs.append((blob, name or f"file_{i + 2}.{ext}", kind, "application/octet-stream"))

    results: list[dict[str, Any]] = []
    files: list[tuple[str, bytes]] = []
    for blob, name, kind, mime in jobs[:MAX_FILES]:
        res = execute_office_action(
            action_id="translate",
            data=blob,
            filename=name,
            file_kind=kind,
            content_type=mime,
            intent=intent,
            understanding=understanding,
        )
        ok = bool(res.get("ok"))
        entry = {"file": name, "ok": ok, "error": res.get("error"), "detail": res.get("detail")}
        if ok and res.get("bytes"):
            out_name = str(res.get("filename") or f"translated_{name}")
            files.append((out_name, bytes(res["bytes"])))
            entry["filename"] = out_name
        results.append(entry)

    passed = [r for r in results if r.get("ok")]
    if not passed:
        return {
            "ok": False,
            "error": "translation_pack_failed",
            "detail": "No file translated",
            "results": results,
        }

    manifest = {
        "product": SKU_ID,
        "target_language": target,
        "results": results,
        "honesty": "Translation of provided files only. Not a sworn/certified translation.",
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for path, blob in files:
            zf.writestr(path, blob)
    zip_bytes = buf.getvalue()
    validation = validate_translation_pack_zip(zip_bytes)
    if not validation.get("ok"):
        return {
            "ok": False,
            "error": "translation_pack_validation_failed",
            "detail": ",".join(validation.get("problems") or []),
            "validation": validation,
            "results": results,
        }
    return {
        "ok": True,
        "action_id": SKU_ID,
        "mime": "application/zip",
        "filename": "virtus-translation-pack.zip",
        "bytes": zip_bytes,
        "results": results,
        "validation": validation,
    }
