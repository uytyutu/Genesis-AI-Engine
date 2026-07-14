"""Public Intel Miner — RegEx pattern mining on public scan data only.

SECURITY LAW: public fields only. Never match or store private keys, seeds, passwords.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_FORBIDDEN_NEAR_MATCH = re.compile(
    r"(private[\s_-]?key|mnemonic|seed[\s_-]?phrase|secret[\s_-]?key|"
    r"api[\s_-]?key|password|credential|wallet[\s_-]?backup)",
    re.I,
)

# Reject full-line matches that look like secrets (64-char hex could be pubkey OR leaked key material)
_SUSPICIOUS_HEX = re.compile(r"^[a-fA-F0-9]{64}$")


@dataclass
class PatternRule:
    id: str
    label: str
    regex: str
    search_in: list[str] = field(default_factory=lambda: ["site_analysis", "website_url"])
    data_product_value_eur: float = 0.0
    lane: str = "data_product"
    min_confidence: float = 0.6
    _compiled: re.Pattern[str] | None = field(default=None, repr=False)

    def compiled(self) -> re.Pattern[str]:
        if self._compiled is None:
            self._compiled = re.compile(self.regex, re.I)
        return self._compiled


@dataclass
class PatternHit:
    pattern_id: str
    pattern_label: str
    matched_value: str
    source_url: str
    context_snippet: str
    confidence: float
    valuation_eur: float
    lane: str


_DEFAULT_PATTERN_CONFIG: dict[str, Any] = {
    "pattern_rules": [
        {
            "id": "eth_contract_public",
            "label": "Публичный ETH-контракт",
            "regex": r"0x[a-fA-F0-9]{40}",
            "search_in": ["site_analysis", "website_url", "fit_reason", "notes"],
            "data_product_value_eur": 2.5,
            "lane": "data_product",
            "min_confidence": 0.6,
        },
        {
            "id": "nft_collection_opensea",
            "label": "OpenSea NFT-коллекция",
            "regex": r"opensea\.io/collection/[a-zA-Z0-9_-]+",
            "search_in": ["site_analysis", "website_url", "fit_reason"],
            "data_product_value_eur": 5.0,
            "lane": "arbitrage_alert",
            "min_confidence": 0.7,
        },
        {
            "id": "nft_collection_blur",
            "label": "Blur NFT-коллекция",
            "regex": r"blur\.io/collection/[a-zA-Z0-9_-]+",
            "search_in": ["site_analysis", "website_url"],
            "data_product_value_eur": 4.0,
            "lane": "arbitrage_alert",
            "min_confidence": 0.7,
        },
    ],
    "garbage_filter": {
        "drop_if_no_valuation": False,
        "drop_if_duplicate_hash": True,
        "max_hits_per_asset": 10,
        "ttl_days": 90,
    },
    "execution_policy": {
        "auto_buy": False,
        "require_ceo_approval": True,
        "note": "Любая покупка — pending_ceo_approval. Только публичные паттерны.",
    },
}


class PublicIntelMiner:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _config_path(self) -> Path:
        return self._memory / "engine_pattern_config.json"

    def load_pattern_config(self) -> dict[str, Any]:
        path = self._config_path()
        if not path.is_file():
            seed = _DEFAULT_MEMORY / "engine_pattern_config.json"
            if seed.is_file():
                try:
                    return json.loads(seed.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(_DEFAULT_PATTERN_CONFIG, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return dict(_DEFAULT_PATTERN_CONFIG)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT_PATTERN_CONFIG)

    def _rules(self) -> list[PatternRule]:
        cfg = self.load_pattern_config()
        rules: list[PatternRule] = []
        for raw in cfg.get("pattern_rules") or []:
            if not raw.get("id") or not raw.get("regex"):
                continue
            try:
                rules.append(
                    PatternRule(
                        id=str(raw["id"]),
                        label=str(raw.get("label") or raw["id"]),
                        regex=str(raw["regex"]),
                        search_in=list(raw.get("search_in") or ["site_analysis", "website_url"]),
                        data_product_value_eur=float(raw.get("data_product_value_eur") or 0),
                        lane=str(raw.get("lane") or "data_product"),
                        min_confidence=float(raw.get("min_confidence") or 0.6),
                    )
                )
            except (TypeError, ValueError, re.error):
                continue
        return rules

    def _corpus(self, opportunity: dict[str, Any], fields: list[str]) -> str:
        chunks: list[str] = []
        for key in fields:
            if key == "site_analysis":
                analysis = opportunity.get("site_analysis")
                if isinstance(analysis, dict):
                    chunks.append(json.dumps(analysis, ensure_ascii=False))
                continue
            val = opportunity.get(key)
            if isinstance(val, str) and val.strip():
                chunks.append(val)
            elif isinstance(val, (int, float)):
                chunks.append(str(val))
        return "\n".join(chunks)

    def _snippet(self, text: str, start: int, end: int, radius: int = 40) -> str:
        lo = max(0, start - radius)
        hi = min(len(text), end + radius)
        snippet = text[lo:hi].replace("\n", " ")
        if lo > 0:
            snippet = "…" + snippet
        if hi < len(text):
            snippet = snippet + "…"
        return snippet[:120]

    def _is_safe_match(self, text: str, match: re.Match[str]) -> bool:
        value = match.group(0).strip()
        if not value or len(value) < 6:
            return False
        if _SUSPICIOUS_HEX.match(value):
            return False
        window = text[max(0, match.start() - 80) : min(len(text), match.end() + 80)]
        if _FORBIDDEN_NEAR_MATCH.search(window):
            return False
        lowered = value.lower()
        if any(x in lowered for x in ("private", "secret", "password", "mnemonic", "seed")):
            return False
        return True

    def mine_patterns_from_scan(
        self,
        opportunity: dict[str, Any],
        *,
        patterns: list[PatternRule] | None = None,
    ) -> list[PatternHit]:
        """Extract public pattern hits from scanner opportunity record."""
        rules = patterns if patterns is not None else self._rules()
        if not rules:
            return []

        cfg = self.load_pattern_config()
        garbage = cfg.get("garbage_filter") if isinstance(cfg.get("garbage_filter"), dict) else {}
        max_hits = int(garbage.get("max_hits_per_asset") or 10)
        drop_dupes = bool(garbage.get("drop_if_duplicate_hash", True))

        source_url = str(opportunity.get("website_url") or "")
        hits: list[PatternHit] = []
        seen_values: set[str] = set()

        for rule in rules:
            text = self._corpus(opportunity, rule.search_in)
            if not text.strip():
                continue
            for match in rule.compiled().finditer(text):
                if len(hits) >= max_hits:
                    break
                if not self._is_safe_match(text, match):
                    continue
                value = match.group(0).strip()
                norm = value.lower()
                if drop_dupes and norm in seen_values:
                    continue
                seen_values.add(norm)

                confidence = min(1.0, rule.min_confidence + 0.15)
                if rule.lane == "arbitrage_alert":
                    confidence = min(1.0, confidence + 0.1)

                if confidence < rule.min_confidence:
                    continue

                hits.append(
                    PatternHit(
                        pattern_id=rule.id,
                        pattern_label=rule.label,
                        matched_value=value,
                        source_url=source_url,
                        context_snippet=self._snippet(text, match.start(), match.end()),
                        confidence=round(confidence, 2),
                        valuation_eur=round(rule.data_product_value_eur, 2),
                        lane=rule.lane,
                    )
                )

        return hits

    def hits_to_dicts(self, hits: list[PatternHit]) -> list[dict[str, Any]]:
        return [asdict(h) for h in hits]
