"""Knowledge Intake — orchestration for chat (AI-1 PDF + session follow-up)."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from app.integration.attachment_policy import AttachmentPolicy, AttachmentTier, resolve_attachment_tier
from app.integration.chat_sessions import ChatSessionStore
from app.integration.feature_registry import FeatureRegistry
from app.integration.knowledge_intake import IntakeDescriptor, KnowledgeIntakeRegistry
from app.integration.knowledge_intake_pdf import AttachmentPdfSource
from app.integration.knowledge_intake_transparency import (
    build_user_attachment_ack,
    transparency_enabled,
)
from app.integration.locale_service import localized_service_copy, resolve_locale
from app.integration.public_chat_attachments import PublicChatAttachmentService


def _safe_id(raw: str) -> str:
    return re.sub(r"[^\w\-]", "_", raw)[:64] or "anonymous"


class KnowledgeIntakeService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory_dir = memory_dir
        self._attachments = PublicChatAttachmentService(memory_dir)
        self._sessions = ChatSessionStore(memory_dir)
        self._policy = AttachmentPolicy(memory_dir=memory_dir)
        self._registry = KnowledgeIntakeRegistry()
        self._registry.register(AttachmentPdfSource())
        self._parse_quota_dir = memory_dir / "public_chat_uploads" / "parse_quotas"
        self._parse_quota_dir.mkdir(parents=True, exist_ok=True)

    def pdf_enabled(self) -> bool:
        return FeatureRegistry(memory_dir=self._memory_dir).is_enabled("attachment_pdf")

    def prepare_for_chat(
        self,
        *,
        attachment_ids: list[str] | None,
        visitor_id: str | None,
        session_id: str | None,
    ) -> list[dict[str, Any]]:
        vid = _safe_id(visitor_id or "anonymous")
        tier = resolve_attachment_tier(visitor_id=vid)
        files: list[dict[str, Any]] = []

        if session_id:
            files.extend(self._session_intake_files(session_id))

        seen: set[str] = set()
        for f in files:
            if f.get("id"):
                seen.add(str(f["id"]))

        for aid in attachment_ids or []:
            if aid in seen:
                continue
            row = self._parse_attachment(aid, visitor_id=vid, tier=tier)
            if row:
                files.append(row)
                seen.add(aid)

        if session_id and files:
            self._persist_session_intake(session_id, files)

        return files

    def build_brain_intake_context(
        self,
        files: list[dict[str, Any]],
        *,
        locale: str | None = None,
    ) -> str:
        if not files:
            return ""
        loc = resolve_locale(locale)
        parsed = [f for f in files if (f.get("parsed_excerpt") or "").strip()]
        if not parsed:
            if transparency_enabled(self._memory_dir):
                from app.integration.knowledge_intake_transparency import build_brain_attachment_note

                return build_brain_attachment_note(files, memory_dir=self._memory_dir, locale=loc)
            lines = [f"• {f.get('filename', 'file')}" for f in files]
            return "Attachments:\n" + "\n".join(lines)

        rules = localized_service_copy("intake_pdf_brain_rules", loc)
        blocks: list[str] = [rules, ""]
        for f in parsed:
            name = f.get("filename") or "document.pdf"
            inc = f.get("pages_included") or "?"
            total = f.get("page_count") or "?"
            blocks.append(f"--- PDF: {name} (pages {inc}/{total}) ---")
            blocks.append(str(f.get("parsed_excerpt") or ""))
            blocks.append("")
        return "\n".join(blocks).strip()

    def build_user_ack(
        self,
        files: list[dict[str, Any]],
        *,
        locale: str | None = None,
    ) -> str:
        if not files:
            return ""
        loc = resolve_locale(locale)
        parsed = [f for f in files if (f.get("parsed_excerpt") or "").strip()]
        if parsed:
            names = ", ".join(str(f.get("filename") or "file") for f in parsed[:3])
            if len(parsed) > 3:
                names += "…"
            pages = parsed[0].get("pages_included")
            total = parsed[0].get("page_count")
            msg = localized_service_copy("attachment_ack_pdf_read", loc)
            return (
                msg.replace("{{files}}", names)
                .replace("{{pages}}", str(pages or "?"))
                .replace("{{total}}", str(total or "?"))
            )
        return build_user_attachment_ack(files, memory_dir=self._memory_dir, locale=loc)

    def _parse_attachment(
        self, attachment_id: str, *, visitor_id: str, tier: AttachmentTier
    ) -> dict[str, Any] | None:
        meta = self._attachments.get_meta(attachment_id)
        if not meta:
            return None
        base = {
            "id": attachment_id,
            "filename": meta.get("filename") or "file",
            "content_type": meta.get("content_type") or "",
            "parsed_excerpt": meta.get("parsed_excerpt") or "",
            "page_count": meta.get("page_count"),
            "pages_included": meta.get("pages_included"),
        }
        if base["parsed_excerpt"]:
            return base

        if not self.pdf_enabled():
            return base

        path = Path(meta.get("path") or "")
        descriptor = IntakeDescriptor(
            kind="attachment",
            attachment_id=attachment_id,
            content_type=base["content_type"],
            path=path,
            label=base["filename"],
            extra={"attachment_id": attachment_id},
        )
        limits = self._policy.limits_for(tier)
        if self._parses_today(visitor_id) >= limits.max_parsed_documents_per_day:
            base["parse_error"] = "daily parse limit reached"
            return base

        result = self._registry.ingest(
            descriptor,
            memory_dir=self._memory_dir,
            tier=tier,
            max_pages=limits.max_parsed_pages_per_day,
        )
        if result.status != "parsed":
            base["parse_error"] = result.reason
            return base

        self._record_parse(visitor_id)
        self._attachments.update_parsed(
            attachment_id,
            parsed_excerpt=result.text_excerpt,
            page_count=result.page_count,
            pages_included=result.pages_included,
        )
        base["parsed_excerpt"] = result.text_excerpt
        base["page_count"] = result.page_count
        base["pages_included"] = result.pages_included
        return base

    def _session_intake_files(self, session_id: str) -> list[dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return []
        docs = session.get("intake_documents")
        if not isinstance(docs, dict):
            return []
        out: list[dict[str, Any]] = []
        for aid, row in docs.items():
            if isinstance(row, dict):
                out.append({**row, "id": aid})
        return out

    def _persist_session_intake(self, session_id: str, files: list[dict[str, Any]]) -> None:
        session = self._sessions.get(session_id)
        if not session:
            return
        docs = dict(session.get("intake_documents") or {})
        for f in files:
            aid = f.get("id")
            if not aid:
                continue
            docs[str(aid)] = {
                "filename": f.get("filename"),
                "content_type": f.get("content_type"),
                "parsed_excerpt": f.get("parsed_excerpt") or "",
                "page_count": f.get("page_count"),
                "pages_included": f.get("pages_included"),
            }
        session["intake_documents"] = docs
        self._sessions.save(session)

    def _parse_quota_path(self, visitor_id: str) -> Path:
        return self._parse_quota_dir / f"{_safe_id(visitor_id)}.json"

    def _parses_today(self, visitor_id: str) -> int:
        path = self._parse_quota_path(visitor_id)
        today = date.today().isoformat()
        if not path.is_file():
            return 0
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 0
        if data.get("date") != today:
            return 0
        return int(data.get("count") or 0)

    def _record_parse(self, visitor_id: str) -> None:
        path = self._parse_quota_path(visitor_id)
        today = date.today().isoformat()
        count = 1
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("date") == today:
                    count = int(data.get("count") or 0) + 1
            except (json.JSONDecodeError, OSError):
                pass
        path.write_text(json.dumps({"date": today, "count": count}), encoding="utf-8")
