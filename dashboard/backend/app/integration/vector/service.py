"""Vector context service — resolve surface + products + setup into one dialog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.store_admin.setup_status import StoreSetupStatusService
from app.integration.vector.business_setup import build_business_setup
from app.integration.vector.dialog_wizard import (
    build_customer_dialog_stub,
    build_platform_dialog,
    build_store_dialog,
    build_website_dialog_stub,
)
from app.integration.vector.progress import VectorProgressStore
from app.integration.vector.ai_health import build_ai_health
from app.integration.vector.website_tips import (
    build_website_admin_dialog,
    scan_website_tips,
)


class VectorContextService:
    def __init__(self, memory_dir: Path, *, sales: Any | None = None) -> None:
        self._memory = Path(memory_dir)
        self._sales = sales
        self._setup = StoreSetupStatusService(self._memory)
        self._progress = VectorProgressStore(self._memory)

    def _customer_orders(
        self, *, customer_id: str | None, email: str | None
    ) -> list[dict[str, Any]]:
        if self._sales is None:
            return []
        try:
            rows = self._sales.list_orders_for_customer(
                customer_id=str(customer_id or ""),
                email=email,
            )
            return [o for o in (rows or []) if isinstance(o, dict)]
        except Exception:
            return []

    def _primary_shop(
        self, orders: list[dict[str, Any]]
    ) -> tuple[str | None, str | None, str | None]:
        for order in orders:
            kind = str(order.get("product_kind") or "")
            if kind == "shop" or "store" in kind:
                oid = str(order.get("order_id") or "") or None
                name = str(
                    order.get("store_name")
                    or order.get("business_name")
                    or order.get("package_name")
                    or ""
                ) or None
                return oid, name, order.get("shop_pipeline")
        return None, None, None

    def _has_website(self, orders: list[dict[str, Any]]) -> bool:
        for order in orders:
            kind = str(order.get("product_kind") or "")
            pid = str(order.get("product_id") or "")
            if kind in {"website", "site"} or pid.startswith("web"):
                return True
            if "website" in kind:
                return True
        return False

    def store_dialog(
        self,
        order_id: str,
        *,
        store_name: str = "",
        shop_pipeline: str | None = None,
        learning_mode: str | None = None,
        step_id: str | None = None,
        include_welcome: bool = False,
        persist: bool = True,
    ) -> dict[str, Any]:
        saved = self._progress.load("store_admin", order_id)
        mode = learning_mode if learning_mode is not None else saved.get("learning_mode")
        sid = step_id if step_id is not None else saved.get("step_id")

        setup = self._setup.get(
            order_id,
            store_name=store_name,
            shop_pipeline=shop_pipeline,
        )
        setup["store_name"] = store_name or setup.get("store_name")
        dialog = build_store_dialog(
            setup,
            learning_mode=mode,
            step_id=sid,
            include_welcome=include_welcome or (mode == "show" and not sid),
        )
        dialog["setup"] = {
            "readiness_pct": setup.get("readiness_pct"),
            "setup_pct": setup.get("setup_pct"),
            "product_count": setup.get("product_count"),
            "steps": setup.get("steps"),
            "tips": setup.get("tips"),
        }
        dialog["order_id"] = order_id
        dialog["progress"] = saved

        if persist and mode in ("skip", "show"):
            wizard = dialog.get("wizard") or {}
            cur_step = wizard.get("step_id") or sid
            self._progress.save(
                "store_admin",
                order_id,
                learning_mode=mode,
                step_id=cur_step,
            )
            dialog["progress"] = self._progress.load("store_admin", order_id)
        return dialog

    def save_progress(
        self,
        scope: str,
        subject_id: str,
        *,
        learning_mode: str | None = None,
        step_id: str | None = None,
        mark_completed: str | None = None,
    ) -> dict[str, Any]:
        return self._progress.save(
            scope,
            subject_id,
            learning_mode=learning_mode,
            step_id=step_id,
            mark_completed=mark_completed,
        )

    def website_tips_for_order(
        self,
        order: dict[str, Any],
    ) -> dict[str, Any]:
        product_id = str(order.get("product_id") or "").strip() or None
        return scan_website_tips(
            product_id=product_id,
            niche=str(order.get("business_name") or order.get("niche") or "") or None,
        )

    def website_dialog_for_order(self, order: dict[str, Any]) -> dict[str, Any]:
        tips = self.website_tips_for_order(order)
        return build_website_admin_dialog(tips)

    def ai_health_for_customer(
        self, *, customer_id: str | None, email: str | None
    ) -> dict[str, Any]:
        orders = self._customer_orders(customer_id=customer_id, email=email)
        has_website = self._has_website(orders)
        store_id, _, _ = self._primary_shop(orders)
        return build_ai_health(
            has_website=has_website,
            has_store=bool(store_id),
            vector_active=True,
            commerce_live=False,
            analytics_live=False,
            crm_live=False,
        )

    def business_bundle(
        self, *, customer_id: str | None, email: str | None
    ) -> dict[str, Any]:
        biz = self.business_setup_for_customer(
            customer_id=customer_id, email=email
        )
        health = self.ai_health_for_customer(
            customer_id=customer_id, email=email
        )
        return {"ok": True, "business_setup": biz, "ai_health": health}
    def business_setup_for_customer(
        self,
        *,
        customer_id: str | None,
        email: str | None,
    ) -> dict[str, Any]:
        orders = self._customer_orders(customer_id=customer_id, email=email)
        has_website = self._has_website(orders)
        store_order_id, store_name, shop_pipeline = self._primary_shop(orders)
        has_store = bool(store_order_id)

        product_count = 0
        branding_done = False
        payments = False
        shipping = False
        taxes = False
        published = False

        if store_order_id:
            setup = self._setup.get(
                store_order_id,
                store_name=store_name or "",
                shop_pipeline=shop_pipeline,
            )
            product_count = int(setup.get("product_count") or 0)
            steps = {
                s["id"]: s for s in setup.get("steps") or [] if isinstance(s, dict)
            }
            branding_done = bool(
                (steps.get("logo") or {}).get("done")
                or (steps.get("colors") or {}).get("done")
            )
            payments = bool((steps.get("stripe") or {}).get("done"))
            shipping = bool((steps.get("shipping") or {}).get("done"))
            taxes = bool((steps.get("taxes") or {}).get("done"))
            email = bool((steps.get("email") or {}).get("done"))
            published = bool((steps.get("publish") or {}).get("done"))

        return build_business_setup(
            has_website=has_website,
            has_store=has_store,
            product_count=product_count,
            branding_done=branding_done,
            store_published=published,
            primary_store_order_id=store_order_id,
            payments_connected=payments,
            shipping_connected=shipping,
            taxes_configured=taxes,
            email_connected=email,
        )

    def platform_dialog(
        self,
        *,
        customer_id: str | None,
        email: str | None,
        learning_mode: str | None = "skip",
    ) -> dict[str, Any]:
        orders = self._customer_orders(customer_id=customer_id, email=email)
        store_order_id, store_name, _pipeline = self._primary_shop(orders)
        has_website = self._has_website(orders)
        biz = self.business_setup_for_customer(
            customer_id=customer_id, email=email
        )
        dialog = build_platform_dialog(
            has_store=bool(store_order_id),
            store_order_id=store_order_id,
            store_name=store_name,
            has_website=has_website,
            business_setup=biz,
            learning_mode=learning_mode,
        )
        dialog["business_setup"] = biz
        return dialog

    def dialog_for_surface(
        self,
        surface: str,
        *,
        order_id: str | None = None,
        store_name: str = "",
        shop_pipeline: str | None = None,
        customer_id: str | None = None,
        email: str | None = None,
        learning_mode: str | None = None,
        step_id: str | None = None,
    ) -> dict[str, Any]:
        surface = (surface or "platform").strip().lower()
        if surface == "store_admin":
            if not order_id:
                return {"ok": False, "error": "order_id_required", "surface": surface}
            return self.store_dialog(
                order_id,
                store_name=store_name,
                shop_pipeline=shop_pipeline,
                learning_mode=learning_mode,
                step_id=step_id,
                include_welcome=learning_mode == "show" and not step_id,
            )
        if surface == "website_admin":
            if order_id and self._sales is not None:
                try:
                    order = self._sales.get_order(order_id)
                except Exception:
                    order = None
                if isinstance(order, dict):
                    return self.website_dialog_for_order(order)
            # Fall back: first website order for customer
            for o in self._customer_orders(customer_id=customer_id, email=email):
                kind = str(o.get("product_kind") or "")
                if kind in {"website", "site"} or "website" in kind:
                    return self.website_dialog_for_order(o)
            return build_website_dialog_stub()
        if surface == "customer":
            return build_customer_dialog_stub()
        return self.platform_dialog(
            customer_id=customer_id,
            email=email,
            learning_mode=learning_mode or "skip",
        )
