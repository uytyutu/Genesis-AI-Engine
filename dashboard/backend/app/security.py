"""Production access gates — Public / Owner / Internal API tiers."""

from __future__ import annotations

import hmac
import os
import re

from fastapi import HTTPException, Request

from app.config import is_production

_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

OWNER_PREFIXES = ("/api/owner/",)

WORKSPACE_PREFIXES = ("/api/workspace/",)
PROJECT_PREFIXES = ("/api/project/",)

INTERNAL_PREFIXES = (
    "/api/dev/",
    "/api/cursor/",
    "/api/ai-hub/",
    "/api/opportunities",
    "/api/acquisition",
    "/api/leads",
    "/api/scanner",
    "/api/engine",
    "/api/modules",
    "/api/queue",
    "/api/activity",
    "/api/tasks",
    "/api/control/",
    "/api/demo/",
    "/api/assistant/",
    "/api/factory/",
    "/api/support",
    *WORKSPACE_PREFIXES,
    *PROJECT_PREFIXES,
)

_PUBLIC_EXACT = frozenset({"/health", "/status", "/api/status"})

_PUBLIC_PREFIXES = (
    "/api/public/",
    "/api/client/",
    "/api/sales/packages",
    "/api/sales/payment-status",
    "/api/sales/email-status",
    "/api/webhooks/",
    "/webhooks/",
)

_PUBLIC_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"^/api/sales/orders$", "POST"),
    (r"^/api/sales/orders/[^/]+/status$", "GET"),
    (r"^/api/sales/orders/[^/]+/download$", "GET"),
    (r"^/api/sales/orders/[^/]+/checkout$", "POST"),
    (r"^/api/sales/orders/[^/]+/confirm-payment$", "POST"),
    (r"^/api/sales/orders/[^/]+/pay-sandbox$", "POST"),
    (r"^/api/sales/orders/[^/]+/reviews$", "POST"),
    (r"^/api/factory/intent$", "POST"),
    (r"^/api/factory/products/[^/]+/preview$", "GET"),
    (r"^/api/client/register$", "POST"),
    (r"^/api/client/login$", "POST"),
    (r"^/api/public/evolution/tickets$", "POST"),
)


def _client_host(request: Request) -> str:
    client = request.client
    return (client.host if client else "") or ""


def is_owner_api_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in OWNER_PREFIXES)


def is_workspace_api_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in WORKSPACE_PREFIXES)


def is_project_api_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PROJECT_PREFIXES)


def is_future_layer_api_path(path: str) -> bool:
    return is_workspace_api_path(path) or is_project_api_path(path)


def is_internal_api_path(path: str) -> bool:
    if is_owner_api_path(path):
        return True
    return any(path.startswith(prefix) for prefix in INTERNAL_PREFIXES)


def is_public_api_path(path: str, method: str = "GET") -> bool:
    if path in _PUBLIC_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in _PUBLIC_PREFIXES):
        return True
    upper = method.upper()
    for pattern, allowed_method in _PUBLIC_PATTERNS:
        if upper == allowed_method and re.match(pattern, path):
            return True
    return False


def production_api_allowed(path: str, method: str = "GET") -> bool:
    return is_public_api_path(path, method)


