"""Sprint 1 — Genesis Sales: client orders and pricing (no payment gateway yet)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.schemas import FactoryIntentRequest

_PACKAGES = {
    "basic": {
        "id": "basic",
        "name": "Landing Basic",
        "price_eur": 350,
        "deliverables": [
            "Современный одностраничный сайт",
            "Адаптация под телефон, планшет и ПК",
            "Базовая SEO-оптимизация",
            "Контакты и форма заявки",
            "Кнопка WhatsApp",
        ],
    },
    "business": {
        "id": "business",
        "name": "Landing Business",
        "price_eur": 650,
        "deliverables": [
            "Всё из Basic",
            "Карта Google",
            "Блок отзывов",
            "Логотип в макете",
            "Расширенное SEO",
            "1 раунд правок",
        ],
    },
    "premium": {
        "id": "premium",
        "name": "Landing Premium",
        "price_eur": 1200,
        "deliverables": [
            "Всё из Business",
            "Премиум-дизайн",
            "Адаптация под телефон, планшет и ПК",
            "Базовая SEO-оптимизация",
            "Настройка Google Analytics",
            "Помощь с доменом",
            "Форма записи / калькулятор",
            "14 дней поддержки после запуска",
            "3 раунда правок",
            "Приоритетная поддержка",
        ],
    },
}


class SalesOrderService:
    def __init__(self, memory_dir: Path, factory_intent: object) -> None:
        self._memory = memory_dir
        self._factory_intent = factory_intent
        self._memory.mkdir(parents=True, exist_ok=True)

    def packages(self) -> list[dict]:
        return list(_PACKAGES.values())

    def create_order(self, payload: dict) -> dict:
        package_id = payload.get("package_id") or self._suggest_package(payload)
        package = _PACKAGES.get(package_id, _PACKAGES["basic"])
        order_id = f"ord-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        order = {
            "order_id": order_id,
            "status": "awaiting_payment",
            "status_label": "Ожидает оплаты",
            "package_id": package_id,
            "package_name": package["name"],
            "price_eur": package["price_eur"],
            "deliverables": package["deliverables"],
            "business_name": payload["business_name"].strip(),
            "description": payload["description"].strip(),
            "city": (payload.get("city") or "").strip(),
            "phone": (payload.get("phone") or "").strip(),
            "whatsapp": (payload.get("whatsapp") or "").strip(),
            "email": (payload.get("email") or "").strip(),
            "needs_logo": bool(payload.get("needs_logo")),
            "needs_domain": bool(payload.get("needs_domain")),
            "extra_wishes": (payload.get("extra_wishes") or "").strip(),
            "created_at": now,
            "updated_at": now,
            "product_id": None,
            "proposal_text": self._proposal_text(package, payload),
            "paid_at": None,
            "payment_provider": None,
            "payment_external_id": None,
            "estimated_delivery_at": None,
            "client_status_message": "",
        }
        self._save_order(order)
        return {
            "ok": True,
            "order_id": order_id,
            "message": (
                "Спасибо! Ваш заказ создан. Оплатите сейчас — и мы сразу начнём работу над сайтом."
            ),
            "package_name": package["name"],
            "price_eur": package["price_eur"],
            "deliverables": package["deliverables"],
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
        brief = self._factory_brief(order)
        intent = FactoryIntentRequest(
            product_type="landing-page",
            description=brief,
            audience=f"Клиенты в {order.get('city') or 'регионе'}",
            goal="Получать заявки с сайта",
            price_eur=float(order["price_eur"]),
            deadline=None,
        )
        result = self._factory_intent.submit(intent)
        order["status"] = "in_production"
        order["status_label"] = "В производстве"
        order["product_id"] = result.get("product_id")
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return {
            "ok": True,
            "order": self._summary(order),
            "product_id": result.get("product_id"),
            "message": "Производство запущено. Проверьте продукт в разделе «Продукты».",
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
            f"Заказ клиента: {order['business_name']}",
            order["description"],
            f"Город: {order.get('city') or 'не указан'}",
            f"Телефон: {order.get('phone') or '—'}",
            f"WhatsApp: {order.get('whatsapp') or '—'}",
            f"Email: {order.get('email') or '—'}",
            f"Пакет: {order['package_name']} ({order['price_eur']} €)",
        ]
        if order.get("needs_logo"):
            lines.append("Нужен логотип в макете.")
        if order.get("needs_domain"):
            lines.append("Нужна помощь с доменом.")
        if order.get("extra_wishes"):
            lines.append(f"Пожелания: {order['extra_wishes']}")
        return "\n".join(lines)

    def _proposal_text(self, package: dict, payload: dict) -> str:
        name = payload["business_name"].strip()
        deliverables = "\n".join(f"✔ {d}" for d in package["deliverables"])
        return (
            f"Здравствуйте!\n\n"
            f"Спасибо за заявку на сайт для «{name}».\n\n"
            f"Пакет: {package['name']} — {package['price_eur']} €\n\n"
            f"Вы получите:\n{deliverables}\n\n"
            f"Срок: 5–7 рабочих дней после подтверждения и оплаты.\n\n"
            f"Готовы начать — напишите, и мы вышлем счёт / ссылку на оплату.\n\n"
            f"С уважением,\n{BRAND_NAME}"
        )

    def public_status(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        timeline = self._client_timeline(order)
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
            "client_message": order.get("client_status_message") or self._default_client_message(order),
            "client_receipt_text": order.get("client_receipt_text", ""),
            "product_id": order.get("product_id"),
            "paid": order.get("status") in ("paid", "in_production", "ready", "delivered"),
        }

    def _client_timeline(self, order: dict) -> list[dict]:
        status = order.get("status", "")
        paid = status in ("paid", "in_production", "ready", "delivered")
        production = status in ("in_production", "ready", "delivered")
        return [
            {"id": "payment", "label": "Получена оплата", "done": paid},
            {"id": "production", "label": "Производство началось", "done": production},
        ]

    def _client_next_step(self, order: dict) -> str:
        status = order.get("status", "")
        if status == "awaiting_payment":
            return "Оплата заказа"
        if status in ("paid", "in_production"):
            return "Создание сайта"
        if status == "ready":
            return "Передача готового сайта"
        if status == "delivered":
            return "Заказ завершён"
        return "Обработка заказа"

    def _client_status_label(self, order: dict) -> str:
        mapping = {
            "awaiting_payment": "Ожидает оплаты",
            "pending_confirmation": "Ожидает подтверждения",
            "confirmed": "Подтверждено",
            "paid": "Оплачен",
            "in_production": "В работе",
            "ready": "Готово",
            "delivered": "Передано клиенту",
        }
        return mapping.get(order.get("status", ""), order.get("status_label", ""))

    def _client_current_step(self, order: dict) -> str:
        status = order.get("status", "")
        if status == "awaiting_payment":
            return "Ожидаем оплату, чтобы начать работу"
        if status in ("paid", "in_production"):
            return "Создаём ваш сайт"
        if status == "ready":
            return "Сайт готов — готовим передачу"
        if status == "delivered":
            return "Проект передан — спасибо за заказ!"
        return "Обрабатываем ваш заказ"

    def _default_client_message(self, order: dict) -> str:
        if order.get("status") == "awaiting_payment":
            return "Оплатите заказ — и мы сразу начнём работу."
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
