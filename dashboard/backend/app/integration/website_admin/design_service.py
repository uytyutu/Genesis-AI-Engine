"""Website Admin Design theme — owner overlay (survives Factory regenerate)."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.integration.store_admin.design_service import FONT_PRESETS
from app.integration.website_admin.media_service import WebsiteMediaService

_HISTORY_LIMIT = 25


def default_design(*, business_name: str = "") -> dict[str, Any]:
    return {
        "version": 1,
        "branding": {
            "site_name": business_name or "",
            "tagline": "",
            "logo": None,
            "favicon": None,
        },
        "colors": {
            "primary": "#0f766e",
            "secondary": "#f5f0e8",
            "button": "#0f766e",
            "link": "#0d9488",
            "background": "#faf7f2",
            "text": "#0f172a",
        },
        "typography": {
            "font_preset": "dm_fraunces",
            "heading_scale": 1.0,
            "body_size_px": 16,
        },
        "motion": {
            "simple_animations": True,
        },
        "updated_at": None,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_runtime(design: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(design)
    for k in ("font_presets", "can_undo", "can_redo", "history_index", "history_len"):
        out.pop(k, None)
    return out


class WebsiteDesignService:
    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "website_admin"
        self._root.mkdir(parents=True, exist_ok=True)
        self._media = WebsiteMediaService(self._root)

    def _order_dir(self, order_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        d = self._root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _design_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "design.json"

    def _history_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "design_history.json"

    def _load_raw(self, order_id: str, *, business_name: str = "") -> dict[str, Any]:
        path = self._design_path(order_id)
        if not path.is_file():
            return default_design(business_name=business_name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default_design(business_name=business_name)
        if not isinstance(data, dict):
            return default_design(business_name=business_name)
        base = default_design(business_name=business_name)
        for key in ("branding", "colors", "typography", "motion"):
            if isinstance(data.get(key), dict):
                base[key].update(data[key])
        base["version"] = int(data.get("version") or 1)
        base["updated_at"] = data.get("updated_at")
        return base

    def _load_history(self, order_id: str) -> dict[str, Any]:
        path = self._history_path(order_id)
        if not path.is_file():
            return {"index": -1, "stack": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"index": -1, "stack": []}
        stack = data.get("stack") if isinstance(data, dict) else None
        if not isinstance(stack, list):
            return {"index": -1, "stack": []}
        index = int(data.get("index") if isinstance(data, dict) else -1)
        return {"index": index, "stack": stack}

    def _save_history(self, order_id: str, hist: dict[str, Any]) -> None:
        self._history_path(order_id).write_text(
            json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _push_history(self, order_id: str, snapshot: dict[str, Any]) -> None:
        hist = self._load_history(order_id)
        stack: list[Any] = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx >= 0 and idx < len(stack) - 1:
            stack = stack[: idx + 1]
        stack.append(_strip_runtime(snapshot))
        if len(stack) > _HISTORY_LIMIT:
            stack = stack[-_HISTORY_LIMIT:]
        self._save_history(order_id, {"index": len(stack) - 1, "stack": stack})

    def _save(self, order_id: str, design: dict[str, Any]) -> None:
        design = _strip_runtime(design)
        design["updated_at"] = _now()
        self._design_path(order_id).write_text(
            json.dumps(design, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _publicize(self, order_id: str, design: dict[str, Any]) -> dict[str, Any]:
        out = copy.deepcopy(design)

        def media_url(img: dict[str, Any] | None) -> dict[str, Any] | None:
            if not isinstance(img, dict) or not img.get("id"):
                return img
            row = dict(img)
            row["url"] = (
                f"/api/client/websites/{order_id}/admin/media/{img['id']}"
            )
            return row

        branding = out.get("branding") or {}
        branding["logo"] = media_url(branding.get("logo"))
        branding["favicon"] = media_url(branding.get("favicon"))
        out["branding"] = branding
        out["font_presets"] = [
            {"id": f["id"], "label": f["label"]} for f in FONT_PRESETS
        ]
        hist = self._load_history(order_id)
        idx = int(hist.get("index") or -1)
        stack = hist.get("stack") or []
        out["can_undo"] = idx > 0
        out["can_redo"] = idx >= 0 and idx < len(stack) - 1
        out["history_index"] = idx
        out["history_len"] = len(stack)
        return out

    def get_design(
        self, order_id: str, *, business_name: str = ""
    ) -> dict[str, Any]:
        path = self._design_path(order_id)
        raw = self._load_raw(order_id, business_name=business_name)
        if not path.is_file():
            self._save(order_id, raw)
            self._push_history(order_id, raw)
        return {
            "ok": True,
            "order_id": order_id,
            "design": self._publicize(order_id, raw),
        }

    def update_design(
        self,
        order_id: str,
        payload: dict[str, Any],
        *,
        business_name: str = "",
        record_history: bool = True,
    ) -> dict[str, Any]:
        current = self._load_raw(order_id, business_name=business_name)
        if record_history:
            hist = self._load_history(order_id)
            if not hist.get("stack"):
                self._push_history(order_id, current)

        next_design = copy.deepcopy(current)
        for key in ("branding", "colors", "typography", "motion"):
            if isinstance(payload.get(key), dict):
                next_design[key] = {**next_design.get(key, {}), **payload[key]}

        for media_key in ("logo", "favicon"):
            if "branding" in payload and media_key in payload["branding"]:
                val = payload["branding"][media_key]
                if val is None:
                    next_design["branding"][media_key] = None
                elif isinstance(val, dict) and val.get("id"):
                    next_design["branding"][media_key] = val

        self._save(order_id, next_design)
        if record_history:
            self._push_history(order_id, next_design)
        return {
            "ok": True,
            "design": self._publicize(order_id, next_design),
        }

    def undo(self, order_id: str, *, business_name: str = "") -> dict[str, Any]:
        hist = self._load_history(order_id)
        stack = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx <= 0 or not stack:
            raise ValueError("nothing_to_undo")
        idx -= 1
        snapshot = copy.deepcopy(stack[idx])
        self._save_history(order_id, {"index": idx, "stack": stack})
        self._save(order_id, snapshot)
        return {"ok": True, "design": self._publicize(order_id, snapshot)}

    def redo(self, order_id: str, *, business_name: str = "") -> dict[str, Any]:
        hist = self._load_history(order_id)
        stack = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx < 0 or idx >= len(stack) - 1:
            raise ValueError("nothing_to_redo")
        idx += 1
        snapshot = copy.deepcopy(stack[idx])
        self._save_history(order_id, {"index": idx, "stack": stack})
        self._save(order_id, snapshot)
        return {"ok": True, "design": self._publicize(order_id, snapshot)}

    def raw_design(
        self, order_id: str, *, business_name: str = ""
    ) -> dict[str, Any]:
        return self._load_raw(order_id, business_name=business_name)

    async def upload_brand_asset(
        self,
        order_id: str,
        upload: UploadFile,
        *,
        role: str = "logo",
    ) -> dict[str, Any]:
        return self._media.save_upload(upload, order_id=order_id, role=role)

    @property
    def media(self) -> WebsiteMediaService:
        return self._media
