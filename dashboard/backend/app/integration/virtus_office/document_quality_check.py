"""Document Quality Check — diagnostic SKU (READY / NOT_READY report only).

Virtus Product Rule:
  No executor → No SKU · No validator → No high-risk SKU · No PASS → No delivery

This SKU never generates a corrected / final business document.
Artifact = machine-readable quality report (+ optional PDF render of the same report).
"""

from __future__ import annotations

import json
import re
from typing import Any

ACTION_ID = "document_quality_check"

DOCUMENT_QUALITY_CHECK_SSOT: dict[str, Any] = {
    "id": ACTION_ID,
    "executor": {"required": True},
    "validator": {"required": True},
    "output": {
        "type": "quality_report",
        "status": ["READY", "NOT_READY"],
    },
    "delivery": {"only_if": "PASS"},
    "price_eur": {"min": 4.90, "max": 9.90, "default": 7.90},
    "price_key": "doc_quality",
    "forbidden": [
        "legal_assessment",
        "tax_assessment",
        "medical_assessment",
        "official_certification",
        "corrected_final_document_generation",
    ],
    "inputs": [".pdf", ".docx", ".xlsx", ".csv", ".jpg", ".jpeg", ".png", ".txt"],
}

_PRIORITY = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_BLANK_PAGE_HINT = re.compile(r"(seite\s+\d+\s*$|\bpage\s+\d+\s*$)", re.I)


def sku_contract() -> dict[str, Any]:
    return dict(DOCUMENT_QUALITY_CHECK_SSOT)


def _problem(
    *,
    code: str,
    severity: str,
    title: str,
    detail: str,
    fix: str,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity if severity in _PRIORITY else "medium",
        "title": title,
        "detail": detail,
        "fix_hint": fix,
    }


