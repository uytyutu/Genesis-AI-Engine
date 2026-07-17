"""Sprint 1 — Genesis Sales: client orders and pricing (no payment gateway yet)."""

from __future__ import annotations

import json
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
from app.schemas import FactoryIntentRequest

_PACKAGES = {
    "basic": {
        "id": "basic",
        "name": "Landing Basic",
        "price_eur": 350,
        "deliverables": [
            "Moderne One-Page-Website",
            "Responsive für Smartphone, Tablet und Desktop",
            "Basis-SEO",
            "Kontakte und Anfrageformular",
            "WhatsApp-Button",
        ],
    },
    "business": {
        "id": "business",
        "name": "Landing Business",
        "price_eur": 650,
        "deliverables": [
            "Alles aus Basic",
            "Google Maps",
            "Bewertungsblock",
            "Logo im Layout (bestehendes Kundenlogo)",
            "Erweitertes SEO",
            "1 Korrekturrunde",
        ],
    },
    "premium": {
        "id": "premium",
        "name": "Landing Premium",
        "price_eur": 1200,
        "deliverables": [
            "Alles aus Business",
            "Premium-Design",
            "Responsive für Smartphone, Tablet und Desktop",
            "Basis-SEO",
            "Google Analytics Einrichtung",
            "Hilfe bei Domain-Auswahl, Kauf und Einrichtung",
            "Termin-/Anfrageformular oder Rechner",
            "14 Tage Support nach dem Launch",
            "3 Korrekturrunden",
            "Prioritäts-Support",
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
        package_id = payload.get("package_id") or self._suggest_package(payload)
        package, _offer = self._package_offer(
            package_id,
            market_code=payload.get("market_code"),
            visitor_id=payload.get("visitor_id"),
            city=payload.get("city"),
            extra_text=payload.get("description"),
        )
        project_ctx = self._resolve_project_context(payload.get("visitor_id"))
        service_id = project_ctx["service_id"]
        launch_mode = bool(project_ctx["launch_mode"])
        project_name = project_ctx.get("project_name")
        order_id = f"ord-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        client_message = project_awaiting_payment_message(launch_mode=launch_mode)
        company_website = self._normalize_company_website(payload.get("company_website"))
        site_analysis = self._analyze_company_website(company_website) if company_website else None
        order = {
            "order_id": order_id,
            "status": "awaiting_payment",
            "status_label": "Wartet auf Zahlung",
            "package_id": package_id,
            "package_name": package["name"],
            "price_eur": package["price_eur"],
            "currency": package.get("currency", "EUR"),
            "symbol": package.get("symbol", "€"),
            "market_code": package.get("market_code", "DE"),
            "price_label": package.get("price_label", f"{package['price_eur']} €"),
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
            "needs_domain": bool(payload.get("needs_domain")),
            "extra_wishes": (payload.get("extra_wishes") or "").strip(),
            "company_website": company_website,
            "site_analysis": site_analysis,
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
            "deliverables": order["deliverables"],
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
            order["status"] = "in_production"
            order["status_label"] = "In Arbeit"
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
        intent = FactoryIntentRequest(
            product_type="landing-page",
            description=brief,
            audience=f"Kunden in {order.get('city') or 'der Region'}",
            goal="Anfragen und Termine über die Website",
            price_eur=float(order["price_eur"]),
            deadline=None,
            client_legal=legal or None,
        )
        result = self._factory_intent.submit(intent)
        order["status"] = "in_production"
        order["status_label"] = "In Arbeit"
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

    def public_status(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        timeline = self._client_timeline(order)
        service_id = str(order.get("service_id") or SERVICE_WEBSITE)
        launch_mode = bool(order.get("launch_mode"))
        return {
            "order_id": order["order_id"],
            "business_name": order["business_name"],
            "package_name": order["package_name"],
            "price_eur": order["price_eur"],
            "status": order["status"],
            "status_label": self._client_status_label(order),
            "current_step": self._client_current_step(order),
            "next_step": self._client_next_step(order),
            "timeline": timeline,
            "estimated_delivery_at": order.get("estimated_delivery_at"),
            "estimated_hours": order.get("estimated_hours"),
            "client_message": order.get("client_status_message")
            or self._default_client_message(order),
            "client_receipt_text": order.get("client_receipt_text", ""),
            "product_id": order.get("product_id"),
            "paid": order.get("status") in ("paid", "in_production", "ready", "delivered"),
            "service_id": service_id,
            "launch_mode": launch_mode,
        }

    def _client_timeline(self, order: dict) -> list[dict]:
        return project_client_timeline(str(order.get("status", "")))

    def _client_next_step(self, order: dict) -> str:
        return project_client_next_step(
            str(order.get("service_id") or SERVICE_WEBSITE),
            str(order.get("status", "")),
        )

    def _client_status_label(self, order: dict) -> str:
        mapping = {
            "awaiting_payment": "Wartet auf Zahlung",
            "pending_confirmation": "Wartet auf Bestätigung",
            "confirmed": "Bestätigt",
            "paid": "Bezahlt",
            "in_production": "In Arbeit",
            "ready": "Fertig",
            "delivered": "An den Kunden übergeben",
        }
        return mapping.get(order.get("status", ""), order.get("status_label", ""))

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
