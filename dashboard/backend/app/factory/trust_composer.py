"""R2.2d — Trust Composer: niche + market trust blocks from real client data only.

No fabricated reviews, ratings, certificates, partner logos, or statistics.
Missing evidence → skip block or render a neutral structural template.
"""

from __future__ import annotations

import hashlib
import html as html_lib
from dataclasses import dataclass, field
from typing import Any, Callable

TRUST_TEMPLATE_IDS = ("A", "B", "C", "D")

# Market → preferred block order (CEO map).
MARKET_TRUST_ORDER: dict[str, tuple[str, ...]] = {
    "DE": ("credentials", "process", "social", "portfolio", "guarantees"),
    "AT": ("credentials", "social", "process", "portfolio", "guarantees"),
    "ES": ("social", "portfolio", "credentials", "guarantees", "process"),
    "FR": ("portfolio", "credentials", "social", "process", "guarantees"),
    "NL": ("process", "credentials", "social", "portfolio", "guarantees"),
}

# Niche → which trust families matter most (filter + priority boost).
NICHE_TRUST_FOCUS: dict[str, tuple[str, ...]] = {
    "dental": ("credentials", "process", "social", "portfolio"),
    "auto": ("guarantees", "portfolio", "brands", "process", "social"),
    "law": ("credentials", "process", "guarantees", "social"),
    "energy": ("credentials", "guarantees", "process", "social"),
    "beauty": ("portfolio", "credentials", "brands", "social"),
    "green": ("credentials", "process", "portfolio", "guarantees"),
    "generic": ("credentials", "process", "social", "portfolio"),
}

# Hero/comp-compatible trust templates (extend without if-chains in builder).
TRUST_TEMPLATES: dict[str, dict[str, str]] = {
    "A": {"label": "Credentials-first", "lead": "credentials"},
    "B": {"label": "Social-proof-first", "lead": "social"},
    "C": {"label": "Portfolio-first", "lead": "portfolio"},
    "D": {"label": "Process-neutral", "lead": "process"},
}


@dataclass(frozen=True)
class TrustEvidence:
    """Only fields the client (or verified order) actually provided."""

    rating: float | None = None
    review_count: int | None = None
    rating_source: str | None = None
    certificates: tuple[str, ...] = ()
    guarantees: tuple[str, ...] = ()
    memberships: tuple[str, ...] = ()
    brands: tuple[str, ...] = ()
    reviews: tuple[tuple[str, str], ...] = ()  # (quote, cite)
    portfolio_paths: tuple[str, ...] = ()
    commitments: tuple[str, ...] = ()  # soft niche promises (not fake certs)
    has_maps: bool = False
    has_process: bool = False

    @property
    def has_social(self) -> bool:
        return self.rating is not None or bool(self.reviews)

    @property
    def has_credentials(self) -> bool:
        return bool(self.certificates or self.memberships or self.commitments)

    @property
    def has_portfolio(self) -> bool:
        return bool(self.portfolio_paths)

    @property
    def has_guarantees(self) -> bool:
        return bool(self.guarantees)

    @property
    def has_brands(self) -> bool:
        return bool(self.brands)


@dataclass(frozen=True)
class TrustComposition:
    template_id: str
    html: str
    css: str
    blocks_used: tuple[str, ...] = ()


