"""Build stamp shown in Launcher вЂ” CEO can verify which exe is running."""

from __future__ import annotations

import sys
from pathlib import Path

BUILD_STAMP = '2026-07-08 10:42 UTC'

if getattr(sys, "frozen", False):
    _exe = Path(sys.executable).resolve()
    BUILD_ID = f"build {BUILD_STAMP} В· {_exe.name}"
else:
    BUILD_ID = f"dev {BUILD_STAMP} В· launcher/app.py"

