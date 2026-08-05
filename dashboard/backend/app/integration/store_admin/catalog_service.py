"""Per-store merchant product catalog (JSON + media on disk)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.integration.store_admin.ai_assist import generate_product_fields
from app.integration.store_admin.media_service import StoreCatalogMediaService
from app.integration.store_admin.models import (
    PRODUCT_TYPE_VALUES,
    STATUS_VALUES,
    STOCK_STATUS_VALUES,
    default_product,
    empty_seo,
    empty_variants,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return (s or "product")[:80]


class StoreCatalogService:
    def __init__(self, memory_dir: Path) -> None:
        self._root = Path(memory_dir) / "store_admin"
        self._root.mkdir(parents=True, exist_ok=True)
        self._media = StoreCatalogMediaService(self._root)

    def _order_dir(self, order_id: str) -> Path:
        safe = re.sub(r"[^\w\-]", "_", order_id)[:80]
        d = self._root / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _catalog_path(self, order_id: str) -> Path:
        return self._order_dir(order_id) / "products.json"

    def _load(self, order_id: str) -> list[dict[str, Any]]:
        path = self._catalog_path(order_id)
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        items = data.get("products") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
        return [p for p in items if isinstance(p, dict)]

    def _save(self, order_id: str, products: list[dict[str, Any]]) -> None:
        path = self._catalog_path(order_id)
        payload = {
            "version": 1,
            "order_id": order_id,
            "updated_at": _now(),
            "products": products,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _public_image(
        self, order_id: str, image: dict[str, Any]
    ) -> dict[str, Any]:
        out = dict(image)
        img_id = str(image.get("id") or "")
        out["url"] = (
            f"/api/client/stores/{order_id}/admin/media/{img_id}"
            if img_id
            else None
        )
        return out

    def _public_product(
        self, order_id: str, product: dict[str, Any]
    ) -> dict[str, Any]:
        out = dict(product)
        images = product.get("images") if isinstance(product.get("images"), list) else []
        out["images"] = [
            self._public_image(order_id, img)
            for img in images
            if isinstance(img, dict)
        ]
        return out

    def list_products(
        self,
        order_id: str,
        *,
        status: str | None = None,
        q: str | None = None,
    ) -> dict[str, Any]:
        products = self._load(order_id)
        if status in STATUS_VALUES:
            products = [p for p in products if p.get("status") == status]
        needle = (q or "").strip().lower()
        if needle:
            products = [
                p
                for p in products
                if needle in str(p.get("title") or "").lower()
                or needle in str(p.get("sku") or "").lower()
                or needle in str(p.get("category") or "").lower()
            ]
        public = [self._public_product(order_id, p) for p in products]
        return {
            "ok": True,
            "order_id": order_id,
            "count": len(public),
            "products": public,
            "product_types": list(PRODUCT_TYPE_VALUES),
            "active_product_types": ["physical"],
        }

    def get_product(self, order_id: str, product_id: str) -> dict[str, Any]:
        for p in self._load(order_id):
            if p.get("id") == product_id:
                return {"ok": True, "product": self._public_product(order_id, p)}
        raise ValueError("catalog_product_not_found")

    def _normalize_payload(
        self, payload: dict[str, Any], *, existing: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        base = existing or default_product()
        out = dict(base)

        pt = str(payload.get("product_type") or out.get("product_type") or "physical")
        if pt not in PRODUCT_TYPE_VALUES:
            raise ValueError("invalid_product_type")
        out["product_type"] = pt

        status = str(payload.get("status") or out.get("status") or "draft")
        if status not in STATUS_VALUES:
            raise ValueError("invalid_status")
        out["status"] = status

        for key in (
            "title",
            "short_description",
            "description",
            "sku",
            "category",
            "subcategory",
            "brand",
            "currency",
        ):
            if key in payload:
                out[key] = str(payload.get(key) or "").strip()

        if "price" in payload:
            try:
                out["price"] = float(payload.get("price") or 0)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid_price") from exc
        if "compare_at_price" in payload:
            raw = payload.get("compare_at_price")
            if raw is None or raw == "":
                out["compare_at_price"] = None
            else:
                try:
                    out["compare_at_price"] = float(raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError("invalid_compare_at_price") from exc

        if "stock_qty" in payload:
            try:
                out["stock_qty"] = max(0, int(payload.get("stock_qty") or 0))
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid_stock_qty") from exc

        if "stock_status" in payload:
            ss = str(payload.get("stock_status") or "in_stock")
            if ss not in STOCK_STATUS_VALUES:
                raise ValueError("invalid_stock_status")
            out["stock_status"] = ss

        if "variants" in payload and isinstance(payload["variants"], dict):
            v = empty_variants()
            src = payload["variants"]
            for key in ("size", "color", "material"):
                raw = src.get(key)
                if isinstance(raw, list):
                    v[key] = [str(x).strip() for x in raw if str(x).strip()][:40]
                elif isinstance(raw, str) and raw.strip():
                    v[key] = [x.strip() for x in raw.split(",") if x.strip()][:40]
            if "weight" in src:
                w = src.get("weight")
                v["weight"] = None if w is None or w == "" else str(w).strip()[:40]
            out["variants"] = v

        if "seo" in payload and isinstance(payload["seo"], dict):
            seo = empty_seo()
            seo_src = payload["seo"]
            seo["title"] = str(seo_src.get("title") or "").strip()[:120]
            seo["description"] = str(seo_src.get("description") or "").strip()[:320]
            slug = str(seo_src.get("slug") or "").strip()
            seo["slug"] = _slugify(slug) if slug else _slugify(str(out.get("title") or ""))
            out["seo"] = seo
        elif not out.get("seo") or not (out.get("seo") or {}).get("slug"):
            seo = dict(out.get("seo") or empty_seo())
            if not seo.get("slug"):
                seo["slug"] = _slugify(str(out.get("title") or "product"))
            out["seo"] = seo

        if not str(out.get("title") or "").strip():
            raise ValueError("title_required")

        return out

    def create_product(self, order_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        products = self._load(order_id)
        row = self._normalize_payload(payload)
        row["id"] = f"prd-{uuid.uuid4().hex[:12]}"
        row["images"] = []
        row["created_at"] = _now()
        row["updated_at"] = row["created_at"]
        products.append(row)
        self._save(order_id, products)
        return {"ok": True, "product": self._public_product(order_id, row)}

    def update_product(
        self, order_id: str, product_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        products = self._load(order_id)
        for i, p in enumerate(products):
            if p.get("id") != product_id:
                continue
            merged = self._normalize_payload(payload, existing=p)
            merged["id"] = product_id
            merged["images"] = p.get("images") if isinstance(p.get("images"), list) else []
            merged["created_at"] = p.get("created_at") or _now()
            merged["updated_at"] = _now()
            products[i] = merged
            self._save(order_id, products)
            return {"ok": True, "product": self._public_product(order_id, merged)}
        raise ValueError("catalog_product_not_found")

    def delete_product(self, order_id: str, product_id: str) -> dict[str, Any]:
        products = self._load(order_id)
        keep: list[dict[str, Any]] = []
        removed = None
        for p in products:
            if p.get("id") == product_id:
                removed = p
                continue
            keep.append(p)
        if removed is None:
            raise ValueError("catalog_product_not_found")
        for img in removed.get("images") or []:
            if isinstance(img, dict):
                self._media.delete_file(str(img.get("path") or ""))
        self._save(order_id, keep)
        return {"ok": True, "deleted": product_id}

    def bulk(self, order_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        action = str(payload.get("action") or "").strip()
        ids = [str(x) for x in (payload.get("product_ids") or []) if str(x)]
        if not ids:
            raise ValueError("product_ids_required")
        if action not in (
            "delete",
            "set_status",
            "set_category",
            "set_price",
        ):
            raise ValueError("invalid_bulk_action")

        products = self._load(order_id)
        id_set = set(ids)
        touched = 0

        if action == "delete":
            keep: list[dict[str, Any]] = []
            for p in products:
                if p.get("id") in id_set:
                    touched += 1
                    for img in p.get("images") or []:
                        if isinstance(img, dict):
                            self._media.delete_file(str(img.get("path") or ""))
                    continue
                keep.append(p)
            self._save(order_id, keep)
            return {"ok": True, "action": action, "affected": touched}

        status = str(payload.get("status") or "")
        category = str(payload.get("category") or "").strip()
        price_raw = payload.get("price")

        for p in products:
            if p.get("id") not in id_set:
                continue
            touched += 1
            if action == "set_status":
                if status not in STATUS_VALUES:
                    raise ValueError("invalid_status")
                p["status"] = status
            elif action == "set_category":
                if not category:
                    raise ValueError("category_required")
                p["category"] = category
            elif action == "set_price":
                try:
                    p["price"] = float(price_raw)
                except (TypeError, ValueError) as exc:
                    raise ValueError("invalid_price") from exc
            p["updated_at"] = _now()

        self._save(order_id, products)
        return {"ok": True, "action": action, "affected": touched}

    def add_images(
        self,
        order_id: str,
        product_id: str,
        uploads: list[UploadFile],
    ) -> dict[str, Any]:
        products = self._load(order_id)
        target = None
        for p in products:
            if p.get("id") == product_id:
                target = p
                break
        if target is None:
            raise ValueError("catalog_product_not_found")

        images = list(target.get("images") or [])
        if not isinstance(images, list):
            images = []
        start_sort = len(images)
        for i, upload in enumerate(uploads):
            row = self._media.save_upload(
                upload, order_id=order_id, product_id=product_id
            )
            row["sort"] = start_sort + i
            row["is_primary"] = False
            images.append(row)

        if images and not any(bool(img.get("is_primary")) for img in images):
            images[0]["is_primary"] = True

        target["images"] = images
        target["updated_at"] = _now()
        self._save(order_id, products)
        return {"ok": True, "product": self._public_product(order_id, target)}

    def update_images(
        self, order_id: str, product_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Reorder and/or set primary image."""
        products = self._load(order_id)
        target = None
        for p in products:
            if p.get("id") == product_id:
                target = p
                break
        if target is None:
            raise ValueError("catalog_product_not_found")

        images = [
            img for img in (target.get("images") or []) if isinstance(img, dict)
        ]
        by_id = {str(img.get("id")): img for img in images}

        order_ids = payload.get("image_ids")
        if isinstance(order_ids, list) and order_ids:
            ordered: list[dict[str, Any]] = []
            for i, iid in enumerate(order_ids):
                img = by_id.get(str(iid))
                if not img:
                    continue
                img = dict(img)
                img["sort"] = i
                ordered.append(img)
            # append any missing
            seen = {str(x.get("id")) for x in ordered}
            for img in images:
                if str(img.get("id")) not in seen:
                    img = dict(img)
                    img["sort"] = len(ordered)
                    ordered.append(img)
            images = ordered

        primary = payload.get("primary_image_id")
        if primary:
            pid = str(primary)
            for img in images:
                img["is_primary"] = str(img.get("id")) == pid
            if images and not any(img.get("is_primary") for img in images):
                images[0]["is_primary"] = True

        target["images"] = images
        target["updated_at"] = _now()
        self._save(order_id, products)
        return {"ok": True, "product": self._public_product(order_id, target)}

    def delete_image(
        self, order_id: str, product_id: str, image_id: str
    ) -> dict[str, Any]:
        products = self._load(order_id)
        target = None
        for p in products:
            if p.get("id") == product_id:
                target = p
                break
        if target is None:
            raise ValueError("catalog_product_not_found")

        images = [
            img for img in (target.get("images") or []) if isinstance(img, dict)
        ]
        keep: list[dict[str, Any]] = []
        removed = None
        for img in images:
            if str(img.get("id")) == image_id:
                removed = img
                continue
            keep.append(img)
        if removed is None:
            raise ValueError("image_not_found")
        self._media.delete_file(str(removed.get("path") or ""))
        for i, img in enumerate(keep):
            img["sort"] = i
        if keep and not any(img.get("is_primary") for img in keep):
            keep[0]["is_primary"] = True
        target["images"] = keep
        target["updated_at"] = _now()
        self._save(order_id, products)
        return {"ok": True, "product": self._public_product(order_id, target)}

    def resolve_media(self, order_id: str, image_id: str) -> Path:
        for p in self._load(order_id):
            for img in p.get("images") or []:
                if isinstance(img, dict) and str(img.get("id")) == image_id:
                    return self._media.resolve_path(str(img.get("path") or ""))
        raise ValueError("image_not_found")

    def ai_generate(
        self,
        order_id: str,
        payload: dict[str, Any],
        *,
        store_name: str = "",
        store_category: str = "",
    ) -> dict[str, Any]:
        hint = str(payload.get("hint") or payload.get("title") or "").strip()
        if not hint:
            raise ValueError("hint_required")
        language = str(payload.get("language") or "en")
        product_type = str(payload.get("product_type") or "physical")
        if product_type not in PRODUCT_TYPE_VALUES:
            product_type = "physical"
        return generate_product_fields(
            hint=hint,
            store_name=store_name,
            store_category=store_category,
            language=language,
            product_type=product_type,
        )
