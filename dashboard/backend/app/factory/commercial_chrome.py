"""Commercial chrome for Strategy sites — DE trust actions, not decoration.

Owner FAIL without:
  - Call / WhatsApp
  - Callback form (Nummer hinterlassen — wir melden uns)
  - Real social SVG icons (not letter placeholders)
  - Impressum + Datenschutz links
"""

from __future__ import annotations

import html as html_lib
import re
from typing import Any


def _esc(s: str) -> str:
    return html_lib.escape(str(s or ""), quote=True)


def _tel_href(phone: str) -> str:
    raw = (phone or "").strip()
    if not raw:
        return "#cc-contact"
    cleaned = re.sub(r"[^\d+]", "", raw)
    if not cleaned or cleaned == "+":
        return "#cc-contact"
    return f"tel:{cleaned}"


def _wa_digits(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone or "")
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = "49" + digits.lstrip("0")
    return digits


# Real brand SVGs (simple path icons) — not letter placeholders
_SOCIAL_SVGS: dict[str, str] = {
    "instagram": (
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" '
        'stroke="currentColor" stroke-width="1.7">'
        '<rect x="3" y="3" width="18" height="18" rx="5"/>'
        '<circle cx="12" cy="12" r="4"/>'
        '<circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/>'
        "</svg>"
    ),
    "facebook": (
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
        '<path d="M14 9h3V6h-3c-1.7 0-3 1.3-3 3v2H9v3h2v7h3v-7h2.5l.5-3H14V9z"/>'
        "</svg>"
    ),
    "linkedin": (
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
        '<path d="M6.5 9.5H4V20h2.5V9.5zM5.2 4A1.6 1.6 0 1 0 5.2 7.2 1.6 1.6 0 0 0 5.2 4z'
        'M20 20h-2.5v-5.2c0-1.5-.6-2.4-1.9-2.4-1 0-1.5.7-1.8 1.3-.1.2-.1.6-.1.9V20H11.2s.05-9.3 0-10.3H13.7'
        'v1.5c.4-.6 1.1-1.7 2.8-1.7 2 0 3.5 1.3 3.5 4.2V20z"/>'
        "</svg>"
    ),
    "youtube": (
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
        '<path d="M23 12.2s0-3.4-.4-5c-.2-1-1-1.8-2-2C18.8 4.8 12 4.8 12 4.8s-6.8 0-8.6.4'
        'c-1 .2-1.8 1-2 2C1 8.8 1 12.2 1 12.2s0 3.4.4 5c.2 1 1 1.8 2 2 1.8.4 8.6.4 8.6.4s6.8 0 8.6-.4'
        'c1-.2 1.8-1 2-2 .4-1.6.4-5 .4-5zM9.8 15.5v-6.6l5.8 3.3-5.8 3.3z"/>'
        "</svg>"
    ),
    "x": (
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
        '<path d="M18.2 3H21l-6.6 7.5L22 21h-6.2l-4.3-5.6L6 21H3.2l7-8L2 3h6.3l3.9 5.2L18.2 3zm-1.1 16.2h1.7'
        'L7 4.7H5.2l11.9 14.5z"/>'
        "</svg>"
    ),
    "whatsapp": (
        '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="currentColor">'
        '<path d="M12 2a9.9 9.9 0 0 0-8.5 14.9L2 22l5.3-1.4A9.9 9.9 0 1 0 12 2zm0 18a8 8 0 0 1-4.1-1.1'
        'l-.3-.2-3.1.8.8-3-.2-.3A8 8 0 1 1 12 20zm4.4-5.9c-.2-.1-1.4-.7-1.6-.8-.2-.1-.4-.1-.5.1-.2.2-.6.8'
        '-.7.9-.1.2-.3.2-.5.1-.2-.1-1-.4-1.9-1.2-.7-.6-1.2-1.4-1.3-1.6-.1-.2 0-.4.1-.5l.4-.4c.1-.1.2-.3'
        '.3-.4.1-.2.1-.3 0-.5-.1-.1-.5-1.3-.7-1.8-.2-.5-.4-.4-.5-.4h-.4c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 1.9'
        's.8 2.2.9 2.3c.1.2 1.6 2.4 3.8 3.4 2.2.9 2.2.6 2.6.6.4 0 1.3-.5 1.5-1 .2-.5.2-.9.1-1z"/>'
        "</svg>"
    ),
}


