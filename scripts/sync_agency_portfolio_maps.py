"""Inject Google Maps into published agency portfolio artifacts (Automotive + Restaurant).

Factory promises maps on Business tier; commercial-chrome exports dropped #maps.
Reads meta.json + fabricated_company.json — no fake locations.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
SITES = ROOT / "dashboard" / "frontend" / "public" / "package-previews" / "sites"

# Matches PUBLIC_AGENCY_PORTFOLIO artifact_id roots (sites/business/*)
PORTFOLIO_ARTIFACTS: tuple[str, ...] = (
    "business/auto",
    "business/restaurant",
)

CC_CONTACT_MARKER = '<section class="cc-chrome" id="cc-contact"'
MAPS_SECTION_RE = re.compile(
    r'<section[^>]*\bid=["\']maps["\'][^>]*>.*?</section>',
    re.I | re.S,
)
HOURS_RE = re.compile(r"Mo[–-]Fr[^<\n]{8,60}")


def _load_backend_maps_helpers():
    sys.path.insert(0, str(BACKEND))
    from app.factory.package_features import maps_embed_src, maps_route_url

    return maps_embed_src, maps_route_url


def _country_label(code: str) -> str:
    c = (code or "").strip().upper()
    if c in ("DE", "DACH"):
        return "Germany"
    return code.strip() or "Germany"


def _maps_required(meta: dict) -> bool:
    pkg = meta.get("package_delivery") or {}
    legal = meta.get("client_legal") or {}
    return bool(pkg.get("maps")) or bool(legal.get("uses_maps"))


def _read_hours(artifact_dir: Path) -> str:
    fab = artifact_dir / "fabricated_company.json"
    if fab.is_file():
        try:
            data = json.loads(fab.read_text(encoding="utf-8"))
            hours = str(data.get("hours") or "").strip()
            if hours:
                return hours
        except json.JSONDecodeError:
            pass
    index = artifact_dir / "index.html"
    if index.is_file():
        m = HOURS_RE.search(index.read_text(encoding="utf-8"))
        if m:
            return m.group(0).strip()
    return "Mo–Fr 09:00–18:00"


def _build_maps_section(meta: dict, hours: str, maps_embed_src, maps_route_url) -> str:
    legal = meta.get("client_legal") or {}
    business_name = str(
        legal.get("business_name") or meta.get("business_name") or ""
    ).strip()
    city = str(legal.get("city") or "").strip()
    street = str(legal.get("street") or "").strip()
    country = _country_label(str(legal.get("country") or meta.get("market_code") or "DE"))

    embed = maps_embed_src(
        business_name=business_name,
        city=city,
        street=street,
        country=country,
    )
    route = maps_route_url(
        business_name=business_name,
        city=city,
        street=street,
        country=country,
    )
    embed_attr = html.escape(embed, quote=True)
    route_attr = html.escape(route, quote=True)
    hours_esc = html.escape(hours, quote=False)

    return f"""<section class="section maps" id="maps">
    <h2>Standort</h2>
    <p class="muted">So finden Sie uns — Karte anhand Ihrer Firmendaten.</p>
    <div class="maps-frame">
      <iframe title="Karte" src="{embed_attr}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
    <div class="maps-actions">
      <a class="btn-route" href="{route_attr}" target="_blank" rel="noopener">Route planen</a>
      <span class="chip">Parkplätze vor Ort</span>
      <span class="chip"><strong>Öffnungszeiten:</strong> {hours_esc}</span>
    </div>
  </section>"""


def _inject_maps(html: str, section: str) -> str:
    if MAPS_SECTION_RE.search(html):
        return MAPS_SECTION_RE.sub(section, html, count=1)
    if CC_CONTACT_MARKER not in html:
        raise ValueError("cc-contact anchor missing — cannot inject maps")
    return html.replace(f"\n{CC_CONTACT_MARKER}", f"\n{section}\n{CC_CONTACT_MARKER}", 1)


def _verify_maps(html_text: str, embed_hint: str) -> list[str]:
    errors: list[str] = []
    if 'id="maps"' not in html_text and "id='maps'" not in html_text:
        errors.append("missing #maps")
    if "maps-frame" not in html_text:
        errors.append("missing .maps-frame")
    if "<iframe" not in html_text or "maps.google.com/maps" not in html_text:
        errors.append("missing Google Maps iframe")
    if embed_hint and embed_hint not in html_text:
        name_part = embed_hint.split()[0] if embed_hint else ""
        if name_part and name_part not in html_text:
            errors.append(f"embed query mismatch (expected business in src): {embed_hint[:40]}")
    return errors


def sync_artifact(rel: str, maps_embed_src, maps_route_url) -> tuple[bool, str]:
    artifact_dir = SITES / rel
    meta_path = artifact_dir / "meta.json"
    index_path = artifact_dir / "index.html"
    if not meta_path.is_file() or not index_path.is_file():
        return False, f"{rel}: missing meta.json or index.html"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not _maps_required(meta):
        return True, f"{rel}: maps not required — skipped"

    hours = _read_hours(artifact_dir)
    section = _build_maps_section(meta, hours, maps_embed_src, maps_route_url)
    html = index_path.read_text(encoding="utf-8")
    updated = _inject_maps(html, section)

    legal = meta.get("client_legal") or {}
    business_name = str(legal.get("business_name") or meta.get("business_name") or "")
    city = str(legal.get("city") or "")
    embed_hint = f"{business_name} {city}".strip()

    errors = _verify_maps(updated, embed_hint)
    if errors:
        return False, f"{rel}: verify fail — {', '.join(errors)}"

    if updated != html:
        index_path.write_text(updated, encoding="utf-8", newline="\n")
        return True, f"{rel}: maps injected/updated ({business_name}, {city})"
    return True, f"{rel}: maps already OK ({business_name}, {city})"


def main() -> int:
    maps_embed_src, maps_route_url = _load_backend_maps_helpers()
    ok = True
    for rel in PORTFOLIO_ARTIFACTS:
        passed, msg = sync_artifact(rel, maps_embed_src, maps_route_url)
        print(("OK  " if passed else "FAIL") + msg.encode("ascii", "replace").decode("ascii"))
        if not passed:
            ok = False
    if not ok:
        print("\nPortfolio maps sync FAILED", file=sys.stderr)
        return 1
    print("\nPortfolio maps integrity PASS — Automotive + Restaurant")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
