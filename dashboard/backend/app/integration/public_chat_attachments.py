"""Public chat file attachments (Mission 1 — briefs, logos, screenshots)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.integration.attachment_policy import AttachmentPolicy, resolve_attachment_tier
from app.integration.knowledge_intake_transparency import transparency_enabled
from app.portal.s1_3_xss_upload import assert_safe_upload_filename

_ALLOWED = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_MAX_BYTES_LEGACY = 8 * 1024 * 1024


def _safe_id(raw: str, *, max_len: int = 64) -> str:
    return re.sub(r"[^\w\-]", "_", raw)[:max_len] or "anonymous"


class PublicChatAttachmentService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory_dir = memory_dir
        self._dir = memory_dir / "public_chat_uploads"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._meta_path = self._dir / "index.json"
        self._quota_dir = self._dir / "upload_quotas"
        self._quota_dir.mkdir(parents=True, exist_ok=True)
        self._policy = AttachmentPolicy(memory_dir=memory_dir)

    def save(
        self,
        upload: UploadFile,
        *,
        visitor_id: str = "anonymous",
        files_in_message: int = 1,
    ) -> dict:
        content_type = (upload.content_type or "application/octet-stream").split(";")[0].strip()
        assert_safe_upload_filename(upload.filename)
        vid = _safe_id(visitor_id)
        tier = resolve_attachment_tier(visitor_id=vid)

        if transparency_enabled(self._memory_dir):
            if content_type not in _ALLOWED:
                raise ValueError("unsupported file type")
            data_peek = upload.file.read()
            size = len(data_peek)
            upload.file.seek(0)
            check = self._policy.check_upload(
                tier=tier,
                content_type=content_type,
                size_bytes=size,
                files_in_message=files_in_message,
                uploads_today=self.uploads_today(vid),
            )
            if not check.allowed:
                raise ValueError(check.reason or "upload not allowed")
            max_bytes = check.limits.max_file_bytes if check.limits else _MAX_BYTES_LEGACY
        else:
            if content_type not in _ALLOWED:
                raise ValueError("unsupported file type")
            max_bytes = _MAX_BYTES_LEGACY
            data_peek = upload.file.read()
            size = len(data_peek)
            upload.file.seek(0)

        data = upload.file.read()
        if len(data) > max_bytes:
            mb = max(1, max_bytes // (1024 * 1024))
            raise ValueError(f"file too large (max {mb} MB)")

        att_id = f"att-{uuid.uuid4().hex[:12]}"
        ext = Path(upload.filename or "file").suffix or ".bin"
        path = self._dir / f"{att_id}{ext}"
        path.write_bytes(data)

        row = {
            "id": att_id,
            "filename": upload.filename or "file",
            "content_type": content_type,
            "size": len(data),
            "path": str(path),
            "visitor_id": vid,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_meta(row)
        self._record_upload(vid)

        stored_only = True
        if transparency_enabled(self._memory_dir):
            parse = self._policy.check_parse(tier=tier, content_type=content_type)
            stored_only = not parse.allowed

        return {
            "id": att_id,
            "filename": row["filename"],
            "content_type": content_type,
            "size": row["size"],
            "is_image": content_type.startswith("image/"),
            "stored_only": stored_only,
        }

    def get_meta(self, attachment_id: str) -> dict | None:
        for m in self._load_meta():
            if m.get("id") == attachment_id:
                return m
        return None

    def update_parsed(
        self,
        attachment_id: str,
        *,
        parsed_excerpt: str,
        page_count: int = 0,
        pages_included: int = 0,
    ) -> None:
        items = self._load_meta()
        updated = False
        for m in items:
            if m.get("id") == attachment_id:
                m["parsed_excerpt"] = parsed_excerpt
                m["page_count"] = page_count
                m["pages_included"] = pages_included
                m["parsed_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
                break
        if updated:
            self._meta_path.write_text(
                json.dumps(items[-100:], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def resolve_files(self, attachment_ids: list[str]) -> list[dict]:
        if not attachment_ids:
            return []
        meta = self._load_meta()
        by_id = {m["id"]: m for m in meta}
        out: list[dict] = []
        for aid in attachment_ids:
            m = by_id.get(aid)
            if m:
                out.append(
                    {
                        "id": m["id"],
                        "filename": m.get("filename") or "file",
                        "content_type": m.get("content_type") or "",
                        "parsed_excerpt": m.get("parsed_excerpt") or "",
                        "page_count": m.get("page_count"),
                        "pages_included": m.get("pages_included"),
                    }
                )
        return out

    def describe(self, attachment_ids: list[str]) -> str:
        """Legacy describe — prefer knowledge_intake_transparency.build_brain_attachment_note."""
        files = self.resolve_files(attachment_ids)
        if not files:
            return ""
        lines = [f"• {f['filename']} ({f['content_type']})" for f in files]
        return "Клиент прикрепил файлы:\n" + "\n".join(lines)

    def uploads_today(self, visitor_id: str) -> int:
        path = self._quota_path(visitor_id)
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

    def _quota_path(self, visitor_id: str) -> Path:
        return self._quota_dir / f"{_safe_id(visitor_id)}.json"

    def _record_upload(self, visitor_id: str) -> None:
        path = self._quota_path(visitor_id)
        today = date.today().isoformat()
        count = 1
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("date") == today:
                    count = int(data.get("count") or 0) + 1
            except (json.JSONDecodeError, OSError):
                pass
        path.write_text(
            json.dumps({"date": today, "count": count}, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_meta(self) -> list[dict]:
        if not self._meta_path.is_file():
            return []
        try:
            data = json.loads(self._meta_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _append_meta(self, row: dict) -> None:
        items = self._load_meta()
        items.append(row)
        self._meta_path.write_text(
            json.dumps(items[-100:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
