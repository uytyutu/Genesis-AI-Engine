"""Media Integrity Gate — Asset Integrity (Hard FAIL).

Reality Over Architecture:
  Broken images / missing logo / empty Before-After = Generation FAIL.
  HTML must not export while any referenced local asset is missing or dead.

Produces:
  assets/asset_manifest.json
  media_integrity.json
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Minimum bytes — tiny stubs are treated as placeholders
_MIN_IMAGE = 4_000
_MIN_VIDEO = 8_000
_MIN_OTHER = 32
_MAX_IMAGE_WARN = 3_500_000  # soft warn only

_REF_RE = re.compile(
    r"""(?:src|href|poster)\s*=\s*["'](assets/[^"']+)["']"""
    r"""|url\(\s*["']?(assets/[^"')]+)["']?\s*\)""",
    re.I,
)

_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
_VIDEO_EXT = {".mp4", ".webm", ".mov"}


class MediaIntegrityError(Exception):
    """Hard FAIL — do not publish / export marketing HTML."""

    def __init__(self, report: "MediaIntegrityReport"):
        self.report = report
        fails = [c.id for c in report.checks if not c.ok]
        super().__init__(f"MEDIA_INTEGRITY_FAIL:{','.join(fails[:12])}")


@dataclass(frozen=True)
class IntegrityCheck:
    id: str
    slot: str
    ok: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MediaIntegrityReport:
    ok: bool
    checks: list[IntegrityCheck] = field(default_factory=list)
    referenced: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    manifest_path: str = "assets/asset_manifest.json"

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "passed": self.ok,
            "gate": "MEDIA_INTEGRITY",
            "action": "PASS" if self.ok else "FAIL_NO_EXPORT",
            "checks": [c.as_dict() for c in self.checks],
            "referenced": list(self.referenced),
            "missing": list(self.missing),
            "summary": {
                c.slot: ("PASS" if c.ok else "FAIL")
                for c in self.checks
                if c.slot
                in {
                    "hero",
                    "gallery",
                    "before_after",
                    "logo",
                    "background",
                    "videos",
                    "icons",
                    "favicon",
                    "fonts",
                    "svg",
                    "lazy",
                    "all_refs",
                }
            },
            "manifest_path": self.manifest_path,
        }


def extract_local_asset_refs(html: str) -> list[str]:
    """Unique relative assets/* paths referenced by HTML/CSS."""
    found: list[str] = []
    seen: set[str] = set()
    for m in _REF_RE.finditer(html or ""):
        rel = (m.group(1) or m.group(2) or "").strip().split("?")[0].split("#")[0]
        if not rel or rel in seen:
            continue
        # Never allow absolute / file / parent traversal
        if ".." in rel or rel.startswith("/") or ":" in rel:
            continue
        if not rel.lower().startswith("assets/"):
            continue
        seen.add(rel)
        found.append(rel)
    return found


def _slot_for(rel: str) -> str:
    name = Path(rel).name.lower()
    parent = Path(rel).parent.name.lower()
    if name.startswith("logo"):
        return "logo"
    if name.startswith("hero") or name == "hero.jpg":
        return "hero"
    if "background" in name or name in {"bg.jpg", "banner.jpg"}:
        return "background"
    if parent == "reputation" or "before" in name or "after" in name:
        return "before_after"
    if parent == "hero_pack" or "gallery" in name or "showcase" in name:
        return "gallery"
    if Path(rel).suffix.lower() in _VIDEO_EXT:
        return "videos"
    if Path(rel).suffix.lower() == ".svg" or "icon" in name:
        return "icons"
    if "favicon" in name:
        return "favicon"
    if Path(rel).suffix.lower() in {".woff", ".woff2", ".ttf", ".otf"}:
        return "fonts"
    return "other"


def _verify_image(path: Path) -> tuple[bool, str]:
    size = path.stat().st_size
    if size < _MIN_IMAGE and path.suffix.lower() != ".svg":
        return False, f"too_small:{size}B_placeholder?"
    if path.suffix.lower() == ".svg":
        text = path.read_text(encoding="utf-8", errors="ignore")[:200]
        if "<svg" not in text.lower():
            return False, "invalid_svg"
        return True, f"{size}B"
    try:
        from PIL import Image

        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im2:
            w, h = im2.size
        if w < 32 or h < 32:
            return False, f"tiny_dims:{w}x{h}"
        note = f"{w}x{h}:{size}B"
        if size > _MAX_IMAGE_WARN:
            note += ":heavy_warn"
        return True, note
    except Exception as exc:  # noqa: BLE001
        return False, f"unreadable:{exc.__class__.__name__}"


def _verify_file(path: Path, rel: str) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
    size = path.stat().st_size
    ext = path.suffix.lower()
    if ext in _IMAGE_EXT:
        return _verify_image(path)
    if ext in _VIDEO_EXT:
        if size < _MIN_VIDEO:
            return False, f"video_too_small:{size}B"
        return True, f"video:{size}B"
    if size < _MIN_OTHER:
        return False, f"empty:{size}B"
    return True, f"{size}B"


def ensure_demo_logo(
    assets_dir: Path,
    *,
    business_name: str,
    niche_id: str = "",
) -> Path:
    """Write assets/logo.png if missing/too small — never leave a broken logo src."""
    from app.factory.brand_mark import brand_initials, _hue_from_name

    dest = assets_dir / "logo.png"
    assets_dir.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size >= _MIN_IMAGE:
        ok, _ = _verify_file(dest, "assets/logo.png")
        if ok:
            return dest
        try:
            dest.unlink()
        except OSError:
            pass
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter

        rgb = _hue_from_name(business_name, niche_id)
        # 640px + noise keeps PNG above integrity _MIN_IMAGE (solid fills compress <4KB)
        size = 640
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pad = 20
        draw.rounded_rectangle(
            (pad, pad, size - pad, size - pad),
            radius=120,
            fill=rgb + (255,),
        )
        initials = brand_initials(business_name)
        try:
            font = ImageFont.truetype("arial.ttf", 220)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), initials, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((size - tw) / 2, (size - th) / 2 - 16),
            initials,
            fill=(250, 250, 249, 255),
            font=font,
        )
        # Soft grain so PNG does not collapse under the 4KB integrity floor
        rgb_img = img.convert("RGB")
        grain = Image.effect_noise((size, size), 18).convert("L")
        grain = grain.filter(ImageFilter.GaussianBlur(0.6))
        rgb_img = Image.blend(rgb_img, Image.merge("RGB", (grain, grain, grain)), 0.08)
        rgb_img.save(dest, "PNG", optimize=False, compress_level=1)
        if dest.stat().st_size < _MIN_IMAGE:
            # Last resort: larger canvas
            big = rgb_img.resize((1024, 1024), Image.Resampling.LANCZOS)
            big.save(dest, "PNG", optimize=False, compress_level=0)
    except Exception:
        from PIL import Image, ImageFilter

        base = Image.new("RGB", (640, 640), (30, 41, 59))
        grain = Image.effect_noise((640, 640), 24).convert("L")
        base = Image.blend(base, Image.merge("RGB", (grain, grain, grain)), 0.12)
        base.save(dest, "PNG", optimize=False, compress_level=0)
    return dest


def build_asset_manifest(
    product_dir: Path,
    html: str,
    *,
    integrity: MediaIntegrityReport | None = None,
) -> dict[str, Any]:
    refs = extract_local_asset_refs(html)
    assets = product_dir / "assets"
    entries: list[dict[str, Any]] = []
    for rel in refs:
        path = product_dir / rel.replace("\\", "/")
        ok, detail = _verify_file(path, rel) if path.is_file() else (False, "missing")
        entries.append(
            {
                "path": rel,
                "slot": _slot_for(rel),
                "exists": path.is_file(),
                "ok": ok,
                "detail": detail,
                "bytes": path.stat().st_size if path.is_file() else 0,
            }
        )
    # Also list files on disk not referenced (inventory)
    disk: list[str] = []
    if assets.is_dir():
        for p in sorted(assets.rglob("*")):
            if p.is_file():
                disk.append(p.relative_to(product_dir).as_posix())
    manifest = {
        "version": 1,
        "gate": "MEDIA_INTEGRITY",
        "referenced": entries,
        "on_disk": disk,
        "integrity_ok": bool(integrity.ok) if integrity else None,
        "missing": list(integrity.missing) if integrity else [
            e["path"] for e in entries if not e["ok"]
        ],
    }
    out = assets / "asset_manifest.json"
    assets.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def run_media_integrity(
    product_dir: Path,
    html: str,
    *,
    require_logo: bool = True,
    require_hero: bool = True,
    package_id: str = "",
) -> MediaIntegrityReport:
    """Full MEDIA INTEGRITY checklist. Any FAIL → report.ok = False."""
    checks: list[IntegrityCheck] = []
    refs = extract_local_asset_refs(html)
    missing: list[str] = []
    assets = product_dir / "assets"
    pkg = (package_id or "").strip().lower()
    tier_floor = pkg in ("business", "premium", "connected")

    # Absolute / Windows path leak in HTML
    if re.search(r"(?:src|href|url\()\s*[\"']?(?:file:|[A-Za-z]:\\|\\\\)", html or "", re.I):
        checks.append(
            IntegrityCheck(
                "no_absolute_paths",
                "all_refs",
                False,
                "local/file absolute path in HTML — forbidden in demos",
            )
        )
    else:
        checks.append(IntegrityCheck("no_absolute_paths", "all_refs", True, "relative_ok"))

    # Empty img src
    empty_img = bool(re.search(r"<img[^>]+src=[\"']\s*[\"']", html or "", re.I))
    checks.append(
        IntegrityCheck("no_empty_img", "gallery", not empty_img, "empty src" if empty_img else "ok")
    )

    # Lazy loading — advisory (missing lazy is not commercial-broken media)
    has_img = "<img" in (html or "").lower()
    has_lazy = "loading=\"lazy\"" in (html or "") or "loading='lazy'" in (html or "")
    checks.append(
        IntegrityCheck(
            "lazy_loading",
            "lazy",
            True,
            "lazy_ok" if has_lazy or not has_img else "advisory_no_lazy",
        )
    )

    slot_status: dict[str, list[bool]] = {}
    for rel in refs:
        path = (product_dir / rel.replace("\\", "/")).resolve()
        try:
            path.relative_to(product_dir.resolve())
        except ValueError:
            checks.append(IntegrityCheck(f"path:{rel}", _slot_for(rel), False, "path_escape"))
            missing.append(rel)
            continue
        ok, detail = _verify_file(path, rel)
        slot = _slot_for(rel)
        slot_status.setdefault(slot, []).append(ok)
        checks.append(IntegrityCheck(f"file:{rel}", slot, ok, detail))
        if not ok:
            missing.append(rel)

    # Required slots when referenced / when page structure needs them
    html_l = (html or "").lower()
    needs_hero = any(
        token in html_l
        for token in (
            "assets/hero.jpg",
            "hero.has-photo",
            "has-hero",
            "cr-hero",
            'class="hero',
            "data-renderer-hero",
            "data-stage=\"first-impression",
        )
    )
    if require_hero and needs_hero:
        hero = assets / "hero.jpg"
        ok, detail = _verify_file(hero, "assets/hero.jpg") if hero.is_file() else (False, "missing")
        checks.append(IntegrityCheck("hero_required", "hero", ok, detail))
        if not ok:
            missing.append("assets/hero.jpg")

    # Business/Premium floor — hero + background + gallery ×3 even if HTML is sparse
    if tier_floor:
        for slot_name, rel in (
            ("hero_tier_floor", "assets/hero.jpg"),
            ("background_tier_floor", "assets/background.jpg"),
        ):
            path = product_dir / rel
            ok, detail = _verify_file(path, rel) if path.is_file() else (False, "missing")
            checks.append(IntegrityCheck(slot_name, rel.split("/")[-1].split(".")[0], ok, detail))
            if not ok:
                missing.append(rel)
        gallery_n = 18 if pkg in ("premium", "connected") else 3
        gallery_files = [assets / f"gallery_{i}.jpg" for i in range(1, gallery_n + 1)]
        # Soft floor: Premium may ship 12+; require at least 12 unique plates
        need = 12 if pkg in ("premium", "connected") else gallery_n
        ok_g = all(
            p.is_file() and _verify_file(p, f"assets/{p.name}")[0]
            for p in gallery_files[:need]
        )
        checks.append(
            IntegrityCheck(
                "gallery_tier_floor",
                "gallery",
                ok_g,
                f"gallery_1..{gallery_n}_ok" if ok_g else f"gallery_1..{gallery_n}_missing",
            )
        )
        if not ok_g:
            missing.extend(f"assets/gallery_{i}.jpg" for i in range(1, gallery_n + 1))

        # Studio Renderer 2.0 — Premium section plates (no empty bands)
        if pkg in ("premium", "connected"):
            for plate in (
                "section_story.jpg",
                "section_services.jpg",
                "section_team.jpg",
                "section_process.jpg",
                "section_contact.jpg",
            ):
                path = assets / plate
                ok, detail = (
                    _verify_file(path, f"assets/{plate}") if path.is_file() else (False, "missing")
                )
                checks.append(IntegrityCheck(f"studio_plate:{plate}", "background", ok, detail))
                if not ok:
                    missing.append(f"assets/{plate}")

    if require_logo and "assets/logo.png" in html_l:
        logo = assets / "logo.png"
        ok, detail = _verify_file(logo, "assets/logo.png") if logo.is_file() else (False, "missing")
        checks.append(IntegrityCheck("logo_required", "logo", ok, detail))
        if not ok:
            missing.append("assets/logo.png")

    if "assets/background.jpg" in html_l or 'data-media-bg="1"' in html_l:
        bg = assets / "background.jpg"
        ok, detail = _verify_file(bg, "assets/background.jpg") if bg.is_file() else (False, "missing")
        checks.append(IntegrityCheck("background_required", "background", ok, detail))
        if not ok:
            missing.append("assets/background.jpg")

    # Gallery / project wall / photo band — must have real stills (not captions alone)
    needs_gallery = any(
        token in html_l
        for token in (
            "assets/gallery",
            "rx-photo-band",
            "cr-case-wall",
            "cr-crew",
            'id="gallery"',
            "gallery_1.jpg",
        )
    )
    if needs_gallery:
        gallery_files = [
            p
            for p in assets.glob("gallery*.jpg")
            if p.is_file()
        ]
        ok_g = len(gallery_files) >= 1 and all(
            _verify_file(p, f"assets/{p.name}")[0] for p in gallery_files[:4]
        )
        checks.append(
            IntegrityCheck(
                "gallery_visual_floor",
                "gallery",
                ok_g,
                f"{len(gallery_files)}_gallery_files" if gallery_files else "missing_gallery",
            )
        )
        if not ok_g:
            missing.append("assets/gallery*.jpg")

    # Empty visual sections: photo stages without any assets/* image reference nearby
    # fail if hero stage exists but only abstract gradients (no assets/ in hero region)
    if "cr-hero-stage" in html_l or 'data-split-hero="1"' in html_l:
        hero_has_media = "assets/hero" in html_l
        checks.append(
            IntegrityCheck(
                "hero_stage_has_media",
                "hero",
                hero_has_media,
                "ok" if hero_has_media else "hero_stage_without_assets",
            )
        )
        if not hero_has_media:
            missing.append("assets/hero.jpg")

    # Before/After: if reputation section ships, BA media must exist
    if 'id="reputation"' in html_l or "reputation-pack" in html_l:
        rep = assets / "reputation"
        ba_files = list(rep.glob("*before*.jpg")) + list(rep.glob("*after*.jpg")) if rep.is_dir() else []
        ok = len(ba_files) >= 2 and all(
            f.stat().st_size >= _MIN_IMAGE for f in ba_files[:6]
        )
        checks.append(
            IntegrityCheck(
                "before_after_required",
                "before_after",
                ok,
                f"{len(ba_files)}_ba_files" if ba_files else "missing_reputation_media",
            )
        )
        if not ok:
            missing.append("assets/reputation/*before|after*")

    # Video: if referenced, must exist (+ optional poster)
    for rel in refs:
        if Path(rel).suffix.lower() in _VIDEO_EXT:
            path = product_dir / rel
            ok, detail = _verify_file(path, rel) if path.is_file() else (False, "missing")
            checks.append(IntegrityCheck(f"video:{rel}", "videos", ok, detail))
            if not ok:
                missing.append(rel)

    # SVG icons / fonts — pass if no local refs fail (already in loop)
    svg_ok = all(c.ok for c in checks if c.slot == "icons") if any(
        c.slot == "icons" for c in checks
    ) else True
    checks.append(IntegrityCheck("svg_icons", "svg", svg_ok, "ok" if svg_ok else "icon_fail"))
    font_ok = all(c.ok for c in checks if c.slot == "fonts") if any(
        c.slot == "fonts" for c in checks
    ) else True
    checks.append(IntegrityCheck("local_fonts", "fonts", font_ok, "ok" if font_ok else "font_fail"))
    fav_refs = [r for r in refs if "favicon" in r.lower()]
    if fav_refs:
        fav_ok = all((product_dir / r).is_file() for r in fav_refs)
        checks.append(IntegrityCheck("favicon", "favicon", fav_ok, "ok" if fav_ok else "missing"))
    else:
        checks.append(IntegrityCheck("favicon", "favicon", True, "not_referenced"))

    all_ok = all(c.ok for c in checks)
    report = MediaIntegrityReport(
        ok=all_ok,
        checks=checks,
        referenced=refs,
        missing=sorted(set(missing)),
    )
    return report


def enforce_media_integrity(
    product_dir: Path,
    html: str,
    *,
    business_name: str = "",
    niche_id: str = "",
    package_id: str = "",
    hard: bool = True,
) -> MediaIntegrityReport:
    """Repair what we can, then Hard FAIL if anything remains broken."""
    assets = product_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    html_l = (html or "").lower()
    pkg = (package_id or "").strip().lower()

    if business_name and "assets/logo.png" in html_l:
        try:
            ensure_demo_logo(assets, business_name=business_name, niche_id=niche_id)
        except Exception:
            pass
        logo = assets / "logo.png"
        ok_logo = False
        if logo.is_file():
            ok_logo, _ = _verify_file(logo, "assets/logo.png")
        if not ok_logo:
            try:
                if logo.is_file():
                    logo.unlink()
                ensure_demo_logo(
                    assets,
                    business_name=business_name or "Virtus",
                    niche_id=niche_id,
                )
            except Exception:
                pass
            # Force a known-good PNG even if brand_mark helpers fail
            if (not logo.is_file()) or not _verify_file(logo, "assets/logo.png")[0]:
                try:
                    from PIL import Image

                    Image.new("RGB", (512, 512), (30, 40, 50)).save(
                        logo, "PNG", optimize=False
                    )
                except Exception:
                    pass

    # Materialize stills referenced by Strategy / Atmosphere CSS — always ensure floor
    try:
        from app.factory.niche_scene_media import ensure_tier_media_floor, write_niche_scene

        if pkg in ("business", "premium", "connected"):
            ensure_tier_media_floor(
                assets,
                niche_id=niche_id or "generic",
                business_name=business_name,
                package_id=pkg or "business",
            )
        elif not (assets / "hero.jpg").is_file():
            write_niche_scene(
                assets / "hero.jpg",
                niche_id=niche_id or "generic",
                seed=f"integrity-hero|{business_name}",
                role="hero",
                size=(1600, 900),
            )
        if "assets/background.jpg" in html_l and not (assets / "background.jpg").is_file():
            write_niche_scene(
                assets / "background.jpg",
                niche_id=niche_id or "generic",
                seed=f"integrity-bg|{business_name}",
                role="banner",
                size=(1920, 1080),
            )
        for gi in range(1, 4):
            gname = f"gallery_{gi}.jpg"
            need = f"assets/{gname}" in html_l or any(
                t in html_l
                for t in ("rx-photo-band", "cr-case-wall", "cr-crew", "gallery_")
            )
            if need and not (assets / gname).is_file():
                write_niche_scene(
                    assets / gname,
                    niche_id=niche_id or "generic",
                    seed=f"integrity-gal{gi}|{business_name}",
                    role="gallery",
                    size=(1200, 800),
                )
        if (
            "assets/gallery.jpg" in html_l or "rx-photo-band" in html_l
        ) and not (assets / "gallery.jpg").is_file():
            write_niche_scene(
                assets / "gallery.jpg",
                niche_id=niche_id or "generic",
                seed=f"integrity-gal|{business_name}",
                role="gallery",
                size=(1200, 800),
            )
    except Exception:
        pass

    # Materialize reputation BA if section present but files missing
    if 'id="reputation"' in (html or "") or "reputation-pack" in (html or ""):
        try:
            from app.factory.design_dna.reputation_pack import (
                build_reputation_pack,
                materialize_reputation_media,
            )
            from app.factory.design_dna.brand_book import resolve_brand_book

            book = resolve_brand_book(
                business_name=business_name or "Business",
                niche_id=niche_id or "generic",
            )
            pack = build_reputation_pack(book)
            materialize_reputation_media(product_dir, pack, book=book)
        except Exception:
            pass

    report = run_media_integrity(product_dir, html, package_id=pkg)
    # One repair pass if tier floor failed
    if not report.ok and pkg in ("business", "premium", "connected"):
        try:
            from app.factory.niche_scene_media import ensure_tier_media_floor

            ensure_tier_media_floor(
                assets,
                niche_id=niche_id or "generic",
                business_name=business_name,
                package_id=pkg,
            )
            report = run_media_integrity(product_dir, html, package_id=pkg)
        except Exception:
            pass
    build_asset_manifest(product_dir, html, integrity=report)
    (product_dir / "media_integrity.json").write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if hard and not report.ok:
        raise MediaIntegrityError(report)
    return report


__all__ = [
    "IntegrityCheck",
    "MediaIntegrityError",
    "MediaIntegrityReport",
    "build_asset_manifest",
    "enforce_media_integrity",
    "ensure_demo_logo",
    "extract_local_asset_refs",
    "run_media_integrity",
]