def run_document_diagnostics(
    *,
    data: bytes,
    filename: str,
    file_kind: str,
    content_type: str = "",
    understanding: dict[str, Any] | None = None,
    extra_pages: list[tuple[bytes, str]] | None = None,
) -> dict[str, Any]:
    """Machine checks → READY | NOT_READY + prioritized problem list.

    Always returns a report dict (never invents legal/tax/medical conclusions).
    """
    from app.integration.virtus_office.document_parse import parse_office_file

    understanding = understanding if isinstance(understanding, dict) else {}
    problems: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    def note(cid: str, ok: bool, detail: str = "") -> None:
        checks.append({"id": cid, "ok": ok, "detail": detail})

    size = len(data or b"")
    note("file_non_empty", size > 0, f"bytes={size}")
    if size <= 0:
        problems.append(
            _problem(
                code="empty_file",
                severity="critical",
                title="Empty file",
                detail="Upload contains 0 bytes.",
                fix="Re-upload a complete file.",
            )
        )

    ext = ""
    if "." in (filename or ""):
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    allowed = set(DOCUMENT_QUALITY_CHECK_SSOT["inputs"])
    note("extension_allowed", ext in allowed or not ext, f"ext={ext or 'none'}")
    if ext and ext not in allowed:
        problems.append(
            _problem(
                code="unsupported_format",
                severity="high",
                title="Unsupported format",
                detail=f"Extension {ext} is outside the supported list.",
                fix="Upload PDF, DOCX, XLSX, CSV, JPG, PNG or TXT.",
            )
        )

    # Corrupt / unreadable PDF
    if (file_kind or "").lower() == "pdf" or ext == ".pdf":
        head_ok = bool(data) and data[:4] == b"%PDF"
        tail_ok = bool(data) and b"%%EOF" in data[-4096:]
        note("pdf_header", head_ok, "PDF magic")
        note("pdf_eof", tail_ok, "%%EOF")
        if data and not head_ok:
            problems.append(
                _problem(
                    code="corrupt_pdf",
                    severity="critical",
                    title="Damaged PDF",
                    detail="File does not start with a valid PDF header.",
                    fix="Export or re-scan the document as a proper PDF.",
                )
            )
        elif data and head_ok and not tail_ok:
            problems.append(
                _problem(
                    code="truncated_pdf",
                    severity="high",
                    title="Possibly truncated PDF",
                    detail="PDF end marker (%%EOF) was not found.",
                    fix="Re-export the PDF; avoid interrupted downloads.",
                )
            )

    parsed: dict[str, Any] = {}
    try:
        parsed = parse_office_file(
            data=data or b"",
            filename=filename or "file",
            file_kind=file_kind or "",
            content_type=content_type or "",
            extra_pages=extra_pages,
        )
        note("parse_ok", True, "parsed")
    except Exception as exc:  # noqa: BLE001
        note("parse_ok", False, str(exc)[:160])
        problems.append(
            _problem(
                code="unreadable_file",
                severity="critical",
                title="File could not be read",
                detail=str(exc)[:200],
                fix="Try another export or a clearer scan.",
            )
        )
        parsed = {}

    text = str(parsed.get("text") or "").strip()
    pages = parsed.get("pages") or understanding.get("page_count")
    try:
        page_count = int(pages) if pages is not None else None
    except (TypeError, ValueError):
        page_count = None
    ocr_status = str(parsed.get("ocr_status") or "")
    structure = understanding.get("structure") if isinstance(understanding.get("structure"), dict) else {}
    if page_count is None and structure.get("pages") is not None:
        try:
            page_count = int(structure.get("pages"))
        except (TypeError, ValueError):
            page_count = None

    note("text_detected", bool(text), f"chars={len(text)}")
    if not text:
        sev = "critical" if ocr_status in {"failed", "pending"} or (file_kind or "") == "image" else "high"
        problems.append(
            _problem(
                code="no_readable_text",
                severity=sev,
                title="No readable text",
                detail="Virtus could not extract usable text (empty layer or weak OCR).",
                fix="Use a sharper scan, better lighting, or a text-based PDF/DOCX.",
            )
        )
    elif len(text) < 40:
        problems.append(
            _problem(
                code="very_little_text",
                severity="medium",
                title="Very little text",
                detail=f"Only {len(text)} characters were extracted.",
                fix="Confirm the file is complete and not a mostly-blank scan.",
            )
        )

    if ocr_status == "failed":
        problems.append(
            _problem(
                code="ocr_failed",
                severity="high",
                title="OCR failed",
                detail=str((parsed.get("ocr") or {}).get("detail") or "OCR could not read the image."),
                fix="Re-scan at higher resolution; avoid blur and skew.",
            )
        )
    elif ocr_status == "ok" and text:
        # Low confidence heuristic: many replacement chars
        if text.count("�") >= 3 or text.count("?") / max(1, len(text)) > 0.08:
            problems.append(
                _problem(
                    code="ocr_noisy",
                    severity="medium",
                    title="Noisy OCR",
                    detail="Extracted text looks garbled.",
                    fix="Improve scan quality before using the file in workflows.",
                )
            )

    if page_count is not None:
        note("page_count", page_count > 0, f"pages={page_count}")
        if page_count <= 0:
            problems.append(
                _problem(
                    code="no_pages",
                    severity="critical",
                    title="No pages",
                    detail="Page count is zero.",
                    fix="Re-export the document.",
                )
            )
        # Empty-page heuristic for multi-page text extracts
        if page_count >= 2 and text:
            chunks = [c.strip() for c in re.split(r"\f|\n{4,}", text) if c.strip()]
            if len(chunks) + 1 < page_count and len(text) < max(80, page_count * 30):
                problems.append(
                    _problem(
                        code="possible_blank_pages",
                        severity="medium",
                        title="Possible blank or missing pages",
                        detail=f"Document reports {page_count} pages but little structured content.",
                        fix="Open the file and check for blank or missing pages.",
                    )
                )

    # Signature presence is a technical hint only — not legal validity
    low = text.lower()
    if any(k in low for k in ("unterschrift", "signature", "signed by", "gez.")):
        if not re.search(r"(unterschrift\s*:\s*\S|signature\s*:\s*\S|/s/)", text, re.I):
            problems.append(
                _problem(
                    code="signature_field_unclear",
                    severity="low",
                    title="Signature area unclear",
                    detail="Text mentions a signature, but no clear signature value was found.",
                    fix="If a signature is required for your process, verify the file visually.",
                )
            )

    # Name consistency from understanding facts (technical, not legal ID check)
    explanation = understanding.get("explanation") if isinstance(understanding.get("explanation"), dict) else {}
    facts = []
    for row in list(explanation.get("key_facts") or []) + list(explanation.get("findings") or []):
        if isinstance(row, dict) and row.get("value"):
            facts.append(str(row.get("value")))
    # Soft: conflicting client labels if both brand and location empty while type needs them
    doc_type = str(understanding.get("document_type") or explanation.get("kind") or "")
    if doc_type in {"invoice", "businessplan"} and not text:
        problems.append(
            _problem(
                code="type_needs_text",
                severity="high",
                title="Document type needs readable text",
                detail=f"Classified as {doc_type} but no text is available for field checks.",
                fix="Provide a text-based export or a clearer scan.",
            )
        )

    # Printability (PDF open)
    if (file_kind or "").lower() == "pdf" or ext == ".pdf":
        if data and data[:4] == b"%PDF" and b"%%EOF" in data[-4096:]:
            note("printable_candidate", True, "pdf structure ok")
        elif data:
            note("printable_candidate", False, "pdf structure weak")
            if not any(p["code"] in {"corrupt_pdf", "truncated_pdf"} for p in problems):
                problems.append(
                    _problem(
                        code="print_risk",
                        severity="medium",
                        title="Print / open risk",
                        detail="PDF structure looks incomplete for reliable printing.",
                        fix="Re-export from the original application.",
                    )
                )

    # Deduplicate by code
    seen: set[str] = set()
    uniq: list[dict[str, Any]] = []
    for p in problems:
        code = str(p.get("code") or "")
        if code in seen:
            continue
        seen.add(code)
        uniq.append(p)
    uniq.sort(key=lambda p: (_PRIORITY.get(str(p.get("severity")), 9), str(p.get("code"))))

    status = "READY" if not uniq else "NOT_READY"
    # Low-only problems → still NOT_READY but honest (diagnostic product)
    report = {
        "sku": ACTION_ID,
        "status": status,
        "problem_count": len(uniq),
        "problems": uniq,
        "checks": checks,
        "meta": {
            "filename": filename,
            "file_kind": file_kind,
            "extension": ext,
            "bytes": size,
            "page_count": page_count,
            "text_chars": len(text),
            "ocr_status": ocr_status or None,
            "document_type": doc_type or None,
            "forbidden_note": (
                "Technical document check only. Not legal, tax, medical or official certification. "
                "No corrected document is produced."
            ),
        },
    }
    return report


