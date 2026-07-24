"""Execute metered commercial API products behind the Gateway."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.commercial_api.catalog import product
from app.commercial_api.keys import CommercialApiKeyStore
from app.commercial_api.pricing import price_eur
from app.commercial_api.rate_limit import allow_request
from app.commercial_api.sanitize import sanitize_public


class CommercialApiGateway:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._keys = CommercialApiKeyStore(memory_dir)

    @property
    def keys(self) -> CommercialApiKeyStore:
        return self._keys

    def account(self, raw_key: str) -> dict[str, Any] | None:
        row = self._keys.resolve(raw_key)
        if not row:
            return None
        return {
            "id": row["id"],
            "label": row.get("label"),
            "balance_eur": row.get("balance_eur"),
            "scopes": row.get("scopes") or [],
            "rate_limit_per_min": row.get("rate_limit_per_min"),
            "requests": row.get("requests"),
            "key_prefix": row.get("key_prefix"),
        }

    def _gate(self, raw_key: str, *, scope: str) -> dict[str, Any]:
        account = self._keys.resolve(raw_key)
        if not account:
            return {"ok": False, "reason": "invalid_api_key", "http_status": 401}
        if not self._keys.has_scope(account, scope):
            self._keys.log_event(
                key_id=str(account["id"]),
                product_id=scope,
                ok=False,
                detail="scope_denied",
            )
            return {
                "ok": False,
                "reason": "scope_denied",
                "scopes": account.get("scopes"),
                "http_status": 403,
            }
        allowed, remaining = allow_request(
            str(account["id"]),
            limit_per_min=int(account.get("rate_limit_per_min") or 100),
        )
        if not allowed:
            self._keys.log_event(
                key_id=str(account["id"]),
                product_id=scope,
                ok=False,
                detail="rate_limited",
            )
            return {
                "ok": False,
                "reason": "rate_limited",
                "retry_after_sec": 60,
                "http_status": 429,
            }
        return {"ok": True, "account": account, "rate_remaining": remaining}

    def run_audit(self, raw_key: str, *, url: str, locale: str = "de") -> dict[str, Any]:
        meta = product("audit", self._memory)
        if not meta or meta.get("status") != "live":
            return {"ok": False, "reason": "product_unavailable", "http_status": 503}
        gate = self._gate(raw_key, scope="audit")
        if not gate.get("ok"):
            return gate
        account = gate["account"]
        price = price_eur("audit", self._memory)
        debit = self._keys.debit(str(account["id"]), price, product_id="audit")
        if not debit.get("ok"):
            return {
                "ok": False,
                "reason": debit.get("reason"),
                "balance_eur": debit.get("balance_eur"),
                "price_eur": price,
                "http_status": 402,
            }
        from app.integration.website_analysis_v1 import WebsiteAnalysisV1

        report = WebsiteAnalysisV1(self._memory).analyze(
            url,
            locale=locale or "de",
            use_cache=True,
            save_case=True,
        )
        public_report = sanitize_public(report)
        return {
            "ok": True,
            "product": "audit",
            "charged_eur": price,
            "balance_eur": debit.get("balance_eur"),
            "rate_remaining": gate.get("rate_remaining"),
            "report": public_report,
            "billing": {
                "model": "pay_per_request",
                "confidence": "CONFIRMED",
                "note_ru": "Списание с prepaid-баланса API-ключа (не farm estimate).",
            },
        }

    def run_leads_preview(
        self, raw_key: str, *, city: str = "", niche: str = "", limit: int = 10
    ) -> dict[str, Any]:
        gate = self._gate(raw_key, scope="leads")
        if not gate.get("ok"):
            return gate
        account = gate["account"]
        meta = product("leads", self._memory) or {}
        price = price_eur("leads", self._memory)
        return {
            "ok": True,
            "product": "leads",
            "status": "preview",
            "charged_eur": 0.0,
            "listed_price_eur": price,
            "balance_eur": account.get("balance_eur"),
            "rate_remaining": gate.get("rate_remaining"),
            "query": {
                "city": city,
                "niche": niche,
                "limit": max(1, min(100, int(limit or 10))),
            },
            "results": [],
            "note_ru": (
                "Эндпоинт зарезервирован (API v2). Биллинг Lead Farm — следующий цикл. "
                f"Плановая цена из каталога: {price} € / pack."
            ),
        }
