"""Website Admin content overlay — owner editable copy (survives Factory regenerate)."""

from __future__ import annotations

import copy
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.website_admin.media_service import WebsiteMediaService

CONTENT_KEYS = (
    "hero",
    "about",
    "services",
    "prices",
    "gallery",
    "team",
    "reviews",
    "faq",
    "contacts",
    "hours",
    "social",
    "seo",
)

_HISTORY_LIMIT = 25


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str = "item") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def default_content(*, business_name: str = "") -> dict[str, Any]:
    name = (business_name or "").strip() or "Ihr Unternehmen"
    return {
        "version": 1,
        "hero": {
            "headline": name,
            "subheadline": "Professioneller Auftritt für Ihr Unternehmen.",
            "cta_label": "Kontakt aufnehmen",
            "image": None,
        },
        "about": {
            "title": "Über uns",
            "body": f"{name} steht für Qualität, Vertrauen und persönliche Betreuung.",
        },
        "services": [
            {
                "id": _uid("svc"),
                "title": "Beratung",
                "description": "Persönliche Beratung für Ihre Anliegen.",
                "price": "",
            }
        ],
        "prices": {
            "enabled": False,
            "title": "Preise",
            "intro": "Transparente Preise — ohne Überraschungen.",
            "items": [],
        },
        "gallery": [],
        "team": [],
        "reviews": [],
        "faq": [
            {
                "id": _uid("faq"),
                "question": "Wie kann ich einen Termin vereinbaren?",
                "answer": "Rufen Sie uns an oder schreiben Sie uns über das Kontaktformular.",
            }
        ],
        "contacts": {
            "phone": "",
            "email": "",
            "address": "",
            "whatsapp": "",
            "city": "",
        },
        "hours": {
            "mon": "09:00–18:00",
            "tue": "09:00–18:00",
            "wed": "09:00–18:00",
            "thu": "09:00–18:00",
            "fri": "09:00–18:00",
            "sat": "Geschlossen",
            "sun": "Geschlossen",
        },
        "social": {
            "instagram": "",
            "facebook": "",
            "tiktok": "",
            "linkedin": "",
            "youtube": "",
            "google_business": "",
        },
        "seo": {
            "title": name,
            "description": f"{name} — professionelle Website.",
        },
        "updated_at": None,
    }


def seed_from_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    meta = meta if isinstance(meta, dict) else {}
    name = str(
        meta.get("business_name")
        or meta.get("company_name")
        or meta.get("brand_name")
        or ""
    ).strip()
    base = default_content(business_name=name)
    city = str(meta.get("city") or "").strip()
    phone = str(meta.get("phone") or meta.get("tel") or "").strip()
    email = str(meta.get("email") or "").strip()
    if city:
        base["contacts"]["city"] = city
        base["hero"]["subheadline"] = f"Ihr Partner in {city}."
    if phone:
        base["contacts"]["phone"] = phone
    if email:
        base["contacts"]["email"] = email
    slogan = str(meta.get("slogan") or meta.get("tagline") or "").strip()
    if slogan:
        base["hero"]["subheadline"] = slogan
    about = str(meta.get("about") or meta.get("mission") or "").strip()
    if about:
        base["about"]["body"] = about[:800]
    services = meta.get("services")
    if isinstance(services, list) and services:
        rows = []
        for item in services[:12]:
            if isinstance(item, str) and item.strip():
                rows.append(
                    {
                        "id": _uid("svc"),
                        "title": item.strip()[:80],
                        "description": "",
                        "price": "",
                    }
                )
            elif isinstance(item, dict):
                rows.append(
                    {
                        "id": str(item.get("id") or _uid("svc")),
                        "title": str(item.get("title") or item.get("name") or "Service")[
                            :80
                        ],
                        "description": str(
                            item.get("description") or item.get("blurb") or ""
                        )[:400],
                        "price": str(item.get("price") or "")[:40],
                    }
                )
        if rows:
            base["services"] = rows
    return base


