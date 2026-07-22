"""R3.3 — Section-Aware Content Gate (no LLM).

Goal: do not publish illogical / generic copy — not «write prettier text».

Questions:
  Media Gate  → does this image fit the section?
  Content Gate → does this text fit the section and niche?

Checks: Hero · Services · Benefits · Navigation.
Legal Gate: extension point only (R3.4 Market Compliance Layer).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Sequence

from app.factory.analyzer import AnalysisResult

ENGINE_ID = "content_gate_v1"

# Universal filler service titles — fail for niches that have real craft vocabulary.
_GENERIC_SERVICE_TITLES = frozenset(
    {
        "beratung",
        "umsetzung",
        "support",
        "lösungen",
        "losungen",
        "loesungen",
        "core service",
        "follow-up",
        "follow up",
        "angebot anfordern",
        "consultation",  # as lone service title (law uses Erstberatung — OK)
        "solutions",
        "implementation",
    }
)

# Marketing claims forbidden as header/nav labels (Navigation Gate).
_NAV_MARKETING_FORBIDDEN = frozenset(
    {
        "geprüft",
        "geprueft",
        "lokal",
        "zuverlässig",
        "zuverlassig",
        "zuverlässig",
        "premium-marken",
        "premium marken",
        "verified",
        "reliable",
        "local",
        "fiable",
        "vérifié",
        "verifie",
    }
)

# Phrases that must not appear in benefits/trust for a niche (deny lists).
_BENEFIT_DENY: dict[str, frozenset[str]] = {
    "beauty": frozenset(
        {
            "sterile tools",
            "sterile",
            "implant",
            "zahn",
            "dental",
            "kfz",
            "werkstatt",
            "laptop",
            "notebook",
        }
    ),
    "computer": frozenset(
        {"sterile", "maniküre", "manikure", "coloration", "wimpern", "zahn", "rasen"}
    ),
    "green": frozenset({"sterile", "implant", "laptop", "zahnarzt", "maniküre"}),
    "restaurant": frozenset({"sterile tools", "implant", "laptop", "kfz", "zahn"}),
    "auto": frozenset({"sterile tools", "maniküre", "wimpern", "coloration"}),
    "law": frozenset({"sterile tools", "maniküre", "kfz-diagnose", "laptop-reparatur"}),
    "dental": frozenset({"maniküre", "coloration", "kfz", "laptop"}),
    "handwerk": frozenset({"sterile tools", "maniküre", "wimpern", "implantate"}),
}

# Niche-safe replacements when Services Gate fails.
_NICHE_SERVICES: dict[str, list[str]] = {
    "beauty": ["Schnitt & Styling", "Coloration", "Maniküre", "Gesichtsbehandlung"],
    "computer": ["PC-Reparatur", "Notebook-Service", "Datenrettung", "Netzwerk"],
    "green": ["Gartenpflege", "Heckenschnitt", "Rasensanierung", "Saisonpflege"],
    "auto": ["Diagnose", "Inspektion", "Reifen", "Ölwechsel"],
    "law": ["Erstberatung", "Vertragsprüfung", "Vertretung", "Verhandlungen"],
    "dental": ["Prophylaxe", "Füllungen", "Implantate", "Ästhetik"],
    "handwerk": ["Rohbau", "Sanierung", "Ausbau", "Renovierung"],
    "restaurant": ["Mittagstisch", "Abendkarte", "Events", "Takeaway"],
    "energy": ["PV-Planung", "Montage", "Service", "Monitoring"],
    "appliance": ["Reparatur", "Ersatzteile", "Wartung", "Notdienst"],
}

_NICHE_TRUST: dict[str, tuple[str, ...]] = {
    "beauty": ("Premium-Produkte", "Erfahrene Stylisten", "Entspannte Atmosphäre"),
    "computer": ("Schnelle Diagnose", "Ersatzteile vor Ort", "Daten-Schutz"),
    "green": ("Saubere Arbeit", "Termintreue", "Pflanzenkenntnis"),
    "auto": ("Transparente Kosten", "Moderne Diagnose", "Garantie"),
    "law": ("Vertraulich", "Klare Honorare", "Feste Ansprechpartner"),
    "dental": ("Sterile Abläufe", "Moderne Praxis", "Ruhige Betreuung"),
    "handwerk": ("Meisterqualität", "Saubere Baustelle", "Klare Termine"),
    "restaurant": ("Frische Zutaten", "Lokale Gäste", "Klare Allergene"),
    "energy": ("Ertragsfokus", "Saubere Montage", "Nachbetreuung"),
    "appliance": ("Schneller Einsatz", "Originalteile", "Garantie"),
}

_NICHE_BENEFITS: dict[str, tuple[str, ...]] = {
    "beauty": (
        "Online-Termine",
        "Individuelle Beratung",
        "Fair kalkulierte Preise",
    ),
    "computer": (
        "Kostenvoranschlag vor Reparatur",
        "Express-Slots möglich",
        "Abholung & Rückgabe",
    ),
    "green": (
        "Saisonpläne",
        "Saubere Entsorgung",
        "Festpreis nach Begehung",
    ),
    "auto": (
        "Schriftliche Diagnose",
        "Keine versteckten Posten",
        "Ersatzwagen auf Anfrage",
    ),
    "law": (
        "Feste Ansprechpartner",
        "Transparente Honorare",
        "Digitale Dokumente",
    ),
    "dental": (
        "Schmerzarme Behandlung",
        "Klare Kostenpläne",
        "Erinnerung an Kontrollen",
    ),
    "handwerk": (
        "Saubere Baustelle",
        "Termintreue",
        "Dokumentierte Abnahme",
    ),
    "restaurant": (
        "Saisonale Karte",
        "Reservierung mit Bestätigung",
        "Allergen-Kennzeichnung",
    ),
}


@dataclass(frozen=True)
class ContentGateCheck:
    id: str
    section: str
    ok: bool
    detail: str = ""


@dataclass
class ContentGateResult:
    passed: bool
    checks: list[ContentGateCheck] = field(default_factory=list)
    engine_id: str = ENGINE_ID
    repairs: list[str] = field(default_factory=list)

    @property
    def failures(self) -> list[str]:
        return [
            f"{c.section}:{c.id}" + (f" — {c.detail}" if c.detail else "")
            for c in self.checks
            if not c.ok
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "passed": self.passed,
            "failures": self.failures,
            "repairs": list(self.repairs),
            "checks": [asdict(c) for c in self.checks],
        }


class ContentGateError(ValueError):
    def __init__(self, result: ContentGateResult):
        self.result = result
        super().__init__("content_gate_failed: " + "; ".join(result.failures[:8]))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _is_generic_service_title(title: str) -> bool:
    t = _norm(title)
    if t in _GENERIC_SERVICE_TITLES:
        return True
    # Exact short filler
    if t in {"service", "services", "lösung", "losung"}:
        return True
    return False


def _benefit_denied(niche: str, text: str) -> str | None:
    deny = _BENEFIT_DENY.get((niche or "generic").lower(), frozenset())
    n = _norm(text)
    for bad in deny:
        if bad in n:
            return bad
    return None


def nav_label_is_marketing(label: str) -> bool:
    """True if a header link text is a marketing claim, not navigation."""
    raw = (label or "").strip()
    if not raw:
        return False
    # Split compound trust bars
    parts = re.split(r"[·|•/,]+", raw)
    tokens = {_norm(p) for p in parts if p.strip()}
    if tokens & _NAV_MARKETING_FORBIDDEN:
        return True
    n = _norm(raw)
    return any(bad in n for bad in _NAV_MARKETING_FORBIDDEN)


def extract_topbar_labels(html: str) -> list[str]:
    m = re.search(
        r'<div class="topbar-links">(.*?)</div>',
        html or "",
        flags=re.I | re.S,
    )
    if not m:
        return []
    return [re.sub(r"<[^>]+>", "", a).strip() for a in re.findall(r"<a\b[^>]*>(.*?)</a>", m.group(1), flags=re.I | re.S)]


def evaluate_navigation_html(html: str) -> ContentGateCheck:
    labels = extract_topbar_labels(html)
    bad = [lab for lab in labels if nav_label_is_marketing(lab)]
    if bad:
        return ContentGateCheck(
            id="nav_no_marketing",
            section="navigation",
            ok=False,
            detail="forbidden:" + ",".join(bad[:4]),
        )
    return ContentGateCheck(
        id="nav_no_marketing",
        section="navigation",
        ok=True,
        detail=f"links={len(labels)}",
    )


def evaluate_analysis(analysis: AnalysisResult) -> ContentGateResult:
    """Rule checks against AnalysisResult (pre-HTML)."""
    niche = (analysis.niche or "generic").lower()
    checks: list[ContentGateCheck] = []

    # --- Hero ---
    headline = analysis.headline or ""
    subtitle = analysis.subtitle or ""
    cta = analysis.cta_label or ""
    hero_ok = bool(headline.strip() and subtitle.strip() and cta.strip())
    checks.append(
        ContentGateCheck(
            id="hero_fields",
            section="hero",
            ok=hero_ok,
            detail="missing_fields" if not hero_ok else "ok",
        )
    )
    # Generic partner headline or multi-filler voice for known niches = weak
    filler_bits = ("beratung", "umsetzung", "support", "lösungen", "losungen", "loesungen")
    hero_blob = f"{headline} {subtitle} {cta}"
    hero_norm = _norm(hero_blob)
    filler_hits = sum(1 for t in filler_bits if t in hero_norm)
    if niche != "generic" and _norm(headline).endswith("ihr partner vor ort"):
        checks.append(
            ContentGateCheck(
                id="hero_niche_voice",
                section="hero",
                ok=False,
                detail="generic_partner_headline",
            )
        )
    elif niche in _NICHE_SERVICES and filler_hits >= 2:
        checks.append(
            ContentGateCheck(
                id="hero_niche_voice",
                section="hero",
                ok=False,
                detail="generic_filler_voice",
            )
        )
    else:
        checks.append(
            ContentGateCheck(id="hero_niche_voice", section="hero", ok=True, detail="ok")
        )

    # --- Services ---
    services = list(analysis.services or [])
    generic_hits = [s for s in services if _is_generic_service_title(s)]
    # Craft niches: any universal filler title (Beratung/Umsetzung/…) is a FAIL.
    if niche in _NICHE_SERVICES and generic_hits:
        svc_ok = False
        detail = "generic_services:" + ",".join(generic_hits[:4])
    elif niche != "generic" and services and len(generic_hits) >= max(2, len(services) // 2):
        svc_ok = False
        detail = "generic_services:" + ",".join(generic_hits[:4])
    else:
        svc_ok = True
        detail = "ok"
    checks.append(
        ContentGateCheck(id="services_niche", section="services", ok=svc_ok, detail=detail)
    )

    # --- Benefits / trust pills ---
    benefit_fail: list[str] = []
    for b in list(analysis.benefits or ()) + list(analysis.trust_points or ()):
        hit = _benefit_denied(niche, b)
        if hit:
            benefit_fail.append(f"{b}:{hit}")
    checks.append(
        ContentGateCheck(
            id="benefits_niche",
            section="benefits",
            ok=not benefit_fail,
            detail=";".join(benefit_fail[:4]) or "ok",
        )
    )

    passed = all(c.ok for c in checks)
    return ContentGateResult(passed=passed, checks=checks)


def sanitize_analysis(analysis: AnalysisResult) -> tuple[AnalysisResult, list[str]]:
    """Repair failing copy with niche defaults (swap, not LLM)."""
    result = evaluate_analysis(analysis)
    if result.passed:
        return analysis, []

    niche = (analysis.niche or "generic").lower()
    repairs: list[str] = []
    services = list(analysis.services or [])
    benefits = list(analysis.benefits or ())
    trust = list(analysis.trust_points or ())

    if any(c.id == "services_niche" and not c.ok for c in result.checks):
        if niche in _NICHE_SERVICES:
            services = list(_NICHE_SERVICES[niche])
            repairs.append(f"services→{niche}_defaults")

    if any(c.id == "benefits_niche" and not c.ok for c in result.checks):
        if niche in _NICHE_TRUST:
            trust = list(_NICHE_TRUST[niche])
            repairs.append(f"trust→{niche}_defaults")
        if niche in _NICHE_BENEFITS:
            benefits = list(_NICHE_BENEFITS[niche])
            repairs.append(f"benefits→{niche}_defaults")

    # Drop any remaining denied benefit/trust tokens
    def _clean(items: Sequence[str]) -> list[str]:
        out = []
        for it in items:
            if _benefit_denied(niche, it):
                continue
            out.append(it)
        return out

    trust = _clean(trust) or list(_NICHE_TRUST.get(niche, analysis.trust_points))
    benefits = _clean(benefits) or list(_NICHE_BENEFITS.get(niche, analysis.benefits))

    fixed = replace(
        analysis,
        services=services,
        benefits=tuple(benefits),
        trust_points=tuple(trust),
    )
    return fixed, repairs


def legal_gate_stub(*, market_code: str | None = None) -> ContentGateCheck:
    """R3.4 extension point — Market Compliance Layer (not enforced in R3.3).

    Future: market → legal profile → footer links → legal pages
    (Impressum/Datenschutz, Privacy Policy, Mentions légales, …).
    """
    market = (market_code or "DE").strip().upper() or "DE"
    return ContentGateCheck(
        id="legal_profile_hook",
        section="legal",
        ok=True,
        detail=f"deferred_r34:{market}",
    )


def run_content_gate(
    *,
    analysis: AnalysisResult | None = None,
    html: str | None = None,
    market_code: str | None = None,
    auto_repair: bool = False,
) -> tuple[ContentGateResult, AnalysisResult | None]:
    """Run Content Gate. If auto_repair, returns sanitized analysis."""
    working = analysis
    repairs: list[str] = []
    if working is not None and auto_repair:
        working, repairs = sanitize_analysis(working)

    if working is not None:
        result = evaluate_analysis(working)
    else:
        result = ContentGateResult(passed=True, checks=[])

    if html is not None:
        result.checks.append(evaluate_navigation_html(html))

    # Legal Gate hook (PASS stub — Market Compliance enforces in R3.4)
    result.checks.append(legal_gate_stub(market_code=market_code))
    result.passed = all(c.ok for c in result.checks)
    result.repairs = repairs
    return result, working


def assert_content_gate(
    *,
    analysis: AnalysisResult | None = None,
    html: str | None = None,
    market_code: str | None = None,
) -> ContentGateResult:
    result, _ = run_content_gate(
        analysis=analysis, html=html, market_code=market_code, auto_repair=False
    )
    if not result.passed:
        raise ContentGateError(result)
    return result
