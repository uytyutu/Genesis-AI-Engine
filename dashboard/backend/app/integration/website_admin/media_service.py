"""Image upload for Website Admin owner media."""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.portal.s1_3_xss_upload import assert_safe_upload_filename

_ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_MAX_BYTES = 8 * 1024 * 1024
_MAX_EDGE = 1600


def _try_optimize(
    data: bytes, *, src_ext: str, max_edge: int = _MAX_EDGE
) -> tuple[bytes, str, dict[str, Any]]:
    meta: dict[str, Any] = {
        "optimized": False,
        "original_bytes": len(data),
        "width": None,
        "height": None,
    }
    try:
        from PIL import Image  # type: ignore
    except Exception:
        meta["reason"] = "pillow_unavailable"
        return data, src_ext if src_ext in _ALLOWED_EXT else ".bin", meta

    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGBA") if img.mode in ("P", "RGBA") else img.convert("RGB")
        w, h = img.size
        meta["width"] = w
        meta["height"] = h
        longest = max(w, h)
        edge = max(64, int(max_edge or _MAX_EDGE))
        if longest > edge:
            scale = edge / float(longest)
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
            meta["width"], meta["height"] = img.size
        out = io.BytesIO()
        save_img = img.convert("RGB")
        save_img.save(out, format="WEBP", quality=82, method=4)
        optimized = out.getvalue()
        meta["optimized"] = True
        meta["stored_bytes"] = len(optimized)
        return optimized, ".webp", meta
    except Exception as exc:
        meta["reason"] = f"optimize_failed:{exc.__class__.__name__}"
        return data, src_ext if src_ext in _ALLOWED_EXT else ".bin", meta


class WebsiteMediaService:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._media = root / "media"
        self._media.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_order(order_id: str) -> str:
        import re

        return re.sub(r"[^\w\-]", "_", order_id)[:80] or "order"

    def save_upload(
        self,
        upload: UploadFile,
        *,
        order_id: str,
        role: str = "gallery",
        max_edge: int = _MAX_EDGE,
    ) -> dict[str, Any]:
        assert_safe_upload_filename(upload.filename)
        name = Path(upload.filename or "image.jpg").name
        ext = Path(name).suffix.lower() or ".jpg"
        if ext not in _ALLOWED_EXT:
            raise ValueError(f"unsupported_image_type:{ext}")

        data = upload.file.read()
        if not data:
            raise ValueError("empty_upload")
        if len(data) > _MAX_BYTES:
            raise ValueError("image_too_large")

        payload, out_ext, meta = _try_optimize(data, src_ext=ext, max_edge=max_edge)
        image_id = f"img-{uuid.uuid4().hex[:12]}"
        safe_role = "".join(c for c in (role or "gallery") if c.isalnum() or c in "-_")[:32] or "gallery"
        rel_dir = Path(self._safe_order(order_id)) / safe_role
        dest_dir = self._media / rel_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{image_id}{out_ext}"
        path = dest_dir / filename
        path.write_bytes(payload)

        return {
            "id": image_id,
            "filename": name,
            "path": str(path.relative_to(self._media)).replace("\\", "/"),
            "content_type": "image/webp" if out_ext == ".webp" else f"image/{out_ext.lstrip('.')}",
            "size": len(payload),
            "role": safe_role,
            "width": meta.get("width"),
            "height": meta.get("height"),
            "optimized": bool(meta.get("optimized")),
        }

    def resolve_path(self, relative: str) -> Path:
        rel = Path(relative.replace("\\", "/"))
        if ".." in rel.parts:
            raise ValueError("invalid_path")
        path = (self._media / rel).resolve()
        if not str(path).startswith(str(self._media.resolve())):
            raise ValueError("invalid_path")
        if not path.is_file():
            raise ValueError("image_not_found")
        return path

    def find_by_id(self, order_id: str, image_id: str) -> Path | None:
        base = self._media / self._safe_order(order_id)
        if not base.is_dir():
            return None
        for path in base.rglob(f"{image_id}.*"):
            if path.is_file():
                return path
        return None

    def delete_by_id(self, order_id: str, image_id: str) -> bool:
        path = self.find_by_id(order_id, image_id)
        if path is None:
            raise ValueError("image_not_found")
        path.unlink(missing_ok=True)
        return True

    def list_order_media(self, order_id: str) -> list[dict[str, Any]]:
        base = self._media / self._safe_order(order_id)
        if not base.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in _ALLOWED_EXT and path.suffix.lower() != ".webp":
                continue
            image_id = path.stem
            role = path.parent.name
            rel = str(path.relative_to(self._media)).replace("\\", "/")
            rows.append(
                {
                    "id": image_id,
                    "role": role,
                    "path": rel,
                    "url": f"/api/client/websites/{order_id}/admin/media/{image_id}",
                    "size": path.stat().st_size,
                }
            )
        return rows
