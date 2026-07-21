"""Client landing Impressum / Datenschutz templates for Path A (DE).

Not legal advice: fills client-supplied data into honest templates.
Publish-ready only when required fields are present AND the client reviews.
"""

from __future__ import annotations

import html
from dataclasses import asdict, dataclass
from typing import Any


_DISCLAIMER_DE = (
    "Dieser Text wurde aus Ihren Angaben automatisch vorbereitet. "
    "Er ersetzt keine Rechtsberatung. Bitte prüfen und freigeben Sie den Inhalt "
    "vor der Veröffentlichung. Für die Vollständigkeit oder rechtliche Richtigkeit "
    "wird keine Haftung übernommen."
)


@dataclass
class ClientLegalInfo:
    business_name: str = ""
    owner_name: str = ""
    legal_form: str = ""
    street: str = ""
    zip: str = ""
    city: str = ""
    country: str = "DE"
    email: str = ""
    phone: str = ""
    website: str = ""
    managing_director: str = ""
    vat_id: str = ""
    handelsregister: str = ""
    register_court: str = ""
    uses_maps: bool = False
    uses_analytics: bool = False
    uses_contact_form: bool = True

    @classmethod
    def from_order(cls, order: dict[str, Any] | None) -> ClientLegalInfo:
        raw = (order or {}).get("client_legal") if isinstance(order, dict) else None
        if not isinstance(raw, dict):
            raw = {}
        business = str((order or {}).get("business_name") or raw.get("business_name") or "").strip()
        email = str(raw.get("email") or (order or {}).get("email") or "").strip()
        phone = str(raw.get("phone") or (order or {}).get("phone") or "").strip()
        website = str(raw.get("website") or (order or {}).get("company_website") or "").strip()
        return cls(
            business_name=business,
            owner_name=str(raw.get("owner_name") or "").strip(),
            legal_form=str(raw.get("legal_form") or "").strip(),
            street=str(raw.get("street") or "").strip(),
            zip=str(raw.get("zip") or "").strip(),
            city=str(raw.get("city") or (order or {}).get("city") or "").strip(),
            country=str(raw.get("country") or "DE").strip() or "DE",
            email=email,
            phone=phone,
            website=website,
            managing_director=str(raw.get("managing_director") or "").strip(),
            vat_id=str(raw.get("vat_id") or "").strip(),
            handelsregister=str(raw.get("handelsregister") or "").strip(),
            register_court=str(raw.get("register_court") or "").strip(),
            uses_maps=bool(raw.get("uses_maps")),
            uses_analytics=bool(raw.get("uses_analytics")),
            uses_contact_form=bool(raw.get("uses_contact_form", True)),
        )

    def missing_impressum_fields(self) -> list[str]:
        missing: list[str] = []
        if not (self.owner_name or self.business_name):
            missing.append("owner_name")
        if not self.street:
            missing.append("street")
        if not self.zip:
            missing.append("zip")
        if not self.city:
            missing.append("city")
        if not self.email:
            missing.append("email")
        return missing

    def is_impressum_ready(self) -> bool:
        return not self.missing_impressum_fields()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["missing_impressum"] = self.missing_impressum_fields()
        data["impressum_ready"] = self.is_impressum_ready()
        return data


