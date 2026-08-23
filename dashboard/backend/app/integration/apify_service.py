"""Apify credentials + status — Virtus Core Actor line (Website Auditor first).

Reads APIFY_KEY / APIFY_TOKEN and APIFY_ID / APIFY_USER_ID from .env.local.
Never invents a live Actor run — honest status only until the Actor ships.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

APIFY_API = "https://api.apify.com/v2"


def apify_token() -> str:
    return (
        os.getenv("APIFY_TOKEN", "").strip()
        or os.getenv("APIFY_KEY", "").strip()
        or os.getenv("APIFY_API_TOKEN", "").strip()
    )


def apify_user_id() -> str:
    return (
        os.getenv("APIFY_USER_ID", "").strip()
        or os.getenv("APIFY_ID", "").strip()
    )


def credentials_snapshot() -> dict[str, Any]:
    token = apify_token()
    user_id = apify_user_id()
    return {
        "configured": bool(token),
        "has_token": bool(token),
        "has_user_id": bool(user_id),
        "token_env": "APIFY_TOKEN"
        if os.getenv("APIFY_TOKEN", "").strip()
        else ("APIFY_KEY" if os.getenv("APIFY_KEY", "").strip() else None),
        "user_id_env": "APIFY_USER_ID"
        if os.getenv("APIFY_USER_ID", "").strip()
        else ("APIFY_ID" if os.getenv("APIFY_ID", "").strip() else None),
        "user_id_masked": (user_id[:4] + "…" + user_id[-3:]) if len(user_id) > 8 else (user_id or None),
        "token_masked": ("…" + token[-4:]) if len(token) >= 4 else (None if not token else "****"),
    }


def check_apify_connection(*, timeout_sec: float = 8.0) -> dict[str, Any]:
    """Verify token against Apify users/me. No Actor runs."""
    snap = credentials_snapshot()
    if not snap["has_token"]:
        return {
            "ok": False,
            "connected": False,
            "configured": False,
            "message": "Нужен APIFY_KEY (или APIFY_TOKEN) в dashboard/backend/.env.local",
            "credentials": snap,
            "product_line": _product_line(ready=False),
        }

    url = f"{APIFY_API}/users/me?token={apify_token()}"
    try:
        req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = json.loads(resp.read().decode("utf-8", errors="replace"))
        data = raw.get("data") if isinstance(raw, dict) else None
        username = None
        remote_id = None
        if isinstance(data, dict):
            username = data.get("username") or data.get("name")
            remote_id = str(data.get("id") or "") or None
        configured_id = apify_user_id()
        id_match = None
        if configured_id and remote_id:
            id_match = configured_id == remote_id
        return {
            "ok": True,
            "connected": True,
            "configured": True,
            "message": "Apify API OK — ключ принят",
            "username": username,
            "remote_user_id": remote_id,
            "id_match": id_match,
            "credentials": snap,
            "product_line": _product_line(ready=True),
        }
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            detail = str(exc)
        return {
            "ok": False,
            "connected": False,
            "configured": True,
            "message": f"Apify отклонил ключ (HTTP {exc.code})",
            "detail": detail,
            "credentials": snap,
            "product_line": _product_line(ready=False),
        }
    except Exception as exc:
        return {
            "ok": False,
            "connected": False,
            "configured": True,
            "message": f"Не удалось проверить Apify: {exc}",
            "credentials": snap,
            "product_line": _product_line(ready=False),
        }


def _product_line(*, ready: bool) -> dict[str, Any]:
    """Honest roadmap — Actors not published until built."""
    return {
        "brand": "Virtus Core",
        "store": "https://apify.com/store",
        "note": "Не очередной парсер Maps — линейка AI Auditor / Lead / Tech Scanner.",
        "actors": [
            {
                "id": "vc_website_auditor",
                "name": "VC Website Auditor",
                "status": "planned" if not ready else "credentials_ready",
                "priority": 1,
                "blurb": "SEO · speed · mobile · Impressum/Datenschutz · tech · AI tips",
            },
            {
                "id": "vc_tech_scanner",
                "name": "VC Tech Scanner",
                "status": "planned",
                "priority": 2,
                "blurb": "CMS · hosting · analytics · pixels · cookie banner",
            },
            {
                "id": "vc_lead_finder",
                "name": "VC Lead Finder",
                "status": "planned",
                "priority": 3,
                "blurb": "Local businesses → contacts → potential client score",
            },
            {
                "id": "vc_business_analyzer",
                "name": "VC Business Analyzer",
                "status": "planned",
                "priority": 4,
                "blurb": "Maps companies → top website problems for outreach",
            },
            {
                "id": "vc_ai_report",
                "name": "VC AI Report",
                "status": "planned",
                "priority": 5,
                "blurb": "PDF / JSON / CSV / Markdown business inspection pack",
            },
        ],
        "client_visible": False,
        "owner_only": True,
    }


def owner_apify_panel() -> dict[str, Any]:
    status = check_apify_connection()
    return {
        "ok": True,
        "surface": "mission_control",
        "owner_only": True,
        "apify": status,
    }
