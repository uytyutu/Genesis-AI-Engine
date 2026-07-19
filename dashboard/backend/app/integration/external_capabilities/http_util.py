"""HTTP helpers for external adapters — short timeouts, never raise to callers."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


USER_AGENT = "VirtusCore/1.0 (local-owner; contact=support@virtus-core.local)"


def http_get_json(
    url: str,
    *,
    timeout: float = 4.0,
    headers: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            if isinstance(data, (dict, list)):
                return data, None
            return None, "unexpected_json_type"
    except urllib.error.HTTPError as exc:
        return None, f"http_{exc.code}"
    except urllib.error.URLError as exc:
        return None, f"url_error:{exc.reason}"
    except (TimeoutError, json.JSONDecodeError, OSError) as exc:
        return None, str(exc)[:120]


def url_with_query(base: str, params: dict[str, str]) -> str:
    return f"{base}?{urllib.parse.urlencode(params)}"