def _esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def _shell_page(*, title: str, body_html: str, accent: str = "#0ea5e9") -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #0f172a; line-height: 1.65;
      max-width: 720px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
    a {{ color: {accent}; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
    h2 {{ font-size: 1.15rem; margin-top: 1.75rem; color: #0369a1; }}
    .muted {{ color: #64748b; font-size: 0.9rem; }}
    .box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.15rem; margin: 1rem 0; white-space: pre-wrap; }}
    .warn {{ background: #fff7ed; border-color: #fed7aa; color: #9a3412; font-size: 0.9rem; }}
    nav {{ margin-bottom: 1.5rem; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <nav><a href="index.html">← Zur Website</a> · <a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></nav>
  <h1>{_esc(title)}</h1>
  {body_html}
</body>
</html>
"""


def build_impressum_html(info: ClientLegalInfo, *, accent: str = "#0ea5e9") -> str:
    missing = info.missing_impressum_fields()
    display_name = info.owner_name or info.business_name or "[Name fehlt]"
    trade = info.business_name or display_name
    lines = [
        display_name,
        trade if trade != display_name else "",
        info.street or "[Straße fehlt]",
        f"{info.zip} {info.city}".strip() or "[PLZ Ort fehlt]",
        info.country,
        "",
        f"E-Mail: {info.email or '[E-Mail fehlt]'}",
    ]
    if info.phone:
        lines.append(f"Telefon: {info.phone}")
    if info.website:
        lines.append(f"Website: {info.website}")
    if info.legal_form:
        lines.append(f"Rechtsform: {info.legal_form}")
    if info.managing_director:
        lines.append(f"Vertretungsberechtigt: {info.managing_director}")
    if info.handelsregister:
        hr = f"Handelsregister: {info.handelsregister}"
        if info.register_court:
            hr += f", Registergericht: {info.register_court}"
        lines.append(hr)
    if info.vat_id:
        lines.append(f"USt-IdNr.: {info.vat_id}")

    block = "\n".join(x for x in lines if x is not None)
    warn = ""
    if missing:
        warn = (
            '<p class="box warn"><strong>Noch nicht publish-ready:</strong> '
            f"fehlende Angaben: {', '.join(missing)}. "
            "Bitte vervollständigen und prüfen, bevor die Seite online geht.</p>"
        )
    body = f"""
  <p class="muted">Angaben gemäß § 5 DDG (Anbieterkennzeichnung) — Vorlage aus Kundendaten.</p>
  {warn}
  <h2>Anbieter</h2>
  <div class="box">{_esc(block)}</div>
  <h2>EU-Streitschlichtung</h2>
  <p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:
  <a href="https://ec.europa.eu/consumers/odr/" rel="noopener">https://ec.europa.eu/consumers/odr/</a></p>
  <h2>Verbraucherstreitbeilegung</h2>
  <p>Wir sind nicht verpflichtet und nicht bereit, an Streitbeilegungsverfahren vor einer
  Verbraucherschlichtungsstelle teilzunehmen.</p>
  <p class="box warn">{_esc(_DISCLAIMER_DE)}</p>
"""
    return _shell_page(title="Impressum", body_html=body, accent=accent)


def build_datenschutz_html(info: ClientLegalInfo, *, accent: str = "#0ea5e9") -> str:
    controller = info.owner_name or info.business_name or "[Verantwortlicher fehlt]"
    contact = info.email or "[E-Mail fehlt]"
    tools: list[str] = []
    if info.uses_contact_form:
        tools.append("Kontaktformular / Termin-Anfrage (Inhalt der Nachricht, Kontaktdaten)")
    if info.uses_maps:
        tools.append("Google Maps / Kartendienst (IP-Adresse kann an den Anbieter übermittelt werden)")
    if info.uses_analytics:
        tools.append("Web-Analyse / Statistik (z. B. Google Analytics — nur falls aktiv eingebunden)")
    if not tools:
        tools.append("Bereitstellung der Website und Kommunikation per E-Mail / Telefon")

    tools_html = "".join(f"<li>{_esc(t)}</li>" for t in tools)
    missing_note = ""
    if not info.is_impressum_ready():
        missing_note = (
            '<p class="box warn">Datenschutz-Vorlage ist vorbereitet, aber Impressum-Daten sind '
            "noch unvollständig — vor Go-live bitte vervollständigen und prüfen.</p>"
        )
    body = f"""
  <p class="muted">Datenschutzerklärung (Vorlage) — angepasst an Ihre Angaben.</p>
  {missing_note}
  <h2>1. Verantwortlicher</h2>
  <div class="box">{_esc(controller)}
E-Mail: {_esc(contact)}
{_esc(info.street)}
{_esc(f"{info.zip} {info.city}".strip())}
{_esc(info.country)}</div>
  <h2>2. Welche Daten wir verarbeiten</h2>
  <ul>{tools_html}</ul>
  <h2>3. Zwecke und Rechtsgrundlagen</h2>
  <p>Verarbeitung zur Anbahnung und Durchführung von Anfragen und Terminen (Art. 6 Abs. 1 lit. b DSGVO)
  sowie — soweit erforderlich — auf Basis berechtigter Interessen an einem sicheren und funktionsfähigen
  Webauftritt (Art. 6 Abs. 1 lit. f DSGVO). Einwilligungen (z. B. optionale Analyse) nur, wenn Sie diese
  gesondert einholen.</p>
  <h2>4. Speicherdauer</h2>
  <p>Anfragen werden nur so lange gespeichert, wie es für die Bearbeitung und gesetzliche Pflichten nötig ist.</p>
  <h2>5. Ihre Rechte</h2>
  <p>Sie haben Rechte auf Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit und Widerspruch
  sowie Beschwerde bei einer Aufsichtsbehörde. Kontakt: {_esc(contact)}.</p>
  <h2>6. Hosting</h2>
  <p>Die Website wird auf einem von Ihnen bzw. Ihrem Dienstleister gewählten Hosting betrieben.
  Bitte ergänzen Sie hier den konkreten Anbieter, sobald er feststeht.</p>
  <p class="box warn">{_esc(_DISCLAIMER_DE)}</p>
"""
    return _shell_page(title="Datenschutzerklärung", body_html=body, accent=accent)


def write_client_legal_pages(
    product_dir: Any,
    info: ClientLegalInfo,
    *,
    accent: str = "#0ea5e9",
    market_code: str | None = None,
) -> dict[str, Any]:
    """Write market-appropriate legal pages (never DE Impressum for US/UK/etc.)."""
    from pathlib import Path

    from app.factory.market_delivery import (
        legal_notice_placeholder,
        market_legal_pack,
        normalize_market,
    )

    root = Path(product_dir)
    root.mkdir(parents=True, exist_ok=True)
    code = normalize_market(market_code or info.country or "DE")
    pack = market_legal_pack(code)
    files: list[str] = []

    # Remove stale DE files when regenerating for another market
    for stale in ("impressum.html", "datenschutz.html", "privacy.html", "terms.html", "LEGAL_NOTICE.txt"):
        p = root / stale
        if p.is_file():
            p.unlink()

    if pack == "de_impressum":
        (root / "impressum.html").write_text(build_impressum_html(info, accent=accent), encoding="utf-8")
        (root / "datenschutz.html").write_text(build_datenschutz_html(info, accent=accent), encoding="utf-8")
        files = ["impressum.html", "datenschutz.html"]
        return {
            "pack": pack,
            "market_code": code,
            "impressum_ready": info.is_impressum_ready(),
            "missing_impressum": info.missing_impressum_fields(),
            "files": files,
        }

    if pack in ("us_privacy", "uk_privacy"):
        (root / "privacy.html").write_text(build_privacy_html_en(info, accent=accent, market=code), encoding="utf-8")
        (root / "terms.html").write_text(build_terms_html_en(info, accent=accent, market=code), encoding="utf-8")
        files = ["privacy.html", "terms.html"]
        return {
            "pack": pack,
            "market_code": code,
            "impressum_ready": False,
            "missing_impressum": [],
            "files": files,
        }

    (root / "LEGAL_NOTICE.txt").write_text(legal_notice_placeholder(code), encoding="utf-8")
    return {
        "pack": "placeholder",
        "market_code": code,
        "impressum_ready": False,
        "missing_impressum": [],
        "files": ["LEGAL_NOTICE.txt"],
        "note": "Legal documents for this market are not yet included.",
    }


def _shell_page_en(*, title: str, body_html: str, accent: str = "#0ea5e9") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #0f172a; line-height: 1.65;
      max-width: 720px; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
    a {{ color: {accent}; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
    h2 {{ font-size: 1.15rem; margin-top: 1.75rem; color: #0369a1; }}
    .muted {{ color: #64748b; font-size: 0.9rem; }}
    .box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.15rem; margin: 1rem 0; white-space: pre-wrap; }}
    .warn {{ background: #fff7ed; border-color: #fed7aa; color: #9a3412; font-size: 0.9rem; }}
    nav {{ margin-bottom: 1.5rem; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <nav><a href="index.html">← Website</a> · <a href="privacy.html">Privacy</a> · <a href="terms.html">Terms</a></nav>
  <h1>{_esc(title)}</h1>
  {body_html}
</body>
</html>
"""


def build_privacy_html_en(info: ClientLegalInfo, *, accent: str = "#0ea5e9", market: str = "US") -> str:
    controller = info.owner_name or info.business_name or "[Business name]"
    contact = info.email or "[email]"
    body = f"""
  <p class="muted">Privacy Policy template for market { _esc(market) } — filled from order data. Not legal advice.</p>
  <p class="box warn">Review with your counsel before go-live. This template is not legal advice.</p>
  <h2>1. Who we are</h2>
  <div class="box">{_esc(controller)}
Email: {_esc(contact)}
{_esc(info.street)}
{_esc(f"{info.zip} {info.city}".strip())}
{_esc(info.country or market)}</div>
  <h2>2. What we collect</h2>
  <p>Contact details you submit via forms or email, and basic technical data needed to operate the site.</p>
  <h2>3. Why we use data</h2>
  <p>To respond to enquiries and run the website. We do not sell personal data.</p>
  <h2>4. Your rights</h2>
  <p>Depending on your location you may have rights to access, correct, or delete personal data. Contact: {_esc(contact)}.</p>
"""
    return _shell_page_en(title="Privacy Policy", body_html=body, accent=accent)


def build_terms_html_en(info: ClientLegalInfo, *, accent: str = "#0ea5e9", market: str = "US") -> str:
    name = info.business_name or info.owner_name or "[Business name]"
    body = f"""
  <p class="muted">Terms of Service template for market {_esc(market)}. Not legal advice.</p>
  <p class="box warn">Replace placeholders and have a lawyer review before publishing.</p>
  <h2>1. Service</h2>
  <p>{_esc(name)} provides the information and contact options on this website.</p>
  <h2>2. No professional advice</h2>
  <p>Content is for general information unless stated otherwise.</p>
  <h2>3. Contact</h2>
  <p>{_esc(info.email or "[email]")}</p>
"""
    return _shell_page_en(title="Terms of Service", body_html=body, accent=accent)
