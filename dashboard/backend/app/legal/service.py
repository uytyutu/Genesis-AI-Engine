"""Legal & Trust Foundation — orchestration layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.legal.document_generators import generate_document, list_document_catalog
from app.legal.entity_store import LegalEntityStore
from app.legal.handoff import one_time_purchase_handoff, subscription_handoff
from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.legal.trust_catalog import build_trust_catalog

_PUBLIC_CONTACT_EMAIL = "hello@genesis-ai-engine.com"


class LegalFoundationService:
    def __init__(self, memory_dir: Path) -> None:
        self._store = LegalEntityStore(memory_dir)

    def status(self) -> dict[str, Any]:
        return self._store.status()

    def trust(self) -> dict[str, Any]:
        return build_trust_catalog(self._store.load())

    def documents_catalog(self) -> list[dict[str, Any]]:
        return list_document_catalog(self._store.load())

    def document(self, doc_id: str, *, locale: str = "de") -> dict[str, Any] | None:
        doc = generate_document(doc_id, self._store.load(), locale=locale)
        return doc.to_dict() if doc else None

    def handoff_one_time(self) -> dict[str, str]:
        return {"markdown": one_time_purchase_handoff(), "type": "one_time"}

    def handoff_subscription(self) -> dict[str, str]:
        return {"markdown": subscription_handoff(), "type": "subscription"}

    def operator_preview(self) -> dict[str, Any]:
        """Compact seller identity for checkout trust — no secrets."""
        cfg = self._store.load()
        op = cfg.operator
        email = op.email.strip() or _PUBLIC_CONTACT_EMAIL
        address_lines = [
            line
            for line in (
                op.address_street.strip(),
                f"{op.address_zip.strip()} {op.address_city.strip()}".strip(),
            )
            if line
        ]
        if op.address_country.strip() and op.address_country.strip().upper() != "DE":
            address_lines.append(op.address_country.strip())
        return {
            "trade_name": op.trade_name.strip() or BRAND_NAME,
            "full_name": op.full_name.strip(),
            "legal_form": op.legal_form.strip(),
            "email": email,
            "phone": op.phone.strip(),
            "website": op.website.strip(),
            "address_lines": address_lines,
            "vat_id": op.vat_id.strip(),
            "impressum_publishable": cfg.is_impressum_publishable(),
            "datenschutz_publishable": cfg.is_datenschutz_publishable(),
        }
