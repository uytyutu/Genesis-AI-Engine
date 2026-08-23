"""Versioned Website Design Spec — Brief to Factory contract.

Phase 3: Brief -> Spec -> Builder.
Phase 4/5: Spec is the sole production contract.

Law: LLM does not write production HTML/JS.
LLM / Director may only propose structured config patches on allowed fields.
Engine builds from Spec. Premium QA judges independently.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.factory.industry_dna import (
    industry_dna_directive,
    industry_family_for_niche,
    industry_hero_profile,
)

SCHEMA = "virtus.website_design_spec.v1"

# Director may change only these design-decision fields (never free HTML).
DIRECTOR_PATCHABLE_FIELDS: frozenset[str] = frozenset(
    {
        "style_hint",
        "hero_profile",
        "cta_primary",
        "section_plan",
        "visual_direction.style",
    }
)

# Frozen identity — patching these requires a new brief, not a director tweak.
IMMUTABLE_IDENTITY_FIELDS: frozenset[str] = frozenset(
    {
        "schema",
        "niche_id",
        "industry_family",
        "market_code",
        "package_id",
        "business.name",
        "business.city",
    }
)

_REQUIRED_TOP: tuple[str, ...] = (
    "schema",
    "version_id",
    "niche_id",
    "industry_family",
    "package_id",
    "market_code",
    "business",
    "hero_profile",
    "cta_primary",
    "section_plan",
    "renderer_strategy",
    "design_dna_directive",
)

_DOMAIN_STATUSES = frozenset(
    {
        "none",
        "have_domain",
        "need_help",
        "owned",
        "available",
        "pending",
        "unknown",
    }
)

_FINGERPRINT_KEYS: tuple[str, ...] = (
    "schema",
    "version_id",
    "niche_id",
    "industry_family",
    "package_id",
    "market_code",
    "renderer_strategy",
    "cta_primary",
    "section_plan",
    "hero_profile",
    "domain_status",
    "services",
    "business.name",
    "business.city",
    "design_dna_directive.style_hint",
    "design_dna_directive.renderer_strategy",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _split_services(raw: Any) -> list[str]:
    if isinstance(raw, list):
        items = [str(x).strip() for x in raw if str(x).strip()]
        return items[:24]
    text = str(raw or "").strip()
    if not text:
        return []
    parts = re.split(r"[\n,;|]+", text)
    return [p.strip() for p in parts if p.strip()][:24]


def normalize_domain_status(raw: str | None) -> str:
    s = (raw or "").strip().lower()
    if s in ("have_domain", "owned", "registered"):
        return "owned"
    if s in ("need_help", "pending", "want_domain"):
        return "need_help"
    if s in ("none", "", "no"):
        return "none"
    if s in _DOMAIN_STATUSES:
        return s
    return "unknown"


def _get_path(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def build_website_design_spec(
    *,
    contacts: dict[str, Any],
    client_legal: dict[str, Any] | None = None,
    niche_id: str,
    package_id: str,
    market_code: str = "DE",
    interview: dict[str, Any] | None = None,
    version: int = 1,
    version_id: str = "V1",
) -> dict[str, Any]:
    """Build Design Spec V1 from order brief + interview (no LLM HTML)."""
    legal = client_legal if isinstance(client_legal, dict) else {}
    iv = interview if isinstance(interview, dict) else {}
    c = contacts if isinstance(contacts, dict) else {}

    niche = str(niche_id or c.get("niche") or iv.get("niche") or "").strip().lower()
    if not niche:
        niche = "generic"
    pid = str(package_id or c.get("package_id") or "basic").strip().lower() or "basic"
    market = str(market_code or c.get("market_code") or "DE").strip().upper() or "DE"

    business_name = str(
        c.get("business_name")
        or iv.get("company_name")
        or legal.get("business_name")
        or ""
    ).strip()
    city = str(c.get("city") or iv.get("city") or legal.get("city") or "").strip()
    phone = str(c.get("phone") or legal.get("phone") or "").strip()
    email = str(c.get("email") or legal.get("email") or "").strip()
    services = _split_services(c.get("services_list") or iv.get("top_services") or "")
    opening_hours = str(c.get("opening_hours") or c.get("hours") or "").strip()
    domain_status = normalize_domain_status(
        str(c.get("domain_status") or c.get("domain") or "")
    )
    visual_style = str(
        c.get("brand_style") or c.get("style") or iv.get("style") or ""
    ).strip()
    about = str(
        c.get("who_is_company") or iv.get("about") or c.get("client_story") or ""
    ).strip()
    from app.factory.de_export_text import polish_de_export_text, resolve_differentiator

    differentiator = str(
        c.get("why_choose_us")
        or c.get("main_promise")
        or iv.get("differentiator")
        or ""
    ).strip()
    differentiator = resolve_differentiator(
        niche_id=niche,
        city=city,
        raw=polish_de_export_text(differentiator, market_code=market),
    )
    about = polish_de_export_text(about, market_code=market)
    diversity_salt = str(c.get("diversity_salt") or "")

    family = industry_family_for_niche(niche)
    directive = industry_dna_directive(
        niche_id=niche,
        package_id=pid,
        business_name=business_name or "Business",
        diversity_salt=diversity_salt,
        style_hint=visual_style,
    )
    section_plan = _section_plan_for_family(family, pid)
    hero_profile = industry_hero_profile(family, pid)
    renderer = str(directive.get("renderer_strategy") or "classic")

    spec: dict[str, Any] = {
        "schema": SCHEMA,
        "version": int(version),
        "version_id": str(version_id),
        "status": "draft",
        "created_at": _now_iso(),
        "market_code": market,
        "niche_id": niche,
        "industry_family": family,
        "package_id": pid,
        "business": {
            "name": business_name,
            "city": city,
            "phone": phone,
            "email": email,
            "about": about,
            "differentiator": differentiator,
        },
        "services": services,
        "opening_hours": opening_hours,
        "domain_status": domain_status,
        "visual_direction": {
            "style": visual_style,
            "mood": directive.get("industry_family") or family,
            "hero_mode": hero_profile.get("hero_mode"),
            "photography": hero_profile.get("photography"),
        },
        "hero_profile": hero_profile,
        "cta_primary": hero_profile.get("cta_primary"),
        "design_dna_directive": directive,
        "section_plan": section_plan,
        "renderer_strategy": renderer,
        "materials": list(c.get("materials") or [])
        if isinstance(c.get("materials"), list)
        else [],
        "source": "brief",
        "immutable": False,
    }
    spec["contract_fingerprint"] = spec_contract_fingerprint(spec)
    return spec


def _section_plan_for_family(family: str, package_id: str) -> list[str]:
    base = ["hero", "services", "trust", "process", "contact"]
    if family == "automotive":
        return ["hero", "services", "werkstatt", "trust", "hours", "contact"]
    if family == "hospitality":
        return [
            "hero",
            "speisekarte",
            "spezialitaeten",
            "galerie",
            "reservierung",
            "contact",
        ]
    if family == "dental":
        return ["hero", "treatments", "team", "trust", "appointment", "contact"]
    if family == "legal":
        return ["hero", "practice_areas", "team", "trust", "contact"]
    if family == "beauty":
        return ["hero", "services", "gallery", "booking", "contact"]
    if family == "realestate":
        return ["hero", "search", "listings", "trust", "contact"]
    if package_id == "premium":
        return base + ["gallery", "faq"]
    return base


def validate_website_design_spec(spec: dict[str, Any] | None) -> dict[str, Any]:
    """Hard contract check. Invalid Spec -> REJECT (do not improvise HTML)."""
    errors: list[str] = []
    if not isinstance(spec, dict) or not spec:
        return {"ok": False, "errors": ["spec:missing"], "status": "REJECT"}

    for key in _REQUIRED_TOP:
        if key not in spec or spec.get(key) in (None, "", []):
            errors.append(f"required:{key}")

    if spec.get("schema") and spec.get("schema") != SCHEMA:
        errors.append("schema:unsupported")

    biz = spec.get("business")
    if not isinstance(biz, dict):
        errors.append("business:not_object")
    else:
        if not str(biz.get("name") or "").strip():
            errors.append("business:name_missing")
        if not str(biz.get("city") or "").strip():
            errors.append("business:city_missing")

    plan = spec.get("section_plan")
    if not isinstance(plan, list) or len(plan) < 3:
        errors.append("section_plan:too_short")
    elif "hero" not in plan or "contact" not in plan:
        errors.append("section_plan:missing_hero_or_contact")

    hero = spec.get("hero_profile")
    if not isinstance(hero, dict) or not hero.get("hero_mode"):
        errors.append("hero_profile:incomplete")

    family = str(spec.get("industry_family") or "")
    niche = str(spec.get("niche_id") or "")
    expected_family = industry_family_for_niche(niche) if niche else ""
    if niche and expected_family and family and family != expected_family:
        errors.append("industry_family:mismatch_niche")

    renderer = str(spec.get("renderer_strategy") or "")
    directive = spec.get("design_dna_directive")
    if isinstance(directive, dict):
        d_renderer = str(directive.get("renderer_strategy") or "")
        if d_renderer and renderer and d_renderer != renderer:
            errors.append("renderer_strategy:directive_mismatch")

    if family == "automotive" and renderer and renderer != "craftsman":
        errors.append("automotive:renderer_must_be_craftsman")
    if family == "hospitality" and renderer and renderer != "restaurant":
        errors.append("hospitality:renderer_must_be_restaurant")

    for forbidden in ("html", "raw_html", "llm_html", "body_html"):
        if forbidden in spec:
            errors.append(f"forbidden:{forbidden}")

    ok = not errors
    return {"ok": ok, "errors": errors, "status": "OK" if ok else "REJECT"}


def spec_contract_fingerprint(spec: dict[str, Any]) -> str:
    """Stable hash of structural contract fields (excludes created_at / prose)."""
    payload: dict[str, Any] = {}
    for key in _FINGERPRINT_KEYS:
        if "." in key:
            payload[key] = _get_path(spec, key)
        else:
            payload[key] = spec.get(key)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def builder_contract_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Normalized Engine input — the only contract Builder may consume."""
    validation = validate_website_design_spec(spec)
    biz = spec.get("business") if isinstance(spec.get("business"), dict) else {}
    directive = (
        spec.get("design_dna_directive")
        if isinstance(spec.get("design_dna_directive"), dict)
        else {}
    )
    return {
        "ok": validation["ok"],
        "errors": list(validation["errors"]),
        "version_id": str(spec.get("version_id") or ""),
        "niche_id": str(spec.get("niche_id") or ""),
        "industry_family": str(spec.get("industry_family") or ""),
        "package_id": str(spec.get("package_id") or ""),
        "market_code": str(spec.get("market_code") or "DE"),
        "renderer_strategy": str(spec.get("renderer_strategy") or ""),
        "cta_primary": str(spec.get("cta_primary") or ""),
        "section_plan": list(spec.get("section_plan") or []),
        "hero_profile": dict(spec.get("hero_profile") or {}),
        "style_hint": str(directive.get("style_hint") or ""),
        "business_name": str(biz.get("name") or ""),
        "city": str(biz.get("city") or ""),
        "services": list(spec.get("services") or []),
        "contract_fingerprint": spec_contract_fingerprint(spec),
    }


