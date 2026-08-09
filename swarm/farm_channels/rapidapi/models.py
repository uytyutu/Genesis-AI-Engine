"""API Farm candidate / job / revenue event schemas."""

from __future__ import annotations

from typing import Any, Literal

STATUS_DISCOVERED = "DISCOVERED"
STATUS_RESEARCHING = "RESEARCHING"
STATUS_CANDIDATE = "CANDIDATE"
STATUS_BUILDING = "BUILDING"
STATUS_TESTING = "TESTING"
STATUS_QUALITY_GATE = "QUALITY_GATE"
STATUS_QUALITY_GATE_FAILED = "QUALITY_GATE_FAILED"
STATUS_READY = "READY"
STATUS_APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
STATUS_PUBLISHING = "PUBLISHING"
STATUS_PUBLISHED = "PUBLISHED"
STATUS_ACTIVE = "ACTIVE"
STATUS_PAUSED = "PAUSED"
STATUS_FAILED = "FAILED"
STATUS_ARCHIVED = "ARCHIVED"

CANDIDATE_STATUSES = (
    STATUS_DISCOVERED,
    STATUS_RESEARCHING,
    STATUS_CANDIDATE,
    STATUS_BUILDING,
    STATUS_TESTING,
    STATUS_QUALITY_GATE,
    STATUS_QUALITY_GATE_FAILED,
    STATUS_READY,
    STATUS_APPROVAL_REQUIRED,
    STATUS_PUBLISHING,
    STATUS_PUBLISHED,
    STATUS_ACTIVE,
    STATUS_PAUSED,
    STATUS_FAILED,
    STATUS_ARCHIVED,
)

REV_POTENTIAL = "POTENTIAL"
REV_ESTIMATED = "ESTIMATED"
REV_EARNED = "EARNED"
REV_PAYOUT_PENDING = "PAYOUT_PENDING"
REV_PAID_OUT = "PAID_OUT"
REV_REFUNDED = "REFUNDED"
REV_ADJUSTED = "ADJUSTED"

RevenueStatus = Literal[
    "POTENTIAL",
    "ESTIMATED",
    "EARNED",
    "PAYOUT_PENDING",
    "PAID_OUT",
    "REFUNDED",
    "ADJUSTED",
]

JOB_KINDS = (
    "discover",
    "research",
    "score",
    "build",
    "test",
    "quality_gate",
    "prepare_publish",
    "publish",
    "monitor",
    "acquire",
    "first_api",
)


def empty_candidate(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "",
        "name": "",
        "category": "",
        "problem": "",
        "target_user": "",
        "use_case": "",
        "endpoints": [],
        "upstream": "",
        "competition_score": 0.0,
        "demand_score": 0.0,
        "implementation_score": 0.0,
        "monetization_score": 0.0,
        "operating_cost": 0.0,
        "suggested_price": {},
        "expected_margin": 0.0,
        "total_score": 0.0,
        "status": STATUS_DISCOVERED,
        "evidence": [],
        "quality_gate": None,
        "publish_package": None,
        "approval": {"required": True, "approved": False, "approved_at": None, "note": ""},
        "metrics": {
            "requests": 0,
            "successful_requests": 0,
            "errors": 0,
            "latency_ms": None,
            "subscribers": 0,
        },
        "created_at": "",
        "updated_at": "",
        "demo": False,
        "last_error": "",
        "current_job_id": "",
        "rapidapi_api_id": "",
        "acquisition": None,
    }
    base.update(overrides)
    return base


def empty_job(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "",
        "candidate_id": "",
        "kind": "discover",
        "status": "queued",  # queued | running | done | failed
        "attempt": 0,
        "created_at": "",
        "updated_at": "",
        "started_at": None,
        "finished_at": None,
        "result": None,
        "error": "",
        "durable": True,
    }
    base.update(overrides)
    return base


def empty_revenue_event(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "",
        "provider": "rapidapi",
        "external_id": "",
        "api_id": "",
        "gross_amount": 0.0,
        "platform_fee": 0.0,
        "net_amount": 0.0,
        "currency": "USD",
        "status": REV_ESTIMATED,
        "occurred_at": "",
        "settled_at": None,
        "payout_id": "",
        "evidence": {},
        "created_at": "",
        "ledger_uuid": None,
        "demo": False,
    }
    base.update(overrides)
    return base