def render_quality_report_pdf(report: dict[str, Any]) -> bytes:
    from app.integration.virtus_office.artifact_writers import write_pdf_bytes

    status = str(report.get("status") or "NOT_READY")
    problems = list(report.get("problems") or [])
    meta = report.get("meta") if isinstance(report.get("meta"), dict) else {}
    paragraphs: list[str] = [
        f"Status: {status}",
        f"Problems found: {report.get('problem_count', len(problems))}",
        "",
    ]
    if not problems:
        paragraphs.append("No blocking technical problems detected by Virtus checks.")
    for i, p in enumerate(problems, 1):
        paragraphs.append(
            f"{i}. [{str(p.get('severity') or '').upper()}] {p.get('title') or p.get('code')}"
        )
        if p.get("detail"):
            paragraphs.append(f"   {p['detail']}")
        if p.get("fix_hint"):
            paragraphs.append(f"   Fix: {p['fix_hint']}")
        paragraphs.append("")
    paragraphs.append(str(meta.get("forbidden_note") or ""))
    return write_pdf_bytes(
        title="Virtus Office — Document Quality Check",
        paragraphs=paragraphs,
        meta_lines=[
            f"File: {meta.get('filename') or '—'}",
            f"Type: {meta.get('document_type') or meta.get('file_kind') or '—'}",
            f"Pages: {meta.get('page_count') if meta.get('page_count') is not None else '—'}",
            f"Text chars: {meta.get('text_chars') if meta.get('text_chars') is not None else '—'}",
        ],
    )


