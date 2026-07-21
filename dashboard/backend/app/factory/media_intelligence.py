"""R2.2e — Media Intelligence for Path A Factory deliverables.

Hero / Gallery / Background selection with client-photo priority, niche
fallbacks, market-aware deterministic picks, and Image Quality Gate inputs.
R3.2 — Section-Aware Media Gate filters candidates (no LLM).
No Pillow required — dimensions from PNG/JPEG/WebP headers.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.factory.hero_pack import primary_hero_src, resolve_slot

Role = Literal["hero", "gallery", "background", "logo"]

# Minimum pixels by role (reject smaller → fallback / drop).
_MIN_SIZE: dict[str, tuple[int, int]] = {
    "hero": (720, 480),
    "gallery": (400, 300),
    "background": (900, 500),
    "logo": (64, 64),
}

# Acceptable aspect ratio ranges (width/height).
_ASPECT: dict[str, tuple[float, float]] = {
    "hero": (1.05, 2.6),
    "gallery": (0.55, 2.4),
    "background": (1.2, 3.0),
    "logo": (0.4, 3.5),
}

_MAX_FILE_BYTES = 4_500_000  # soft cap for ZIP weight


@dataclass(frozen=True)
class ImageAssessment:
    path: str
    role: str
    ok: bool
    width: int = 0
    height: int = 0
    bytes: int = 0
    reason: str = ""
    source: str = "unknown"  # client | niche | pack


@dataclass
class MediaPlan:
    hero_src: str = "assets/hero.jpg"
    hero_from_client: bool = False
    hero_ok: bool = False
    gallery: list[str] = field(default_factory=list)
    background_src: str | None = None
    assessments: list[ImageAssessment] = field(default_factory=list)
    css: str = ""
    gate_ok: bool = True
    gate_failures: list[str] = field(default_factory=list)
    media_gate_ok: bool = True
    media_gate_failures: list[str] = field(default_factory=list)
    media_gate: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "hero_src": self.hero_src,
            "hero_from_client": self.hero_from_client,
            "hero_ok": self.hero_ok,
            "gallery": list(self.gallery),
            "background_src": self.background_src,
            "assessments": [asdict(a) for a in self.assessments],
            "gate_ok": self.gate_ok,
            "gate_failures": list(self.gate_failures),
            "media_gate_ok": self.media_gate_ok,
            "media_gate_failures": list(self.media_gate_failures),
            "media_gate": self.media_gate,
        }


def read_image_size(path: Path) -> tuple[int, int] | None:
    """Return (width, height) for PNG/JPEG/WebP without external deps."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24:
        return None
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return int(w), int(h)
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        w, h = struct.unpack("<HH", data[6:10])
        return int(w), int(h)
    # WebP RIFF
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return _webp_size(data)
    # JPEG
    if data[:2] == b"\xff\xd8":
        return _jpeg_size(data)
    return None


def assess_image(
    path: Path,
    *,
    role: Role,
    source: str = "unknown",
) -> ImageAssessment:
    rel = path.as_posix()
    if not path.is_file():
        return ImageAssessment(path=rel, role=role, ok=False, reason="missing", source=source)
    try:
        size_b = path.stat().st_size
    except OSError:
        return ImageAssessment(path=rel, role=role, ok=False, reason="unreadable", source=source)
    if size_b < 800:
        return ImageAssessment(
            path=rel, role=role, ok=False, bytes=size_b, reason="too_small_file", source=source
        )
    if size_b > _MAX_FILE_BYTES:
        return ImageAssessment(
            path=rel, role=role, ok=False, bytes=size_b, reason="too_large_file", source=source
        )
    dims = read_image_size(path)
    if dims is None:
        # SVG / unknown — allow logo SVG only
        if role == "logo" and path.suffix.lower() == ".svg":
            return ImageAssessment(
                path=rel, role=role, ok=True, bytes=size_b, reason="svg_ok", source=source
            )
        return ImageAssessment(
            path=rel, role=role, ok=False, bytes=size_b, reason="unknown_format", source=source
        )
    w, h = dims
    min_w, min_h = _MIN_SIZE[role]
    if w < min_w or h < min_h:
        return ImageAssessment(
            path=rel,
            role=role,
            ok=False,
            width=w,
            height=h,
            bytes=size_b,
            reason=f"pixelated_or_small:{w}x{h}",
            source=source,
        )
    aspect = w / max(h, 1)
    lo, hi = _ASPECT[role]
    if aspect < lo or aspect > hi:
        return ImageAssessment(
            path=rel,
            role=role,
            ok=False,
            width=w,
            height=h,
            bytes=size_b,
            reason=f"bad_aspect:{aspect:.2f}",
            source=source,
        )
    return ImageAssessment(
        path=rel,
        role=role,
        ok=True,
        width=w,
        height=h,
        bytes=size_b,
        reason="ok",
        source=source,
    )


