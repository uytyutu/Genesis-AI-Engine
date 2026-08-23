"""Honest DE PLZ sample — major cities only (not full national coverage)."""

from __future__ import annotations

# Keep in sync with former runtime_handlers._PLZ_MAP
DE_PLZ_SAMPLE: dict[str, dict[str, str]] = {
    "10115": {"city": "Berlin", "region": "Berlin"},
    "20095": {"city": "Hamburg", "region": "Hamburg"},
    "80331": {"city": "München", "region": "Bayern"},
    "50667": {"city": "Köln", "region": "Nordrhein-Westfalen"},
    "60311": {"city": "Frankfurt am Main", "region": "Hessen"},
    "70173": {"city": "Stuttgart", "region": "Baden-Württemberg"},
    "01067": {"city": "Dresden", "region": "Sachsen"},
    "04109": {"city": "Leipzig", "region": "Sachsen"},
    "30159": {"city": "Hannover", "region": "Niedersachsen"},
    "40213": {"city": "Düsseldorf", "region": "Nordrhein-Westfalen"},
}


def lookup_de_plz(code: str) -> dict[str, str] | None:
    c = (code or "").strip()
    if len(c) == 4:
        c = c.zfill(5)
    row = DE_PLZ_SAMPLE.get(c)
    if not row:
        return None
    return {"postal_code": c, "locality": row["city"], "region": row["region"]}
