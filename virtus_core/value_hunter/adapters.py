"""Discovery adapters — independent, timeout-safe, no global crash."""

from __future__ import annotations

import time
from typing import Any, Callable


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


AdapterFn = Callable[[], list[dict[str, Any]]]


def _safe_run(name: str, fn: AdapterFn, timeout_note: str = "") -> dict[str, Any]:
    t0 = time.time()
    try:
        items = fn()
        return {
            "adapter": name,
            "ok": True,
            "count": len(items),
            "items": items,
            "ms": int((time.time() - t0) * 1000),
            "error": None,
        }
    except Exception as e:
        return {
            "adapter": name,
            "ok": False,
            "count": 0,
            "items": [],
            "ms": int((time.time() - t0) * 1000),
            "error": str(e),
            "status": "SKIPPED",
            "note": timeout_note or "adapter_error",
        }


def bounty_adapter() -> list[dict[str, Any]]:
    return [
        {
            "id": "bounty_immunefi",
            "title": "Immunefi — публичные bug bounty",
            "kind": "BUG_BOUNTY",
            "asset": "USDT/USDC/ETH",
            "protocol": "Immunefi",
            "eligibility": "Валидный in-scope отчёт",
            "required_action": "Исследование + PoC + отчёт",
            "reward_rule": "По таблице программы",
            "withdrawal_path": "Выплата программы → кошелёк владельца",
            "capital_required_eur": 0.0,
            "gas_required_eur": 0.0,
            "gas_sponsored": True,
            "fees_required_eur": 0.0,
            "registration_required": True,
            "account_required": True,
            "kyc_required": False,
            "source_of_funds_type": "BUG_BOUNTY",
            "source_of_funds_description": "Пул вознаграждений программы",
            "source_of_funds_evidence": "https://immunefi.com/explore/",
            "url": "https://immunefi.com/explore/",
            "automatable": "partial",
            "risk": "Высокая конкуренция",
            "probability": None,
            "expected_gross": None,
            "status": "DISCOVERED",
        }
    ]


def faucet_adapter() -> list[dict[str, Any]]:
    return [
        {
            "id": "faucet_ton_testnet",
            "title": "TON testnet faucet",
            "kind": "TESTNET_REWARD",
            "asset": "testnet TON",
            "protocol": "TON Testnet",
            "eligibility": "Адрес testnet-кошелька",
            "required_action": "Запрос у крана",
            "reward_rule": "Лимит крана",
            "withdrawal_path": "Наш testnet wallet",
            "capital_required_eur": 0.0,
            "gas_required_eur": 0.0,
            "gas_sponsored": True,
            "fees_required_eur": 0.0,
            "registration_required": False,
            "account_required": False,
            "kyc_required": False,
            "source_of_funds_type": "TESTNET_REWARD",
            "source_of_funds_description": "Эмиссия testnet faucet",
            "source_of_funds_evidence": "https://t.me/testgiver_ton_bot",
            "url": "https://t.me/testgiver_ton_bot",
            "automatable": "high",
            "risk": "Не mainnet REAL",
            "probability": 0.9,
            "expected_gross": 0.0,
            "status": "DISCOVERED",
            "notes": "Для Genesis Gate. Не писать в Reality Ledger как REAL mainnet.",
        }
    ]


def incentive_adapter() -> list[dict[str, Any]]:
    return [
        {
            "id": "incentive_lp_mining",
            "title": "DEX liquidity mining",
            "kind": "LIQUIDITY_INCENTIVE",
            "asset": "TON/USDT LP rewards",
            "protocol": "DeDust/STON style LP",
            "eligibility": "Внести оба актива пула",
            "required_action": "Provide liquidity",
            "reward_rule": "Инцентивы кампании",
            "withdrawal_path": "Claim → wallet",
            "capital_required_eur": 50.0,
            "gas_required_eur": 1.0,
            "gas_sponsored": False,
            "fees_required_eur": 0.5,
            "registration_required": True,
            "account_required": True,
            "kyc_required": False,
            "source_of_funds_type": "INCENTIVE",
            "source_of_funds_description": "Эмиссия/бюджет протокола",
            "source_of_funds_evidence": "https://help.dedust.io/en/liquidity/pools",
            "url": "https://help.dedust.io/en/liquidity/pools",
            "automatable": "high",
            "risk": "IL + капитал",
            "probability": None,
            "expected_gross": None,
            "status": "DISCOVERED",
        }
    ]


