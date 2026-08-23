"""One-off Preview/Demo HTTP + CSP audit (local)."""
from __future__ import annotations

import urllib.request

URLS = [
    ("Dental", "/package-previews/sites/business/dental/index.html"),
    ("Law", "/package-previews/sites/business/law/index.html"),
    ("Restaurant", "/package-previews/sites/business/restaurant/index.html"),
    ("Beauty", "/package-previews/sites/business/beauty/index.html"),
    ("Auto", "/package-previews/sites/business/auto/index.html"),
    ("Fitness", "/package-previews/sites/business/fitness/index.html"),
    ("Handwerk", "/package-previews/sites/business/handwerk/index.html"),
    ("IT", "/package-previews/sites/business/it/index.html"),
    ("Store Fashion", "/package-previews/stores/fashion/index.html"),
    ("Store Beauty", "/package-previews/stores/beauty/index.html"),
    ("Store Electronics", "/package-previews/stores/electronics/index.html"),
    ("Store Furniture", "/package-previews/stores/furniture/index.html"),
    ("Store Food", "/package-previews/stores/food/index.html"),
    ("Store Handwerk", "/package-previews/stores/handwerk/index.html"),
]


def main() -> None:
    print(f"{'Demo':<18} {'HTTP':<5} {'bytes':<7} {'frame-ancestors':<16} Status")
    print("-" * 70)
    for name, path in URLS:
        try:
            req = urllib.request.Request("http://127.0.0.1:3000" + path, method="HEAD")
            with urllib.request.urlopen(req, timeout=5) as r:
                code = r.status
                csp = r.headers.get("Content-Security-Policy", "")
            if "frame-ancestors 'self'" in csp:
                fa = "self"
            elif "frame-ancestors 'none'" in csp:
                fa = "none"
            else:
                fa = "?"
            with urllib.request.urlopen("http://127.0.0.1:3000" + path, timeout=5) as r2:
                n = len(r2.read())
            if code == 200 and fa == "self" and n >= 5000:
                status = "PASS"
            elif code == 200 and fa == "self":
                status = "THIN"
            else:
                status = "FAIL"
            print(f"{name:<18} {code:<5} {n:<7} {fa:<16} {status}")
        except Exception as exc:  # noqa: BLE001
            err = getattr(exc, "code", type(exc).__name__)
            print(f"{name:<18} {err!s:<5} {'-':<7} {'-':<16} FAIL")


if __name__ == "__main__":
    main()
