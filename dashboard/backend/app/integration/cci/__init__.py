"""Commercial Contact Intelligence (CCI) — find who can buy, not any email.

CCI Golden Rule: never optimize send volume; optimize probability of a
commercial dialogue. Same input → same Decision (CCI-0 Deterministic Resolver).

Canon v1.0:
- Decision object is the only return shape (no bare email).
- Auto commercial send MUST go through CCI (no first-email bypass).
"""

from __future__ import annotations

from app.integration.cci.canon import CCI_RULESET, CCI_VERSION, GOLDEN_RULE
from app.integration.cci.decision import Decision, decision_to_dict
from app.integration.cci.resolver import resolve_commercial_contact

__all__ = [
    "CCI_RULESET",
    "CCI_VERSION",
    "GOLDEN_RULE",
    "Decision",
    "decision_to_dict",
    "resolve_commercial_contact",
]
