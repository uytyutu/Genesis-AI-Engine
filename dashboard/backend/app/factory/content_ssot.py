"""Content SSOT helpers — geo consistency for Factory website intelligence.

Minimal module so Product Intelligence can audit city consistency without a
parallel company store. Expand later; do not invent a second Business Profile.
"""

from __future__ import annotations

import re
from typing import Any

# Common DE city tokens (lightweight; not a gazetteer product).
_CITY_RE = re.compile(
    r"\b("
    r"Berlin|Hamburg|München|Munich|Köln|Cologne|Frankfurt|Stuttgart|Düsseldorf|"
    r"Dortmund|Essen|Leipzig|Bremen|Dresden|Hannover|Nürnberg|Nuremberg|Duisburg|"
    r"Bochum|Wuppertal|Bielefeld|Bonn|Münster|Karlsruhe|Mannheim|Augsburg|"
    r"Wiesbaden|Gelsenkirchen|Mönchengladbach|Braunschweig|Chemnitz|Kiel|Aachen|"
    r"Halle|Magdeburg|Freiburg|Krefeld|Lübeck|Oberhausen|Erfurt|Rostock|Mainz|"
    r"Kassel|Hagen|Hamm|Saarbrücken|Potsdam|Ludwigshafen|Oldenburg|Osnabrück|"
    r"Leverkusen|Heidelberg|Darmstadt|Regensburg|Würzburg|Ingolstadt|Ulm|Heilbronn|"
    r"Paderborn|Offenbach|Göttingen|Bottrop|Trier|Recklinghausen|Reutlingen|Koblenz"
    r")\b",
    re.IGNORECASE,
)


def cities_mentioned(html: str) -> list[str]:
    found = _CITY_RE.findall(html or "")
    # Preserve first-seen order, case-normalized display from match
    out: list[str] = []
    seen: set[str] = set()
    for c in found:
        key = c.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def audit_geo_consistency(*, html: str, city: str) -> dict[str, Any]:
    """Return IntelCheck-shaped dict for geo consistency vs SSOT city."""
    ssot = (city or "").strip()
    mentioned = cities_mentioned(html or "")
    if not ssot:
        return {
            "id": "geo_consistency",
            "status": "REVIEW_REQUIRED",
            "detail": "no SSOT city provided",
            "found": mentioned[:8],
            "expected": [],
        }
    ssot_key = ssot.casefold()
    foreign = [c for c in mentioned if c.casefold() != ssot_key and ssot_key not in c.casefold()]
    if foreign and ssot_key not in {c.casefold() for c in mentioned}:
        return {
            "id": "geo_consistency",
            "status": "FAIL",
            "detail": f"content cities conflict with SSOT city {ssot}",
            "found": mentioned[:8],
            "expected": [ssot],
        }
    return {
        "id": "geo_consistency",
        "status": "PASS",
        "detail": f"geo aligned with {ssot}",
        "found": mentioned[:8],
        "expected": [ssot],
    }
