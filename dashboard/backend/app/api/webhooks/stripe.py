"""POST /api/webhooks/stripe — Stripe checkout.session.completed."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.integration.context import get_integration
from app.schemas import StripeWebhookResponse
from app.services.finance_center import (
    StripeWebhookCriticalError,
    StripeWebhookError,
    handle_stripe_webhook_event,
)

router = APIRouter(tags=["webhooks"])


@router.post("/api/webhooks/stripe", response_model=StripeWebhookResponse)
@router.post("/webhooks/stripe", response_model=StripeWebhookResponse)
async def stripe_webhook(request: Request) -> StripeWebhookResponse:
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    ctx = get_integration()
    try:
        result = handle_stripe_webhook_event(payload, signature, ctx.revenue)
    except StripeWebhookCriticalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except StripeWebhookError as exc:
        raise HTTPException(status_code=400, detail="Некорректный webhook") from exc
    except ValueError as exc:
        code = str(exc)
        if code == "order_not_found":
            raise HTTPException(status_code=404, detail="Заказ не найден") from exc
        if code == "amount_mismatch":
            raise HTTPException(status_code=400, detail="Сумма не совпадает") from exc
        raise HTTPException(status_code=400, detail="Оплата не прошла") from exc
    return StripeWebhookResponse(**result)
