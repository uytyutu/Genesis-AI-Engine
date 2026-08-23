"""StoreFactoryService — generate / publish / regenerate / rollback AI Store HTML."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.factory.store_factory.composer import write_storefront
from app.factory.store_factory.manifest import (
    append_generation_log,
    default_store_meta,
    list_html_pages,
    load_json,
    read_generation_log,
    save_json,
    utc_now,
)
from app.factory.store_factory.quality import run_shop_quality_gate
from app.factory.store_factory.templates import StoreTemplateRegistry


class StoreFactoryService:
    def __init__(self, memory_dir: Path, sandbox_dir: Path | None = None) -> None:
        self._memory = Path(memory_dir)
        self._sandbox = Path(sandbox_dir) if sandbox_dir else self._memory / "sandbox"
        self._sandbox.mkdir(parents=True, exist_ok=True)
        self._published_root = self._sandbox.parent / "published"
        self._registry = StoreTemplateRegistry()

    def product_dir(self, product_id: str) -> Path:
        return self._sandbox / product_id

    def published_dir(self, product_id: str) -> Path:
        return self._published_root / product_id

    def load_store_meta(self, product_id: str) -> dict[str, Any]:
        return load_json(self.product_dir(product_id) / "store_meta.json")

    def generation_log(self, product_id: str, *, limit: int = 80) -> list[dict[str, Any]]:
        return read_generation_log(self.product_dir(product_id), limit=limit)

    def live_url(self, order_id: str) -> str:
        return f"/api/client/stores/{order_id}/live"

    def preview_url(self, product_id: str) -> str:
        return f"/api/factory/products/{product_id}/preview"

    def _snapshot_version(self, product_dir: Path, version: int) -> Path:
        dest = product_dir / "versions" / f"v{version}"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for item in product_dir.iterdir():
            if item.name in ("versions", "generation_log.jsonl"):
                continue
            target = dest / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        return dest

    def _restore_version(self, product_dir: Path, version: int) -> None:
        src = product_dir / "versions" / f"v{version}"
        if not src.is_dir():
            raise ValueError("version_not_found")
        for item in list(product_dir.iterdir()):
            if item.name in ("versions", "generation_log.jsonl"):
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        for item in src.iterdir():
            target = product_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    def _write_product_meta(
        self,
        product_dir: Path,
        *,
        product_id: str,
        order: dict[str, Any],
        brief: dict[str, Any],
        template_id: str,
        version: int,
        quality: dict[str, Any],
    ) -> None:
        # Drop in-memory StudioPlan object — meta.json must be JSON-safe.
        brief_meta = {
            k: v
            for k, v in (brief or {}).items()
            if k != "_studio_plan" and not hasattr(v, "as_dict")
        }
        meta = {
            "id": product_id,
            "product_id": product_id,
            "product_kind": "shop",
            "order_id": order.get("id") or order.get("order_id"),
            "business_name": brief.get("store_name") or order.get("business_name"),
            "package_id": "ecommerce_shop",
            "market_code": order.get("market_code") or "DE",
            "shop_brief": brief_meta,
            "template_id": template_id,
            "version": version,
            "status": "ready",
            "owner_approved": True,
            "published": False,
            "quality_gate": quality,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        save_json(product_dir / "meta.json", meta)

    def generate_from_order(
        self,
        order: dict[str, Any],
        *,
        product_id: str | None = None,
        bump_version: bool = True,
    ) -> dict[str, Any]:
        from app.integration.shop_brief import validate_shop_brief

        order_id = str(order.get("id") or order.get("order_id") or "").strip()
        if not order_id:
            raise ValueError("order_id_required")

        brief_raw = order.get("shop_brief")
        brief = validate_shop_brief(
            brief_raw
            if isinstance(brief_raw, dict)
            else {
                "company_name": order.get("business_name"),
                "store_name": order.get("business_name"),
                "what_is_sold": order.get("description"),
            }
        )
        # Ensure legal pages for DACH when market is known on the order.
        if not isinstance(brief.get("market_code"), str) or not brief.get("market_code"):
            brief = {**brief, "market_code": str(order.get("market_code") or "DE")}

        existing_id = str(product_id or order.get("product_id") or "").strip()
        pid = existing_id or f"shop-{uuid.uuid4().hex[:12]}"
        product_dir = self.product_dir(pid)
        product_dir.mkdir(parents=True, exist_ok=True)

        store_meta = self.load_store_meta(pid) or default_store_meta(
            order_id=order_id,
            product_id=pid,
            template_id="",
        )
        current = int(store_meta.get("current_version") or 0)
        version = current + 1 if bump_version or current == 0 else max(1, current)
        if current == 0:
            version = 1

        store_pkg = str(
            order.get("package_id")
            or brief.get("package_id")
            or order.get("path_a_package")
            or "business"
        ).strip().lower() or "business"
        if store_pkg in ("starter", "ai_store", "shop"):
            store_pkg = "business" if store_pkg != "starter" else "basic"
        catalog_n = brief.get("catalog_size") or brief.get("product_count")
        try:
            catalog_n = int(catalog_n) if catalog_n is not None else None
        except (TypeError, ValueError):
            catalog_n = None
        # Resolve AFTER package/catalog are known — demo product count depends on them.
        brief = {
            **brief,
            "package_id": store_pkg if store_pkg in ("basic", "business", "premium") else "business",
            "catalog_size": catalog_n or {"basic": 12, "business": 18, "premium": 24}.get(
                store_pkg if store_pkg in ("basic", "business", "premium") else "business",
                18,
            ),
        }
        catalog_n = int(brief["catalog_size"])
        resolved = self._registry.resolve(brief)
        from app.factory.visual_intelligence.store_director import decide_store_experience
        from app.factory.visual_intelligence.studio import convene_board

        store_director = decide_store_experience(
            package_id=store_pkg,
            category=str(brief.get("category") or brief.get("what_is_sold") or "")
            or None,
            catalog_size=catalog_n,
        )
        # Store packages map to website ladder for Creative Director emotion brief.
        creative_pkg = store_pkg if store_pkg in ("basic", "business", "premium") else "business"
        from app.factory.visual_intelligence.studio import convene_board

        studio_plan = convene_board(
            package_id=creative_pkg,
            niche=str(brief.get("niche") or brief.get("category") or "generic"),
            market_code=str(brief.get("market_code") or order.get("market_code") or "DE"),
            goal="commerce",
            surface="store",
            catalog_size=catalog_n,
            category=str(brief.get("category") or "") or None,
        )
        creative_brief = studio_plan.creative
        brief = {
            **brief,
            "package_id": creative_pkg,
            "store_director": store_director,
            "creative_director": creative_brief,
            "digital_creative_studio": studio_plan.as_dict(),
            "_studio_plan": studio_plan,
        }
        append_generation_log(
            product_dir,
            "generating",
            {
                "version": version,
                "template_id": resolved.template_id,
                "store_director": store_director.get("engine"),
                "luxury_mode": bool(creative_brief.get("luxury_mode")),
            },
        )

        written = write_storefront(product_dir, brief=brief, resolved=resolved)

        try:
            from app.factory.studio_critic import run_studio_critic

            critic = run_studio_critic(
                product_dir,
                niche_id=str(brief.get("niche_id") or brief.get("niche") or ""),
                brand_name=str(brief.get("store_name") or brief.get("business_name") or ""),
                package_id=str(brief.get("package_id") or creative_pkg or ""),
            )
            brief["studio_critic"] = critic.as_dict()
            if critic.rebuild and str(brief.get("package_id") or "").lower() in (
                "premium",
                "connected",
            ):
                brief["studio_critic_rebuild_recommended"] = True
        except Exception:
            pass

        # User Data Protection Rule: Factory never wipes owner design/catalog.
        # Re-apply Store Admin Design overlay onto freshly generated HTML.
        try:
            from app.integration.store_admin.design_apply import (
                apply_design_to_product_dir,
            )

            apply_design_to_product_dir(
                self._memory,
                order_id,
                product_dir,
                store_name=str(brief.get("store_name") or ""),
            )
        except Exception:
            pass

        quality = run_shop_quality_gate(
            product_dir, brief=brief, colors=resolved.colors
        )
        append_generation_log(
            product_dir,
            "quality_check",
            {"passed": quality.passed, "errors": quality.errors},
        )

        self._write_product_meta(
            product_dir,
            product_id=pid,
            order=order,
            brief=brief,
            template_id=resolved.template_id,
            version=version,
            quality=quality.as_dict(),
        )

        self._snapshot_version(product_dir, version)

        versions = list(store_meta.get("versions") or [])
        versions = [v for v in versions if int(v.get("version") or 0) != version]
        versions.append(
            {
                "version": version,
                "created_at": utc_now(),
                "template_id": resolved.template_id,
                "pages": written,
                "quality_passed": quality.passed,
            }
        )
        store_meta.update(
            {
                "order_id": order_id,
                "product_id": pid,
                "product_kind": "shop",
                "template_id": resolved.template_id,
                "pipeline": "ready_to_publish" if quality.passed else "factory_queue",
                "current_version": version,
                "versions": versions,
                "quality": quality.as_dict(),
                "store_director": store_director,
                "creative_director": creative_brief,
                "digital_creative_studio": studio_plan.as_dict(),
                "luxury_mode": bool(creative_brief.get("luxury_mode")),
                "studio_critic": brief.get("studio_critic"),
                "studio_critic_rebuild_recommended": brief.get(
                    "studio_critic_rebuild_recommended"
                ),
                "updated_at": utc_now(),
            }
        )
        save_json(product_dir / "store_meta.json", store_meta)
        append_generation_log(
            product_dir,
            "version_saved",
            {"version": version, "pages": written},
        )

        return {
            "ok": quality.passed,
            "product_id": pid,
            "version": version,
            "template_id": resolved.template_id,
            "pages": written,
            "quality": quality.as_dict(),
            "store_meta": store_meta,
        }

    def publish(self, product_id: str, *, order_id: str | None = None) -> dict[str, Any]:
        product_dir = self.product_dir(product_id)
        if not (product_dir / "index.html").is_file():
            raise ValueError("product_not_found")

        meta = load_json(product_dir / "meta.json")
        store_meta = self.load_store_meta(product_id) or {}
        oid = str(order_id or store_meta.get("order_id") or meta.get("order_id") or "")
        if oid:
            try:
                from app.integration.store_admin.design_apply import (
                    apply_design_to_product_dir,
                )

                apply_design_to_product_dir(self._memory, oid, product_dir)
            except Exception:
                pass
        published_url = self.live_url(oid) if oid else self.preview_url(product_id)
        now = utc_now()

        meta["published"] = True
        meta["published_at"] = now
        meta["status"] = "published"
        meta["public_url"] = published_url
        meta["owner_approved"] = True
        meta["updated_at"] = now
        save_json(product_dir / "meta.json", meta)

        store_meta["published"] = True
        store_meta["published_at"] = now
        store_meta["published_url"] = published_url
        store_meta["pipeline"] = "published"
        store_meta["updated_at"] = now
        save_json(product_dir / "store_meta.json", store_meta)

        self._published_root.mkdir(parents=True, exist_ok=True)
        dest = self.published_dir(product_id)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(product_dir, dest)

        append_generation_log(
            product_dir, "published", {"published_url": published_url}
        )
        return {
            "ok": True,
            "product_id": product_id,
            "published_url": published_url,
            "preview_url": self.preview_url(product_id),
            "version": store_meta.get("current_version"),
            "store_meta": store_meta,
        }

    def regenerate(self, order: dict[str, Any]) -> dict[str, Any]:
        result = self.generate_from_order(order, bump_version=True)
        if not result.get("ok"):
            return result
        pub = self.publish(
            result["product_id"],
            order_id=str(order.get("id") or order.get("order_id") or ""),
        )
        result["publish"] = pub
        result["published_url"] = pub.get("published_url")
        return result

    def rollback(self, product_id: str, version: int, *, order_id: str | None = None) -> dict[str, Any]:
        product_dir = self.product_dir(product_id)
        store_meta = self.load_store_meta(product_id)
        if not store_meta:
            raise ValueError("product_not_found")
        ver = int(version)
        known = {int(v.get("version") or 0) for v in (store_meta.get("versions") or [])}
        if ver not in known:
            raise ValueError("version_not_found")

        self._restore_version(product_dir, ver)
        # Re-apply owner design after snapshot restore (User Data Protection).
        try:
            from app.integration.store_admin.design_apply import (
                apply_design_to_product_dir,
            )

            oid = str(order_id or store_meta.get("order_id") or "")
            if oid:
                apply_design_to_product_dir(self._memory, oid, product_dir)
        except Exception:
            pass
        store_meta["current_version"] = ver
        store_meta["updated_at"] = utc_now()
        store_meta["pipeline"] = "ready_to_publish"
        save_json(product_dir / "store_meta.json", store_meta)
        append_generation_log(product_dir, "rollback", {"version": ver})

        pub = self.publish(product_id, order_id=order_id or store_meta.get("order_id"))
        return {
            "ok": True,
            "product_id": product_id,
            "version": ver,
            "published_url": pub.get("published_url"),
            "store_meta": self.load_store_meta(product_id),
        }

    def resolve_live_file(self, product_id: str, rel_path: str = "index.html") -> Path:
        rel = str(rel_path or "index.html").replace("\\", "/").lstrip("/")
        if ".." in rel.split("/"):
            raise ValueError("invalid_path")
        if not rel or rel.endswith("/"):
            rel = "index.html"
        for root in (self.published_dir(product_id), self.product_dir(product_id)):
            path = (root / rel).resolve()
            try:
                path.relative_to(root.resolve())
            except ValueError as exc:
                raise ValueError("invalid_path") from exc
            if path.is_file():
                return path
        raise ValueError("product_not_found")

    def read_live_html(self, product_id: str, page: str = "index.html") -> str:
        path = self.resolve_live_file(product_id, page)
        if path.suffix.lower() != ".html":
            raise ValueError("product_not_found")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def rewrite_live_urls(
        text: str, *, order_id: str, relative_dir: str = ""
    ) -> str:
        """Rewrite relative href/src/url(...) to the store live asset base."""
        import re
        from pathlib import PurePosixPath

        base = f"/api/client/stores/{order_id}/live"

        def _norm(target: str) -> str | None:
            t = (target or "").strip()
            if not t or t.startswith(
                ("http://", "https://", "/", "#", "mailto:", "data:", "javascript:")
            ) or t.startswith(base):
                return None
            joined = PurePosixPath(relative_dir or ".") / t
            parts: list[str] = []
            for part in joined.parts:
                if part in ("", "."):
                    continue
                if part == "..":
                    if parts:
                        parts.pop()
                    continue
                parts.append(part)
            return "/".join(parts) if parts else None

        def _href(match: re.Match[str]) -> str:
            attr, quote, target = match.group(1), match.group(2), match.group(3)
            cleaned = _norm(target)
            if cleaned is None:
                return match.group(0)
            return f"{attr}={quote}{base}/{cleaned}{quote}"

        text = re.sub(r'(href|src)=([\'"])([^\'"]+)\2', _href, text, flags=re.I)

        def _css_url(match: re.Match[str]) -> str:
            quote, target = match.group(1) or "", match.group(2)
            cleaned = _norm(target)
            if cleaned is None:
                return match.group(0)
            if quote:
                return f"url({quote}{base}/{cleaned}{quote})"
            return f"url({base}/{cleaned})"

        return re.sub(
            r"url\(\s*([\'\"]?)([^)\'\"]+)\1\s*\)",
            _css_url,
            text,
            flags=re.I,
        )

    @classmethod
    def rewrite_live_html(cls, html: str, order_id: str) -> str:
        """Point relative page/asset links at the live API base."""
        import re

        base = f"/api/client/stores/{order_id}/live"
        boot = (
            "<script>"
            f"window.__VIRTUS_STORE__={{orderId:{json.dumps(order_id)},"
            f"apiBase:'/api/store/{order_id}',accountPath:'account.html'}};"
            "</script>"
        )
        if "__VIRTUS_STORE__" not in html:
            if re.search(r"</head>", html, flags=re.I):
                html = re.sub(
                    r"</head>", f"  {boot}\n</head>", html, count=1, flags=re.I
                )
            else:
                html = boot + html

        html = cls.rewrite_live_urls(html, order_id=order_id, relative_dir="")
        if not re.search(r"<base\b", html, flags=re.I):
            tag = f'<base href="{base}/" />'
            if re.search(r"<head\b[^>]*>", html, flags=re.I):
                html = re.sub(
                    r"(<head\b[^>]*>)", rf"\1\n  {tag}", html, count=1, flags=re.I
                )
            else:
                html = f"{tag}\n{html}"
        return html

    def status_payload(self, product_id: str | None) -> dict[str, Any]:
        if not product_id:
            return {"product_id": None, "pipeline": None, "version": None}
        meta = self.load_store_meta(product_id)
        pages = list_html_pages(self.product_dir(product_id))
        return {
            "product_id": product_id,
            "pipeline": meta.get("pipeline"),
            "version": meta.get("current_version"),
            "published": bool(meta.get("published")),
            "published_url": meta.get("published_url"),
            "template_id": meta.get("template_id"),
            "versions": meta.get("versions") or [],
            "pages": pages,
            "quality": meta.get("quality"),
        }