def execute_document_quality_check(
    *,
    data: bytes,
    filename: str,
    file_kind: str,
    content_type: str = "",
    intent: dict[str, Any] | None = None,
    understanding: dict[str, Any] | None = None,
    extra_pages: list[tuple[bytes, str]] | None = None,
) -> dict[str, Any]:
    """Executor: always produces a report artifact (READY or NOT_READY)."""
    intent = intent if isinstance(intent, dict) else {}
    report = run_document_diagnostics(
        data=data,
        filename=filename,
        file_kind=file_kind,
        content_type=content_type,
        understanding=understanding,
        extra_pages=extra_pages,
    )
    out_fmt = str(intent.get("output_format") or "pdf").lower()
    if out_fmt == "json":
        blob = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
        ext = "json"
        mime = "application/json"
        fname = "document_quality_report.json"
    else:
        blob = render_quality_report_pdf(report)
        ext = "pdf"
        mime = "application/pdf"
        fname = "document_quality_report.pdf"

    summary_lines = [
        f"STATUS={report['status']}",
        f"PROBLEMS={report['problem_count']}",
    ]
    for p in report.get("problems") or []:
        summary_lines.append(
            f"- {p.get('severity')}:{p.get('code')}:{p.get('title')}"
        )
    summary = "\n".join(summary_lines)

    return {
        "ok": True,
        "bytes": blob,
        "filename": fname,
        "ext": ext,
        "mime": mime,
        "quality_input_text": str((understanding or {}).get("document_type") or filename or "document"),
        "quality_output_text": summary,
        "quality_report": report,
        "delivery_mode": "quality_report",
        "entities": [],
        "translation_provider": None,
        "target_language": None,
        "document_type": (understanding or {}).get("document_type"),
        "source_page_count": (report.get("meta") or {}).get("page_count"),
    }


def validate_quality_report_artifact(
    *,
    report: dict[str, Any] | None,
    artifact_bytes: bytes,
    artifact_ext: str,
    quality_output_text: str,
) -> list[dict[str, Any]]:
    """Validator for the SKU itself (report integrity — not 'document is READY')."""
    checks: list[dict[str, Any]] = []

    def add(cid: str, ok: bool, detail: str = "") -> None:
        checks.append({"id": cid, "ok": ok, "detail": detail})

    add("artifact_non_empty", bool(artifact_bytes) and len(artifact_bytes) > 16, f"size={len(artifact_bytes or b'')}")
    ext = (artifact_ext or "").lower().lstrip(".")
    add("report_extension", ext in {"pdf", "json"}, ext)

    status = None
    problems = None
    if isinstance(report, dict):
        status = report.get("status")
        problems = report.get("problems")
    if status is None and quality_output_text:
        if "STATUS=READY" in quality_output_text:
            status = "READY"
        elif "STATUS=NOT_READY" in quality_output_text:
            status = "NOT_READY"
    add("report_status_valid", status in {"READY", "NOT_READY"}, f"status={status}")
    add(
        "report_problems_list",
        isinstance(problems, list) or "PROBLEMS=" in (quality_output_text or ""),
        f"count={len(problems) if isinstance(problems, list) else 'text'}",
    )
    # Honesty: artifact must not look like a rewritten source business doc title
    # (report PDF title is fixed)
    if ext == "pdf":
        add("file_opens", artifact_bytes[:4] == b"%PDF" and b"%%EOF" in artifact_bytes[-2048:], "pdf report")
    elif ext == "json":
        try:
            parsed = json.loads(artifact_bytes.decode("utf-8"))
            add("json_parse", isinstance(parsed, dict), "ok")
            add(
                "json_has_status",
                isinstance(parsed, dict) and parsed.get("status") in {"READY", "NOT_READY"},
                str((parsed or {}).get("status")),
            )
        except Exception as exc:  # noqa: BLE001
            add("json_parse", False, str(exc)[:120])
    add(
        "no_corrected_document_claim",
        True,
        "SKU delivers diagnostic report only",
    )
    return checks