def claim_adapter() -> list[dict[str, Any]]:
    return [
        {
            "id": "claim_research",
            "title": "Официальные permissionless claims",
            "kind": "CLAIM",
            "asset": "varies",
            "protocol": "UNKNOWN_UNTIL_VERIFIED",
            "eligibility": "UNKNOWN",
            "required_action": "Claim при eligibility",
            "reward_rule": "UNKNOWN",
            "withdrawal_path": "UNKNOWN",
            "capital_required_eur": 0.0,
            "gas_required_eur": 1.0,
            "gas_sponsored": False,
            "fees_required_eur": 0.0,
            "registration_required": False,
            "account_required": False,
            "kyc_required": False,
            "source_of_funds_type": "CLAIM",
            "source_of_funds_description": "Требует живой официальной кампании",
            "source_of_funds_evidence": "",
            "url": "",
            "automatable": "partial",
            "risk": "Скам-клоны",
            "probability": None,
            "expected_gross": None,
            "status": "DISCOVERED",
        }
    ]


def sponsored_adapter() -> list[dict[str, Any]]:
    return [
        {
            "id": "sponsored_gas_research",
            "title": "Sponsored / gasless execution (исследование)",
            "kind": "SPONSORED_EXECUTION",
            "asset": "protocol-specific",
            "protocol": "RESEARCH",
            "eligibility": "Живая sponsored-кампания",
            "required_action": "Вызов через sponsor",
            "reward_rule": "UNKNOWN",
            "withdrawal_path": "UNKNOWN",
            "capital_required_eur": 0.0,
            "gas_required_eur": 0.0,
            "gas_sponsored": True,
            "fees_required_eur": 0.0,
            "registration_required": False,
            "account_required": False,
            "kyc_required": False,
            "source_of_funds_type": "SPONSORED_EXECUTION",
            "source_of_funds_description": "Спонсор газа/операции",
            "source_of_funds_evidence": "UNKNOWN",
            "url": "",
            "automatable": "high",
            "risk": "Нужна официальная документация",
            "probability": None,
            "expected_gross": None,
            "status": "DISCOVERED",
        }
    ]


def exit_converter_adapter() -> list[dict[str, Any]]:
    return [
        {
            "id": "exit_thorchain",
            "title": "THORChain — только EXIT-конвертер",
            "kind": "EXIT_CONVERTER",
            "asset": "BTC",
            "protocol": "THORChain",
            "eligibility": "Держать supported inbound asset",
            "required_action": "Swap через поддерживаемый pool",
            "reward_rule": "n/a — конвертация, не награда",
            "withdrawal_path": "BTC address владельца",
            "capital_required_eur": 0.0,
            "gas_required_eur": 1.0,
            "gas_sponsored": False,
            "fees_required_eur": 0.0,
            "registration_required": False,
            "account_required": False,
            "kyc_required": False,
            "source_of_funds_type": "OTHER_DOCUMENTED_SOURCE",
            "source_of_funds_description": "Не источник — конвертер существующего актива",
            "source_of_funds_evidence": "https://dev.thorchain.org/swap-guide/quickstart-guide.html",
            "url": "https://dev.thorchain.org/swap-guide/quickstart-guide.html",
            "automatable": "high",
            "risk": "VCORE не supported напрямую",
            "probability": None,
            "expected_gross": None,
            "status": "EXIT_ONLY",
            "forbidden": False,
        }
    ]


def security_reject_adapter() -> list[dict[str, Any]]:
    return [
        {
            "id": "reject_foreign_sweep",
            "title": "Сбор чужих кошельков / dormant sweep",
            "kind": "FORBIDDEN",
            "asset": "any",
            "protocol": "n/a",
            "eligibility": "—",
            "required_action": "—",
            "reward_rule": "—",
            "withdrawal_path": "—",
            "capital_required_eur": 0.0,
            "gas_required_eur": 0.0,
            "gas_sponsored": True,
            "fees_required_eur": 0.0,
            "registration_required": False,
            "account_required": False,
            "kyc_required": False,
            "source_of_funds_type": "",
            "source_of_funds_description": "",
            "source_of_funds_evidence": "",
            "url": "",
            "automatable": "none",
            "risk": "Запрещено",
            "requires_foreign_wallet": True,
            "forbidden": True,
            "probability": None,
            "expected_gross": None,
            "status": "DISCOVERED",
        }
    ]


ALL_ADAPTERS: list[tuple[str, AdapterFn]] = [
    ("bounty", bounty_adapter),
    ("faucet", faucet_adapter),
    ("incentive", incentive_adapter),
    ("claim", claim_adapter),
    ("sponsored", sponsored_adapter),
    ("exit", exit_converter_adapter),
    ("security_reject_sample", security_reject_adapter),
]


def run_all_adapters() -> dict[str, Any]:
    results = []
    items: list[dict[str, Any]] = []
    for name, fn in ALL_ADAPTERS:
        r = _safe_run(name, fn)
        results.append({k: v for k, v in r.items() if k != "items"})
        items.extend(r.get("items") or [])
    return {"at": _now(), "adapters": results, "raw_items": items}
