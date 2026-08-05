"""Store Admin Design theme — owner overlay (survives Factory regenerate)."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.integration.store_admin.media_service import StoreCatalogMediaService

FONT_PRESETS: tuple[dict[str, str], ...] = (
    {
        "id": "dm_fraunces",
        "label": "DM Sans + Fraunces",
        "sans": '"DM Sans", "Segoe UI", system-ui, sans-serif',
        "display": '"Fraunces", Georgia, serif',
        "import": "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,600;9..40,700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap",
    },
    {
        "id": "outfit_source",
        "label": "Outfit + Source Serif",
        "sans": '"Outfit", system-ui, sans-serif',
        "display": '"Source Serif 4", Georgia, serif',
        "import": "https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap",
    },
    {
        "id": "space_libre",
        "label": "Space Grotesk + Libre Baskerville",
        "sans": '"Space Grotesk", system-ui, sans-serif',
        "display": '"Libre Baskerville", Georgia, serif',
        "import": "https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Space+Grotesk:wght@400;600;700&display=swap",
    },
    {
        "id": "manrope_playfair",
        "label": "Manrope + Playfair",
        "sans": '"Manrope", system-ui, sans-serif',
        "display": '"Playfair Display", Georgia, serif',
        "import": "https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&family=Playfair+Display:wght@600;700&display=swap",
    },
)

_HISTORY_LIMIT = 40


def default_design(*, store_name: str = "") -> dict[str, Any]:
    return {
        "version": 1,
        "branding": {
            "store_name": store_name or "",
            "tagline": "",
            "logo": None,
            "favicon": None,
        },
        "hero": {
            "enabled": True,
            "banners": [],
        },
        "colors": {
            "primary": "#0f766e",
            "secondary": "#f5f0e8",
            "button": "#0f766e",
            "link": "#0d9488",
            "background": "#faf7f2",
        },
        "typography": {
            "font_preset": "dm_fraunces",
            "heading_scale": 1.0,
            "body_size_px": 16,
        },
        "homepage": {
            "hero": True,
            "categories": True,
            "featured": True,
            "new_arrivals": True,
            "bestsellers": True,
            "reviews": True,
            "newsletter": True,
            "footer": True,
        },
        "updated_at": None,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_runtime(design: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(design)
    out.pop("can_undo", None)
    out.pop("can_redo", None)
    out.pop("history_index", None)
    out.pop("history_len", None)
    out.pop("font_presets", None)
    return out


class StoreDesignService:
    """
    User Data Protection Rule:
    Design lives under store_admin/{order_id}/ — Factory never deletes it.
    After regenerate, apply_design_to_product_dir re-paints the storefront.
    """

    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "store_admin"
        self._root.mkdir(parents=True, exist_ok=True)
        self._media = StoreCatalogMediaService(self._root)

    def _order_dir(self, order_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        d = self._root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _design_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "design.json"

    def _history_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "design_history.json"

    def _load_raw(self, order_id: str, *, store_name: str = "") -> dict[str, Any]:
        path = self._design_path(order_id)
        if not path.is_file():
            return default_design(store_name=store_name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default_design(store_name=store_name)
        if not isinstance(data, dict):
            return default_design(store_name=store_name)
        base = default_design(store_name=store_name)
        merged = copy.deepcopy(base)
        for key in ("branding", "hero", "colors", "typography", "homepage"):
            if isinstance(data.get(key), dict):
                merged[key].update(data[key])
        merged["version"] = int(data.get("version") or 1)
        merged["updated_at"] = data.get("updated_at")
        return merged

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

    def _save_design(self, order_id: str, design: dict[str, Any]) -> None:
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
                f"/api/client/stores/{order_id}/admin/design/media/{img['id']}"
            )
            return row

        branding = out.get("branding") or {}
        branding["logo"] = media_url(branding.get("logo"))
        branding["favicon"] = media_url(branding.get("favicon"))
        out["branding"] = branding
        hero = out.get("hero") or {}
        banners = []
        for b in hero.get("banners") or []:
            if isinstance(b, dict):
                banners.append(media_url(b))
        hero["banners"] = banners
        out["hero"] = hero

        hist = self._load_history(order_id)
        idx = int(hist.get("index") or -1)
        stack = hist.get("stack") or []
        out["can_undo"] = idx > 0
        out["can_redo"] = idx >= 0 and idx < len(stack) - 1
        out["history_index"] = idx
        out["history_len"] = len(stack)
        out["font_presets"] = [
            {"id": f["id"], "label": f["label"]} for f in FONT_PRESETS
        ]
        return out

    def get_design(
        self, order_id: str, *, store_name: str = ""
    ) -> dict[str, Any]:
        return {
            "ok": True,
            "order_id": order_id,
            "design": self._publicize(
                order_id, self._load_raw(order_id, store_name=store_name)
            ),
        }

    def _push_history(self, order_id: str, snapshot: dict[str, Any]) -> None:
        hist = self._load_history(order_id)
        stack: list[Any] = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx >= 0 and idx < len(stack) - 1:
            stack = stack[: idx + 1]
        stack.append(_strip_runtime(snapshot))
        if len(stack) > _HISTORY_LIMIT:
            stack = stack[-_HISTORY_LIMIT:]
        hist = {"index": len(stack) - 1, "stack": stack}
        self._save_history(order_id, hist)

    def update_design(
        self,
        order_id: str,
        payload: dict[str, Any],
        *,
        store_name: str = "",
        record_history: bool = True,
    ) -> dict[str, Any]:
        current = self._load_raw(order_id, store_name=store_name)
        if record_history:
            hist = self._load_history(order_id)
            if not hist.get("stack"):
                self._push_history(order_id, current)

        next_design = copy.deepcopy(current)
        for key in ("branding", "hero", "colors", "typography", "homepage"):
            if isinstance(payload.get(key), dict):
                next_design[key] = {**next_design.get(key, {}), **payload[key]}

        for media_key in ("logo", "favicon"):
            if "branding" in payload and media_key in payload["branding"]:
                val = payload["branding"][media_key]
                if val is None:
                    next_design["branding"][media_key] = None
                elif isinstance(val, dict) and val.get("id"):
                    existing = current.get("branding", {}).get(media_key)
                    if isinstance(existing, dict) and existing.get("id") == val.get(
                        "id"
                    ):
                        next_design["branding"][media_key] = existing
                    else:
                        next_design["branding"][media_key] = val

        if isinstance(payload.get("hero"), dict) and "banners" in payload["hero"]:
            next_design["hero"]["banners"] = list(payload["hero"]["banners"] or [])

        self._save_design(order_id, next_design)
        if record_history:
            commit = bool(payload.get("commit"))
            only_style = set(payload.keys()) <= {
                "colors",
                "typography",
                "commit",
            }
            if commit or not only_style:
                self._push_history(order_id, next_design)
            else:
                # coalesce rapid color/type tweaks into one undo step
                self._replace_top_history(order_id, next_design)
        return {
            "ok": True,
            "design": self._publicize(order_id, next_design),
        }

    def _replace_top_history(self, order_id: str, snapshot: dict[str, Any]) -> None:
        hist = self._load_history(order_id)
        stack: list[Any] = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx < 0 or not stack:
            self._push_history(order_id, snapshot)
            return
        stack[idx] = _strip_runtime(snapshot)
        self._save_history(order_id, {"index": idx, "stack": stack})

    def undo(self, order_id: str, *, store_name: str = "") -> dict[str, Any]:
        hist = self._load_history(order_id)
        stack = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx <= 0 or not stack:
            raise ValueError("nothing_to_undo")
        idx -= 1
        design = copy.deepcopy(stack[idx])
        self._save_design(order_id, design)
        self._save_history(order_id, {"index": idx, "stack": stack})
        return {"ok": True, "design": self._publicize(order_id, design)}

    def redo(self, order_id: str, *, store_name: str = "") -> dict[str, Any]:
        hist = self._load_history(order_id)
        stack = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx < 0 or idx >= len(stack) - 1:
            raise ValueError("nothing_to_redo")
        idx += 1
        design = copy.deepcopy(stack[idx])
        self._save_design(order_id, design)
        self._save_history(order_id, {"index": idx, "stack": stack})
        return {"ok": True, "design": self._publicize(order_id, design)}

    def restore_defaults(
        self, order_id: str, *, store_name: str = ""
    ) -> dict[str, Any]:
        current = self._load_raw(order_id, store_name=store_name)
        self._push_history(order_id, current)
        design = default_design(store_name=store_name or current.get("branding", {}).get("store_name") or "")
        self._save_design(order_id, design)
        self._push_history(order_id, design)
        return {"ok": True, "design": self._publicize(order_id, design)}

    def upload_asset(
        self,
        order_id: str,
        upload: UploadFile,
        *,
        kind: str,
        store_name: str = "",
    ) -> dict[str, Any]:
        kind = (kind or "").strip().lower()
        edges = {
            "logo": 512,
            "favicon": 256,
            "banner": 1920,
            "banner_mobile": 900,
        }
        if kind not in edges:
            raise ValueError("invalid_asset_kind")
        row = self._media.save_upload(
            upload,
            order_id=order_id,
            product_id="design",
            max_edge=edges[kind],
            subdir="design",
        )
        row["kind"] = kind
        design = self._load_raw(order_id, store_name=store_name)
        self._push_history(order_id, design)

        if kind == "logo":
            design["branding"]["logo"] = row
        elif kind == "favicon":
            design["branding"]["favicon"] = row
        else:
            banners = list(design.get("hero", {}).get("banners") or [])
            banners.append({**row, "role": kind})
            design.setdefault("hero", {})["banners"] = banners

        self._save_design(order_id, design)
        self._push_history(order_id, design)
        return {
            "ok": True,
            "asset": {
                **row,
                "url": f"/api/client/stores/{order_id}/admin/design/media/{row['id']}",
            },
            "design": self._publicize(order_id, design),
        }

    def resolve_media(self, order_id: str, image_id: str) -> Path:
        design = self._load_raw(order_id)
        candidates: list[dict[str, Any]] = []
        branding = design.get("branding") or {}
        for key in ("logo", "favicon"):
            img = branding.get(key)
            if isinstance(img, dict):
                candidates.append(img)
        for b in (design.get("hero") or {}).get("banners") or []:
            if isinstance(b, dict):
                candidates.append(b)
        for img in candidates:
            if str(img.get("id")) == image_id:
                return self._media.resolve_path(str(img.get("path") or ""))
        raise ValueError("image_not_found")

    def raw_design(self, order_id: str, *, store_name: str = "") -> dict[str, Any]:
        return self._load_raw(order_id, store_name=store_name)
