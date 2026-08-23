# -*- coding: utf-8 -*-
"""Cinematic scene control for Premium/Business websites.

Owns sequence frames under product_dir/assets/seq/ without destroying design system.
CONTROL_POINT_ORIGINAL is created once on first bake / ensure_original.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ORIGINAL_NAME = "CONTROL_POINT_ORIGINAL"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seq_dir(product_dir: Path) -> Path:
    d = product_dir / "assets" / "seq"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _versions_root(product_dir: Path) -> Path:
    d = product_dir / "versions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _original_dir(product_dir: Path) -> Path:
    return _versions_root(product_dir) / ORIGINAL_NAME


def ensure_control_point_original(product_dir: Path) -> dict[str, Any]:
    """Snapshot full product tree once. Never overwrite existing ORIGINAL."""
    product_dir = Path(product_dir)
    if not product_dir.is_dir():
        raise ValueError("product_dir_missing")
    dest = _original_dir(product_dir)
    meta_path = dest / "_control_point.json"
    if dest.is_dir() and meta_path.is_file():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        return {"ok": True, "id": ORIGINAL_NAME, "already_exists": True}

    dest.mkdir(parents=True, exist_ok=True)
    for item in product_dir.iterdir():
        if item.name == "versions":
            continue
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    meta = {
        "ok": True,
        "id": ORIGINAL_NAME,
        "created_at": _now(),
        "label": "Original Premium",
        "source": "virtus_core",
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def list_cinematic_scenes(product_dir: Path) -> dict[str, Any]:
    product_dir = Path(product_dir)
    seq = _seq_dir(product_dir)
    frames: list[dict[str, Any]] = []
    for path in sorted(seq.glob("f*.jpg")) + sorted(seq.glob("f*.png")) + sorted(
        seq.glob("f*.webp")
    ):
        m = re.match(r"f(\d+)", path.stem, re.I)
        if not m:
            continue
        idx = int(m.group(1))
        frames.append(
            {
                "scene": idx,
                "filename": path.name,
                "rel": f"assets/seq/{path.name}",
                "bytes": path.stat().st_size if path.is_file() else 0,
            }
        )
    # de-dupe by scene preferring jpg
    by_scene: dict[int, dict[str, Any]] = {}
    for f in frames:
        prev = by_scene.get(f["scene"])
        if prev is None or str(f["filename"]).endswith(".jpg"):
            by_scene[f["scene"]] = f
    ordered = [by_scene[k] for k in sorted(by_scene)]
    original = _original_dir(product_dir)
    return {
        "ok": True,
        "scenes": ordered,
        "count": len(ordered),
        "has_original": (original / "_control_point.json").is_file(),
        "original_id": ORIGINAL_NAME,
    }


def _scene_path(product_dir: Path, scene: int) -> Path | None:
    seq = _seq_dir(product_dir)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = seq / f"f{scene:03d}{ext}"
        if p.is_file():
            return p
    # also accept f01.jpg style
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = seq / f"f{scene:02d}{ext}"
        if p.is_file():
            return p
    return None


def replace_cinematic_scene(
    product_dir: Path,
    scene: int,
    data: bytes,
    *,
    filename: str = "upload.jpg",
) -> dict[str, Any]:
    if scene < 1 or scene > 99:
        raise ValueError("invalid_scene")
    if not data:
        raise ValueError("empty_upload")
    if len(data) > 12 * 1024 * 1024:
        raise ValueError("image_too_large")
    product_dir = Path(product_dir)
    ensure_control_point_original(product_dir)
    seq = _seq_dir(product_dir)
    # history snapshot of previous frame
    hist = _versions_root(product_dir) / "edits" / _now().replace(":", "")
    hist.mkdir(parents=True, exist_ok=True)
    prev = _scene_path(product_dir, scene)
    if prev and prev.is_file():
        shutil.copy2(prev, hist / prev.name)

    ext = Path(filename).suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    # normalize to fNNN.jpg when possible
    dest = seq / f"f{scene:03d}.jpg"
    # remove other extensions for same scene
    for old in seq.glob(f"f{scene:03d}.*"):
        try:
            old.unlink()
        except OSError:
            pass
    for old in seq.glob(f"f{scene:02d}.*"):
        try:
            old.unlink()
        except OSError:
            pass

    try:
        from PIL import Image
        import io

        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.save(dest, "JPEG", quality=88, optimize=True)
    except Exception:
        dest = seq / f"f{scene:03d}{ext}"
        dest.write_bytes(data)

    return {
        "ok": True,
        "scene": scene,
        "rel": f"assets/seq/{dest.name}",
        "saved_at": _now(),
        "live_sync": True,
    }


def restore_cinematic_scene(product_dir: Path, scene: int) -> dict[str, Any]:
    product_dir = Path(product_dir)
    original = _original_dir(product_dir)
    if not original.is_dir():
        raise ValueError("original_missing")
    src = None
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        cand = original / "assets" / "seq" / f"f{scene:03d}{ext}"
        if cand.is_file():
            src = cand
            break
    if src is None:
        raise ValueError("original_scene_missing")
    seq = _seq_dir(product_dir)
    for old in list(seq.glob(f"f{scene:03d}.*")) + list(seq.glob(f"f{scene:02d}.*")):
        try:
            old.unlink()
        except OSError:
            pass
    dest = seq / src.name
    shutil.copy2(src, dest)
    return {"ok": True, "scene": scene, "restored_from": ORIGINAL_NAME, "rel": f"assets/seq/{dest.name}"}


def restore_website_original(product_dir: Path) -> dict[str, Any]:
    product_dir = Path(product_dir)
    src = _original_dir(product_dir)
    if not (src / "_control_point.json").is_file():
        raise ValueError("original_missing")
    # wipe current (except versions)
    for item in list(product_dir.iterdir()):
        if item.name == "versions":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            try:
                item.unlink()
            except OSError:
                pass
    for item in src.iterdir():
        if item.name == "_control_point.json":
            continue
        target = product_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    return {"ok": True, "restored": ORIGINAL_NAME, "restored_at": _now()}


def list_website_versions(product_dir: Path) -> dict[str, Any]:
    product_dir = Path(product_dir)
    versions = []
    original = _original_dir(product_dir)
    if (original / "_control_point.json").is_file():
        try:
            meta = json.loads((original / "_control_point.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {"id": ORIGINAL_NAME}
        versions.append(
            {
                "id": ORIGINAL_NAME,
                "label": meta.get("label") or "Original Premium",
                "created_at": meta.get("created_at"),
                "kind": "original",
            }
        )
    edits = _versions_root(product_dir) / "edits"
    if edits.is_dir():
        for d in sorted(edits.iterdir(), reverse=True)[:20]:
            if d.is_dir():
                versions.append(
                    {
                        "id": d.name,
                        "label": f"Client edit · {d.name}",
                        "created_at": None,
                        "kind": "edit",
                    }
                )
    versions.insert(
        0,
        {
            "id": "current",
            "label": "Current",
            "created_at": _now(),
            "kind": "current",
        },
    )
    return {"ok": True, "versions": versions}
