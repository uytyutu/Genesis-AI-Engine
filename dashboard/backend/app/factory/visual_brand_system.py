"""Per-company Visual Brand System — not «a picture for a section».

Virtus Core Factory must invent a visual brand for each digital company:
  photos · illustrations · 3D accents · gradients · motion · icons · color system

Law: two companies must not share the same Hero / Gallery / Background language.
Pillow remains offline fallback; Image Provider is preferred when configured.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

VisualMedium = Literal[
    "cinematic_photo",
    "editorial_photo",
    "isometric_illustration",
    "glass_3d",
    "abstract_gradient",
    "neon_line",
    "minimal_illustration",
    "premium_business_graphic",
]

Role = Literal[
    "hero",
    "hero_background",
    "gallery",
    "before_after",
    "team",
    "equipment",
    "projects",
    "illustration",
    "icon",
    "video_storyboard",
]


# Niche → scene library (German craft / commerce). Never café-generic.
_SCENE_LIBRARIES: dict[str, dict[str, tuple[str, ...]]] = {
    "auto": {
        "hero": (
            "moderne Kfz-Werkstatt abends",
            "Mechaniker an BMW / Audi / Mercedes",
            "Diagnosegerät und Hebebühne",
            "Werkzeuge und Funken, warmes Arbeitslicht",
        ),
        "gallery": (
            "Motorwechsel",
            "Computerdiagnose",
            "Bremsenreparatur",
            "Fahrzeugelektrik",
            "Reifenwechsel",
            "Fahrzeugübergabe an Kunden",
        ),
        "before_after": ("verschmutzter Motorraum", "sauber diagnostizierter Motorraum"),
        "team": ("Meister in Overall", "Diagnose-Techniker"),
        "equipment": ("Hebebühne", "OBD-Diagnose", "Drehmomentschlüssel"),
    },
    "auto_detailing": {
        "hero": (
            "Premium-Detailing-Studio",
            "Lackpolitur unter LED",
            "schwarzer Sportwagen, Spiegelglanz",
            "Keramikversiegelung, Dunst und Glanz",
        ),
        "gallery": (
            "Lackkorrektur",
            "Innenraumreinigung",
            "Felgenpflege",
            "Scheibenversiegelung",
            "Vorher/Nachher Lack",
            "Keramikbeschichtung",
        ),
        "before_after": ("matte Lackfläche", "Hochglanz nach Politur"),
        "team": ("Detailer mit Poliermaschine",),
        "equipment": ("Poliermaschine", "Dampfreiniger", "Keramik-Set"),
    },
    "auto_parts": {
        "hero": ("Ersatzteilregale", "Bremsenscheiben und Öle", "Katalog und Theke"),
        "gallery": ("Ölflaschen", "Filterwand", "Bremsenregal", "Kundenberatung an Theke"),
        "team": ("Fachverkäufer am Regal",),
        "equipment": ("Regalwagen", "Teilekatalog"),
    },
    "car_dealership": {
        "hero": ("heller Autosalon", "Neuwagen Ausstellung", "Schlüsselübergabe"),
        "gallery": ("Showroom", "Probefahrt", "Beratungstisch", "Auslieferung"),
        "team": ("Verkaufsberater", "Auslieferungs-Team"),
        "equipment": ("Showroom-Beleuchtung", "Tablet-Konfigurator"),
    },
    "dental": {
        "hero": ("helle Praxis", "Behandlungsstuhl", "sterile Instrumente", "Röntgenmonitor"),
        "gallery": ("Prophylaxe", "Digitale Aufnahme", "Team in Praxis", "Wartezimmer Ruhe"),
        "team": ("Zahnarzt mit Patient", "Prophylaxe-Assistentin"),
        "equipment": ("Behandlungseinheit", "Intraoralkamera"),
    },
    "orthodontics": {
        "hero": ("kieferorthopädische Praxis", "Aligner und Scan", "Jugendlicher Patient lächelnd"),
        "gallery": ("3D-Scan", "Aligner-Set", "Kontrolltermin", "Vorher/Nachher Lächeln"),
        "before_after": ("Zahnstellung vorher", "harmonisches Lächeln nachher"),
        "team": ("Kieferorthopäde", "Assistenz"),
        "equipment": ("Intraoralscanner", "Aligner-Schienen"),
    },
    "psychology": {
        "hero": ("behagliches Therapiezimmer", "Tageslicht", "Sessel und Pflanze", "ruhige Atmosphäre"),
        "gallery": ("Gesprächsecke", "Notizbuch", "Fensterlicht", "Warteraum dezent"),
        "team": ("Therapeut im Gespräch",),
        "equipment": ("Sesselpaar", "leises Ambiente"),
    },
    "family_psychology": {
        "hero": ("Familienraum warm", "zwei Sessel und Kinderecke dezent", "weiches Licht"),
        "gallery": ("Paargespräch", "Elternberatung", "Ruheecke"),
        "team": ("Systemische Therapeutin",),
        "equipment": ("runde Gesprächsrunde",),
    },
    "cleaning": {
        "hero": ("Professionelles Reinigungsteam", "Fensterputz an Glasfassade", "Wohnung nach Pflege"),
        "gallery": ("Büroreinigung", "Fensterfront", "Bodenpflege", "Desinfektion"),
        "before_after": ("Büro vor Reinigung", "Büro nach Reinigung"),
        "team": ("Team in einheitlicher Kleidung",),
        "equipment": ("Poliermaschine", "Teleskopstange"),
    },
    "office_cleaning": {
        "hero": ("leeres Büro abends, Team bei Glasreinigung", "Open-Space nach Pflege"),
        "gallery": ("Sanitärbereich", "Küche Büro", "Schreibtischzonen"),
        "team": ("Facility-Team",),
        "equipment": ("Industrie-Staubsauger",),
    },
    "handwerk": {
        "hero": ("Baustelle innen", "Fliesenverlegung", "Handwerker in Arbeitskleidung"),
        "gallery": ("Bodenverlegung", "Küchenmontage", "Treppenbau", "Werkzeugwand"),
        "team": ("Meister und Geselle",),
        "equipment": ("Laser-Nivelliergerät", "Werkzeugkoffer"),
    },
    "fitness": {
        "hero": ("moderner Gym-Floor", "Hantelzone", "Personal Training"),
        "gallery": ("Kraftbereich", "Cardio", "Stretching-Zone", "Trainer und Kunde"),
        "team": ("Personal Trainer",),
        "equipment": ("Hantelständer", "Rack"),
    },
    "law": {
        "hero": ("ruhiges Anwaltsbüro", "Akten und Stadtblick", "Verhandlungstisch"),
        "gallery": ("Beratung", "Dokumente", "Bibliothek", "Empfang"),
        "team": ("Anwalt im Gespräch",),
        "equipment": ("Aktenordner", "Konferenzraum"),
    },
    "photography": {
        "hero": ("Fotostudio Softbox", "Porträtsession", "Kamera und Lichtsetup"),
        "gallery": ("Produktsetup", "Outdoor-Session", "Retusche-Arbeitsplatz"),
        "team": ("Fotograf hinter Kamera",),
        "equipment": ("Softbox", "Blitzanlage"),
    },
    "computer": {
        "hero": ("IT-Werkbank", "geöffneter Laptop", "Diagnose-Monitor"),
        "gallery": ("Mainboard-Reparatur", "Datenrettung", "Kundenübergabe Notebook"),
        "team": ("Techniker mit ESD-Armband",),
        "equipment": ("Lötkolbenstation", "Diagnose-PC"),
    },
    "it_support": {
        "hero": ("Remote-Support Setup", "Server-Rack und Notebook", "Klarheit im Chaos der Kabel"),
        "gallery": ("Netzwerkverkabelung", "Backup-Station", "Helpdesk"),
        "team": ("IT-Support Engineer",),
        "equipment": ("Switch", "KVM"),
    },
    "elektro": {
        "hero": ("Elektroinstallation", "Sicherungskasten", "Fachkraft mit Messgerät"),
        "gallery": ("Leitungsverlegung", "Smart-Home Panel", "Messung"),
        "team": ("Elektriker",),
        "equipment": ("Multimeter", "Leitungszieher"),
    },
    "sanitaer": {
        "hero": ("moderne Badbaustelle", "Rohrleitung", "Sanitär-Meister"),
        "gallery": ("Armaturenmontage", "Heizung", "Wasserschaden-Diagnose"),
        "team": ("Sanitär-Team",),
        "equipment": ("Presszange", "Rohrabschneider"),
    },
    "energy": {
        "hero": ("Photovoltaik auf Dach", "Wechselrichter", "Haus mit Solar"),
        "gallery": ("Modulmontage", "Monitoring-App", "Speicherbatterie"),
        "team": ("Solar-Techniker",),
        "equipment": ("Module", "Wechselrichter"),
    },
    "gartenpflege": {
        "hero": ("gepflegter Garten Morgenlicht", "Hecke und Rasen", "Gärtner bei Arbeit"),
        "gallery": ("Rasenschnitt", "Beetpflege", "Baumschnitt"),
        "team": ("Gärtner-Team",),
        "equipment": ("Heckenschere", "Rasenmäher"),
    },
    "landschaft": {
        "hero": ("Landschaftsarchitektur Entwurf", "Natursteinweg", "Abendlicht Garten"),
        "gallery": ("Terassenbau", "Wasserlauf", "Bepflanzung"),
        "team": ("Landschaftsgärtner",),
        "equipment": ("Naturstein", "Pflanzplan"),
    },
}

_MEDIUM_SETS: tuple[tuple[VisualMedium, ...], ...] = (
    ("cinematic_photo", "glass_3d", "abstract_gradient", "neon_line"),
    ("editorial_photo", "minimal_illustration", "abstract_gradient", "premium_business_graphic"),
    ("cinematic_photo", "isometric_illustration", "glass_3d", "abstract_gradient"),
    ("editorial_photo", "neon_line", "glass_3d", "minimal_illustration"),
    ("cinematic_photo", "premium_business_graphic", "abstract_gradient", "isometric_illustration"),
)

_ILLUSTRATION_PACKS = (
    "isometric craft marks",
    "glassmorphism panels",
    "soft 3D product icons",
    "abstract gradient orbs",
    "motion shape ribbons",
    "neon line diagrams",
    "minimal line illustrations",
    "premium business geometry",
)

_MOTION_LANGS = (
    "cinematic parallax · soft reveal · magnetic CTA",
    "editorial fade · staggered cards · calm hover",
    "kinetic micro-motion · glow pulse · scroll scenes",
    "atelier drift · glass shimmer · slow depth",
    "industrial snap · sharp transitions · tool hover",
)


@dataclass(frozen=True)
class ColorSystem:
    primary: str
    accent: str
    secondary: str
    surface: str
    cards: str
    background: str
    gradient: str
    glow: str
    ink: str
    muted: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class VisualBrand:
    """Unique visual identity for one company generation."""

    brand_name: str
    niche_id: str
    fingerprint: str
    color: ColorSystem
    media_mix: tuple[VisualMedium, ...]
    illustration_pack: str
    motion_language: str
    icon_style: str
    scene_library: dict[str, tuple[str, ...]]
    prompts: dict[str, str] = field(default_factory=dict)
    uniqueness_rules: tuple[str, ...] = (
        "No repeated Hero across companies",
        "No stock café/salon plates",
        "Gallery proves this profession only",
        "Colors + motion + illustration unique to this brand",
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "brand_name": self.brand_name,
            "niche_id": self.niche_id,
            "fingerprint": self.fingerprint,
            "color": self.color.as_dict(),
            "media_mix": list(self.media_mix),
            "illustration_pack": self.illustration_pack,
            "motion_language": self.motion_language,
            "icon_style": self.icon_style,
            "scene_library": {k: list(v) for k, v in self.scene_library.items()},
            "prompts": dict(self.prompts),
            "uniqueness_rules": list(self.uniqueness_rules),
        }


def _digest(*parts: str) -> bytes:
    return hashlib.sha256("|".join(p for p in parts if p).encode("utf-8")).digest()


def _hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def invent_color_system(
    *,
    niche_id: str,
    brand_name: str,
    diversity_salt: str = "",
    base_accent: str | None = None,
) -> ColorSystem:
    """Per-company palette — not a single primary swap."""
    dig = _digest(niche_id, brand_name, diversity_salt, "color")
    niche_bias = {
        "auto": (18, 22, 28, 220, 50, 45),
        "auto_detailing": (8, 10, 14, 200, 170, 80),
        "dental": (236, 244, 248, 40, 140, 180),
        "orthodontics": (244, 250, 252, 60, 160, 170),
        "psychology": (240, 236, 228, 90, 120, 110),
        "family_psychology": (246, 240, 232, 140, 110, 90),
        "cleaning": (236, 244, 250, 30, 140, 190),
        "office_cleaning": (230, 238, 246, 40, 110, 160),
        "photography": (16, 16, 20, 230, 90, 70),
        "computer": (10, 14, 28, 60, 130, 255),
        "it_support": (12, 18, 32, 40, 200, 180),
        "fitness": (10, 10, 14, 255, 70, 50),
        "law": (248, 246, 240, 55, 55, 62),
        "handwerk": (28, 18, 10, 240, 150, 30),
        "energy": (8, 28, 34, 250, 190, 40),
        "elektro": (10, 12, 30, 255, 210, 50),
        "sanitaer": (14, 30, 40, 50, 160, 200),
        "gartenpflege": (10, 36, 22, 70, 170, 90),
        "landschaft": (14, 40, 28, 90, 150, 80),
    }.get(niche_id, (20, 24, 30, 50 + dig[0] % 120, 140 + dig[1] % 80, 160 + dig[2] % 60))

    bg_r, bg_g, bg_b, ac_r, ac_g, ac_b = niche_bias
    ac_r = (ac_r + dig[3] % 40 - 15) % 256
    ac_g = (ac_g + dig[4] % 40 - 15) % 256
    ac_b = (ac_b + dig[5] % 40 - 15) % 256
    if base_accent and base_accent.startswith("#") and len(base_accent) >= 7:
        try:
            ac_r, ac_g, ac_b = (
                int(base_accent[1:3], 16),
                int(base_accent[3:5], 16),
                int(base_accent[5:7], 16),
            )
        except ValueError:
            pass

    primary = _hex(bg_r, bg_g, bg_b) if (bg_r + bg_g + bg_b) < 200 else _hex(
        max(20, bg_r - 180), max(20, bg_g - 180), max(20, bg_b - 180)
    )
    accent = _hex(ac_r, ac_g, ac_b)
    secondary = _hex((ac_r + 40) % 200 + 30, (ac_g + 20) % 180 + 40, (ac_b + 60) % 200 + 20)
    surface = _hex(min(255, bg_r + 210), min(255, bg_g + 210), min(255, bg_b + 210))
    if (bg_r + bg_g + bg_b) > 500:
        surface = _hex(bg_r, bg_g, bg_b)
        primary = _hex(max(10, bg_r - 200), max(10, bg_g - 200), max(10, bg_b - 200))
    sr = int(surface[1:3], 16)
    sg = int(surface[3:5], 16)
    sb = int(surface[5:7], 16)
    cards = _hex(max(0, sr - 6), max(0, sg - 4), max(0, sb - 2))
    background = surface if (bg_r + bg_g + bg_b) > 400 else primary
    gradient = (
        f"linear-gradient(145deg,{primary} 0%,{_hex(ac_r // 2, ac_g // 2, ac_b // 2)} 48%,"
        f"{accent} 100%)"
    )
    glow = f"rgba({ac_r},{ac_g},{ac_b},0.35)"
    ink = "#0b0d10" if (bg_r + bg_g + bg_b) > 400 else "#f4f6f8"
    muted = "#64748b" if ink.startswith("#0") else "#94a3b8"
    return ColorSystem(
        primary=primary,
        accent=accent,
        secondary=secondary,
        surface=surface,
        cards=cards,
        background=background,
        gradient=gradient,
        glow=glow,
        ink=ink,
        muted=muted,
    )


def scene_library_for(niche_id: str) -> dict[str, tuple[str, ...]]:
    key = (niche_id or "generic").strip().lower()
    if key in _SCENE_LIBRARIES:
        return dict(_SCENE_LIBRARIES[key])
    aliases = {
        "detailing": "auto_detailing",
        "autodetailing": "auto_detailing",
        "parts": "auto_parts",
        "dealership": "car_dealership",
        "autohaus": "car_dealership",
        "ortho": "orthodontics",
        "it": "computer",
        "laptop": "computer",
        "solar": "energy",
        "photovoltaik": "energy",
        "landscape": "landschaft",
        "familientherapie": "family_psychology",
    }
    mapped = aliases.get(key.replace(" ", "").replace("_", ""))
    if mapped and mapped in _SCENE_LIBRARIES:
        return dict(_SCENE_LIBRARIES[mapped])
    return {
        "hero": ("professioneller Arbeitsort", "Team bei echter Arbeit", "deutsche Alltagsszene"),
        "gallery": ("Detail Arbeit", "Kundenmoment", "Werkzeug / Material", "Ergebnis"),
        "team": ("Fachkraft",),
        "equipment": ("Werkzeug der Branche",),
    }


def build_image_prompt(
    *,
    role: Role | str,
    brand_name: str,
    niche_id: str,
    scenes: tuple[str, ...],
    medium: VisualMedium,
    illustration_pack: str,
    must_forbid: tuple[str, ...] = (),
    city: str = "",
) -> str:
    scene_line = ", ".join(scenes[:4]) if scenes else niche_id
    forbid = (
        ", ".join(must_forbid[:6])
        or "generic stock café, salon spa, SaaS dashboard, purple gradient cliché"
    )
    city_bit = f" in {city}" if city else " in Germany"
    return (
        f"Premium German brand visual for «{brand_name}» ({niche_id}){city_bit}. "
        f"Role={role}. Medium={medium}. Illustration language={illustration_pack}. "
        f"Must show: {scene_line}. "
        f"Cinematic lighting, European digital-studio quality, unique to this company. "
        f"Forbidden: {forbid}, repeated template look, watermark, text overlays."
    )


def invent_visual_brand(
    *,
    brand_name: str,
    niche_id: str,
    diversity_salt: str = "",
    city: str = "",
    base_accent: str | None = None,
    forbidden: tuple[str, ...] = (),
) -> VisualBrand:
    dig = _digest(brand_name, niche_id, diversity_salt, city)
    mix = _MEDIUM_SETS[dig[0] % len(_MEDIUM_SETS)]
    ill = _ILLUSTRATION_PACKS[dig[1] % len(_ILLUSTRATION_PACKS)]
    motion = _MOTION_LANGS[dig[2] % len(_MOTION_LANGS)]
    icons = (
        "line geometric marks",
        "filled craft glyphs",
        "soft rounded symbols",
        "technical blueprint icons",
        "minimal stroke set",
    )[dig[3] % 5]
    colors = invent_color_system(
        niche_id=niche_id,
        brand_name=brand_name,
        diversity_salt=diversity_salt,
        base_accent=base_accent,
    )
    scenes = scene_library_for(niche_id)
    hero_scenes = list(scenes.get("hero") or ())
    if hero_scenes and dig[4] % 2 == 0:
        hero_scenes = hero_scenes[1:] + hero_scenes[:1]
    scenes["hero"] = tuple(hero_scenes)

    prompts: dict[str, str] = {}
    role_map: list[tuple[str, str, tuple[str, ...]]] = [
        ("hero", mix[0], scenes.get("hero", ())),
        ("hero_background", mix[2] if len(mix) > 2 else mix[0], scenes.get("hero", ())),
        ("gallery", mix[0], scenes.get("gallery", ())),
        ("before_after", mix[0], scenes.get("before_after", scenes.get("gallery", ())[:2])),
        ("team", mix[1] if len(mix) > 1 else mix[0], scenes.get("team", ())),
        ("equipment", mix[1] if len(mix) > 1 else mix[0], scenes.get("equipment", ())),
        ("projects", mix[0], scenes.get("gallery", ())[2:6] or scenes.get("gallery", ())),
        (
            "illustration",
            mix[1] if len(mix) > 1 else "minimal_illustration",
            scenes.get("hero", ())[:2],
        ),
        ("icon", "minimal_illustration", (icons,)),
        ("video_storyboard", mix[0], scenes.get("hero", ())[:3]),
    ]
    for role, medium, sc in role_map:
        prompts[role] = build_image_prompt(
            role=role,  # type: ignore[arg-type]
            brand_name=brand_name,
            niche_id=niche_id,
            scenes=sc,
            medium=medium,  # type: ignore[arg-type]
            illustration_pack=ill,
            must_forbid=forbidden,
            city=city,
        )

    fp = hashlib.sha256(
        f"{brand_name}|{niche_id}|{diversity_salt}|{colors.accent}|{ill}|{motion}".encode()
    ).hexdigest()[:20]

    return VisualBrand(
        brand_name=brand_name,
        niche_id=niche_id,
        fingerprint=fp,
        color=colors,
        media_mix=mix,
        illustration_pack=ill,
        motion_language=motion,
        icon_style=icons,
        scene_library=scenes,
        prompts=prompts,
    )


# Last provider that successfully wrote an image (or resolved offline).
_LAST_IMAGE_PROVIDER: dict[str, Any] = {
    "provider": "studio_offline",
    "label": "Studio Offline Media",
}


def last_image_provider() -> dict[str, Any]:
    return dict(_LAST_IMAGE_PROVIDER)


def resolve_image_provider() -> dict[str, Any]:
    """Probe image backends in preference order. Always returns a usable fallback.

    Order: VIRTUS_IMAGE_API_URL → OPENAI → FAL → HF → studio_offline (Pillow).
    Never asks the client to paste keys — Factory auto-chains silently.
    """
    chain: list[dict[str, Any]] = []

    custom = (os.environ.get("VIRTUS_IMAGE_API_URL") or "").strip()
    if custom:
        chain.append(
            {
                "provider": "virtus_image_api",
                "label": "Virtus Image API",
                "configured": True,
                "endpoint": custom,
            }
        )

    if (os.environ.get("OPENAI_API_KEY") or "").strip():
        chain.append(
            {
                "provider": "openai",
                "label": "OpenAI Images",
                "configured": True,
                "model": os.environ.get("VIRTUS_OPENAI_IMAGE_MODEL") or "dall-e-3",
            }
        )

    fal = (os.environ.get("FAL_KEY") or "").strip()
    if fal:
        # fal.ai REST is usable via fal.run + Key auth — keep in chain.
        chain.append(
            {
                "provider": "fal",
                "label": "fal.ai",
                "configured": True,
                "endpoint": "https://fal.run/fal-ai/flux/schnell",
            }
        )

    hf = (
        os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_TOKEN") or ""
    ).strip()
    if hf:
        chain.append(
            {
                "provider": "huggingface",
                "label": "Hugging Face Inference",
                "configured": True,
                "model": os.environ.get("VIRTUS_HF_IMAGE_MODEL")
                or "black-forest-labs/FLUX.1-schnell",
            }
        )

    offline = {
        "provider": "studio_offline",
        "label": "Studio Offline Media",
        "configured": True,
        "note": "Pillow niche scenes — last resort, no client key prompt",
    }
    chain.append(offline)

    primary = chain[0]
    return {
        "provider": primary["provider"],
        "label": primary["label"],
        "configured": True,
        "remote": primary["provider"] != "studio_offline",
        "chain": [c["provider"] for c in chain],
        "primary": primary,
        "note": primary.get("note")
        or f"Using {primary['label']} (auto-chain)",
    }


def image_provider_configured() -> bool:
    """True when a remote Image Provider is available (not Pillow-only)."""
    return bool(resolve_image_provider().get("remote"))


def _ok_image(dest: Path) -> bool:
    return dest.is_file() and dest.stat().st_size > 800


def _download_url(url: str, dest: Path, *, timeout: int = 90) -> bool:
    if not url.startswith("http"):
        return False
    with urllib.request.urlopen(url, timeout=timeout) as img_resp:
        dest.write_bytes(img_resp.read())
    return _ok_image(dest)


def _try_virtus_image_api(prompt: str, dest: Path, *, size: tuple[int, int]) -> bool:
    custom = (os.environ.get("VIRTUS_IMAGE_API_URL") or "").strip()
    if not custom:
        return False
    payload = json.dumps(
        {"prompt": prompt[:1800], "width": size[0], "height": size[1]}
    ).encode("utf-8")
    req = urllib.request.Request(
        custom,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "VirtusCore-Factory/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = resp.read()
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "image/" in ctype:
            dest.write_bytes(body)
            return _ok_image(dest)
        data = json.loads(body.decode("utf-8", errors="ignore") or "{}")
        url = str(data.get("url") or data.get("image_url") or "")
        return _download_url(url, dest)


def _try_openai_images(prompt: str, dest: Path, *, size: tuple[int, int]) -> bool:
    oai = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not oai:
        return False
    payload = json.dumps(
        {
            "model": os.environ.get("VIRTUS_OPENAI_IMAGE_MODEL") or "dall-e-3",
            "prompt": prompt[:1800],
            "n": 1,
            "size": "1792x1024" if size[0] >= size[1] else "1024x1792",
            "response_format": "url",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {oai}",
            "User-Agent": "VirtusCore-Factory/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        url = str(((data.get("data") or [{}])[0]).get("url") or "")
        return _download_url(url, dest)


def _try_fal_images(prompt: str, dest: Path, *, size: tuple[int, int]) -> bool:
    """fal.ai REST (flux/schnell). Skip silently if key/API unavailable."""
    fal = (os.environ.get("FAL_KEY") or "").strip()
    if not fal:
        return False
    endpoint = (
        os.environ.get("VIRTUS_FAL_IMAGE_URL") or "https://fal.run/fal-ai/flux/schnell"
    ).strip()
    payload = json.dumps(
        {
            "prompt": prompt[:1800],
            "image_size": {
                "width": int(size[0]),
                "height": int(size[1]),
            },
            "num_images": 1,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Key {fal}",
            "User-Agent": "VirtusCore-Factory/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore") or "{}")
        images = data.get("images") or []
        url = ""
        if images and isinstance(images[0], dict):
            url = str(images[0].get("url") or "")
        if not url:
            url = str(data.get("url") or data.get("image_url") or "")
        return _download_url(url, dest)


def _try_hf_images(prompt: str, dest: Path, *, size: tuple[int, int]) -> bool:
    """Optional HF Inference — best-effort; skip on any failure."""
    hf = (
        os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_TOKEN") or ""
    ).strip()
    if not hf:
        return False
    model = (
        os.environ.get("VIRTUS_HF_IMAGE_MODEL")
        or "black-forest-labs/FLUX.1-schnell"
    ).strip()
    endpoint = f"https://api-inference.huggingface.co/models/{model}"
    payload = json.dumps(
        {
            "inputs": prompt[:1800],
            "parameters": {"width": int(size[0]), "height": int(size[1])},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {hf}",
            "User-Agent": "VirtusCore-Factory/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = resp.read()
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "image/" in ctype or body[:3] == b"\xff\xd8\xff" or body[:8] == b"\x89PNG\r\n\x1a\n":
            dest.write_bytes(body)
            return _ok_image(dest)
        # Some HF routes return JSON with a URL
        try:
            data = json.loads(body.decode("utf-8", errors="ignore") or "{}")
            url = str(data.get("url") or data.get("image_url") or "")
            return _download_url(url, dest)
        except Exception:
            return False


def try_provider_image(prompt: str, dest: Path, *, size: tuple[int, int] = (1600, 900)) -> bool:
    """Try remote image providers in resolve order until one writes ``dest``.

    Returns True if a remote provider wrote the file.
    On exhaustion, marks last provider as Studio Offline Media and returns False
    so callers can write niche Pillow scenes (higher quality than a blank canvas).
    """
    global _LAST_IMAGE_PROVIDER
    dest.parent.mkdir(parents=True, exist_ok=True)
    resolved = resolve_image_provider()
    attempts: list[tuple[str, str, Any]] = [
        ("virtus_image_api", "Virtus Image API", _try_virtus_image_api),
        ("openai", "OpenAI Images", _try_openai_images),
        ("fal", "fal.ai", _try_fal_images),
        ("huggingface", "Hugging Face Inference", _try_hf_images),
    ]
    allowed = set(resolved.get("chain") or [])
    for provider_id, label, fn in attempts:
        if provider_id not in allowed:
            continue
        try:
            if fn(prompt, dest, size=size):
                _LAST_IMAGE_PROVIDER = {
                    "provider": provider_id,
                    "label": label,
                    "remote": True,
                }
                return True
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
            json.JSONDecodeError,
            Exception,
        ):
            continue
    _LAST_IMAGE_PROVIDER = {
        "provider": "studio_offline",
        "label": "Studio Offline Media",
        "remote": False,
    }
    return False


def persist_visual_brand(product_dir: Path, brand: VisualBrand) -> Path:
    path = Path(product_dir) / "VISUAL_BRAND.json"
    path.write_text(json.dumps(brand.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def css_variables(brand: VisualBrand) -> str:
    c = brand.color
    return f"""
:root {{
  --vb-primary: {c.primary};
  --vb-accent: {c.accent};
  --vb-secondary: {c.secondary};
  --vb-surface: {c.surface};
  --vb-cards: {c.cards};
  --vb-bg: {c.background};
  --vb-gradient: {c.gradient};
  --vb-glow: {c.glow};
  --vb-ink: {c.ink};
  --vb-muted: {c.muted};
}}
"""


__all__ = [
    "ColorSystem",
    "VisualBrand",
    "build_image_prompt",
    "css_variables",
    "image_provider_configured",
    "invent_color_system",
    "invent_visual_brand",
    "last_image_provider",
    "persist_visual_brand",
    "resolve_image_provider",
    "scene_library_for",
    "try_provider_image",
]
