"""
VCORE-X01 — External Exchangeability (Asset Identity Engine)

Proves chain (not painted economics):
  identity → compatibility → market → liquidity → swap → external asset → TXID

REAL_EXTERNAL_ASSET = PASS only after X01.10 TXID with confirmed external asset.

Forbidden:
  - VCORE = €1 as market price
  - token created ⇒ liquid ⇒ sellable
  - Virtus UI liquidity without real external counter-asset
  - Virtus-owned exchange as proof (must be external permissionless DEX)

P-01/P-02/P-03 lab frozen — not this track.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "vcore_exchangeability"
_GENESIS = _ROOT / ".runtime" / "vcore_genesis_state.json"
_LAST = _RUNTIME / "x01_last.json"

STON_API = "https://api.ston.fi"
STON_NATIVE_TON = "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c"
TONAPI_TESTNET = "https://testnet.tonapi.io/v2"
TONAPI_MAINNET = "https://tonapi.io/v2"

X01_GOAL = (
    "Can VCORE — without Virtus Core's own exchange — be accepted by an external "
    "permissionless DEX and swapped for a real external asset?"
)

X01_STAGES: tuple[tuple[str, str], ...] = (
    ("X01.1", "CONTRACT"),
    ("X01.2", "TOKEN_STANDARD"),
    ("X01.3", "WALLET_COMPATIBILITY"),
    ("X01.4", "CONTRACT_VERIFICATION"),
    ("X01.5", "EXTERNAL_DEX_DISCOVERY"),
    ("X01.6", "VCORE_X_POOL"),
    ("X01.7", "REAL_EXTERNAL_LIQUIDITY"),
    ("X01.8", "SMALL_TEST_SWAP"),
    ("X01.9", "EXTERNAL_ASSET_RECEIVED"),
    ("X01.10", "TXID"),
)

FORBIDDEN = (
    "VCORE = €1 declared as market price",
    "token deployed ⇒ automatically liquid",
    "UI shows liquidity without external counter-asset reserves",
    "Virtus internal swap counts as external proof",
)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_genesis() -> dict[str, Any]:
    if not _GENESIS.exists():
        return {"stage": "NOT_STARTED", "jettonMaster": None, "symbol": "VCORE", "decimals": 9}
    return json.loads(_GENESIS.read_text(encoding="utf-8"))


def _http_json(url: str, *, method: str = "GET", body: dict | None = None, timeout: float = 15.0) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json", "User-Agent": "VirtusCore-X01/1.0"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": resp.status, "json": json.loads(raw) if raw.strip() else {}}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return {"ok": False, "status": 0, "error": str(e), "json": {}}


def _tonapi_base(network: str) -> str:
    return TONAPI_MAINNET if "mainnet" in network else TONAPI_TESTNET


def _wallet_compatibility(g: dict[str, Any], *, offline: bool) -> dict[str, Any]:
    master = g.get("jettonMaster")
    admin = g.get("adminAddress")
    jw_admin = g.get("jettonWalletAdmin")
    bal_chain = g.get("adminBalanceOnChain")
    probe_bal = g.get("probeBalanceOnChain")

    local_ok = bool(jw_admin) or (
        bal_chain is not None and str(bal_chain) not in ("", "0", "0.0")
    ) or (probe_bal is not None and str(probe_bal) not in ("", "0", "0.0"))

    remote_ok = False
    remote_detail = None
    if not offline and master and admin:
        base = _tonapi_base(str(g.get("network") or "ton-testnet"))
        url = f"{base}/accounts/{urllib.parse.quote(admin)}/jettons/{urllib.parse.quote(master)}"
        r = _http_json(url)
        if r.get("ok") and isinstance(r.get("json"), dict):
            remote_detail = r["json"]
            bal = remote_detail.get("balance") or remote_detail.get("quantity")
            try:
                remote_ok = int(str(bal or 0)) > 0
            except (TypeError, ValueError):
                remote_ok = bool(bal)

    ok = local_ok or remote_ok
    return {
        "pass": ok,
        "admin_address": admin,
        "jetton_wallet_admin": jw_admin,
        "admin_balance_local": bal_chain,
        "probe_balance_local": probe_bal,
        "remote_jetton_balance": remote_detail,
        "note": "Wallet must hold VCORE Jetton — not just master contract exists",
    }


def _ston_discover(jetton_master: str | None) -> dict[str, Any]:
    routers = _http_json(f"{STON_API}/v1/routers")
    search = _http_json(
        f"{STON_API}/v1/assets/query",
        method="POST",
        body={"search_terms": ["VCORE", "Virtus", "VirtusCore"], "limit": 20},
    )
    asset_list = (search.get("json") or {}).get("asset_list") or []
    vcore_hits = [
        a
        for a in asset_list
        if isinstance(a, dict)
        and (str(a.get("symbol", "")).upper() == "VCORE" or "VIRTUS" in str(a.get("symbol", "")).upper())
    ]

    pool_found = False
    pool_detail = None
    liquidity_external = False
    counter_asset = None
    reserve_hint = None

    if jetton_master:
        for pair in ((jetton_master, STON_NATIVE_TON), (STON_NATIVE_TON, jetton_master)):
            pools = _http_json(f"{STON_API}/v1/pools/by_market/{pair[0]}/{pair[1]}")
            plist = (pools.get("json") or {}).get("pool_list") or []
            if plist:
                pool_found = True
                pool_detail = plist[0] if isinstance(plist[0], dict) else {"raw": plist[0]}
                counter_asset = "TON"
                for key in ("reserve0", "reserve1", "token0_balance", "token1_balance", "lp_total_supply"):
                    if isinstance(pool_detail, dict) and pool_detail.get(key):
                        reserve_hint = {key: pool_detail.get(key)}
                        try:
                            if float(pool_detail[key]) > 0:
                                liquidity_external = True
                        except (TypeError, ValueError):
                            pass
                break

    dex_sees_vcore = len(vcore_hits) > 0 or (jetton_master and pool_found)

    return {
        "venue": "STON.fi",
        "external_permissionless": True,
        "virtus_exchange_excluded": True,
        "api_ok": routers.get("ok") or search.get("ok"),
        "dex_sees_vcore": dex_sees_vcore,
        "vcore_hits": vcore_hits,
        "pool_found": pool_found,
        "pool_detail": pool_detail,
        "counter_asset": counter_asset,
        "reserve_hint": reserve_hint,
        "real_external_liquidity": liquidity_external,
        "note": "Pool without counter-asset reserves ≠ real market",
    }


def _step_status(*, pass_: bool, blocked: bool = False, not_yet: bool = False) -> str:
    if pass_:
        return "PASS"
    if blocked:
        return "BLOCKED"
    if not_yet:
        return "NOT_YET"
    return "FAIL"


def run_x01_external_exchangeability(*, offline: bool = False) -> dict[str, Any]:
    g = _load_genesis()
    master = g.get("jettonMaster")
    stage = str(g.get("stage") or "NOT_STARTED")
    symbol = g.get("symbol") or "VCORE"
    decimals = int(g.get("decimals") or 9)
    network = g.get("network") or "ton-testnet"
    ext = g.get("externalVerification") or {}
    value = g.get("valueLayers") or {}

    contract_ok = bool(master) and stage not in ("NOT_STARTED", "GENESIS_DRAFT")
    standard_ok = contract_ok
    wallet = _wallet_compatibility(g, offline=offline)
    wallet_ok = wallet["pass"]
    verified_ok = stage == "VERIFIED"

    ston = {"offline": True} if offline else _ston_discover(master)
    if not offline:
        ston["offline"] = False

    dex_ok = bool(ston.get("dex_sees_vcore")) if not offline else False
    pool_ok = bool(ston.get("pool_found")) if not offline else False
    liq_ok = bool(ston.get("real_external_liquidity")) if not offline else False

    real_settlement = value.get("realSettlement") or {}
    txid = real_settlement.get("tx")
    ext_amount = real_settlement.get("amount")
    external_received = bool(txid) and ext_amount not in (None, "", 0, 0.0) and float(ext_amount or 0) > 0
    txid_ok = bool(txid) and external_received

    # X01.8 — small test swap: only PASS after owner-confirmed swap TX; sim alone = NOT_YET
    swap_ok = txid_ok
    swap_status = _step_status(pass_=swap_ok, not_yet=liq_ok and verified_ok and not swap_ok)

    stages: dict[str, dict[str, Any]] = {}
    for code, name in X01_STAGES:
        key = f"{code}_{name}"
        if name == "CONTRACT":
            st = _step_status(pass_=contract_ok, not_yet=not contract_ok)
            detail = {"jetton_master": master, "stage": stage, "blockers": g.get("blockers") or []}
        elif name == "TOKEN_STANDARD":
            st = _step_status(pass_=standard_ok, not_yet=not contract_ok)
            detail = {"standard": "TEP-74 Jetton", "network": network, "decimals": decimals, "symbol": symbol}
        elif name == "WALLET_COMPATIBILITY":
            st = _step_status(pass_=wallet_ok, not_yet=contract_ok and not wallet_ok)
            detail = wallet
        elif name == "CONTRACT_VERIFICATION":
            st = _step_status(pass_=verified_ok, not_yet=contract_ok and not verified_ok)
            detail = {"stage": stage, "external_verification": ext}
        elif name == "EXTERNAL_DEX_DISCOVERY":
            st = _step_status(pass_=dex_ok, not_yet=contract_ok and verified_ok and not dex_ok, blocked=not contract_ok)
            detail = {k: ston.get(k) for k in ("venue", "dex_sees_vcore", "vcore_hits", "external_permissionless")}
        elif name == "VCORE_X_POOL":
            st = _step_status(pass_=pool_ok, not_yet=dex_ok and not pool_ok)
            detail = {"pool_found": ston.get("pool_found"), "counter_asset": ston.get("counter_asset"), "pairs": ["VCORE/TON", "VCORE/USDT", "VCORE/USDC"]}
        elif name == "REAL_EXTERNAL_LIQUIDITY":
            st = _step_status(pass_=liq_ok, not_yet=pool_ok and not liq_ok)
            detail = {
                "real_external_liquidity": ston.get("real_external_liquidity"),
                "reserve_hint": ston.get("reserve_hint"),
                "forbidden": "Virtus-painted liquidity without external counter-asset",
                "declared_usd_not_market": value.get("declared"),
                "market_usd_must_be_discovered": value.get("market"),
            }
        elif name == "SMALL_TEST_SWAP":
            st = swap_status
            detail = {"mode": "owner_gated_small_swap", "simulation_only_until_txid": True, "virtus_exchange_counts": False}
        elif name == "EXTERNAL_ASSET_RECEIVED":
            st = _step_status(pass_=external_received, not_yet=not external_received)
            detail = {"real_settlement": real_settlement, "must_be_external_not_virtus_only": True}
        elif name == "TXID":
            st = _step_status(pass_=txid_ok, not_yet=not txid_ok)
            detail = {"txid": txid}
        else:
            st = "FAIL"
            detail = {}
        stages[key] = {"code": code, "name": name, "status": st, **detail}

    passed = sum(1 for s in stages.values() if s["status"] == "PASS")
    not_yet = sum(1 for s in stages.values() if s["status"] == "NOT_YET")

    if txid_ok:
        outcome = "X01_COMPLETE_REAL_EXTERNAL_ASSET"
        readiness = "MARKET_PROVEN_ON_CHAIN"
        real_external = "PASS"
    elif liq_ok and verified_ok:
        outcome = "X01_READY_FOR_SMALL_TEST_SWAP"
        readiness = "TECHNICALLY_READY_ECONOMIC_MARKET_EXISTS"
        real_external = "NOT_YET"
    elif pool_ok:
        outcome = "X01_POOL_EXISTS_CHECK_LIQUIDITY"
        readiness = "POOL_WITHOUT_PROVEN_EXTERNAL_RESERVES"
        real_external = "NOT_YET"
    elif contract_ok:
        outcome = "X01_TOKEN_READY_MARKET_NOT_CREATED"
        readiness = "TECHNICALLY_READY_ECONOMIC_MARKET_NOT_CREATED"
        real_external = "NOT_YET"
    else:
        outcome = "X01_GENESIS_FIRST"
        readiness = "IDENTITY_INCOMPLETE"
        real_external = "NOT_YET"

    report = {
        "experiment_id": "VCORE-X01",
        "title": "External Exchangeability",
        "engine": "Asset Identity / Exchangeability Engine",
        "version": "1.1.0",
        "at": _now(),
        "goal": X01_GOAL,
        "proof_chain": [
            "VCORE",
            "real token contract",
            "network standard",
            "verified contract",
            "wallet holds VCORE",
            "DEX sees VCORE",
            "VCORE/X market",
            "real external liquidity X",
            "user SWAP",
            "receive X",
            "TXID",
        ],
        "forbidden": list(FORBIDDEN),
        "stages": stages,
        "summary": {
            "pass_count": passed,
            "not_yet_count": not_yet,
            "readiness": readiness,
            "experiment_outcome": outcome,
            "REAL_EXTERNAL_ASSET": real_external,
        },
        "economic_truth": {
            "declared_reference_usd": (value.get("declared") or {}).get("amount"),
            "model_usd": (value.get("model") or {}).get("amount"),
            "market_usd_discovered": (value.get("market") or {}).get("amount", 0),
            "executable_ton": (value.get("executable") or {}).get("amount", 0),
            "law": "Price discovered by market; liquidity must exist as external counter-asset",
        },
        "ston_discovery": ston if not offline else {"offline": True},
        "genesis_touch": False,
        "genesis_auto_modify": False,
        "lab_frozen": {"P-01": "CONTROL", "P-02": "archived", "P-03": "FROZEN"},
        "next": (
            "Genesis PASS → external permissionless pool → independent LP (real TON/USDT) → "
            "small owner swap on STON (not Virtus UI) → TXID → REAL_EXTERNAL_ASSET=PASS"
        ),
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _LAST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (_RUNTIME / "last_assessment.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def assess_exchangeability(*, offline: bool = False) -> dict[str, Any]:
    """Backward-compatible alias → VCORE-X01."""
    return run_x01_external_exchangeability(offline=offline)
