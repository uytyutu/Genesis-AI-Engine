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
        """Compact § 5 DDG footer + UWG opt-out for DE outreach / transactional mail."""
        return self.email_footer_for_market(
            "DE",
            include_opt_out=include_opt_out,
            for_outreach=for_outreach,
            language="de",
        )

    def email_footer_for_market(
        self,
        market: str | None,
        *,
        include_opt_out: bool = True,
        for_outreach: bool = False,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Market-aware sender footer — Impressum only for DE/AT/CH, not for US/CIS."""
        from app.integration.outreach_language_service import normalize_market_code

        cfg = self._store.load()
        op = cfg.operator
        email = op.email.strip() or _PUBLIC_CONTACT_EMAIL
        site = _public_site_base(op.website)
        impressum_url = f"{site}/impressum"
        datenschutz_url = f"{site}/datenschutz"
        privacy_url = f"{site}/privacy"
        publishable = cfg.is_impressum_publishable()
        m = (normalize_market_code(market) or "DE").upper()
        lang = (language or "de").lower()
        if m in ("US", "CA", "GB", "UK", "AU"):
            profile = "us"
        elif m in ("UA", "RU", "BY", "KZ", "CIS"):
            profile = "cis"
        else:
            profile = "de"

        trade = op.trade_name.strip() or BRAND_NAME
        opt_out_mailto = f"mailto:{email}?subject=Unsubscribe"

        if profile == "de":
            lines: list[str] = ["—", "Impressum (§ 5 DDG)"]
            if publishable:
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
            ready = publishable and include_opt_out
        elif profile == "us":
            lines = ["—", "Sender information"]
            if publishable:
                lines.append(op.full_name.strip() or trade)
                if trade and trade != op.full_name.strip():
                    lines.append(trade)
                addr = cfg.formatted_address().replace("\n", ", ")
                if addr:
                    lines.append(addr)
                lines.append(f"Email: {email}")
            else:
                lines.append(BRAND_NAME)
                lines.append(f"Email: {email}")
            lines.append(f"Privacy: {privacy_url}")
            opt_out_mailto = f"mailto:{email}?subject=Unsubscribe"
            if include_opt_out:
                lines.extend(
                    [
                        "",
                        "Unsubscribe: reply «Unsubscribe» or use this link — we will stop marketing emails.",
                        f"Unsubscribe: {opt_out_mailto}",
                    ]
                )
            ready = include_opt_out and bool(email)
        elif lang == "uk":
            lines = ["—", "Дані відправника"]
            lines.append(op.full_name.strip() or trade if publishable else BRAND_NAME)
            lines.append(f"Email: {email}")
            lines.append(f"Конфіденційність: {privacy_url}")
            opt_out_mailto = f"mailto:{email}?subject=Vidmova%20rozsylky"
            if include_opt_out:
                lines.extend(
                    [
                        "",
                        "Відписка: відповідайте «Відписатись» або перейдіть за посиланням — "
                        "маркетингові листи більше не надсилатимемо.",
                        f"Відписатись: {opt_out_mailto}",
                    ]
                )
            ready = include_opt_out and bool(email)
        else:
            lines = ["—", "Данные отправителя"]
            lines.append(op.full_name.strip() or trade if publishable else BRAND_NAME)
            lines.append(f"Email: {email}")
            lines.append(f"Конфиденциальность: {privacy_url}")
            opt_out_mailto = f"mailto:{email}?subject=Otpisatsya"
            if include_opt_out:
                lines.extend(
                    [
                        "",
                        "Отписка: ответьте «Отписаться» или перейдите по ссылке — "
                        "маркетинговые письма больше не отправим.",
                        f"Отписаться: {opt_out_mailto}",
                    ]
                )
            ready = include_opt_out and bool(email)

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

        return {
            "text": text,
            "html": html_block,
            "market": m,
            "profile": profile,
            "impressum_publishable": publishable,
            "ready_for_outreach": bool(ready),
            "opt_out_mailto": opt_out_mailto,
            "list_unsubscribe": f"<{opt_out_mailto}>",
            "impressum_url": impressum_url,
            "datenschutz_url": datenschutz_url,
            "privacy_url": privacy_url,
        }
