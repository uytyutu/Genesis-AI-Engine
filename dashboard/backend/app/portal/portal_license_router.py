"""Commercial Platform 6.5 — License HTTP.

GET  /portal/licenses
POST /portal/licenses/{license_id}/validate
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.license import LicenseError
from app.portal.license_facade import LicenseFacade
from app.portal.license_view import LicenseView, build_validation_dict

ENGINE_ID = "portal_license_router_v1"

portal_license_router = APIRouter(
    prefix="/portal",
    tags=["portal-licenses"],
)

_license_facade: LicenseFacade | None = None


def set_license_facade(facade: LicenseFacade) -> None:
    global _license_facade
    _license_facade = facade


def clear_license_facade() -> None:
    global _license_facade
    _license_facade = None


def get_license_facade() -> LicenseFacade:
    if _license_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_licenses_not_configured"
        )
    return _license_facade


@portal_license_router.get("/licenses", response_model=None)
def http_list_licenses(
    request: Request,
    licenses: Annotated[LicenseFacade, Depends(get_license_facade)],
) -> list[LicenseView]:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return licenses.list_licenses(account_id=account.account_id)


@portal_license_router.post(
    "/licenses/{license_id}/validate",
    response_model=None,
)
def http_validate_license(
    license_id: str,
    request: Request,
    licenses: Annotated[LicenseFacade, Depends(get_license_facade)],
) -> dict[str, Any]:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return build_validation_dict(
        licenses.validate(
            account_id=account.account_id, license_id=license_id
        )
    )
