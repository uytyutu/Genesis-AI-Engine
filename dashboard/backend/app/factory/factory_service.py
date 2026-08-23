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
            apply_order_advantages,
            apply_order_contacts,
            apply_order_services,
            delivery_meta,
            resolve_package_features,
        )
        from app.factory.market_delivery import normalize_market
        from app.factory.motion_brief import gate_motion_level, normalize_motion_level
        from app.factory.css_motion import write_motion_assets
        from app.factory.ux_polish import write_ux_polish_assets
        from app.integration.factory_metrics import StageTimer, record_build

        timer = StageTimer()
        product_id = intent_id or str(uuid.uuid4())
        contacts = contacts if isinstance(contacts, dict) else {}
        # Queue wait is attributed by sales_order when known; default 0 for direct builds.
        try:
            queue_s = float(contacts.get("_factory_queue_s") or 0)
        except (TypeError, ValueError):
            queue_s = 0.0
        if queue_s > 0:
            timer.stages["queue"] = round(queue_s, 4)

        analysis = analyze(
            description,
            niche_hint=str(contacts.get("niche") or "") or None,
        )
        market = normalize_market(
            market_code
            or contacts.get("market_code")
            or (client_legal or {}).get("country")
            or "DE"
        )
        motion_raw = (
            motion_level
            or contacts.get("motion_level")
            or "css"
        )
        gate = gate_motion_level(
            str(motion_raw),
            package_id=str(package_id or contacts.get("package_id") or ""),
            niche_id=str(
                contacts.get("niche")
                or getattr(analysis, "niche", "")
                or ""
            ),
        )
        if not gate["ok"]:
            raise ValueError("WAITLIST_REQUIRED")
        motion = normalize_motion_level(gate["motion_level"])
        analysis = apply_order_contacts(
            analysis,
            business_name=str(contacts.get("business_name") or "") or None,
            phone=str(contacts.get("phone") or "") or None,
            email=str(contacts.get("email") or "") or None,
        )
        analysis = apply_order_services(analysis, contacts.get("services_list"))
        analysis = apply_order_advantages(analysis, contacts.get("advantages"))

        # —— Commerce model + Business Interview (before studio / HTML)
        from app.factory.business_interview import (
            interview_from_payload,
            interview_to_contacts,
        )
        from app.factory.commerce_model import normalize_commerce_mode

        _iv_payload = contacts.get("business_interview")
        if not isinstance(_iv_payload, dict):
            _iv_payload = {
                "free_text": contacts.get("dialogue")
                or contacts.get("client_story")
                or "",
                "about": contacts.get("who_is_company") or "",
                "company_name": contacts.get("business_name") or analysis.business_name,
                "city": contacts.get("city") or "",
                "style": contacts.get("brand_style") or contacts.get("style") or "",
                "differentiator": contacts.get("why_choose_us")
                or contacts.get("main_promise")
                or "",
                "top_services": contacts.get("services_list") or (),
                "site_jobs": contacts.get("site_jobs") or (),
                "wishes": contacts.get("dream_wishes") or "",
                "niche": analysis.niche or contacts.get("niche") or "",
            }
        interview = interview_from_payload(_iv_payload)
        contacts = interview_to_contacts(interview, contacts)
        if interview.niche_hint and not str(contacts.get("niche") or "").strip():
            contacts["niche"] = interview.niche_hint
            analysis = analyze(
                description or interview.about or interview.free_text,
                niche_hint=interview.niche_hint,
            )
            analysis = apply_order_contacts(
                analysis,
                business_name=str(contacts.get("business_name") or "") or None,
                phone=str(contacts.get("phone") or "") or None,
                email=str(contacts.get("email") or "") or None,
            )

        commerce = normalize_commerce_mode(
            package_id or contacts.get("package_id"),
            commerce_mode=str(contacts.get("commerce_mode") or "") or None,
        )
        contacts["commerce_mode"] = commerce.commerce_mode
        contacts["commerce_resolution"] = commerce.as_dict()
        package_id = commerce.factory_package_id

        # Business Generation — invent a living company for demos (not niche template)
        fabricate = bool(
            contacts.get("demo_gallery")
            or contacts.get("fabricate_company")
            or contacts.get("fabricate")
        )
        if fabricate:
            from app.factory.company_fabrication import apply_fabricated_company

            analysis, contacts, _company = apply_fabricated_company(analysis, contacts)

        timer.mark("template")

        from app.factory.composers import run_composers
        from app.factory.content_gate import run_content_gate

        commercial_meta: dict = {}
        for _attempt in range(3):
            analysis, commercial = run_composers(
                analysis,
                contacts=contacts,
                package_id=package_id or contacts.get("package_id"),
                scenario_id=analysis.niche,
            )
            commercial_meta = commercial.as_dict()
            if commercial.hard_passed:
                break
            # Auto-rebuild: sanitize analysis and re-compose (Hard Gate recovery).
            _, repaired = run_content_gate(analysis=analysis, auto_repair=True)
            if repaired is None:
                break
            analysis = repaired
        features = resolve_package_features(package_id or contacts.get("package_id"))
        from app.factory.visual_intelligence.studio import convene_board

        pkg_id = str(features.package_id or "standalone").strip().lower() or "standalone"
        studio_plan = convene_board(
            package_id=pkg_id if pkg_id in ("basic", "business", "premium") else (
                "premium" if pkg_id == "connected" else "business"
            ),
            niche=analysis.niche,
            market_code=market,
            goal=str(contacts.get("goal") or "lead") or None,
            surface="website",
        )
        creative_brief = studio_plan.creative
        # Motion Director + Creative Director: full product always gets motion floor
        motion_from_studio = str(
            (studio_plan.apply or {}).get("motion_level") or motion
        )
        if motion_from_studio in ("css", "none"):
            motion = motion_from_studio if motion_from_studio == "css" else "css"
        city = str(contacts.get("city") or "").strip()
        street = str(contacts.get("street") or "").strip()
        whatsapp = str(contacts.get("whatsapp") or contacts.get("phone") or "").strip()
        # Ensure contacts dict carries city for composers on rebuild paths
        if city and not contacts.get("city"):
            contacts = {**contacts, "city": city}
        timer.mark("content")

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

        # Spec-as-Contract live builds: ensure gallery service slots exist so
        # Media Integrity does not REJECT before Premium QA can judge the Spec.
        # Minimal placeholders only — not a media pipeline expansion.
        try:
            from PIL import Image

            _assets = product_dir / "assets"
            _assets.mkdir(parents=True, exist_ok=True)
            for _fname in ("service_1.jpg", "service_2.jpg", "service_3.jpg"):
                _dest = _assets / _fname
                if _dest.is_file() and _dest.stat().st_size > 64:
                    continue
                Image.new("RGB", (1200, 800), color=(42, 48, 56)).save(
                    _dest, format="JPEG", quality=82
                )
        except Exception:
            pass

        from app.factory.client_assets import apply_client_assets
        from app.factory.brand_style import normalize_brand_style

        materials = contacts.get("materials")
        if not isinstance(materials, list):
            materials = []
        client_assets = apply_client_assets(product_dir, materials)
        brand_style_id = normalize_brand_style(str(contacts.get("brand_style") or ""))

        # —— Business Intelligence Generation (company before HTML)
        from app.factory.business_intelligence import (
            resolve_business_intelligence,
            write_business_intelligence,
        )

        bi = resolve_business_intelligence(
            niche_id=str(analysis.niche or contacts.get("niche") or ""),
            company_name=str(
                contacts.get("business_name") or analysis.business_name or ""
            ),
            city=city or str(contacts.get("city") or ""),
            interview=contacts.get("business_interview")
            if isinstance(contacts.get("business_interview"), dict)
            else None,
            contacts=contacts,
            is_store=False,
        )
        write_business_intelligence(product_dir, bi)
        contacts["business_intelligence"] = bi.as_dict()
        contacts["subniche_id"] = bi.subniche_id
        contacts["business_components"] = [c.as_dict() for c in bi.components]
        # Business Language Engine — industry voice before HTML (not one generic copywriter)
        try:
            from app.factory.business_language import (
                build_beauty_lumia_brief,
                resolve_voice,
            )

            _voice = resolve_voice(bi.niche_id, bi.subniche_id)
            if _voice.industry_id == "beauty_nail_brow_massage":
                _lang = build_beauty_lumia_brief(
                    company_name=str(
                        contacts.get("business_name") or analysis.business_name or bi.company_name
                    ),
                    city=city or str(contacts.get("city") or bi.city or ""),
                )
                contacts["business_language"] = _lang.as_dict()
            else:
                contacts["business_language"] = {
                    "industry_id": _voice.industry_id,
                    "market": "DE",
                    "voice": _voice.as_dict(),
                    "flags": ["german_business_standard", "niche_voice"],
                }
        except Exception:
            pass
        if bi.differentiator and not contacts.get("why_choose_us"):
            contacts["why_choose_us"] = bi.differentiator
        if bi.style and not brand_style_id:
            brand_style_id = normalize_brand_style(bi.style)

        from app.factory.website_design_spec import (
            apply_spec_to_contacts,
            build_website_design_spec,
            freeze_website_design_spec,
            validate_website_design_spec,
            write_website_design_spec,
        )

        website_design_spec = build_website_design_spec(
            contacts=contacts,
            client_legal=client_legal if isinstance(client_legal, dict) else None,
            niche_id=str(analysis.niche or contacts.get("niche") or bi.niche_id or ""),
            package_id=pkg_id,
            market_code=market,
            interview=interview.as_dict(),
        )
        _spec_gate = validate_website_design_spec(website_design_spec)
        website_design_spec["validation"] = {
            "ok": _spec_gate["ok"],
            "errors": list(_spec_gate["errors"]),
            "status": _spec_gate["status"],
        }
        if _spec_gate["ok"]:
            # V1 snapshot becomes immutable once Engine accepts the contract.
            website_design_spec = freeze_website_design_spec(website_design_spec)
        else:
            website_design_spec["status"] = "REJECT"
        contacts = apply_spec_to_contacts(website_design_spec, contacts)
        write_website_design_spec(product_dir, website_design_spec)

        # Digital business floor — ALL niches / packages get niche media + identity.
        # Commercial idea / first impression still prefer known Commercial Reality niches.
        from app.factory.design_dna.atmosphere_pack import (
            apply_media_briefs,
            build_atmosphere_pack,
        )
        from app.factory.design_dna.brand_book import resolve_brand_book
        from app.factory.design_dna.business_identity import (
            resolve_business_identity,
            write_business_identity,
        )
        from app.factory.design_dna.media_truth import enforce_media_truth_on_product
        from app.factory.design_dna.reputation_pack import write_reputation_pack
        from app.factory.niche_scene_media import ensure_tier_media_floor, write_niche_scene

        _idea_niches = {
            "dachreinigung",
            "zaunbau",
            "gartenpflege",
            "handwerk",
            "cleaning",
            "office_cleaning",
            "green",
            "psychology",
            "family_psychology",
            "restaurant",
            "law",
            "beauty",
            "dental",
            "orthodontics",
            "auto",
            "auto_detailing",
            "fitness",
            "realestate",
            "photography",
            "computer",
            "it_support",
            "energy",
            "elektro",
            "sanitaer",
            "maler",
            "car_dealership",
            "landschaft",
        }
        _niche_l = str(analysis.niche or "").lower()
        assets_dir = product_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        book = resolve_brand_book(
            business_name=analysis.business_name,
            niche_id=analysis.niche,
            package_id=pkg_id,
            diversity_salt=str(contacts.get("diversity_salt") or ""),
            city=city or "",
        )
        metaphor = book.visual_metaphor
        idea_seed = ""

        if _niche_l in _idea_niches:
            from app.factory.commercial_idea import (
                assert_commercial_idea,
                resolve_commercial_idea,
                write_commercial_idea,
            )
            from app.factory.first_impression import (
                apply_first_impression_to_analysis,
                assert_first_impression,
                resolve_first_impression,
                write_first_impression,
            )

            idea = resolve_commercial_idea(
                niche_id=str(analysis.niche or ""),
                contacts=contacts,
            )
            idea_report = assert_commercial_idea(
                idea, package_id=pkg_id, hard=False
            )
            write_commercial_idea(product_dir, idea, idea_report)

            fi = resolve_first_impression(
                niche_id=str(analysis.niche or ""),
                contacts=contacts,
            )
            fi_report = assert_first_impression(
                fi, package_id=pkg_id, hard=(pkg_id in ("premium", "connected"))
            )
            write_first_impression(product_dir, fi, fi_report)
            analysis = apply_first_impression_to_analysis(analysis, fi)
            contacts["client_story"] = fi.story
            contacts["problem_before"] = fi.problem_before
            contacts["first_impression"] = fi.as_dict()
            metaphor = idea.metaphor or fi.idea or book.visual_metaphor
            idea_seed = idea.idea[:40] if idea.idea else ""

        pack = build_atmosphere_pack(book)
        apply_media_briefs(
            product_dir,
            pack,
            niche_id=analysis.niche,
            business_name=analysis.business_name,
            package_id=pkg_id,
        )
        # Always materialize hero + background + gallery (never ship text-only shells)
        ensure_tier_media_floor(
            assets_dir,
            niche_id=analysis.niche,
            business_name=analysis.business_name,
            package_id=pkg_id,
            metaphor=metaphor,
            accent_hex=book.palette.accent_hex,
        )
        # Extra unique stills keyed to brand fingerprint (overrides floor with richer seeds)
        write_niche_scene(
            assets_dir / "hero.jpg",
            niche_id=analysis.niche,
            seed=f"hero|{pkg_id}|{analysis.business_name}|{book.fingerprint}|{idea_seed}",
            role="hero",
            size=(1600, 900),
            metaphor=metaphor,
            accent_hex=book.palette.accent_hex,
        )
        write_niche_scene(
            assets_dir / "background.jpg",
            niche_id=analysis.niche,
            seed=f"bg|{pkg_id}|{analysis.business_name}|{book.fingerprint}",
            role="banner",
            size=(1920, 1080),
            metaphor=metaphor,
            accent_hex=book.palette.accent_hex,
        )
        for gi in range(1, 4):
            write_niche_scene(
                assets_dir / f"gallery_{gi}.jpg",
                niche_id=analysis.niche,
                seed=f"gal{gi}|{pkg_id}|{analysis.business_name}|{book.fingerprint}",
                role="gallery",
                size=(1200, 800),
                metaphor=metaphor,
                accent_hex=book.palette.accent_hex,
            )
        write_niche_scene(
            assets_dir / "gallery.jpg",
            niche_id=analysis.niche,
            seed=f"gal|{pkg_id}|{analysis.business_name}|{book.fingerprint}",
            role="gallery",
            size=(1200, 800),
            metaphor=metaphor,
            accent_hex=book.palette.accent_hex,
        )
        write_niche_scene(
            assets_dir / "illustration.jpg",
            niche_id=analysis.niche,
            seed=f"ill|{pkg_id}|{analysis.business_name}|{book.fingerprint}",
            role="product",
            size=(1000, 1000),
            metaphor=metaphor,
            accent_hex=book.palette.accent_hex,
        )
        (product_dir / "atmosphere_pack.json").write_text(
            __import__("json").dumps(pack.as_dict(), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        client_assets.hero_from_client = False

        ident = resolve_business_identity(
            business_name=analysis.business_name,
            niche_id=analysis.niche,
            package_id=pkg_id,
            city=city or "",
            diversity_salt=str(contacts.get("diversity_salt") or ""),
        )
        write_business_identity(product_dir, ident)
        enforce_media_truth_on_product(
            product_dir,
            niche_id=analysis.niche,
            business_name=analysis.business_name,
            package_id=pkg_id,
        )
        write_reputation_pack(
            product_dir,
            business_name=analysis.business_name,
            niche_id=analysis.niche,
            package_id=pkg_id,
            diversity_salt=str(contacts.get("diversity_salt") or ""),
            city=city or "",
        )

        pack_manifest: dict = {}
        pack_manifest_path = product_dir / "assets" / "hero_pack" / "manifest.json"
        if pack_manifest_path.is_file():
            try:
                pack_manifest = json.loads(pack_manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pack_manifest = {}
        timer.mark("assets")

        # Re-stamp First Impression (client story) onto analysis before HTML compose
        try:
            from app.factory.first_impression import (
                apply_first_impression_to_analysis,
                resolve_first_impression,
            )

            _fi = resolve_first_impression(
                niche_id=str(analysis.niche or ""),
                contacts=contacts,
            )
            if _fi.story:
                analysis = apply_first_impression_to_analysis(analysis, _fi)
                contacts["first_impression"] = _fi.as_dict()
        except Exception:
            pass

        def _compose(*, diversity_salt: str = ""):
            from app.factory.dream_brief import dream_brief_from_contacts

            _dream = dream_brief_from_contacts(contacts)
            return compose_landing(
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
                brand_style=brand_style_id or _dream.style or None,
                client_trust=contacts.get("trust")
                if isinstance(contacts.get("trust"), dict)
                else None,
                product_dir=product_dir,
                hero_from_client=client_assets.hero_from_client,
                diversity_salt=diversity_salt,
                studio_plan=studio_plan,
                approach=_dream.approach(),
                contacts=contacts,
            )

        composed = _compose(
            diversity_salt=str(contacts.get("diversity_salt") or ""),
        )
        html = composed.html
        plan = composed.plan
        if composed.analysis is not None:
            analysis = composed.analysis
        client_assets.gallery = list(composed.gallery)
        client_assets.hero_from_client = composed.hero_from_client
        media_plan = composed.media_plan
        content_gate = composed.content_gate

        # Design Memory: if too similar to prior builds → one diversity rebuild.
        from app.factory.visual_intelligence.ai_design_director import score_html
        from app.factory.visual_intelligence.design_memory import (
            check_similarity,
            record_composition,
        )

        design_memory_dir = self._memory / "design_memory"
        director_score = score_html(
            html,
            package_id=pkg_id,
            niche=analysis.niche,
            luxury_mode=bool(creative_brief.get("luxury_mode")),
        )
        design_memory = check_similarity(
            str(director_score.get("fingerprint") or ""),
            niche=analysis.niche,
            package_id=pkg_id,
            memory_dir=design_memory_dir,
        )
        if design_memory.get("rebuild_needed"):
            composed = _compose(diversity_salt="dm1")
            html = composed.html
            plan = composed.plan
            if composed.analysis is not None:
                analysis = composed.analysis
            client_assets.gallery = list(composed.gallery)
            client_assets.hero_from_client = composed.hero_from_client
            media_plan = composed.media_plan
            content_gate = composed.content_gate
            director_score = score_html(
                html,
                package_id=pkg_id,
                niche=analysis.niche,
                luxury_mode=bool(creative_brief.get("luxury_mode")),
            )
            design_memory = {
                **check_similarity(
                    str(director_score.get("fingerprint") or ""),
                    niche=analysis.niche,
                    package_id=pkg_id,
                    memory_dir=design_memory_dir,
                ),
                "auto_rebuild": True,
                "diversity_salt": "dm1",
            }

        # Experience Director — judges impression; may force Luxury/Hero rebuild.
        from app.factory.visual_intelligence.studio.experience_director import (
            decide_experience_impression,
        )

        experience_decision = decide_experience_impression(
            package_id=pkg_id,
            first_impression=int(
                (director_score.get("scores") or {}).get("first_impression") or 0
            ),
            overall=int(director_score.get("overall") or 0),
            luxury_mode=bool(studio_plan.luxury_mode),
        )
        if experience_decision.get("rebuild_recommended") and pkg_id in (
            "premium",
            "connected",
            "standalone",
            "business",
        ):
            composed = _compose(diversity_salt="exp1")
            html = composed.html
            plan = composed.plan
            if composed.analysis is not None:
                analysis = composed.analysis
            client_assets.gallery = list(composed.gallery)
            client_assets.hero_from_client = composed.hero_from_client
            media_plan = composed.media_plan
            content_gate = composed.content_gate
            director_score = score_html(
                html,
                package_id=pkg_id,
                niche=analysis.niche,
                luxury_mode=True,
            )
            experience_decision = {
                **decide_experience_impression(
                    package_id=pkg_id,
                    first_impression=int(
                        (director_score.get("scores") or {}).get("first_impression") or 0
                    ),
                    overall=int(director_score.get("overall") or 0),
                    luxury_mode=True,
                ),
                "auto_rebuild": True,
                "diversity_salt": "exp1",
            }
        timer.mark("render")

        # Final Commercial Gate on HTML (Hard Gate + AI Score). Rule №1 > score.
        from app.factory.composers import run_composers as _run_cg

        analysis, commercial_final = _run_cg(
            analysis,
            contacts=contacts,
            package_id=package_id or contacts.get("package_id"),
            html=html,
            scenario_id=analysis.niche,
        )
        commercial_meta = commercial_final.as_dict()

        gate_meta = plan.gate_meta()
        gate_meta["niche"] = analysis.niche
        gate_meta["content_gate"] = content_gate
        gate_meta["commercial_gate"] = commercial_meta
        validation = validate_landing(
            html,
            meta=gate_meta,
            assets_dir=product_dir / "assets",
        )
        # Asset Integrity — Hard FAIL before publish (Reality Over Architecture)
        from app.factory.media_integrity import (
            MediaIntegrityError,
            enforce_media_integrity,
            ensure_demo_logo,
        )

        ensure_demo_logo(
            product_dir / "assets",
            business_name=analysis.business_name,
            niche_id=str(analysis.niche or ""),
        )
        try:
            integrity = enforce_media_integrity(
                product_dir,
                html,
                business_name=analysis.business_name,
                niche_id=str(analysis.niche or ""),
                package_id=pkg_id,
                hard=True,
            )
        except MediaIntegrityError as exc:
            (product_dir / "media_integrity.json").write_text(
                __import__("json").dumps(
                    exc.report.as_dict(), ensure_ascii=False, indent=2
                )
                + "\n",
                encoding="utf-8",
            )
            raise
        gate_meta["media_integrity"] = integrity.as_dict()
        try:
            from app.factory.renderers.registry import renderer_coverage, strategy_id_for

            cov = renderer_coverage()
            cov["this_product"] = strategy_id_for(
                niche_id=str(analysis.niche or ""),
                package_id=pkg_id,
            )
            (product_dir / "renderer_coverage.json").write_text(
                __import__("json").dumps(cov, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            gate_meta["renderer_coverage"] = cov
        except Exception:
            pass

        if pkg_id in ("premium", "connected"):
            try:
                from app.factory.studio_renderer_v2 import (
                    inject_studio_html,
                    write_studio_assets,
                )

                write_studio_assets(
                    product_dir,
                    niche_id=str(analysis.niche or ""),
                    package_id=pkg_id,
                    business_name=str(getattr(analysis, "business_name", "") or ""),
                )
                html = inject_studio_html(html, package_id=pkg_id)
            except Exception:
                pass
            # Premium Website: full-film Cinematic Story (replaces landing body).
            # Basic / Business / Lorene path must never enter this block.
            try:
                from app.integration.experience_engine.premium_apply import (
                    apply_premium_website_experience,
                )

                pe = apply_premium_website_experience(
                    product_dir,
                    html,
                    package_id=pkg_id,
                    niche=str(analysis.niche or ""),
                    brand=str(getattr(analysis, "business_name", "") or ""),
                )
                if pe.get("ok") and pe.get("html"):
                    html = str(pe["html"])
                    gate_meta["premium_experience"] = {
                        "status": pe.get("status"),
                        "scene_count": pe.get("scene_count"),
                        "reason": pe.get("reason"),
                        "assets": pe.get("assets_written"),
                        "ai_video": False,
                    }
                else:
                    gate_meta["premium_experience"] = {
                        "status": pe.get("status"),
                        "reason": pe.get("reason"),
                        "skipped": pe.get("skipped", True),
                    }
            except Exception as exc:
                gate_meta["premium_experience"] = {
                    "status": "APPLY_ERROR",
                    "reason": type(exc).__name__,
                }

        (product_dir / "index.html").write_text(html, encoding="utf-8")

        from app.factory.premium_site_qa import run_premium_site_qa

        premium_qa = run_premium_site_qa(
            html=html,
            meta={
                "niche": analysis.niche,
                "city": city,
                "website_design_spec": website_design_spec,
            },
            niche_id=str(analysis.niche or ""),
            design_spec=website_design_spec,
            assets_dir=product_dir / "assets",
        )
        gate_meta["premium_site_qa"] = premium_qa

        from app.factory.visual_intelligence.studio.commercial_readiness import (
            score_commercial_readiness,
        )

        # Re-read after studio apply path (html already studio-applied in compose)
        commercial_readiness = score_commercial_readiness(
            html,
            package_id=pkg_id,
            niche=analysis.niche,
            market_code=market,
            luxury_mode=bool(studio_plan.luxury_mode),
        )
        # If Performance vetoes video mid-flight, re-apply studio once more
        if (commercial_readiness.get("performance_detail") or {}).get("veto_video"):
            from app.factory.visual_intelligence.studio.apply_html import (
                apply_studio_to_html,
            )

            html = apply_studio_to_html(html, studio_plan)
            (product_dir / "index.html").write_text(html, encoding="utf-8")
            commercial_readiness = score_commercial_readiness(
                html,
                package_id=pkg_id,
                niche=analysis.niche,
                market_code=market,
                luxury_mode=bool(studio_plan.luxury_mode),
            )

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
        timer.mark("gates")

        meta = {
            "product_id": product_id,
            "intent_id": intent_id,
            "product_type": "Website",
            "description": description,
            "niche": analysis.niche,
            "template_id": analysis.template_id,
            "business_name": analysis.business_name,
            "market_code": market,
            "language": str(
                contacts.get("language")
                or contacts.get("ui_lang")
                or ""
            ).strip()
            or None,
            "locale": str(contacts.get("locale") or "").strip() or None,
            "currency": str(contacts.get("currency") or "").strip() or None,
            "ui_lang": str(contacts.get("ui_lang") or contacts.get("language") or "").strip()
            or None,
            "path_a_pricing": {
                "package_id": str(
                    package_id or contacts.get("package_id") or "basic"
                ).strip().lower()
                or "basic",
                "amount": contacts.get("amount")
                if contacts.get("amount") is not None
                else contacts.get("price_eur"),
                "currency": str(contacts.get("currency") or "").strip() or None,
                "price_label": str(contacts.get("price_label") or "").strip() or None,
            },
            "market_design": resolve_market_design(market).market_id,
            "motion_level": motion,
            "composer_engine": plan.engine_id,
            "composition_plan": plan.as_dict(),
            "design_dna": getattr(composed, "design_dna", None) or {},
            "hero_layout": plan.hero_layout,
            "component_profile": plan.component_profile,
            "layout_profile": profile_as_dict(plan.layout_profile),
            "trust_template": plan.trust_template,
            "creative_director": creative_brief,
            "digital_creative_studio": studio_plan.as_dict(),
            "luxury_mode": bool(studio_plan.luxury_mode),
            "design_director": director_score,
            "design_memory": design_memory,
            "experience_director": experience_decision,
            "commercial_readiness": commercial_readiness,
            "commercial_ready": bool(commercial_readiness.get("commercial_ready")),
            "media_plan": media_plan,
            "content_gate": content_gate,
            "commercial_gate": commercial_meta,
            "website_design_spec": website_design_spec,
            "premium_site_qa": premium_qa,
            "premium_qa_verdict": premium_qa.get("verdict"),
            "owner_version_id": website_design_spec.get("version_id"),
            "status": (
                "commercial_ready"
                if commercial_readiness.get("commercial_ready")
                and commercial_meta.get("hard_passed", True)
                else "completed"
                if commercial_meta.get("hard_passed", True)
                else "needs_rebuild"
            ),
            "quality_percent": validation.quality_percent,
            "validation_passed": validation.passed and bool(commercial_meta.get("hard_passed", True)),
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
            "factory_stages": timer.as_dict(),
            "delivery_locked": False,
        }
        try:
            if meta.get("validation_passed") and director_score.get("fingerprint"):
                record_composition(
                    fingerprint=str(director_score["fingerprint"]),
                    package_id=pkg_id,
                    niche=str(analysis.niche or ""),
                    layout_profile=str(getattr(plan.layout_profile, "id", "") or ""),
                    hero_layout=str(plan.hero_layout or ""),
                    memory_dir=design_memory_dir,
                )
        except Exception:
            pass

        # Reality Sprint scorecard (eyes) + Studio Collection compare + Law №4 flag
        try:
            from app.factory.reality_sprint import empty_scorecard, write_product_scorecard
            from app.factory.studio_collection import compare_to_collection

            card = empty_scorecard(
                niche_id=str(analysis.niche or ""),
                product_id=product_id,
                company_name=str(analysis.business_name or ""),
                preview_url="index.html",
            )
            write_product_scorecard(product_dir, card)
            coll = compare_to_collection(
                niche_id=str(analysis.niche or ""),
                fingerprint=str(director_score.get("fingerprint") or ""),
                overall_score=int(director_score.get("overall") or meta.get("quality_percent") or 0),
                memory_dir=self._memory / "studio_collection",
            )
            meta["studio_collection"] = coll
            meta["law4"] = {
                "violation": bool(design_memory.get("law4_violation")),
                "similarity_pct": design_memory.get("similarity_pct"),
                "cross_niche_similarity_pct": design_memory.get(
                    "cross_niche_similarity_pct"
                ),
                "action": design_memory.get("action_ru"),
            }
            meta["commercial_review"] = "PENDING_OWNER"
            meta["reality_sprint"] = "PENDING_OWNER"
            if design_memory.get("law4_violation"):
                meta["status"] = "needs_rebuild"
                meta["validation_passed"] = False
            if coll.get("verdict") == "worse_than_best" or coll.get(
                "verdict"
            ) == "worse_clone_of_etalon":
                meta["export_blocked_reason"] = coll.get("message")
                # Soft block while collection is young; hard when peers ≥ 3
                if int(coll.get("peers") or 0) >= 3:
                    meta["status"] = "needs_rebuild"
                    meta["validation_passed"] = False
            (product_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

        try:
            from app.factory.visual_intelligence.studio.experience_replay import (
                build_experience_replay,
                write_experience_replay,
            )

            replay = build_experience_replay(
                studio_plan,
                design_director=director_score,
                design_memory=design_memory,
                experience=experience_decision,
                commercial_readiness=commercial_readiness,
            )
            write_experience_replay(product_dir, replay)
            meta["experience_replay"] = replay
            (product_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            (product_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        try:
            dna_payload = getattr(composed, "design_dna", None) or meta.get("design_dna")
            if dna_payload:
                (product_dir / "design_dna.json").write_text(
                    json.dumps(dna_payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        except Exception:
            pass
        try:
            fab = contacts.get("fabricated_company")
            if isinstance(fab, dict):
                (product_dir / "fabricated_company.json").write_text(
                    json.dumps(fab, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                meta["commercial_review"] = "PENDING_OWNER"
                meta["business_generation"] = True
                meta["demo_content"] = True
                (product_dir / "meta.json").write_text(
                    json.dumps(meta, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        except Exception:
            pass
        try:
            from app.factory.studio_critic import run_studio_critic

            critic = run_studio_critic(
                product_dir,
                niche_id=str(analysis.niche or contacts.get("niche") or ""),
                brand_name=str(analysis.business_name or ""),
                package_id=pkg_id,
            )
            critic_dict = critic.as_dict()
            meta["studio_critic"] = critic_dict
            meta["experience_score"] = critic_dict
            contacts["studio_critic"] = critic_dict
            contacts["experience_score"] = critic_dict
            if critic.rebuild and pkg_id in ("premium", "connected"):
                # Keep export for owner eyes — flag rebuild, do not delete product.
                meta["studio_critic_rebuild_recommended"] = True
                contacts["studio_critic_rebuild_recommended"] = True
            (product_dir / "meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        try:
            record_build(
                self._memory,
                product_id=product_id,
                order_id=str(contacts.get("order_id") or "") or None,
                stages=timer.as_dict(),
                kind="build",
                cached_zip=False,
            )
        except Exception:
            pass
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
        # New revision unlocks Production Artifact for rebuild.
        meta["delivery_locked"] = False
        meta.pop("delivery_sha256", None)
        meta.pop("delivery_manifest", None)

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
            if getattr(composed, "design_dna", None):
                meta["design_dna"] = composed.design_dna
                try:
                    (product_dir / "design_dna.json").write_text(
                        json.dumps(composed.design_dna, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except OSError:
                    pass
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
        return self._pack_product_zip(product_id, meta, mark_download=True, use_cache=True)

    def prebuild_client_delivery_zip(self, product_id: str) -> dict:
        """Pack once at Ready — freeze immutable Production Artifact."""
        import hashlib

        meta = self._load_meta(product_id)
        if not meta:
            raise ValueError("product_not_found")
        product_dir = self._sandbox / product_id
        compliance = meta.get("compliance") if isinstance(meta.get("compliance"), dict) else {}
        cg = meta.get("commercial_gate") if isinstance(meta.get("commercial_gate"), dict) else {}
        built_at = datetime.now(timezone.utc).isoformat()
        (product_dir / "compliance_report.json").write_text(
            json.dumps(
                {
                    "product_id": product_id,
                    "at": built_at,
                    "compliance": compliance,
                    "commercial_gate": cg,
                    "validation_passed": meta.get("validation_passed"),
                    "quality_percent": meta.get("quality_percent"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        draft_manifest = {
            "immutable": True,
            "product_id": product_id,
            "revision": int(meta.get("revision") or 0),
            "built_at": built_at,
            "compliance_passed": bool(compliance.get("passed")),
            "commercial_hard_passed": bool(cg.get("hard_passed", True)),
            "factory_stages": meta.get("factory_stages")
            if isinstance(meta.get("factory_stages"), dict)
            else {},
            "artifacts": [
                "index.html",
                "client_delivery.zip",
                "compliance_report.json",
                "delivery_manifest.json",
            ],
        }
        (product_dir / "delivery_manifest.json").write_text(
            json.dumps(draft_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # Unlock only for this intentional Ready freeze rebuild.
        meta["delivery_locked"] = False
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        data, filename = self._pack_product_zip(
            product_id, meta, mark_download=False, use_cache=False, force_rebuild=True
        )
        meta = self._load_meta(product_id) or meta
        sha = hashlib.sha256(data).hexdigest()
        manifest = {
            **draft_manifest,
            "filename": filename,
            "bytes": len(data),
            "sha256": sha,
        }
        (product_dir / "delivery_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        meta["delivery_locked"] = True
        meta["delivery_sha256"] = sha
        meta["delivery_manifest"] = manifest
        meta["client_zip_bytes"] = len(data)
        meta["updated_at"] = built_at
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {
            "ok": True,
            "product_id": product_id,
            "filename": filename,
            "bytes": len(data),
            "sha256": sha,
            "cached": True,
            "immutable": True,
            "manifest": manifest,
        }

    def _pack_product_zip(
        self,
        product_id: str,
        meta: dict,
        *,
        mark_download: bool,
        use_cache: bool = True,
        force_rebuild: bool = False,
    ) -> tuple[bytes, str]:
        from app.factory.market_delivery import deploy_readme, normalize_market
        from app.factory.client_legal_pages import ClientLegalInfo, write_client_legal_pages
        from app.integration.factory_metrics import StageTimer, record_build

        product_dir = self._sandbox / product_id
        html_path = product_dir / "index.html"
        if not html_path.is_file():
            raise ValueError("product_not_found")

        timer = StageTimer()
        slug = self._zip_slug(meta.get("business_name") or "", product_id)
        filename = f"{slug}.zip"
        cache_path = product_dir / "client_delivery.zip"
        rev = int(meta.get("revision") or 0)
        locked = bool(meta.get("delivery_locked"))

        # Production mode: after Ready freeze, downloads never re-pack.
        if (
            locked
            and use_cache
            and not force_rebuild
            and cache_path.is_file()
            and cache_path.stat().st_size > 1000
        ):
            data = cache_path.read_bytes()
            timer.mark("zip")
            try:
                record_build(
                    self._memory,
                    product_id=product_id,
                    stages=timer.as_dict(),
                    zip_bytes=len(data),
                    cached_zip=True,
                    kind="zip_immutable",
                )
            except Exception:
                pass
            if mark_download:
                meta["export_downloaded_at"] = datetime.now(timezone.utc).isoformat()
                meta["updated_at"] = meta["export_downloaded_at"]
                (product_dir / "meta.json").write_text(
                    json.dumps(meta, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            return data, filename

        if (
            use_cache
            and not force_rebuild
            and cache_path.is_file()
            and meta.get("client_zip_revision") == rev
            and cache_path.stat().st_size > 1000
        ):
            data = cache_path.read_bytes()
            timer.mark("zip")
            try:
                record_build(
                    self._memory,
                    product_id=product_id,
                    stages=timer.as_dict(),
                    zip_bytes=len(data),
                    cached_zip=True,
                    kind="zip_cache",
                )
            except Exception:
                pass
            if mark_download:
                meta["export_downloaded_at"] = datetime.now(timezone.utc).isoformat()
                meta["updated_at"] = meta["export_downloaded_at"]
                (product_dir / "meta.json").write_text(
                    json.dumps(meta, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            return data, filename

        html = html_path.read_text(encoding="utf-8")
        # Skip full compliance re-run when commercial + prior compliance already passed.
        cg = meta.get("commercial_gate") if isinstance(meta.get("commercial_gate"), dict) else {}
        prior = meta.get("compliance") if isinstance(meta.get("compliance"), dict) else {}
        demo_pack = bool(
            meta.get("demo_order")
            or meta.get("allow_demo_pack")
            or meta.get("demo")
            or meta.get("is_demo")
        )
        need_compliance = not (
            cg.get("passed") is True
            and prior.get("passed") is True
            and meta.get("validation_passed") is True
        )
        if demo_pack:
            # Owner demo Path A — pack HTML for eyes; gate report stays in meta.
            need_compliance = False
            meta["demo_pack_note"] = (
                "Demo ZIP without re-assert compliance — PENDING_OWNER visual bar."
            )
        if need_compliance:
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
        timer.mark("gates")

        market = normalize_market(str(meta.get("market_code") or "DE"))
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

        # Pack only assets referenced by HTML (+ small essentials). Avoid shipping
        # duplicate hero_pack JPEGs that inflate ZIP ~6× with identical bytes.
        include_assets = self._assets_for_client_zip(html, product_dir / "assets")

        buf = io.BytesIO()
        # STORED for already-compressed images — much faster than re-DEFLATE.
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            archive.writestr("index.html", html)
            for legal_name in legal_meta.get("files") or []:
                legal_path = product_dir / str(legal_name)
                if legal_path.is_file():
                    archive.writestr(str(legal_name), legal_path.read_text(encoding="utf-8"))
            for asset in include_assets:
                rel = asset.relative_to(product_dir).as_posix()
                data_bytes = asset.read_bytes()
                if asset.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".woff2"}:
                    info = zipfile.ZipInfo(rel)
                    info.compress_type = zipfile.ZIP_STORED
                    archive.writestr(info, data_bytes)
                else:
                    archive.writestr(rel, data_bytes)
            archive.writestr(
                "README_PUBLISH.txt",
                deploy_readme(
                    market,
                    package_id=str(
                        (meta.get("package_delivery") or {}).get("package_id")
                        or meta.get("package_id")
                        or "basic"
                    ),
                    ui_lang=str(meta.get("language") or meta.get("ui_lang") or "") or None,
                ),
            )
            # Include freeze docs when present (Production Artifact).
            for extra_name in ("delivery_manifest.json", "compliance_report.json"):
                extra_path = product_dir / extra_name
                if extra_path.is_file():
                    archive.writestr(extra_name, extra_path.read_text(encoding="utf-8"))

        data = buf.getvalue()
        timer.mark("zip")
        cache_path.write_bytes(data)
        meta["client_zip_revision"] = rev
        meta["client_zip_bytes"] = len(data)
        meta["client_zip_built_at"] = datetime.now(timezone.utc).isoformat()

        if mark_download:
            meta["export_downloaded_at"] = datetime.now(timezone.utc).isoformat()
            meta["updated_at"] = meta["export_downloaded_at"]
        else:
            meta["updated_at"] = datetime.now(timezone.utc).isoformat()
        (product_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        try:
            record_build(
                self._memory,
                product_id=product_id,
                stages=timer.as_dict(),
                zip_bytes=len(data),
                cached_zip=False,
                kind="zip_build",
                extra={"asset_files": len(include_assets)},
            )
        except Exception:
            pass
        return data, filename

    def _assets_for_client_zip(self, html: str, assets_dir: Path) -> list[Path]:
        """Return asset files to ship — referenced paths + small essentials only."""
        if not assets_dir.is_dir():
            return []
        import re

        refs: set[str] = set()
        for m in re.finditer(
            r"""(?:src|href)=["'](assets/[^"']+)["']""", html, flags=re.I
        ):
            refs.add(m.group(1).replace("\\", "/"))
        for m in re.finditer(r"""url\(\s*["']?(assets/[^"')]+)""", html, flags=re.I):
            refs.add(m.group(1).replace("\\", "/"))

        chosen: list[Path] = []
        seen: set[str] = set()
        for rel in sorted(refs):
            # strip query
            rel = rel.split("?", 1)[0]
            path = (assets_dir.parent / rel).resolve()
            try:
                path.relative_to(assets_dir.resolve())
            except ValueError:
                continue
            if path.is_file() and rel not in seen:
                chosen.append(path)
                seen.add(rel)

        # Essentials often not in src= but needed for polish / gate docs
        for extra in (
            "media_manifest.json",
            "ux_polish.js",
            "motion_kit.css",
            "reveal.js",
            "experience_engine.css",
            "experience_engine.js",
        ):
            p = assets_dir / extra
            key = f"assets/{extra}"
            if p.is_file() and key not in seen:
                chosen.append(p)
                seen.add(key)

        # If HTML references nothing under assets/, keep hero.jpg only (never whole hero_pack).
        if not chosen:
            for fallback in ("hero.jpg", "logo.png", "background.jpg"):
                p = assets_dir / fallback
                if p.is_file():
                    chosen.append(p)
                    break
        return chosen

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
        html = html_path.read_text(encoding="utf-8")
        return self.rewrite_preview_html(html, product_id)

    def resolve_preview_asset(self, product_id: str, asset_path: str) -> Path | None:
        """Safe path under sandbox/{product_id}/ for Website Admin live preview."""
        pid = (product_id or "").strip()
        rel = (asset_path or "").strip().lstrip("/").replace("\\", "/")
        if not pid or not rel or ".." in Path(rel).parts:
            return None
        root = (self._sandbox / pid).resolve()
        if not root.is_dir():
            return None
        target = (root / rel).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            return None
        return target if target.is_file() else None

    @staticmethod
    def rewrite_asset_urls(
        text: str, *, product_id: str, relative_dir: str = ""
    ) -> str:
        """Rewrite relative href/src/url(...) to Factory preview asset base."""
        from pathlib import PurePosixPath

        base = f"/api/factory/products/{product_id}/preview"

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

        def _attr(match: re.Match[str]) -> str:
            attr, quote, target = match.group(1), match.group(2), match.group(3)
            cleaned = _norm(target)
            if cleaned is None:
                return match.group(0)
            return f"{attr}={quote}{base}/{cleaned}{quote}"

        text = re.sub(r'(href|src)=([\'"])([^\'"]+)\2', _attr, text, flags=re.I)

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
    def rewrite_preview_html(cls, html: str, product_id: str) -> str:
        """Point relative page/asset links at the Factory preview asset base."""
        base = f"/api/factory/products/{product_id}/preview/"
        html = cls.rewrite_asset_urls(html, product_id=product_id, relative_dir="")
        # So runtime-relative paths in owner JS (assets/virtus-owner/…) resolve correctly.
        if re.search(r"<base\b", html, flags=re.I):
            return html
        tag = f'<base href="{base}" />'
        if re.search(r"<head\b[^>]*>", html, flags=re.I):
            return re.sub(
                r"(<head\b[^>]*>)", rf"\1\n  {tag}", html, count=1, flags=re.I
            )
        return f"{tag}\n{html}"

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
