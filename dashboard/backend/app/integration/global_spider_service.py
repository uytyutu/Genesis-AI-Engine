"""Global Spider — worldwide technology-pattern discovery (public URLs only).

SECURITY LAW: no IP/port scanning, no credential probes. Only public HTTP(S)
targets via curated seeds and optional Google Places text search worldwide.
"""

from __future__ import annotations

import json
import logging
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

logger = logging.getLogger(__name__)

# City → approximate center for Places locationBias (meters radius from config)
_CITY_COORDS: dict[str, tuple[float, float]] = {
    "köln": (50.9375, 6.9603),
    "koln": (50.9375, 6.9603),
    "cologne": (50.9375, 6.9603),
    "berlin": (52.5200, 13.4050),
    "hamburg": (53.5511, 9.9937),
    "münchen": (48.1351, 11.5820),
    "munchen": (48.1351, 11.5820),
    "munich": (48.1351, 11.5820),
    "frankfurt": (50.1109, 8.6821),
    "stuttgart": (48.7758, 9.1829),
    "düsseldorf": (51.2277, 6.7735),
    "dusseldorf": (51.2277, 6.7735),
    "leipzig": (51.3397, 12.3731),
    "dresden": (51.0504, 13.7373),
    "pirna": (50.9623, 13.9415),
}


def _city_coords(city: str) -> tuple[float, float] | None:
    key = (city or "").strip().casefold()
    return _CITY_COORDS.get(key)


# Major DE hubs — used when search_city / target_city == "all_major_hubs"
DE_MAJOR_HUBS: tuple[str, ...] = (
    "Berlin",
    "Hamburg",
    "München",
    "Köln",
    "Frankfurt",
    "Stuttgart",
    "Düsseldorf",
    "Leipzig",
    "Dresden",
    "Hannover",
    "Nürnberg",
    "Dortmund",
    "Essen",
    "Bremen",
    "Bonn",
    "Mannheim",
    "Karlsruhe",
    "Augsburg",
    "Chemnitz",
    "Pirna",
)

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_BLOCKED_SEED_HOSTS = frozenset(
    {
        "wikipedia.org",
        "python.org",
        "mozilla.org",
        "debian.org",
        "nginx.com",
        "cloudflare.com",
        "f5.com",
        "example.com",
        "github.com",
        "google.com",
        "facebook.com",
        "apache.org",
        "w3.org",
    }
)