def support_bridge_allowed(request: Request) -> bool:
    """CEO desk (localhost) may call production /api/support with shared bridge secret."""
    secret = (
        os.getenv("SUPPORT_BRIDGE_SECRET", "").strip()
        or os.getenv("RESEND_INBOUND_WEBHOOK_SECRET", "").strip()
    )
    if not secret:
        return False
    header = (
        request.headers.get("x-support-bridge")
        or request.headers.get("x-genesis-support-bridge")
        or ""
    ).strip()
    if header and hmac.compare_digest(header, secret):
        return True
    auth = (request.headers.get("authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token and hmac.compare_digest(token, secret):
            return True
    return False


def local_owner_access_allowed(request: Request) -> bool:
    """Owner setup and dev tools — localhost in development only."""
    if is_production():
        return False
    return _client_host(request) in _LOCAL_HOSTS


def dev_mode_allowed(request: Request) -> bool:
    """Thinking Brief / debug — never in production."""
    if is_production():
        return False
    flag = os.getenv("GENESIS_DEV_MODE", "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    return _client_host(request) in _LOCAL_HOSTS


def require_local_owner(request: Request) -> None:
    if not local_owner_access_allowed(request):
        raise HTTPException(
            status_code=403,
            detail="Owner and development endpoints are disabled in production",
        )


def api_access_denied_response(path: str, method: str) -> dict[str, str]:
    if is_production():
        return {"detail": "Not available in production"}
    if is_owner_api_path(path):
        return {"detail": "Owner endpoints require localhost"}
    return {"detail": "Internal endpoints require localhost"}


_META_EXFILTRATION = re.compile(
    r"system\s*prompt|thinking\s*brief|внутренн\w*\s+инструк|"
    r"api\s*keys?|\.env|secrets?/|память\s+друг|чуж\w+\s+памят|"
    r"workforce\s*director|runtime\s*pipeline|executive\s*trace|"
    r"director_reflections|employee_ratings|"
    r"покажи\s+(?:свой|мне|полный)|"
    r"выведи\s+(?:содержимое|все)|dump\s+(?:config|memory|prompt)|"
    # S1.4 — jailbreak / prompt-injection / secret extraction probes
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions|"
    r"disregard\s+(your|the)\s+(rules|instructions|system)|"
    r"you\s+are\s+now\s+(dan|jailbroken|unrestricted)|"
    r"developer\s+mode\s+enabled|\bjailbreak\b|"
    r"reveal\s+(your\s+)?(system|hidden)\s+prompt|"
    r"print\s+your\s+instructions|"
    r"пренебреги\s+(предыдущ|системн)|"
    r"забудь\s+(все\s+)?(?:свои\s+)?инструк|"
    r"режим\s+без\s+ограничен|"
    r"покажи\s+системн\w*\s+промпт|"
    r"extract\s+(the\s+)?api\s*key",
    re.I,
)

_INTERNAL_TERMS_IN_ANSWER = re.compile(
    r"thinking\s*brief|runtime\s*pipeline|workforce\s*reality|"
    r"executive\s*(?:trace|decision)|director_reflections|"
    r"GENESIS_GROQ_API_KEY|sk-[a-zA-Z0-9]{12,}",
    re.I,
)

_INFRA_LEAK_IN_ANSWER = re.compile(
    r"облачн\w*\s+модел|cloud[\s-]?proof|cloud[\s-]?exhausted|cloud\s+provider|"
    r"\bgroq\b|\bgemini\b|openrouter|\bollama\b|"
    r"лимит\w*\s+или\s+сет|provider|аварийный\s+режим|"
    r"инфраструктур|genesis-local|не\s+штатная\s+работа|"
    r"повторите\s+через\s+минуту",
    re.I,
)

_USER_SAFE_FALLBACK = (
    "Извините, сейчас не удалось сформировать ответ. "
    "Попробуйте переформулировать — я здесь, чтобы помочь."
)

META_EXFILTRATION_REFUSAL = (
    "Я не раскрываю внутренние инструкции, ключи или чужую память — "
    "это часть моей работы как собеседника. Давайте лучше о вашей задаче: "
    "чем могу быть полезен?"
)


def is_meta_exfiltration_attempt(text: str) -> bool:
    return bool(_META_EXFILTRATION.search((text or "").strip()))


def scrub_internal_terms_from_answer(text: str) -> str:
    """Last-line defense — never echo internal stack or LLM infra to users."""
    if not text:
        return text
    if _INTERNAL_TERMS_IN_ANSWER.search(text) or _INFRA_LEAK_IN_ANSWER.search(text):
        return _USER_SAFE_FALLBACK
    return text
