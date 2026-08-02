"""Virtus Core Platform API — Stripe prepaid → key → audit (second commercial product).

Commercial Engine only (Country Desk dual offer). Not Farm Earn.
Same Places → Opportunity → offer scores → Outbox; no second Hunt.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.commercial_api.keys import CommercialApiKeyStore
from app.commercial_api.packages import get_package, list_packages
from app.integration.finance_service import FinanceService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.public_site_url import configured_public_base

FULFILLMENTS_FILE = "commercial_api_fulfillments.jsonl"
LOW_BALANCE_COOLDOWN_FILE = "commercial_api_topup_sent.json"

# Extensible commercial catalog — score, pick max (never hard-wire SaaS→API only).
CommercialScorer = Callable[[dict[str, Any], dict[str, Any]], int]

_API_NICHE_RE = re.compile(
    r"\b(saas|software|agency|agentur|crm|marketing\s*soft|digital\s*agency|"
    r"ai\s*start|ml\s*start|devtools|platform|api\b|web\s*agency)\b",
    re.I,
)
_LOCAL_BIZ_RE = re.compile(
    r"\b(restaurant|gastronom|cafe|café|hotel|salon|praxis|arzt|handwerk|"
    r"bäckerei|bakery|florist|friseur|barber|pizzeria|imbiss|shop|store|"
    r"ресторан|кафе|салон|отель)\b",
    re.I,
)


def _lead_blob(row: dict[str, Any], meta: dict[str, Any]) -> str:
    return " ".join(
        str(x or "")
        for x in (
            row.get("company_name"),
            row.get("niche"),
            row.get("category"),
            row.get("fit_reason"),
            meta.get("niche"),
            meta.get("industry"),
        )
    )


def _score_website(row: dict[str, Any], meta: dict[str, Any]) -> int:
    """Local / SMB website demand. Zero when website offer already rejected."""
    if meta.get("website_offer") == "rejected" or meta.get("skip_reason") in (
        "website_offer_ineligible",
        "healthy_site",
    ):
        return 0
    score = 55
    blob = _lead_blob(row, meta)
    if _LOCAL_BIZ_RE.search(blob):
        score += 26
    if _API_NICHE_RE.search(blob):
        score -= 18
    # Weak / missing site boosts website product
    url = str(row.get("website") or row.get("url") or meta.get("website") or "").strip()
    if not url:
        score += 12
    return max(0, min(100, score))


def _score_platform_api(row: dict[str, Any], meta: dict[str, Any]) -> int:
    score = 40
    blob = _lead_blob(row, meta)
    if _API_NICHE_RE.search(blob):
        score += 36
    if _LOCAL_BIZ_RE.search(blob):
        score -= 22
    # Healthy modern site → website weak, API / tooling more plausible
    if meta.get("website_offer") == "rejected" or str(
        meta.get("website_offer_reason") or ""
    ):
        score += 10
    return max(0, min(100, score))


# Future OCR / Audit API: append scorers here — Country Desk picks max, no rewrite.
COMMERCIAL_PRODUCT_SCORERS: tuple[tuple[str, str, str, CommercialScorer], ...] = (
    ("website", "Website", "website", _score_website),
    ("platform_api", "Platform API", "api", _score_platform_api),
)


def score_commercial_offers(row: dict[str, Any] | None) -> dict[str, Any]:
    """Rank sellable products for one Country Desk lead — pick highest score."""
    if not row:
        return {
            "ok": True,
            "products": [],
            "selected_id": "website",
            "selected_lane": "website",
            "selected_score": 0,
            "forced": False,
        }
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    forced = str(meta.get("offer_lane") or row.get("offer_lane") or "").strip().lower()
    products: list[dict[str, Any]] = []
    for pid, label, lane, scorer in COMMERCIAL_PRODUCT_SCORERS:
        products.append(
            {
                "id": pid,
                "label": label,
                "lane": lane,
                "score": int(scorer(row, meta)),
            }
        )
    products.sort(key=lambda p: (-int(p["score"]), p["id"]))
    if forced in ("website", "api"):
        match = next((p for p in products if p["lane"] == forced), None)
        selected = match or products[0]
        return {
            "ok": True,
            "products": products,
            "selected_id": selected["id"],
            "selected_lane": forced,
            "selected_score": int(selected["score"]),
            "forced": True,
        }
    best = products[0] if products else {
        "id": "website",
        "lane": "website",
        "score": 0,
    }
    return {
        "ok": True,
        "products": products,
        "selected_id": best["id"],
        "selected_lane": best["lane"],
        "selected_score": int(best["score"]),
        "forced": False,
        "note_ru": (
            "Country Desk выбирает продукт по max(score). "
            "Не жёсткое правило SaaS→API. Commercial Engine ≠ Farm Earn."
        ),
    }


def resolve_offer_lane(row: dict[str, Any] | None) -> str:
    """website | api — from product scores (max), not a hard niche map."""
    return str(score_commercial_offers(row).get("selected_lane") or "website")


class PlatformApiBilling:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._keys = CommercialApiKeyStore(memory_dir)
        self._checkout = PaymentCheckoutService(memory_dir)
        self._finance = FinanceService(memory_dir)

    def packages_public(self) -> list[dict[str, Any]]:
        out = []
        for p in list_packages(self._memory):
            out.append(
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "price_eur": float(p.get("price_eur") or 0),
                    "balance_eur": float(p.get("balance_eur") or p.get("price_eur") or 0),
                    "scopes": list(p.get("scopes") or ["audit"]),
                    "note_ru": p.get("note_ru") or "",
                    "best_for_ru": p.get("best_for_ru") or "",
                }
            )
        return out

    def create_checkout(
        self,
        *,
        package_id: str,
        customer_email: str,
        success_url: str | None = None,
        cancel_url: str | None = None,
    ) -> dict[str, Any]:
        pkg = get_package(package_id, self._memory)
        if not pkg:
            return {"ok": False, "reason": "unknown_package", "http_status": 404}
        email = (customer_email or "").strip().lower()
        if "@" not in email:
            return {"ok": False, "reason": "email_required", "http_status": 400}
        price = float(pkg.get("price_eur") or 0)
        if price <= 0:
            return {"ok": False, "reason": "invalid_price", "http_status": 400}

        base = configured_public_base().rstrip("/")
        success = (
            success_url
            or f"{base}/api-access?paid=1&session_id={{CHECKOUT_SESSION_ID}}"
        ).strip()
        cancel = (cancel_url or f"{base}/api-access").strip()
        # Synthetic order_id for Stripe metadata + finance settlement link
        order_id = f"api_{pkg['id']}_{email.split('@')[0][:12]}"
        label = f"Virtus Core Platform API · {pkg.get('name') or pkg['id']}"
        extra_meta = {
            "product": "commercial_api_package",
            "package_id": str(pkg["id"]),
            "customer_email": email[:160],
        }

        try:
            session = self._checkout.create_checkout(
                order_id=order_id,
                amount_eur=price,
                label=label,
                success_url=success,
                cancel_url=cancel,
                currency="eur",
                market_code="DE",
                extra_metadata=extra_meta,
            )
        except ValueError as exc:
            return {"ok": False, "reason": str(exc), "http_status": 503}

        if session.get("provider") == "sandbox":
            # Immediate fulfill in sandbox for local QA — no /order/pay redirect
            fulfilled = self.fulfill_package_payment(
                package_id=str(pkg["id"]),
                customer_email=email,
                amount_eur=price,
                session_id=str(session.get("session_id") or ""),
                payment_intent="sandbox",
                order_id=order_id,
            )
            return {
                "ok": True,
                "provider": "sandbox",
                "checkout_url": f"{base}/api-access?paid=1&sandbox=1",
                "session_id": session.get("session_id"),
                "package_id": pkg["id"],
                "price_eur": price,
                "sandbox": True,
                "fulfilled": fulfilled,
            }

        return {
            "ok": True,
            "provider": session.get("provider"),
            "checkout_url": session.get("checkout_url"),
            "session_id": session.get("session_id"),
            "package_id": pkg["id"],
            "price_eur": price,
            "sandbox": bool(session.get("sandbox")),
        }

    def _annotate_stripe_session(
        self,
        *,
        session_id: str,
        package_id: str,
        customer_email: str,
        order_id: str,
    ) -> None:
        import os

        import httpx

        secret = os.getenv("STRIPE_SECRET_KEY", "").strip() or os.getenv(
            "STRIPE_SECRET_KEY_LIVE", ""
        ).strip()
        if not secret or not session_id:
            return
        data = {
            "metadata[product]": "commercial_api_package",
            "metadata[package_id]": package_id,
            "metadata[customer_email]": customer_email[:160],
            "metadata[order_id]": order_id,
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                client.post(
                    f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
                    data=data,
                    auth=(secret, ""),
                )
        except Exception:
            pass

    def confirm_paid_session(self, session_id: str) -> dict[str, Any]:
        """Buyer return path — fulfill Platform API if Stripe session is paid."""
        sid = (session_id or "").strip()
        if not sid:
            return {"ok": False, "reason": "session_id_required", "http_status": 400}
        existing = self.already_fulfilled(sid)
        if existing:
            return {
                "ok": True,
                "already_processed": True,
                "package_id": existing.get("package_id"),
                "key_prefix": existing.get("key_prefix"),
                "balance_eur": existing.get("balance_eur"),
                "customer_email": existing.get("customer_email"),
                "note_ru": "Ключ уже выдан — проверьте email.",
            }
        if sid.startswith("sandbox-"):
            return {
                "ok": False,
                "reason": "sandbox_use_checkout_response",
                "http_status": 404,
                "note_ru": "Sandbox ключ приходит сразу из POST /checkout.",
            }
        parsed = self._checkout.retrieve_paid_session(sid)
        if not parsed:
            return {
                "ok": False,
                "reason": "payment_not_confirmed",
                "http_status": 402,
                "note_ru": "Оплата ещё не подтверждена — подождите webhook или обновите страницу.",
            }
        product = str(parsed.get("product") or "")
        package_id = str(parsed.get("package_id") or "")
        order_id = str(parsed.get("order_id") or "")
        if product != "commercial_api_package" and not order_id.startswith("api_"):
            return {
                "ok": False,
                "reason": "not_platform_api",
                "http_status": 400,
            }
        if not package_id and order_id.startswith("api_"):
            # api_{package}_{emailslug}
            parts = order_id.split("_")
            package_id = parts[1] if len(parts) >= 2 else ""
        email = str(parsed.get("customer_email") or parsed.get("sender") or "").strip()
        fulfilled = self.fulfill_package_payment(
            package_id=package_id,
            customer_email=email,
            amount_eur=float(parsed.get("amount_eur") or 0),
            session_id=sid,
            payment_intent=str(parsed.get("payment_intent") or ""),
            order_id=order_id,
            sender=email,
        )
        if not fulfilled.get("ok"):
            return {**fulfilled, "http_status": 400}
        return {
            "ok": True,
            "already_processed": bool(fulfilled.get("already_processed")),
            "package_id": fulfilled.get("package_id"),
            "api_key": fulfilled.get("api_key"),
            "key_prefix": fulfilled.get("key_prefix")
            or (str(fulfilled.get("api_key") or "")[:12]),
            "balance_eur": fulfilled.get("balance_eur"),
            "customer_email": email,
            "email_sent": fulfilled.get("email_sent"),
            "note_ru": (
                "Ключ выдан. Сохраните его — повторный показ только в email."
                if fulfilled.get("api_key")
                else "Ключ отправлен на email."
            ),
        }

    def already_fulfilled(self, session_id: str) -> dict[str, Any] | None:
        sid = (session_id or "").strip()
        if not sid:
            return None
        path = self._memory / FULFILLMENTS_FILE
        if not path.is_file():
            return None
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if str(row.get("session_id") or "") == sid:
                    return row
        except (json.JSONDecodeError, OSError):
            return None
        return None

    def fulfill_package_payment(
        self,
        *,
        package_id: str,
        customer_email: str,
        amount_eur: float,
        session_id: str,
        payment_intent: str = "",
        order_id: str = "",
        sender: str = "",
    ) -> dict[str, Any]:
        existing = self.already_fulfilled(session_id)
        if existing:
            return {"ok": True, "already_processed": True, **existing}

        pkg = get_package(package_id, self._memory)
        if not pkg:
            return {"ok": False, "reason": "unknown_package"}

        email = (customer_email or sender or "").strip().lower()
        key_row = self._keys.create_from_package(
            package=pkg,
            label=f"Platform API · {pkg.get('name')}",
            customer_email=email,
            prefix="vk_live_",
        )
        api_key = str(key_row.get("api_key") or "")
        if api_key.startswith("vc_"):
            api_key = self._keys.reissue_with_prefix(key_row["id"], prefix="vk_live_") or api_key

        oid = order_id or f"api_{package_id}_{session_id[:12]}"
        self._finance.credit_order_payment(
            float(amount_eur),
            f"Platform API · {pkg.get('name')} · {email}",
            provider="stripe" if not str(payment_intent).startswith("sandbox") else "sandbox",
            order_id=oid,
            sender=email,
            external_id=session_id or payment_intent,
        )

        record = {
            "at": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "payment_intent": payment_intent,
            "package_id": package_id,
            "order_id": oid,
            "customer_email": email,
            "amount_eur": round(float(amount_eur), 2),
            "key_id": key_row.get("id"),
            "key_prefix": (api_key or "")[:12],
            "balance_eur": key_row.get("balance_eur"),
        }
        self._append_fulfillment(record)
        mail = self._send_key_email(email=email, api_key=api_key, package=pkg)
        return {
            "ok": True,
            "already_processed": False,
            "api_key": api_key,
            "key_id": key_row.get("id"),
            "balance_eur": key_row.get("balance_eur"),
            "package_id": package_id,
            "email_sent": bool(mail.get("ok")),
            "mail": mail,
            **{k: v for k, v in record.items() if k != "at"},
        }

    def _append_fulfillment(self, row: dict[str, Any]) -> None:
        path = self._memory / FULFILLMENTS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _send_key_email(
        self, *, email: str, api_key: str, package: dict[str, Any]
    ) -> dict[str, Any]:
        if not email or not api_key:
            return {"ok": False, "reason": "missing"}
        try:
            from app.integration.receipt_email_service import ReceiptEmailService

            base = configured_public_base().rstrip("/")
            pkg_name = str(package.get("name") or package.get("id") or "Starter")
            subject = f"Virtus Core Platform API — {pkg_name} key"
            text = (
                f"Thank you for purchasing Virtus Core Platform API ({pkg_name}).\n\n"
                f"Your API key (keep secret):\n{api_key}\n\n"
                f"Example:\n"
                f"curl -X POST {base}/api/v1/audit \\\n"
                f'  -H "X-API-Key: {api_key}" \\\n'
                f'  -H "Content-Type: application/json" \\\n'
                f'  -d \'{{"url":"https://example.com","locale":"de"}}\'\n\n'
                f"Packages & docs: {base}/api-access\n"
                f"OpenAPI: {base}/api/v1/openapi.json\n"
            )
            return ReceiptEmailService(self._memory)._send(  # noqa: SLF001
                to=email,
                subject=subject,
                text=text,
                html=None,
            )
        except Exception as exc:
            return {"ok": False, "reason": str(exc)[:120]}

    def maybe_low_balance_topup(self, account: dict[str, Any]) -> dict[str, Any] | None:
        """Send one top-up email per 7 days when balance is low."""
        bal = float(account.get("balance_eur") or 0)
        pkg_id = str(account.get("package_id") or "starter")
        pkg = get_package(pkg_id, self._memory) or get_package("starter", self._memory)
        if not pkg:
            return None
        from app.commercial_api.pricing import price_eur

        unit = float(price_eur("audit", self._memory) or 0.5)
        start_bal = float(pkg.get("balance_eur") or pkg.get("price_eur") or 24)
        audits_left = int(bal / unit) if unit > 0 else 0
        low = bal <= start_bal * 0.05 or audits_left <= 3
        if not low or bal <= 0:
            return None
        email = str(account.get("customer_email") or "").strip()
        key_id = str(account.get("id") or "")
        if not email or not key_id:
            return None
        if self._topup_cooldown_active(key_id):
            return {"skipped": True, "reason": "cooldown"}
        base = configured_public_base().rstrip("/")
        link = f"{base}/api-access?package={pkg_id}&topup=1"
        try:
            from app.integration.receipt_email_service import ReceiptEmailService

            text = (
                f"Your Virtus Core Platform API balance is low ({bal:.2f} € · ~{audits_left} audits left).\n"
                f"Top up: {link}\n"
            )
            mail = ReceiptEmailService(self._memory)._send(  # noqa: SLF001
                to=email,
                subject="Virtus Core API — balance low, top up",
                text=text,
                html=None,
            )
            if mail.get("ok"):
                self._mark_topup_sent(key_id)
            return mail
        except Exception as exc:
            return {"ok": False, "reason": str(exc)[:120]}

    def _topup_cooldown_active(self, key_id: str) -> bool:
        path = self._memory / LOW_BALANCE_COOLDOWN_FILE
        if not path.is_file():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False
        at = str((data.get(key_id) or {}).get("at") or "")
        if not at:
            return False
        try:
            sent = datetime.fromisoformat(at.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - sent).total_seconds() < 7 * 86400
        except ValueError:
            return False

    def _mark_topup_sent(self, key_id: str) -> None:
        path = self._memory / LOW_BALANCE_COOLDOWN_FILE
        data: dict[str, Any] = {}
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        data[key_id] = {"at": datetime.now(timezone.utc).isoformat()}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def analytics(self) -> dict[str, Any]:
        """CEO usage analytics per key — gated until first paid API buyer."""
        from app.commercial_api.pricing import price_eur

        path = self._memory / FULFILLMENTS_FILE
        paid_n = 0
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if float(row.get("amount_eur") or 0) > 0:
                    paid_n += 1
        if paid_n <= 0:
            return {
                "title_ru": "Platform API · Usage Analytics",
                "phase": "awaiting_first_buyer",
                "keys": [],
                "summary": {
                    "keys": 0,
                    "buyers": 0,
                    "revenue_eur": 0.0,
                    "debited_eur": 0.0,
                    "profit_est_eur": 0.0,
                },
                "gate_ru": (
                    "Сначала 1 API-покупатель (Micro 5 € или Starter) → потом Analytics. "
                    "Пустые графики Profit/Latency до первой оплаты не показываем."
                ),
            }

        unit = float(price_eur("audit", self._memory) or 0.5)
        keys = self._keys.list_public()
        usage = self._keys.recent_usage(limit=5000)
        by_key: dict[str, dict[str, Any]] = {}
        for k in keys:
            kid = str(k.get("id"))
            by_key[kid] = {
                "key_id": kid,
                "label": k.get("label"),
                "customer_email": k.get("customer_email"),
                "package_id": k.get("package_id"),
                "balance_eur": float(k.get("balance_eur") or 0),
                "requests": int(k.get("requests") or 0),
                "revenue_eur": 0.0,
                "debited_eur": 0.0,
                "latencies_ms": [],
            }
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kid = str(row.get("key_id") or "")
                if kid in by_key:
                    by_key[kid]["revenue_eur"] = round(
                        by_key[kid]["revenue_eur"] + float(row.get("amount_eur") or 0), 2
                    )
        for u in usage:
            kid = str(u.get("key_id") or "")
            if kid not in by_key:
                continue
            amt = float(u.get("amount_eur") or 0)
            if amt < 0:
                by_key[kid]["debited_eur"] = round(by_key[kid]["debited_eur"] + abs(amt), 4)
            lat = u.get("latency_ms")
            if lat is not None:
                try:
                    by_key[kid]["latencies_ms"].append(float(lat))
                except (TypeError, ValueError):
                    pass
        rows = []
        for kid, r in by_key.items():
            lats = r.pop("latencies_ms")
            avg_lat = round(sum(lats) / len(lats), 1) if lats else None
            # Execution cost proxy until per-call LLM metering: ~15% of debit
            cost_est = round(float(r["debited_eur"]) * 0.15, 2)
            profit = round(float(r["revenue_eur"]) - cost_est, 2)
            rows.append(
                {
                    **r,
                    "execution_cost_est_eur": cost_est,
                    "profit_est_eur": profit,
                    "avg_latency_ms": avg_lat,
                    "audits_left_est": int(float(r["balance_eur"]) / unit) if unit else 0,
                }
            )
        rows.sort(key=lambda x: float(x.get("revenue_eur") or 0), reverse=True)
        revenue = round(sum(float(x["revenue_eur"]) for x in rows), 2)
        buyers = sum(1 for x in rows if float(x.get("revenue_eur") or 0) > 0)
        return {
            "title_ru": "Platform API · Usage Analytics",
            "phase": "live",
            "keys": rows,
            "summary": {
                "keys": len(rows),
                "buyers": buyers,
                "revenue_eur": revenue,
                "debited_eur": round(sum(float(x["debited_eur"]) for x in rows), 2),
                "profit_est_eur": round(sum(float(x["profit_est_eur"]) for x in rows), 2),
            },
        }


def draft_platform_api_letter(
    *,
    company: str,
    lang: str = "de",
) -> tuple[str, str]:
    """Deterministic outreach for Platform API lane."""
    base = configured_public_base().rstrip("/")
    cta = f"{base}/api-access"
    name = (company or "Ihr Team").strip() or "Ihr Team"
    if lang.startswith("de"):
        subject = f"{name}: Virtus Core Platform API (Website-Audit per API)"
        body = (
            f"Guten Tag,\n\n"
            f"für Teams wie {name}, die Websites programmatisch prüfen wollen, "
            f"gibt es Virtus Core Platform API: URL rein → strukturierter Audit-Report raus.\n\n"
            f"Prepaid ab Micro — Key sofort nach Stripe-Zahlung.\n"
            f"Start: {cta}\n\n"
            f"Viele Grüße\nVirtus Core"
        )
    elif lang.startswith("ru"):
        subject = f"{name}: Virtus Core Platform API (аудит сайта по API)"
        body = (
            f"Здравствуйте,\n\n"
            f"для команд вроде {name}, которым нужен программный аудит сайтов: "
            f"Virtus Core Platform API — URL → отчёт.\n\n"
            f"Prepaid Micro/Starter/Pro — ключ сразу после оплаты Stripe.\n"
            f"{cta}\n\n"
            f"Virtus Core"
        )
    else:
        subject = f"{name}: Virtus Core Platform API (site audit via API)"
        body = (
            f"Hello,\n\n"
            f"For teams like {name} that need programmatic site audits: "
            f"Virtus Core Platform API — send a URL, get a structured report.\n\n"
            f"Prepaid Micro/Starter/Pro — API key issued automatically after Stripe.\n"
            f"Start: {cta}\n\n"
            f"Virtus Core"
        )
    return subject, body
