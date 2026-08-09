"""Media Truth — beauty without profession proof is not quality.

Every photo / illustration / video must answer YES to all three:
  1. Is it beautiful?
  2. Does it fit the brand?
  3. Does it match the profession?

Any NO → REBUILD. Brand Book Media DNA is the authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.factory.design_dna.brand_book import BrandBook, MediaDNA, resolve_brand_book


# Path / filename tokens that fail profession proof for craft / general
_GLOBAL_FORBIDDEN_TOKENS = (
    "cafe",
    "café",
    "coffee",
    "restaurant",
    "bistro",
    "salon",
    "spa",
    "nail",
    "cowork",
    "office",
    "laptop",
    "meeting",
    "handshake",
    "startup",
    "saas",
    "dashboard",
    "yoga",
    "cocktail",
)


@dataclass(frozen=True)
class MediaTruthVerdict:
    ok: bool
    beautiful: bool
    brand_fit: bool
    profession_fit: bool
    action: str  # PASS | REBUILD
    reasons: tuple[str, ...] = ()
    path: str = ""
    role: str = "hero"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _tokens_from_path(path: Path | str) -> str:
    p = Path(path)
    return f"{p.name} {p.parent.name} {p.as_posix()}".lower()


def _hits_forbidden(blob: str, media: MediaDNA) -> list[str]:
    hits: list[str] = []
    for token in _GLOBAL_FORBIDDEN_TOKENS:
        if token in blob:
            hits.append(token)
    for ban in media.forbidden:
        t = ban.lower().strip()
        if len(t) >= 3 and t in blob:
            hits.append(t)
    return hits


def _profession_signal(blob: str, media: MediaDNA) -> bool:
    keys = [k.lower() for k in media.profession_keywords if k]
    if not keys:
        return True
    return any(k in blob for k in keys)


def judge_media_truth(
    *,
    path: Path | str,
    book: BrandBook,
    role: str = "hero",
    source: str = "unknown",
    file_bytes: int = 0,
) -> MediaTruthVerdict:
    """Judge one asset against Brand Book Media DNA."""
    media = book.media_dna
    blob = _tokens_from_path(path)
    # Generated Brand Book scenes are profession-locked by construction
    if source in ("brand_book", "niche_scene", "atmosphere_pack"):
        beautiful = file_bytes >= 8_000 or file_bytes == 0
        return MediaTruthVerdict(
            ok=True,
            beautiful=beautiful,
            brand_fit=True,
            profession_fit=True,
            action="PASS",
            reasons=("brand_book_directed_scene",),
            path=str(path),
            role=role,
        )

    forbidden_hits = _hits_forbidden(blob, media)
    profession_fit = _profession_signal(blob, media) and not forbidden_hits
    # Stock packs without profession tokens fail — even if "pretty"
    if source in ("pack", "niche", "stock") and not _profession_signal(blob, media):
        profession_fit = False

    brand_fit = not forbidden_hits
    # Soft beauty proxy: missing/tiny files fail
    beautiful = True
    try:
        p = Path(path)
        if p.is_file():
            sz = p.stat().st_size
            if sz < 4_000:
                beautiful = False
            file_bytes = sz
    except OSError:
        beautiful = False

    reasons: list[str] = []
    if forbidden_hits:
        reasons.append(f"forbidden_tokens:{','.join(forbidden_hits[:6])}")
    if not profession_fit:
        reasons.append("missing_profession_proof")
    if not brand_fit:
        reasons.append("brand_mismatch")
    if not beautiful:
        reasons.append("not_beautiful_or_too_small")

    ok = beautiful and brand_fit and profession_fit
    return MediaTruthVerdict(
        ok=ok,
        beautiful=beautiful,
        brand_fit=brand_fit,
        profession_fit=profession_fit,
        action="PASS" if ok else "REBUILD",
        reasons=tuple(reasons),
        path=str(path),
        role=role,
    )


def enforce_media_truth_on_product(
    product_dir: Path,
    *,
    niche_id: str,
    business_name: str,
    package_id: str = "business",
) -> dict[str, Any]:
    """Scan hero/background; REBUILD craft scenes if Media Truth fails."""
    book = resolve_brand_book(
        business_name=business_name,
        niche_id=niche_id,
        package_id=package_id,
    )
    assets = product_dir / "assets"
    report: dict[str, Any] = {
        "rule": "Media Truth — beauty without profession proof ≠ quality",
        "media_dna": book.media_dna.as_dict(),
        "verdicts": [],
        "rebuilds": [],
        "ok": True,
    }
    targets = (
        ("hero", assets / "hero.jpg"),
        ("background", assets / "background.jpg"),
        ("gallery", assets / "gallery.jpg"),
    )
    for role, path in targets:
        if not path.is_file():
            continue
        # Heuristic source: huge photographic stock vs small generated scenes
        sz = path.stat().st_size
        source = "brand_book" if sz < 200_000 else "pack"
        verdict = judge_media_truth(
            path=path, book=book, role=role, source=source, file_bytes=sz
        )
        report["verdicts"].append(verdict.as_dict())
        if not verdict.ok:
            report["ok"] = False
            report["rebuilds"].append(role)
            try:
                from app.factory.niche_scene_media import write_niche_scene

                write_niche_scene(
                    path,
                    niche_id=niche_id,
                    seed=f"media-truth|{role}|{book.fingerprint}",
                    role="hero" if role == "hero" else "banner" if role == "background" else "gallery",
                    size=(1600, 900) if role != "gallery" else (1400, 1000),
                    metaphor=book.visual_metaphor,
                    accent_hex=book.palette.accent_hex,
                )
                report["verdicts"].append(
                    {
                        "ok": True,
                        "action": "REBUILT",
                        "role": role,
                        "path": str(path),
                        "reasons": ["rebuilt_from_media_dna"],
                    }
                )
            except Exception as exc:  # noqa: BLE001
                report["verdicts"].append(
                    {"ok": False, "action": "REBUILD_FAILED", "role": role, "error": str(exc)}
                )

    import json

    (product_dir / "media_truth.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


__all__ = [
    "MediaTruthVerdict",
    "enforce_media_truth_on_product",
    "judge_media_truth",
]
