"""German export orthography — ASCII fallbacks → proper umlauts on client HTML."""

from __future__ import annotations

import re

# Whole-word / phrase fixes for common generator ASCII (market DE).
_DE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("Oelwechsel", "Ölwechsel"),
    ("Oel ", "Öl "),
    (" Oel", " Öl"),
    ("Oel,", "Öl,"),
    ("Oel.", "Öl."),
    (" fuer ", " für "),
    (" Fuer ", " Für "),
    ("fuer ", "für "),
    ("Fuer ", "Für "),
    ("Kueche", "Küche"),
    ("kueche", "küche"),
    ("Ueber", "Über"),
    ("ueber", "über"),
    ("Groesse", "Größe"),
    ("groesse", "größe"),
    ("ssaeure", "säure"),
    ("Strasse", "Straße"),
    ("strasse", "straße"),
    ("Oeffnungs", "Öffnungs"),
    ("oeffnungs", "öffnungs"),
)

_DE_WORD_FIX = re.compile(
    r"\b("
    r"fuer|Fuer|"
    r"Oel|oel|"
    r"Kueche|kueche|"
    r"Ueber|ueber|"
    r"Strasse|strasse|"
    r"Groesse|groesse"
    r")\b"
)

_DE_WORD_MAP = {
    "fuer": "für",
    "Fuer": "Für",
    "Oel": "Öl",
    "oel": "öl",
    "Kueche": "Küche",
    "kueche": "küche",
    "Ueber": "Über",
    "ueber": "über",
    "Strasse": "Straße",
    "strasse": "straße",
    "Groesse": "Größe",
    "groesse": "größe",
}


def polish_de_export_html(html: str, *, market_code: str = "DE") -> str:
    """Apply DE orthography to exported HTML when market is Germany."""
    if (market_code or "").strip().upper() != "DE":
        return html
    if not html:
        return html
    out = html
    for src, dst in _DE_REPLACEMENTS:
        out = out.replace(src, dst)

    def _sub(m: re.Match[str]) -> str:
        return _DE_WORD_MAP.get(m.group(1), m.group(1))

    out = _DE_WORD_FIX.sub(_sub, out)
    return out


def polish_de_export_text(text: str, *, market_code: str = "DE") -> str:
    if (market_code or "").strip().upper() != "DE":
        return text
    if not text:
        return text
    out = text
    for src, dst in _DE_REPLACEMENTS:
        out = out.replace(src, dst)
    return _DE_WORD_FIX.sub(lambda m: _DE_WORD_MAP.get(m.group(1), m.group(1)), out)


GENERIC_DIFFERENTIATOR = "Qualität, Verlässlichkeit, lokale Präsenz"

_NICHE_DIFFERENTIATOR: dict[str, str] = {
    "auto": "Ehrliche Diagnose vor der Rechnung — Meisterwerkstatt mit klarer Kommunikation.",
    "autohaus": "Fahrzeuge mit Transparenz — Beratung, Service und Vertrauen vor dem Kauf.",
    "car_dealership": "Fahrzeuge mit Transparenz — Beratung, Service und Vertrauen vor dem Kauf.",
    "restaurant": "Saisonale Küche, Gastfreundschaft und Reservierung ohne Umwege.",
    "dental": "Vertrauensvolle Zahnmedizin — klare Abläufe und ehrliche Beratung.",
    "law": "Kanzlei mit klarer Einschätzung — strukturiert, verlässlich, menschlich.",
}


def niche_differentiator(niche_id: str, city: str = "") -> str:
    niche = (niche_id or "generic").strip().lower()
    base = _NICHE_DIFFERENTIATOR.get(niche, GENERIC_DIFFERENTIATOR)
    loc = (city or "").strip()
    if loc and niche in ("auto", "restaurant", "dental", "law"):
        return f"{base} · {loc}"
    return base


def resolve_differentiator(
    *,
    niche_id: str,
    city: str = "",
    raw: str = "",
) -> str:
    text = (raw or "").strip()
    if not text or text == GENERIC_DIFFERENTIATOR:
        return niche_differentiator(niche_id, city)
    return polish_de_export_text(text, market_code="DE")
