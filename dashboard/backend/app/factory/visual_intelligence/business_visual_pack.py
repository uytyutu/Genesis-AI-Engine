"""Business Visual Pack + Visual Quality Gate (SSOT).

Rule (immutable):
  Business and Premium must not contain empty decorative zones.
  Every major visual slot must be filled with content:
  image, 3D model, video, KPI card, or illustration.

Phase 1 = Business Visual Pack (Hero fill, trust, no placeholders).
Phase 2 = Premium Visual Engine (composers for 3D/video/Lottie/…).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ENGINE_ID = "business_visual_pack_v1"

SSOT_RULE = (
    "Business and Premium must not contain empty decorative zones. "
    "Every major visual slot must be filled with content: "
    "image, 3D model, video, KPI card, or illustration."
)

PackageTier = Literal["basic", "business", "premium"]

# Qualitative value props only — never invent years/counts for client deliverables.
_NICHE_KPI: dict[str, tuple[tuple[str, str], tuple[str, str], tuple[str, str]]] = {
    "law": (("Klar", "Erstberatung"), ("Fest", "Honorare"), ("Diskret", "Mandat")),
    "dental": (("Sanft", "Behandlung"), ("Modern", "Technik"), ("Termin", "schnell")),
    "beauty": (("Frisch", "Look"), ("Hygiene", "First"), ("Beratung", "inkl.")),
    "auto": (("Ehrlich", "Diagnose"), ("Garantie", "Arbeit"), ("Fair", "Preis")),
    "restaurant": (("Frisch", "Küche"), ("Lokal", "Gäste"), ("Reserv.", "einfach")),
    "fitness": (("Stark", "Training"), ("Coaching", "vor Ort"), ("Flexibel", "Zeiten")),
    "handwerk": (("Sauber", "Arbeit"), ("Festpreis", "Angebot"), ("Pünktlich", "Termin")),
    "computer": (("Schnell", "Hilfe"), ("Klar", "SLA"), ("Lokal", "Support")),
    "it": (("Schnell", "Hilfe"), ("Klar", "SLA"), ("Lokal", "Support")),
    "psychology": (("Ruhig", "Raum"), ("Klar", "Honorar"), ("Vertraulich", "Gespräch")),
    "therapy": (("Ruhig", "Raum"), ("Klar", "Honorar"), ("Vertraulich", "Gespräch")),
    "generic": (("Klar", "Angebot"), ("Schnell", "Antwort"), ("Lokal", "Service")),
}


@dataclass
class VisualSlotFinding:
    slot: str
    severity: Literal["fail", "warn"]
    detail: str


@dataclass
class VisualQualityReport:
    ok: bool
    package_id: str
    engine: str = ENGINE_ID
    ssot: str = SSOT_RULE
    findings: list[VisualSlotFinding] = field(default_factory=list)
    score: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "package_id": self.package_id,
            "engine": self.engine,
            "ssot": self.ssot,
            "score": self.score,
            "findings": [
                {"slot": f.slot, "severity": f.severity, "detail": f.detail}
                for f in self.findings
            ],
        }


def default_kpi_for_niche(niche: str | None) -> dict[str, str]:
    key = (niche or "generic").strip().lower()
    triples = _NICHE_KPI.get(key) or _NICHE_KPI["generic"]
    (v1, n1), (v2, n2), (v3, n3) = triples
    return {
        "stats_v1": v1,
        "stats_n1": n1,
        "stats_v2": v2,
        "stats_n2": n2,
        "stats_v3": v3,
        "stats_n3": n3,
    }


def ensure_business_kpi_ui(
    ui: dict[str, str],
    *,
    package_id: str | None,
    niche: str | None = None,
) -> dict[str, str]:
    """Business/Premium always get KPI values so Hero slots are never empty."""
    pkg = (package_id or "basic").strip().lower()
    if pkg not in {"business", "premium"}:
        return ui
    out = dict(ui)
    if not (out.get("stats_v1") or "").strip():
        out.update(default_kpi_for_niche(niche))
    return out


def audit_html_visual_slots(
    html: str,
    *,
    package_id: str = "business",
    assets_dir: Path | None = None,
) -> VisualQualityReport:
    """Detect empty decorative zones / placeholders on Business+ HTML."""
    pkg = (package_id or "basic").strip().lower()
    findings: list[VisualSlotFinding] = []
    if pkg == "basic":
        return VisualQualityReport(ok=True, package_id=pkg, score=100, findings=[])

    html_l = html or ""

    # Empty Hero-E orb: figure present but no <img> and no illustration SVG
    if 'class="hero-E-orb"' in html_l or "hero-E-orb" in html_l:
        orb = re.search(
            r'<figure[^>]*hero-E-orb[^>]*>(.*?)</figure>',
            html_l,
            flags=re.I | re.S,
        )
        if orb:
            body = orb.group(1).lower()
            if "<img" not in body and "hero-e-illu" not in body and "<svg" not in body:
                findings.append(
                    VisualSlotFinding(
                        "hero_media",
                        "fail",
                        "Hero-E orb has no image/illustration — empty decorative zone",
                    )
                )

    # Decorative-only media column without img (layout A)
    if "hero-A-media" in html_l:
        media = re.search(
            r'<figure[^>]*hero-A-media[^>]*>(.*?)</figure>',
            html_l,
            flags=re.I | re.S,
        )
        if media and "<img" not in media.group(1).lower() and "<svg" not in media.group(1).lower():
            findings.append(
                VisualSlotFinding(
                    "hero_media",
                    "fail",
                    "Hero-A media column empty (deco only)",
                )
            )

    # Business+ must expose KPI or strong trust chips in hero
    has_kpi = "hero-kpi" in html_l or 'aria-label="stats"' in html_l
    has_trust = "trust-pill" in html_l or "trust-chip" in html_l
    if not has_kpi and not has_trust:
        findings.append(
            VisualSlotFinding(
                "hero_accent",
                "fail",
                "No KPI cards and no trust badges in Hero",
            )
        )
    elif not has_kpi:
        findings.append(
            VisualSlotFinding(
                "hero_kpi",
                "warn",
                "Hero has trust badges but no KPI cards (Business Visual Pack prefers both)",
            )
        )

    # Stub asset URLs only — ignore HTML input placeholder="" attributes.
    if re.search(
        r"(?:src|href)=[\"'][^\"']*(?:via\.placeholder|placehold\.co|unsplash\.com/photo-000|placeholder\.(?:jpg|png|webp|svg))",
        html_l,
        re.I,
    ) or re.search(
        r"data-asset-source=[\"']placeholder[\"']",
        html_l,
        re.I,
    ):
        findings.append(
            VisualSlotFinding(
                "assets",
                "fail",
                "Placeholder / stub asset reference in HTML",
            )
        )

    if assets_dir and assets_dir.is_dir():
        hero = assets_dir / "hero.jpg"
        if hero.is_file() and hero.stat().st_size < 8_000:
            findings.append(
                VisualSlotFinding(
                    "hero_asset",
                    "fail",
                    f"hero.jpg too small ({hero.stat().st_size}B) — likely placeholder",
                )
            )
        elif not hero.is_file() and "assets/hero.jpg" in html_l:
            findings.append(
                VisualSlotFinding(
                    "hero_asset",
                    "fail",
                    "HTML references assets/hero.jpg but file missing",
                )
            )

    fails = [f for f in findings if f.severity == "fail"]
    warns = [f for f in findings if f.severity == "warn"]
    score = max(0, 100 - 25 * len(fails) - 8 * len(warns))
    return VisualQualityReport(
        ok=len(fails) == 0,
        package_id=pkg,
        findings=findings,
        score=score,
    )


def audit_demo_gallery_visual_quality(
    previews_root: Path | None = None,
) -> dict[str, Any]:
    """CEO / Launch Blocker signal over public Business demos."""
    # .../app/factory/visual_intelligence → parents[4] = dashboard
    root = previews_root or (
        Path(__file__).resolve().parents[4]
        / "frontend"
        / "public"
        / "package-previews"
        / "sites"
        / "business"
    )
    niches = (
        "dental",
        "law",
        "restaurant",
        "beauty",
        "auto",
        "fitness",
        "handwerk",
        "it",
    )
    items: list[dict[str, Any]] = []
    for niche in niches:
        index = root / niche / "index.html"
        assets = root / niche / "assets"
        if not index.is_file():
            items.append(
                {
                    "id": niche,
                    "ok": False,
                    "score": 0,
                    "findings": [{"slot": "missing", "severity": "fail", "detail": "index.html missing"}],
                }
            )
            continue
        html = index.read_text(encoding="utf-8", errors="replace")
        report = audit_html_visual_slots(
            html, package_id="business", assets_dir=assets if assets.is_dir() else None
        )
        items.append({"id": niche, **report.as_dict()})

    passed = sum(1 for i in items if i.get("ok"))
    goal = len(niches)
    status = "PASS" if passed == goal else "FAIL"
    return {
        "ok": status == "PASS",
        "status": status,
        "title": "Visual Quality Gate",
        "phase": "business_visual_pack",
        "ssot": SSOT_RULE,
        "pass": passed,
        "goal": goal,
        "items": items,
        "next": (
            "Business Visual Pack complete"
            if status == "PASS"
            else "Fill empty Hero slots + replace placeholders on Business demos"
        ),
    }
