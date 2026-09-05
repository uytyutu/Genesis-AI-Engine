"""HTTP API — Virtus Office (Stage 1–5 + CC-2 payment + CC-3/4 delivery).

OFFICE_PIPELINE_LIVE flipped by owner for soft-beta (2026-09-05).
Owner token OR Client Workspace bearer (for owned jobs).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Header, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field

from app.integration.virtus_office.job_engine import OfficeJobEngine, OfficeJobError
from app.integration.virtus_office.language_catalog import catalog_public
from app.integration.virtus_office.office_job_ssot import (
    OFFICE_JOB_STATUSES,
    OFFICE_PIPELINE_LIVE,
    OFFICE_PRICE_MATRIX_EUR,
    office_stripe_live,
)
from app.integration.virtus_office.payment_bridge import (
    lock_and_begin_checkout,
    mark_payment_outcome,
)

router = APIRouter(prefix="/api/office", tags=["virtus-office"])


def _engine() -> OfficeJobEngine:
    from app.main import _memory_dir

    return OfficeJobEngine(_memory_dir())


class CreateJobBody(BaseModel):
    owner_hint: str | None = Field(default=None, max_length=64)
    service_preset: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=160)


class SelectActionBody(BaseModel):
    action_id: str = Field(..., min_length=2, max_length=32)
    target_language: str | None = Field(default=None, max_length=16)
    source_language: str | None = Field(default=None, max_length=16)
    output_format: str | None = Field(default=None, max_length=16)
    document_settings: dict[str, Any] | None = None
    special_wishes: str | None = Field(default=None, max_length=2000)
    confirm_settings: bool = True


class DocumentSettingsBody(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
    special_wishes: str | None = Field(default=None, max_length=2000)
    confirm: bool = False
    action_id: str | None = Field(default=None, max_length=32)
    target_language: str | None = Field(default=None, max_length=16)
    source_language: str | None = Field(default=None, max_length=16)
    output_format: str | None = Field(default=None, max_length=16)


class BewerbungProfileBody(BaseModel):
    profile: dict[str, Any] = Field(default_factory=dict)
    action_id: str | None = Field(default=None, max_length=32)
    output_format: str | None = Field(default=None, max_length=16)


class CheckoutBody(BaseModel):
    success_url: str = Field(..., min_length=8, max_length=800)
    cancel_url: str = Field(..., min_length=8, max_length=800)
    email: str | None = Field(default=None, max_length=160)
    price_eur: float | None = None


class PaymentOutcomeBody(BaseModel):
    outcome: str = Field(..., min_length=4, max_length=16)


class ClaimDeliveryBody(BaseModel):
    delivery_token: str = Field(..., min_length=16, max_length=128)


def _http_error(exc: OfficeJobError) -> HTTPException:
    status = {
        "not_found": 404,
        "forbidden": 403,
        "invalid_state": 409,
        "already_ingested": 409,
        "not_ready": 409,
        "payment_required": 403,
        "price_locked": 403,
        "price_mismatch": 403,
        "price_lock_tampered": 403,
        "price_lock_missing": 403,
        "no_artifact": 404,
        "profile_incomplete": 400,
        "empty_upload": 400,
        "invalid_preset": 400,
        "invalid_action": 400,
        "action_required": 400,
        "target_language_required": 400,
        "unsupported_action": 400,
        "quality_gate_failed": 409,
        "format_unavailable": 404,
        "payment_not_configured": 503,
        "checkout_failed": 502,
        "already_paid": 409,
        "not_locked": 409,
        "invalid_outcome": 400,
        "invalid_price": 400,
    }.get(exc.code, 400)
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message})


def _token_or_401(token: str | None) -> str:
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"code": "token_required", "message": "X-Office-Owner-Token fehlt"},
        )
    return token


def _optional_client(request: Request) -> tuple[str | None, str | None]:
    """Reuse Client Workspace bearer when present — no second account stack."""
    try:
        from app.integration.customer_identity.auth import verify_client_bearer

        payload = verify_client_bearer(request)
        if not payload:
            return None, None
        cid = str(payload.get("sub") or "").strip() or None
        email = str(payload.get("email") or "").strip().lower() or None
        return cid, email
    except Exception:
        return None, None


def _require_client(request: Request) -> tuple[str, str | None]:
    from app.integration.customer_identity.auth import require_client

    payload = require_client(request)
    cid = str(payload["sub"])
    email = str(payload.get("email") or "").strip().lower() or None
    if not email:
        try:
            from app.main import _customer_identity

            me = _customer_identity().me(cid)
            email = str((me.get("account") or {}).get("email") or "").strip().lower() or None
        except Exception:
            email = None
    return cid, email


@router.get("/status")
def office_engine_status() -> dict[str, Any]:
    from app.integration.virtus_office.bewerbung_ssot import (
        BEWERBUNG_DISCLAIMER_DE,
        bewerbung_action_meta,
    )
    from app.integration.virtus_office.ocr_engine import ocr_capabilities
    from app.integration.virtus_office.office_job_ssot import (
        OFFICE_SELLABLE_NOW,
        OFFICE_SKU_ROADMAP,
        OFFICE_VITRINE_FORBIDDEN,
    )
    from app.integration.virtus_office.office_capability_audit import (
        audit_matrix,
        report_table,
    )

    caps = audit_matrix()
    return {
        "ok": True,
        "product": "virtus_office",
        "pipeline_live": OFFICE_PIPELINE_LIVE,
        "stage": "CC-4",
        "stage_label": "bewerbung_2_digital_delivery",
        "stripe_live": office_stripe_live(),
        "statuses": list(OFFICE_JOB_STATUSES),
        "price_matrix_eur": OFFICE_PRICE_MATRIX_EUR,
        "languages": catalog_public(),
        "executable_actions": list(OFFICE_SELLABLE_NOW),
        "sellable_skus": caps["sellable_skus"],
        "sku_roadmap": list(OFFICE_SKU_ROADMAP),
        "vitrine_forbidden": list(OFFICE_VITRINE_FORBIDDEN),
        "vitrine_skus": caps["vitrine_skus"],
        "product_rule": caps["product_rule"],
        "capability_audit": {
            "by_status": caps["by_status"],
            "rows": caps["rows"],
            "inconsistencies": caps["inconsistencies"],
            "b2b_packages": caps["b2b_packages"],
            "next_b2b_candidates": caps["next_b2b_candidates"],
            "live_gate": caps["live_gate"],
            "report_table": report_table(),
        },
        "country_pricing": False,
        "bewerbung": {
            "actions": bewerbung_action_meta(),
            "disclaimer_de": BEWERBUNG_DISCLAIMER_DE,
        },
        "ocr": ocr_capabilities(),
        "note": (
            "OFFICE_PIPELINE_LIVE=True (owner soft-beta). "
            "stripe_live follows PaymentCheckoutService.is_live_mode(). "
            "Client vitrine = SELLABLE only; roadmap SKUs stay internal until validators PASS."
        ),
    }


@router.get("/languages")
def office_languages() -> dict[str, Any]:
    return {"ok": True, **catalog_public()}


@router.get("/cabinet")
def office_cabinet(request: Request) -> dict[str, Any]:
    """Meine Aufträge — Client Workspace identity."""
    cid, email = _require_client(request)
    jobs = _engine().list_for_customer(customer_id=cid, email=email, limit=50)
    # Rechnungen via Core office orders
    invoices: list[dict[str, Any]] = []
    try:
        from app.main import _ctx

        orders = _ctx().sales.list_orders_for_customer(
            customer_id=cid, email=email, limit=50
        )
        for o in orders:
            pkg = str(o.get("package_id") or "")
            kind = str(o.get("product_kind") or "")
            if kind == "office" or pkg.startswith("office_"):
                invoices.append(
                    {
                        "order_id": o.get("order_id"),
                        "status": o.get("status"),
                        "price_eur": o.get("price_eur"),
                        "price_label": o.get("price_label"),
                        "package_name": o.get("package_name"),
                        "paid_at": o.get("paid_at"),
                        "receipt_path": f"/order/status/{o.get('order_id')}",
                        "office_job_id": o.get("office_job_id"),
                    }
                )
    except Exception:
        invoices = []
    downloads = [j for j in jobs if j.get("download_ready")]
    files = [
        {
            "job_id": j.get("job_id"),
            "filename": j.get("filename"),
            "artifact_filename": j.get("artifact_filename"),
            "artifact_ext": j.get("artifact_ext"),
            "status": j.get("status"),
            "download_ready": j.get("download_ready"),
        }
        for j in jobs
        if j.get("filename") or j.get("artifact_filename")
    ]
    return {
        "ok": True,
        "jobs": jobs,
        "files": files,
        "invoices": invoices,
        "downloads": downloads,
    }


@router.post("/jobs")
def create_office_job(request: Request, body: CreateJobBody | None = None) -> dict[str, Any]:
    hint = (body.owner_hint if body else None) or None
    preset = (body.service_preset if body else None) or None
    email = (body.email if body else None) or None
    cid, client_email = _optional_client(request)
    try:
        created = _engine().create_job(
            owner_hint=hint,
            service_preset=preset,
            customer_id=cid,
            email=email or client_email,
        )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **created}


@router.get("/jobs/{job_id}")
def get_office_job(
    request: Request,
    job_id: str,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    eng = _engine()
    try:
        if x_office_owner_token:
            view = eng.get_job(job_id, owner_token=x_office_owner_token)
        else:
            cid, email = _optional_client(request)
            if not cid:
                raise HTTPException(
                    status_code=401,
                    detail={"code": "token_required", "message": "X-Office-Owner-Token fehlt"},
                )
            view = eng.get_for_customer(job_id, customer_id=cid, email=email)
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/upload")
async def upload_office_job_file(
    job_id: str,
    file: UploadFile = File(...),
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = _engine().upload(job_id, owner_token=token, upload=file)
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/upload-pages")
async def upload_office_job_pages(
    job_id: str,
    files: list[UploadFile] = File(...),
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = _engine().upload_pages(job_id, owner_token=token, uploads=list(files or []))
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/select-action")
def select_office_action(
    job_id: str,
    body: SelectActionBody,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = _engine().select_action(
            job_id,
            owner_token=token,
            action_id=body.action_id,
            target_language=body.target_language,
            source_language=body.source_language,
            output_format=body.output_format,
            document_settings=body.document_settings,
            special_wishes=body.special_wishes,
            confirm_settings=body.confirm_settings,
        )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/document-settings")
def configure_document_settings(
    job_id: str,
    body: DocumentSettingsBody,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = _engine().configure_document_settings(
            job_id,
            owner_token=token,
            values=body.values,
            special_wishes=body.special_wishes,
            confirm=body.confirm,
            action_id=body.action_id,
            target_language=body.target_language,
            source_language=body.source_language,
            output_format=body.output_format,
        )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/bewerbung-profile")
def submit_bewerbung_profile(
    job_id: str,
    body: BewerbungProfileBody,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = _engine().submit_bewerbung_profile(
            job_id,
            owner_token=token,
            profile=body.profile or {},
            action_id=body.action_id,
            output_format=body.output_format,
        )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/bewerbung-photo")
async def attach_bewerbung_photo(
    job_id: str,
    file: UploadFile = File(...),
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = _engine().attach_bewerbung_photo(job_id, owner_token=token, upload=file)
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/checkout")
def checkout_office_job(
    request: Request,
    job_id: str,
    body: CheckoutBody,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    cid, client_email = _optional_client(request)
    try:
        view = lock_and_begin_checkout(
            _engine(),
            job_id,
            owner_token=token,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            email=body.email or client_email,
            customer_id=cid,
            client_price_eur=body.price_eur,
        )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/claim-delivery")
def claim_office_delivery(job_id: str, body: ClaimDeliveryBody) -> dict[str, Any]:
    """Scoped email link → validate delivery token (no owner_token in email)."""
    from app.integration.virtus_office.digital_product_delivery import claim_delivery_access

    try:
        view = claim_delivery_access(
            _engine(), job_id, delivery_token=body.delivery_token
        )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/payment-outcome")
def office_payment_outcome(
    job_id: str,
    body: PaymentOutcomeBody,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = mark_payment_outcome(
            _engine(),
            job_id,
            owner_token=token,
            outcome=body.outcome,
        )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.post("/jobs/{job_id}/continue")
@router.post("/jobs/{job_id}/execute")
def execute_office_job(
    request: Request,
    job_id: str,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    eng = _engine()
    try:
        if x_office_owner_token:
            view = eng.execute(job_id, owner_token=x_office_owner_token)
        else:
            cid, email = _optional_client(request)
            if not cid:
                raise HTTPException(
                    status_code=401,
                    detail={"code": "token_required", "message": "X-Office-Owner-Token fehlt"},
                )
            view = eng.execute_for_customer(job_id, customer_id=cid, email=email)
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}


@router.get("/jobs/{job_id}/artifact")
def download_office_artifact(
    request: Request,
    job_id: str,
    format: str | None = Query(default=None, alias="format"),
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
    x_office_delivery_token: str | None = Header(default=None, alias="X-Office-Delivery-Token"),
    delivery_token: str | None = Query(default=None),
):
    from fastapi.responses import Response

    eng = _engine()
    dt = x_office_delivery_token or delivery_token
    try:
        if x_office_owner_token:
            data, filename, mime = eng.get_artifact_bytes(
                job_id, owner_token=x_office_owner_token, fmt=format
            )
        elif dt:
            data, filename, mime = eng.get_artifact_with_delivery_token(
                job_id, delivery_token=dt, fmt=format
            )
        else:
            cid, email = _optional_client(request)
            if not cid:
                raise HTTPException(
                    status_code=401,
                    detail={"code": "token_required", "message": "X-Office-Owner-Token fehlt"},
                )
            data, filename, mime = eng.get_artifact_for_customer(
                job_id, customer_id=cid, email=email, fmt=format
            )
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return Response(
        content=data,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )


@router.post("/jobs/{job_id}/cancel")
def cancel_office_job(
    job_id: str,
    x_office_owner_token: str | None = Header(default=None, alias="X-Office-Owner-Token"),
) -> dict[str, Any]:
    token = _token_or_401(x_office_owner_token)
    try:
        view = _engine().cancel(job_id, owner_token=token)
    except OfficeJobError as exc:
        raise _http_error(exc) from exc
    return {"ok": True, **view}