def pick_niche_hero(
    *,
    niche_id: str,
    package_id: str,
    market_code: str,
    business_name: str,
) -> Path | None:
    """Market-aware deterministic pick among hero_1/2/3 niche stills.

    R3.2: only candidates that pass Section-Aware Media Gate for Hero.
    Never falls back to a denied (illogical) image — returns None instead.
    """
    from app.factory.media_gate import media_fits_section

    slots = ("hero_1", "hero_2", "hero_3")
    candidates: list[Path] = []
    seen: set[Path] = set()
    for slot in slots:
        p = resolve_slot(niche_id, package_id, slot)
        if p is not None and p.is_file() and p not in seen:
            seen.add(p)
            candidates.append(p)
    if not candidates:
        primary = primary_hero_src(niche_id, package_id)
        if primary is not None and primary.is_file():
            candidates.append(primary)
    # Prefer assets that pass pixel quality AND section/niche meaning
    good = [
        p
        for p in candidates
        if assess_image(p, role="hero", source="niche").ok
        and media_fits_section(p, niche_id=niche_id, section="hero", source="niche")
    ]
    if not good:
        return None
    seed = f"{business_name}|{package_id}|{niche_id}|{(market_code or 'DE').upper()}|media-hero"
    idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(good)
    return good[idx]


def pick_niche_background(
    *,
    niche_id: str,
    package_id: str,
    market_code: str,
    business_name: str,
) -> Path | None:
    from app.factory.media_gate import media_fits_section

    slots = ("background_1", "background_2", "banner", "showcase", "hero_2")
    candidates: list[Path] = []
    seen: set[Path] = set()
    for slot in slots:
        p = resolve_slot(niche_id, package_id, slot)
        if p is not None and p.is_file() and p not in seen:
            seen.add(p)
            candidates.append(p)
    if not candidates:
        return None
    good = [
        p
        for p in candidates
        if assess_image(p, role="background", source="pack").ok
        and media_fits_section(p, niche_id=niche_id, section="about", source="pack")
    ]
    if not good:
        return None
    seed = f"{business_name}|{package_id}|{niche_id}|{(market_code or 'DE').upper()}|media-bg"
    idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[8:16], 16) % len(good)
    return good[idx]


