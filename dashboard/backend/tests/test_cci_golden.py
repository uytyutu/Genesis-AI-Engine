"""CCI golden tests — same HTML → same Decision forever."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integration.cci import CCI_RULESET, CCI_VERSION, resolve_commercial_contact

GOLDEN_DIR = Path(__file__).resolve().parent / "golden" / "cci"


def _cases() -> list[str]:
    return sorted({p.stem for p in GOLDEN_DIR.glob("*.html")})


@pytest.mark.parametrize("stem", _cases())
def test_cci_golden_case(stem: str) -> None:
    html = (GOLDEN_DIR / f"{stem}.html").read_text(encoding="utf-8")
    expected = json.loads((GOLDEN_DIR / f"{stem}.expected.json").read_text(encoding="utf-8"))
    website = expected["website_url"]

    d1 = resolve_commercial_contact(website_url=website, html=html)
    d2 = resolve_commercial_contact(website_url=website, html=html)

    # CCI-0 deterministic
    assert d1.trace_id == d2.trace_id
    assert d1.chosen == d2.chosen
    assert d1.decision == d2.decision
    assert d1.contact_confidence == d2.contact_confidence
    assert d1.reasons_selected == d2.reasons_selected

    assert d1.cci_version == CCI_VERSION
    assert d1.ruleset == CCI_RULESET
    assert d1.trace_id
    assert d1.reasons_selected  # explainability first

    assert d1.decision == expected["expect_decision"]
    assert d1.chosen == expected["expect_chosen"]

    rejected_emails = {r.email for r in d1.rejected}
    for must in expected.get("must_reject_contains") or []:
        assert must in rejected_emails or (
            d1.decision == "HOLD" and must in html.lower()
        )


def test_cci_never_returns_bare_email_contract() -> None:
    d = resolve_commercial_contact(
        emails=["info@acme.test", "support@acme.test"],
        website_url="https://acme.test",
    )
    assert hasattr(d, "chosen")
    assert hasattr(d, "decision")
    assert hasattr(d, "contact_confidence")
    assert hasattr(d, "company_fit")
    assert hasattr(d, "reasons_selected")
    assert hasattr(d, "rejected")
    assert hasattr(d, "cci_version")
    assert hasattr(d, "ruleset")
    assert hasattr(d, "trace_id")
    assert d.decision in ("auto_send", "HOLD", "never")
