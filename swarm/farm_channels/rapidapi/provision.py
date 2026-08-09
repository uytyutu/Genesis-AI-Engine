"""Live RapidAPI OpenAPI provisioning — no fake Hub success."""

from __future__ import annotations

import json
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _rapidapi_key() -> str:
    for name in (
        "RAPIDAPI_PUBLISH_TOKEN",
        "RAPIDAPI_PROVIDER_TOKEN",
        "RAPIDAPI_KEY",
        "RAPIDAPI_PROVIDER_KEY",
    ):
        v = (os.environ.get(name) or "").strip()
        if v:
            return v
    return ""


def provision_create_api(
    *,
    openapi: dict[str, Any],
    api_name: str,
    category: str = "",
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Call RapidAPI Platform Create API (OpenAPI file upload).

    Env overrides:
      RAPIDAPI_PROVISION_URL
      RAPIDAPI_PLATFORM_HOST
    """
    key = _rapidapi_key()
    if not key:
        return {
            "ok": False,
            "requires_ceo_action": True,
            "error": "missing_credentials",
            "detail": "RAPIDAPI_KEY / RAPIDAPI_PUBLISH_TOKEN required for live provision",
        }

    # Defaults from RapidAPI Platform API docs (Create API / OAS upload).
    # Override with Hub CI/CD snippet if Provider Dashboard differs.
    url = (
        os.environ.get("RAPIDAPI_PROVISION_URL")
        or "https://platformv.p.rapidapi.com/v1/apis"
    ).strip()
    host = (
        os.environ.get("RAPIDAPI_PLATFORM_HOST")
        or "platformapi1.rapidapi-x.rapidapi.com"
    ).strip()
    owner_id = (os.environ.get("RAPIDAPI_OWNER_ID") or "").strip()
    if owner_id and "rapidapi-file" not in url:
        url = (
            os.environ.get("RAPIDAPI_PROVISION_URL")
            or "https://platformv.p.rapidapi.com/v1/apis/rapidapi-file/admin"
        ).strip()

    # Persist openapi for multipart file part
    work = Path(artifacts_dir) if artifacts_dir else Path(".")
    work.mkdir(parents=True, exist_ok=True)
    oas_path = work / "openapi.provision.json"
    oas_path.write_text(json.dumps(openapi, ensure_ascii=False, indent=2), encoding="utf-8")

    boundary = f"----VirtusFarm{uuid.uuid4().hex}"
    file_bytes = oas_path.read_bytes()
    filename = "openapi.json"
    content_type = mimetypes.guess_type(filename)[0] or "application/json"

    parts: list[bytes] = []
    # Optional metadata fields some Hub variants accept
    fields: list[tuple[str, str]] = [
        ("name", api_name),
        ("category", category or "Other"),
        ("fileFormat", "openapi"),
    ]
    if owner_id:
        fields.append(("ownerId", owner_id))
    for field, value in fields:
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
        + file_bytes
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    req = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": host,
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = getattr(resp, "status", 200) or 200
    except HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = str(exc)
        hint = ""
        if "doesn't exist" in (err_body or "").lower() or "does not exist" in (
            err_body or ""
        ).lower():
            hint = (
                " Platform Create API endpoint unavailable for this key "
                "(personal Hub often needs Provider UI / GraphQL Platform API). "
                "Create the API in Provider Dashboard, set Base URL to GENESIS "
                "runtime, then attach apiId — do not fake ACTIVE."
            )
        return {
            "ok": False,
            "requires_ceo_action": True,
            "error": "provision_http_error",
            "http_status": exc.code,
            "detail": ((err_body[:2000] or str(exc)) + hint)[:2200],
            "provision_url": url,
            "ceo_action": [
                "Open RapidAPI Provider → Add New API",
                "Set Base URL to public Farm runtime",
                "Add endpoint + paid plan + Make public",
                "Record rapidapi_api_id on the candidate",
            ],
        }
    except URLError as exc:
        return {
            "ok": False,
            "requires_ceo_action": True,
            "error": "provision_network_error",
            "detail": str(exc.reason or exc),
            "provision_url": url,
        }
    except Exception as exc:
        return {
            "ok": False,
            "requires_ceo_action": True,
            "error": "provision_exception",
            "detail": str(exc),
            "provision_url": url,
        }

    parsed: Any
    try:
        parsed = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        parsed = {"raw": raw}

    api_id = _extract_api_id(parsed)
    if status >= 200 and status < 300 and api_id:
        return {
            "ok": True,
            "api_id": api_id,
            "http_status": status,
            "response": parsed,
            "provision_url": url,
            "hub_hint": f"Confirm listing + pricing in RapidAPI Provider Dashboard (apiId={api_id})",
        }

    return {
        "ok": False,
        "requires_ceo_action": True,
        "error": "provision_no_api_id",
        "http_status": status,
        "detail": (
            "RapidAPI response did not include apiId. "
            "Check RAPIDAPI_PROVISION_URL / RAPIDAPI_PLATFORM_HOST against Hub CI/CD snippet, "
            "or create/update API once in Provider Dashboard."
        ),
        "response": parsed if isinstance(parsed, dict) else {"raw": raw[:2000]},
        "provision_url": url,
    }


def _extract_api_id(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("apiId", "api_id", "id", "apiID"):
        v = payload.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    data = payload.get("data")
    if isinstance(data, dict):
        return _extract_api_id(data)
    info = payload.get("x-rapidapi-info") or payload.get("rapidapi")
    if isinstance(info, dict):
        return _extract_api_id(info)
    return ""
