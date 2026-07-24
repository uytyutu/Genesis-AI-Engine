"""FastAPI router — Virtus Commercial API Gateway v0."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.commercial_api.catalog import catalog
from app.commercial_api.gateway import CommercialApiGateway
from app.commercial_api.keys import CommercialApiKeyStore
from app.commercial_api.pricing import pricing_public, save_default_pricing_file
from app.commercial_api.revenue_lab import RevenueLab, contours

router = APIRouter(prefix="/api/v1", tags=["commercial-api"])


def _memory(request: Request) -> Path:
    del request
    import os

    mem = os.getenv("GENESIS_MEMORY_DIR", "").strip()
    if mem:
        return Path(mem)
    return Path(__file__).resolve().parent.parent / "memory"


def _gateway(request: Request) -> CommercialApiGateway:
    return CommercialApiGateway(_memory(request))


def _require_key(x_api_key: str | None) -> str:
    key = (x_api_key or "").strip()
    if not key:
        raise HTTPException(status_code=401, detail="missing_api_key")
    return key


def _require_owner(request: Request) -> None:
    from app.integration.owner_auth import owner_access_allowed

    if not owner_access_allowed(request):
        raise HTTPException(status_code=403, detail="owner_only")


class AuditBody(BaseModel):
    url: str = Field(..., min_length=4, max_length=2048)
    locale: str = Field(default="de", max_length=8)


class LeadsBody(BaseModel):
    city: str = Field(default="", max_length=120)
    niche: str = Field(default="", max_length=120)
    limit: int = Field(default=10, ge=1, le=100)


class CreateKeyBody(BaseModel):
    label: str = Field(default="client", max_length=80)
    balance_eur: float = Field(default=5.0, ge=0, le=10_000)
    customer_email: str = Field(default="", max_length=160)
    scopes: list[str] = Field(default_factory=lambda: ["audit"])
    rate_limit_per_min: int = Field(default=100, ge=1, le=1000)


class CreditBody(BaseModel):
    key_id: str = Field(..., min_length=4, max_length=32)
    amount_eur: float = Field(..., gt=0, le=10_000)
    note: str = Field(default="", max_length=200)


class LabCandidateBody(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    api_ok: bool = True
    automation_allowed: bool | None = None
    payouts: bool | None = None
    roi_note: str = Field(default="unknown", max_length=80)
    why_ru: str = Field(default="", max_length=500)
    source_type: str = Field(default="Affiliate", max_length=40)


@router.get("")
@router.get("/")
def v1_root() -> dict:
    return {
        "name": "Virtus Core Commercial API",
        "version": "v0",
        "pitch_ru": (
            "Клиенты платят Virtus за инфраструктуру (audit / leads / factory). "
            "Gateway перед ядром: ключ → scope → лимит → модуль → ответ."
        ),
        "catalog": "/api/v1/catalog",
        "pricing": "/api/v1/pricing",
        "contours": "/api/v1/contours",
        "auth": "X-API-Key",
    }


@router.get("/pricing")
def v1_pricing(request: Request) -> dict:
    return pricing_public(_memory(request))


@router.get("/catalog")
def v1_catalog(request: Request) -> dict:
    return catalog(_memory(request))


@router.get("/contours")
def v1_contours() -> dict:
    return contours()


@router.get("/me")
def v1_me(
    request: Request, x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> dict:
    account = _gateway(request).account(_require_key(x_api_key))
    if not account:
        raise HTTPException(status_code=401, detail="invalid_api_key")
    return {"ok": True, "account": account}


@router.post("/audit")
def v1_audit(
    body: AuditBody,
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    result = _gateway(request).run_audit(
        _require_key(x_api_key), url=body.url, locale=body.locale
    )
    if not result.get("ok"):
        raise HTTPException(status_code=int(result.get("http_status") or 400), detail=result)
    return result


@router.post("/leads")
def v1_leads(
    body: LeadsBody,
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    result = _gateway(request).run_leads_preview(
        _require_key(x_api_key),
        city=body.city,
        niche=body.niche,
        limit=body.limit,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=int(result.get("http_status") or 400), detail=result)
    return result


@router.post("/admin/keys")
def v1_admin_create_key(body: CreateKeyBody, request: Request) -> dict:
    _require_owner(request)
    mem = _memory(request)
    save_default_pricing_file(mem)
    store = CommercialApiKeyStore(mem)
    return {
        "ok": True,
        "key": store.create_key(
            label=body.label,
            balance_eur=body.balance_eur,
            customer_email=body.customer_email,
            scopes=body.scopes,
            rate_limit_per_min=body.rate_limit_per_min,
        ),
    }


@router.get("/admin/keys")
def v1_admin_list_keys(request: Request) -> dict:
    _require_owner(request)
    store = CommercialApiKeyStore(_memory(request))
    return {"ok": True, "keys": store.list_public(), "usage": store.recent_usage(limit=30)}


@router.post("/admin/keys/{key_id}/revoke")
def v1_admin_revoke_key(key_id: str, request: Request) -> dict:
    _require_owner(request)
    result = CommercialApiKeyStore(_memory(request)).revoke(key_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.post("/admin/credit")
def v1_admin_credit(body: CreditBody, request: Request) -> dict:
    _require_owner(request)
    result = CommercialApiKeyStore(_memory(request)).credit(
        body.key_id, body.amount_eur, note=body.note or "owner_credit"
    )
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get("/admin/lab/candidates")
def v1_lab_list(request: Request) -> dict:
    _require_owner(request)
    lab = RevenueLab(_memory(request))
    return {"ok": True, "candidates": lab.list_candidates(), "contours": contours()}


@router.post("/admin/lab/candidates")
def v1_lab_add(body: LabCandidateBody, request: Request) -> dict:
    _require_owner(request)
    lab = RevenueLab(_memory(request))
    row = lab.add_candidate(
        name=body.name,
        api_ok=body.api_ok,
        automation_allowed=body.automation_allowed,
        payouts=body.payouts,
        roi_note=body.roi_note,
        why_ru=body.why_ru,
        source_type=body.source_type,
    )
    return {"ok": True, "candidate": row}
