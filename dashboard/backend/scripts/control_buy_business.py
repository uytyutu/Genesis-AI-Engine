"""Control purchase: Business package → Factory → assert ZIP artefacts."""

from __future__ import annotations

import io
import sys
import tempfile
import zipfile
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.factory.factory_service import FactoryService
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.sales_order_service import SalesOrderService


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="patha_ctrl_"))
    factory = FactoryService(memory_dir=tmp, sandbox_dir=tmp / "sandbox")
    intent = FactoryIntentService(memory_dir=tmp, factory=factory)
    sales = SalesOrderService(tmp, intent)
    created = sales.create_order(
        {
            "business_name": "Autowerkstatt Kontrolle",
            "description": "Kfz-Werkstatt Inspektion Reifen Köln",
            "email": "kontrolle@test.de",
            "phone": "+49 221 555 1212",
            "whatsapp": "+49 171 5551212",
            "city": "Köln",
            "package_id": "business",
            "needs_logo": True,
            "client_legal": {
                "owner_name": "Max Kontrolle",
                "street": "Hauptstr. 12",
                "zip": "50667",
                "city": "Köln",
                "email": "kontrolle@test.de",
                "phone": "+49 221 555 1212",
            },
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    assert order is not None
    order["status"] = "paid"
    sales._save_order(order)
    prod = sales.start_production(order_id)
    product_id = str(prod["product_id"])
    html = (tmp / "sandbox" / product_id / "index.html").read_text(encoding="utf-8")
    checks = {
        "wa.me": "wa.me/" in html,
        "maps_iframe": "maps.google.com" in html and 'id="maps"' in html,
        "testimonials": 'id="testimonials"' in html,
        "logo.png": "logo.png" in html,
        "ld_json": "application/ld+json" in html,
        "og_title": "og:title" in html,
        "no_analytics": "G-XXXXXXXXXX" not in html,
        "no_calculator": 'id="calculator"' not in html,
        "real_phone": "+49 221 555 1212" in html,
        "business_name": "Autowerkstatt Kontrolle" in html,
    }
    zip_bytes, zip_name = factory.build_client_delivery_zip(product_id)
    names = zipfile.ZipFile(io.BytesIO(zip_bytes)).namelist()
    print("ZIP_NAME", zip_name)
    print("TMP", tmp)
    print("PRODUCT", product_id)
    print("ZIP", names)
    for key, ok in checks.items():
        print(f"  {'OK' if ok else 'FAIL'} {key}")
    print("ALL_OK", all(checks.values()))
    for line in html.splitlines():
        if "maps.google.com" in line:
            print("MAPS", line.strip()[:180])
            break
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
