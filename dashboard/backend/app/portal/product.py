"""Mission 6.1 — Product Domain (catalog entry).

First Product Platform object. Answers: what products does Virtus Core offer?

```text
Product
  product_id · product_type · display_name · description · availability
```

Independent of Website · WebsiteOwnership · Billing · Licenses.
Does not authenticate · authorize · know Session · HTTP.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

ENGINE_ID = "product_domain_v1"

ProductAvailability = Literal["available", "coming_soon", "unavailable"]

# Stable type codes — catalog contract must stay extensible without rename.
KNOWN_PRODUCT_TYPES: frozenset[str] = frozenset(
    {
        "website",
        "chatbot",
        "crm",
        "analytics",
        "automation",
    }
)


@dataclass(frozen=True)
class Product:
    """One independently purchasable Virtus Core product (catalog row)."""

    product_id: str
    product_type: str
    display_name: str
    description: str
    availability: ProductAvailability

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_product_catalog() -> tuple[Product, ...]:
    """Static seed catalog — replaceable via Store without changing API."""
    return (
        Product(
            product_id="prod_website",
            product_type="website",
            display_name="Landing Website",
            description="One-time landing packages: Basic 350 € · Business 650 € · Premium 1200 €.",
            availability="available",
        ),
        Product(
            product_id="prod_chatbot",
            product_type="chatbot",
            display_name="AI Business Employee (Vector)",
            description="Vector for customer conversations. Activate today; paid monthly plans Coming Soon.",
            availability="available",
        ),
        Product(
            product_id="prod_crm",
            product_type="crm",
            display_name="CRM",
            description="CRM Starter 29 € · Business 79 € · Pro 149 € / mo — Coming Soon.",
            availability="coming_soon",
        ),
        Product(
            product_id="prod_analytics",
            product_type="analytics",
            display_name="Analytics",
            description="Website analytics overview.",
            availability="coming_soon",
        ),
        Product(
            product_id="prod_automation",
            product_type="automation",
            display_name="Automation",
            description="Automation Starter 49 € · Business 99 € / mo — Coming Soon.",
            availability="coming_soon",
        ),
    )
