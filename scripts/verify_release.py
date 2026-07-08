"""Post-change smoke test — Cursor must pass before reporting work done.

Run from repo root:
    py scripts/verify_release.py
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _ok(label: str) -> None:
    print(f"  OK  {label}")


def _fail(label: str, detail: str = "") -> None:
    msg = f"FAIL {label}"
    if detail:
        msg += f": {detail}"
    print(msg)
    raise SystemExit(1)


def check_imports() -> None:
    from launcher.app import _validate_path_helpers
    from launcher.deps import check_dependencies, frontend_deps_ready
    from launcher.frontend_repair import diagnose_frontend
    from launcher.paths import find_project_root

    _validate_path_helpers()
    root = find_project_root(ROOT)
    if not (root / "PROJECT_STATE.md").exists():
        _fail("project root", str(root))
    _ok("launcher imports and path helpers")

    deps = check_dependencies(root)
    if not deps.python_ok:
        _fail("Python", "not found")
    _ok(f"Python ({deps.python_version or 'found'})")

    if not deps.node_ok:
        print("  WARN Node.js not found — Mission Control install will prompt owner")
    else:
        _ok(f"Node.js ({deps.node_version or 'found'})")

    if deps.node_ok and not frontend_deps_ready(root):
        print("  WARN frontend deps not installed — Virtus Core will auto npm install on first start")
    elif deps.node_ok:
        _ok("Mission Control dependencies (node_modules/next)")


def check_brand_constants() -> None:
    from launcher.branding import ASSISTANT_NAME, BRAND_NAME

    if BRAND_NAME != "Virtus Core":
        _fail("BRAND_NAME", BRAND_NAME)
    if ASSISTANT_NAME != "Vector":
        _fail("ASSISTANT_NAME", ASSISTANT_NAME)
    _ok(f"launcher brand ({BRAND_NAME} · {ASSISTANT_NAME})")


def check_tauri_title() -> None:
    conf = ROOT / "client" / "desktop" / "src-tauri" / "tauri.conf.json"
    if not conf.is_file():
        print("  WARN tauri.conf.json missing — skip Tauri title check")
        return
    text = conf.read_text(encoding="utf-8")
    if '"title": "Virtus Core"' not in text or '"productName": "Virtus Core"' not in text:
        _fail("Tauri desktop title", "expected Virtus Core in tauri.conf.json")
    _ok("Tauri desktop title (Virtus Core)")


def check_desktop_ui_title() -> None:
    index = ROOT / "client" / "desktop" / "index.html"
    if not index.is_file():
        print("  WARN client/desktop/index.html missing")
        return
    if "<title>Virtus Core</title>" not in index.read_text(encoding="utf-8"):
        _fail("desktop index.html title", "expected Virtus Core")
    _ok("Tauri web shell title (Virtus Core)")


def check_launcher_window() -> None:
    from launcher.app import GenesisLauncher

    app = GenesisLauncher()
    root_fn = app._root
    if not callable(root_fn):
        _fail("tkinter _root()", f"got {type(root_fn).__name__}")
    app.update()
    app.focus_get()
    app.destroy()
    _ok("GenesisLauncher window (no WindowsPath/_root bug)")


def check_backend_api(timeout: float = 25.0) -> None:
    backend = ROOT / "dashboard" / "backend"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8766"],
        cwd=backend,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    url = "http://127.0.0.1:8766/api/status"
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status < 500:
                        _ok("Backend API /api/status")
                        return
            except (urllib.error.URLError, OSError, TimeoutError):
                time.sleep(0.5)
        _fail("Backend API", "timeout on :8766")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def check_pytest() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q", "--tb=no"],
        cwd=ROOT / "dashboard" / "backend",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        tail = (result.stdout + result.stderr)[-800:]
        _fail("pytest", tail)
    last = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "passed"
    _ok(f"pytest ({last})")


def check_exe_built() -> None:
    exe = ROOT / "dist" / "Genesis.exe"
    if not exe.exists():
        print("  WARN dist/Genesis.exe missing — run launcher/build.ps1 before owner delivery")
        return
    age_hours = (time.time() - exe.stat().st_mtime) / 3600
    _ok(f"Genesis.exe exists ({exe.stat().st_size // 1024} KB, {age_hours:.1f}h old)")


def main() -> None:
    print("Virtus Core release verification")
    print("=" * 40)
    check_imports()
    check_brand_constants()
    check_tauri_title()
    check_desktop_ui_title()
    check_launcher_window()
    check_backend_api()
    check_pytest()
    check_exe_built()
    print("=" * 40)
    print("All required checks passed.")


if __name__ == "__main__":
    main()
