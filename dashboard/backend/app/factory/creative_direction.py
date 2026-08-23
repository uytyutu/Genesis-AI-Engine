"""Creative Direction brief for Factory media + WebGL."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Heavy WebGL only when it amplifies the niche (Studio Renderer 2.0).
# Psychology / coaching → cinematic photo, not WebGL.
_WEBGL_NICHES = frozenset({
    "auto", "detailing", "auto_detailing", "furniture",
    "jewelry", "energy", "solar", "car_dealership",
    "architecture", "immobilien",
})

_MEDIA_BY_NICHE = {
    "auto": "industrial_craft",
    "auto_detailing": "showroom_gloss",
    "detailing": "showroom_gloss",
    "car_dealership": "showroom_gloss",
    "dental": "clinical_clean",
    "orthodontics": "clinical_clean",
    "psychology": "editorial_soft",
    "family_psychology": "editorial_soft",
    "furniture": "atelier_warm",
    "jewelry": "glass_3d",
    "energy": "tech_energy",
    "elektro": "industrial_craft",
    "sanitaer": "industrial_craft",
    "maler": "atelier_warm",
    "handwerk": "industrial_craft",
}


@dataclass(frozen=True)
class CreativeBrief:
    brand_name: str
    niche_id: str
    package_id: str
    media_mode: str
    visual_metaphor: str
    hero_concept: str
    motion_language: str
    recommends_webgl: bool
    experience_tier: str
    fingerprint: str
    image_prompt: str = ""
    offline_media: bool = False

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["director"] = "creative_direction_v1"
        return d

    def to_image_prompt(self, *, brand_name: str = "", niche_id: str = "") -> str:
        if self.image_prompt.strip():
            return self.image_prompt.strip()
        name = brand_name or self.brand_name
        niche = niche_id or self.niche_id
        return (
            f"Premium European brand visual for {name} ({niche}). "
            f"Mode={self.media_mode}. Metaphor={self.visual_metaphor}. "
            f"Hero={self.hero_concept}."
        )


def recommends_webgl_3d(niche_id: str | None, package_id: str | None = None) -> bool:
    niche = (niche_id or "").strip().lower().replace("-", "_")
    pkg = (package_id or "").strip().lower()
    if pkg in ("basic", "business", "standalone"):
        return False
    try:
        from app.factory.studio_renderer_v2 import decide_webgl

        return decide_webgl(niche, pkg).enabled
    except Exception:
        return niche in _WEBGL_NICHES


def _metaphor(niche_id: str) -> str:
    return {
        "auto": "Lift and precise mechanics",
        "auto_detailing": "Mirror gloss under studio light",
        "dental": "Bright precision clinic",
        "orthodontics": "Gentle arc to a smile",
        "furniture": "Calm living volumes",
        "jewelry": "Light on a ring",
        "energy": "Panels catching sky",
        "car_dealership": "Showroom key handover",
        "elektro": "Clean electrical install",
        "sanitaer": "Water and precise fittings",
        "maler": "Paint plane and brush",
        "family_psychology": "Warm family room",
        "psychology": "Still and safe",
    }.get((niche_id or "").lower(), "Brand character in space")


def invent_creative_brief(
    *,
    brand_name: str,
    niche_id: str,
    package_id: str = "business",
    diversity_salt: str = "",
    city: str = "",
    offline_media: bool | None = None,
) -> CreativeBrief:
    from app.factory.visual_brand_system import image_provider_configured

    niche = (niche_id or "generic").strip().lower() or "generic"
    pkg = (package_id or "business").strip().lower() or "business"
    mode = _MEDIA_BY_NICHE.get(niche, "cinematic_photo")
    metaphor = _metaphor(niche)
    webgl = recommends_webgl_3d(niche, "premium") if pkg in ("premium", "connected") else False
    experience = (
        "cinematic" if pkg in ("premium", "connected")
        else "rich" if pkg == "business" else "soft"
    )
    motion = {
        "cinematic": "parallax magnetic CTA scroll reveal soft tilt",
        "rich": "reveal gentle parallax card tilt",
        "soft": "fade reveal calm hover",
    }[experience]
    hero = f"{metaphor} | {brand_name}"
    if city:
        hero = f"{hero} | {city}"
    offline = (
        bool(offline_media) if offline_media is not None
        else (pkg in ("premium", "connected") and not image_provider_configured())
    )
    prompt = (
        f"{brand_name} {niche} brand hero, {metaphor}, European studio, "
        f"media_mode={mode}, cinematic lighting"
    )
    fp = hashlib.sha256(
        f"{brand_name}|{niche}|{pkg}|{mode}|{diversity_salt}|{webgl}".encode()
    ).hexdigest()[:20]
    return CreativeBrief(
        brand_name=brand_name or "Virtus Company",
        niche_id=niche,
        package_id=pkg,
        media_mode=mode,
        visual_metaphor=metaphor,
        hero_concept=hero,
        motion_language=motion,
        recommends_webgl=webgl,
        experience_tier=experience,
        fingerprint=fp,
        image_prompt=prompt,
        offline_media=offline,
    )


def persist_creative_brief(product_dir: Path | str, brief: CreativeBrief) -> Path:
    path = Path(product_dir) / "CREATIVE_BRIEF.json"
    path.write_text(
        json.dumps(brief.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load_creative_brief(product_dir: Path | str) -> CreativeBrief | None:
    path = Path(product_dir) / "CREATIVE_BRIEF.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return CreativeBrief(
            brand_name=str(data.get("brand_name") or ""),
            niche_id=str(data.get("niche_id") or "generic"),
            package_id=str(data.get("package_id") or "business"),
            media_mode=str(data.get("media_mode") or "cinematic_photo"),
            visual_metaphor=str(data.get("visual_metaphor") or ""),
            hero_concept=str(data.get("hero_concept") or ""),
            motion_language=str(data.get("motion_language") or ""),
            recommends_webgl=bool(data.get("recommends_webgl")),
            experience_tier=str(data.get("experience_tier") or "soft"),
            fingerprint=str(data.get("fingerprint") or ""),
            image_prompt=str(data.get("image_prompt") or ""),
            offline_media=bool(data.get("offline_media")),
        )
    except (TypeError, ValueError):
        return None


__all__ = [
    "CreativeBrief",
    "invent_creative_brief",
    "load_creative_brief",
    "persist_creative_brief",
    "recommends_webgl_3d",
]