def _next_version_id(current: str) -> str:
    text = str(current or "V1").strip().upper()
    if text.startswith("V") and text[1:].isdigit():
        return f"V{int(text[1:]) + 1}"
    return "V2"


def apply_director_config_patch(
    spec: dict[str, Any],
    patch: dict[str, Any] | None,
    *,
    bump_version: bool = True,
) -> dict[str, Any]:
    """Apply allowed Director fields only. Returns new Spec (prior version stays immutable).

    Rejects unknown keys and identity mutations. Never accepts HTML.
    """
    if not isinstance(spec, dict) or not spec:
        return {
            "ok": False,
            "errors": ["spec:missing"],
            "status": "REJECT",
            "spec": None,
        }

    patch = patch if isinstance(patch, dict) else {}
    errors: list[str] = []
    for key in patch:
        if key in ("html", "raw_html", "llm_html", "body_html"):
            errors.append(f"forbidden:{key}")
            continue
        if key in IMMUTABLE_IDENTITY_FIELDS:
            errors.append(f"immutable:{key}")
            continue
        if key.startswith("business."):
            errors.append(f"immutable:{key}")
            continue
        if key not in DIRECTOR_PATCHABLE_FIELDS:
            errors.append(f"not_patchable:{key}")

    if errors:
        return {
            "ok": False,
            "errors": errors,
            "status": "REJECT",
            "spec": None,
        }

    new_spec = copy.deepcopy(spec)
    prior_id = str(spec.get("version_id") or "V1")
    new_spec["parent_version_id"] = prior_id
    if bump_version:
        new_spec["version_id"] = _next_version_id(prior_id)
        new_spec["version"] = int(spec.get("version") or 1) + 1
    new_spec["status"] = "draft"
    new_spec["immutable"] = False
    new_spec["source"] = "director_patch"
    new_spec["created_at"] = _now_iso()

    if "style_hint" in patch:
        hint = str(patch["style_hint"] or "").strip()
        directive = dict(
            new_spec.get("design_dna_directive")
            if isinstance(new_spec.get("design_dna_directive"), dict)
            else {}
        )
        directive["style_hint"] = hint
        new_spec["design_dna_directive"] = directive
        visual = dict(
            new_spec.get("visual_direction")
            if isinstance(new_spec.get("visual_direction"), dict)
            else {}
        )
        visual["style"] = hint
        new_spec["visual_direction"] = visual

    if "visual_direction.style" in patch:
        hint = str(patch["visual_direction.style"] or "").strip()
        visual = dict(
            new_spec.get("visual_direction")
            if isinstance(new_spec.get("visual_direction"), dict)
            else {}
        )
        visual["style"] = hint
        new_spec["visual_direction"] = visual
        directive = dict(
            new_spec.get("design_dna_directive")
            if isinstance(new_spec.get("design_dna_directive"), dict)
            else {}
        )
        directive["style_hint"] = hint
        new_spec["design_dna_directive"] = directive

    if "hero_profile" in patch:
        hp = patch["hero_profile"]
        if not isinstance(hp, dict):
            return {
                "ok": False,
                "errors": ["hero_profile:not_object"],
                "status": "REJECT",
                "spec": None,
            }
        merged = dict(new_spec.get("hero_profile") or {})
        merged.update({k: v for k, v in hp.items() if v is not None})
        new_spec["hero_profile"] = merged
        if merged.get("cta_primary") and "cta_primary" not in patch:
            new_spec["cta_primary"] = merged.get("cta_primary")

    if "cta_primary" in patch:
        new_spec["cta_primary"] = str(patch["cta_primary"] or "").strip()
        hp = dict(new_spec.get("hero_profile") or {})
        hp["cta_primary"] = new_spec["cta_primary"]
        new_spec["hero_profile"] = hp

    if "section_plan" in patch:
        plan = patch["section_plan"]
        if not isinstance(plan, list) or not plan:
            return {
                "ok": False,
                "errors": ["section_plan:invalid"],
                "status": "REJECT",
                "spec": None,
            }
        new_spec["section_plan"] = [str(x).strip() for x in plan if str(x).strip()]

    validation = validate_website_design_spec(new_spec)
    if not validation["ok"]:
        return {
            "ok": False,
            "errors": validation["errors"],
            "status": "REJECT",
            "spec": None,
        }

    new_spec["contract_fingerprint"] = spec_contract_fingerprint(new_spec)
    return {
        "ok": True,
        "errors": [],
        "status": "OK",
        "spec": new_spec,
        "parent_version_id": prior_id,
        "version_id": new_spec["version_id"],
    }