def _strip_runtime(content: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(content)
    for k in ("can_undo", "can_redo", "history_index", "history_len"):
        out.pop(k, None)
    return out


class WebsiteContentService:
    """Owner content under website_admin/{order_id}/ — Factory never deletes it."""

    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "website_admin"
        self._root.mkdir(parents=True, exist_ok=True)
        self._media = WebsiteMediaService(self._root)

    def _order_dir(self, order_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        d = self._root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _content_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "content.json"

    def _history_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "content_history.json"

    def _load_raw(
        self, order_id: str, *, seed: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        path = self._content_path(order_id)
        if not path.is_file():
            return copy.deepcopy(seed or default_content())
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return copy.deepcopy(seed or default_content())
        if not isinstance(data, dict):
            return copy.deepcopy(seed or default_content())
        base = copy.deepcopy(seed or default_content())
        for key in CONTENT_KEYS:
            if key in data:
                if isinstance(base.get(key), dict) and isinstance(data[key], dict):
                    base[key] = {**base[key], **data[key]}
                else:
                    base[key] = data[key]
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

    def _save(self, order_id: str, content: dict[str, Any]) -> None:
        content = _strip_runtime(content)
        content["updated_at"] = _now()
        self._content_path(order_id).write_text(
            json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _publicize(self, order_id: str, content: dict[str, Any]) -> dict[str, Any]:
        out = copy.deepcopy(content)

        def media_url(img: dict[str, Any] | None) -> dict[str, Any] | None:
            if not isinstance(img, dict) or not img.get("id"):
                return img
            row = dict(img)
            row["url"] = (
                f"/api/client/websites/{order_id}/admin/media/{img['id']}"
            )
            return row

        hero = out.get("hero") or {}
        hero["image"] = media_url(hero.get("image"))
        out["hero"] = hero

        gallery = []
        for item in out.get("gallery") or []:
            if isinstance(item, dict):
                row = dict(item)
                row["image"] = media_url(row.get("image"))
                gallery.append(row)
        out["gallery"] = gallery

        team = []
        for item in out.get("team") or []:
            if isinstance(item, dict):
                row = dict(item)
                row["image"] = media_url(row.get("image"))
                team.append(row)
        out["team"] = team

        hist = self._load_history(order_id)
        idx = int(hist.get("index") or -1)
        stack = hist.get("stack") or []
        out["can_undo"] = idx > 0
        out["can_redo"] = idx >= 0 and idx < len(stack) - 1
        out["history_index"] = idx
        out["history_len"] = len(stack)
        return out

    def get_content(
        self,
        order_id: str,
        *,
        seed_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        seed = seed_from_meta(seed_meta) if seed_meta is not None else None
        path = self._content_path(order_id)
        if not path.is_file() and seed is not None:
            self._save(order_id, seed)
            self._push_history(order_id, seed)
            raw = seed
        else:
            raw = self._load_raw(order_id, seed=seed)
        return {
            "ok": True,
            "order_id": order_id,
            "content": self._publicize(order_id, raw),
        }

    def update_content(
        self,
        order_id: str,
        payload: dict[str, Any],
        *,
        seed_meta: dict[str, Any] | None = None,
        record_history: bool = True,
    ) -> dict[str, Any]:
        seed = seed_from_meta(seed_meta) if seed_meta is not None else None
        current = self._load_raw(order_id, seed=seed)
        if record_history:
            hist = self._load_history(order_id)
            if not hist.get("stack"):
                self._push_history(order_id, current)

        next_content = copy.deepcopy(current)

        for key in ("hero", "about", "contacts", "hours", "social", "seo", "prices"):
            if isinstance(payload.get(key), dict):
                next_content[key] = {**next_content.get(key, {}), **payload[key]}

        for list_key in ("services", "gallery", "team", "reviews", "faq"):
            if list_key in payload and isinstance(payload[list_key], list):
                next_content[list_key] = payload[list_key]

        if isinstance(payload.get("prices"), dict) and "items" in payload["prices"]:
            next_content["prices"]["items"] = list(payload["prices"]["items"] or [])

        if isinstance(payload.get("hero"), dict) and "image" in payload["hero"]:
            val = payload["hero"]["image"]
            if val is None:
                next_content["hero"]["image"] = None
            elif isinstance(val, dict) and val.get("id"):
                next_content["hero"]["image"] = val

        self._save(order_id, next_content)
        if record_history:
            self._push_history(order_id, next_content)
        return {
            "ok": True,
            "content": self._publicize(order_id, next_content),
        }

    def undo(
        self, order_id: str, *, seed_meta: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        hist = self._load_history(order_id)
        stack = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx <= 0 or not stack:
            raise ValueError("nothing_to_undo")
        idx -= 1
        snapshot = copy.deepcopy(stack[idx])
        self._save_history(order_id, {"index": idx, "stack": stack})
        self._save(order_id, snapshot)
        return {
            "ok": True,
            "content": self._publicize(order_id, snapshot),
        }

    def redo(
        self, order_id: str, *, seed_meta: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        hist = self._load_history(order_id)
        stack = list(hist.get("stack") or [])
        idx = int(hist.get("index") or -1)
        if idx < 0 or idx >= len(stack) - 1:
            raise ValueError("nothing_to_redo")
        idx += 1
        snapshot = copy.deepcopy(stack[idx])
        self._save_history(order_id, {"index": idx, "stack": stack})
        self._save(order_id, snapshot)
        return {
            "ok": True,
            "content": self._publicize(order_id, snapshot),
        }

    def raw_content(
        self, order_id: str, *, seed_meta: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        seed = seed_from_meta(seed_meta) if seed_meta is not None else None
        return self._load_raw(order_id, seed=seed)

    @property
    def media(self) -> WebsiteMediaService:
        return self._media