def _detect_network(href: str, index: int) -> str:
    h = (href or "").lower()
    if "instagram" in h:
        return "instagram"
    if "facebook" in h or "fb.com" in h:
        return "facebook"
    if "linkedin" in h:
        return "linkedin"
    if "youtube" in h or "youtu.be" in h:
        return "youtube"
    if "twitter" in h or "x.com" in h:
        return "x"
    if "wa.me" in h or "whatsapp" in h:
        return "whatsapp"
    order = ("instagram", "facebook", "linkedin", "youtube", "x")
    return order[index] if index < len(order) else "instagram"


def _label_for(net: str) -> str:
    return {
        "instagram": "Instagram",
        "facebook": "Facebook",
        "linkedin": "LinkedIn",
        "youtube": "YouTube",
        "x": "X",
        "whatsapp": "WhatsApp",
    }.get(net, "Social")


def social_icons_html(
    social: list[str] | tuple[str, ...] | None,
    *,
    business_name: str = "",
    class_name: str = "cc-social",
) -> str:
    """Build real SVG social links. Used in chrome AND topbar — not nav-only."""
    social_links = list(social or ())
    if not social_links:
        slug = re.sub(r"[^a-z0-9]+", "", (business_name or "demo").lower())[:24] or "demo"
        social_links = [
            f"https://instagram.com/{slug}.demo",
            f"https://facebook.com/{slug}.demo",
            f"https://linkedin.com/company/{slug}-demo",
        ]
    icons: list[str] = []
    for i, href in enumerate(social_links[:5]):
        net = _detect_network(href, i)
        label = _label_for(net)
        svg = _SOCIAL_SVGS.get(net) or _SOCIAL_SVGS["instagram"]
        icons.append(
            f'<a class="{_esc(class_name)}" href="{_esc(href)}" target="_blank" '
            f'rel="noopener" aria-label="{_esc(label)}" title="{_esc(label)}">{svg}</a>'
        )
    return "".join(icons)