def _is_blocked_seed_url(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return any(host == d or host.endswith("." + d) for d in _BLOCKED_SEED_HOSTS)

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
    "freeze_lists": True,
    "target_mode": "places_only",
    "seed_targets": [],
    "toloka_task_categories": [],
    "places_queries": [],
    "profitable_niches": [
        "Kfz-Werkstatt",
        "Autowerkstatt",
        "Autoreparatur",
        "Photovoltaik Anbieter",
        "Dachdecker",
    ],
    "min_task_price": DEFAULT_MIN_TASK_PRICE,
    "polling_interval_sec": DEFAULT_POLLING_INTERVAL_SEC,
    "hosting_asn_hints": [
        {"asn_label": "Global CDN / shared hosting", "note": "Public URL seeds only — no port scan"},
        {"asn_label": "WordPress.com / SaaS builders", "note": "Detected via HTML tech_stack"},
    ],
    "regions_enabled": False,
    "max_batch": 200,
    "search_region": "de",
    "search_city": "Köln",
    "target_city": "Köln",
    "search_radius": 20000,
    "search_lat": 50.9375,
    "search_lng": 6.9603,
    "note": "profitable_niches cycle · target_city + search_radius from config",
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

    def hunting_target(self) -> dict[str, Any]:
        """Locked location + niche comb from config (shared by Spider / Acquisition / Asset Scanner)."""
        cfg = self.load_config()
        city = str(cfg.get("target_city") or cfg.get("search_city") or "Köln").strip() or "Köln"
        niches = [
            str(q).strip()
            for q in (cfg.get("profitable_niches") or cfg.get("places_queries") or [])
            if str(q).strip()
        ]
        if not niches:
            niches = list(_DEFAULT_GLOBAL_CONFIG.get("profitable_niches") or [])
        try:
            radius_m = int(cfg.get("search_radius") or 20000)
        except (TypeError, ValueError):
            radius_m = 20000
        radius_m = max(1000, min(radius_m, 50000))
        return {
            "target_city": city,
            "search_city": city,
            "search_radius": radius_m,
            "profitable_niches": niches,
            "search_region": str(cfg.get("search_region") or "de").strip().lower() or "de",
        }

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
        lat: float | None = None,
        lng: float | None = None,
        radius_m: int = 25000,
    ) -> None:
        if not self._places.configured() or len(urls) >= batch_limit:
            return
        try:
            leads = self._places.search_text(
                query=f"{query} {city}".strip() if city and city.casefold() not in query.casefold() else query,
                limit=min(12, batch_limit - len(urls)),
                region=region,
                lat=lat,
                lng=lng,
                radius_m=radius_m,
            )
        except (ValueError, RuntimeError) as exc:
            err = str(exc)
            stats["places_error"] = err[:180]
            if "OVER_QUERY_LIMIT" in err or "REQUEST_DENIED" in err:
                stats["places_quota_or_denied"] = True
            logger.warning("Places search failed in %s: %s", city, err[:160])
            return
        for lead in leads:
            site = (lead.website or "").strip()
            if site.startswith(("http://", "https://")) and site not in seen and not _is_blocked_seed_url(site):
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
        # Location lock: target_city wins over search_city (CEO config)
        city_raw = str(cfg.get("target_city") or cfg.get("search_city") or "Köln").strip()
        hub_mode = city_raw.casefold() in ("all_major_hubs", "all", "*", "de_hubs")
        if hub_mode:
            hubs = [str(c).strip() for c in (cfg.get("hub_cities") or DE_MAJOR_HUBS) if str(c).strip()]
        else:
            hubs = [city_raw]
        stats["hubs"] = list(hubs)
        stats["hub_mode"] = hub_mode
        stats["target_city"] = city_raw

        try:
            radius_m = int(cfg.get("search_radius") or 20000)
        except (TypeError, ValueError):
            radius_m = 20000
        radius_m = max(1000, min(radius_m, 50000))
        stats["search_radius_m"] = radius_m

        try:
            lat = float(cfg["search_lat"]) if cfg.get("search_lat") is not None else None
        except (TypeError, ValueError):
            lat = None
        try:
            lng = float(cfg["search_lng"]) if cfg.get("search_lng") is not None else None
        except (TypeError, ValueError):
            lng = None
        # Hub mode: no single coordinate bias. Single city: use config or known center.
        if hub_mode:
            lat, lng = None, None
        elif lat is None or lng is None:
            coords = _city_coords(city_raw)
            if coords:
                lat, lng = coords

        places_only = bool(cfg.get("freeze_lists") or cfg.get("target_mode") == "places_only")
        # Autonomous niche comb: profitable_niches first, else places_queries
        niches = [
            str(q).strip()
            for q in (cfg.get("profitable_niches") or cfg.get("places_queries") or [])
            if str(q).strip()
        ]
        stats["niches"] = list(niches)
        places_queries = niches

        if not places_only:
            for raw in cfg.get("seed_targets") or []:
                u = str(raw).strip()
                if not u:
                    continue
                if u.startswith(("http://", "https://")):
                    if _is_blocked_seed_url(u):
                        continue
                    if u not in seen:
                        seen.add(u)
                        urls.append(u)
                        stats["seeds"] += 1
                else:
                    for hub in hubs:
                        hub_lat, hub_lng = (None, None) if hub_mode else (lat, lng)
                        if hub_mode:
                            c = _city_coords(hub)
                            if c:
                                hub_lat, hub_lng = c
                        self._places_text_search(
                            u,
                            region=region,
                            city=hub,
                            seen=seen,
                            urls=urls,
                            batch_limit=batch_limit,
                            stats=stats,
                            lat=hub_lat,
                            lng=hub_lng,
                            radius_m=radius_m,
                        )
                        if len(urls) >= batch_limit:
                            return urls[:batch_limit], stats
                if len(urls) >= batch_limit:
                    return urls[:batch_limit], stats

        # Niche cycle × city hubs — autonomous comb without manual category typing
        if places_queries and self._places.configured():
            for q in places_queries:
                if len(urls) >= batch_limit:
                    break
                logger.info("Niche sweep: %s", q)
                stats["niche_current"] = q
                for hub in hubs:
                    if len(urls) >= batch_limit:
                        break
                    hub_lat, hub_lng = (lat, lng)
                    if hub_mode:
                        c = _city_coords(hub)
                        hub_lat, hub_lng = (c if c else (None, None))
                    logger.info("Searching places in %s · niche=%s ...", hub, q)
                    stats["regions_scanned"] = int(stats.get("regions_scanned") or 0) + 1
                    before = len(urls)
                    self._places_text_search(
                        q,
                        region=region,
                        city=hub,
                        seen=seen,
                        urls=urls,
                        batch_limit=batch_limit,
                        stats=stats,
                        stat_key="places_queries",
                        lat=hub_lat,
                        lng=hub_lng,
                        radius_m=radius_m,
                    )
                    if len(urls) > before:
                        stats["places_queries"] = int(stats.get("places_queries") or 0) + 1
                    if len(urls) >= batch_limit:
                        return urls[:batch_limit], stats

        # Optional worldwide regions only when not locked to DE hubs
        world_scan = bool(cfg.get("regions_enabled", True)) and not hub_mode and region != "de"
        if self._places.configured() and world_scan:
            suffix = _NICHE_QUERY_SUFFIX.get(niche, _NICHE_QUERY_SUFFIX["local_service"])
            per_region = max(2, batch_limit // max(1, len(_GLOBAL_QUERIES)))
            for scan_region, scan_city, base_query in _GLOBAL_QUERIES:
                if len(urls) >= batch_limit:
                    break
                logger.info("Searching places in %s...", scan_city)
                stats["regions_scanned"] = int(stats.get("regions_scanned") or 0) + 1
                query = f"{base_query} {suffix}".strip()
                try:
                    leads = self._places.search_text(
                        query=f"{query} {scan_city}",
                        limit=min(per_region, 25),
                        region=scan_region,
                    )
                except (ValueError, RuntimeError):
                    continue
                for lead in leads:
                    site = (lead.website or "").strip()
                    if (
                        site.startswith(("http://", "https://"))
                        and site not in seen
                        and not _is_blocked_seed_url(site)
                    ):
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
        niches = [str(x).strip() for x in (cfg.get("profitable_niches") or []) if str(x).strip()]
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
            "profitable_niches": niches,
            "profitable_niches_count": len(niches),
            "min_task_price": settings["min_task_price"],
            "polling_interval_sec": settings["polling_interval_sec"],
            "hunter_mode": True,
            "places_configured": self._places.configured(),
            "asn_watch": cfg.get("asn_watch"),
            "hosting_asn_hints": cfg.get("hosting_asn_hints") or [],
            "search_region": cfg.get("search_region"),
            "search_city": cfg.get("search_city"),
            "target_city": cfg.get("target_city") or cfg.get("search_city"),
            "search_radius": cfg.get("search_radius"),
            "note": str(
                cfg.get("note")
                or "profitable_niches · target_city · Places API (New)"
            ),
        }
