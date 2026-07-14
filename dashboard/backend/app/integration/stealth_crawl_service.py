"""Stealth Mode facade — delegates to stealth_http."""

from app.integration.stealth_http import (
    READ_ONLY_METHODS,
    STEALTH_USER_AGENT,
    StealthHttpClient,
    StealthPreflight,
    UnauthorizedOperation,
    external_get,
    external_request,
    log_stealth_violation,
    requires_stealth_policy,
    stealth_fetch_get,
    stealth_preflight,
    stealth_status,
)

__all__ = [
    "READ_ONLY_METHODS",
    "STEALTH_USER_AGENT",
    "StealthCrawlService",
    "StealthHttpClient",
    "StealthPreflight",
    "UnauthorizedOperation",
    "external_get",
    "external_request",
    "log_stealth_violation",
    "requires_stealth_policy",
    "stealth_fetch_get",
    "stealth_preflight",
    "stealth_status",
]


class StealthCrawlService(StealthHttpClient):
    """Backward-compatible alias."""

    def fetch_get(self, url: str, *, timeout: float = 12.0) -> object:
        return self.get(url, timeout=timeout)
