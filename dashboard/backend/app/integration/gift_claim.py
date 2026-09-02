"""Public gift claim: form → account + paid gift order → Factory path → credentials."""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import HTTPException


def _gen_password() -> str:
    # Readable enough to copy once; 12+ chars
    return secrets.token_urlsafe(9)


def claim_friend_gift(
    *,
    code: str,
    identity_service: Any,
    sales_service: Any,
    revenue_service: Any,
    body: dict[str, Any],
) -> dict[str, Any]:
    from app.integration.gift_token import peek_token, redeem_token

    peek = peek_token(code)
    if not peek.get("ok"):
        raise HTTPException(status_code=403, detail=str(peek.get("error") or "gift_code_invalid"))

    name = str(body.get("name") or body.get("contact_name") or "").strip()
    email = str(body.get("email") or "").strip()
    business_name = str(body.get("business_name") or body.get("company_name") or "").strip()
    city = str(body.get("city") or "").strip() or None
    niche = str(body.get("niche") or "").strip() or None
    description = str(body.get("description") or body.get("wishes") or "").strip()
    phone = str(body.get("phone") or "").strip() or None
    locale = str(body.get("locale") or "ru").strip()[:2] or "ru"

    if len(name) < 2:
        raise HTTPException(status_code=400, detail="name_required")
    if "@" not in email:
        raise HTTPException(status_code=400, detail="email_required")
    if len(business_name) < 2:
        raise HTTPException(status_code=400, detail="business_name_required")
    if len(description) < 10:
        raise HTTPException(status_code=400, detail="description_required")

    password = str(body.get("password") or "").strip()
    password_generated = False
    if len(password) < 8:
        password = _gen_password()
        password_generated = True

    # 1) Account (gift code replaces email OTP)
    try:
        session = identity_service.register(
            name=name,
            email=email,
            password=password,
            locale=locale,
            country=str(body.get("country") or ""),
            prior_visitor_id=str(body.get("visitor_id") or "") or None,
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail="email_already_registered",
            ) from exc
        raise

    customer_id = str(session.get("customer_id") or "")
    token = str(session.get("token") or "")

    # 2) Gift flags on Client Card
    try:
        card = identity_service._store.load_card(customer_id)
        if card:
            card.gift_account = True
            card.gift_unlimited = True
            card.unlimited = True
            card.workspace_mode = "gift_unlimited"
            card.tier = "premium"
            if business_name:
                card.company_display_name = business_name
            identity_service._store.save_card(card)
        company = identity_service._store.load_company_by_customer(customer_id)
        if company and business_name:
            company.name = business_name
            identity_service._store.save_company(company)
    except Exception:
        pass

    package_id = str(peek.get("package_id") or "standalone")
    order_payload = {
        "business_name": business_name,
        "description": description,
        "city": city,
        "phone": phone,
        "email": email.lower(),
        "niche": niche,
        "package_id": package_id,
        "commerce_mode": "standalone",
        "product_kind": "website",
        "gift_code": code.strip().upper(),
        "payment_mode": "gift",
        "customer_id": customer_id,
        "ui_lang": locale,
        "dialogue": description,
        "extra_wishes": str(body.get("extra_wishes") or "") or None,
        "brand_style": str(body.get("brand_style") or "modern") or "modern",
    }

    # 3) Create gift order (tagged; may auto-pay in HTTP layer — also pay here for safety)
    try:
        created = sales_service.create_order(order_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order_id = str(created.get("order_id") or "")
    if not order_id:
        raise HTTPException(status_code=500, detail="order_create_failed")

    # Bind customer + redeem + fulfill
    try:
        sales_service.attach_customer_by_email(customer_id=customer_id, email=email)
    except Exception:
        pass

    order = sales_service.get_order(order_id) or {}
    already_paid = str(order.get("status") or "") in {
        "paid",
        "in_production",
        "ready",
        "delivered",
    }
    if not already_paid:
        try:
            # redeem happens inside complete_gift_payment
            revenue_service.complete_gift_payment(order_id)
        except ValueError as exc:
            # If create_order path already redeemed somehow, try attach only
            msg = str(exc)
            if msg == "gift_code_used":
                # Order may exist unpaid — force apply if order still gift-tagged
                try:
                    peek2 = peek_token(code)
                    if peek2.get("ok"):
                        redeem_token(code, order_id=order_id)
                except Exception:
                    pass
            else:
                raise HTTPException(status_code=400, detail=msg) from exc

    order = sales_service.get_order(order_id) or order

    return {
        "ok": True,
        "gift": True,
        "message_ru": (
            "Готово. Virtus Core создал ваш кабинет и запускает сайт по описанию. "
            "Сохраните логин и пароль."
        ),
        "message_de": (
            "Fertig. Virtus Core hat Ihren Workspace erstellt und startet die Website. "
            "Bitte Login speichern."
        ),
        "email": email.lower(),
        "password": password,
        "password_generated": password_generated,
        "token": token,
        "name": name,
        "customer_id": customer_id,
        "order_id": order_id,
        "business_name": business_name,
        "package_id": package_id,
        "order_status": order.get("status"),
        "login_path": "/client/login",
        "workspace_path": "/client",
        "status_path": f"/order/status/{order_id}",
    }
