"""Central Stealth HTTP policy for external website reads.

Applies to third-party public sites only — NOT payment/LLM/TTS APIs.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)

STEALTH_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

READ_ONLY_METHODS = frozenset({"GET", "HEAD"})
DEFAULT_MIN_INTERVAL_SEC = 4.0

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

_STEALTH_EXEMPT_HOSTS = frozenset(
    {
        "api.stripe.com",
        "maps.googleapis.com",
        "api.openai.com",
        "api.groq.com",
        "api.resend.com",
        "api.etherscan.io",
        "api.polygonscan.com",
        "api.arbiscan.io",
        "api.bscscan.com",
        "api.elevenlabs.io",
        "openrouter.ai",
        "api.openrouter.ai",
        "localhost",
        "127.0.0.1",
    }
)

_STEALTH_EXEMPT_SUFFIXES = (
    ".stripe.com",
    ".googleapis.com",
    ".openai.azure.com",
    ".cognitiveservices.azure.com",
    ".up.railway.app",
    ".vercel.app",
)

_FORBIDDEN_PATH = re.compile(
    r"(?:^|/)"
    r"(?:wp-admin|wp-login\.php|admin|administrator|login|signin|signup|register|"
    r"cgi-bin|phpmyadmin|\.env|\.git|api/internal|oauth|authorize)"
    r"(?:/|$|\?)",
    re.I,
)


class UnauthorizedOperation(Exception):
    """Force-Read-Only: only GET/HEAD permitted on stealth-scoped hosts."""


@dataclass
class StealthPreflight:
    allowed: bool
    url: str
    domain: str
    reason: str | None = None
    robots_checked: bool = False
    robots_allowed: bool | None = None
    read_only: bool = True


def requires_stealth_policy(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    host = (parsed.netloc or "").lower().split(":")[0]
    if not host:
        return False
    if host in _STEALTH_EXEMPT_HOSTS:
        return False
    if any(host.endswith(suffix) for suffix in _STEALTH_EXEMPT_SUFFIXES):
        return False
    if host.startswith("192.168.") or host.startswith("10."):
        return False
    return parsed.scheme in ("http", "https")


def log_stealth_violation(
    *,
    url: str,
    method: str,
    reason: str,
    memory_dir: Path | None = None,
) -> None:
    row = {
        "at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "method": str(method).upper(),
        "reason": reason,
        "event": "stealth_violation",
    }
    logger.warning("Stealth Mode violation: %s %s — %s", method.upper(), url, reason)
    path = (memory_dir or _DEFAULT_MEMORY) / "stealth_violations.jsonl"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


class StealthHttpClient:
    """Force-Read-Only httpx client for external website crawling."""

    def __init__(
        self,
        *,
        min_interval_sec: float = DEFAULT_MIN_INTERVAL_SEC,
        memory_dir: Path | None = None,
    ) -> None:
        self._min_interval = max(3.0, min(5.0, float(min_interval_sec)))
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._last_hit: dict[str, float] = {}
        self._robots_cache: dict[str, tuple[float, RobotFileParser | None, str]] = {}

    def browser_headers(self) -> dict[str, str]:
        return {
            "User-Agent": STEALTH_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        }

    def status(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "mode": "stealth",
            "user_agent": STEALTH_USER_AGENT,
            "min_interval_sec": self._min_interval,
            "robots_txt_required": True,
            "read_only": True,
            "force_read_only": True,
            "allowed_methods": sorted(READ_ONLY_METHODS),
            "violation_log": "memory/stealth_violations.jsonl",
            "legal_note": (
                "Только публичное чтение HTML. robots.txt обязателен. "
                "Любой не-GET/HEAD на внешний сайт → Unauthorized Operation."
            ),
        }

    def assert_read_only_target(self, url: str) -> None:
        raw = (url or "").strip()
        if not raw.startswith(("http://", "https://")):
            raise ValueError("public_http_only")
        path = urlparse(raw).path or "/"
        if _FORBIDDEN_PATH.search(path):
            raise ValueError("forbidden_target")

    def preflight(self, url: str, *, method: str = "GET", skip_throttle: bool = False) -> StealthPreflight:
        normalized = (url or "").strip()
        parsed = urlparse(normalized)
        domain = (parsed.netloc or "").lower().split(":")[0]
        if not domain:
            return StealthPreflight(False, normalized, "", reason="invalid_url")

        method_u = method.upper()
        if method_u not in READ_ONLY_METHODS:
            log_stealth_violation(
                url=normalized,
                method=method_u,
                reason="Unauthorized Operation",
                memory_dir=self._memory,
            )
            return StealthPreflight(
                False, normalized, domain, reason="Unauthorized Operation", read_only=False
            )

        try:
            self.assert_read_only_target(normalized)
        except ValueError as exc:
            return StealthPreflight(False, normalized, domain, reason=str(exc))

        robots_ok, checked = self._robots_allows(normalized)
        if checked and not robots_ok:
            return StealthPreflight(
                False,
                normalized,
                domain,
                reason="robots_txt_disallowed",
                robots_checked=True,
                robots_allowed=False,
            )
        if not skip_throttle:
            self._throttle_domain(domain)
        return StealthPreflight(
            True,
            normalized,
            domain,
            robots_checked=checked,
            robots_allowed=robots_ok if checked else None,
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        timeout: float = 12.0,
        follow_redirects: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        method_u = method.upper()
        if requires_stealth_policy(url):
            if method_u not in READ_ONLY_METHODS:
                log_stealth_violation(
                    url=url,
                    method=method_u,
                    reason="Unauthorized Operation",
                    memory_dir=self._memory,
                )
                raise UnauthorizedOperation("Unauthorized Operation")
            gate = self.preflight(url, method=method_u)
            if not gate.allowed:
                raise ValueError(gate.reason or "stealth_blocked")
            headers = {**self.browser_headers(), **(kwargs.pop("headers", None) or {})}
            with httpx.Client(timeout=timeout, follow_redirects=follow_redirects, headers=headers) as client:
                response = client.request(method_u, url, **kwargs)
            if response.request.method.upper() not in READ_ONLY_METHODS:
                log_stealth_violation(
                    url=url,
                    method=response.request.method,
                    reason="Unauthorized Operation",
                    memory_dir=self._memory,
                )
                raise UnauthorizedOperation("Unauthorized Operation")
            return response

        headers = kwargs.pop("headers", None) or {}
        with httpx.Client(timeout=timeout, follow_redirects=follow_redirects) as client:
            return client.request(method_u, url, headers=headers, **kwargs)

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("HEAD", url, **kwargs)

    def _throttle_domain(self, domain: str) -> None:
        now = time.monotonic()
        last = self._last_hit.get(domain, 0.0)
        wait = self._min_interval - (now - last)
        if wait > 0:
            time.sleep(wait)
        self._last_hit[domain] = time.monotonic()

    def _robots_allows(self, url: str) -> tuple[bool, bool]:
        parsed = urlparse(url)
        domain = (parsed.netloc or "").lower().split(":")[0]
        if not domain:
            return False, False

        now = time.monotonic()
        cached = self._robots_cache.get(domain)
        if cached and (now - cached[0]) < 3600.0:
            parser, status = cached[1], cached[2]
            if parser is None:
                return True, status == "missing"
            return parser.can_fetch(STEALTH_USER_AGENT, url), True

        robots_url = f"{parsed.scheme}://{domain}/robots.txt"
        try:
            with httpx.Client(timeout=8.0, headers=self.browser_headers()) as client:
                res = client.get(robots_url)
        except httpx.HTTPError:
            self._robots_cache[domain] = (now, None, "unreachable")
            return True, False

        if res.status_code == 404:
            self._robots_cache[domain] = (now, None, "missing")
            return True, True
        if res.status_code >= 400:
            self._robots_cache[domain] = (now, None, "error")
            return True, False

        parser = RobotFileParser()
        parser.parse(res.text.splitlines())
        allowed = parser.can_fetch(STEALTH_USER_AGENT, url)
        self._robots_cache[domain] = (now, parser, "ok")
        return allowed, True


_DEFAULT_CLIENT = StealthHttpClient()


def stealth_preflight(url: str, *, method: str = "GET", skip_throttle: bool = False) -> StealthPreflight:
    return _DEFAULT_CLIENT.preflight(url, method=method, skip_throttle=skip_throttle)


def stealth_fetch_get(url: str, *, timeout: float = 12.0) -> httpx.Response:
    return _DEFAULT_CLIENT.get(url, timeout=timeout)


def stealth_status() -> dict[str, Any]:
    return _DEFAULT_CLIENT.status()


def external_get(url: str, **kwargs: Any) -> httpx.Response:
    return _DEFAULT_CLIENT.get(url, **kwargs)


def external_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    return _DEFAULT_CLIENT.request(method, url, **kwargs)