def finalize_product_media(
    product_dir: Path,
    *,
    niche_id: str,
    market_code: str,
    package_id: str,
    business_name: str,
    hero_from_client: bool = False,
    gallery_rels: list[str] | None = None,
) -> MediaPlan:
    """Validate/replace hero & gallery; write media_manifest.json + CSS hooks."""
    assets = product_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    assessments: list[ImageAssessment] = []
    failures: list[str] = []

    hero_path = assets / "hero.jpg"
    client_hero_ok = False
    if hero_path.is_file() and hero_from_client:
        a = assess_image(hero_path, role="hero", source="client")
        assessments.append(a)
        client_hero_ok = a.ok
        if not a.ok:
            failures.append(f"client_hero:{a.reason}")

    niche_hero_src: Path | None = None
    hero_ok_force_fail = False
    if not client_hero_ok:
        niche_hero = pick_niche_hero(
            niche_id=niche_id,
            package_id=package_id,
            market_code=market_code,
            business_name=business_name,
        )
        if niche_hero is not None:
            niche_hero_src = niche_hero
            shutil.copy2(niche_hero, hero_path)
            a = assess_image(hero_path, role="hero", source="niche")
            assessments.append(a)
            if not a.ok:
                failures.append(f"niche_hero:{a.reason}")
            hero_from_client = False
        elif not hero_path.is_file():
            failures.append("hero:missing")
            a = ImageAssessment(path="assets/hero.jpg", role="hero", ok=False, reason="missing")
            assessments.append(a)
        else:
            # Stale/wrong hero on disk and no Media Gate–passing candidate
            failures.append("hero:no_media_gate_candidate")
            try:
                hero_path.unlink(missing_ok=True)
            except OSError:
                pass
            hero_from_client = False
            hero_ok_force_fail = True

    hero_final = assess_image(hero_path, role="hero", source="client" if hero_from_client else "niche")
    if hero_path.is_file() and hero_final.ok:
        # refresh last assessment
        if not assessments or assessments[-1].path.endswith("hero.jpg") is False:
            assessments.append(hero_final)

    # Gallery: keep only quality-passing client photos
    kept_gallery: list[str] = []
    for rel in gallery_rels or []:
        p = product_dir / rel.replace("\\", "/")
        # rel is assets/client/...
        if not p.is_file():
            p = product_dir / Path(rel)
        a = assess_image(p, role="gallery", source="client")
        assessments.append(
            ImageAssessment(
                path=rel,
                role="gallery",
                ok=a.ok,
                width=a.width,
                height=a.height,
                bytes=a.bytes,
                reason=a.reason,
                source="client",
            )
        )
        if a.ok:
            kept_gallery.append(rel)
        else:
            failures.append(f"gallery:{rel}:{a.reason}")

    # Background from pack (optional visual consistency)
    bg_rel: str | None = None
    bg_src = pick_niche_background(
        niche_id=niche_id,
        package_id=package_id,
        market_code=market_code,
        business_name=business_name,
    )
    if bg_src is not None:
        dest = assets / "background.jpg"
        shutil.copy2(bg_src, dest)
        ba = assess_image(dest, role="background", source="pack")
        assessments.append(
            ImageAssessment(
                path="assets/background.jpg",
                role="background",
                ok=ba.ok,
                width=ba.width,
                height=ba.height,
                bytes=ba.bytes,
                reason=ba.reason,
                source="pack",
            )
        )
        if ba.ok:
            bg_rel = "assets/background.jpg"
        else:
            failures.append(f"background:{ba.reason}")
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass

    # Logo soft check (does not fail gate alone if missing)
    for logo_name in ("logo.png", "logo.svg"):
        lp = assets / logo_name
        if lp.is_file():
            assessments.append(assess_image(lp, role="logo", source="client"))

    hero_ok = (
        hero_path.is_file()
        and not hero_ok_force_fail
        and assess_image(
            hero_path,
            role="hero",
            source="client" if (hero_from_client and client_hero_ok) else "niche",
        ).ok
    )
    gate_failures: list[str] = []
    if not hero_path.is_file():
        gate_failures.append("hero:missing")
    elif not hero_ok:
        gate_failures.append("hero:not_ok")
    gate_ok = hero_ok

    # R3.2 — Section-Aware Media Gate (tag from showcase source, not product copy)
    from app.factory.media_gate import Section, run_media_gate

    assignments: list[tuple[Section, Path, str]] = []
    if hero_from_client and client_hero_ok and hero_path.is_file():
        assignments.append(("hero", hero_path, "client"))
    elif niche_hero_src is not None:
        assignments.append(("hero", niche_hero_src, "niche"))
    elif hero_path.is_file():
        assignments.append(("hero", hero_path, "niche"))

    if bg_src is not None and bg_rel:
        assignments.append(("about", bg_src, "pack"))

    for rel in kept_gallery:
        p = product_dir / rel.replace("\\", "/")
        if p.is_file():
            assignments.append(("gallery", p, "client"))

    mg = run_media_gate(niche_id=niche_id, assignments=assignments)
    media_gate_ok = mg.passed and bool(hero_ok)
    media_gate_failures = list(mg.failures)
    if not hero_ok and "hero:missing" not in gate_failures and "hero:not_ok" not in media_gate_failures:
        if "hero:no_media_gate_candidate" in failures:
            media_gate_failures.append("hero:no_passing_candidate")
            media_gate_ok = False
    if not media_gate_ok:
        gate_failures.extend(f"media_gate:{f}" for f in media_gate_failures[:6])
        gate_ok = False

    css = _media_css(hero_ok=hero_ok, background=bg_rel, gallery=kept_gallery)
    plan = MediaPlan(
        hero_src="assets/hero.jpg",
        hero_from_client=bool(hero_from_client and client_hero_ok),
        hero_ok=hero_ok,
        gallery=kept_gallery,
        background_src=bg_rel,
        assessments=assessments,
        css=css,
        gate_ok=gate_ok,
        gate_failures=gate_failures,
        media_gate_ok=media_gate_ok,
        media_gate_failures=media_gate_failures,
        media_gate=mg.as_dict(),
    )
    (assets / "media_manifest.json").write_text(
        json.dumps(plan.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return plan


def _media_css(*, hero_ok: bool, background: str | None, gallery: list[str]) -> str:
    """Prevent stretch/blur — cover + fixed aspect; optional site background."""
    lines = [
        "    /* Media Intelligence R2.2e */",
        "    .hero.has-photo, .hero-bleed.has-photo {",
        "      background-size: cover !important;",
        "      background-position: center center !important;",
        "      background-repeat: no-repeat !important;",
        "    }",
        "    .hero img, .hero-A-media img, .hero-C-portrait img, .hero-E-orb img,",
        "    .hero-F-banner img, .trust-photo img, .gal-item img, .gal-cell img,",
        "    .gal-hero img, .gal-side img, .client-photo img {",
        "      object-fit: cover;",
        "      object-position: center;",
        "      max-width: 100%;",
        "      height: 100%;",
        "      image-rendering: auto;",
        "    }",
        "    @media (max-width: 720px) {",
        "      .hero.has-photo { min-height: 52vh; }",
        "      .gal-masonry { column-count: 2; }",
        "    }",
    ]
    if background:
        lines.append(
            f'    body[data-media-bg="1"] .about {{'
            f' background-image: linear-gradient(180deg,rgba(248,250,252,.94),rgba(248,250,252,.97)),'
            f' url("{background}"); background-size: cover; background-position: center; }}'
        )
    if not hero_ok:
        lines.append("    /* hero fallback gradient only — media gate flagged */")
    _ = gallery  # reserved for future responsive srcset
    return "\n".join(lines) + "\n"


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    i = 2
    n = len(data)
    while i < n - 8:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5 : i + 9])
            return int(w), int(h)
        if marker == 0xD9 or marker == 0xDA:
            break
        if marker == 0x00:
            i += 1
            continue
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        i += 2 + length
    return None


def _webp_size(data: bytes) -> tuple[int, int] | None:
    # VP8X
    if data[12:16] == b"VP8X" and len(data) >= 30:
        w = 1 + int.from_bytes(data[24:27], "little")
        h = 1 + int.from_bytes(data[27:30], "little")
        return w, h
    # VP8 
    if data[12:16] == b"VP8 " and len(data) >= 30:
        # lossy frame header starts at 20
        if data[23] == 0x9D and data[24:27] == b"\x01\x2a":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
    # VP8L
    if data[12:16] == b"VP8L" and len(data) >= 25:
        bits = struct.unpack("<I", data[21:25])[0]
        w = (bits & 0x3FFF) + 1
        h = ((bits >> 14) & 0x3FFF) + 1
        return w, h
    return None


def load_media_manifest(assets_dir: Path) -> dict[str, Any] | None:
    path = assets_dir / "media_manifest.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None
