"""Virtus Video AI public API — catalog, create studio, billing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.integration.viewora import orchestrator as orch
from app.integration.viewora.billing import VieworaBilling
from app.integration.viewora.product import public_catalog
from app.integration.viewora.store import VieworaStore

router = APIRouter(prefix="/api/viewora", tags=["viewora"])


def _memory(request: Request) -> Path:
    del request
    import os

    mem = os.getenv("GENESIS_MEMORY_DIR", "").strip()
    if mem:
        return Path(mem)
    return Path(__file__).resolve().parents[2] / "memory"


class CreateBody(BaseModel):
    account_id: str | None = None
    brief: str = Field(..., min_length=1, max_length=4000)
    creation_type: str = "viral_short"
    mode: str | None = None
    visual_dna: dict[str, str] | None = None
    product_style: str | None = None
    action: str = "create"


class CheckoutBody(BaseModel):
    account_id: str | None = None
    kind: str = Field(..., pattern="^(plan|credits)$")
    sku: str
    email: str = ""
    success_url: str = ""
    cancel_url: str = ""
    prefer_demo: bool = False


class AccountBody(BaseModel):
    account_id: str | None = None


@router.get("/catalog")
def catalog() -> dict[str, Any]:
    return {"ok": True, **public_catalog()}


@router.post("/account")
def account(body: AccountBody, request: Request) -> dict[str, Any]:
    billing = VieworaBilling(_memory(request))
    snap = billing.account_snapshot(body.account_id)
    return {"ok": True, **snap}


@router.post("/create")
def create(body: CreateBody, request: Request) -> dict[str, Any]:
    billing = VieworaBilling(_memory(request))
    store = VieworaStore(_memory(request))
    snap = billing.account_snapshot(body.account_id)
    account = snap["account"]

    action = (body.action or "create").strip().lower()
    spend_action = {
        "create": "create",
        "make_it_better": "make_it_better",
        "generate_10": "generate_10",
        "hook_lab": "hook_lab",
        "test_hooks": "test_hooks",
        "optimize": "optimize_score",
        "product_video": "product_video",
        "podcast_shorts": "podcast_shorts",
        "content_machine": "content_machine_30",
        "random_style": "create",
        "dubbing": "dubbing_lang",
        "ai_creator_batch": "ai_creator_batch",
        "viral_lab": "viral_lab",
    }.get(action, "create")

    try:
        account = billing.spend(account, action=spend_action)
    except ValueError as exc:
        raise HTTPException(
            status_code=402,
            detail={
                "code": str(exc),
                "message": "Недостаточно кредитов или бесплатных creations. Выберите план.",
                "pricing_path": "/viewora/pricing",
            },
        ) from exc

    brief = body.brief.strip()
    result: dict[str, Any]

    if action == "make_it_better":
        suggestion = orch.suggest_better(brief, body.creation_type)
        result = {
            "suggestion": suggestion,
            "package": orch.build_package(
                brief=brief,
                creation_type=body.creation_type,
                mode=suggestion["mode"],
                visual_dna=suggestion["visual_dna"],
            ),
        }
    elif action == "generate_10":
        result = {"versions": orch.generate_ten(brief, body.creation_type)}
    elif action == "hook_lab":
        result = orch.hook_lab(brief)
    elif action == "test_hooks":
        lab = orch.hook_lab(brief)
        result = {"test_hooks": lab["test_hooks"], "hooks": lab["hooks"][:10]}
    elif action == "optimize":
        pkg = orch.build_package(
            brief=brief,
            creation_type=body.creation_type,
            mode=body.mode,
            visual_dna=body.visual_dna,
        )
        score = dict(pkg.get("watchability") or pkg["viral_score"])
        weak = score["weakest"]
        score["scores"] = dict(score["scores"])
        score["scores"][weak] = min(99, int(score["scores"][weak]) + 8)
        score["overall"] = round(sum(score["scores"].values()) / 5)
        score["optimized"] = True
        pkg["watchability"] = score
        pkg["viral_score"] = score
        result = {"package": pkg}
    elif action == "viral_lab":
        result = orch.viral_lab(brief, body.creation_type)
    elif action == "product_video":
        result = {
            "package": orch.product_video_brief(
                brief, body.product_style or "TikTok style"
            )
        }
    elif action == "podcast_shorts":
        result = orch.podcast_to_shorts(brief, 20)
    elif action == "content_machine":
        result = orch.content_machine_30(brief)
    elif action == "random_style":
        dna = orch.random_style()
        result = {
            "visual_dna": dna,
            "package": orch.build_package(
                brief=brief,
                creation_type=body.creation_type,
                mode=body.mode,
                visual_dna=dna,
            ),
        }
    elif action == "dubbing":
        result = orch.dubbing_pack(brief)
    elif action == "ai_creator_batch":
        result = orch.ai_creator_batch(brief, 5)
    else:
        result = {
            "package": orch.build_package(
                brief=brief,
                creation_type=body.creation_type,
                mode=body.mode,
                visual_dna=body.visual_dna,
                product_style=body.product_style,
            )
        }

    job = store.append_job(
        {
            "account_id": account["id"],
            "action": action,
            "brief": brief[:500],
            "creation_type": body.creation_type,
            "result_summary": {
                "keys": list(result.keys()),
                "mode": (result.get("package") or {}).get("mode"),
            },
        }
    )

    return {
        "ok": True,
        "account": account,
        "job_id": job["id"],
        "action": action,
        "result": result,
    }


@router.get("/jobs")
def jobs(request: Request, account_id: str) -> dict[str, Any]:
    store = VieworaStore(_memory(request))
    return {"ok": True, "jobs": store.list_jobs(account_id)}


@router.post("/checkout")
def checkout(body: CheckoutBody, request: Request) -> dict[str, Any]:
    billing = VieworaBilling(_memory(request))
    origin = str(request.headers.get("origin") or "").rstrip("/")
    success = body.success_url or f"{origin}/viewora/success?paid=1"
    cancel = body.cancel_url or f"{origin}/viewora/pricing?canceled=1"
    out = billing.create_order(
        account_id=body.account_id or "",
        kind=body.kind,
        sku=body.sku,
        email=body.email,
        success_url=success,
        cancel_url=cancel,
        prefer_demo=body.prefer_demo,
    )
    if not out.get("ok"):
        raise HTTPException(
            status_code=int(out.get("http_status") or 400),
            detail=out.get("reason") or "checkout_failed",
        )
    return out


@router.get("/orders/{order_id}")
def order_status(order_id: str, request: Request) -> dict[str, Any]:
    billing = VieworaBilling(_memory(request))
    order = billing.order_status(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    return {"ok": True, "order": order}


@router.post("/orders/{order_id}/pay-demo")
def pay_demo(order_id: str, request: Request) -> dict[str, Any]:
    billing = VieworaBilling(_memory(request))
    out = billing.pay_demo(order_id)
    if not out.get("ok"):
        raise HTTPException(
            status_code=int(out.get("http_status") or 400),
            detail=out.get("reason") or "pay_failed",
        )
    return out


@router.post("/orders/{order_id}/pay-sandbox")
def pay_sandbox(order_id: str, request: Request) -> dict[str, Any]:
    billing = VieworaBilling(_memory(request))
    out = billing.pay_sandbox(order_id)
    if not out.get("ok"):
        raise HTTPException(
            status_code=int(out.get("http_status") or 400),
            detail=out.get("reason") or "pay_failed",
        )
    return out
