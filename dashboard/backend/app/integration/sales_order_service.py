"""Sprint 1 — Genesis Sales: client orders and pricing (no payment gateway yet)."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.integration.commerce_engine import (
    resolve_checkout_market,
    resolve_checkout_packages,
    resolve_final_offer,
)
from app.integration.product_line import (
    BRAND_NAME,
    SERVICE_WEBSITE,
    project_awaiting_payment_message,
    project_client_current_step,
    project_client_next_step,
    project_client_timeline,
    project_launch_deliverables,
    project_order_created_message,
    service_label_ru,
)
from app.integration.client_review_service import new_review_token
from app.schemas import FactoryIntentRequest

logger = logging.getLogger(__name__)

# Post-ZIP handoff (Assisted Deployment) — never store host passwords.
DEPLOYMENT_PREFERENCES = frozenset({"unset", "zip_only", "assisted"})
HOSTING_PROVIDERS = frozenset(
    {"ionos", "hetzner", "cloudflare_pages", "vercel", "other"}
)

_PACKAGES = {
    "basic": {
        "id": "basic",
        "name": "Landing Basic",
        "price_eur": 350,
        "deliverables": [
            "Fertige Landing Page (One-Page, mobil)",
            "Vollständiges Website-Archiv (ZIP) — Sie sind Eigentümer der Dateien",
            "Anleitung zur Selbst-Veröffentlichung",
            "Impressum- und Datenschutz-Vorlagen (von Ihnen zu prüfen)",
            "WhatsApp-Button, Kontaktformular, Basis-SEO",
            "Lieferzeit: ca. 5–14 Werktage (je nach Paket und Rückmeldungen).",
        ],
    },
    "business": {
        "id": "business",
        "name": "Landing Business",
        "price_eur": 650,
        "deliverables": [
            "Alles aus Basic (inkl. ZIP und Eigentum an den Dateien)",
            "Google Maps, Bewertungsblock, Logo-Platzhalter, erweitertes SEO",
            "Hilfe beim Upload auf Ihren Hosting-Zugang (manuell)",
            "1 Korrekturrunde",
            "Hilfe bei der Wahl des Hostings; Vertrag Domain/Hosting direkt mit dem Anbieter",
            "Lieferzeit: ca. 5–14 Werktage (je nach Paket und Rückmeldungen).",
        ],
    },
    "premium": {
        "id": "premium",
        "name": "Landing Premium",
        "price_eur": 1200,
        "deliverables": [
            "Alles aus Business",
            "Premium-Design, Kostenrechner, Analytics-Platzhalter",
            "Vollständige Veröffentlichung: Domain-Anbindung, Hosting-Setup, SSL, Go-live (wenn Sie Zugang geben)",
            "14 Tage Support + 3 Korrekturrunden",
            "Domain/Hosting-Vertrag schließen Sie direkt mit dem Anbieter (kein Reseller-Modell)",
            "Lieferzeit: ca. 5–14 Werktage (je nach Paket und Rückmeldungen).",
        ],
    },
}


class SalesOrderService:
    def __init__(self, memory_dir: Path, factory_intent: object) -> None:
        self._memory = memory_dir
        self._factory_intent = factory_intent
        self._memory.mkdir(parents=True, exist_ok=True)

    def checkout_packages(
        self,
        *,
        market_code: str | None = None,
        visitor_id: str | None = None,
        city: str | None = None,
        extra_text: str | None = None,
    ) -> dict:
        resolved = resolve_checkout_market(
            market_code=market_code,
            city=city,
            visitor_id=visitor_id,
            memory_dir=self._memory,
            extra_text=extra_text,
        )
        deliverables = {k: v["deliverables"] for k, v in _PACKAGES.items()}
        names = {k: v["name"] for k, v in _PACKAGES.items()}
        return resolve_checkout_packages(
            resolved,
            deliverables_by_id=deliverables,
            names_by_id=names,
        )

    def packages(
        self,
        *,
        market_code: str | None = None,
        visitor_id: str | None = None,
        city: str | None = None,
        extra_text: str | None = None,
    ) -> list[dict]:
        return self.checkout_packages(
            market_code=market_code,
            visitor_id=visitor_id,
            city=city,
            extra_text=extra_text,
        )["packages"]

    def _package_offer(
        self,
        package_id: str,
        *,
        market_code: str | None = None,
        visitor_id: str | None = None,
        city: str | None = None,
        extra_text: str | None = None,
    ) -> tuple[dict, dict]:
        resolved = resolve_checkout_market(
            market_code=market_code,
            city=city,
            visitor_id=visitor_id,
            memory_dir=self._memory,
            extra_text=extra_text,
        )
        tier = package_id if package_id in _PACKAGES else "basic"
        base = _PACKAGES.get(tier, _PACKAGES["basic"])
        offer = resolve_final_offer(tier, resolved)
        package = {
            **base,
            "price_eur": float(offer.amount),
            "currency": offer.currency,
            "symbol": offer.symbol,
            "market_code": offer.market_code,
            "price_label": offer.price_label,
        }
        return package, offer.as_dict()

    def create_order(self, payload: dict) -> dict:
        from app.factory.market_delivery import client_status_label
        from app.factory.motion_brief import gate_motion_level, normalize_motion_level

        package_id = payload.get("package_id") or self._suggest_package(payload)
        package, _offer = self._package_offer(
            package_id,
            market_code=payload.get("market_code"),
            visitor_id=payload.get("visitor_id"),
            city=payload.get("city"),
            extra_text=payload.get("description"),
        )
        motion = normalize_motion_level(str(payload.get("motion_level") or "none"))
        gate = gate_motion_level(motion)
        if not gate["ok"]:
            raise ValueError("WAITLIST_REQUIRED")
        project_ctx = self._resolve_project_context(payload.get("visitor_id"))
        service_id = project_ctx["service_id"]
        launch_mode = bool(project_ctx["launch_mode"])
        project_name = project_ctx.get("project_name")
        order_id = f"ord-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        client_message = project_awaiting_payment_message(launch_mode=launch_mode)
        company_website = self._normalize_company_website(payload.get("company_website"))
        site_analysis = self._analyze_company_website(company_website) if company_website else None

        existing_domain = (payload.get("existing_domain") or "").strip() or None
        domain_status = (payload.get("domain_status") or "").strip().lower()
        if domain_status not in ("none", "have_domain", "need_help"):
            if existing_domain or company_website:
                domain_status = "have_domain"
            elif payload.get("needs_domain"):
                domain_status = "need_help"
            else:
                domain_status = "none"
        domain_help_message = None
        if domain_status in ("none", "need_help"):
            domain_help_message = (
                "Wir können bei der Auswahl und Anbindung einer Domain helfen — "
                "ohne sofortigen Kaufzwang."
            )
        effective_needs_domain = domain_status in ("none", "need_help") and not existing_domain

        social_links = {
            "google_business": (payload.get("google_business") or "").strip() or None,
            "instagram": (payload.get("instagram") or "").strip() or None,
            "facebook": (payload.get("facebook") or "").strip() or None,
            "tiktok": (payload.get("tiktok") or "").strip() or None,
            "linkedin": (payload.get("linkedin") or "").strip() or None,
            "youtube": (payload.get("youtube") or "").strip() or None,
            "telegram": (payload.get("telegram") or "").strip() or None,
            "whatsapp": (payload.get("whatsapp") or "").strip() or None,
            "website": company_website,
            "domain": existing_domain,
        }
        social_links = {k: v for k, v in social_links.items() if v}

        material_ids = [
            str(x).strip()
            for x in (payload.get("material_ids") or [])
            if str(x).strip()
        ][:40]
        materials_bundle: dict = {"files": [], "count": 0}
        buyer_insights: dict | None = None
        try:
            from app.integration.order_materials_service import OrderMaterialsService

            mats = OrderMaterialsService(self._memory)
            if material_ids:
                materials_bundle = mats.attach_to_order(order_id, material_ids)
            buyer_insights = mats.build_buyer_insights(
                company_website=company_website,
                domain=existing_domain,
                domain_status=domain_status,
                social=social_links,
                material_ids=material_ids,
                site_analysis=site_analysis,
            )
        except Exception as exc:
            logger.warning("order materials/insights skipped: %s", exc)

        order = {
            "order_id": order_id,
            "status": "awaiting_payment",
            "status_label": client_status_label(
                "awaiting_payment", package.get("market_code", "DE")
            ),
            "package_id": package_id,
            "package_name": package["name"],
            "price_eur": package["price_eur"],
            "currency": package.get("currency", "EUR"),
            "symbol": package.get("symbol", "€"),
            "market_code": package.get("market_code", "DE"),
            "price_label": package.get("price_label", f"{package['price_eur']} €"),
            "motion_level": motion,
            "deliverables": (
                project_launch_deliverables(service_id)
                if launch_mode
                else package["deliverables"]
            ),
            "business_name": payload["business_name"].strip(),
            "description": payload["description"].strip(),
            "city": (payload.get("city") or "").strip(),
            "phone": (payload.get("phone") or "").strip(),
            "whatsapp": (payload.get("whatsapp") or "").strip(),
            "email": (payload.get("email") or "").strip(),
            "needs_logo": bool(payload.get("needs_logo")),
            "needs_domain": bool(effective_needs_domain),
            "domain_status": domain_status,
            "existing_domain": existing_domain,
            "domain_help_message": domain_help_message,
            "extra_wishes": (payload.get("extra_wishes") or "").strip(),
            "company_website": company_website,
            "niche": (payload.get("niche") or "").strip() or None,
            "specialization": (payload.get("specialization") or "").strip() or None,
            "social_links": social_links,
            "materials": materials_bundle,
            "buyer_insights": buyer_insights,
            "site_analysis": site_analysis,
            "project_workspace": {
                "materials": materials_bundle.get("files") or [],
                "analysis": buyer_insights,
                "documents": [],
                "invoices": [],
                "status": "awaiting_payment",
            },
            "client_legal": self._client_legal_payload(payload),
            "visitor_id": (payload.get("visitor_id") or "").strip()[:64] or None,
            "service_id": service_id,
            "launch_mode": launch_mode,
            "project_name": project_name,
            "created_at": now,
            "updated_at": now,
            "product_id": (payload.get("product_id") or "").strip() or None,
            "proposal_text": self._proposal_text(package, payload, project_ctx=project_ctx),
            "paid_at": None,
            "payment_provider": None,
            "payment_external_id": None,
            "estimated_delivery_at": None,
            "client_status_message": client_message,
            "deployment_preference": "unset",
            "hosting_provider": None,
            "deployment_preference_at": None,
        }
        self._save_order(order)
        return {
            "ok": True,
            "order_id": order_id,
            "message": project_order_created_message(
                service_id,
                launch_mode=launch_mode,
                project_name=project_name or payload["business_name"].strip(),
            ),
            "package_name": package["name"],
            "price_eur": package["price_eur"],
            "currency": package.get("currency", "EUR"),
            "symbol": package.get("symbol", "€"),
            "market_code": package.get("market_code", "DE"),
            "price_label": package.get("price_label"),
            "motion_level": motion,
            "deliverables": order["deliverables"],
            "buyer_insights": buyer_insights,
        }

    def list_orders(self, limit: int = 20) -> list[dict]:
        orders = self._load_all()
        orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
        return [self._summary(o) for o in orders[:limit]]

    def list_pending(self) -> list[dict]:
        return [o for o in self.list_orders(50) if o["status"] == "pending_confirmation"]

    def get_order(self, order_id: str) -> dict | None:
        for order in self._load_all():
            if order.get("order_id") == order_id:
                return order
        return None

    def confirm_order(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order["status"] not in ("pending_confirmation", "awaiting_payment"):
            raise ValueError("invalid_status")
        order["status"] = "confirmed"
        order["status_label"] = "Подтверждено · отправьте КП клиенту"
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return self._summary(order)

    def start_production(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order["status"] not in ("pending_confirmation", "confirmed", "awaiting_payment", "paid"):
            raise ValueError("invalid_status")

        existing_product_id = (order.get("product_id") or "").strip()
        if existing_product_id:
            product = self._factory_intent._factory.get_product(existing_product_id)
            if not product:
                raise ValueError("product_not_found")
            from app.factory.market_delivery import client_status_label

            market = str(order.get("market_code") or "DE")
            order["status"] = "in_production"
            order["status_label"] = client_status_label("in_production", market)
            order["product_id"] = existing_product_id
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_order(order)
            return {
                "ok": True,
                "order": self._summary(order),
                "product_id": existing_product_id,
                "message": "Zahlung erhalten. Produktion läuft mit dem bestehenden Entwurf.",
            }

        brief = self._factory_brief(order)
        legal = order.get("client_legal") if isinstance(order.get("client_legal"), dict) else {}
        legal = dict(legal)
        package_id = str(order.get("package_id") or "basic")
        street = str(legal.get("street") or "").strip()
        market = str(order.get("market_code") or legal.get("country") or "DE")
        from app.factory.motion_brief import gate_motion_level, normalize_motion_level

        motion = normalize_motion_level(str(order.get("motion_level") or "none"))
        gate = gate_motion_level(motion)
        if not gate["ok"]:
            raise ValueError("WAITLIST_REQUIRED")
        contacts = {
            "business_name": order.get("business_name"),
            "phone": order.get("phone"),
            "whatsapp": order.get("whatsapp") or order.get("phone"),
            "email": order.get("email") or legal.get("email"),
            "city": order.get("city") or legal.get("city"),
            "street": street,
            "package_id": package_id,
            "needs_logo": bool(order.get("needs_logo")),
            "market_code": market,
            "motion_level": motion,
        }
        if not legal.get("country"):
            legal["country"] = market
        intent = FactoryIntentRequest(
            product_type="landing-page",
            description=brief,
            audience=f"Kunden in {order.get('city') or 'der Region'}",
            goal="Anfragen und Termine über die Website",
            price_eur=float(order["price_eur"]),
            deadline=None,
            client_legal=legal or None,
            package_id=package_id if package_id in ("basic", "business", "premium") else "basic",
            contacts=contacts,
            motion_level=motion,
        )
        result = self._factory_intent.submit(intent)
        from app.factory.market_delivery import client_status_label

        order["status"] = "in_production"
        order["status_label"] = client_status_label("in_production", market)
        order["product_id"] = result.get("product_id")
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return {
            "ok": True,
            "order": self._summary(order),
            "product_id": result.get("product_id"),
            "message": "Produktion gestartet. Landing Page wird vorbereitet.",
        }

    def _suggest_package(self, payload: dict) -> str:
        if payload.get("needs_domain"):
            return "premium"
        if payload.get("needs_logo"):
            return "business"
        if len((payload.get("extra_wishes") or "").strip()) > 120:
            return "business"
        return "basic"

    def _factory_brief(self, order: dict) -> str:
        lines = [
            f"Kundenauftrag: {order['business_name']}",
            order["description"],
            f"Stadt: {order.get('city') or 'nicht angegeben'}",
            f"Telefon: {order.get('phone') or '—'}",
            f"WhatsApp: {order.get('whatsapp') or '—'}",
            f"E-Mail: {order.get('email') or '—'}",
            f"Paket: {order['package_name']} ({order.get('price_label') or order['price_eur']})",
        ]
        website = (order.get("company_website") or "").strip()
        if website:
            lines.append(f"Bestehende Website: {website}")
        analysis = order.get("site_analysis")
        if isinstance(analysis, dict) and not analysis.get("error"):
            lines.append("Analyse der bestehenden Website (für den neuen Landing-Neustart):")
            if analysis.get("title"):
                lines.append(f"  Titel: {analysis['title']}")
            if analysis.get("tech_stack"):
                lines.append(f"  Technik: {', '.join(analysis['tech_stack'])}")
            strengths = analysis.get("strengths") or []
            issues = analysis.get("issues") or []
            if strengths:
                lines.append("  Stärken: " + "; ".join(str(s) for s in strengths[:6]))
            if issues:
                lines.append("  Schwächen / Chancen: " + "; ".join(str(i) for i in issues[:8]))
            score = analysis.get("improvement_score")
            if score is not None:
                lines.append(f"  Verbesserungs-Score: {score}")
            lines.append(
                "Bitte nutze diese Analyse zusammen mit den Kundenantworten — "
                "neuer Landing Page Neustart, kein Flickwerk am alten CMS."
            )
        elif website:
            lines.append(
                "Website angegeben, Analyse nicht verfügbar — "
                "Landing trotzdem am Geschäft ausrichten (Path A Neustart)."
            )
        if order.get("needs_logo"):
            lines.append(
                "Kundenlogo einbinden (bestehende Datei nach Bestellung) "
                "und Firmenfarben berücksichtigen — kein neues Logo-Design."
            )
        if order.get("needs_domain"):
            lines.append(
                "Hilfe bei Domain-Auswahl, Kauf und Einrichtung "
                "(laufende Gebühren zahlt der Kunde beim Registrar)."
            )
        if order.get("extra_wishes"):
            lines.append(f"Wünsche: {order['extra_wishes']}")
        legal = order.get("client_legal") if isinstance(order.get("client_legal"), dict) else {}
        if legal:
            lines.append("Impressum-Daten (für DE Go-live, Kunde muss prüfen):")
            for key in (
                "owner_name",
                "legal_form",
                "street",
                "zip",
                "city",
                "managing_director",
                "vat_id",
            ):
                val = str(legal.get(key) or "").strip()
                if val:
                    lines.append(f"  {key}: {val}")
        return "\n".join(lines)

    @staticmethod
    def _client_legal_payload(payload: dict) -> dict:
        raw = payload.get("client_legal")
        if isinstance(raw, dict):
            return {k: v for k, v in raw.items() if v not in (None, "")}
        # Flattened optional fields from older clients
        keys = (
            "owner_name",
            "legal_form",
            "street",
            "zip",
            "city",
            "country",
            "email",
            "phone",
            "managing_director",
            "vat_id",
            "handelsregister",
            "register_court",
            "uses_maps",
            "uses_analytics",
        )
        out = {k: payload.get(k) for k in keys if payload.get(k) not in (None, "")}
        return out

    @staticmethod
    def _normalize_company_website(raw: object) -> str | None:
        text = str(raw or "").strip()
        if not text:
            return None
        if not re.match(r"^https?://", text, flags=re.I):
            text = f"https://{text}"
        if len(text) > 400:
            return None
        return text

    def _analyze_company_website(self, url: str) -> dict | None:
        """Best-effort Path A analysis — never blocks order creation."""
        try:
            from app.integration.site_analysis_service import SiteAnalysisService

            result = SiteAnalysisService(self._memory).analyze(url, use_cache=True)
            if not isinstance(result, dict):
                return {"url": url, "error": "invalid_analysis"}
            # Persist a compact snapshot for Factory / CEO review
            return {
                "url": result.get("url") or url,
                "final_url": result.get("final_url"),
                "title": result.get("title"),
                "has_https": result.get("has_https"),
                "has_viewport": result.get("has_viewport"),
                "load_ms": result.get("load_ms"),
                "issues": list(result.get("issues") or [])[:12],
                "strengths": list(result.get("strengths") or [])[:8],
                "tech_stack": list(result.get("tech_stack") or [])[:6],
                "improvement_score": result.get("improvement_score"),
                "detected_lang": result.get("detected_lang"),
                "error": result.get("error"),
                "analyzed_at": result.get("analyzed_at"),
                "from_cache": bool(result.get("from_cache")),
            }
        except Exception as exc:
            return {"url": url, "error": f"analysis_failed:{type(exc).__name__}"}

    def _proposal_text(self, package: dict, payload: dict, *, project_ctx: dict | None = None) -> str:
        ctx = project_ctx or {}
        service_id = ctx.get("service_id") or SERVICE_WEBSITE
        label = service_label_ru(service_id, fallback="проект")
        name = payload["business_name"].strip()
        deliverables = "\n".join(f"✔ {d}" for d in package["deliverables"])
        if ctx.get("launch_mode"):
            deliverables = "\n".join(
                f"✔ {d}" for d in project_launch_deliverables(service_id)
            )
        price_line = package.get("price_label") or f"{package['price_eur']} {package.get('symbol', '€')}"
        return (
            f"Guten Tag,\n\n"
            f"vielen Dank für Ihre Anfrage zu {label} «{name}».\n\n"
            f"Startpreis: {price_line}\n\n"
            f"Nach der Zahlung:\n{deliverables}\n\n"
            f"Lieferzeit: 5–7 Werktage nach Bestätigung und Zahlung.\n\n"
            f"Wenn Sie starten möchten, schreiben Sie uns — wir senden Rechnung / Zahlungslink.\n\n"
            f"Mit freundlichen Grüßen\n{BRAND_NAME}"
        )

    def _resolve_project_context(self, visitor_id: str | None) -> dict:
        vid = (visitor_id or "").strip()[:64]
        if not vid:
            return {
                "service_id": SERVICE_WEBSITE,
                "project_name": None,
                "launch_mode": False,
            }
        try:
            from app.integration.project_platform.service import ProjectPlatformService

            state = ProjectPlatformService(self._memory).get_for_visitor(vid)
        except Exception:
            return {
                "service_id": SERVICE_WEBSITE,
                "project_name": None,
                "launch_mode": False,
            }
        if not state.get("has_project") or not state.get("project"):
            return {
                "service_id": SERVICE_WEBSITE,
                "project_name": None,
                "launch_mode": False,
            }
        project = state["project"]
        service_id = str(project.get("service_id") or SERVICE_WEBSITE)
        company = ""
        for item in project.get("journey", {}).get("items", []):
            if item.get("id") == "company" and item.get("status") == "done":
                company = str(item.get("value") or "").strip()
                break
        if not company:
            title = str(project.get("identity", {}).get("title") or "").strip()
            if title and title not in ("Мой проект", "Хочу создать сайт для своей компании."):
                company = title
        has_preview = any(
            art.get("kind") == "preview" and art.get("href")
            for ver in project.get("versions", [])
            for art in ver.get("artifacts", [])
        )
        launch_mode = bool(has_preview and company)
        return {
            "service_id": service_id,
            "project_name": company or None,
            "launch_mode": launch_mode,
        }

    def mark_delivered_by_product(self, product_id: str) -> dict | None:
        """Factory handoff → sales order delivered + review token (Path A trust)."""
        pid = (product_id or "").strip()
        if not pid:
            return None
        order = next(
            (o for o in self._load_all() if str(o.get("product_id") or "").strip() == pid),
            None,
        )
        if not order:
            return None
        return self.mark_order_delivered(str(order["order_id"]))

    def mark_order_delivered(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") not in ("paid", "in_production", "ready", "delivered"):
            raise ValueError("not_paid")
        now = datetime.now(timezone.utc).isoformat()
        order["status"] = "delivered"
        order["status_label"] = "An den Kunden übergeben"
        order["delivered_at"] = order.get("delivered_at") or now
        order["review_eligible"] = True
        if not order.get("review_token"):
            order["review_token"] = new_review_token()
        order["updated_at"] = now
        self._save_order(order)
        return order

    def public_status(self, order_id: str) -> dict:
        from app.factory.market_delivery import (
            client_current_step,
            client_next_step,
            client_status_label,
            client_timeline,
            market_ui_lang,
            normalize_market,
        )
        from app.integration.market_registry import format_amount, get_market

        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        market = normalize_market(str(order.get("market_code") or "DE"))
        currency = str(order.get("currency") or get_market(market).currency or "EUR")
        symbol = str(order.get("symbol") or get_market(market).symbol or "€")
        amount = float(order.get("price_eur") or 0)
        price_label = str(order.get("price_label") or "").strip() or format_amount(
            int(round(amount)), symbol
        )
        service_id = str(order.get("service_id") or SERVICE_WEBSITE)
        launch_mode = bool(order.get("launch_mode"))
        download_ready = self._client_download_ready(order)
        submitted = bool(order.get("review_submitted"))
        eligible = (
            bool(order.get("review_eligible"))
            and str(order.get("status") or "") == "delivered"
            and not submitted
        )
        token = str(order.get("review_token") or "") if eligible else ""
        status = str(order.get("status") or "")
        return {
            "order_id": order["order_id"],
            "business_name": order["business_name"],
            "package_name": order["package_name"],
            "price_eur": amount,
            "price_label": price_label,
            "currency": currency,
            "symbol": symbol,
            "market_code": market,
            "ui_lang": market_ui_lang(market),
            "motion_level": str(order.get("motion_level") or "none"),
            "status": status,
            "status_label": client_status_label(status, market),
            "current_step": client_current_step(status, market),
            "next_step": client_next_step(status, market),
            "timeline": client_timeline(status, market),
            "estimated_delivery_at": order.get("estimated_delivery_at"),
            "estimated_hours": order.get("estimated_hours"),
            "client_message": order.get("client_status_message")
            or self._default_client_message(order),
            "client_receipt_text": order.get("client_receipt_text", ""),
            "product_id": order.get("product_id"),
            "paid": status in ("paid", "in_production", "ready", "delivered"),
            "download_ready": download_ready,
            "download_url": f"/api/sales/orders/{order_id}/download" if download_ready else None,
            "service_id": service_id,
            "launch_mode": launch_mode,
            "review_eligible": eligible,
            "review_submitted": submitted,
            "review_url": f"/order/review/{order_id}?token={token}" if token else None,
            "deployment_preference": str(order.get("deployment_preference") or "unset"),
            "hosting_provider": order.get("hosting_provider"),
            "assisted_guide": self._assisted_guide_payload(order),
        }

    def set_deployment_preference(
        self,
        order_id: str,
        preference: str,
        hosting_provider: str | None = None,
    ) -> dict:
        """Client chooses ZIP Only vs Assisted after ZIP is ready. No credentials stored."""
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if not self._client_download_ready(order):
            raise ValueError("download_not_ready")

        pref = str(preference or "").strip().lower()
        if pref not in ("zip_only", "assisted"):
            raise ValueError("invalid_preference")

        provider: str | None = None
        raw_provider = (hosting_provider or "").strip().lower() or None
        if raw_provider:
            if raw_provider not in HOSTING_PROVIDERS:
                raise ValueError("invalid_provider")
            provider = raw_provider

        now = datetime.now(timezone.utc).isoformat()
        order["deployment_preference"] = pref
        order["hosting_provider"] = provider
        order["deployment_preference_at"] = now
        for banned in (
            "hosting_password",
            "ftp_password",
            "password",
            "credentials",
            "api_token",
        ):
            order.pop(banned, None)
        order["updated_at"] = now
        self._save_order(order)

        if pref == "assisted":
            try:
                from app.integration.owner_notification_service import (
                    OwnerNotificationService,
                )

                provider_label = provider or "not_selected"
                OwnerNotificationService(self._memory).notify(
                    title="Assisted Deployment angefragt",
                    message=(
                        f"{order.get('business_name')} · {order_id} · "
                        f"Anbieter: {provider_label}. "
                        "Keine Hosting-Passwörter in Virtus — Variante A/B mit dem Kunden."
                    ),
                    order_id=order_id,
                )
            except Exception as exc:
                logger.warning("assisted deployment notify failed: %s", exc)

        return self.public_status(order_id)

    @staticmethod
    def _assisted_guide_payload(order: dict) -> dict | None:
        pref = str(order.get("deployment_preference") or "unset")
        if pref != "assisted":
            return None
        return {
            "headline": "Wir können helfen, die Website zu veröffentlichen.",
            "trust": [
                "Website läuft auf Ihrem Hosting",
                "Domain gehört Ihnen",
                "Hosting-Konto gehört Ihnen",
                "SSL und DNS gehören Ihnen",
                "Alle Anbieter-Rechnungen gehen an Sie",
            ],
            "never_stores": [
                "Hosting-Passwort",
                "Domain-Passwort",
                "Bankkarten",
                "Dauerhaften Zugang",
            ],
            "variant_a": (
                "Bevorzugt: Sie legen einen temporären Benutzer an oder laden uns "
                "als Helfer ein. Nach Go-live entfernen Sie den Zugang — Sie bleiben "
                "alleiniger Eigentümer."
            ),
            "variant_b": (
                "Falls kein temporärer Zugang möglich ist: Sie bleiben eingeloggt und "
                "folgen der Anleitung; Hilfe per Chat oder Anruf."
            ),
            "providers": sorted(HOSTING_PROVIDERS),
            "hosting_provider": order.get("hosting_provider"),
        }

    def build_client_download(self, order_id: str) -> tuple[bytes, str]:
        """Paid Path A order → ZIP with landing + legal pages (no CEO gate)."""
        from app.factory.market_delivery import client_status_label, normalize_market

        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if not self._client_download_ready(order):
            raise ValueError("download_not_ready")
        product_id = str(order.get("product_id") or "").strip()
        factory = getattr(self._factory_intent, "_factory", None)
        if factory is None or not hasattr(factory, "build_client_delivery_zip"):
            raise ValueError("factory_unavailable")
        market = normalize_market(str(order.get("market_code") or "DE"))
        # Ensure product meta carries market before ZIP pack regenerates legal pages.
        try:
            meta = factory._load_meta(product_id)  # type: ignore[attr-defined]
            if isinstance(meta, dict) and meta.get("market_code") != market:
                meta["market_code"] = market
                product_dir = factory._sandbox / product_id  # type: ignore[attr-defined]
                (product_dir / "meta.json").write_text(
                    __import__("json").dumps(meta, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        except Exception:
            pass
        data, filename = factory.build_client_delivery_zip(product_id)
        order["client_downloaded_at"] = datetime.now(timezone.utc).isoformat()
        if order.get("status") == "in_production":
            order["status"] = "ready"
            order["status_label"] = client_status_label("ready", market)
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return data, filename

    def _client_download_ready(self, order: dict) -> bool:
        if order.get("status") not in ("paid", "in_production", "ready", "delivered"):
            return False
        product_id = str(order.get("product_id") or "").strip()
        if not product_id:
            return False
        factory = getattr(self._factory_intent, "_factory", None)
        if factory is None or not hasattr(factory, "get_product"):
            return False
        return bool(factory.get_product(product_id))

    def _client_timeline(self, order: dict) -> list[dict]:
        from app.factory.market_delivery import client_timeline

        return client_timeline(str(order.get("status", "")), order.get("market_code"))

    def _client_next_step(self, order: dict) -> str:
        from app.factory.market_delivery import client_next_step

        return client_next_step(str(order.get("status", "")), order.get("market_code"))

    def _client_status_label(self, order: dict) -> str:
        from app.factory.market_delivery import client_status_label

        return client_status_label(str(order.get("status", "")), order.get("market_code"))

    def _client_current_step(self, order: dict) -> str:
        return project_client_current_step(
            str(order.get("service_id") or SERVICE_WEBSITE),
            str(order.get("status", "")),
        )

    def _default_client_message(self, order: dict) -> str:
        if order.get("status") == "awaiting_payment":
            return project_awaiting_payment_message(
                launch_mode=bool(order.get("launch_mode")),
            )
        return ""

    def _summary(self, order: dict) -> dict:
        return {
            "order_id": order["order_id"],
            "status": order["status"],
            "status_label": order["status_label"],
            "business_name": order["business_name"],
            "city": order.get("city", ""),
            "phone": order.get("phone", ""),
            "whatsapp": order.get("whatsapp", ""),
            "package_name": order["package_name"],
            "price_eur": order["price_eur"],
            "created_at": order["created_at"],
            "product_id": order.get("product_id"),
            "proposal_text": order.get("proposal_text", ""),
            "motion_level": str(order.get("motion_level") or "none"),
            "market_code": order.get("market_code"),
            "paid": order.get("status") in ("paid", "in_production", "ready", "delivered"),
            "paid_at": order.get("paid_at"),
            "estimated_delivery_at": order.get("estimated_delivery_at"),
        }

    def _orders_path(self) -> Path:
        return self._memory / "sales_orders.json"

    def _load_all(self) -> list[dict]:
        path = self._orders_path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_order(self, order: dict) -> None:
        orders = [o for o in self._load_all() if o.get("order_id") != order.get("order_id")]
        orders.append(order)
        self._orders_path().write_text(
            json.dumps(orders, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
