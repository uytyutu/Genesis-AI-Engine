"""CCI-0 Deterministic Resolver — same input → same Decision."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable

from app.integration.cci.canon import CCI_RULESET, CCI_VERSION
from app.integration.cci.decision import Decision, RejectedCandidate
from app.integration.cci.scoring import (
    MIN_CONFIDENCE_FOR_AUTO,
    MIN_RAW_FOR_AUTO,
    business_domain_from_url,
    normalize_confidence,
    normalize_email,
    score_email,
)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_JUNK_SUFFIXES = ("example.com", "wixpress.com", "sentry.io", "cloudflare.com")


def harvest_emails_from_html(html: str, *, limit: int = 20) -> list[str]:
    found: list[str] = []
    text = html or ""
    for match in _EMAIL_RE.findall(text):
        low = match.lower()
        if any(low.endswith(f"@{s}") or f"@{s}" in low for s in _JUNK_SUFFIXES):
            continue
        if low not in found:
            found.append(low)
    for m in re.findall(r"mailto:([^\s\"'?]+)", text, re.I):
        for em in _EMAIL_RE.findall(m):
            low = em.lower()
            if any(low.endswith(f"@{s}") for s in _JUNK_SUFFIXES):
                continue
            if low not in found:
                found.append(low)
    return found[:limit]


def _trace_id(
    *,
    emails: Iterable[str],
    business_domain: str,
    html: str,
) -> str:
    """Stable id from inputs (not random) — same input → same trace_id."""
    blob = "|".join(sorted(normalize_email(e) for e in emails))
    blob += f"#{business_domain}#{hashlib.sha256((html or '').encode('utf-8')).hexdigest()[:16]}"
    blob += f"#{CCI_VERSION}#{CCI_RULESET}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def resolve_commercial_contact(
    *,
    emails: list[str] | None = None,
    website_url: str | None = None,
    html: str = "",
    company_fit: int | None = None,
) -> Decision:
    """Pick commercial mailbox. Deterministic. Always returns a full Decision."""
    biz = business_domain_from_url(website_url)
    harvested = list(emails or [])
    if html:
        for em in harvest_emails_from_html(html):
            if em not in harvested:
                harvested.append(em)

    # Stable unique order: first appearance, then we re-sort by score for choice
    unique: list[str] = []
    for em in harvested:
        n = normalize_email(em)
        if n and n not in unique:
            unique.append(n)

    trace = _trace_id(emails=unique, business_domain=biz, html=html)

    if not unique:
        return Decision(
            chosen=None,
            decision="HOLD",
            contact_confidence=0,
            company_fit=company_fit,
            reasons_selected=("- No email candidates",),
            rejected=(),
            cci_version=CCI_VERSION,
            ruleset=CCI_RULESET,
            trace_id=trace,
            raw_score=0,
            candidates_scored=(),
        )

    scored = [score_email(em, business_domain=biz, html=html) for em in unique]
    # Deterministic ranking: higher raw_score first, then email lexicographic
    scored.sort(key=lambda s: (-s.raw_score, s.email))

    candidates_audit: list[dict[str, Any]] = [
        {
            "email": s.email,
            "raw_score": s.raw_score,
            "role_score": s.role_score,
            "hard_reject": s.hard_reject,
            "plus": list(s.reasons_plus),
            "minus": list(s.reasons_minus),
        }
        for s in scored
    ]

    best = scored[0]
    rejected: list[RejectedCandidate] = []
    for s in scored[1:]:
        reasons = tuple(list(s.reasons_minus) or (f"- Lower score than {best.email}",))
        if s.hard_reject:
            reasons = tuple(list(s.reasons_minus) + ["- Hard reject role/domain"])
        rejected.append(RejectedCandidate(email=s.email, reasons=reasons))

    conf = normalize_confidence(best.raw_score)
    selected_reasons = tuple(best.reasons_plus)
    if best.reasons_minus and not best.hard_reject:
        # still surface soft minuses on chosen
        selected_reasons = selected_reasons + tuple(best.reasons_minus)

    if best.hard_reject or best.raw_score < MIN_RAW_FOR_AUTO or conf < MIN_CONFIDENCE_FOR_AUTO:
        hold_reasons = list(selected_reasons) if selected_reasons else []
        hold_reasons.append("- Contact confidence below auto_send threshold")
        if best.hard_reject:
            hold_reasons.append("- Best candidate is hard-rejected (support/noreply/vendor)")
        # Best goes to rejected list as well for audit
        rejected.insert(
            0,
            RejectedCandidate(email=best.email, reasons=tuple(best.reasons_minus) or ("- Unsuitable",)),
        )
        return Decision(
            chosen=None,
            decision="HOLD",
            contact_confidence=conf,
            company_fit=company_fit,
            reasons_selected=tuple(hold_reasons) or ("- HOLD: no commercial contact",),
            rejected=tuple(rejected),
            cci_version=CCI_VERSION,
            ruleset=CCI_RULESET,
            trace_id=trace,
            raw_score=best.raw_score,
            candidates_scored=tuple(candidates_audit),
        )

    if not selected_reasons:
        selected_reasons = ("+ Highest commercial score",)

    return Decision(
        chosen=best.email,
        decision="auto_send",
        contact_confidence=conf,
        company_fit=company_fit,
        reasons_selected=selected_reasons,
        rejected=tuple(rejected),
        cci_version=CCI_VERSION,
        ruleset=CCI_RULESET,
        trace_id=trace,
        raw_score=best.raw_score,
        candidates_scored=tuple(candidates_audit),
    )
