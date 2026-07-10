"""Unified handoff — one-time purchase vs subscription (all services)."""

from __future__ import annotations

from urllib.parse import urlencode

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME
from app.integration.product_line import artifact_label_ru, service_label_ru
from app.legal.handoff import one_time_purchase_handoff, subscription_handoff


def one_time_handoff_customer_ru(service_id: str) -> str:
    artifact = artifact_label_ru(service_id)
    label = service_label_ru(service_id).lower()
    return (
        f"**После разовой оплаты — {label}:**\n\n"
        f"**Что вы получаете:**\n"
        f"• готовый результат — **{artifact}**\n"
        "• исходные файлы и архив проекта\n"
        "• инструкции по использованию и публикации\n\n"
        f"**Что дальше:**\n"
        f"• {BRAND_NAME} завершает работу по этому заказу\n"
        "• проект переходит к вам — мы не ведём его дальше без отдельного соглашения\n"
        "• поддержка после передачи — только если вы её отдельно закажете\n\n"
        "Подробности — в AGB и разделе доверия на сайте."
    )


def subscription_handoff_customer_ru(service_id: str) -> str:
    artifact = artifact_label_ru(service_id)
    return (
        f"**С подпиской — {artifact} остаётся в {BRAND_NAME}:**\n\n"
        f"• проект и все версии хранятся в вашей цифровой компании\n"
        f"• {ASSISTANT_NAME} продолжает сопровождать — правки, новые версии, развитие\n"
        "• история работы и артефакты всегда доступны\n"
        "• это не скидка на разовую покупку, а другой формат сотрудничества\n\n"
        "Условия — в AGB и на странице доверия."
    )


def unified_handoff_message(
    purchase_type: str,
    service_id: str,
    *,
    locale: str = "ru",
) -> str:
    if purchase_type == "subscription":
        if locale.startswith("de"):
            return subscription_handoff()
        return subscription_handoff_customer_ru(service_id)
    if locale.startswith("de"):
        return one_time_purchase_handoff()
    return one_time_handoff_customer_ru(service_id)


def build_order_href(
    *,
    service_id: str,
    visitor_id: str,
    workspace_id: str | None = None,
    purchase_type: str = "one_time",
    package_id: str = "business",
) -> str:
    params: dict[str, str] = {
        "service_id": service_id,
        "visitor_id": visitor_id,
        "purchase_type": purchase_type,
        "package": package_id,
    }
    if workspace_id:
        params["workspace_id"] = workspace_id
    return f"/order?{urlencode(params)}"


def build_purchase_ctas(
    *,
    service_id: str,
    visitor_id: str,
    workspace_id: str | None = None,
) -> list[dict[str, str | bool | None]]:
    one_time = build_order_href(
        service_id=service_id,
        visitor_id=visitor_id,
        workspace_id=workspace_id,
        purchase_type="one_time",
    )
    sub = build_order_href(
        service_id=service_id,
        visitor_id=visitor_id,
        workspace_id=workspace_id,
        purchase_type="subscription",
    )
    return [
        {"href": one_time, "label": "💳 Разовая покупка", "group": "purchase", "available": True},
        {"href": sub, "label": f"🔄 Подписка с {ASSISTANT_NAME}", "group": "purchase", "available": True},
    ]
