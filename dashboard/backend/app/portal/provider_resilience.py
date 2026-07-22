"""OR4 — Provider resilience (timeout · safe retry · operator-safe errors)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable, TypeVar

from app.portal.ai_provider_protocol import AIGenerationResult

ENGINE_ID = "provider_resilience_v1"

OPERATOR_PROVIDER_UNAVAILABLE = (
    "AI provider temporarily unavailable. Conversation remains available."
)

DEFAULT_TIMEOUT_SECONDS = 60.0
SAFE_RETRY_ERROR_CODES = frozenset(
    {"rate_limited", "provider_unavailable", "timeout", "generation_failed"}
)

T = TypeVar("T")


def call_with_timeout(
    fn: Callable[[], T], *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
) -> T:
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeout as exc:
            future.cancel()
            raise TimeoutError("provider_timeout") from exc


def _error_code(result: AIGenerationResult) -> str | None:
    prepared = result.prepared or {}
    if prepared.get("error_code"):
        return str(prepared["error_code"])
    ai_response = prepared.get("ai_response")
    if isinstance(ai_response, dict):
        meta = ai_response.get("metadata") or {}
        if isinstance(meta, dict) and meta.get("error_code"):
            return str(meta["error_code"])
        if ai_response.get("finish_reason") == "error":
            return "generation_failed"
    if prepared.get("ready") is False and result.provider_type in {"none", "stub"}:
        return "provider_unavailable"
    return None


def is_provider_failure(result: AIGenerationResult) -> bool:
    code = _error_code(result)
    if code is not None:
        return True
    text = (result.text or "").strip().lower()
    if text in {"provider unavailable.", ""}:
        return True
    return False


def should_retry(result: AIGenerationResult) -> bool:
    code = _error_code(result)
    return code in SAFE_RETRY_ERROR_CODES if code else False


def operator_safe_failure(
    *, provider_type: str, prepared: dict | None = None
) -> AIGenerationResult:
    merged = dict(prepared or {})
    merged["operator_safe"] = True
    merged["error_code"] = "provider_unavailable"
    return AIGenerationResult(
        text=OPERATOR_PROVIDER_UNAVAILABLE,
        provider_type=provider_type or "none",
        prepared=merged,
    )


def generate_resilient(
    generate_once: Callable[[], AIGenerationResult],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_attempts: int = 2,
) -> AIGenerationResult:
    """Timeout + one safe retry. Never raises vendor stack to callers."""
    last: AIGenerationResult | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            last = call_with_timeout(generate_once, timeout_seconds=timeout_seconds)
        except TimeoutError:
            last = operator_safe_failure(
                provider_type="timeout",
                prepared={"error_code": "timeout", "attempt": attempt},
            )
        except Exception as exc:  # noqa: BLE001 — degrade for operator
            last = operator_safe_failure(
                provider_type="error",
                prepared={
                    "error_code": "provider_unavailable",
                    "attempt": attempt,
                    "detail": type(exc).__name__,
                },
            )
        assert last is not None
        if not is_provider_failure(last):
            return last
        if attempt >= max_attempts or not should_retry(last):
            break
    assert last is not None
    if is_provider_failure(last):
        return operator_safe_failure(
            provider_type=last.provider_type,
            prepared=dict(last.prepared or {}),
        )
    return last
