"""Knowledge Intake — PDF source (AI-1)."""

from __future__ import annotations

import logging
from pathlib import Path

from app.integration.attachment_policy import AttachmentPolicy, AttachmentTier
from app.integration.knowledge_intake import IntakeDescriptor, IntakeResult, IntakeSourceKind

logger = logging.getLogger(__name__)

_MAX_PROMPT_CHARS = 14_000


def extract_pdf_text(
    path: Path,
    *,
    max_pages: int,
    max_chars: int | None = _MAX_PROMPT_CHARS,
) -> tuple[str, int, int]:
    """Return (text, total_pages, pages_included). Tries pypdf (non-strict) first.

    max_chars defaults to Knowledge Intake prompt budget (14k). Pass None for
    full Virtus Office extraction (no silent truncation).
    """
    from pypdf import PdfReader

    last_error: Exception | None = None
    for strict in (False, True):
        try:
            reader = PdfReader(str(path), strict=strict)
            total = len(reader.pages)
            take = max(0, min(total, max_pages))
            parts: list[str] = []
            for i in range(take):
                try:
                    page_text = reader.pages[i].extract_text() or ""
                except (OSError, ValueError, KeyError) as exc:
                    logger.warning("PDF page %s extract failed: %s", i, exc)
                    page_text = ""
                if page_text.strip():
                    parts.append(page_text.strip())
            text = "\n\n".join(parts).strip()
            if max_chars is not None and len(text) > max_chars:
                text = text[:max_chars].rstrip() + "\n…[текст обрезан по лимиту контекста]"
            if text.strip():
                return text, total, take
            # Empty text but readable PDF — still return page counts (scan / image-only).
            if total > 0:
                return "", total, take
        except Exception as exc:
            last_error = exc
            logger.warning("PDF read failed (strict=%s): %s", strict, exc)
    raise ValueError(f"pdf parse error: {last_error or 'no extractable text'}")


def extract_pdf_text_bytes(
    data: bytes,
    *,
    max_pages: int = 20,
    max_chars: int | None = _MAX_PROMPT_CHARS,
) -> tuple[str, int, int]:
    """Same as extract_pdf_text for in-memory bytes (Virtus Office reuse)."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        path = Path(tmp.name)
    try:
        return extract_pdf_text(path, max_pages=max_pages, max_chars=max_chars)
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


class AttachmentPdfSource:
    kind: IntakeSourceKind = "attachment"

    def can_handle(self, descriptor: IntakeDescriptor) -> bool:
        mime = (descriptor.content_type or "").split(";")[0].strip().lower()
        return mime == "application/pdf" and descriptor.path is not None

    def ingest(
        self,
        descriptor: IntakeDescriptor,
        *,
        memory_dir: Path | None = None,
        tier: AttachmentTier = "free",
        max_pages: int = 5,
        **_kwargs: object,
    ) -> IntakeResult:
        path = descriptor.path
        if not path or not path.is_file():
            return IntakeResult(
                status="denied",
                kind="attachment",
                reason="pdf file not found",
            )

        policy = AttachmentPolicy(memory_dir=memory_dir)
        parse_check = policy.check_parse(
            tier=tier,
            content_type=descriptor.content_type or "application/pdf",
        )
        if not parse_check.allowed:
            return IntakeResult(
                status="denied",
                kind="attachment",
                reason=parse_check.reason or "pdf parse not allowed",
            )

        limits = policy.limits_for(tier)
        page_cap = min(max_pages, limits.max_parsed_pages_per_day or max_pages)
        try:
            text, total, included = extract_pdf_text(path, max_pages=page_cap)
        except Exception as exc:
            logger.warning("PDF parse failed: %s", exc)
            return IntakeResult(
                status="unsupported",
                kind="attachment",
                reason=f"pdf parse error: {exc}",
            )

        if not text.strip():
            return IntakeResult(
                status="unsupported",
                kind="attachment",
                reason="no extractable text in pdf",
                page_count=total,
                pages_included=included,
            )

        return IntakeResult(
            status="parsed",
            kind="attachment",
            text_excerpt=text,
            page_count=total,
            pages_included=included,
            metadata={
                "filename": descriptor.label or path.name,
                "attachment_id": descriptor.extra.get("attachment_id"),
            },
        )
