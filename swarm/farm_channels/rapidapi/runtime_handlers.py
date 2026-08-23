"""In-process Farm API runtimes served under /api/farm/runtime/{slug}."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from swarm.farm_channels.rapidapi.markets.postal_runtime import (
    handle_de_plz_compat,
    handle_global_postal,
)

SUPPORTED_SLUGS = frozenset(
    {
        "de-plz-city-lookup",
        "global-postal-location",
        "openapi-lint-report",
        "html-meta-og-extractor",
    }
)


def slug_supported(slug: str) -> bool:
    return (slug or "").strip().lower() in SUPPORTED_SLUGS


def health_payload(slug: str) -> dict[str, Any]:
    return {
        "status": "ok",
        "slug": slug,
        "channel": "api_farm_runtime",
        "supported": slug_supported(slug),
    }


def handle_runtime(
    slug: str,
    *,
    method: str,
    path: str,
    query: dict[str, str] | None = None,
    body: Any = None,
) -> tuple[int, dict[str, Any]]:
    """Dispatch runtime call. Returns (http_status, json_body)."""
    s = (slug or "").strip().lower()
    method_u = (method or "GET").upper()
    path_n = path if path.startswith("/") else f"/{path}"
    query = query or {}

    if path_n in ("/health", "/"):
        return 200, health_payload(s)

    if not slug_supported(s):
        return 404, {
            "error": "unknown_runtime",
            "detail": f"No Farm runtime for slug {s!r}",
            "supported": sorted(SUPPORTED_SLUGS),
        }

    if s == "de-plz-city-lookup":
        return handle_de_plz_compat(method_u, path_n, body, query=query)
    if s == "global-postal-location":
        return handle_global_postal(method_u, path_n, body, query=query)
    if s == "openapi-lint-report":
        return _openapi_lint(method_u, path_n, body)
    if s == "html-meta-og-extractor":
        return _meta(method_u, path_n, body)
    return 404, {"error": "not_implemented", "slug": s}


def _openapi_lint(method: str, path: str, body: Any) -> tuple[int, dict[str, Any]]:
    if method != "POST" or path != "/v1/openapi/lint":
        return 404, {"error": "not_found", "path": path}
    doc = body
    if isinstance(body, dict) and "openapi" not in body and "document" in body:
        doc = body.get("document")
    if isinstance(doc, str):
        try:
            doc = json.loads(doc)
        except json.JSONDecodeError:
            return 400, {"error": "validation", "detail": "document must be JSON object"}
    if not isinstance(doc, dict):
        return 400, {"error": "validation", "detail": "POST JSON OpenAPI object"}
    issues: list[dict[str, str]] = []
    if not doc.get("openapi"):
        issues.append({"severity": "error", "message": "missing openapi version"})
    if not isinstance(doc.get("paths"), dict) or not doc.get("paths"):
        issues.append({"severity": "error", "message": "paths empty or missing"})
    if not isinstance(doc.get("info"), dict):
        issues.append({"severity": "warning", "message": "info object missing"})
    return 200, {"ok": not any(i["severity"] == "error" for i in issues), "issues": issues}


def _meta(method: str, path: str, body: Any) -> tuple[int, dict[str, Any]]:
    if method != "POST" or path != "/v1/meta/extract":
        return 404, {"error": "not_found", "path": path}
    if not isinstance(body, dict):
        return 400, {"error": "validation", "detail": "JSON body required"}
    url = str(body.get("url") or "").strip()
    html = str(body.get("html") or "")
    if not url and not html:
        return 400, {"error": "validation", "detail": "Provide url or html"}
    if url and not html:
        # Honest: no silent fetch of arbitrary URLs without caller-supplied HTML in v1
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return 400, {"error": "validation", "detail": "url must be http(s)"}
        return 200, {
            "url": url,
            "title": None,
            "description": None,
            "og_image": None,
            "note": "Pass html in body for extraction (v1 does not fetch remote pages).",
        }
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    desc_m = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
        html,
        re.I,
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
        html,
        re.I,
    )
    og_m = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']*)["\']',
        html,
        re.I,
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:image["\']',
        html,
        re.I,
    )
    return 200, {
        "url": url or None,
        "title": title_m.group(1).strip() if title_m else None,
        "description": desc_m.group(1).strip() if desc_m else None,
        "og_image": og_m.group(1).strip() if og_m else None,
    }
