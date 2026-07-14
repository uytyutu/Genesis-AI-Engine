"""Digital Dust — legal recoverable-asset discovery from PUBLIC data only.

SECURITY LAW (binding):
- ONLY public contract references and explorer-visible signals
- NEVER private keys, mnemonics, seeds, or third-party wallet access
- ONLY assets claimable via public withdraw/claim functions — CEO executes manually
- Record as Potential Recoverable Assets — no auto wallet transactions
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.integration.public_intel_miner import PatternHit

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_ETH_ADDRESS = re.compile(r"0x[a-fA-F0-9]{40}")
_FORBIDDEN = re.compile(
    r"(private[\s_-]?key|mnemonic|seed[\s_-]?phrase|secret[\s_-]?key|"
    r"wallet[\s_-]?backup|password|credential)",
    re.I,
)
_PUBLIC_CLAIM_SIGNALS = re.compile(
    r"(withdraw\s*\(|claim\s*\(|recover\s*\(|emergencyWithdraw|"
    r"orphan\s+(?:pool|token)|abandoned\s+liquidity|paused\s+pool|"
    r"unclaimed\s+rewards|stuck\s+liquidity)",
    re.I,
)
_PUBLIC_ABI_CLAIM = re.compile(
    r"function\s+(withdraw|claim|recover|emergencyWithdraw|getReward)\s*\(",
    re.I,
)


@dataclass
class RecoverableAsset:
    asset_id: str
    contract_address: str
    network: str
    signal: str
    claim_type: str
    valuation_eur: float
    source_url: str
    context_snippet: str
    legal_status: str
    ceo_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DigitalDustService:
    """Find orphan/stuck tokens in PUBLIC registries — never touch private wallets."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _ledger_path(self) -> Path:
        return self._memory / "harvest_ledger.jsonl"

    def is_safe_public_reference(self, text: str, *, value: str = "") -> bool:
        blob = f"{text} {value}".strip()
        if not blob:
            return False
        if _FORBIDDEN.search(blob):
            return False
        if re.match(r"^[a-fA-F0-9]{64}$", value.strip()):
            return False
        return True

    def extract_contract_addresses(self, text: str) -> list[str]:
        if not text or _FORBIDDEN.search(text):
            return []
        seen: set[str] = set()
        out: list[str] = []
        for m in _ETH_ADDRESS.finditer(text):
            addr = m.group(0)
            key = addr.lower()
            if key not in seen and self.is_safe_public_reference(text, value=addr):
                seen.add(key)
                out.append(addr)
        return out

    def detect_claim_signals(self, text: str) -> list[str]:
        if not text or _FORBIDDEN.search(text):
            return []
        return [m.group(0)[:80] for m in _PUBLIC_CLAIM_SIGNALS.finditer(text)]

    def _infer_network(self, text: str) -> str:
        lower = text.lower()
        if "polygon" in lower or "matic" in lower:
            return "polygon"
        if "arbitrum" in lower:
            return "arbitrum"
        if "bsc" in lower or "binance" in lower:
            return "bsc"
        return "ethereum"

    def _verify_public_abi_claim(self, address: str, network: str) -> str | None:
        """Optional: Etherscan public ABI — read-only claim function check."""
        api_key = os.getenv("ETHERSCAN_API_KEY", "").strip()
        if not api_key:
            return None
        base = {
            "ethereum": "https://api.etherscan.io/api",
            "polygon": "https://api.polygonscan.com/api",
            "arbitrum": "https://api.arbiscan.io/api",
            "bsc": "https://api.bscscan.com/api",
        }.get(network, "https://api.etherscan.io/api")
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    base,
                    params={
                        "module": "contract",
                        "action": "getabi",
                        "address": address,
                        "apikey": api_key,
                    },
                )
            if not res.is_success:
                return None
            body = res.json()
            abi_raw = body.get("result") if isinstance(body, dict) else None
            if not isinstance(abi_raw, str) or abi_raw.startswith("Max rate"):
                return None
            if _PUBLIC_ABI_CLAIM.search(abi_raw):
                m = _PUBLIC_ABI_CLAIM.search(abi_raw)
                return (m.group(1) if m else "claim") + "()"
        except httpx.HTTPError:
            return None
        return None

    def build_recoverable_from_hits(
        self,
        row: dict[str, Any],
        hits: list[PatternHit],
    ) -> list[RecoverableAsset]:
        dust_hits = [h for h in hits if h.lane == "digital_dust"]
        if not dust_hits:
            return []

        analysis = row.get("site_analysis") if isinstance(row.get("site_analysis"), dict) else {}
        corpus = json.dumps(
            {
                "fit_reason": row.get("fit_reason"),
                "site_analysis": analysis,
                "notes": row.get("notes"),
                "hits": [h.matched_value for h in dust_hits],
            },
            ensure_ascii=False,
        )

        addresses = self.extract_contract_addresses(corpus)
        claims = self.detect_claim_signals(corpus)
        if not addresses and not claims:
            return []

        source_url = str(row.get("website_url") or "")
        network = self._infer_network(corpus)
        assets: list[RecoverableAsset] = []

        for addr in addresses[:5]:
            abi_claim = self._verify_public_abi_claim(addr, network)
            signal = claims[0] if claims else (abi_claim or "public_contract_reference")
            claim_type = abi_claim or ("withdraw/claim" if claims else "manual_review")
            if not claims and not abi_claim:
                continue
            assets.append(
                RecoverableAsset(
                    asset_id=f"dust-{addr[-8:].lower()}",
                    contract_address=addr,
                    network=network,
                    signal=signal,
                    claim_type=claim_type,
                    valuation_eur=round(sum(h.valuation_eur for h in dust_hits) / max(1, len(addresses)), 2),
                    source_url=source_url,
                    context_snippet=(corpus[:120] + "…") if len(corpus) > 120 else corpus,
                    legal_status="potential_recoverable_public_only",
                    ceo_action="CEO verifies ownership/eligibility → manual claim() — never third-party wallets",
                )
            )

        if not assets and claims:
            assets.append(
                RecoverableAsset(
                    asset_id=f"dust-signal-{row.get('id', 'x')[:8]}",
                    contract_address="",
                    network=network,
                    signal=claims[0],
                    claim_type="withdraw/claim",
                    valuation_eur=round(sum(h.valuation_eur for h in dust_hits), 2),
                    source_url=source_url,
                    context_snippet=claims[0][:120],
                    legal_status="signal_only_needs_contract_address",
                    ceo_action="Find public contract on explorer → verify public claim — CEO only",
                )
            )
        return assets

    def append_harvest_ledger(self, assets: list[RecoverableAsset], *, opportunity_id: str) -> int:
        if not assets:
            return 0
        path = self._ledger_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with path.open("a", encoding="utf-8") as f:
            for asset in assets:
                entry = {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "type": "potential_recoverable_asset",
                    "opportunity_id": opportunity_id,
                    **asset.to_dict(),
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                written += 1
        return written

    def process_opportunity(
        self,
        row: dict[str, Any],
        hits: list[PatternHit],
        *,
        opportunity_update: Any,
    ) -> dict[str, Any]:
        assets = self.build_recoverable_from_hits(row, hits)
        meta = dict(row.get("meta") or {})
        meta["digital_dust_scanned_at"] = datetime.now(timezone.utc).isoformat()
        if assets:
            meta["recoverable_assets"] = [a.to_dict() for a in assets]
            meta["recoverable_assets_count"] = len(assets)
            meta["digital_dust_value_eur"] = round(sum(a.valuation_eur for a in assets), 2)
            meta["execution_status"] = meta.get("execution_status") or "pending_ceo_approval"
            meta["ceo_action"] = "Verify public claim eligibility — manual only"
            self.append_harvest_ledger(assets, opportunity_id=row["id"])
        else:
            meta["recoverable_assets_count"] = 0
        return opportunity_update(row["id"], {"meta": meta})

    def dashboard(self) -> dict[str, Any]:
        path = self._ledger_path()
        count = 0
        value = 0.0
        networks: dict[str, int] = {}
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "potential_recoverable_asset":
                    continue
                count += 1
                value += float(entry.get("valuation_eur") or 0)
                net = str(entry.get("network") or "ethereum")
                networks[net] = networks.get(net, 0) + 1
        return {
            "mode": "digital_dust",
            "legal_boundary": "PUBLIC contracts only · NO private keys · NO third-party wallets",
            "recoverable_assets_count": count,
            "recoverable_value_eur": round(value, 2),
            "networks": networks,
            "etherscan_configured": bool(os.getenv("ETHERSCAN_API_KEY", "").strip()),
            "note": "Potential Recoverable Assets → harvest_ledger.jsonl · CEO manual claim only.",
        }

    @staticmethod
    def logic_chain() -> list[dict[str, str]]:
        return [
            {
                "step": "1",
                "name": "Public Scan",
                "detail": "Сайт / публичный реестр → только HTTP(S) и explorer-данные",
            },
            {
                "step": "2",
                "name": "PublicIntelMiner",
                "detail": "RegEx: 0x-контракты + сигналы withdraw/claim/orphan pool",
            },
            {
                "step": "3",
                "name": "Security Gate",
                "detail": "Блок: private key · mnemonic · seed · credentials — уничтожить match",
            },
            {
                "step": "4",
                "name": "Digital Dust Validator",
                "detail": "Только публичные claim-функции (ABI Etherscan если ключ есть)",
            },
            {
                "step": "5",
                "name": "Smart-Gate",
                "detail": "Никогда авто-кошелёк · риск > порога → pending_ceo_approval",
            },
            {
                "step": "6",
                "name": "Harvest Ledger",
                "detail": "potential_recoverable_asset → CEO вручную claim()",
            },
        ]
