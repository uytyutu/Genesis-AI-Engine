#!/usr/bin/env python3
"""Open research_3d scene engine in the browser (local HTTP — required for ES modules).

Usage (repo root):
  py -3.12 scripts/open_research_3d.py
"""

from __future__ import annotations

import functools
import http.server
import socketserver
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVE = ROOT / "dashboard" / "backend" / "_research_3d"
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/runtime/scene_engine.html"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SERVE), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print("[%s] %s" % (self.log_date_time_string(), format % args))


def main() -> int:
    engine = SERVE / "runtime" / "scene_engine.html"
    vendor = SERVE / "runtime" / "vendor" / "three.module.js"
    if not engine.is_file():
        print("MISSING:", engine)
        return 1
    if not vendor.is_file():
        print("MISSING vendor three.js:", vendor)
        print("Re-run vendor download or restore runtime/vendor/")
        return 1

    handler = functools.partial(QuietHandler)
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    except OSError as exc:
        print(f"Port {PORT} busy ({exc}). Trying to open existing server…")
        webbrowser.open(URL)
        print(URL)
        return 0

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print("Serving", SERVE)
    print("Open:", URL)
    time.sleep(0.4)
    webbrowser.open(URL)
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping…")
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
