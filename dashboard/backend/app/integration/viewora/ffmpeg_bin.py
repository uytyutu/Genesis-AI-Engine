"""Resolve FFmpeg binary for Virtus Video AI (env → imageio-ffmpeg → PATH)."""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def resolve_ffmpeg() -> str | None:
    for env_name in ("FFMPEG_PATH", "IMAGEIO_FFMPEG_EXE"):
        val = (os.getenv(env_name) or "").strip()
        if val and os.path.isfile(val):
            return val
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass
    which = shutil.which("ffmpeg")
    return which


def ffmpeg_available() -> bool:
    exe = resolve_ffmpeg()
    if not exe:
        return False
    try:
        subprocess.run(
            [exe, "-version"],
            check=True,
            capture_output=True,
            timeout=15,
        )
        return True
    except Exception:
        return False
