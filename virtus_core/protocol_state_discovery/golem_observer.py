"""
Golem P-03 field observer — Phase A (observational) / Phase B (settlement).

Rules (binding):
  - NO artificial job
  - NO token purchase / stake
  - NO painted economics
  - Wait for legitimate market match only

Yagna REST default: http://127.0.0.1:7465
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "experiments"
_JOURNAL = _RUNTIME / "p03_observation_journal.jsonl"

DEFAULT_YAGNA_URL = os.environ.get("YA_API_URL", "http://127.0.0.1:7465")
GLM_POLYGON = "0x0B220b82F3eA3B7F6d9A1D8ab58930C064A2b5Bf"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_journal(row: dict[str, Any]) -> None:
    _RUNTIME.mkdir(parents=True, exist_ok=True)
    with _JOURNAL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _which(name: str) -> str | None:
    return shutil.which(name)


def _http_get_json(url: str, *, timeout: float = 3.0) -> dict[str, Any] | list[Any] | None:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def check_prerequisites() -> dict[str, Any]:
    """Detect Yagna/Golem provider tooling without installing anything."""
    yagna = _which("yagna")
    golemsp = _which("golemsp")
    wsl = _which("wsl")

    return {
        "yagna_path": yagna,
        "golemsp_path": golemsp,
        "wsl_available": bool(wsl),
        "platform_note": (
            "Golem provider officially targets Linux. On Windows use WSL2 + provider container/docs."
        ),
        "ready_to_observe": bool(yagna or golemsp),
        "owner_wallet_env": os.environ.get("YA_ACCOUNT") or os.environ.get("ya_provider_account"),
    }


def probe_yagna_api(base_url: str = DEFAULT_YAGNA_URL) -> dict[str, Any]:
    """Read-only probe of local Yagna if daemon is running."""
    out: dict[str, Any] = {
        "base_url": base_url,
        "reachable": False,
        "identity": None,
        "payment_status_polygon": None,
        "activities_sample": None,
        "error": None,
    }
    version = _http_get_json(f"{base_url.rstrip('/')}/version")
    if version is None:
        out["error"] = "yagna_api_unreachable"
        return out
    out["reachable"] = True
    out["version"] = version

    me = _http_get_json(f"{base_url.rstrip('/')}/me")
    out["identity"] = me

    pay = _http_get_json(
        f"{base_url.rstrip('/')}/payment/status?network=polygon&driver=erc20"
    )
    out["payment_status_polygon"] = pay

    activities = _http_get_json(f"{base_url.rstrip('/')}/activity?limit=5")
    out["activities_sample"] = activities

    return out


def extract_settlement_hints(yagna_probe: dict[str, Any]) -> dict[str, Any]:
    """
    Best-effort parse for Phase B hints. Does NOT claim REAL without TXID.
    """
    hints: dict[str, Any] = {
        "job_id": None,
        "earned_glm": None,
        "billing_evidence": None,
        "polygon_txid": None,
        "settlement_observed": False,
    }
    activities = yagna_probe.get("activities_sample")
    if isinstance(activities, list) and activities:
        first = activities[0]
        if isinstance(first, dict):
            hints["job_id"] = first.get("id") or first.get("activity_id")
            hints["billing_evidence"] = {
                "state": first.get("state"),
                "usage": first.get("usage"),
                "agreement_id": first.get("agreement_id"),
            }

    pay = yagna_probe.get("payment_status_polygon")
    if isinstance(pay, dict):
        # Yagna payment status shape varies; capture raw for journal
        hints["billing_evidence"] = hints["billing_evidence"] or pay
        total = pay.get("total_amount") or pay.get("amount") or pay.get("balance")
        if total not in (None, "", "0", 0):
            try:
                if float(total) > 0:
                    hints["earned_glm"] = total
            except (TypeError, ValueError):
                pass

    hints["settlement_observed"] = bool(hints["polygon_txid"])
    return hints


def run_phase_a_observation(*, base_url: str = DEFAULT_YAGNA_URL) -> dict[str, Any]:
    """
    Phase A — observational snapshot. No artificial job. No broadcast.
    """
    prereq = check_prerequisites()
    row = {
        "phase": "A",
        "at": _now(),
        "prerequisites": prereq,
        "yagna_probe": None,
        "settlement_hints": None,
        "phase_a_status": "UNKNOWN",
        "message": "",
    }

    if not prereq["ready_to_observe"]:
        row["phase_a_status"] = "PREREQUISITES_MISSING"
        row["message"] = (
            "yagna/golemsp не найдены в PATH. P-03 Phase A не может наблюдать без provider daemon. "
            "Установите Golem provider (Linux/WSL) — docs.golem.network/providers — затем повторите."
        )
        _append_journal(row)
        return row

    probe = probe_yagna_api(base_url)
    row["yagna_probe"] = probe

    if not probe.get("reachable"):
        row["phase_a_status"] = "WAITING_PROVIDER_START"
        row["message"] = (
            "Инструменты найдены, но Yagna API недоступен. Запустите provider (golemsp run) "
            "с YA_PAYMENT_NETWORK_GROUP=mainnet и owner wallet — затем повторите observation."
        )
        _append_journal(row)
        return row

    hints = extract_settlement_hints(probe)
    row["settlement_hints"] = hints

    if hints.get("job_id"):
        row["phase_a_status"] = "JOB_ACTIVITY_SEEN"
        row["message"] = (
            f"Activity detected id={hints['job_id']}. Phase B: verify billing + Polygon TXID before CANDIDATE_REAL."
        )
    else:
        row["phase_a_status"] = "OBSERVING_NO_MATCH_YET"
        row["message"] = (
            "Provider API reachable — legitimate match not observed in this snapshot. "
            "NOT a theory failure — possible market-demand blocker (taxonomy #3)."
        )

    _append_journal(row)
    return row


def run_phase_b_settlement(*, phase_a: dict[str, Any]) -> dict[str, Any]:
    """
    Phase B — only if settlement evidence exists. Never paint REAL without TXID.
    """
    hints = (phase_a or {}).get("settlement_hints") or {}
    txid = hints.get("polygon_txid")
    amount = hints.get("earned_glm")
    job_id = hints.get("job_id")

    if txid and amount and job_id:
        status = "SETTLEMENT_TX_OBSERVED"
        brick = "CANDIDATE_REAL_BRICK"
        real = "REAL_EXTERNAL_ASSET_PENDING_OWNER_VERIFY"
    elif job_id and amount:
        status = "BILLING_WITHOUT_TXID"
        brick = "INCOMPLETE_ECONOMIC_BRICK"
        real = "NOT_CLAIMED"
    elif job_id:
        status = "JOB_WITHOUT_BILLING"
        brick = "INCOMPLETE_ECONOMIC_BRICK"
        real = "NOT_CLAIMED"
    else:
        status = "NO_JOB_NO_SETTLEMENT"
        brick = "INCOMPLETE_ECONOMIC_BRICK"
        real = "NOT_CLAIMED"

    row = {
        "phase": "B",
        "at": _now(),
        "phase_b_status": status,
        "job_id": job_id,
        "earned_glm": amount,
        "polygon_txid": txid,
        "glm_polygon_contract": GLM_POLYGON,
        "economic_brick_state": brick,
        "real_external_asset": real,
        "message": (
            "REAL_EXTERNAL_ASSET only after owner-verified Polygon TXID + balance delta — not inferred from API alone."
        ),
    }
    _append_journal(row)
    return row
