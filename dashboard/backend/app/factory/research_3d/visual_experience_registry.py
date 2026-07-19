"""Visual Experience Engine — Product Registry (research / Premium).

Product language (user-facing): Visual Experience / Interactive Product Engine.
On-disk library stays under showcases/ for stability (folder = data, not brand).

Layout (scalable — add product = add folder):
  showcases/<niche>/
    quality.json                 niche defaults
    metadata.json                optional
    preview.jpg                  niche fallback still
    model.glb                    optional niche fallback
    products/
      <product_id>/
        product.json             score, specializations, premium, labels
        preview.jpg|webp         preferred
        model.glb                optional
        hotspots.json            optional

Resolve:
  niche (+ alias) → list products → score by specialization →
  approved+premium product → interactive_3d else preview else niche/generic fallback.
Never empty for Business/Premium.

Path A must not enable live Stripe 3d_premium from this module.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

QualityTier = Literal["placeholder", "approved", "premium"]
DeliveryMode = Literal["none", "preview", "interactive_3d", "css_motion"]

# Product-facing engine id (not "showcase" in client configs)
ENGINE_ID = "visual_experience"
ENGINE_LABEL = "Visual Experience Engine"

_ROOT = Path(__file__).resolve().parents[3] / "_research_3d"
_LIBRARY_ROOT = _ROOT / "showcases"
_INDEX = _LIBRARY_ROOT / "index.json"
_LIBRARY = _LIBRARY_ROOT / "library.json"
_PRODUCTS_MANIFEST = _LIBRARY_ROOT / "products_manifest.json"

NICHE_ALIASES: dict[str, str] = {
    "solar": "energy",
    "pv": "energy",
    "hvac": "appliance",
    "climate": "appliance",
    "kitchen": "appliance",
    "windows": "handwerk",
    "window": "handwerk",
    "roof": "handwerk",
    "furniture": "handwerk",
    "construction": "handwerk",
    "fitness": "beauty",
    "spa": "beauty",
    "real_estate": "generic",
    "immobilien": "generic",
    "restaurant": "generic",
    "hotel": "generic",
    "hospitality": "generic",
    "car": "auto",
    "garage": "auto",
    "workshop": "auto",
    "it": "computer",
    "legal": "law",
    "garden": "green",
    "dentist": "dental",
    "dentistry": "dental",
    "default": "generic",
}


@dataclass(frozen=True)
class ProductEntry:
    """One interactive/visual product inside a niche (implant, engine, solar_panel…)."""

    niche_id: str
    product_id: str
    score: int
    premium: bool
    specializations: tuple[str, ...]
    tags: tuple[str, ...]
    label_de: str
    label_en: str
    quality: QualityTier
    client_facing_3d: bool
    preview_rel: str | None
    model_rel: str | None
    folder_rel: str
    hotspots: tuple[dict[str, Any], ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def allows_interactive_3d(self) -> bool:
        return self.client_facing_3d and self.quality in ("approved", "premium")


@dataclass(frozen=True)
class NicheCatalog:
    niche_id: str
    quality: QualityTier
    client_facing_3d: bool
    label_de: str
    label_en: str
    sub_de: str
    sub_en: str
    preview_rel: str | None
    model_rel: str | None
    products: tuple[ProductEntry, ...]
    resolved_via_alias: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    # Back-compat aliases used by older showcase_registry callers
    @property
    def scenes(self) -> tuple[ProductEntry, ...]:
        return self.products

    @property
    def allows_interactive_3d(self) -> bool:
        return self.client_facing_3d and self.quality in ("approved", "premium")

    @property
    def primary(self) -> str:
        return str(self.raw.get("primary") or "product")


# Legacy name kept for imports
ShowcaseScene = ProductEntry
ShowcaseEntry = NicheCatalog


def library_root() -> Path:
    return _LIBRARY_ROOT


def showcase_root() -> Path:
    """Deprecated alias — disk root of the Visual Experience library."""
    return _LIBRARY_ROOT


def canonicalize_niche(niche_id: str | None) -> str:
    key = str(niche_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not key:
        return "generic"
    return NICHE_ALIASES.get(key, key)


_SPECIALIZATION_MAP = _LIBRARY_ROOT / "specialization_map.json"


def load_specialization_map() -> dict[str, Any]:
    return _read_json(_SPECIALIZATION_MAP)


def resolve_specialization_profile(
    specialization: str | None,
    *,
    niche_id: str | None = None,
) -> dict[str, Any] | None:
    """Pick specialization_map entry from free-text specialization + optional niche."""
    data = load_specialization_map()
    specs = data.get("specializations") or {}
    if not isinstance(specs, dict) or not specs:
        return None
    tokens = _tokenize(specialization)
    niche = canonicalize_niche(niche_id) if niche_id else ""
    best_key = None
    best_score = -1
    for key, row in specs.items():
        if not isinstance(row, dict):
            continue
        score = 0
        key_l = key.lower()
        if key_l in tokens or key_l in (specialization or "").lower().replace(" ", "_"):
            score += 50
        if any(t in key_l or key_l in t for t in tokens):
            score += 20
        row_niche = str(row.get("niche") or "")
        if niche and row_niche == niche:
            score += 10
        if score > best_score:
            best_score = score
            best_key = key
    if best_key is None or best_score <= 0:
        # niche default: first map entry matching niche
        if niche:
            for key, row in specs.items():
                if isinstance(row, dict) and str(row.get("niche") or "") == niche:
                    best_key = key
                    break
        if best_key is None:
            best_key = "general" if "general" in specs else None
    if best_key is None:
        return None
    row = dict(specs[best_key])
    # Cap conversion hotspots at 4
    hs = row.get("hotspots") or []
    if isinstance(hs, list):
        row["hotspots"] = hs[:4]
    row["id"] = best_key
    # Resolve message + cta copy
    msg_copy = data.get("message_copy") or {}
    cta_copy = data.get("cta_copy") or {}
    messages = []
    for mid in row.get("messages") or []:
        block = msg_copy.get(mid) if isinstance(msg_copy, dict) else None
        if isinstance(block, dict):
            messages.append({"id": mid, **block})
    cta_id = str(row.get("cta") or "contact")
    cta_block = cta_copy.get(cta_id) if isinstance(cta_copy, dict) else None
    row["messages_resolved"] = messages
    row["cta_resolved"] = (
        {"id": cta_id, **cta_block} if isinstance(cta_block, dict) else {"id": cta_id}
    )
    return row


def _preferred_product_from_map(profile: dict[str, Any] | None) -> str | None:
    if not profile:
        return None
    products = profile.get("products") or []
    if isinstance(products, list) and products:
        return str(products[0])
    return None


def _rel_to_research(path: Path) -> str:
    try:
        return path.relative_to(_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _normalize_quality(value: str | None) -> QualityTier:
    raw = str(value or "placeholder").strip().lower()
    if raw in ("approved", "ok", "thematic"):
        return "approved"
    if raw in ("premium", "studio", "premium_3d"):
        return "premium"
    return "placeholder"


def _find_preview(folder: Path, preferred: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if preferred:
        p = Path(preferred)
        candidates.append(folder / p if not p.is_absolute() else p)
        # allow niche-relative from product folder: ../../preview.jpg handled by resolve
        candidates.append((folder / preferred).resolve())
    for name in ("preview.webp", "preview.jpg", "preview.png", "preview.jpeg"):
        candidates.append(folder / name)
    seen: set[str] = set()
    for c in candidates:
        try:
            key = str(c.resolve())
        except OSError:
            key = str(c)
        if key in seen:
            continue
        seen.add(key)
        if c.is_file():
            return c
    return None


def _find_model(folder: Path, preferred: str | None = None) -> Path | None:
    if preferred:
        p = folder / preferred
        if p.is_file():
            return p
    p = folder / "model.glb"
    return p if p.is_file() else None


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    parts = re.split(r"[^\w]+", str(text).lower().replace("-", "_"))
    return {p for p in parts if len(p) >= 3}


def list_showcase_niches() -> list[str]:
    if not _LIBRARY_ROOT.is_dir():
        return []
    return sorted(
        p.name
        for p in _LIBRARY_ROOT.iterdir()
        if p.is_dir() and (p / "quality.json").is_file()
    )


def list_niche_products(niche_id: str | None) -> list[str]:
    key = canonicalize_niche(niche_id)
    products_dir = _LIBRARY_ROOT / key / "products"
    if not products_dir.is_dir():
        return []
    return sorted(
        p.name
        for p in products_dir.iterdir()
        if p.is_dir() and (p / "product.json").is_file()
    )


def _load_product(niche_id: str, product_dir: Path, niche_quality: dict[str, Any]) -> ProductEntry | None:
    raw = _read_json(product_dir / "product.json")
    if not raw:
        return None
    pid = str(raw.get("id") or product_dir.name)
    specs = raw.get("specializations") or []
    if not isinstance(specs, list):
        specs = []
    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    try:
        score = int(raw.get("score", 50))
    except (TypeError, ValueError):
        score = 50
    score = max(0, min(100, score))

    q = _normalize_quality(raw.get("quality") or niche_quality.get("quality"))
    facing = raw.get("client_facing_3d")
    if facing is None:
        facing = niche_quality.get("client_facing_3d")

    preview = _find_preview(product_dir, str(raw.get("preview") or "") or None)
    if preview is None:
        # inherit niche still
        preview = _find_preview(_LIBRARY_ROOT / niche_id, "preview.jpg")
    model = _find_model(product_dir, str(raw.get("model") or "") or None)
    if model is None and raw.get("inherit_model", True):
        model = _find_model(_LIBRARY_ROOT / niche_id, "model.glb")

    hs_raw = _read_json(product_dir / "hotspots.json")
    hotspots: tuple[dict[str, Any], ...] = ()
    if isinstance(hs_raw.get("hotspots"), list):
        hotspots = tuple(h for h in hs_raw["hotspots"] if isinstance(h, dict))

    return ProductEntry(
        niche_id=niche_id,
        product_id=pid,
        score=score,
        premium=bool(raw.get("premium", True)),
        specializations=tuple(str(s).lower().replace(" ", "_") for s in specs),
        tags=tuple(str(t).lower() for t in tags),
        label_de=str(raw.get("label_de") or niche_quality.get("label_de") or pid),
        label_en=str(raw.get("label_en") or niche_quality.get("label_en") or pid),
        quality=q,
        client_facing_3d=bool(facing),
        preview_rel=_rel_to_research(preview) if preview else None,
        model_rel=_rel_to_research(model) if model else None,
        folder_rel=_rel_to_research(product_dir),
        hotspots=hotspots,
        raw=raw,
    )


def _products_from_legacy_metadata(
    niche_id: str,
    quality: dict[str, Any],
    metadata: dict[str, Any],
) -> tuple[ProductEntry, ...]:
    """Backward compatible: metadata.scenes[] → ProductEntry without products/ folders."""
    raw_scenes = metadata.get("scenes")
    out: list[ProductEntry] = []
    niche_folder = _LIBRARY_ROOT / niche_id
    if isinstance(raw_scenes, list):
        for i, row in enumerate(raw_scenes):
            if not isinstance(row, dict):
                continue
            sid = str(row.get("id") or f"scene_{i}")
            tags = row.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            specs = row.get("specializations") or []
            if not isinstance(specs, list):
                specs = []
            try:
                score = int(row.get("score", 80 if row.get("primary") else 60))
            except (TypeError, ValueError):
                score = 70
            preview = _find_preview(niche_folder, str(row.get("preview") or "preview.jpg"))
            model = _find_model(niche_folder, str(row.get("model") or "model.glb"))
            out.append(
                ProductEntry(
                    niche_id=niche_id,
                    product_id=sid,
                    score=max(0, min(100, score)),
                    premium=bool(row.get("premium", True)),
                    specializations=tuple(str(s).lower().replace(" ", "_") for s in specs),
                    tags=tuple(str(t).lower() for t in tags),
                    label_de=str(row.get("label_de") or quality.get("label_de") or sid),
                    label_en=str(row.get("label_en") or quality.get("label_en") or sid),
                    quality=_normalize_quality(row.get("quality") or quality.get("quality")),
                    client_facing_3d=bool(
                        row.get("client_facing_3d")
                        if row.get("client_facing_3d") is not None
                        else quality.get("client_facing_3d")
                    ),
                    preview_rel=_rel_to_research(preview) if preview else None,
                    model_rel=_rel_to_research(model) if model else None,
                    folder_rel=_rel_to_research(niche_folder),
                    raw=row,
                )
            )
    if out:
        return tuple(out)

    # Single niche-level product
    preview = _find_preview(niche_folder)
    model = _find_model(niche_folder)
    return (
        ProductEntry(
            niche_id=niche_id,
            product_id="default",
            score=70,
            premium=True,
            specializations=(),
            tags=tuple(
                str(t).lower()
                for t in (quality.get("tags") or [quality.get("primary") or "product"])
                if t
            ),
            label_de=str(quality.get("label_de") or niche_id),
            label_en=str(quality.get("label_en") or niche_id),
            quality=_normalize_quality(quality.get("quality")),
            client_facing_3d=bool(quality.get("client_facing_3d")),
            preview_rel=_rel_to_research(preview) if preview else None,
            model_rel=_rel_to_research(model) if model else None,
            folder_rel=_rel_to_research(niche_folder),
            raw={"id": "default", "legacy": True},
        ),
    )


def resolve_niche_catalog(niche_id: str | None) -> NicheCatalog | None:
    requested = str(niche_id or "").strip().lower()
    key = canonicalize_niche(niche_id)
    folder = _LIBRARY_ROOT / key
    qpath = folder / "quality.json"
    if not qpath.is_file():
        return None

    quality = _read_json(qpath)
    metadata = _read_json(folder / "metadata.json")
    products_dir = folder / "products"
    products: list[ProductEntry] = []
    if products_dir.is_dir():
        for pdir in sorted(products_dir.iterdir()):
            if not pdir.is_dir():
                continue
            prod = _load_product(key, pdir, quality)
            if prod:
                products.append(prod)

    if not products:
        products = list(_products_from_legacy_metadata(key, quality, metadata))

    alias_used = (
        requested if requested and requested != key and requested in NICHE_ALIASES else None
    )
    preview = _find_preview(folder)
    model = _find_model(folder)

    return NicheCatalog(
        niche_id=key,
        quality=_normalize_quality(quality.get("quality")),
        client_facing_3d=bool(quality.get("client_facing_3d")),
        label_de=str(quality.get("label_de") or key),
        label_en=str(quality.get("label_en") or key),
        sub_de=str(
            quality.get("sub_de")
            or metadata.get("sub_de")
            or "Digitale Präsentation moderner Technologien für Ihr Gewerbe."
        ),
        sub_en=str(
            quality.get("sub_en")
            or metadata.get("sub_en")
            or "A digital presentation of modern technology for your trade."
        ),
        preview_rel=_rel_to_research(preview) if preview else None,
        model_rel=_rel_to_research(model) if model else None,
        products=tuple(products),
        resolved_via_alias=alias_used,
        metadata=metadata,
        raw=quality,
    )


def resolve_showcase(niche_id: str | None) -> NicheCatalog | None:
    """Back-compat name → niche catalog."""
    return resolve_niche_catalog(niche_id)


def score_product(
    product: ProductEntry,
    *,
    specialization: str | None = None,
    tier: str = "premium",
) -> float:
    """Rank product for client fit. Higher wins."""
    total = float(product.score)
    tokens = _tokenize(specialization)
    # specialization match (strong signal)
    spec_set = set(product.specializations)
    if tokens & spec_set:
        total += 40.0
    else:
        # partial: specialization string contains product id / tags
        for s in product.specializations:
            if s in (specialization or "").lower().replace(" ", "_"):
                total += 40.0
                break
        else:
            for t in product.tags:
                if t in tokens:
                    total += 12.0
                    break

    total += 8.0 * len(set(product.tags) & tokens)
    if product.premium and tier == "premium":
        total += 6.0
    if product.preview_rel:
        total += 4.0
    if product.allows_interactive_3d and product.model_rel:
        total += 10.0
    return total


def pick_product(
    catalog: NicheCatalog,
    *,
    specialization: str | None = None,
    tier: str = "premium",
    product_id: str | None = None,
) -> ProductEntry:
    products = list(catalog.products)
    if not products:
        # should not happen — resolve always synthesizes default
        raise ValueError("empty_product_catalog")

    if product_id:
        for p in products:
            if p.product_id == product_id:
                return p

    ranked = sorted(
        products,
        key=lambda p: score_product(p, specialization=specialization, tier=tier),
        reverse=True,
    )
    return ranked[0]


def pick_scene(
    entry: NicheCatalog,
    *,
    specialization: str | None = None,
) -> ProductEntry:
    """Back-compat alias for pick_product."""
    return pick_product(entry, specialization=specialization, tier="premium")


def resolve_visual_experience(
    *,
    niche_id: str | None,
    tier: str | None = "premium",
    specialization: str | None = None,
    product_id: str | None = None,
    locale: str = "de",
) -> dict[str, Any]:
    """Primary Product Registry delivery API (Visual Experience Engine)."""
    t = str(tier or "premium").strip().lower()
    if t not in ("basic", "business", "premium"):
        t = "premium"

    catalog = resolve_niche_catalog(niche_id)
    fallback_used = False
    if catalog is None:
        catalog = resolve_niche_catalog("generic")
        fallback_used = True
        if catalog is None:
            return {
                "ok": False,
                "engine": ENGINE_ID,
                "mode": "none",
                "tier": t,
                "reason": "visual_experience_library_empty",
            }

    spec_profile = resolve_specialization_profile(
        specialization, niche_id=catalog.niche_id
    )
    preferred = product_id or _preferred_product_from_map(spec_profile)
    # If map prefers a product that exists, bias pick_product
    if preferred and not product_id:
        ids = {p.product_id for p in catalog.products}
        if preferred not in ids:
            # try other products from map in order
            preferred = None
            for cand in (spec_profile or {}).get("products") or []:
                if str(cand) in ids:
                    preferred = str(cand)
                    break

    product = pick_product(
        catalog,
        specialization=specialization,
        tier=t,
        product_id=preferred,
    )
    # If specialization map lists products, re-rank among that subset
    if spec_profile and not product_id:
        allowed = {
            str(x) for x in (spec_profile.get("products") or []) if x
        }
        if allowed:
            subset = [p for p in catalog.products if p.product_id in allowed]
            if subset:
                product = max(
                    subset,
                    key=lambda p: score_product(
                        p, specialization=specialization, tier=t
                    ),
                )

    match_score = score_product(product, specialization=specialization, tier=t)

    label = product.label_de if locale.lower().startswith("de") else product.label_en
    # Message accent from map (first resolved message)
    if spec_profile and spec_profile.get("messages_resolved"):
        msg0 = spec_profile["messages_resolved"][0]
        if locale.lower().startswith("de") and msg0.get("de"):
            label = str(msg0["de"])
        elif msg0.get("en"):
            label = str(msg0["en"])

    preview_rel = product.preview_rel or catalog.preview_rel
    model_rel = product.model_rel

    cta = (spec_profile or {}).get("cta_resolved") or {"id": "contact"}
    hotspots = list((spec_profile or {}).get("hotspots") or product.hotspots)[:4]

    base = {
        "ok": True,
        "engine": ENGINE_ID,
        "engine_label": ENGINE_LABEL,
        "component": ENGINE_ID,
        "never_empty": True,
        "tier": t,
        "niche_id": catalog.niche_id,
        "requested_niche": canonicalize_niche(niche_id) if niche_id else catalog.niche_id,
        "alias": catalog.resolved_via_alias,
        "fallback_generic": fallback_used,
        "product_id": product.product_id,
        "scene_id": product.product_id,  # back-compat
        "product_score": product.score,
        "match_score": round(match_score, 2),
        "premium_product": product.premium,
        "specializations": list(product.specializations),
        "scene_tags": list(product.tags),
        "label_de": product.label_de,
        "label_en": product.label_en,
        "label": label,
        "sub_de": catalog.sub_de,
        "sub_en": catalog.sub_en,
        "quality": product.quality if product.quality != "placeholder" else catalog.quality,
        "preview": preview_rel,
        "model": None,
        "hotspots": hotspots,
        "cta": cta,
        "specialization_id": (spec_profile or {}).get("id"),
        "messages": list((spec_profile or {}).get("messages_resolved") or []),
        "library_path": product.folder_rel,
        "products_available": [p.product_id for p in catalog.products],
    }

    if t == "basic":
        return {**base, "mode": "none", "reason": "basic_no_visual_experience"}

    if t == "business":
        mode: DeliveryMode = "preview" if preview_rel else "css_motion"
        return {
            **base,
            "mode": mode,
            "reason": "business_preview" if preview_rel else "business_css_motion",
        }

    if product.allows_interactive_3d and model_rel:
        return {
            **base,
            "mode": "interactive_3d",
            "model": model_rel,
            "preview": preview_rel,
            "reason": "premium_approved_product",
        }

    if preview_rel:
        return {
            **base,
            "mode": "preview",
            "reason": "premium_awaiting_approved_model",
        }

    return {
        **base,
        "mode": "css_motion",
        "reason": "premium_css_motion_no_preview",
    }


def resolve_showcase_delivery(
    *,
    niche_id: str | None,
    tier: str | None = "premium",
    specialization: str | None = None,
    locale: str = "de",
) -> dict[str, Any]:
    """Back-compat wrapper → Visual Experience delivery."""
    return resolve_visual_experience(
        niche_id=niche_id,
        tier=tier,
        specialization=specialization,
        locale=locale,
    )


def build_showcase_embed_config(
    *,
    niche_id: str | None,
    tier: str | None = "premium",
    specialization: str | None = None,
    locale: str = "de",
) -> dict[str, Any]:
    return resolve_visual_experience(
        niche_id=niche_id,
        tier=tier,
        specialization=specialization,
        locale=locale,
    )


def build_visual_experience_config(
    *,
    niche_id: str | None,
    tier: str | None = "premium",
    specialization: str | None = None,
    product_id: str | None = None,
    locale: str = "de",
) -> dict[str, Any]:
    return resolve_visual_experience(
        niche_id=niche_id,
        tier=tier,
        specialization=specialization,
        product_id=product_id,
        locale=locale,
    )


def load_showcase_index() -> dict[str, Any]:
    if not _INDEX.is_file():
        return {"version": 0, "niches": {}}
    return _read_json(_INDEX)


def load_library_manifest() -> dict[str, Any]:
    data = _read_json(_LIBRARY)
    if data:
        return data
    return rebuild_library_manifest()


def rebuild_library_manifest() -> dict[str, Any]:
    niches = []
    index_niches: dict[str, Any] = {}
    all_products: list[dict[str, Any]] = []

    for niche_id in list_showcase_niches():
        catalog = resolve_niche_catalog(niche_id)
        if not catalog:
            continue
        niches.append(
            {
                "niche_id": niche_id,
                "label_de": catalog.label_de,
                "label_en": catalog.label_en,
                "quality": catalog.quality,
                "client_facing_3d": catalog.client_facing_3d,
                "has_preview": bool(catalog.preview_rel),
                "has_model": bool(catalog.model_rel),
                "product_count": len(catalog.products),
                "scene_count": len(catalog.products),
                "products": [p.product_id for p in catalog.products],
                "path": f"showcases/{niche_id}",
                "preview": catalog.preview_rel,
                "model": catalog.model_rel,
            }
        )
        index_niches[niche_id] = {
            "niche": niche_id,
            "quality": catalog.quality,
            "client_facing_3d": catalog.client_facing_3d,
            "path": f"showcases/{niche_id}",
            "products": [p.product_id for p in catalog.products],
            "label_de": catalog.label_de,
            "label_en": catalog.label_en,
        }
        for p in catalog.products:
            all_products.append(
                {
                    "niche_id": niche_id,
                    "product_id": p.product_id,
                    "score": p.score,
                    "premium": p.premium,
                    "specializations": list(p.specializations),
                    "quality": p.quality,
                    "path": p.folder_rel,
                }
            )

    manifest = {
        "version": 2,
        "engine": ENGINE_ID,
        "engine_label": ENGINE_LABEL,
        "aliases": dict(NICHE_ALIASES),
        "niches": niches,
        "rule": (
            "Add showcases/<niche>/products/<product>/ with product.json — "
            "no platform code change"
        ),
        "player": "runtime/showcase/index.html?niche=<id>&tier=premium",
    }
    _LIBRARY_ROOT.mkdir(parents=True, exist_ok=True)
    _LIBRARY.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _INDEX.write_text(
        json.dumps({"version": 3, "engine": ENGINE_ID, "niches": index_niches}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    _PRODUCTS_MANIFEST.write_text(
        json.dumps(
            {"version": 1, "engine": ENGINE_ID, "products": all_products},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def ensure_product_tree_example(niche_id: str, products: list[dict[str, Any]]) -> None:
    """Create products/<id>/product.json (+ copy niche preview once). Helper for bootstrap."""
    niche = canonicalize_niche(niche_id)
    niche_dir = _LIBRARY_ROOT / niche
    products_dir = niche_dir / "products"
    products_dir.mkdir(parents=True, exist_ok=True)
    niche_preview = _find_preview(niche_dir)
    niche_model = _find_model(niche_dir)

    for spec in products:
        pid = str(spec["id"])
        pdir = products_dir / pid
        pdir.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": pid,
            "score": int(spec.get("score", 80)),
            "premium": bool(spec.get("premium", True)),
            "specializations": list(spec.get("specializations") or []),
            "tags": list(spec.get("tags") or []),
            "label_de": spec.get("label_de") or pid,
            "label_en": spec.get("label_en") or pid,
            "quality": spec.get("quality") or "placeholder",
            "client_facing_3d": bool(spec.get("client_facing_3d", False)),
            "inherit_model": True,
        }
        (pdir / "product.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        # Copy still into primary product so nested path is self-contained
        if niche_preview and not _find_preview(pdir):
            dest = pdir / niche_preview.name
            if not dest.is_file():
                shutil.copy2(niche_preview, dest)
        if (
            bool(spec.get("copy_model"))
            and niche_model
            and not (pdir / "model.glb").is_file()
        ):
            shutil.copy2(niche_model, pdir / "model.glb")
        hs = pdir / "hotspots.json"
        if not hs.is_file():
            hs.write_text(
                json.dumps(
                    {"version": 1, "product_id": pid, "hotspots": []},
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
