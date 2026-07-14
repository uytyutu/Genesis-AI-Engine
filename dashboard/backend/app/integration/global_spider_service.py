"""Global Spider — worldwide technology-pattern discovery (public URLs only).

SECURITY LAW: no IP/port scanning, no credential probes. Only public HTTP(S)
targets via curated seeds and optional Google Places text search worldwide.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.integration.google_places_service import GooglePlacesService

from app.integration.farm_hunting_defaults import (
    DEFAULT_MIN_TASK_PRICE,
    DEFAULT_POLLING_INTERVAL_SEC,
    HIGH_VALUE_PLACES_QUERIES,
    HIGH_VALUE_SEED_TARGETS,
    HIGH_VALUE_TOLOKA_CATEGORIES,
    hunting_settings,
    merge_hunting_config,
)

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_TLD_COUNTRY: dict[str, str] = {
    "de": "DE",
    "at": "AT",
    "ch": "CH",
    "uk": "GB",
    "co.uk": "GB",
    "fr": "FR",
    "es": "ES",
    "it": "IT",
    "nl": "NL",
    "pl": "PL",
    "in": "IN",
    "br": "BR",
    "mx": "MX",
    "au": "AU",
    "ca": "CA",
    "us": "US",
    "com": "GLOBAL",
    "org": "GLOBAL",
    "net": "GLOBAL",
}

_GLOBAL_QUERIES: list[tuple[str, str, str]] = [
    ("us", "New York", "local business website"),
    ("us", "Los Angeles", "dentist website"),
    ("gb", "London", "plumber website"),
    ("gb", "Manchester", "cafe website"),
    ("in", "Mumbai", "clinic website"),
    ("in", "Delhi", "restaurant website"),
    ("br", "São Paulo", "oficina mecânica site"),
    ("mx", "Mexico City", "taller mecánico sitio"),
    ("au", "Sydney", "tradie website"),
    ("ca", "Toronto", "auto repair website"),
    ("de", "Berlin", "Handwerker website"),
    ("fr", "Paris", "artisan site web"),
    ("es", "Madrid", "taller web"),
    ("it", "Rome", "officina sito"),
    ("pl", "Warsaw", "warsztat strona"),
    ("nl", "Amsterdam", "loodgieter website"),
]


def world_scan_regions() -> list[tuple[str, str, str]]:
    """(region_code, city, base_query) — worldwide Places batch."""
    return list(_GLOBAL_QUERIES)

_NICHE_QUERY_SUFFIX: dict[str, str] = {
    "local_service": "local service business",
    "expired_landing": "coming soon business website",
    "niche_blog": "old blog website",
}

_DEFAULT_GLOBAL_CONFIG: dict[str, Any] = {
    "mode": "global_spider",
    "zero_cost": True,
    "tech_pattern_priority": True,
    "asn_watch": "horizon_public_url_seeds_only",
    "seed_targets": list(HIGH_VALUE_SEED_TARGETS),
    "toloka_task_categories": list(HIGH_VALUE_TOLOKA_CATEGORIES),
    "places_queries": list(HIGH_VALUE_PLACES_QUERIES),
    "min_task_price": DEFAULT_MIN_TASK_PRICE,
    "polling_interval_sec": DEFAULT_POLLING_INTERVAL_SEC,
    "hosting_asn_hints": [
        {"asn_label": "Global CDN / shared hosting", "note": "Public URL seeds only — no port scan"},
        {"asn_label": "WordPress.com / SaaS builders", "note": "Detected via HTML tech_stack"},
    ],
    "regions_enabled": True,
    "max_batch": 200,
    "search_region": "de",
    "search_city": "Dresden",
    "note": "toloka_task_categories — вектор биржи · min_task_price — отсев копеек · polling_interval_sec — охота.",
}


class GlobalSpiderService:
    """Discovers public targets worldwide by technology/problem patterns."""

    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._places = GooglePlacesService()

    def _config_path(self) -> Path:
        return self._memory / "global_spider_config.json"

    def load_config(self) -> dict[str, Any]:
        path = self._config_path()
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            cfg = merge_hunting_config(dict(_DEFAULT_GLOBAL_CONFIG))
            path.write_text(
                json.dumps(cfg, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return cfg
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            cfg = merge_hunting_config(raw if isinstance(raw, dict) else {})
            if cfg != raw:
                path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
            return cfg
        except (json.JSONDecodeError, OSError):
            return merge_hunting_config(dict(_DEFAULT_GLOBAL_CONFIG))

    @staticmethod
    def infer_country_code(url: str) -> str:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            return "UNKNOWN"
        parts = host.split(".")
        if len(parts) >= 3 and f"{parts[-2]}.{parts[-1]}" in _TLD_COUNTRY:
            return _TLD_COUNTRY[f"{parts[-2]}.{parts[-1]}"]
        tld = parts[-1] if parts else ""
        return _TLD_COUNTRY.get(tld, "GLOBAL")

    def _places_text_search(
        self,
        query: str,
        *,
        region: str,
        city: str,
        seen: set[str],
        urls: list[str],
        batch_limit: int,
        stats: dict[str, Any],
        stat_key: str = "query_seeds",
    ) -> None:
        if not self._places.configured() or len(urls) >= batch_limit:
            return
        try:
            leads = self._places.search_text(
                query=f"{query} {city}".strip(),
                limit=min(12, batch_limit - len(urls)),
                region=region,
            )
        except (ValueError, RuntimeError):
            return
        for lead in leads:
            site = (lead.website or "").strip()
            if site.startswith(("http://", "https://")) and site not in seen:
                seen.add(site)
                urls.append(site)
                stats["places"] += 1
                stats[stat_key] = int(stats.get(stat_key) or 0) + 1
            if len(urls) >= batch_limit:
                break

    def discover_candidate_urls(
        self,
        *,
        niche: str = "local_service",
        batch_limit: int = 100,
        tech_pattern_ids: list[str] | None = None,
    ) -> tuple[list[str], dict[str, Any]]:
        cfg = self.load_config()
        batch_limit = max(1, min(int(cfg.get("max_batch") or 1000), int(batch_limit)))
        seen: set[str] = set()
        urls: list[str] = []
        stats = {
            "seeds": 0,
            "places": 0,
            "query_seeds": 0,
            "places_queries": 0,
            "regions_scanned": 0,
            "toloka_categories": len(cfg.get("toloka_task_categories") or []),
            "tech_filter": tech_pattern_ids or [],
        }
        region = str(cfg.get("search_region") or "de").strip().lower()
        city = str(cfg.get("search_city") or "Dresden").strip()

        for raw in cfg.get("seed_targets") or []:
            u = str(raw).strip()
            if not u:
                continue
            if u.startswith(("http://", "https://")):
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
                    stats["seeds"] += 1
            else:
                self._places_text_search(
                    u, region=region, city=city, seen=seen, urls=urls, batch_limit=batch_limit, stats=stats
                )
            if len(urls) >= batch_limit:
                return urls[:batch_limit], stats

        for raw in cfg.get("places_queries") or []:
            q = str(raw).strip()
            if not q:
                continue
            before = len(urls)
            self._places_text_search(
                q,
                region=region,
                city=city,
                seen=seen,
                urls=urls,
                batch_limit=batch_limit,
                stats=stats,
                stat_key="places_queries",
            )
            if len(urls) > before:
                stats["places_queries"] = int(stats.get("places_queries") or 0) + 1
            if len(urls) >= batch_limit:
                return urls[:batch_limit], stats

        if self._places.configured() and cfg.get("regions_enabled", True):
            suffix = _NICHE_QUERY_SUFFIX.get(niche, _NICHE_QUERY_SUFFIX["local_service"])
            per_region = max(2, batch_limit // max(1, len(_GLOBAL_QUERIES)))
            for region, city, base_query in _GLOBAL_QUERIES:
                if len(urls) >= batch_limit:
                    break
                stats["regions_scanned"] += 1
                query = f"{base_query} {suffix}".strip()
                try:
                    leads = self._places.search_text(
                        query=f"{query} {city}",
                        limit=min(per_region, 25),
                        region=region,
                    )
                except (ValueError, RuntimeError):
                    continue
                for lead in leads:
                    site = (lead.website or "").strip()
                    if site.startswith(("http://", "https://")) and site not in seen:
                        seen.add(site)
                        urls.append(site)
                        stats["places"] += 1
                    if len(urls) >= batch_limit:
                        break

        return urls[:batch_limit], stats

    def matches_tech_patterns(self, analysis: dict[str, Any], pattern_ids: list[str] | None) -> bool:
        if not pattern_ids:
            return True
        stack = [str(s).lower() for s in (analysis.get("tech_stack") or [])]
        issues = " ".join(str(i) for i in (analysis.get("issues") or [])).lower()
        hay = " ".join(stack) + " " + issues
        for pid in pattern_ids:
            token = pid.replace("cms_", "").replace("_", " ")
            if token in hay or pid.replace("_", "-") in hay:
                return True
        return False

    def spider_dashboard(self) -> dict[str, Any]:
        cfg = self.load_config()
        settings = hunting_settings(cfg)
        toloka = [str(x).strip() for x in (cfg.get("toloka_task_categories") or []) if str(x).strip()]
        places_q = [str(x).strip() for x in (cfg.get("places_queries") or []) if str(x).strip()]
        seeds = [str(x).strip() for x in (cfg.get("seed_targets") or []) if str(x).strip()]
        return {
            "mode": cfg.get("mode", "global_spider"),
            "zero_cost": bool(cfg.get("zero_cost", True)),
            "regions_enabled": bool(cfg.get("regions_enabled", True)),
            "seed_targets_count": len(seeds),
            "seed_targets": seeds[:10],
            "toloka_categories_count": len(toloka),
            "toloka_task_categories": toloka[:12],
            "places_queries_count": len(places_q),
            "places_queries": places_q[:8],
            "min_task_price": settings["min_task_price"],
            "polling_interval_sec": settings["polling_interval_sec"],
            "hunter_mode": True,
            "places_configured": self._places.configured(),
            "asn_watch": cfg.get("asn_watch"),
            "hosting_asn_hints": cfg.get("hosting_asn_hints") or [],
            "search_region": cfg.get("search_region"),
            "search_city": cfg.get("search_city"),
            "note": str(
                cfg.get("note")
                or "Toloka-категории + min_task_price · polling_interval_sec = режим охотника."
            ),
        }
