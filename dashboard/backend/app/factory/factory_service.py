"""Factory v0.1 — Landing Page production department (sandbox only)."""

from __future__ import annotations

import io
import json
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.client_legal_pages import ClientLegalInfo, write_client_legal_pages
from app.factory.composer_engine import compose_landing
from app.factory.compliance_engine import assert_compliance, ComplianceError
from app.factory.landing_patcher import try_patch
from app.factory.layout_variants import profile_as_dict
from app.factory.market_design import resolve_market_design
from app.factory.quality_gate import QualityGateError
from app.factory.validator import owner_review_check, validate_landing

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_SANDBOX = _BACKEND_ROOT / "sandbox"
_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


class FactoryService:
    def __init__(self, memory_dir: Path | None = None, sandbox_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        if sandbox_dir is not None:
            self._sandbox = sandbox_dir
        elif memory_dir is not None:
            self._sandbox = memory_dir / "sandbox"
        else:
            self._sandbox = _DEFAULT_SANDBOX
        self._memory.mkdir(parents=True, exist_ok=True)
        self._sandbox.mkdir(parents=True, exist_ok=True)

    def build_landing(
        self,
        description: str,
        intent_id: str | None = None,
        *,
        client_legal: dict | None = None,
        package_id: str | None = None,
        contacts: dict | None = None,
        market_code: str | None = None,
        motion_level: str | None = None,
    ) -> dict:
        from app.factory.package_features import (
            apply_order_contacts,
            delivery_meta,
            resolve_package_features,
        )
        from app.factory.market_delivery import normalize_market
        from app.factory.motion_brief import gate_motion_level, normalize_motion_level
        from app.factory.css_motion import write_motion_assets
        from app.factory.ux_polish import write_ux_polish_assets

        product_id = intent_id or str(uuid.uuid4())
        analysis = analyze(description)
        contacts = contacts if isinstance(contacts, dict) else {}
        market = normalize_market(
            market_code
            or contacts.get("market_code")
            or (client_legal or {}).get("country")
            or "DE"
        )
        motion_raw = (
            motion_level
            or contacts.get("motion_level")
            or (
                "css"
                if str(package_id or contacts.get("package_id") or "basic").strip().lower()
                in ("business", "premium")
                else "none"
            )
        )
        gate = gate_motion_level(str(motion_raw))
        if not gate["ok"]:
            raise ValueError("WAITLIST_REQUIRED")
        motion = normalize_motion_level(gate["motion_level"])
        analysis = apply_order_contacts(
            analysis,
            business_name=str(contacts.get("business_name") or "") or None,
            phone=str(contacts.get("phone") or "") or None,
            email=str(contacts.get("email") or "") or None,
        )
        features = resolve_package_features(package_id or contacts.get("package_id"))
        city = str(contacts.get("city") or "").strip()
        street = str(contacts.get("street") or "").strip()
        whatsapp = str(contacts.get("whatsapp") or contacts.get("phone") or "").strip()

        product_dir = self._sandbox / product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        from app.factory.catalog_manager import CatalogManager, write_catalog_assets

        # Catalog Engine off for Path A service landings (CEO: лишний на сайтах).
        catalog_view = None
        if features.catalog_grid:
            catalog_view = CatalogManager(product_dir / "catalog").resolve_for_build(
                analysis.niche,
                features.package_id,
                seed_if_missing=True,
            )
        if motion == "css":
            write_motion_assets(product_dir)
        write_ux_polish_assets(product_dir)
        from app.factory.hero_still import write_hero_asset

        write_hero_asset(product_dir, analysis.niche, features.package_id)
        if catalog_view is not None:
            write_catalog_assets(product_dir, catalog_view)

        from app.factory.client_assets import apply_client_assets
        from app.factory.brand_style import normalize_brand_style

        materials = contacts.get("materials")
        if not isinstance(materials, list):
            materials = []
        client_assets = apply_client_assets(product_dir, materials)
        brand_style_id = normalize_brand_style(str(contacts.get("brand_style") or ""))

        pack_manifest: dict = {}
        pack_manifest_path = product_dir / "assets" / "hero_pack" / "manifest.json"
        if pack_manifest_path.is_file():
            try:
                pack_manifest = json.loads(pack_manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pack_manifest = {}

        composed = compose_landing(
            analysis,
            features=features,
            whatsapp=whatsapp,
            city=city,
            street=street,
            motion_level=motion,
            market_code=market,
            catalog=catalog_view,
            hero_pack_manifest=pack_manifest,
            client_logo=client_assets.logo,
            client_logo_src=client_assets.logo_src,
            client_gallery=list(client_assets.gallery),
            brand_style=brand_style_id,
            client_trust=contacts.get("trust") if isinstance(contacts.get("trust"), dict) else None,
            product_dir=product_dir,
            hero_from_client=client_assets.hero_from_client,
        )
        html = composed.html
        plan = composed.plan
        if composed.analysis is not None:
            analysis = composed.analysis
        client_assets.gallery = list(composed.gallery)
        client_assets.hero_from_client = composed.hero_from_client
        media_plan = composed.media_plan
        content_gate = composed.content_gate

        gate_meta = plan.gate_meta()
        gate_meta["niche"] = analysis.niche
        gate_meta["content_gate"] = content_gate
        validation = validate_landing(
            html,
            meta=gate_meta,
            assets_dir=product_dir / "assets",
        )
        (product_dir / "index.html").write_text(html, encoding="utf-8")

        legal_payload = dict(client_legal or {})
        if features.maps:
            legal_payload["uses_maps"] = True
        if features.analytics:
            legal_payload["uses_analytics"] = True
        legal_info = ClientLegalInfo.from_order(
            {
                "business_name": analysis.business_name,
                "client_legal": legal_payload,
                "city": city,
            }
        )
        legal_info.country = market
        if not legal_info.email and analysis.email:
            legal_info.email = analysis.email
        if not legal_info.phone and analysis.phone:
            legal_info.phone = analysis.phone
        if not legal_info.business_name:
            legal_info.business_name = analysis.business_name
        legal_meta = write_client_legal_pages(
            product_dir, legal_info, market_code=market
        )

        meta = {
            "product_id": product_id,
            "intent_id": intent_id,
            "product_type": "Landing Page",
            "description": description,
            "niche": analysis.niche,
            "template_id": analysis.template_id,
            "business_name": analysis.business_name,
            "market_code": market,
            "market_design": resolve_market_design(market).market_id,
            "motion_level": motion,
            "composer_engine": plan.engine_id,
            "composition_plan": plan.as_dict(),
            "hero_layout": plan.hero_layout,
            "component_profile": plan.component_profile,
            "layout_profile": profile_as_dict(plan.layout_profile),
            "trust_template": plan.trust_template,
            "media_plan": media_plan,
            "content_gate": content_gate,
            "status": "completed",
            "quality_percent": validation.quality_percent,
            "validation_passed": validation.passed,
            "technical_checks": validation.technical_checks,
            "quality_gate": validation.quality_gate,
            "compliance": validation.compliance,
            "owner_approved": False,
            "owner_approved_at": None,
            "revision": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "style_flags": {
                "modern": features.premium_design,
                "blue_boost": False,
                "calculator": features.calculator,
                "testimonials": features.testimonials,
            },
            "package_delivery": delivery_meta(features),
            "catalog_enabled": catalog_view is not None,
            "client_assets": client_assets.as_dict(),
            "brand_style": brand_style_id,
            "client_legal": legal_info.to_dict(),
            "legal_pages": legal_meta,
            "publish_ready_de": bool(legal_meta.get("impressum_ready"))
            if legal_meta.get("pack") == "de_impressum"
            else False,
        }
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._product_summary(meta)

    def build_landing_from_opportunity(self, opportunity: dict) -> dict:
        """Factory landing grounded in Engine stealth scan — repair offer, not generic fluff."""
        analysis = opportunity.get("site_analysis") if isinstance(opportunity.get("site_analysis"), dict) else {}
        meta = opportunity.get("meta") if isinstance(opportunity.get("meta"), dict) else {}
        company = str(opportunity.get("company_name") or analysis.get("title") or "Business").strip()
        issues = [str(i) for i in (analysis.get("issues") or []) if str(i).strip()]
        strengths = [str(s) for s in (analysis.get("strengths") or [])[:2]]
        niche = str(meta.get("niche") or "local_service")
        url = str(opportunity.get("website_url") or analysis.get("url") or "")

        issue_line = "; ".join(issues[:4]) if issues else "veralteter Web-Auftritt"
        strength_line = "; ".join(strengths) if strengths else ""
        description = (
            f"{company}. Website: {url}. Nische: {niche}. "
            f"Gefundene Probleme (Stealth-Scan): {issue_line}."
        )
        if strength_line:
            description += f" Stärken: {strength_line}."
        description += " Ziel: neue Landing Page (digitaler Neustart) — Hilfe, kein Spam."

        return self.build_landing(description[:900])

    def improve(self, product_id: str, feedback: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")

        flags = dict(meta.get("style_flags", {}))
        lower = feedback.lower()
        product_dir = self._sandbox / product_id
        existing_html = (product_dir / "index.html").read_text(encoding="utf-8")
        catalog_view = None
        package_id = str(
            ((meta.get("package_delivery") or {}) if isinstance(meta.get("package_delivery"), dict) else {}).get(
                "package_id"
            )
            or "basic"
        )

        patched_html, patches = try_patch(existing_html, feedback)
        if patches:
            html = patched_html
            flags["last_patches"] = patches
        else:
            if any(w in lower for w in ("син", "blue", "голуб")):
                flags["blue_boost"] = True
            if any(w in lower for w in ("современ", "modern", "минимал")):
                flags["modern"] = True
            if any(w in lower for w in ("калькулятор", "calculator", "расчёт", "расчет")):
                flags["calculator"] = True
            if any(w in lower for w in ("отзыв", "review")):
                flags["testimonials"] = True
            if any(w in lower for w in ("крупн", "заголовок")):
                flags["large_headline"] = True

            analysis = analyze(meta["description"])
            from app.factory.market_delivery import normalize_market
            from app.factory.package_features import resolve_package_features

            delivery = meta.get("package_delivery") if isinstance(meta.get("package_delivery"), dict) else {}
            features = resolve_package_features(str(delivery.get("package_id") or "basic"))
            package_id = features.package_id
            contacts = meta.get("client_legal") if isinstance(meta.get("client_legal"), dict) else {}
            market = normalize_market(str(meta.get("market_code") or contacts.get("country") or "DE"))
            from app.factory.catalog_manager import CatalogManager, write_catalog_assets

            catalog_view = CatalogManager(product_dir / "catalog").resolve_for_build(
                str(meta.get("niche") or analysis.niche),
                features.package_id,
                seed_if_missing=True,
            )
            write_hero_asset = __import__(
                "app.factory.hero_still", fromlist=["write_hero_asset"]
            ).write_hero_asset
            write_hero_asset(product_dir, str(meta.get("niche") or analysis.niche), package_id)
            from app.factory.ux_polish import write_ux_polish_assets

            write_ux_polish_assets(product_dir)
            if catalog_view is not None:
                write_catalog_assets(product_dir, catalog_view)
            pack_manifest: dict = {}
            mp = product_dir / "assets" / "hero_pack" / "manifest.json"
            if mp.is_file():
                try:
                    pack_manifest = json.loads(mp.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pack_manifest = {}
            ca = meta.get("client_assets") if isinstance(meta.get("client_assets"), dict) else {}
            trust_payload = None
            if isinstance(meta.get("client_legal"), dict) and isinstance(
                meta["client_legal"].get("trust"), dict
            ):
                trust_payload = meta["client_legal"].get("trust")
            composed = compose_landing(
                analysis,
                features=features,
                whatsapp=str(contacts.get("phone") or ""),
                city=str(contacts.get("city") or ""),
                street=str(contacts.get("street") or ""),
                modern=flags.get("modern", False) or features.premium_design,
                blue_boost=flags.get("blue_boost", False),
                calculator=flags.get("calculator", False) or features.calculator,
                include_testimonials=flags.get("testimonials", False) or features.testimonials,
                large_headline=flags.get("large_headline", False) or features.premium_design,
                market_code=market,
                catalog=catalog_view,
                hero_pack_manifest=pack_manifest,
                client_logo=bool(ca.get("logo")),
                client_logo_src=str(ca.get("logo_src") or "assets/logo.png"),
                client_gallery=list(ca.get("gallery") or []),
                brand_style=str(meta.get("brand_style") or "") or None,
                client_trust=trust_payload,
                product_dir=product_dir,
                hero_from_client=bool(ca.get("hero_from_client")),
            )
            html = composed.html
            ca = dict(ca)
            ca["gallery"] = list(composed.gallery)
            ca["hero_from_client"] = composed.hero_from_client
            meta["client_assets"] = ca
            meta["media_plan"] = composed.media_plan
            meta["content_gate"] = composed.content_gate
            meta["composer_engine"] = composed.plan.engine_id
            meta["composition_plan"] = composed.plan.as_dict()
            meta["hero_layout"] = composed.plan.hero_layout
            meta["component_profile"] = composed.plan.component_profile
            meta["layout_profile"] = profile_as_dict(composed.plan.layout_profile)
            meta["trust_template"] = composed.plan.trust_template

        validation = validate_landing(
            html,
            meta=meta,
            assets_dir=product_dir / "assets",
        )

        (product_dir / "index.html").write_text(html, encoding="utf-8")
        if catalog_view is not None:
            from app.factory.catalog_manager import write_catalog_assets

            write_catalog_assets(product_dir, catalog_view)

        meta["revision"] = int(meta.get("revision", 0)) + 1
        meta["quality_percent"] = validation.quality_percent
        meta["validation_passed"] = validation.passed
        meta["technical_checks"] = validation.technical_checks
        meta["quality_gate"] = validation.quality_gate
        meta["compliance"] = validation.compliance
        meta["owner_approved"] = False
        meta["owner_approved_at"] = None
        meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        meta["last_feedback"] = feedback.strip()
        meta["style_flags"] = flags
        meta["status"] = "completed"
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._product_summary(meta)

    def approve(self, product_id: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        meta["owner_approved"] = True
        meta["owner_approved_at"] = datetime.now(timezone.utc).isoformat()
        meta["status"] = "owner_approved"
        (self._sandbox / product_id / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self._product_summary(meta)

    def publish(self, product_id: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        if not meta.get("owner_approved"):
            raise ValueError("not_approved")
        meta["published"] = True
        meta["published_at"] = datetime.now(timezone.utc).isoformat()
        meta["status"] = "published"
        meta["public_url"] = f"/api/factory/products/{product_id}/preview"
        product_dir = self._sandbox / product_id
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        published_root = self._sandbox.parent / "published"
        published_root.mkdir(parents=True, exist_ok=True)
        dest = published_root / product_id
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(product_dir, dest)
        self._touch_milestone("published", True)
        return self._product_summary(meta)

    def build_export_zip(self, product_id: str) -> tuple[bytes, str]:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        if not meta.get("owner_approved"):
            raise ValueError("not_approved")
        if not meta.get("published"):
            raise ValueError("not_published")
        return self._pack_product_zip(product_id, meta, mark_download=True)

    def build_client_delivery_zip(self, product_id: str) -> tuple[bytes, str]:
        """Path A — client download after payment/production (no CEO approve gate)."""
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        return self._pack_product_zip(product_id, meta, mark_download=True)

    def _pack_product_zip(
        self,
        product_id: str,
        meta: dict,
        *,
        mark_download: bool,
    ) -> tuple[bytes, str]:
        from app.factory.market_delivery import deploy_readme, normalize_market
        from app.factory.client_legal_pages import ClientLegalInfo, write_client_legal_pages

        product_dir = self._sandbox / product_id
        html_path = product_dir / "index.html"
        if not html_path.is_file():
            raise ValueError("product_not_found")

        html = html_path.read_text(encoding="utf-8")
        try:
            compliance = assert_compliance(
                html,
                meta=meta,
                assets_dir=product_dir / "assets",
            )
        except ComplianceError as err:
            if err.result.quality_gate is not None:
                raise QualityGateError(err.result.quality_gate) from err
            raise
        meta["compliance"] = compliance.as_dict()

        market = normalize_market(str(meta.get("market_code") or "DE"))
        # Regenerate legal pages for this market on every pack (fixes legacy DE-only products).
        legal_info = ClientLegalInfo.from_order(
            {
                "business_name": meta.get("business_name"),
                "client_legal": meta.get("client_legal")
                if isinstance(meta.get("client_legal"), dict)
                else {},
            }
        )
        legal_info.country = market
        legal_meta = write_client_legal_pages(product_dir, legal_info, market_code=market)
        meta["market_code"] = market
        meta["legal_pages"] = legal_meta

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("index.html", html_path.read_text(encoding="utf-8"))
            for legal_name in legal_meta.get("files") or []:
                legal_path = product_dir / str(legal_name)
                if legal_path.is_file():
                    archive.writestr(str(legal_name), legal_path.read_text(encoding="utf-8"))
            assets_dir = product_dir / "assets"
            if assets_dir.is_dir():
                for asset in assets_dir.rglob("*"):
                    if not asset.is_file() or asset.name == ".gitkeep":
                        continue
                    rel = asset.relative_to(product_dir).as_posix()
                    archive.writestr(rel, asset.read_bytes())
            archive.writestr(
                "README_PUBLISH.txt",
                deploy_readme(
                    market,
                    package_id=str(
                        (meta.get("package_delivery") or {}).get("package_id")
                        or meta.get("package_id")
                        or "basic"
                    ),
                ),
            )

        if mark_download:
            meta["export_downloaded_at"] = datetime.now(timezone.utc).isoformat()
            meta["updated_at"] = meta["export_downloaded_at"]
            (product_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        slug = self._zip_slug(meta.get("business_name") or "", product_id)
        return buf.getvalue(), f"{slug}.zip"

    def mark_delivered(self, product_id: str) -> dict:
        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        if not meta.get("owner_approved"):
            raise ValueError("not_approved")
        if not meta.get("published"):
            raise ValueError("not_published")
        now = datetime.now(timezone.utc).isoformat()
        meta["delivered_to_client"] = True
        meta["delivered_at"] = now
        meta["status"] = "delivered"
        meta["updated_at"] = now
        product_dir = self._sandbox / product_id
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        published = self._sandbox.parent / "published" / product_id / "meta.json"
        if published.is_file():
            try:
                pub_meta = json.loads(published.read_text(encoding="utf-8"))
                pub_meta.update(
                    {
                        "delivered_to_client": True,
                        "delivered_at": now,
                        "status": "delivered",
                        "updated_at": now,
                    }
                )
                published.write_text(json.dumps(pub_meta, ensure_ascii=False, indent=2), encoding="utf-8")
            except (json.JSONDecodeError, OSError):
                pass
        self._touch_milestone("delivered_to_client", True)
        self._touch_milestone("owner_tested", True)
        return self._product_summary(meta)

    def _zip_slug(self, name: str, product_id: str) -> str:
        ascii_name = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
        ascii_name = re.sub(r"-{2,}", "-", ascii_name).strip("-")
        if ascii_name:
            return ascii_name[:40]
        return product_id[:12]

    def _client_handoff_message(self, meta: dict) -> str:
        name = meta.get("business_name") or "ваш сайт"
        return (
            f"Здравствуйте!\n\n"
            f"Ваш сайт «{name}» готов.\n\n"
            f"Во вложении — архив ZIP с файлом index.html и короткой инструкцией, "
            f"как разместить сайт в интернете.\n\n"
            f"Кратко:\n"
            f"1. Распакуйте архив\n"
            f"2. Откройте index.html в браузере и проверьте\n"
            f"3. Загрузите на хостинг (Netlify, GitHub Pages или ваш провайдер)\n\n"
            f"Если нужна помощь с размещением — напишите.\n\n"
            f"С уважением"
        )

    def _handoff_checklist(self, meta: dict) -> list[dict[str, str | bool]]:
        return [
            {"id": "preview", "label": "Просмотреть превью", "done": True},
            {
                "id": "approved",
                "label": "Одобрить для клиента (Owner Approved)",
                "done": bool(meta.get("owner_approved")),
            },
            {
                "id": "published",
                "label": "Подготовить к передаче (Publish)",
                "done": bool(meta.get("published")),
            },
            {
                "id": "download",
                "label": "Скачать ZIP и проверить файлы",
                "done": bool(meta.get("export_downloaded_at")),
            },
            {
                "id": "message",
                "label": "Отправить клиенту (WhatsApp / email + ZIP)",
                "done": bool(meta.get("delivered_to_client")),
            },
            {
                "id": "delivered",
                "label": "Передано клиенту",
                "done": bool(meta.get("delivered_to_client")),
            },
        ]

    def _touch_milestone(self, key: str, value: bool | int | str = True) -> None:
        path = self._memory / "owner_milestones.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        data[key] = value
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_product(self, product_id: str) -> dict | None:
        meta = self._load_meta(product_id)
        return self._product_summary(meta) if meta else None

    def list_products(self, limit: int = 50) -> list[dict]:
        items: list[dict] = []
        if not self._sandbox.exists():
            return items
        for path in sorted(self._sandbox.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not path.is_dir():
                continue
            meta = self._load_meta(path.name)
            if meta:
                items.append(self._product_summary(meta))
            if len(items) >= limit:
                break
        return items

    def latest_product(self) -> dict | None:
        products = self.list_products(limit=1)
        return products[0] if products else None

    def read_preview_html(self, product_id: str) -> str | None:
        html_path = self._sandbox / product_id / "index.html"
        if not html_path.exists():
            return None
        return html_path.read_text(encoding="utf-8")

    def _load_meta(self, product_id: str) -> dict | None:
        meta_path = self._sandbox / product_id / "meta.json"
        if not meta_path.exists():
            return None
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _product_summary(self, meta: dict) -> dict:
        pid = meta["product_id"]
        approved = bool(meta.get("owner_approved"))
        checks = list(meta.get("technical_checks", []))
        checks.append(owner_review_check(approved))
        return {
            "product_id": pid,
            "product_type": meta.get("product_type", "Landing Page"),
            "business_name": meta.get("business_name", ""),
            "description": meta.get("description", ""),
            "status": meta.get("status", "completed"),
            "status_label": self._status_label(meta),
            "quality_percent": int(meta.get("quality_percent", 0)),
            "checks": checks,
            "owner_approved": approved,
            "owner_approved_at": meta.get("owner_approved_at"),
            "published": bool(meta.get("published")),
            "published_at": meta.get("published_at"),
            "public_url": meta.get("public_url"),
            "revision": int(meta.get("revision", 0)),
            "niche": meta.get("niche", "generic"),
            "template_id": meta.get("template_id", ""),
            "motion_level": meta.get("motion_level", "none"),
            "hero_layout": meta.get("hero_layout"),
            "component_profile": meta.get("component_profile"),
            "quality_gate": meta.get("quality_gate"),
            "validation_passed": meta.get("validation_passed"),
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
            "preview_url": f"/api/factory/products/{pid}/preview",
            "delivered_to_client": bool(meta.get("delivered_to_client")),
            "delivered_at": meta.get("delivered_at"),
            "client_message": self._client_handoff_message(meta),
            "handoff_checklist": self._handoff_checklist(meta),
        }

    def _status_label(self, meta: dict) -> str:
        if meta.get("delivered_to_client"):
            return "Передано клиенту"
        if meta.get("published"):
            return "Published"
        if meta.get("owner_approved"):
            return "Owner Approved"
        if meta.get("status") == "completed":
            return "Completed"
        return str(meta.get("status", "completed"))
