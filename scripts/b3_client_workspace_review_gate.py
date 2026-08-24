#!/usr/bin/env python3
"""B3 Client Workspace Review Gate — runnable wrapper.

Isolated fixture + pytest suite. Does not commit. Does not disable OTP in
production HTTP. Optional ``--live`` checks local :8000/:3000 when running.

  py -3.12 scripts/b3_client_workspace_review_gate.py
  py -3.12 scripts/b3_client_workspace_review_gate.py --live
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
FRONTEND = ROOT / "dashboard" / "frontend"
sys.path.insert(0, str(BACKEND))


def _run_pytest() -> int:
    import pytest

    targets = [
        BACKEND / "tests" / "test_b3_client_workspace_review_gate.py",
        BACKEND / "tests" / "test_b3_analytics_foundation.py",
    ]
    return pytest.main([*(str(t) for t in targets), "-q", "--tb=short"])


def _http_json(url: str, *, method: str = "GET", token: str | None = None, body: dict | None = None) -> tuple[int, dict | list | str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read().decode("utf-8", errors="replace")
            try:
                return res.status, json.loads(raw)
            except json.JSONDecodeError:
                return res.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def _live_checks(api: str, web: str) -> list[tuple[str, bool, str]]:
    """Seed into a temp memory is not visible to a live uvicorn.

    Live mode verifies: public pages + middleware posture + source honesty,
    and that /api/client/me rejects anonymous (real auth still on).
    Full authenticated live path requires operator to point uvicorn at a
    seeded memory (see fixture) — documented in FAIL hints.
    """
    rows: list[tuple[str, bool, str]] = []

    code, body = _http_json(f"{api}/health")
    rows.append(("API health", code == 200, f"status={code}"))

    code, body = _http_json(f"{api}/api/client/me")
    rows.append(
        (
            "Anonymous /api/client/me → 401",
            code == 401,
            f"status={code} body={body!r}"[:180],
        )
    )

    # Frontend routes must not leak CEO chrome into Support HTML shell
    for path, label in (
        ("/client/login", "Login reachable"),
        ("/client/support", "Support route (middleware)"),
        ("/client/settings", "Settings route (middleware)"),
        ("/client/billing", "Billing route (middleware)"),
    ):
        req = urllib.request.Request(f"{web}{path}", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                html = res.read().decode("utf-8", errors="replace")
                status = res.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            html = exc.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            rows.append((label, False, str(exc)))
            continue
        # Unauthenticated /client/* often redirects to login (3xx) or serves login
        ok = status in {200, 307, 302, 308}
        ceo_leak = "/executive" in html and path == "/client/support"
        rows.append(
            (
                label,
                ok and not ceo_leak,
                f"http={status} ceo_leak={ceo_leak}",
            )
        )

    # Source SSOT — Support page must not deep-link CEO
    support_src = (FRONTEND / "app" / "client" / "support" / "page.tsx").read_text(
        encoding="utf-8"
    )
    rows.append(
        (
            "Support source has no /executive",
            "/executive" not in support_src,
            "support/page.tsx",
        )
    )
    return rows


def _seed_report() -> dict:
    import tempfile

    from app.integration.customer_identity.b3_review_fixture import (
        ENGINE_ID,
        seed_b3_empty_client,
        seed_b3_review_client,
    )

    os.environ.setdefault(
        "GENESIS_CLIENT_JWT_SECRET", "b3-review-gate-jwt-secret-32chars!!"
    )
    os.environ.setdefault("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    os.environ.setdefault("GENESIS_PAYMENT_SANDBOX", "1")
    os.environ.setdefault("GENESIS_SMTP_MOCK", "1")

    with tempfile.TemporaryDirectory(prefix="b3-review-") as tmp:
        memory = Path(tmp)
        ready = seed_b3_review_client(memory)
        empty = seed_b3_empty_client(memory)
        return {
            "engine": ENGINE_ID,
            "ready": {
                "email": ready.email,
                "customer_id": ready.customer_id,
                "order_id": ready.order_id,
                "product_id": ready.product_id,
                "download_ready": ready.download_ready,
                "admin": f"/client/websites/{ready.order_id}/admin",
                "preview": f"/api/factory/products/{ready.product_id}/preview",
                "token_len": len(ready.token),
            },
            "empty": {
                "email": empty.email,
                "orders": 0,
                "download_ready": empty.download_ready,
            },
        }


def _resolve_live_memory() -> Path:
    """Match the running backend IntegrationContext memory root."""
    env = (os.environ.get("GENESIS_MEMORY_DIR") or "").strip()
    if env:
        return Path(env).expanduser()
    try:
        from app.integration.context import get_integration

        return Path(get_integration().adapter.brain.config.memory_dir)
    except Exception:
        # Launcher / Integration default: dashboard/backend/app/memory
        return BACKEND / "app" / "memory"


def _live_authenticated(api: str, web: str) -> list[tuple[str, bool, str]]:
    """Seed isolated B3 client into live memory, login via real /api/client/login."""
    from app.integration.customer_identity.b3_review_fixture import (
        B3_REVIEW_EMAIL,
        B3_REVIEW_PASSWORD,
        seed_b3_review_client,
    )

    rows: list[tuple[str, bool, str]] = []
    memory = _resolve_live_memory()
    os.environ.setdefault("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    os.environ.setdefault("GENESIS_PAYMENT_SANDBOX", "1")
    os.environ.setdefault("GENESIS_SMTP_MOCK", "1")
    # Prefer JWT secret already used by running backend; fixture sets a default if absent.
    try:
        fx = seed_b3_review_client(memory)
        rows.append(
            (
                "Live memory seed (isolated B3 email)",
                True,
                f"memory={memory} order={fx.order_id}",
            )
        )
    except Exception as exc:  # noqa: BLE001
        rows.append(("Live memory seed", False, str(exc)))
        return rows

    code, body = _http_json(
        f"{api}/api/client/login",
        method="POST",
        body={"email": B3_REVIEW_EMAIL, "password": B3_REVIEW_PASSWORD},
    )
    token = ""
    if isinstance(body, dict):
        token = str(body.get("token") or body.get("access_token") or "").strip()
    rows.append(
        (
            "POST /api/client/login (fixture account)",
            code == 200 and bool(token),
            f"status={code} token_len={len(token)}",
        )
    )
    if not token:
        return rows

    code, me = _http_json(f"{api}/api/client/me", token=token)
    rows.append(("GET /api/client/me", code == 200, f"status={code}"))

    code, orders = _http_json(f"{api}/api/client/orders", token=token)
    order_ok = False
    if code == 200 and isinstance(orders, dict):
        order_ok = any(
            str(r.get("order_id")) == str(fx.order_id)
            for r in (orders.get("orders") or [])
        )
    rows.append(
        (
            "Dashboard orders include Website",
            order_ok,
            f"status={code} order_id={fx.order_id}",
        )
    )

    code, analytics = _http_json(
        f"{api}/api/client/analytics/overview?period=30d", token=token
    )
    a_ok = False
    no_fake = True
    if code == 200 and isinstance(analytics, dict):
        a_ok = analytics.get("analytics_state") == "not_connected"
        for m in analytics.get("metrics") or []:
            mid = str(m.get("metric_id") or "")
            if "visitor" in mid.lower() or "besucher" in str(m.get("label") or "").lower():
                # only allowed if source is website_traffic AND points from real tracker
                # v1: must not appear while traffic not_connected
                no_fake = False
        for m in analytics.get("metrics") or []:
            if not m.get("source_id"):
                no_fake = False
    rows.append(
        (
            "Analytics overview · Website Aktiv → Analytics not_connected",
            a_ok and no_fake,
            f"status={code} state={(analytics.get('analytics_state') if isinstance(analytics, dict) else None)}",
        )
    )

    code, ctx = _http_json(f"{api}/api/client/context", token=token)
    ctx_ok = (
        code == 200
        and isinstance(ctx, dict)
        and ctx.get("engine") == "b3_client_context_v1"
        and isinstance(ctx.get("analytics"), dict)
        and ctx["analytics"].get("analytics_state") == "not_connected"
    )
    rows.append(
        (
            "Client Context API embeds Analytics SSOT",
            ctx_ok,
            f"status={code}",
        )
    )

    code, connect = _http_json(
        f"{api}/api/client/analytics/connect",
        method="POST",
        token=token,
        body={},
    )
    connect_ok = (
        isinstance(connect, dict)
        and connect.get("ok") is False
        and connect.get("status") == "coming_soon"
    )
    rows.append(
        (
            "Analytics connect refuses fake Connected",
            connect_ok,
            f"http={code} ok={connect.get('ok') if isinstance(connect, dict) else None} status={connect.get('status') if isinstance(connect, dict) else None}",
        )
    )

    code, meta = _http_json(
        f"{api}/api/client/websites/{fx.order_id}/admin/preview-meta",
        token=token,
    )
    preview = ""
    if isinstance(meta, dict):
        preview = str(meta.get("preview_url") or "")
    rows.append(
        (
            "Website Admin preview-meta (Verwalten)",
            code == 200 and bool(preview),
            f"status={code} preview={preview}",
        )
    )

    if fx.product_id:
        req = urllib.request.Request(
            f"{api}/api/factory/products/{fx.product_id}/preview",
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                pstatus = res.status
                ctype = res.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            pstatus = exc.code
            ctype = ""
        except Exception as exc:  # noqa: BLE001
            pstatus = 0
            ctype = str(exc)
        rows.append(
            (
                "Preview HTML reachable",
                pstatus == 200,
                f"status={pstatus} ctype={ctype}",
            )
        )

    # ZIP only when download_ready — authenticated download
    if fx.download_url:
        req = urllib.request.Request(
            f"{api}{fx.download_url}",
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                zstatus = res.status
                blob = res.read(4)
        except urllib.error.HTTPError as exc:
            zstatus = exc.code
            blob = b""
        except Exception as exc:  # noqa: BLE001
            zstatus = 0
            blob = str(exc).encode()
        rows.append(
            (
                "ZIP download when download_ready",
                zstatus == 200 and blob[:2] == b"PK",
                f"status={zstatus}",
            )
        )

    # Frontend pages with real client cookie (middleware gate)
    for path in (
        "/client",
        f"/client/websites/{fx.order_id}/admin",
        "/client/products",
        "/client/settings",
        "/client/billing",
        "/client/support",
    ):
        req = urllib.request.Request(
            f"{web}{path}",
            headers={"Cookie": f"virtus_client_token={token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as res:
                status = res.status
                html = res.read(8000).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            status = exc.code
            html = exc.read(2000).decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            rows.append((f"WEB {path}", False, str(exc)))
            continue
        leak = "/executive" in html and path.endswith("/support")
        rows.append(
            (
                f"WEB {path}",
                status == 200 and not leak,
                f"http={status} ceo_leak={leak}",
            )
        )

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="B3 Client Workspace Review Gate")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Probe local API/frontend + authenticated fixture path against live memory",
    )
    parser.add_argument("--api", default=os.environ.get("B3_GATE_API", "http://127.0.0.1:8000"))
    parser.add_argument("--web", default=os.environ.get("B3_GATE_WEB", "http://127.0.0.1:3000"))
    args = parser.parse_args()

    print("=== B3 Client Workspace Review Gate ===")
    print("NO COMMIT · isolated fixture · real JWT (register path, not OTP bypass)")
    print()

    try:
        report = _seed_report()
        print("Fixture seed: PASS")
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001
        print(f"Fixture seed: FAIL — {exc}")
        return 1

    print()
    print("Pytest suite…")
    code = _run_pytest()
    print(f"Pytest exit: {code}")

    live_fail = 0
    if args.live:
        print()
        print(f"Live probes · API={args.api} · WEB={args.web}")
        for name, ok, detail in _live_checks(args.api.rstrip("/"), args.web.rstrip("/")):
            mark = "PASS" if ok else "FAIL"
            if not ok:
                live_fail += 1
            print(f"  [{mark}] {name} — {detail}")
        print()
        print("Live authenticated workflow…")
        for name, ok, detail in _live_authenticated(
            args.api.rstrip("/"), args.web.rstrip("/")
        ):
            mark = "PASS" if ok else "FAIL"
            if not ok:
                live_fail += 1
            print(f"  [{mark}] {name} — {detail}")

    print()
    if code == 0 and live_fail == 0:
        print("B3 E2E REVIEW GATE: PASS")
        print("Next: owner visual glance -> APPROVE COMMIT B3")
        return 0
    print("B3 E2E REVIEW GATE: FAIL")
    print("Status remains: B3 REVIEW REQUIRED - NO COMMIT")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
