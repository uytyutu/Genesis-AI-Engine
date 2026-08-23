"""Public Business ID — safe to share with support (not internal UUID)."""

from __future__ import annotations

import secrets

# Avoid 0/O/1/I ambiguity when reading aloud.
_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def generate_business_id() -> str:
    """Format: VC-8Q4M-L72P"""
    raw = "".join(secrets.choice(_ALPHABET) for _ in range(8))
    return f"VC-{raw[:4]}-{raw[4:]}"


def normalize_business_id(value: str | None) -> str:
    raw = str(value or "").strip().upper().replace(" ", "")
    if not raw:
        return ""
    # Accept VC-XXXX-XXXX or VCXXXXXX
    compact = raw.replace("-", "")
    if compact.startswith("VC") and len(compact) == 10:
        body = compact[2:]
        return f"VC-{body[:4]}-{body[4:]}"
    return raw