def freeze_website_design_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Mark Spec immutable (V1/V2 snapshots stay frozen after ship)."""
    out = copy.deepcopy(spec)
    out["immutable"] = True
    out["status"] = "frozen"
    out["frozen_at"] = _now_iso()
    out["contract_fingerprint"] = spec_contract_fingerprint(out)
    return out


def apply_spec_to_contacts(spec: dict[str, Any], contacts: dict[str, Any]) -> dict[str, Any]:
    """Merge Spec into factory contacts for compose path."""
    out = dict(contacts or {})
    out["website_design_spec"] = spec
    biz = spec.get("business") if isinstance(spec.get("business"), dict) else {}
    if biz.get("name"):
        out["business_name"] = str(biz["name"])
    if biz.get("city"):
        out["city"] = str(biz["city"])
    if biz.get("phone"):
        out["phone"] = str(biz["phone"])
    if biz.get("email"):
        out["email"] = str(biz["email"])
    if spec.get("niche_id"):
        out["niche"] = str(spec["niche_id"])
    if spec.get("services"):
        out["services_list"] = "\n".join(spec["services"])
    if spec.get("opening_hours"):
        out["opening_hours"] = str(spec["opening_hours"])
    if spec.get("domain_status"):
        out["domain_status"] = str(spec["domain_status"])
    directive = (
        spec.get("design_dna_directive")
        if isinstance(spec.get("design_dna_directive"), dict)
        else {}
    )
    hint = str(directive.get("style_hint") or "").strip()
    if hint:
        out["brand_style"] = hint
    renderer = str(
        spec.get("renderer_strategy") or directive.get("renderer_strategy") or ""
    ).strip()
    if renderer:
        out["renderer_strategy_hint"] = renderer
    out["design_spec_version_id"] = str(spec.get("version_id") or "V1")
    out["design_contract_fingerprint"] = str(
        spec.get("contract_fingerprint") or spec_contract_fingerprint(spec)
    )
    return out


def write_website_design_spec(product_dir: Path, spec: dict[str, Any]) -> Path:
    product_dir.mkdir(parents=True, exist_ok=True)
    path = product_dir / "website_design_spec.json"
    path.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # Immutable per-version snapshot (V1/V2 never overwrite each other).
    vid = str(spec.get("version_id") or "V1").strip() or "V1"
    snap = product_dir / f"website_design_spec.{vid}.json"
    if not snap.is_file():
        snap.write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return path


def read_website_design_spec(product_dir: Path) -> dict[str, Any] | None:
    path = product_dir / "website_design_spec.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def read_website_design_spec_version(
    product_dir: Path, version_id: str
) -> dict[str, Any] | None:
    vid = str(version_id or "").strip()
    if not vid:
        return None
    path = product_dir / f"website_design_spec.{vid}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None
