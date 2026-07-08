#!/usr/bin/env python3
"""Generate Virtus Core / Vector brand assets from vector SVG masters."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRAND_RENDERER = ROOT / "scripts" / "brand_renderer"
BRAND_RENDER_JS = BRAND_RENDERER / "render.mjs"
BRANDING = ROOT / "branding"
MASTER = BRANDING / "vector" / "vector-app-icon.svg"
FAVICON = BRANDING / "vector" / "vector-mark-compact.svg"
ANDROID_FG = BRANDING / "vector" / "android-foreground.svg"
ANDROID_BG = BRANDING / "vector" / "android-background.svg"
LOGO = BRANDING / "virtus-core" / "virtus-core-logo.svg"
SIGNATURE = BRANDING / "virtus-core" / "virtus-core-signature-stacked.svg"
OUT = BRANDING / "generated"
TOKENS = BRANDING / "design-tokens.json"

LAUNCHER_ASSETS = ROOT / "launcher" / "assets"
TAURI_ICONS = ROOT / "client" / "desktop" / "src-tauri" / "icons"
WEB_PUBLIC = ROOT / "dashboard" / "frontend" / "public" / "brand"
DESKTOP_PUBLIC = ROOT / "client" / "desktop" / "public"
ANDROID_BASE = OUT / "android"
IOS_BASE = OUT / "ios"
WINDOWS_BASE = OUT / "windows"
LINUX_BASE = OUT / "linux"
WEB_BASE = OUT / "web"
AUDIT_DIR = OUT / "audit"

AUDIT_SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024, 2048)
ICO_SIZES = (256, 128, 64, 48, 32, 24, 16)
FAVICON_THRESHOLD = 24

PNG_TARGETS: list[tuple[Path, int, Path]] = [
    (LAUNCHER_ASSETS / "virtus-icon.png", 512, MASTER),
    (LAUNCHER_ASSETS / "genesis-icon.png", 512, MASTER),
    (WEB_PUBLIC / "vector-mark-512.png", 512, MASTER),
    (WEB_PUBLIC / "vector-mark-192.png", 192, MASTER),
    (WEB_PUBLIC / "vector-mark-180.png", 180, MASTER),
    (WEB_PUBLIC / "apple-touch-icon.png", 180, MASTER),
    (WEB_PUBLIC / "icon-192.png", 192, MASTER),
    (WEB_PUBLIC / "icon-512.png", 512, MASTER),
    (WEB_PUBLIC / "favicon-16.png", 16, FAVICON),
    (WEB_PUBLIC / "favicon-24.png", 24, FAVICON),
    (WEB_PUBLIC / "favicon-32.png", 32, FAVICON),
    (WEB_BASE / "icon-1024.png", 1024, MASTER),
    (WEB_BASE / "icon-2048.png", 2048, MASTER),
    (DESKTOP_PUBLIC / "icon-512.png", 512, MASTER),
    (DESKTOP_PUBLIC / "icon-192.png", 192, MASTER),
    (TAURI_ICONS / "icon.png", 512, MASTER),
    (TAURI_ICONS / "128x128@2x.png", 256, MASTER),
    (TAURI_ICONS / "128x128.png", 128, MASTER),
    (TAURI_ICONS / "32x32.png", 32, FAVICON),
    (TAURI_ICONS / "16x16.png", 16, FAVICON),
    (IOS_BASE / "AppIcon-1024.png", 1024, MASTER),
    (IOS_BASE / "AppIcon-180.png", 180, MASTER),
]

TAURI_SQUARE_TARGETS: list[tuple[Path, int, Path]] = [
    (TAURI_ICONS / "Square30x30Logo.png", 30, FAVICON),
    (TAURI_ICONS / "Square44x44Logo.png", 44, FAVICON),
    (TAURI_ICONS / "Square71x71Logo.png", 71, FAVICON),
    (TAURI_ICONS / "Square89x89Logo.png", 89, FAVICON),
    (TAURI_ICONS / "Square107x107Logo.png", 107, FAVICON),
    (TAURI_ICONS / "Square142x142Logo.png", 142, MASTER),
    (TAURI_ICONS / "Square150x150Logo.png", 150, MASTER),
    (TAURI_ICONS / "Square284x284Logo.png", 284, MASTER),
    (TAURI_ICONS / "Square310x310Logo.png", 310, MASTER),
    (TAURI_ICONS / "StoreLogo.png", 50, FAVICON),
]

ANDROID_DENSITIES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}


def _npx_cmd() -> list[str]:
    for name in ("npx.cmd", "npx"):
        path = shutil.which(name)
        if path:
            return [path]
    raise OSError("npx not found — install Node.js for brand asset generation")


def _render_cairosvg(path: Path, size: int) -> bytes:
    import cairosvg

    return cairosvg.svg2png(url=str(path), output_width=size, output_height=size)


def _render_node_resvg(path: Path, size: int) -> bytes:
    """Stable local @resvg/resvg-js — avoids flaky npx CLI crashes on Windows."""
    if not BRAND_RENDER_JS.is_file():
        raise OSError("scripts/brand_renderer/render.mjs missing")
    node_modules = BRAND_RENDERER / "node_modules" / "@resvg" / "resvg-js"
    if not node_modules.is_dir():
        subprocess.run(
            ["npm", "install", "--no-audit", "--no-fund"],
            check=True,
            cwd=BRAND_RENDERER,
            capture_output=True,
            text=True,
        )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        subprocess.run(
            ["node", str(BRAND_RENDER_JS), str(path), str(out), str(size)],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return out.read_bytes()
    finally:
        out.unlink(missing_ok=True)


def _render_resvg(path: Path, size: int) -> bytes:
    try:
        return _render_node_resvg(path, size)
    except (OSError, subprocess.CalledProcessError):
        pass
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        subprocess.run(
            [
                *_npx_cmd(),
                "--yes",
                "@resvg/resvg-js-cli",
                "--fit-width",
                str(size),
                "--fit-height",
                str(size),
                str(path),
                str(out),
            ],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return out.read_bytes()
    finally:
        out.unlink(missing_ok=True)


def render_png(source: Path, size: int) -> bytes:
    try:
        return _render_cairosvg(source, size)
    except (ImportError, OSError):
        return _render_resvg(source, size)


def write_png(path: Path, size: int, source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render_png(source, size))
    print(f"  PNG {size:4d} -> {path.relative_to(ROOT)}")


def write_ico(path: Path, sizes: tuple[int, ...], source: Path) -> None:
    from PIL import Image

    frames = []
    for s in sizes:
        src = FAVICON if s <= FAVICON_THRESHOLD else source
        frames.append(Image.open(BytesIO(render_png(src, s))).convert("RGBA"))
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(path, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[1:])
    print(f"  ICO       -> {path.relative_to(ROOT)}")


def copy_masters() -> None:
    copies = [
        (WEB_PUBLIC / "vector-mark.svg", MASTER),
        (WEB_PUBLIC / "vector-mark-compact.svg", FAVICON),
        (WEB_PUBLIC / "virtus-core-logo.svg", LOGO),
        (WEB_PUBLIC / "virtus-core-signature.svg", SIGNATURE),
        (DESKTOP_PUBLIC / "icon.svg", MASTER),
        (LINUX_BASE / "vector-mark.svg", MASTER),
        (BRANDING / "vector" / "vector-app-icon.svg", MASTER),
    ]
    for dest, src in copies:
        if src == dest:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  SVG       -> {dest.relative_to(ROOT)}")


def write_favicon_ico() -> None:
    write_ico(WEB_BASE / "favicon.ico", ICO_SIZES, MASTER)
    shutil.copy2(WEB_BASE / "favicon.ico", WEB_PUBLIC / "favicon.ico")


def write_audit_sheet() -> None:
    from PIL import Image, ImageDraw

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    cols = 3
    rows = (len(AUDIT_SIZES) + cols - 1) // cols
    pad = 24
    label_h = 28
    max_cell = 128
    sheet_w = cols * (max_cell + pad) + pad
    sheet_h = rows * (max_cell + label_h + pad) + pad
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (8, 8, 12, 255))
    draw = ImageDraw.Draw(sheet)
    for i, size in enumerate(AUDIT_SIZES):
        col, row = i % cols, i // cols
        x0 = pad + col * (max_cell + pad)
        y0 = pad + row * (max_cell + label_h + pad)
        src = FAVICON if size <= FAVICON_THRESHOLD else MASTER
        icon = Image.open(BytesIO(render_png(src, size))).convert("RGBA")
        disp = min(max_cell, size) if size >= max_cell else size
        icon = icon.resize((disp, disp), Image.Resampling.LANCZOS)
        ox = x0 + (max_cell - disp) // 2
        oy = y0 + (max_cell - disp) // 2
        sheet.paste(icon, (ox, oy), icon)
        draw.text((x0, y0 + max_cell + 4), f"{size}px", fill=(200, 200, 210))
    out = AUDIT_DIR / "virtus-core-size-audit.png"
    sheet.save(out, format="PNG")
    print(f"  AUDIT     -> {out.relative_to(ROOT)}")


def write_validation_report() -> None:
    checks = []
    for path in (
        LAUNCHER_ASSETS / "virtus.ico",
        LAUNCHER_ASSETS / "virtus-icon.png",
        WEB_PUBLIC / "vector-mark.svg",
        WEB_PUBLIC / "favicon-32.png",
        WEB_PUBLIC / "icon-512.png",
        TAURI_ICONS / "icon.ico",
    ):
        checks.append({"path": str(path.relative_to(ROOT)), "exists": path.is_file()})
    report = {"brand": "Virtus Core", "assistant": "Vector", "checks": checks}
    out = OUT / "brand-validation.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  REPORT    -> {out.relative_to(ROOT)}")


def main() -> int:
    if not MASTER.is_file() or not FAVICON.is_file():
        print("Missing branding SVG masters in branding/vector/", file=sys.stderr)
        return 1

    print("Virtus Core brand asset pipeline")
    print(f"  Master: {MASTER.relative_to(ROOT)}")
    copy_masters()
    if TOKENS.is_file():
        shutil.copy2(TOKENS, OUT / "design-tokens.json")

    for path, size, source in PNG_TARGETS:
        write_png(path, size, source)
    for path, size, source in TAURI_SQUARE_TARGETS:
        write_png(path, size, source)
    for folder, size in ANDROID_DENSITIES.items():
        write_png(ANDROID_BASE / folder / "ic_launcher.png", size, MASTER)
        write_png(ANDROID_BASE / folder / "ic_launcher_round.png", size, MASTER)
        write_png(ANDROID_BASE / folder / "ic_launcher_foreground.png", size, ANDROID_FG)
        write_png(ANDROID_BASE / folder / "ic_launcher_background.png", size, ANDROID_BG)

    write_ico(LAUNCHER_ASSETS / "virtus.ico", ICO_SIZES, MASTER)
    write_ico(LAUNCHER_ASSETS / "genesis.ico", ICO_SIZES, MASTER)
    write_ico(TAURI_ICONS / "icon.ico", ICO_SIZES, MASTER)
    write_ico(WINDOWS_BASE / "virtus-core.ico", ICO_SIZES, MASTER)
    write_favicon_ico()
    write_png(TAURI_ICONS / "icon.icns.png", 512, MASTER)
    shutil.copy2(TAURI_ICONS / "icon.icns.png", TAURI_ICONS / "icon.icns")
    write_audit_sheet()
    write_validation_report()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
