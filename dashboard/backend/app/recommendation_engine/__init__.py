"""Universal Recommendation Engine — needs → multi-source official offers.

Rules:
- Recommend only after a confirmed need (audit gap), never “we have a link”.
- Official URLs only; no invented commissions.
- Client payload never includes affiliate/commission money.
- Sources are pluggable (Digistore24, partners, Virtus Core later).
"""

from __future__ import annotations

from app.recommendation_engine.engine import (
    build_recommended_solutions,
    public_solutions_only,
)
from app.recommendation_engine.needs import detect_confirmed_needs

__all__ = [
    "build_recommended_solutions",
    "detect_confirmed_needs",
    "public_solutions_only",
]