def collect_trust_evidence(
    *,
    client_trust: dict[str, Any] | None,
    commitments: tuple[str, ...] | list[str],
    portfolio_paths: list[str] | tuple[str, ...] | None,
    has_maps: bool,
    has_process: bool,
) -> TrustEvidence:
    """Parse order/contacts trust payload — ignore empty / placeholder values."""
    raw = client_trust if isinstance(client_trust, dict) else {}
    rating = _as_float(raw.get("rating") or raw.get("google_rating"))
    review_count = _as_int(raw.get("review_count") or raw.get("google_reviews"))
    source = _clean_str(raw.get("rating_source") or raw.get("source"))
    if rating is not None and not source:
        source = "Google" if raw.get("google_rating") is not None else None

    certs = _str_tuple(raw.get("certificates") or raw.get("certs"))
    guarantees = _str_tuple(raw.get("guarantees") or raw.get("warranty"))
    memberships = _str_tuple(raw.get("memberships") or raw.get("associations"))
    brands = _str_tuple(raw.get("brands") or raw.get("partners"))
    reviews = _review_tuple(raw.get("reviews"))
    portfolio = tuple(p for p in (portfolio_paths or []) if p)
    commits = tuple(c for c in commitments if _clean_str(c))

    # Fabrication guard: rating without count is OK; count without rating is dropped.
    if review_count is not None and rating is None:
        review_count = None

    return TrustEvidence(
        rating=rating,
        review_count=review_count,
        rating_source=source,
        certificates=certs,
        guarantees=guarantees,
        memberships=memberships,
        brands=brands,
        reviews=reviews,
        portfolio_paths=portfolio,
        commitments=commits,
        has_maps=bool(has_maps),
        has_process=bool(has_process),
    )


def select_trust_template(
    *,
    niche_id: str,
    market_code: str,
    business_name: str,
    package_id: str,
    evidence: TrustEvidence,
) -> str:
    """Deterministic template from evidence + seed (compatible with available data)."""
    pool = _available_templates(evidence)
    niche = (niche_id or "generic").strip().lower()
    market = (market_code or "DE").strip().upper()
    seed = f"{business_name.strip()}|{package_id}|{niche}|{market}|trust"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return pool[int(digest[16:24], 16) % len(pool)]


def compose_trust_section(
    *,
    template_id: str,
    evidence: TrustEvidence,
    niche_id: str,
    market_code: str,
    ui: dict[str, str],
    business_name: str,
    section_class: str,
    process_html: str = "",
) -> TrustComposition:
    tid = template_id if template_id in TRUST_TEMPLATES else "D"
    market = (market_code or "DE").strip().upper()
    niche = (niche_id or "generic").strip().lower()
    order = _resolve_block_order(market, niche, evidence, tid)
    blocks: list[str] = []
    used: list[str] = []
    for kind in order:
        renderer = _BLOCK_RENDERERS.get(kind)
        if not renderer:
            continue
        chunk = renderer(evidence, ui, business_name, section_class, process_html)
        if chunk:
            blocks.append(chunk)
            used.append(kind)
    if not blocks:
        # Neutral empty: no trust section (honest) — return empty html
        return TrustComposition(template_id=tid, html="", css=_trust_css(), blocks_used=())

    esc = html_lib.escape
    title = esc(ui.get("trust_section_title") or ui.get("trust_bar") or "Vertrauen")
    body = "\n".join(blocks)
    html = f"""
  <section class="{section_class} trust-composer" id="trust" data-trust-template="{tid}">
    <h2>{title}</h2>
    <div class="trust-stack">
{body}
    </div>
  </section>
"""
    return TrustComposition(
        template_id=tid,
        html=html,
        css=_trust_css(),
        blocks_used=tuple(used),
    )


def _available_templates(evidence: TrustEvidence) -> tuple[str, ...]:
    pool: list[str] = []
    if evidence.has_credentials:
        pool.append("A")
    if evidence.has_social:
        pool.append("B")
    if evidence.has_portfolio:
        pool.append("C")
    pool.append("D")  # always — process/neutral
    # Dedupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in pool:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return tuple(out)


def _resolve_block_order(
    market: str,
    niche: str,
    evidence: TrustEvidence,
    template_id: str,
) -> list[str]:
    base = list(MARKET_TRUST_ORDER.get(market) or MARKET_TRUST_ORDER["DE"])
    focus = NICHE_TRUST_FOCUS.get(niche) or NICHE_TRUST_FOCUS["generic"]
    # Boost niche focus to front while keeping market relative order among rest
    ordered: list[str] = []
    for k in focus:
        if k not in ordered:
            ordered.append(k)
    for k in base:
        if k not in ordered:
            ordered.append(k)
    # Template lead block first when available
    lead = TRUST_TEMPLATES[template_id]["lead"]
    if lead in ordered:
        ordered.remove(lead)
        ordered.insert(0, lead)
    # brands is niche-only family
    if "brands" not in ordered and evidence.has_brands:
        ordered.insert(1, "brands")
    # Filter to what we can render
    capable = {
        "credentials": evidence.has_credentials,
        "social": evidence.has_social,
        "portfolio": evidence.has_portfolio,
        "guarantees": evidence.has_guarantees,
        "brands": evidence.has_brands,
        "process": evidence.has_process,
    }
    return [k for k in ordered if capable.get(k)]


