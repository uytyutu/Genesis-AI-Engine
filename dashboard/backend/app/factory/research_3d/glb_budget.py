"""glTF/GLB size budget for research 3D — fail loud before packaging."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Soft research budget: hero asset should stay mobile-friendly.
DEFAULT_MAX_GLB_BYTES = 2_500_000  # 2.5 MB compressed GLB target
DEFAULT_MAX_TOTAL_BYTES = 4_000_000


@dataclass(frozen=True)
class GlbBudgetResult:
    ok: bool
    code: str
    bytes_used: int = 0
    limit: int = DEFAULT_MAX_GLB_BYTES
    detail: str = ""


def check_glb_budget(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_GLB_BYTES,
) -> GlbBudgetResult:
    p = Path(path)
    if not p.is_file():
        return GlbBudgetResult(False, "missing_glb", detail=str(p))
    size = p.stat().st_size
    if size <= 0:
        return GlbBudgetResult(False, "empty_glb", bytes_used=size, limit=max_bytes)
    if size > max_bytes:
        return GlbBudgetResult(
            False,
            "glb_too_large",
            bytes_used=size,
            limit=max_bytes,
            detail=f"{size} > {max_bytes} — compress with Draco/KTX2 before research ship",
        )
    suffix = p.suffix.lower()
    if suffix not in (".glb", ".gltf"):
        return GlbBudgetResult(
            False,
            "bad_extension",
            bytes_used=size,
            limit=max_bytes,
            detail="Only .glb / .gltf allowed in research workshop",
        )
    return GlbBudgetResult(True, "ok", bytes_used=size, limit=max_bytes)


def check_assets_total(
    asset_dir: Path,
    *,
    max_total: int = DEFAULT_MAX_TOTAL_BYTES,
) -> GlbBudgetResult:
    root = Path(asset_dir)
    if not root.is_dir():
        return GlbBudgetResult(False, "no_asset_dir", detail=str(root))
    total = 0
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".glb", ".gltf", ".bin", ".png", ".jpg", ".jpeg", ".webp", ".ktx2"):
            total += p.stat().st_size
    if total > max_total:
        return GlbBudgetResult(
            False,
            "assets_too_large",
            bytes_used=total,
            limit=max_total,
            detail=f"total 3D assets {total} > {max_total}",
        )
    return GlbBudgetResult(True, "ok", bytes_used=total, limit=max_total)
