"""CounterLiquidityProof — without Proof = NO_REAL_LIQUIDITY."""

from __future__ import annotations

from typing import Any
import uuid


def build_counter_liquidity_proof(opp: dict[str, Any], *, simulation: dict[str, Any] | None = None) -> dict[str, Any]:
    reserve = opp.get("reserve")
    if reserve is None:
        reserve = opp.get("poolReserve")
    depth = opp.get("executable_depth")
    if depth is None:
        depth = opp.get("max_executable")

    source_ok = bool(opp.get("source") or opp.get("sourceType"))
    has_reserve = reserve is not None and float(reserve or 0) > 0
    has_depth = depth is not None and float(depth or 0) > 0

    status = "NO_REAL_LIQUIDITY"
    if source_ok and has_reserve and has_depth and (opp.get("strict_pass") or opp.get("status") in ("ZERO_CAPITAL", "LIQUIDITY_VERIFIED")):
        status = "LIQUIDITY_VERIFIED"
    elif source_ok and not has_reserve:
        status = "NO_REAL_COUNTER_LIQUIDITY"
    elif not source_ok:
        status = "NO_SOURCE"

    return {
        "proofId": f"CLP-{uuid.uuid4().hex[:10]}",
        "protocol": opp.get("protocol"),
        "pool": opp.get("poolAddress"),
        "counterAsset": opp.get("counterAsset"),
        "reserve": reserve if reserve is not None else "UNKNOWN",
        "source": opp.get("source") or opp.get("sourceType"),
        "sourceEvidence": opp.get("evidence") or "",
        "capitalRequired": float(opp.get("capital_required") or 0),
        "gasRequired": float(opp.get("gas_required") or 0),
        "eligibility": opp.get("eligibility"),
        "route": opp.get("route") or "UNKNOWN",
        "quote": opp.get("quote") or "UNKNOWN",
        "simulation": simulation or {"ok": False, "status": "NOT_RUN"},
        "maxExecutable": depth if depth is not None else "UNKNOWN",
        "txHash": None,
        "settlement": None,
        "status": status,
        "implied_vs_executable": {
            "implied": opp.get("implied_price") or "UNKNOWN",
            "executable": depth if depth is not None else "UNKNOWN",
            "note": "IMPLIED ≠ EXECUTABLE",
        },
    }