def _block_credentials(
    evidence: TrustEvidence,
    ui: dict[str, str],
    business: str,
    sec: str,
    process_html: str,
) -> str:
    esc = html_lib.escape
    pills: list[str] = []
    for c in evidence.certificates:
        pills.append(f'<span class="trust-chip trust-chip-cert">{esc(c)}</span>')
    for m in evidence.memberships:
        pills.append(f'<span class="trust-chip trust-chip-member">{esc(m)}</span>')
    for c in evidence.commitments:
        pills.append(f'<span class="trust-chip">{esc(c)}</span>')
    if not pills:
        return ""
    label = esc(ui.get("trust_credentials_title") or ui.get("trust_bar") or "Qualität")
    return f"""
      <div class="trust-block" data-trust-block="credentials">
        <h3>{label}</h3>
        <div class="trust-chip-row">{"".join(pills)}</div>
      </div>
"""


def _block_social(
    evidence: TrustEvidence,
    ui: dict[str, str],
    business: str,
    sec: str,
    process_html: str,
) -> str:
    esc = html_lib.escape
    parts: list[str] = []
    if evidence.rating is not None:
        src = esc(evidence.rating_source or "")
        count = (
            f'<span class="trust-rating-count">{evidence.review_count}</span>'
            if evidence.review_count is not None
            else ""
        )
        src_html = f'<span class="trust-rating-src">{src}</span>' if src else ""
        parts.append(
            f'<div class="trust-rating"><strong>{evidence.rating:g}</strong>'
            f"{count}{src_html}</div>"
        )
    for quote, cite in evidence.reviews[:3]:
        parts.append(
            f'<blockquote class="trust-quote"><p>{esc(quote)}</p>'
            f"<cite>{esc(cite)}</cite></blockquote>"
        )
    if not parts:
        return ""
    label = esc(ui.get("reviews") or "Reviews")
    return f"""
      <div class="trust-block" data-trust-block="social">
        <h3>{label}</h3>
        <div class="trust-social">{"".join(parts)}</div>
      </div>
"""


def _block_portfolio(
    evidence: TrustEvidence,
    ui: dict[str, str],
    business: str,
    sec: str,
    process_html: str,
) -> str:
    esc = html_lib.escape
    if not evidence.portfolio_paths:
        return ""
    figs = "\n".join(
        f'        <figure class="trust-photo"><img src="{esc(p)}" alt="{esc(business)}" loading="lazy"></figure>'
        for p in evidence.portfolio_paths[:6]
    )
    label = esc(ui.get("gallery_title") or ui.get("showcase_title") or "Galerie")
    return f"""
      <div class="trust-block" data-trust-block="portfolio">
        <h3>{label}</h3>
        <div class="trust-portfolio">{figs}
        </div>
      </div>
"""


def _block_guarantees(
    evidence: TrustEvidence,
    ui: dict[str, str],
    business: str,
    sec: str,
    process_html: str,
) -> str:
    esc = html_lib.escape
    if not evidence.guarantees:
        return ""
    items = "".join(f"<li>{esc(g)}</li>" for g in evidence.guarantees)
    label = esc(ui.get("trust_guarantees_title") or "Garantie")
    return f"""
      <div class="trust-block" data-trust-block="guarantees">
        <h3>{label}</h3>
        <ul class="trust-guarantee-list">{items}</ul>
      </div>
"""


