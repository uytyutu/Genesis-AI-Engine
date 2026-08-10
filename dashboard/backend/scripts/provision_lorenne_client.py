"""Provision LORENNE (Svitlana) into live backend memory — Premium site + shop.

In-process (uses NEW pricing / cinematic rules). Writes into dashboard/backend/memory
so the already-running uvicorn can serve login + Client Card without restart.

Does not commit or deploy.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

# Demo bridge + JWT before importing app modules that read env
os.environ.setdefault("GENESIS_ALLOW_DEMO_PAYMENT", "1")
os.environ.setdefault(
    "GENESIS_CLIENT_JWT_SECRET",
    os.environ.get("GENESIS_CLIENT_JWT_SECRET")
    or os.environ.get("JWT_SECRET")
    or "lorenne-local-dev-secret",
)

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

# Soft-load secrets from .env.local (names only used for JWT / demo flags)
_env = BACKEND / ".env.local"
if _env.is_file():
    for _line in _env.read_text(encoding="utf-8", errors="replace").splitlines():
        if not _line or _line.strip().startswith("#") or "=" not in _line:
            continue
        _k, _v = _line.split("=", 1)
        _k = _k.strip()
        _v = _v.strip().strip('"').strip("'")
        if _k.startswith("GENESIS_") and _k not in os.environ:
            os.environ[_k] = _v
os.environ["GENESIS_ALLOW_DEMO_PAYMENT"] = "1"

EMAIL = os.environ.get("LORENNE_EMAIL", "Bulhakovasvitlana94@gmail.com").strip()
PASSWORD = os.environ.get("LORENNE_PASSWORD", "").strip()
NAME = os.environ.get("LORENNE_NAME", "Svitlana Bulhakova").strip()
BRAND = "LORENNE"
CITY = "Berlin"

if not PASSWORD:
    raise SystemExit(
        "Set LORENNE_PASSWORD in the environment before running this script."
    )

LOGO_SRC = Path(
    os.environ.get(
        "LORENNE_LOGO",
        r"C:\Users\hppav\.cursor\projects\d-Games-Genesis-AI-Engine\assets\lorenne-logo.png",
    )
)

GIFT_BOXES = [
    ("Kraft Tanken Box", 49.0, "Wellness", "Mood diary, Vitamintee, ätherisches Öl, Atemkarten, QR Relax."),
    ("Zeit für Dich Box", 54.0, "Relax", "Seidenschlafmaske, Badebombe, 5-Minuten-Notizbuch, Abendritual, QR."),
    ("Leseglück Box", 44.0, "Lifestyle", "Lesezeichen, Mini-Notizbuch, Buchquaste, Kerze."),
    ("Danke Box", 39.0, "Momente", "Naturhonig, Kerzen, Mini-Trockenblumen, Karte."),
    ("Mama Box", 59.0, "Momente", "Große Auswahl für Mütter — Pflege und Rituale."),
    ("Movie Night Box", 47.0, "Lifestyle", "QR Filme, Kakao-Rezept, Lichterkette, Guess the Movie."),
    ("Study Box", 42.0, "Study", "Pomodoro-Timer, Merktechnik-Karten, Sticker, Emergency Chocolate."),
    ("Pink Girl Box", 52.0, "Beauty", "Leuchtspiegel, Face Roller, Satin-Scrunchie, Mini-Parfum, Glow Challenge."),
    ("Self Love Box", 48.0, "Self Love", "30 Affirmationskarten."),
    ("Best Friends Box", 45.0, "Friends", "Polaroid-Rahmen, Partner-Armband/Brelok, Bucket-List-Karte."),
    ("Beauty Box", 51.0, "Beauty", "Kopfhaut-Massager, Mini-Handtuch, Satin-Haargummis, Face Roller."),
    ("Sunday Reset Box", 55.0, "Collections", "Me-time Ritual: Abend → Nacht → Morgen → Wochenende."),
    ("Sakura Box", 46.0, "Blumen Box", "Blumen-Box (keine echten Blumen) — Sakura mit Duftkarte."),
    ("Rose Box", 46.0, "Blumen Box", "Blumen-Box Rose — Duft und Ritualkarten."),
    ("Open When Collection", 43.0, "Open When", "Kleine Umschläge «Open when…»."),
    ("KozyBox Relax", 49.0, "Wellness", "Signature Relax-Box — Wärme, Tee, digitale Playlist."),
    ("RelaxBox", 49.0, "Relax", "Entspannungsbox mit QR-Meditation und Ritual Cards."),
    ("Japan Box", 58.0, "Around the World", "Around-the-Box World — Japan-Stimmung."),
    ("Paris Box", 58.0, "Around the World", "Around-the-Box World — Paris-Stimmung."),
    ("Memory Box — Neuer Lebensabschnitt", 52.0, "Memory", "Unterstützung für einen neuen Lebensabschnitt."),
]


def main() -> int:
    from fastapi import HTTPException

    from app.factory.factory_service import FactoryService
    from app.integration.customer_identity.service import CustomerIdentityService
    from app.integration.factory_intent_service import FactoryIntentService
    from app.integration.finance_service import FinanceService
    from app.integration.owner_notification_service import OwnerNotificationService
    from app.integration.payment_checkout_service import PaymentCheckoutService
    from app.integration.revenue_pipeline_service import RevenuePipelineService
    from app.integration.sales_order_service import SalesOrderService
    from app.integration.store_admin.catalog_service import StoreCatalogService
    from app.integration.store_admin.design_service import StoreDesignService

    # Local launcher: app/memory. Production (OVH): GENESIS_MEMORY_DIR=/data.
    memory_env = (os.environ.get("GENESIS_MEMORY_DIR") or "").strip()
    memory = Path(memory_env) if memory_env else (BACKEND / "app" / "memory")
    memory.mkdir(parents=True, exist_ok=True)

    report: dict = {"brand": BRAND, "email": EMAIL, "memory": str(memory)}

    identity = CustomerIdentityService(memory)
    try:
        sess = identity.register(
            name=NAME,
            email=EMAIL,
            password=PASSWORD,
            locale="de",
            country="DE",
        )
        report["register"] = "created"
    except HTTPException as exc:
        if exc.detail == "email_already_registered":
            sess = identity.login(email=EMAIL, password=PASSWORD)
            report["register"] = "existing_login"
        else:
            raise

    # Session payload does not always include customer_id — resolve via email index.
    from app.integration.customer_identity.store import CustomerIdentityStore

    store = CustomerIdentityStore(memory)
    customer_id = str(store.find_customer_by_email(EMAIL) or "").strip()
    card = store.load_card(customer_id) if customer_id else None
    business_id = str(getattr(card, "business_id", "") or "").strip()
    if not customer_id:
        raise RuntimeError("customer_id_missing_after_register")
    report["customer_id"] = customer_id
    report["business_id"] = business_id

    factory = FactoryService(memory_dir=memory)
    intent = FactoryIntentService(memory_dir=memory, factory=factory)
    sales = SalesOrderService(memory, intent)
    finance = FinanceService(memory)
    notify = OwnerNotificationService(memory)
    checkout = PaymentCheckoutService(memory)
    revenue = RevenuePipelineService(sales, finance, checkout, notify)

    web = sales.create_order(
        {
            "business_name": BRAND,
            "description": (
                "LORENNE — Premium Geschenkboxen für Frauen und Teens. "
                "Kraft tanken, Rituale, Open-when, QR-Playlists."
            ),
            "email": EMAIL,
            "package_id": "premium",
            "city": CITY,
            "niche": "beauty",
            "market_code": "DE",
            "ui_lang": "de",
            "customer_id": customer_id,
            "cinematic_enabled": True,
            "demo": True,
            "brand_style": "cinematic",
            "services_list": [
                "Kraft Tanken Box",
                "Zeit für Dich Box",
                "Movie Night Box",
                "Self Love Box",
            ],
        }
    )
    web_id = str(web["order_id"])
    report["website_order_id"] = web_id
    report["website_price"] = web.get("price_eur")
    report["website_cinematic_price"] = web.get("cinematic_price_eur")
    report["website_paid"] = revenue.complete_demo_payment(web_id).get("ok")

    shop = sales.create_order(
        {
            "business_name": BRAND,
            "description": "LORENNE Online-Shop — Gift Boxes",
            "email": EMAIL,
            "package_id": "ecommerce_shop",
            "city": CITY,
            "market_code": "DE",
            "ui_lang": "de",
            "customer_id": customer_id,
            "demo": True,
            "cinematic_enabled": True,
            "shop_brief": {
                "company_name": BRAND,
                "store_name": BRAND,
                "what_is_sold": "Premium Geschenkboxen",
                "category": "gifts",
                "catalog_size": "21-50",
                "languages": ["de"],
                "currency": "EUR",
                "payments": ["stripe", "invoice"],
                "shipping": ["dhl", "pickup"],
                "pages": [
                    "home",
                    "catalog",
                    "pdp",
                    "about",
                    "contact",
                    "legal",
                    "returns",
                    "cart",
                ],
                "style": "premium",
                "market_code": "DE",
            },
        }
    )
    shop_id = str(shop["order_id"])
    report["shop_order_id"] = shop_id
    report["shop_price"] = shop.get("price_eur")
    report["shop_paid"] = revenue.complete_demo_payment(shop_id).get("ok")

    design = StoreDesignService(memory)
    design.update_design(
        shop_id,
        {
            "tone_id": "deep_lilac",
            "branding": {
                "store_name": BRAND,
                "tagline": "Geschenkboxen mit Seele — Open when you need it.",
            },
        },
        store_name=BRAND,
    )
    report["design_tone"] = "deep_lilac"

    catalog = StoreCatalogService(memory)
    seeded = 0
    for name, price, category, desc in GIFT_BOXES:
        catalog.create_product(
            shop_id,
            {
                "title": name,
                "price": price,
                "category": category,
                "description": desc,
                "stock_qty": 25,
                "stock_status": "in_stock",
                "status": "published",
                "brand": BRAND,
                "currency": "EUR",
            },
        )
        seeded += 1
    report["products_seeded"] = seeded

    public_logo = (
        BACKEND.parent
        / "frontend"
        / "public"
        / "client-brands"
        / "lorenne"
        / "logo.png"
    )
    if LOGO_SRC.is_file():
        public_logo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LOGO_SRC, public_logo)
        report["logo_public"] = "/" + str(
            public_logo.relative_to(BACKEND.parent / "frontend" / "public")
        ).replace("\\", "/")

    # Support Center note
    try:
        from app.integration.customer_identity.support_center import SupportCenterService

        SupportCenterService(memory).add_note(
            customer_id,
            "Erste Client Card — LORENNE Gift Boxes (Premium Website + Online-Shop). "
            "Owner gift for Svitlana. She can add phone/email details later.",
            author="owner",
        )
        report["client_card_note"] = True
    except Exception as exc:  # noqa: BLE001
        report["client_card_note_error"] = str(exc)[:200]

    report["login"] = {
        "email": EMAIL,
        "client_home": "http://127.0.0.1:3000/client",
        "website_admin": f"http://127.0.0.1:3000/client/websites/{web_id}/admin",
        "shop_admin": f"http://127.0.0.1:3000/client/stores/{shop_id}/admin",
        "support_card": "http://127.0.0.1:3000/clients",
    }

    out = BACKEND.parent / ".tmp_lorenne_provision.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
