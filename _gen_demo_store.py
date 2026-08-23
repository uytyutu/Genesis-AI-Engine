"""One-shot: regenerate public/demo-store for CEO visual check."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "dashboard" / "backend"))

from app.factory.store_factory.composer import write_storefront  # noqa: E402
from app.factory.store_factory.templates import StoreTemplateRegistry  # noqa: E402
from app.integration.shop_brief import validate_shop_brief  # noqa: E402


def main() -> None:
    out = ROOT / "dashboard" / "frontend" / "public" / "demo-store"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    brief = validate_shop_brief(
        {
            "company_name": "Nordlicht GmbH",
            "store_name": "Nordlicht Boots",
            "what_is_sold": "Outdoor boots and bags for Germany",
            "category": "clothing",
            "catalog_size": "100",
            "languages": ["de"],
            "currency": "EUR",
            "payments": ["stripe"],
            "shipping": ["dhl"],
            "pages": ["home", "catalog", "pdp", "about", "contact", "legal", "returns"],
            "style": "warm",
        }
    )
    brief["market_code"] = "DE"
    resolved = StoreTemplateRegistry().resolve(brief)
    written = write_storefront(out, brief=brief, resolved=resolved)
    index = (out / "index.html").read_text(encoding="utf-8")
    print(f"written={len(written)} dir={out}")
    print(f"neuheiten={'Neuheiten' in index}")
    print(f"reviews={'id=\"reviews\"' in index}")
    print(f"warenkorb={'Warenkorb' in index or 'Warenkorb' in (out / 'cart.html').read_text(encoding='utf-8')}")


if __name__ == "__main__":
    main()
