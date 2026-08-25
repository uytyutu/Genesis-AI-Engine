"""Product Intelligence — niche / content / catalog semantic consistency.

Statuses (honest):
  PASS | FAIL | REVIEW_REQUIRED | NOT_AVAILABLE

Does not invent LLM calls. Uses client niche context + distinctive vocab families.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


# Distinctive markers per industry family — used as cross-contamination checks.
# Not a full language model: if unknown, return REVIEW_REQUIRED / NOT_AVAILABLE.
_FAMILY_MARKERS: dict[str, tuple[str, ...]] = {
    "law": (
        "kanzlei",
        "rechtsgebiete",
        "rechtsgebiet",
        "rechtsanwalt",
        "wirtschaftsrecht",
        "vertragsprüfung",
        "vertragsprufung",
    ),
    "dental": (
        "zahnarzt",
        "zahnmedizin",
        "prophylaxe",
        "implantat",
        "behandlungsstuhl",
        "zahnarztangst",
        "kieferorthop",
    ),
    "auto": (
        "werkstatt",
        "inspektion",
        "autohaus",
        "reifenwechsel",
        "ölwechsel",
        "olwechsel",
        "fahrzeugankauf",
        "detailing",
    ),
    "restaurant": (
        "speisekarte",
        "mittagstisch",
        "reservierung",
        "gaststätte",
        "gaststatte",
    ),
    "beauty": (
        "nagelstudio",
        "wimpern",
        "maniküre",
        "manikure",
        "kosmetikstudio",
        "wimpernlifting",
    ),
    "handwerk": (
        "dachreinigung",
        "zaunbau",
        "baustelle",
        "malerbetrieb",
        "sanitär",
        "sanitaer",
        "elektroinstallation",
    ),
    "psychology": (
        "psycholog",
        "psychotherapie",
        "beratungspraxis",
        "familientherapie",
    ),
    "realestate": (
        "immobilienmakler",
        "objektbesichtigung",
        "eigentumswohnung",
    ),
    "fashion": (
        "kollektion",
        "modedesign",
        "outfit",
        "lookbook",
    ),
    "fitness": ("mitgliedschaft", "workout", "krafttraining", "fitnessstudio"),
    "cleaning": ("gebäudereinigung", "unterhaltsreinigung", "putzfirma", "hausmeisterservice"),
    "computer": ("it-support", "notebook-reparatur", "pc-reparatur", "edv-service"),
    "photography": ("fotostudio", "hochzeitsfotografie", "portraitfotografie"),
    "accounting": ("steuerberatung", "buchhaltung", "jahresabschluss"),
    "energy": ("photovoltaik", "wärmepumpe", "warmepumpe", "energieberatung"),
}

# Niche → own family + foreign families that must not appear in chrome.
_NICHE_FAMILY: dict[str, str] = {
    "law": "law",
    "accounting": "accounting",
    "dental": "dental",
    "orthodontics": "dental",
    "beauty": "beauty",
    "auto": "auto",
    "auto_ankauf": "auto",
    "auto_detailing": "auto",
    "car_dealership": "auto",
    "restaurant": "restaurant",
    "handwerk": "handwerk",
    "dachreinigung": "handwerk",
    "zaunbau": "handwerk",
    "gartenpflege": "handwerk",
    "maler": "handwerk",
    "elektro": "handwerk",
    "sanitaer": "handwerk",
    "green": "handwerk",
    "energy": "energy",
    "psychology": "psychology",
    "family_psychology": "psychology",
    "realestate": "realestate",
    "fashion": "fashion",
    "fitness": "fitness",
    "cleaning": "cleaning",
    "computer": "computer",
    "it_support": "computer",
    "appliance": "computer",
    "photography": "photography",
}

# Expected chrome tokens (nav / hero) — soft positive signal.
_EXPECTED_CHROME: dict[str, tuple[str, ...]] = {
    "dental": ("praxis", "behandlung", "termin", "zahn"),
    "orthodontics": ("praxis", "behandlung", "termin"),
    "beauty": ("salon", "termin", "pflege", "studio"),
    "law": ("kanzlei", "kontakt", "recht"),
    "accounting": ("steuer", "kontakt", "beratung"),
    "auto": ("service", "kontakt", "werkstatt", "termin"),
    "auto_ankauf": ("ankauf", "fahrzeug", "kontakt"),
    "auto_detailing": ("detailing", "pflege", "kontakt"),
    "car_dealership": ("fahrzeuge", "kontakt", "autohaus"),
    "restaurant": ("menü", "menu", "reservierung", "haus"),
    "handwerk": ("leistung", "kontakt", "angebot"),
    "dachreinigung": ("leistung", "kontakt", "dach"),
    "zaunbau": ("leistung", "kontakt", "zaun"),
    "gartenpflege": ("garten", "leistung", "kontakt"),
    "elektro": ("leistung", "kontakt", "elektro"),
    "sanitaer": ("leistung", "kontakt", "sanit"),
    "maler": ("leistung", "kontakt", "maler"),
    "psychology": ("praxis", "kontakt", "termin"),
    "family_psychology": ("praxis", "kontakt", "familie"),
    "fashion": ("katalog", "kollektion", "shop"),
    "fitness": ("training", "mitglied", "kontakt"),
    "cleaning": ("reinigung", "kontakt", "angebot"),
    "computer": ("reparatur", "kontakt", "service"),
    "it_support": ("support", "kontakt", "it"),
    "photography": ("galerie", "portfolio", "kontakt"),
    "realestate": ("immobilien", "kontakt", "objekte"),
    "energy": ("energie", "kontakt", "beratung"),
    "appliance": ("reparatur", "kontakt", "service"),
    "green": ("leistung", "kontakt", "garten"),
}


@dataclass
class IntelCheck:
    id: str
    status: str  # PASS | FAIL | REVIEW_REQUIRED | NOT_AVAILABLE
    detail: str = ""
    found: list[str] = field(default_factory=list)
    expected: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "detail": self.detail,
            "found": self.found,
            "expected": self.expected,
            "what": self.detail,
            "why": (
                f"Found: {', '.join(self.found)}"
                if self.found
                else self.detail
            ),
            "example": (
                f"Expected niche signals: {', '.join(self.expected)}"
                if self.expected
                else ""
            ),
        }


@dataclass
class ProductIntelligenceResult:
    niche_id: str
    checks: list[IntelCheck] = field(default_factory=list)

    @property
    def status(self) -> str:
        statuses = [c.status for c in self.checks]
        if any(s == "FAIL" for s in statuses):
            return "FAIL"
        if any(s == "REVIEW_REQUIRED" for s in statuses):
            return "REVIEW_REQUIRED"
        if statuses and all(s == "NOT_AVAILABLE" for s in statuses):
            return "NOT_AVAILABLE"
        if statuses and all(s in ("PASS", "NOT_AVAILABLE") for s in statuses):
            return "PASS"
        return "REVIEW_REQUIRED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "niche_id": self.niche_id,
            "checks": [c.as_dict() for c in self.checks],
            "niche_match": next(
                (c.as_dict() for c in self.checks if c.id == "niche_match"), None
            ),
            "content_match": next(
                (c.as_dict() for c in self.checks if c.id == "content_match"), None
            ),
            "catalog_match": next(
                (c.as_dict() for c in self.checks if c.id == "catalog_match"), None
            ),
            "image_match": next(
                (c.as_dict() for c in self.checks if c.id == "image_match"), None
            ),
            "geo_consistency": next(
                (c.as_dict() for c in self.checks if c.id == "geo_consistency"), None
            ),
        }


class _ChromeText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = False
        self._in_nav = False
        self._in_hero = False
        self.nav_text: list[str] = []
        self.hero_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        attr = {k: (v or "") for k, v in attrs}
        if t in ("script", "style"):
            self._skip = True
        if t == "nav" or "nav" in attr.get("class", "").lower() or attr.get("role") == "navigation":
            self._in_nav = True
        if "hero" in attr.get("class", "").lower() or attr.get("data-hero-layout"):
            self._in_hero = True
        if t == "header":
            self._in_hero = True

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in ("script", "style"):
            self._skip = False
        if t == "nav":
            self._in_nav = False
        if t == "header":
            self._in_hero = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        chunk = (data or "").strip()
        if not chunk:
            return
        self.parts.append(chunk)
        if self._in_nav:
            self.nav_text.append(chunk)
        if self._in_hero:
            self.hero_text.append(chunk)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def evaluate_website_niche_intelligence(
    *,
    html: str,
    niche_id: str,
) -> ProductIntelligenceResult:
    niche = (niche_id or "generic").strip().lower() or "generic"
    result = ProductIntelligenceResult(niche_id=niche)
    if niche == "generic":
        result.checks.append(
            IntelCheck(
                "niche_match",
                "REVIEW_REQUIRED",
                "generic niche — owner must confirm industry",
            )
        )
        return result

    family = _NICHE_FAMILY.get(niche)
    if not family:
        result.checks.append(
            IntelCheck(
                "niche_match",
                "NOT_AVAILABLE",
                f"no signature family for niche={niche}",
            )
        )
        return result

    parser = _ChromeText()
    try:
        parser.feed(html or "")
    except Exception:
        result.checks.append(
            IntelCheck("niche_match", "REVIEW_REQUIRED", "html parse failed")
        )
        return result

    chrome = _norm(" ".join(parser.nav_text + parser.hero_text + parser.parts[:40]))
    own = _FAMILY_MARKERS.get(family, ())
    foreign_hits: list[str] = []
    for other_family, markers in _FAMILY_MARKERS.items():
        if other_family == family:
            continue
        for m in markers:
            if m in chrome:
                # Avoid false positives: short shared substrings
                if len(m) < 5:
                    continue
                foreign_hits.append(m)

    expected = list(_EXPECTED_CHROME.get(niche, own[:3]))
    own_hits = [m for m in own if m in chrome]

    if foreign_hits:
        result.checks.append(
            IntelCheck(
                "niche_match",
                "FAIL",
                f"foreign industry markers in nav/hero for niche={niche}",
                found=sorted(set(foreign_hits))[:8],
                expected=expected,
            )
        )
        result.checks.append(
            IntelCheck(
                "content_match",
                "FAIL",
                "navigation/hero copy mismatches requested business type",
                found=sorted(set(foreign_hits))[:8],
                expected=expected,
            )
        )
    elif own_hits or any(e in chrome for e in expected):
        result.checks.append(
            IntelCheck(
                "niche_match",
                "PASS",
                f"chrome matches family={family}",
                found=own_hits[:5],
                expected=expected,
            )
        )
        result.checks.append(
            IntelCheck("content_match", "PASS", "no foreign industry chrome"),
        )
    else:
        result.checks.append(
            IntelCheck(
                "niche_match",
                "REVIEW_REQUIRED",
                "no strong niche signal and no foreign markers",
                expected=expected,
            )
        )
        result.checks.append(
            IntelCheck(
                "content_match",
                "REVIEW_REQUIRED",
                "ambiguous chrome — owner eyes",
            )
        )
    return result


# Clothing product keyword families for catalog title↔image binding.
_PRODUCT_KEYWORD_FAMILIES: dict[str, tuple[str, ...]] = {
    "tee": ("tee", "t-shirt", "shirt", "top"),
    "shirt": ("shirt", "blouse", "oxford", "linen"),
    "jacket": ("jacket", "blazer", "coat", "overshirt"),
    "trousers": ("trousers", "pants", "chinos", "jeans", "skirt"),
    "shoe": ("sneaker", "boot", "shoe"),
    "bag": ("tote", "bag", "belt", "scarf"),
    "hoodie": ("hoodie", "crew", "knit", "camisole"),
}


def evaluate_store_catalog_intelligence(
    *,
    product_dir: Path,
    products: list[dict[str, Any]],
    category: str = "",
) -> ProductIntelligenceResult:
    niche = (category or "clothing").strip().lower() or "clothing"
    result = ProductIntelligenceResult(niche_id=niche)
    if not products:
        result.checks.append(
            IntelCheck("catalog_match", "FAIL", "empty catalog")
        )
        result.checks.append(
            IntelCheck("image_match", "FAIL", "no products")
        )
        return result

    missing_img = 0
    unbound = 0
    placeholder = 0
    for p in products:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name") or "").strip()
        img = str(p.get("image") or p.get("image_slot") or "").strip()
        bound = str(p.get("image_bound_to") or "").strip()
        if not img:
            missing_img += 1
            continue
        path = product_dir / img.replace("\\", "/").lstrip("/")
        if not path.is_file() or path.stat().st_size < 500:
            missing_img += 1
        if "placeholder" in img.lower() or "missing" in img.lower():
            placeholder += 1
        if bound and name and bound.lower() != name.lower():
            unbound += 1
        elif not bound:
            # Legacy builds without binding metadata → review, not fake PASS
            unbound += 1

    if missing_img:
        result.checks.append(
            IntelCheck(
                "catalog_match",
                "FAIL",
                f"{missing_img} products missing real image files",
            )
        )
        result.checks.append(
            IntelCheck("image_match", "FAIL", "missing product images"),
        )
    elif placeholder:
        result.checks.append(
            IntelCheck("catalog_match", "FAIL", "placeholder images in catalog")
        )
        result.checks.append(
            IntelCheck("image_match", "FAIL", "placeholder images"),
        )
    elif unbound and any(not str(p.get("image_bound_to") or "") for p in products if isinstance(p, dict)):
        result.checks.append(
            IntelCheck(
                "catalog_match",
                "PASS",
                f"{len(products)} products with images",
            )
        )
        result.checks.append(
            IntelCheck(
                "image_match",
                "REVIEW_REQUIRED",
                "image_bound_to metadata missing — cannot prove title↔image without browser eyes",
            )
        )
    else:
        result.checks.append(
            IntelCheck(
                "catalog_match",
                "PASS",
                f"{len(products)} products titled and imaged",
            )
        )
        result.checks.append(
            IntelCheck(
                "image_match",
                "PASS",
                "each product image bound to its title at seed time",
            )
        )
    return result


def run_website_product_intelligence(
    *,
    html: str,
    niche_id: str,
    city: str = "",
) -> dict[str, Any]:
    result = evaluate_website_niche_intelligence(html=html, niche_id=niche_id)
    try:
        from app.factory.content_ssot import audit_geo_consistency, cities_mentioned
    except ImportError:
        audit_geo_consistency = None  # type: ignore[assignment]
        cities_mentioned = None  # type: ignore[assignment]

    ssot_city = (city or "").strip()
    if cities_mentioned is None:
        result.checks.append(
            IntelCheck(
                "geo_consistency",
                "REVIEW_REQUIRED",
                "content_ssot module unavailable — geo audit skipped",
            )
        )
    elif not ssot_city:
        mentioned = cities_mentioned(html or "")
        if len(mentioned) > 1:
            result.checks.append(
                IntelCheck(
                    "geo_consistency",
                    "FAIL",
                    "multiple cities in customer-facing content without SSOT city",
                    found=mentioned[:8],
                    expected=[],
                )
            )
        elif len(mentioned) == 1:
            result.checks.append(
                IntelCheck(
                    "geo_consistency",
                    "PASS",
                    f"single city in content: {mentioned[0]}",
                    found=mentioned,
                    expected=mentioned,
                )
            )
        else:
            result.checks.append(
                IntelCheck(
                    "geo_consistency",
                    "REVIEW_REQUIRED",
                    "no city signal in content",
                )
            )
    elif audit_geo_consistency is not None:
        geo = audit_geo_consistency(html=html, city=ssot_city)
        result.checks.append(
            IntelCheck(
                geo["id"],
                geo["status"],
                geo["detail"],
                found=list(geo.get("found") or []),
                expected=list(geo.get("expected") or []),
            )
        )

    try:
        from app.factory.chrome_copy_audit import audit_client_facing_copy

        chrome = audit_client_facing_copy(
            html=html,
            niche_id=niche_id,
            client_delivery=True,
        )
        result.checks.append(
            IntelCheck(
                chrome["id"],
                chrome["status"],
                chrome.get("detail") or "",
                found=[f.get("detail", "") for f in (chrome.get("findings") or [])][:8],
                expected=[],
            )
        )
    except ImportError:
        result.checks.append(
            IntelCheck(
                "chrome_copy_audit",
                "REVIEW_REQUIRED",
                "chrome_copy_audit module unavailable — skipped",
            )
        )
    return result.as_dict()


def run_store_product_intelligence(
    *,
    product_dir: Path,
    products: list[dict[str, Any]],
    category: str = "",
) -> dict[str, Any]:
    return evaluate_store_catalog_intelligence(
        product_dir=product_dir,
        products=products,
        category=category,
    ).as_dict()
