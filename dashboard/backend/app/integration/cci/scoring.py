"""Deterministic mathematical contact scoring (no LLM)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

# --- Weights (frozen with CCI_RULESET 2026-07) ---

ROLE_EXACT: dict[str, int] = {
    "geschaeftsfuehrung": 95,
    "geschaeftsleitung": 95,
    "geschaeftsfuehrer": 95,
    "ceo": 95,
    "founder": 95,
    "inhaber": 95,
    "owner": 95,
    "managingdirector": 95,
    "managing-director": 95,
    "director": 88,
    "headofsales": 90,
    "sales": 90,
    "vertrieb": 90,
    "business": 88,
    "angebot": 88,
    "bd": 85,
    "kontakt": 80,
    "contact": 80,
    "anfrage": 80,
    "hello": 78,
    "info": 70,
    "office": 60,
    "buero": 60,
    "reception": 55,
    "support": -100,
    "help": -100,
    "ticket": -100,
    "servicedesk": -100,
    "itsupport": -100,
    "hilfe": -100,
    "noreply": -1000,
    "no-reply": -1000,
    "donotreply": -1000,
    "mailer-daemon": -1000,
    "postmaster": -1000,
    "abuse": -1000,
    "webmaster": -80,
    "admin": -60,
    "hostmaster": -80,
}

NAMED_PERSON_SCORE = 100
UNKNOWN_LOCAL_SCORE = 40

SAME_DOMAIN_BONUS = 25
CROSS_DOMAIN_PENALTY = -80
AGENCY_DOMAIN_PENALTY = -120

PAGE_IMPRESSUM_BONUS = 20
PAGE_KONTAKT_BONUS = 18
PAGE_HOMEPAGE_BONUS = 5
PAGE_FOOTER_AGENCY_PENALTY = -40

# Auto-send only if score and normalized confidence clear these floors.
MIN_RAW_FOR_AUTO = 50
MIN_CONFIDENCE_FOR_AUTO = 55

_AGENCY_HINTS = (
    "website by",
    "webdesign by",
    "made by",
    "erstellt von",
    "webseite von",
)

_TICKET_VENDOR_HINTS = (
    "zendesk",
    "freshdesk",
    "hypernode",
    "servicenow",
    "helpscout",
    "intercom",
    "osticket",
    "jira",
    "atlassian",
)


@dataclass(frozen=True)
class ScoredEmail:
    email: str
    raw_score: int
    role_score: int
    reasons_plus: tuple[str, ...]
    reasons_minus: tuple[str, ...]
    hard_reject: bool


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def business_domain_from_url(website_url: str | None) -> str:
    raw = (website_url or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        host = urlparse(raw).netloc.lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host.split(":")[0]


def email_domain(email: str) -> str:
    parts = normalize_email(email).split("@")
    return parts[-1] if len(parts) == 2 else ""


def local_part(email: str) -> str:
    parts = normalize_email(email).split("@")
    return parts[0] if parts else ""


def _is_named_person(local: str) -> bool:
    if local in ROLE_EXACT:
        return False
    # max.mustermann / max-mustermann — not noreply-style
    if re.fullmatch(r"[a-z]{2,}[._-][a-z]{2,}", local):
        return True
    return False


def _role_score(local: str) -> tuple[int, str]:
    key = local.replace("_", "").replace(".", "")
    # try exact local first
    if local in ROLE_EXACT:
        return ROLE_EXACT[local], local
    compact = local.replace("-", "").replace(".", "").replace("_", "")
    for role, score in ROLE_EXACT.items():
        role_c = role.replace("-", "")
        if compact == role_c or local == role:
            return score, role
    if _is_named_person(local):
        return NAMED_PERSON_SCORE, "named_person"
    return UNKNOWN_LOCAL_SCORE, "unknown"


def _page_context(email: str, html: str) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """Lightweight page authority from HTML surrounding the address (CCI-1)."""
    if not html:
        return PAGE_HOMEPAGE_BONUS, ("+ Homepage context",), ()
    low = html.lower()
    em = normalize_email(email)
    idx = low.find(em)
    if idx < 0:
        # mailto without full email in body
        local = local_part(em)
        idx = low.find(f"mailto:{em}")
        if idx < 0 and local:
            idx = low.find(local)
    plus: list[str] = []
    minus: list[str] = []
    bonus = PAGE_HOMEPAGE_BONUS
    plus.append("+ Homepage")

    window = ""
    if idx >= 0:
        start = max(0, idx - 400)
        end = min(len(low), idx + len(em) + 400)
        window = low[start:end]

    if "impressum" in window or 'rel="impressum"' in low and em in low:
        # Prefer impressum section if email appears near the word or page has impressum block
        if "impressum" in window:
            bonus = PAGE_IMPRESSUM_BONUS
            plus = ["+ Found in Impressum context"]
    if any(k in window for k in ("kontakt", "contact us", "contact-us", "/contact")):
        if bonus < PAGE_KONTAKT_BONUS:
            bonus = PAGE_KONTAKT_BONUS
            plus = ["+ Found in Kontakt/Contact context"]

    agency_hit = any(h.lower() in window for h in _AGENCY_HINTS)
    if agency_hit and idx >= 0:
        bonus += PAGE_FOOTER_AGENCY_PENALTY
        minus.append("- Agency / website-by footer context")

    return bonus, tuple(plus), tuple(minus)


def score_email(
    email: str,
    *,
    business_domain: str,
    html: str = "",
) -> ScoredEmail:
    em = normalize_email(email)
    local = local_part(em)
    domain = email_domain(em)
    plus: list[str] = []
    minus: list[str] = []

    role_pts, role_label = _role_score(local)
    if role_label == "named_person":
        plus.append("+ Named person mailbox")
    elif role_pts >= 90:
        plus.append(f"+ Decision-maker / sales role ({role_label})")
    elif role_pts >= 70:
        plus.append(f"+ Commercial mailbox ({role_label})")
    elif role_pts >= 40:
        plus.append(f"+ Generic role ({role_label})")
    else:
        minus.append(f"- Non-commercial / technical role ({role_label})")

    raw = role_pts
    hard = role_pts <= -100

    biz = (business_domain or "").lower().removeprefix("www.")
    if biz and domain:
        if domain == biz or domain.endswith("." + biz):
            raw += SAME_DOMAIN_BONUS
            plus.append("+ Same domain as business website")
        else:
            raw += CROSS_DOMAIN_PENALTY
            minus.append("- Email domain != business domain")
            # Ticket / vendor hosts
            if any(v in domain for v in _TICKET_VENDOR_HINTS):
                raw += AGENCY_DOMAIN_PENALTY
                minus.append("- Ticket / vendor host domain")
                hard = True
            elif any(x in domain for x in ("agency", "agentur", "webdesign", "hosting")):
                raw += AGENCY_DOMAIN_PENALTY
                minus.append("- Likely agency / hosting domain")

    page_bonus, page_plus, page_minus = _page_context(em, html)
    raw += page_bonus
    plus.extend(page_plus)
    minus.extend(page_minus)

    if hard or role_pts <= -100:
        hard = True

    return ScoredEmail(
        email=em,
        raw_score=raw,
        role_score=role_pts,
        reasons_plus=tuple(plus),
        reasons_minus=tuple(minus),
        hard_reject=hard,
    )


def normalize_confidence(raw_score: int) -> int:
    """Map raw score to 0..100. Anchors: -1000→0, 0→35, 50→55, 100→78, 145→100."""
    # Piecewise linear, deterministic
    if raw_score <= -100:
        return max(0, min(20, 20 + raw_score // 50))
    if raw_score < 0:
        return max(0, 35 + raw_score // 3)
    # 0..145+ → 35..100
    capped = min(145, raw_score)
    return int(35 + (capped / 145.0) * 65)
