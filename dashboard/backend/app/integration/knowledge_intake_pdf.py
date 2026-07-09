"""Knowledge Intake — PDF source (AI-1)."""

from __future__ import annotations

import logging
from pathlib import Path

from app.integration.attachment_policy import AttachmentPolicy, AttachmentTier
from app.integration.knowledge_intake import IntakeDescriptor, IntakeResult, IntakeSourceKind

logger = logging.getLogger(__name__)

_MAX_PROMPT_CHARS = 14_000


def extract_pdf_text(path: Path, *, max_pages: int) -> tuple[str, int, int]:
    """Return (text, total_pages, pages_included)."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
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
    if len(text) > _MAX_PROMPT_CHARS:
        text = text[:_MAX_PROMPT_CHARS].rstrip() + "\n…[текст обрезан по лимиту контекста]"
    return text, total, take


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