def _block_brands(
    evidence: TrustEvidence,
    ui: dict[str, str],
    business: str,
    sec: str,
    process_html: str,
) -> str:
    esc = html_lib.escape
    if not evidence.brands:
        return ""
    pills = "".join(f'<span class="trust-chip trust-chip-brand">{esc(b)}</span>' for b in evidence.brands)
    label = esc(ui.get("trust_brands_title") or "Marken")
    return f"""
      <div class="trust-block" data-trust-block="brands">
        <h3>{label}</h3>
        <div class="trust-chip-row">{pills}</div>
      </div>
"""


def _block_process(
    evidence: TrustEvidence,
    ui: dict[str, str],
    business: str,
    sec: str,
    process_html: str,
) -> str:
    """Reuse existing process markup when present — structural, not fabricated stats."""
    if not evidence.has_process or not process_html.strip():
        return ""
    # Extract inner grid if full section passed; else wrap.
    return f"""
      <div class="trust-block" data-trust-block="process">
{process_html}
      </div>
"""


_BLOCK_RENDERERS: dict[str, Callable[..., str]] = {
    "credentials": _block_credentials,
    "social": _block_social,
    "portfolio": _block_portfolio,
    "guarantees": _block_guarantees,
    "brands": _block_brands,
    "process": _block_process,
}


def _trust_css() -> str:
    return """
    /* Trust Composer R2.2d */
    .trust-composer .trust-stack { display: grid; gap: 2rem; }
    .trust-block h3 { font-size: 1.15rem; margin-bottom: 0.85rem; color: var(--pd); }
    .trust-chip-row { display: flex; flex-wrap: wrap; gap: 0.55rem; }
    .trust-chip {
      border: 1px solid var(--line); background: #fff; border-radius: 999px;
      padding: 0.4rem 0.9rem; font-size: 0.85rem; font-weight: 600; color: var(--pd);
    }
    .trust-chip-cert { border-color: var(--p); }
    .trust-chip-brand { background: var(--surface); }
    .trust-rating {
      display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: baseline;
      margin-bottom: 1rem;
    }
    .trust-rating strong {
      font-size: clamp(1.75rem, 4vw, 2.4rem); color: var(--p); letter-spacing: -0.03em;
    }
    .trust-rating-count, .trust-rating-src { color: var(--muted); font-size: 0.95rem; }
    .trust-social { display: grid; gap: 1rem; }
    .trust-quote {
      margin: 0; padding: 1rem 0 1rem 1rem; border-left: 3px solid var(--acc);
      background: transparent;
    }
    .trust-quote cite { display: block; margin-top: 0.5rem; color: var(--muted); font-size: 0.85rem; }
    .trust-portfolio {
      display: grid; gap: 0.65rem; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    }
    .trust-photo { margin: 0; border-radius: 10px; overflow: hidden; aspect-ratio: 4/3; background: var(--surface); }
    .trust-photo img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .trust-guarantee-list { list-style: none; display: grid; gap: 0.55rem; }
    .trust-guarantee-list li {
      padding-left: 1.35rem; position: relative;
    }
    .trust-guarantee-list li::before {
      content: "✓"; position: absolute; left: 0; color: var(--p); font-weight: 700;
    }
    .trust-block[data-trust-block="process"] .process-grid { margin-top: 0.25rem; }
"""


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in ("n/a", "na", "none", "null", "-", "todo", "tbd"):
        return None
    return s


def _str_tuple(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
        return tuple(p for p in parts if _clean_str(p))
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            c = _clean_str(item)
            if c:
                out.append(c)
        return tuple(out)
    return ()


def _review_tuple(value: Any) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    out: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = _clean_str(item.get("text") or item.get("quote") or item.get("body"))
        cite = _clean_str(item.get("cite") or item.get("author") or item.get("name"))
        if text and cite:
            out.append((text, cite))
    return tuple(out)


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        n = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    if n < 0 or n > 5.5:
        return None
    return n


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(float(str(value)))
    except (TypeError, ValueError):
        return None
    if n < 0 or n > 1_000_000:
        return None
    return n
