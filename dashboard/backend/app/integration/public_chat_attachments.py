"""Public chat file attachments (Mission 1 — briefs, logos, screenshots)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

_ALLOWED = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_MAX_BYTES = 8 * 1024 * 1024


class PublicChatAttachmentService:
    def __init__(self, memory_dir: Path) -> None:
        self._dir = memory_dir / "public_chat_uploads"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._meta_path = self._dir / "index.json"

    def save(self, upload: UploadFile) -> dict:
        content_type = (upload.content_type or "application/octet-stream").split(";")[0].strip()
        if content_type not in _ALLOWED:
            raise ValueError("unsupported file type")

        data = upload.file.read()
        if len(data) > _MAX_BYTES:
            raise ValueError("file too large (max 8 MB)")

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
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_meta(row)
        return {
            "id": att_id,
            "filename": row["filename"],
            "content_type": content_type,
            "size": row["size"],
            "is_image": content_type.startswith("image/"),
        }

    def describe(self, attachment_ids: list[str]) -> str:
        if not attachment_ids:
            return ""
        meta = self._load_meta()
        by_id = {m["id"]: m for m in meta}
        lines = []
        for aid in attachment_ids:
            m = by_id.get(aid)
            if m:
                lines.append(f"• {m['filename']} ({m['content_type']})")
        if not lines:
            return ""
        return "Клиент прикрепил файлы:\n" + "\n".join(lines)

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
