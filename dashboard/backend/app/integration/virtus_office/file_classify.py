"""Classify Office uploads by extension + MIME (no second storage)."""

from __future__ import annotations

from pathlib import Path

from app.integration.virtus_office.office_job_ssot import (
    OFFICE_ALLOWED_EXT,
    OFFICE_EXT_TO_KIND,
    OFFICE_GENERIC_MIME,
    OFFICE_KIND_MIMES,
)


def normalize_content_type(content_type: str | None) -> str:
    raw = (content_type or "").split(";")[0].strip().lower()
    if raw == "image/jpg":
        return "image/jpeg"
    return raw


def classify_office_file(
    *,
    filename: str,
    content_type: str | None,
    size: int,
) -> tuple[str | None, str | None]:
    """Return (file_kind, failure_reason). failure_reason set ⇒ reject."""
    if size <= 0:
        return None, "empty_file"

    name = Path(filename or "file").name
    ext = Path(name).suffix.lower()
    mime = normalize_content_type(content_type)

    if ext not in OFFICE_ALLOWED_EXT:
        return None, "unsupported_type"

    kind = OFFICE_EXT_TO_KIND[ext]
    allowed_mimes = OFFICE_KIND_MIMES[kind]

    if mime in OFFICE_GENERIC_MIME:
        return kind, None

    # openxml prefix soft-match for docx/xlsx
    if kind in {"docx", "xlsx"} and mime.startswith("application/vnd.openxmlformats"):
        return kind, None

    if mime.startswith("image/") and kind == "image":
        if mime in allowed_mimes or mime in {"image/jpeg", "image/png"}:
            return kind, None
        return None, "mime_ext_mismatch"

    if mime not in allowed_mimes:
        return None, "mime_ext_mismatch"

    return kind, None