def build_commercial_chrome(
    *,
    business_name: str,
    phone: str,
    email: str,
    city: str = "",
    ui: dict[str, str] | None = None,
    social: list[str] | tuple[str, ...] | None = None,
    anchor: str = "cc-contact",
) -> tuple[str, str]:
    """Return (html, css) — inject before footer on Strategy documents."""
    ui = ui or {}
    phone = (phone or "").strip()
    email = (email or "").strip()
    name = (business_name or "Unternehmen").strip()
    tel_href = _tel_href(phone)
    wa = _wa_digits(phone)
    wa_href = f"https://wa.me/{wa}" if wa else "#cc-contact"

    social_html = social_icons_html(social, business_name=name)

    form_name = ui.get("form_name") or "Name"
    form_phone = ui.get("form_phone") or "Telefonnummer"
    form_msg = ui.get("form_message") or "Ihr Anliegen (optional)"
    form_ph_name = ui.get("form_name_ph") or "Ihr Name"
    form_ph_phone = ui.get("form_phone_ph") or "+49 …"
    subject = "Rückruf anfordern"
    action = f"mailto:{_esc(email)}?subject={_esc(subject)}" if email else "#cc-contact"

    html = f"""
<section class="cc-chrome" id="{_esc(anchor)}" data-commercial-chrome="1" aria-label="Kontakt">
  <div class="cc-wrap">
    <div class="cc-actions" role="group" aria-label="Sofort kontaktieren">
      <a class="cc-btn cc-call" href="{_esc(tel_href)}">Anrufen</a>
      <a class="cc-btn cc-wa" href="{_esc(wa_href)}" target="_blank" rel="noopener">WhatsApp</a>
      <a class="cc-btn cc-ghost" href="#cc-callback">Rückruf</a>
    </div>

    <div class="cc-grid">
      <div class="cc-copy">
        <p class="cc-kicker">{_esc(city or "Deutschland")} · Kontakt</p>
        <h2>Nummer hinterlassen — wir melden uns</h2>
        <p class="cc-lead">
          Kein Formular-Labyrinth. Name, Telefon — und wir rufen zurück.
        </p>
        <ul class="cc-facts">
          <li><a href="{_esc(tel_href)}">{_esc(phone or "Telefon folgt")}</a></li>
          <li><a href="mailto:{_esc(email)}">{_esc(email or "E-Mail folgt")}</a></li>
          <li>{_esc(name)}</li>
        </ul>
        <div class="cc-socials" aria-label="Social Media">{social_html}</div>
      </div>

      <form class="cc-form contact-form" id="cc-callback" action="{action}" method="get">
        <label>{_esc(form_name)}
          <input name="name" required autocomplete="name" placeholder="{_esc(form_ph_name)}">
        </label>
        <label>{_esc(form_phone)}
          <input name="phone" type="tel" required autocomplete="tel"
            placeholder="{_esc(form_ph_phone)}">
        </label>
        <label>{_esc(form_msg)}
          <textarea name="body" rows="3" placeholder="Kurz Ihr Anliegen…"></textarea>
        </label>
        <button type="submit">Rückruf anfordern</button>
        <p class="cc-note">Mit dem Absenden stimmen Sie der Kontaktaufnahme zu.
          <a href="datenschutz.html">Datenschutz</a></p>
      </form>
    </div>

    <nav class="cc-legal" aria-label="Rechtliches">
      <a href="impressum.html">Impressum</a>
      <a href="datenschutz.html">Datenschutz</a>
      <a href="impressum.html#haftung">Haftung</a>
      <span>DE · DSGVO</span>
    </nav>
  </div>
</section>
"""

    css = """
/* Commercial chrome — mandatory for Strategy Premium (Owner bar) */
.cc-chrome {
  background: #0f1410;
  color: #f4f1ea;
  padding: clamp(2.5rem, 6vw, 4.5rem) clamp(1.25rem, 4vw, 2.5rem);
  border-top: 1px solid rgba(255,255,255,.08);
}
.cc-wrap { max-width: 1080px; margin: 0 auto; }
.cc-actions {
  display: flex; flex-wrap: wrap; gap: .65rem;
  margin-bottom: 1.75rem;
}
.cc-btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: .75rem 1.2rem; text-decoration: none; font-weight: 650;
  border-radius: 2px; border: 1px solid transparent;
}
.cc-call { background: #f4f1ea; color: #111; }
.cc-wa { background: #25d366; color: #06240f; }
.cc-ghost {
  background: transparent; color: #f4f1ea;
  border-color: rgba(244,241,234,.35);
}
.cc-grid {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: clamp(1.5rem, 4vw, 2.75rem);
  align-items: start;
}
.cc-kicker {
  margin: 0 0 .5rem; font-size: .72rem;
  letter-spacing: .14em; text-transform: uppercase; opacity: .55;
}
.cc-copy h2 {
  margin: 0 0 .75rem;
  font-size: clamp(1.45rem, 3vw, 2rem);
  line-height: 1.15; font-weight: 600; max-width: 16ch;
}
.cc-lead { margin: 0 0 1rem; opacity: .82; max-width: 36ch; line-height: 1.55; }
.cc-facts {
  list-style: none; margin: 0 0 1.25rem; padding: 0;
  display: grid; gap: .35rem;
}
.cc-facts a { color: #f4f1ea; }
.cc-socials { display: flex; flex-wrap: wrap; gap: .5rem; }
.cc-social {
  width: 2.4rem; height: 2.4rem; border-radius: 999px;
  border: 1px solid rgba(244,241,234,.28);
  display: inline-flex; align-items: center; justify-content: center;
  color: #f4f1ea; text-decoration: none;
}
.cc-social svg { display: block; }
.cc-social:hover { background: rgba(255,255,255,.08); }
.topbar-socials {
  display: inline-flex; align-items: center; gap: .35rem;
  margin-right: .65rem; vertical-align: middle;
}
.topbar-social {
  width: 1.85rem; height: 1.85rem; border-radius: 999px;
  border: 1px solid rgba(0,0,0,.14);
  display: inline-flex; align-items: center; justify-content: center;
  color: inherit; text-decoration: none; opacity: .85;
}
.topbar-social:hover { opacity: 1; background: rgba(0,0,0,.05); }
.topbar-social svg { width: 14px; height: 14px; }
.cc-form {
  display: grid; gap: .75rem;
  padding: 1.15rem 1.2rem 1.25rem;
  background: #171c18;
  border: 1px solid rgba(255,255,255,.1);
}
.cc-form label {
  display: grid; gap: .35rem; font-size: .88rem; opacity: .92;
}
.cc-form input, .cc-form textarea {
  width: 100%; box-sizing: border-box;
  padding: .7rem .75rem; border: 1px solid rgba(255,255,255,.16);
  background: #0f1410; color: #f4f1ea; border-radius: 2px;
  font: inherit;
}
.cc-form button {
  margin-top: .25rem; padding: .8rem 1rem;
  background: #f4f1ea; color: #111; border: 0;
  font-weight: 700; cursor: pointer; border-radius: 2px;
}
.cc-note { margin: 0; font-size: .75rem; opacity: .55; line-height: 1.45; }
.cc-note a { color: #c9d6de; }
.cc-legal {
  display: flex; flex-wrap: wrap; gap: .85rem 1.25rem;
  margin-top: 2rem; padding-top: 1.15rem;
  border-top: 1px solid rgba(255,255,255,.1);
  font-size: .82rem;
}
.cc-legal a { color: #c9d6de; text-decoration: underline; text-underline-offset: .15em; }
.cc-legal span { opacity: .45; }
@media (max-width: 800px) {
  .cc-grid { grid-template-columns: 1fr; }
  .topbar-socials { display: none; }
}
/* Sticky call strip — mobile first trust */
.cc-sticky {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 40;
  display: none; gap: .5rem; padding: .55rem .75rem;
  background: rgba(15,20,16,.94); backdrop-filter: blur(8px);
  border-top: 1px solid rgba(255,255,255,.12);
}
.cc-sticky a {
  flex: 1; text-align: center; padding: .7rem .5rem;
  text-decoration: none; font-weight: 700; border-radius: 2px;
}
.cc-sticky .cc-call { background: #f4f1ea; color: #111; }
.cc-sticky .cc-wa { background: #25d366; color: #06240f; }
@media (max-width: 800px) {
  .cc-sticky { display: flex; }
  body { padding-bottom: 4.2rem; }
}
"""
    sticky = f"""
<div class="cc-sticky" aria-label="Schnellkontakt">
  <a class="cc-call" href="{_esc(tel_href)}">Anrufen</a>
  <a class="cc-wa" href="{_esc(wa_href)}" target="_blank" rel="noopener">WhatsApp</a>
</div>
"""
    return html + sticky, css


def social_from_contacts(contacts: dict[str, Any] | None) -> list[str]:
    c = contacts if isinstance(contacts, dict) else {}
    fab = c.get("fabricated_company") if isinstance(c.get("fabricated_company"), dict) else {}
    raw = fab.get("social") or c.get("social") or ()
    if isinstance(raw, str):
        return [raw]
    out = []
    for item in raw:
        s = str(item).strip()
        if not s:
            continue
        if s.startswith("http"):
            out.append(s)
        else:
            out.append("https://" + s.lstrip("/"))
    return out


__all__ = [
    "build_commercial_chrome",
    "social_from_contacts",
    "social_icons_html",
]
