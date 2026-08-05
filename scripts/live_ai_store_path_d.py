"""Live AI Store path D — register → order → pay(simulate) → open → regen → rollback → persist check.

Uses the same memory dir as the running backend (dashboard/backend/memory by default).
Does not start uvicorn/npm. Requires backend already on :8000.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

API = "http://127.0.0.1:8000"
MEMORY_CANDIDATES = [
    BACKEND / "app" / "memory",
    BACKEND / "memory",
    ROOT / "memory",
]


def _load_env() -> None:
    """Load backend .env files into os.environ (no printing)."""
    import os

    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env.local", override=False)
        load_dotenv(BACKEND / ".env", override=False)
        return
    except Exception:
        pass
    for name in (".env.local", ".env"):
        path = BACKEND / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def _http(method: str, path: str, *, token: str | None = None, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"{method} {path} → {exc.code}: {detail}") from exc


def main() -> int:
    print("== AI Store live path D ==")
    print("API", API)
    _load_env()

    status = _http("GET", "/api/status")
    print("backend_ok", status.get("name"), "pid", status.get("backend_pid"), "commit", status.get("git_commit"))

    from app.integration.customer_identity.auth import hash_password, validate_email
    from app.integration.customer_identity.provision import CustomerProvisioner
    from app.integration.customer_identity.service import CustomerIdentityService

    email = f"live.store.d+{int(time.time())}@test.local"
    password = "LiveStorePathD1!"
    token = ""
    customer_id = ""
    memory_used: Path | None = None

    for memory in MEMORY_CANDIDATES:
        if not memory.is_dir():
            print("skip memory missing", memory)
            continue
        print("try memory", memory)
        try:
            identity = CustomerIdentityService(memory)
            session = identity.register(
                name="Live Store Path D",
                email=email,
                password=password,
                locale="de",
                country="DE",
            )
            token = str(session.get("token") or "")
            customer_id = str(
                (session.get("account") or {}).get("customer_id") or session.get("customer_id") or ""
            )
        except RuntimeError as exc:
            if "JWT_SECRET" not in str(exc) and "not configured" not in str(exc):
                print("register_err", type(exc).__name__, str(exc)[:120])
                continue
            provisioner = CustomerProvisioner(memory)
            try:
                account, _card, _company, _welcome = provisioner.provision(
                    name="Live Store Path D",
                    email=validate_email(email),
                    password_hash=hash_password(password),
                    locale="de",
                    country="DE",
                )
            except Exception as exc2:
                # email may already exist from prior attempt in this memory
                print("provision_err", type(exc2).__name__, str(exc2)[:120])
                continue
            customer_id = account.customer_id
            token = ""
        except Exception as exc:
            print("register_err", type(exc).__name__, str(exc)[:120])
            continue

        try:
            login = _http("POST", "/api/client/login", body={"email": email, "password": password})
            token = str(login.get("token") or token)
            if token:
                memory_used = memory
                print("STEP login OK via", memory)
                break
            print("login empty token", memory)
        except Exception as exc:
            print("login_fail", memory, str(exc)[:160])
            # unique email for next memory attempt
            email = f"live.store.d+{int(time.time())}@test.local"
            continue

    if not memory_used or not token or not customer_id:
        raise RuntimeError("could_not_align_customer_with_running_backend_memory")
    MEMORY = memory_used
    print("STEP register OK", customer_id, email, "memory", MEMORY)

    brief = {
        "company_name": "Nordlicht Handels GmbH",
        "store_name": "Nordlicht Boots Live",
        "what_is_sold": "Outdoor boots and jackets for DE",
        "category": "clothing",
        "catalog_size": "100",
        "languages": ["de"],
        "currency": "EUR",
        "payments": ["stripe", "paypal"],
        "shipping": ["dhl", "dpd"],
        "pages": ["home", "catalog", "pdp", "about", "contact", "faq", "legal", "returns", "cart"],
        "style": "warm",
        "market_code": "DE",
        "country": "DE",
    }
    created = _http(
        "POST",
        "/api/sales/orders",
        token=token,
        body={
            "business_name": "Nordlicht Boots Live",
            "email": email,
            "package_id": "ecommerce_shop",
            "product_kind": "shop",
            "description": "Outdoor boots and jackets for DE market",
            "shop_brief": brief,
            "market_code": "DE",
        },
    )
    order_id = str(created.get("order_id") or "")
    if not order_id:
        raise RuntimeError(f"no_order_id: {created}")
    print("STEP brief+order OK", order_id)

    # Sandbox pay: start shop pipeline on the same memory the live API uses
    from app.integration.sales_order_service import SalesOrderService

    sales = SalesOrderService(MEMORY, object())
    order = sales.get_order(order_id)
    if not order:
        raise RuntimeError("order_not_visible_in_aligned_memory")
    pipe = sales.start_shop_pipeline(order_id)
    print(
        "STEP pay+factory",
        "ok=",
        pipe.get("ok"),
        "pipeline=",
        pipe.get("shop_pipeline"),
        "product=",
        pipe.get("product_id"),
        "url=",
        pipe.get("published_url"),
    )
    if not pipe.get("ok"):
        raise RuntimeError(f"pipeline_failed: {pipe}")

    product_id = str(pipe.get("product_id") or "")
    live = _http("GET", f"/api/client/stores/{order_id}/live", token=token)
    # live may be HTML redirect or JSON — accept either
    print("STEP open store HTTP", type(live).__name__, str(live)[:120].replace("\n", " "))

    # Fetch HTML assets via live path
    req = urllib.request.Request(
        f"{API}/api/client/stores/{order_id}/live/",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    markers = {
        "store_name": "Nordlicht Boots Live" in html,
        "cart_badge": "data-cart-badge" in html,
        "drawer": 'id="nav-drawer"' in html,
        "add_cart": 'data-action="add-cart"' in html or "In den Warenkorb" in html,
        "mobile_bar": "mobile-bar" in html,
        "warm_hint": "store.css" in html,
    }
    print("STEP storefront markers", markers)
    if not markers["store_name"] or not markers["drawer"]:
        raise RuntimeError(f"storefront_incomplete: {markers}")

    # CSS warm check
    css_req = urllib.request.Request(
        f"{API}/api/client/stores/{order_id}/live/assets/store.css",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(css_req, timeout=60) as resp:
        css = resp.read().decode("utf-8", errors="replace")
    warm = "--store-bg" in css and not __import__("re").search(
        r"--store-bg\s*:\s*#fff(?:fff)?\s*;", css, __import__("re").I
    )
    print("STEP warm_bg", warm, "bg_line", [ln for ln in css.splitlines() if "--store-bg" in ln][:1])

    # Regenerate
    regen = _http("POST", f"/api/client/stores/{order_id}/regenerate", token=token, body={})
    print("STEP regenerate", regen.get("ok"), "version", regen.get("version") or regen.get("current_version"))
    if regen.get("ok") is False:
        raise RuntimeError(f"regen_failed: {regen}")

    status_after = _http("GET", f"/api/client/stores/{order_id}/status", token=token)
    versions = status_after.get("versions") or status_after.get("available_versions") or []
    current = status_after.get("version") or status_after.get("current_version")
    print("STEP status versions", "current=", current, "list=", versions)

    # Rollback to v1 if possible
    target = 1
    if isinstance(versions, list) and versions:
        nums = []
        for v in versions:
            try:
                nums.append(int(v if not isinstance(v, dict) else v.get("version") or v.get("n") or 0))
            except (TypeError, ValueError):
                pass
        if 1 in nums:
            target = 1
        elif nums:
            target = min(nums)
    rolled = _http(
        "POST",
        f"/api/client/stores/{order_id}/rollback",
        token=token,
        body={"version": target},
    )
    print("STEP rollback", rolled.get("ok"), "to", target, rolled.get("version") or rolled.get("current_version"))

    # Persist check: product dir still exists
    product_dir = MEMORY / "sandbox" / product_id
    index = product_dir / "index.html"
    print("STEP persist_files", "dir=", product_dir.is_dir(), "index=", index.is_file())
    if not index.is_file():
        raise RuntimeError("store_files_missing_after_path")

    out = {
        "ok": True,
        "order_id": order_id,
        "product_id": product_id,
        "customer_id": customer_id,
        "email": email,
        "markers": markers,
        "warm_bg": warm,
        "published_url": pipe.get("published_url"),
        "cabinet": f"http://127.0.0.1:3000/client/stores/{order_id}",
        "live": f"{API}/api/client/stores/{order_id}/live/",
    }
    print("RESULT", json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAIL", str(exc).encode("ascii", "replace").decode("ascii"))
        raise SystemExit(1) from exc
