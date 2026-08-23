"""Creative Identity gate — HTML is last export.

Reality Benchmark FAIL: marketing HTML frozen until Creative Identity
is felt by Owner and Creative Conflict is clean.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


REALITY_BENCHMARK_STATUS = "PENDING_OWNER"
REALITY_BENCHMARK_NOTE = (
    "Commercial review: PENDING_OWNER — eyes over JSON. "
    "Factory invents Business Identity + Visual Brand per company. "
    "Would a stranger believe this company is 5 years old? If no → REBUILD. "
    "HTML export allowed so Owner can judge living sites, not Concept decks."
)

# Allow full marketing HTML so gallery / clients see real sites.
# Owner PASS/FAIL still required (eyes). Env VIRTUS_ALLOW_HTML_EXPORT=0 re-freezes.
SITE_HTML_EXPORT_FROZEN = False

# Back-compat alias
ConceptGateError = type("ConceptGateError", (RuntimeError,), {})


class IdentityGateError(RuntimeError):
    """Raised when marketing HTML is requested without Creative Identity."""


def html_export_unlocked() -> bool:
    env = (os.environ.get("VIRTUS_ALLOW_HTML_EXPORT") or "").strip().lower()
    if env in {"0", "false", "no", "off"}:
        return False
    if env in {"1", "true", "yes", "on"}:
        return True
    return not SITE_HTML_EXPORT_FROZEN


def assert_concept_pack_on_disk(product_dir: Path | None) -> Path:
    """Prefer creative_identity.json; accept legacy concept_pack.json."""
    if product_dir is None:
        raise IdentityGateError("product_dir required for identity gate")
    root = Path(product_dir)
    for name in ("creative_identity.json", "concept_pack.json"):
        path = root / name
        if path.is_file():
            return path
    raise IdentityGateError(
        f"Missing creative_identity.json in {product_dir} — "
        "invent Creative Identity before any HTML export."
    )


def should_export_marketing_html(
    *,
    studio_generation_status: str = "",
    portfolio_test_yes: bool | None = None,
) -> bool:
    """Marketing HTML when unlocked. Env override wins for explicit client-form demos.

    PORTFOLIO TEST: if studio would not put the project in its portfolio → no export.
    """
    if portfolio_test_yes is False:
        return False
    env = (os.environ.get("VIRTUS_ALLOW_HTML_EXPORT") or "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    if not html_export_unlocked():
        return False
    status = (studio_generation_status or "").upper()
    if status in {"FAIL_TEMPLATE", "FAIL", "REBUILD", "CREATIVE_CONFLICT"}:
        return False
    return True


def gate_report(*, html_allowed: bool, reason: str = "") -> dict[str, Any]:
    return {
        "sprint": "Creative Identity Generation",
        "reality_benchmark": REALITY_BENCHMARK_STATUS,
        "reality_note": REALITY_BENCHMARK_NOTE,
        "html_export_allowed": html_allowed,
        "reason": reason
        or (
            REALITY_BENCHMARK_NOTE
            if not html_allowed
            else "HTML export unlocked — Owner PASS still required"
        ),
        "question": "Who is the human — and what idea can you feel?",
        "not_question": "How do we assemble a psychologist website?",
        "benchmark": "€50k creative agency / EU digital studios 2026",
        "naming": "Creative Identity — not Concept",
    }
