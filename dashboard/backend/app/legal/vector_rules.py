"""Vector commerce rules for legal & trust — no service/document imports."""

from __future__ import annotations

from app.legal.handoff import handoff_rules_for_vector
from app.legal.trust_catalog import trust_rules_for_vector


def legal_trust_rules_for_vector() -> str:
    return f"""# Legal & Trust Foundation — {trust_rules_for_vector()}

{handoff_rules_for_vector()}

Dokumente werden aus **legal_entity.json** generiert — nicht aus statischen Vorlagen.
Aktualisierung der Dokumente ohne Produktcode-Änderung: nur Entity-Daten pflegen.
"""
