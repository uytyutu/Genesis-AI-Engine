"""Legal & Trust Foundation — orchestration layer."""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any

from app.legal.document_generators import generate_document, list_document_catalog
from app.legal.entity_store import LegalEntityStore
from app.legal.handoff import one_time_purchase_handoff, subscription_handoff
from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.legal.trust_catalog import build_trust_catalog

_PUBLIC_CONTACT_EMAIL = "hello@genesis-ai-engine.com"


def _public_site_base(cfg_website: str) -> str:
    return (
        cfg_website.strip()
        or os.getenv("GENESIS_PUBLIC_URL", "").strip()
        or os.getenv("NEXT_PUBLIC_SITE_URL", "").strip()
        or "https://genesis-ai-engine.vercel.app"
    ).rstrip("/")


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

    def email_footer_de(
        self,
        *,
        include_opt_out: bool = True,
        for_outreach: bool = False,
    ) -> dict[str, Any]:
        """Compact § 5 DDG footer + UWG opt-out for CEO Outbox / transactional mail."""
        cfg = self._store.load()
        op = cfg.operator
        email = op.email.strip() or _PUBLIC_CONTACT_EMAIL
        site = _public_site_base(op.website)
        impressum_url = f"{site}/impressum"
        datenschutz_url = f"{site}/datenschutz"
        publishable = cfg.is_impressum_publishable()

        lines: list[str] = ["—", "Impressum (§ 5 DDG)"]
        if publishable:
            trade = op.trade_name.strip() or BRAND_NAME
            lines.append(op.full_name.strip())
            if trade and trade != op.full_name.strip():
                lines.append(trade)
            if op.legal_form.strip():
                lines.append(op.legal_form.strip())
            addr = cfg.formatted_address().replace("\n", ", ")
            if addr:
                lines.append(addr)
            lines.append(f"E-Mail: {email}")
            if op.phone.strip():
                lines.append(f"Telefon: {op.phone.strip()}")
            if op.managing_director.strip():
                lines.append(f"Vertretungsberechtigt: {op.managing_director.strip()}")
            if op.vat_id.strip():
                lines.append(f"USt-IdNr.: {op.vat_id.strip()}")
            if op.handelsregister.strip():
                hr = op.handelsregister.strip()
                if op.register_court.strip():
                    hr += f", Registergericht: {op.register_court.strip()}"
                lines.append(f"Handelsregister: {hr}")
        else:
            missing = ", ".join(cfg.missing_impressum_fields())
            lines.append(
                "Anbieterkennzeichnung unvollständig — Gewerbedaten in Legal Foundation ergänzen "
                f"(fehlend: {missing})."
            )
            lines.append(f"Kontakt: {email}")

        lines.append(f"Impressum online: {impressum_url}")
        lines.append(f"Datenschutz: {datenschutz_url}")

        opt_out_mailto = f"mailto:{email}?subject=Abmelden%20Werbung"
        if include_opt_out:
            lines.extend(
                [
                    "",
                    "Widerspruch gegen Werbe-E-Mails (UWG § 7 Abs. 3):",
                    "Antworten Sie mit «Abmelden» oder nutzen Sie den Abmelde-Link — "
                    "wir senden keine weiteren Werbenachrichten.",
                    f"Abmelden: {opt_out_mailto}",
                ]
            )

        text = "\n".join(lines)
        html_lines = [f"<strong>{html.escape(lines[0])}</strong>"] if lines else []
        for line in lines[1:]:
            if not line:
                html_lines.append("<br>")
            else:
                html_lines.append(html.escape(line))
        html_block = (
            '<hr style="border:none;border-top:1px solid #27272f;margin:28px 0 16px">'
            '<p style="margin:0;font-size:11px;line-height:1.55;color:#71717a">'
            + "<br>".join(html_lines)
            + "</p>"
        )

        ready_for_outreach = publishable and include_opt_out

        return {
            "text": text,
            "html": html_block,
            "impressum_publishable": publishable,
            "ready_for_outreach": ready_for_outreach,
            "opt_out_mailto": opt_out_mailto,
            "list_unsubscribe": f"<{opt_out_mailto}>",
            "impressum_url": impressum_url,
            "datenschutz_url": datenschutz_url,
        }
